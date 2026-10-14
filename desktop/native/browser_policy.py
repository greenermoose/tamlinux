#!/usr/bin/python3
"""Fixed native browser-color endpoint with explicit, preserving recovery."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

DIRECTORIES = ['/etc/chromium/policies/managed','/etc/opt/chrome/policies/managed',
               '/etc/opt/edge/policies/managed','/etc/brave/policies/managed']
RECOVERY = Path('/var/lib/tamlinux/browser-recovery')


def validate_directory(path, uid):
    for parent in (path,*path.parents):
        info=parent.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0,uid)
                or ((info.st_mode & 0o022) and not (parent == Path('/tmp') and info.st_uid==0 and info.st_mode & stat.S_ISVTX))):
            raise ValueError('Browser policy directory must have trusted ownership and permissions')


def snapshot(path, uid, limit=65536):
    if path.is_symlink(): raise ValueError('Conflicting browser policy link')
    if not path.exists(): return {'present':False}
    info=path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=uid or info.st_size>limit:
        raise ValueError('Conflicting browser policy file')
    return {'present':True,'bytes':base64.b64encode(path.read_bytes()).decode(),
            'mode':stat.S_IMODE(info.st_mode)}


def write(path, value):
    if not value['present']:
        path.unlink(missing_ok=True)
    else:
        fd,name=tempfile.mkstemp(prefix='.tamlinux-policy-',dir=path.parent)
        try:
            data=base64.b64decode(value['bytes'],validate=True)
            if len(data)>1024*1024: raise ValueError('Recovery record exceeds limit')
            with os.fdopen(fd,'wb') as handle:
                handle.write(data);handle.flush();os.fchmod(handle.fileno(),value['mode'] & 0o777);os.fsync(handle.fileno())
            os.replace(name,path)
        finally: Path(name).unlink(missing_ok=True)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def save(path, value):
    write(path,{'present':True,'mode':0o600,'bytes':base64.b64encode((json.dumps(value,indent=2)+'\n').encode()).decode()})


def apply(color, directories, recovery, uid=0):
    if not re.fullmatch('[0-9a-f]{6}',color): raise ValueError('Expected one lowercase six-digit color')
    rows=[]
    for directory in map(Path,directories):
        if not directory.exists(): continue
        validate_directory(directory,uid)
        target=directory/'tamlinux-color.json'
        rows.append({'path':str(target),'before':snapshot(target,uid)})
    if not rows: raise ValueError('No supported native browser policy directory is installed')
    if any(parent.is_symlink() for parent in (recovery,*recovery.parents)):
        raise ValueError('Redirected recovery directory')
    recovery.mkdir(parents=True,mode=0o700,exist_ok=True)
    if recovery.is_symlink() or recovery.stat().st_uid!=uid or recovery.stat().st_mode & 0o077:
        raise ValueError('Recovery directory must be private and trusted')
    journal=Path(tempfile.mkdtemp(prefix='color-',dir=recovery))
    payload=(json.dumps({'BrowserThemeColor':'#'+color,'BrowserColorScheme':'device'})+'\n').encode()
    after={'present':True,'mode':0o644,'bytes':base64.b64encode(payload).decode()}
    doc={'schema':1,'status':'prepared','files':rows,'after':after}
    save(journal/'manifest.json',doc)
    try:
        for row in rows:
            row['status']='writing';save(journal/'manifest.json',doc)
            write(Path(row['path']),after);row['status']='applied';save(journal/'manifest.json',doc)
    except BaseException:
        for row in reversed(rows):
            if row.get('status') in ('writing','applied'): write(Path(row['path']),row['before'])
        doc['status']='restored-after-failure';save(journal/'manifest.json',doc);raise
    doc['status']='applied';save(journal/'manifest.json',doc)
    return journal


def restore(journal, directories, uid=0):
    permitted={str(Path(directory)/'tamlinux-color.json') for directory in directories}
    value=snapshot(journal/'manifest.json',uid,1024*1024)
    if not value['present']:raise ValueError('Recovery journal unavailable')
    doc=json.loads(base64.b64decode(value['bytes']))
    if doc.get('schema')!=1 or any(row['path'] not in permitted for row in doc['files']):
        raise ValueError('Unlisted native recovery destination')
    # Validate the full set before restoring anything.
    for row in doc['files']:
        validate_directory(Path(row['path']).parent,uid)
        snapshot(Path(row['path']),uid)
    for row in reversed(doc['files']):
        target=Path(row['path']);current=snapshot(target,uid)
        if current!=row['before']:
            name='later-'+hashlib.sha256((str(target)+json.dumps(current,sort_keys=True)).encode()).hexdigest()+'.json'
            if not (journal/name).exists():save(journal/name,{'path':str(target),'state':current})
            write(target,row['before'])
    doc['status']='restored';save(journal/'manifest.json',doc)


def main(arguments):
    if os.geteuid()!=0:raise ValueError('Native policy changes require root authorization')
    if len(arguments)==1:
        print(apply(arguments[0],DIRECTORIES,RECOVERY).name)
    elif len(arguments)==2 and arguments[0]=='--restore' and re.fullmatch('color-[a-zA-Z0-9_-]{6,64}',arguments[1]):
        journal=RECOVERY/arguments[1]
        validate_directory(RECOVERY,0)
        validate_directory(journal,0)
        if journal.is_symlink():raise ValueError('Redirected recovery journal')
        restore(journal,DIRECTORIES)
    else:raise ValueError('Expected COLOR or --restore JOURNAL')


if __name__=='__main__':
    import sys
    try:main(sys.argv[1:])
    except (OSError,ValueError,KeyError) as error:sys.exit('tam-theme-set-browser-policy: '+str(error))
