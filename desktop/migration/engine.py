#!/usr/bin/env python3
"""Explicit, retryable user-state migration. Originals and later writes survive.

Plans are private recovery records, not arbitrary write instructions: every row
must still belong to this finite manifest and current XDG roots on resume.
No package, compositor, service or network command is executed. The CLI refreshes
the desktop database after an explicit launcher/MIME apply or rollback.
"""
import argparse
import base64
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
LIMIT = 1024 * 1024


def roots(environ):
    home = Path(environ['HOME'])
    result = {kind: Path(environ.get(variable) or home / fallback)
              for kind, variable, fallback in [('config','XDG_CONFIG_HOME','.config'),
                  ('state','XDG_STATE_HOME','.local/state'), ('data','XDG_DATA_HOME','.local/share')]}
    if not home.is_absolute() or any(not p.is_absolute() for p in result.values()):
        raise ValueError('HOME and XDG roots must be absolute')
    return result


def safe(path):
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Redirected parent: '+str(path))
    return path


def snapshot(path):
    safe(path)
    if not path.exists() and not path.is_symlink(): return {'kind':'absent'}
    info = path.lstat()
    if info.st_uid != os.getuid(): raise ValueError('Owner mismatch: '+str(path))
    if stat.S_ISLNK(info.st_mode):
        return {'kind':'link', 'link':os.readlink(path)}
    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
        raise ValueError('Expected bounded regular file: '+str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        current = os.fstat(fd)
        if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError('File changed while opening')
        content = os.read(fd, LIMIT + 1)
        if len(content)>LIMIT: raise ValueError('File grew beyond limit')
        return {'kind':'file', 'bytes':base64.b64encode(content).decode(),
                'mode':stat.S_IMODE(info.st_mode)}
    finally: os.close(fd)


def atomic(path, value):
    safe(path); path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if value['kind']=='absent':
        path.unlink(missing_ok=True)
    else:
        fd, name = tempfile.mkstemp(prefix='.tamlinux-migrate-', dir=path.parent)
        temporary = Path(name)
        try:
            if value['kind']=='link':
                os.close(fd); fd=-1; temporary.unlink(); temporary.symlink_to(value['link'])
            elif value['kind']=='file':
                data=base64.b64decode(value['bytes'],validate=True)
                if len(data)>LIMIT: raise ValueError('Recovery bytes exceed limit')
                os.write(fd,data); os.fchmod(fd,value['mode'] & 0o777); os.fsync(fd)
                os.close(fd); fd=-1
            else: raise ValueError('Unknown recovery kind')
            os.replace(temporary,path)
        finally:
            if fd>=0: os.close(fd)
            temporary.unlink(missing_ok=True)
    descriptor=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def save(path, document):
    atomic(path, {'kind':'file','mode':0o600,
        'bytes':base64.b64encode((json.dumps(document,indent=2,sort_keys=True)+'\n').encode()).decode()})


def convert(kind, data, commands, locations=None):
    if kind=='bytes': return data
    text=data.decode('utf-8')
    if kind=='imv-escape':
        lines=text.splitlines(keepends=True)
        sections=[i for i,line in enumerate(lines)
                  if re.fullmatch(r'\s*\[binds\]\s*(?:[#;].*)?',line.rstrip('\r\n'))]
        if len(sections)>1: raise ValueError('Multiple imv binds sections require review')
        newline='\r\n' if b'\r\n' in data else '\n'
        if sections:
            start=sections[0]+1
            end=next ( (i for i in range(start,len(lines)) if re.match(r'^\s*\[',lines[i])), len(lines))
            if any(re.match(r'^\s*<Escape>\s*=',line, re.IGNORECASE) for line in lines[start:end]):
                return None
            if end and not lines[end-1].endswith(('\n','\r')): lines[end-1]+=newline
            lines.insert(end,'<Escape> = quit'+newline)
        else:
            if lines and not lines[-1].endswith(('\n','\r')): lines[-1]+=newline
            lines.extend(['[binds]'+newline,'<Escape> = quit'+newline])
        return ''.join(lines).encode()
    if kind=='terminal-theme':
        if locations is None: raise ValueError('Terminal migration needs the selected XDG roots')
        state=str(locations['state'])
        if any(char in state for char in '\\"\r\n'):
            raise ValueError('Theme state path requires explicit terminal quoting review')
        result=[];section=''
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith('['): section=line.strip()
            directive=re.match(r'^\s*(include\s*(?:=|\s)|config-file\s*=|general\.import\s*=|import\s*=)',line)
            if directive and (not re.match(r'^\s*import\s*=',line) or section=='[general]'):
                for leaf in ('foot.ini','kitty.conf','ghostty.conf','alacritty.toml'):
                    for old in ('~/.local/state/omarchy/current/theme/'+leaf,
                                str(locations['state']/'omarchy/current/theme'/leaf)):
                        line=re.sub(r'(?<![\w/.-])'+re.escape(old)+r'(?=["\s\]]|$)',
                            lambda match: str(locations['state']/'tamlinux/current/theme'/leaf),line)
            result.append(line)
        converted=''.join(result).encode()
        return converted if converted!=data else None
    if kind=='desktop-mode':
        if text.strip()=='omarchy': return b'tamlinux\n'
        if text.strip() in ('tamlinux','mac','windows'): return data
        raise ValueError('Unknown desktop mode')
    if kind=='editor':
        value=text.strip()
        if value not in ('helix','hx','nvim','vim','emacs','code','cursor','zeditor','sublime_text'):
            raise ValueError('Unknown editor selection')
        return ('helix\n' if value=='hx' else value+'\n').encode()
    if kind=='device-name':
        value=text.removesuffix('\n')
        if not value or any(ord(c)<32 or ord(c)==127 for c in value):
            raise ValueError('Input device name must be one nonempty plain-data line')
        return data
    if kind=='webapp':
        # Only known executable/icon fields in Desktop Entry are changed.
        section=''; result=[]; changed=False
        replacements={
            'omarchy-launch-webapp':'tam-launch-webapp',
            'omarchy-webapp-handler-zoom':'tam-webapp-handler-zoom',
        }
        for line in text.splitlines(keepends=True):
            if line.startswith('['): section=line.strip()
            if section=='[Desktop Entry]':
                if line.rstrip('\r\n')=='Icon=omarchy-discord':
                    icon=HERE.parent/'assets/icons/tamlinux-discord.png'
                    if not icon.is_file(): raise ValueError('No selected replacement for omarchy-discord')
                    line=line.replace('Icon=omarchy-discord','Icon=tamlinux-discord',1); changed=True
                for old,new in replacements.items():
                    if re.match(r'^Exec='+re.escape(old)+r'(?:\s|$)',line):
                        if new not in commands: raise ValueError('No selected replacement for '+old)
                        line=line.replace('Exec='+old,'Exec='+new,1); changed=True
                        break
                # Preserve the terminal flags and any trailing launcher arguments.
                prefix='Exec=xdg-terminal-exec --app-id=TUI.tile -e '
                old='omarchy-launch-docker-tui';new='tam-launch-docker-tui'
                if re.match('^'+re.escape(prefix+old)+r'(?:\s|$)',line):
                    if new not in commands: raise ValueError('No selected replacement for '+old)
                    line=line.replace(prefix+old,prefix+new,1); changed=True
            result.append(line)
        return ''.join(result).encode() if changed else None
    if kind=='retire-hey-mime':
        section=''; result=[]
        for line in text.splitlines(keepends=True):
            if line.startswith('['): section=line.strip()
            match=re.fullmatch(r'([^=\r\n]+)=(.*?)(\r?\n)?',line)
            if section in ('[Default Applications]','[Added Associations]','[Removed Associations]') and match:
                tokens=match[2].split(';')
                kept=[token for token in tokens if token.strip()!='HEY.desktop']
                if kept!=tokens:
                    if not any(token.strip() for token in kept): continue
                    line=match[1]+'='+';'.join(kept)+(match[3] or '')
            result.append(line)
        converted=''.join(result).encode()
        return converted if converted!=data else None
    if kind=='bar-layout':
        doc=json.loads(text)
        if not isinstance(doc,dict) or not isinstance(doc.get('layout'),dict):
            raise ValueError('Unknown bar layout document')
        def identity(value):
            if not isinstance(value,str): raise ValueError('Invalid bar identity')
            if value.startswith('omarchy.'): value='tamlinux.'+value[8:]
            if not value.startswith(('tamlinux.','fred.')): raise ValueError('Unknown bar provider')
            return value
        for side in ('left','center','right'):
            if not isinstance(doc['layout'].get(side),list): raise ValueError('Missing bar region')
            for item in doc['layout'][side]: item['id']=identity(item['id'])
        if 'centerAnchor' in doc: doc['centerAnchor']=identity(doc['centerAnchor'])
        return (json.dumps(doc,indent=2)+'\n').encode()
    if kind=='hypr':
        def helper(match):
            name='tam-'+match.group(1)
            if name not in commands: raise ValueError('No selected replacement for '+match.group(0))
            return name
        text=re.sub(r'\bomarchy-([a-z0-9]+(?:-[a-z0-9]+)*)\b',helper,text)
        # Scalar variable identifiers are generic configuration values, not
        # machine IDs. No output, path, partition or host identifier is changed.
        text=re.sub(r'\bomarchy_(monitor_scale|gdk_scale)\b',r'tamlinux_\1',text)
        if re.search('omarchy',text,re.I):
            raise ValueError('Manual review required for inherited Lua references')
        return text.encode()
    raise ValueError('Unknown conversion')


def converted_state(kind, before, commands, locations=None):
    data=base64.b64decode(before['bytes'],validate=True)
    if kind=='retire-hey':
        # Accept only the inherited template or its owned-command conversion.
        # Extra fields, actions, duplicate keys or custom Exec need review.
        lines=data.decode('utf-8').splitlines()
        fields={}
        if not lines or lines[0]!='[Desktop Entry]':
            raise ValueError('Custom HEY launcher requires explicit review')
        for line in lines[1:]:
            if not line: continue
            key,sep,value=line.partition('=')
            if not sep or key in fields:
                raise ValueError('Custom HEY launcher requires explicit review')
            fields[key]=value
        expected={'Version':'1.0','Name':'HEY','Terminal':'false','Type':'Application',
                  'Icon':'hey','StartupNotify':'true','MimeType':'x-scheme-handler/mailto'}
        command=fields.pop('Exec',None)
        if fields!=expected or command not in ('omarchy-webapp-handler-hey %u','tam-webapp-handler-hey %u'):
            raise ValueError('Custom HEY launcher requires explicit review')
        return {'kind':'absent'}
    content=convert(kind,data,commands,locations)
    if content is None: return None
    return {'kind':'file','mode':before['mode'],'bytes':base64.b64encode(content).decode()}


def candidates(manifest, locations):
    for item in manifest['paths']:
        root=locations[item['root']]
        if item['id']=='webapps':
            for source in sorted((root/'applications').glob('*.desktop')):
                if source.name=='HEY.desktop': continue  # Explicit retirement owns this path.
                yield item,source,source
        elif '*' in item['source']:
            for source in sorted(root.glob(item['source'])):
                yield item,source,source
        else: yield item,root/item['source'],root/item['target']


def selected_commands():
    # Installed commands or the maintained source tree; never the caller's PATH.
    prefix=HERE.parents[2]
    directory=prefix/'bin'
    if directory.is_dir(): return {p.name for p in directory.iterdir()}
    return {p.name for p in (HERE.parents[1]/'commands').iterdir() if p.is_dir()}


def prepare(locations, directory, only=None):
    manifest=json.loads((HERE/'paths.json').read_text())
    rows=[]; conflicts=[]; commands=selected_commands()
    for item,source,target in candidates(manifest,locations):
        if only is not None and item['id'] != only: continue
        before_source=snapshot(source)
        if before_source['kind']=='absent': continue
        if before_source['kind']!='file':
            conflicts.append({'id':item['id'],'path':str(source),'reason':'Link requires explicit review; original preserved'}); continue
        try: post=converted_state(item['conversion'],before_source,commands,locations)
        except (ValueError,KeyError,TypeError,UnicodeError) as error:
            conflicts.append({'id':item['id'],'path':str(source),'reason':str(error)});continue
        if post is None: continue
        pre=snapshot(target)
        if source!=target and pre['kind']!='absent' and pre!=post:
            conflicts.append({'id':item['id'],'path':str(target),'reason':'Existing destination differs; neither file changed'});continue
        if pre==post: continue
        rows.append({'id':item['id'],'source':str(source),'target':str(target),'sourceBefore':before_source,
                     'before':pre,'after':post,'status':'prepared'})
    directory.mkdir(mode=0o700,parents=True,exist_ok=False)
    doc={'schema':1,'manifestSHA256':hashlib.sha256((HERE/'paths.json').read_bytes()).hexdigest(),
         'roots':{k:str(v) for k,v in locations.items()},'status':'blocked' if conflicts else 'prepared',
         'rows':rows,'conflicts':conflicts,'scope':manifest['scope']}
    save(directory/'journal.json',doc)
    return doc


def load(directory, locations):
    record=snapshot(directory/'journal.json')
    if record['kind']!='file': raise ValueError('Missing private migration journal')
    doc=json.loads(base64.b64decode(record['bytes']))
    if doc.get('schema')!=1 or doc.get('roots')!={k:str(v) for k,v in locations.items()}:
        raise ValueError('Journal roots do not match this user')
    manifest=json.loads((HERE/'paths.json').read_text())
    if doc.get('manifestSHA256')!=hashlib.sha256((HERE/'paths.json').read_bytes()).hexdigest():
        raise ValueError('Migration manifest changed')
    permitted={(item['id'],str(a),str(b)) for item,a,b in candidates(manifest,locations)}
    for row in doc['rows']:
        if (row['id'],row['source'],row['target']) not in permitted:
            raise ValueError('Journal contains an unlisted destination')
        expected=converted_state(next(x['conversion'] for x in manifest['paths'] if x['id']==row['id']),
                                 row['sourceBefore'],selected_commands(),locations)
        if expected is None or row['after']!=expected:
            raise ValueError('Converted state does not match selected rules')
    return doc


def apply(directory, locations, stop_after=None):
    doc=load(directory,locations)
    if doc['conflicts'] or doc['status'] in ('rolled-back','rolling-back'):
        raise ValueError('Resolve conflicts with a new plan before applying')
    # Check the complete batch first. A modified destination/source never gets
    # overwritten by an old plan, including an interrupted previous attempt.
    for row in doc['rows']:
        actual=snapshot(Path(row['target']))
        if actual not in (row['before'],row['after']): raise ValueError('Destination changed since planning')
        if row['source']!=row['target'] and snapshot(Path(row['source']))!=row['sourceBefore']:
            raise ValueError('Source changed since planning')
    doc['status']='applying'; save(directory/'journal.json',doc)
    for index,row in enumerate(doc['rows']):
        target=Path(row['target'])
        if snapshot(target)!=row['after']:
            row['status']='writing'; save(directory/'journal.json',doc)
            atomic(target,row['after'])
        row['status']='applied'; save(directory/'journal.json',doc)
        if stop_after is not None and index+1>=stop_after: return doc
    doc['status']='applied';save(directory/'journal.json',doc);return doc


def rollback(directory, locations):
    doc=load(directory,locations);doc['status']='rolling-back';save(directory/'journal.json',doc)
    for index,row in reversed(list(enumerate(doc['rows']))):
        if row['status'] in ('prepared','restored'): continue
        target=Path(row['target']); actual=snapshot(target)
        if actual!=row['before']:
            # Archive the exact later file or link before restoring the prior
            # destination. A retry never deletes an existing recovery record.
            archive=directory/'new-writes'/str(index)
            archive.mkdir(parents=True,mode=0o700,exist_ok=True)
            saved=archive/(hashlib.sha256(json.dumps(actual,sort_keys=True).encode()).hexdigest()+'.json')
            if not saved.exists(): save(saved,{'path':str(target),'state':actual})
            row['status']='restoring';save(directory/'journal.json',doc)
            atomic(target,row['before'])
        row['status']='restored';save(directory/'journal.json',doc)
    doc['status']='rolled-back';save(directory/'journal.json',doc);return doc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','apply','rollback','status','preserve','restore','checkpoint-status'])
    parser.add_argument('journal',type=Path)
    parser.add_argument('--only', choices=['imv-escape'], help='Plan only the imv Escape binding migration')
    parser.add_argument('--audio', action='store_true', help='Include owned tuning service, connected audio volumes/mutes and defaults')
    parser.add_argument('--audio-state', action='store_true', help='Separate persistent WirePlumber state checkpoint; requires WirePlumber stopped')
    parser.add_argument('--gtk', action='store_true', help='Include the four owned GTK user values through dconf')
    parser.add_argument('--settings-source',type=Path,action='append',default=[],help='Repeat for each absolute source config root; same finite config paths, at most eight roots')
    parser.add_argument('--claude-root',type=Path,help='Claude configuration root; defaults to a configured CLAUDE_CONFIG_DIR')
    parser.add_argument('--t3code-root',type=Path,help='T3 Code root; defaults to a configured T3CODE_HOME')
    parser.add_argument('--obsidian-vault',type=Path,action='append',default=[],help='Explicit Obsidian vault root; only its Tamlinux theme is checkpointed')
    args=parser.parse_args(); locations=roots(os.environ)
    if args.only and args.action != 'plan': parser.error('--only applies to plan; apply and rollback use the journal')
    base=locations['state']/'tamlinux/migration';safe(base);base.mkdir(parents=True,mode=0o700,exist_ok=True)
    directory=args.journal.absolute()
    if directory.parent!=base or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}',directory.name):
        parser.error('Journal must be a named directory immediately under $XDG_STATE_HOME/tamlinux/migration')
    descriptor=os.open(base/'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(descriptor,fcntl.LOCK_EX)
        if args.action in ('preserve','restore','checkpoint-status'):
            spec=importlib.util.spec_from_file_location('settings_recovery',HERE/'recovery.py')
            recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
            checkpoint_roots={**locations,'home':Path(os.environ['HOME'])}
            if len(args.settings_source)>recovery.MAX_SETTINGS_SOURCES or len(set(args.settings_source))!=len(args.settings_source):
                raise ValueError('Expected at most eight distinct settings source roots')
            for index,path in enumerate(sorted(args.settings_source)):
                if not path.is_absolute() or '..' in path.parts: raise ValueError('Settings source roots must be absolute without parent traversal')
                checkpoint_roots['settingsSource'+(str(index) if index else '')]=path
            for kind,explicit,variable in [('claude',args.claude_root,'CLAUDE_CONFIG_DIR'),('t3code',args.t3code_root,'T3CODE_HOME')]:
                value=explicit or os.environ.get(variable)
                if value:
                    path=Path(value)
                    if not path.is_absolute() or '..' in path.parts: raise ValueError('Application roots must be absolute without parent traversal')
                    checkpoint_roots[kind]=path
            if len(args.obsidian_vault)>recovery.MAX_VAULTS or len(set(args.obsidian_vault))!=len(args.obsidian_vault):
                raise ValueError('Expected at most 32 distinct Obsidian vault roots')
            for index,path in enumerate(sorted(args.obsidian_vault)):
                if not path.is_absolute() or '..' in path.parts: raise ValueError('Vault roots must be absolute without parent traversal')
                checkpoint_roots['obsidianVault'+str(index)]=path
            dconf=shutil.which('dconf') if args.gtk else None
            if args.gtk and not dconf: raise ValueError('GTK recovery requires the delivered dconf client')
            audio={name:shutil.which(name) for name in ('systemctl','pactl')} if args.audio else None
            if args.audio and not all(audio.values()): raise ValueError('Audio recovery requires delivered systemctl and pactl clients')
            audio_state=shutil.which('systemctl') if args.audio_state else None
            if args.audio_state and (not audio_state or args.audio or args.gtk or args.settings_source or args.claude_root or args.t3code_root or args.obsidian_vault):
                raise ValueError('Persistent audio requires systemctl and its own checkpoint without settings options')
            if args.action=='preserve': doc=recovery.preserve(checkpoint_roots,directory,dconf,audio,audio_state=audio_state)
            elif args.action=='restore': doc=recovery.restore(checkpoint_roots,directory,dconf,audio=audio,audio_state=audio_state)
            else: doc=recovery.load(directory,checkpoint_roots,audio_state=args.audio_state)
            print(json.dumps({'status':doc['status'],'files':len(doc['files']),
                'gtkCaptured':doc['gtk'] is not None,'audioCaptured':doc.get('audio') is not None,'audioStateCaptured':doc.get('selection')=='audio-state','journal':str(directory),
                'scope':doc['scope'],'externalOwners':doc['externalOwners']}))
            return 0
        if args.audio or args.audio_state or args.gtk or args.settings_source or args.claude_root or args.t3code_root or args.obsidian_vault:
            raise ValueError('Checkpoint options are only valid for settings checkpoint actions')
        refresh=None
        if args.action in ('apply','rollback'):
            pending=load(directory,locations)
            if any(row['id']=='webapps' or row['id'].startswith('retire-hey') for row in pending['rows']):
                refresh=shutil.which('update-desktop-database')
                if not refresh: raise ValueError('Launcher migration requires update-desktop-database')
        if args.action=='plan': doc=prepare(locations,directory,args.only)
        elif args.action=='apply': doc=apply(directory,locations)
        elif args.action=='rollback': doc=rollback(directory,locations)
        else: doc=load(directory,locations)
        if refresh and (locations['data']/'applications').is_dir():
            subprocess.run([refresh,str(locations['data']/'applications')],check=True)
        print(json.dumps({'status':doc['status'],'rows':len(doc['rows']),
                          'conflicts':doc['conflicts'],'journal':str(directory),'scope':doc['scope']}))
        return 1 if doc['conflicts'] else 0
    finally: os.close(descriptor)


if __name__=='__main__':
    import sys
    try: sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as error:
        sys.exit('tam-migrate-desktop: '+str(error))
