#!/usr/bin/python3
"""Fixed native DNS checkpoints; archive later values before explicit restore."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

BASE = Path('/var/lib/tamlinux/network-recovery')
FILES = (Path('/etc/NetworkManager/conf.d/20-tamlinux-dns.conf'), Path('/etc/systemd/resolved.conf'))
FIELDS = ('ipv4.ignore-auto-dns', 'ipv4.dns', 'ipv6.ignore-auto-dns', 'ipv6.dns')
TYPES = ('802-3-ethernet', '802-11-wireless')
UNITS = ('NetworkManager.service', 'systemd-resolved.service')
UUID = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}')
MAX_FILE = 128 * 1024
MAX_RECORD = 4 * 1024 * 1024


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def trusted(path, uid, private=False):
    info = path.lstat()
    if info.st_uid != uid or stat.S_ISLNK(info.st_mode) or stat.S_IMODE(info.st_mode) > 0o777:
        raise ValueError('Untrusted DNS recovery/settings object')
    if private and (not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077):
        raise ValueError('DNS recovery directory must be private')
    return info


def parents(path):
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Redirected DNS recovery/settings parent')


def read(path, uid, limit=MAX_RECORD):
    parents(path)
    info = trusted(path, uid)
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError('Expected bounded regular DNS file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        actual = os.fstat(fd)
        with os.fdopen(fd, 'rb', closefd=False) as file:
            data = file.read(limit + 1)
        after = os.fstat(fd)
        if ((info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino)
                or (actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns)
                != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                or len(data) != actual.st_size or len(data) > limit):
            raise ValueError('DNS file changed during capture')
        return data
    finally:
        os.close(fd)


def sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish(path, data, mode=0o600, gid=None):
    parents(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.dns-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
            if gid is not None:
                os.fchown(file.fileno(), -1, gid)
            os.fchmod(file.fileno(), mode)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        sync(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def save(path, value):
    data = encoded(value) + b'\n'
    if len(data) > MAX_RECORD:
        raise ValueError('DNS record exceeds limit')
    publish(path, data)


def directory(base=BASE, uid=0):
    parents(base)
    base.mkdir(parents=True, mode=0o700, exist_ok=True)
    trusted(base, uid, True)
    lock = base / '.lock'
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(descriptor).st_uid != uid or not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('Untrusted DNS lock')
    finally:
        os.close(descriptor)
    return base


def snapshot(path, uid):
    parents(path)
    if not path.exists() and not path.is_symlink():
        return {'present': False}
    info = trusted(path, uid)
    data = read(path, uid, MAX_FILE)
    return {'present': True, 'bytes': base64.b64encode(data).decode(), 'sha256': digest(data),
            'mode': stat.S_IMODE(info.st_mode), 'gid': info.st_gid}


class Provider:
    def run(self, tool, *args, check=True):
        return subprocess.run(['/usr/bin/' + tool, *args], check=check, capture_output=True,
                              text=True, timeout=30, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})

    def profiles(self):
        rows = self.run('nmcli', '-t', '-e', 'no', '-f', 'UUID,TYPE', 'connection', 'show').stdout.splitlines()
        result = {}
        for row in rows:
            uuid, separator, kind = row.partition(':')
            if not separator or not UUID.fullmatch(uuid) or uuid in result:
                raise ValueError('Invalid native connection inventory')
            if kind not in TYPES:
                continue
            fields = {field: self.run('nmcli', '-e', 'no', '-g', field, 'connection', 'show', 'uuid', uuid).stdout.rstrip('\n')
                      for field in FIELDS}
            result[uuid] = {'type': kind, 'fields': fields}
            if len(result) > 256:
                raise ValueError('DNS connection limit exceeded')
        return result

    def profile(self, uuid):
        kind = self.run('nmcli', '-g', 'connection.type', 'connection', 'show', 'uuid', uuid).stdout.strip()
        return {'type': kind, 'fields': {
            field: self.run('nmcli', '-e', 'no', '-g', field, 'connection', 'show', 'uuid', uuid).stdout.rstrip('\n')
            for field in FIELDS}}

    def units(self):
        result = {unit: self.run('systemctl', 'is-active', unit, check=False).stdout.strip() for unit in UNITS}
        if any(value not in ('active', 'inactive') for value in result.values()):
            raise ValueError('Required native DNS service owner is unavailable')
        return result

    def modify(self, uuid, fields):
        arguments = [item for field in FIELDS for item in (field, fields[field])]
        self.run('nmcli', 'connection', 'modify', 'uuid', uuid, *arguments)

    def reload(self, units):
        if units['NetworkManager.service'] == 'active':
            self.run('nmcli', 'general', 'reload', 'conf')
            rows = self.run('nmcli', '-t', '-e', 'no', '-f', 'DEVICE,TYPE,STATE', 'device', 'status').stdout.splitlines()
            for row in rows:
                parts = row.split(':')
                if len(parts) != 3:
                    raise ValueError('Invalid native device inventory')
                device, kind, state = parts
                if kind in ('wifi', 'ethernet') and state == 'connected':
                    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', device):
                        raise ValueError('Invalid native device name')
                    self.run('nmcli', 'device', 'reapply', device)
        if units['systemd-resolved.service'] == 'active':
            self.run('systemctl', 'reload-or-restart', 'systemd-resolved.service')
        elif self.units()['systemd-resolved.service'] == 'active':
            self.run('systemctl', 'stop', 'systemd-resolved.service')
        if units['NetworkManager.service'] == 'active':
            self.run('nmcli', 'general', 'reload', 'dns-full')


def validate(value, files):
    if not isinstance(value, dict) or set(value) != {'files', 'profiles', 'units'} or set(value['files']) != {str(p) for p in files}:
        raise ValueError('Unlisted native DNS destination')
    for item in value['files'].values():
        if item == {'present': False}:
            continue
        if (set(item) != {'present', 'bytes', 'sha256', 'mode', 'gid'} or item['present'] is not True
                or type(item['mode']) is not int or not 0 <= item['mode'] <= 0o777
                or type(item['gid']) is not int or not 0 <= item['gid'] < 2**32):
            raise ValueError('Invalid native DNS file state')
        data = base64.b64decode(item['bytes'], validate=True)
        if len(data) > MAX_FILE or digest(data) != item['sha256']:
            raise ValueError('DNS original bytes failed verification')
    if not isinstance(value['profiles'], dict) or len(value['profiles']) > 256:
        raise ValueError('Invalid DNS connection inventory')
    for uuid, row in value['profiles'].items():
        if not UUID.fullmatch(uuid) or set(row) != {'type', 'fields'} or row['type'] not in TYPES or set(row['fields']) != set(FIELDS):
            raise ValueError('Invalid DNS connection fields')
        for name, text in row['fields'].items():
            if not isinstance(text, str) or len(text) > 8192 or any(c in text for c in '\0\r\n'):
                raise ValueError('Invalid bounded DNS value')
            if name.endswith('ignore-auto-dns') and text not in ('yes', 'no'):
                raise ValueError('Invalid DNS automatic setting')
    if set(value['units']) != set(UNITS) or any(v not in ('active', 'inactive') for v in value['units'].values()):
        raise ValueError('Invalid native DNS service state')


def observe(files, provider, uid):
    result = {'files': {str(p): snapshot(p, uid) for p in files},
              'profiles': provider.profiles(), 'units': provider.units()}
    validate(result, files)
    return result


def preserve(base=BASE, files=FILES, provider=None, uid=0):
    provider = provider or Provider()
    base = directory(base, uid)
    before = observe(files, provider, uid)
    if observe(files, provider, uid) != before:
        raise ValueError('DNS settings changed during capture; stop writers and retry')
    journal = Path(tempfile.mkdtemp(prefix='dns.', dir=base))
    doc = {'schema': 1, 'kind': 'dns-checkpoint', 'before': before,
           'beforeSha256': digest(encoded(before))}
    save(journal / 'checkpoint.json', doc)
    # The setter consumes this fixed inventory, not arbitrary recovery commands.
    publish(journal / 'connections.tsv', ''.join(f"{uuid}:{row['type']}\n" for uuid,row in before['profiles'].items()).encode())
    return journal


def load(journal, base, files, uid):
    if journal.parent != base or not re.fullmatch(r'dns\.[A-Za-z0-9_-]{6,32}', journal.name):
        raise ValueError('Expected a named DNS checkpoint under the fixed recovery directory')
    parents(journal)
    trusted(journal, uid, True)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate DNS recovery field')
            result[key] = value
        return result
    doc = json.loads(read(journal / 'checkpoint.json', uid), object_pairs_hook=pairs)
    if doc.get('schema') != 1 or doc.get('kind') != 'dns-checkpoint' or digest(encoded(doc['before'])) != doc.get('beforeSha256'):
        raise ValueError('Invalid or changed original DNS checkpoint')
    validate(doc['before'], files)
    return doc


def restore(journal, base=BASE, files=FILES, provider=None, uid=0):
    provider = provider or Provider()
    doc = load(journal, base, files, uid)
    original = doc['before']
    current = observe(files, provider, uid)
    for uuid, row in original['profiles'].items():
        if uuid not in current['profiles'] or current['profiles'][uuid]['type'] != row['type']:
            raise ValueError('Original NetworkManager connection is missing or has changed type')
    archive = journal / ('later-' + digest(encoded(current)) + '.json')
    later = {'schema': 1, 'state': current}
    if archive.exists() or archive.is_symlink():
        if json.loads(read(archive, uid)) != later:
            raise ValueError('Existing later DNS archive is corrupt; no settings changed')
    else:
        save(archive, later)
    save(journal / 'restore.json', {'schema': 1, 'status': 'restoring'})
    # Refuse a concurrent writer before changing any selected native settings.
    if observe(files, provider, uid) != current:
        raise ValueError('DNS settings changed after archival; retry to preserve the newer values')
    for path in files:
        if snapshot(path, uid) != current['files'][str(path)]:
            raise ValueError('DNS file changed after archival; retry to preserve its newer values')
        item = original['files'][str(path)]
        if item['present']:
            publish(path, base64.b64decode(item['bytes'], validate=True), item['mode'], item['gid'])
        elif path.exists():
            path.unlink()
            sync(path.parent)
    for uuid, row in original['profiles'].items():
        if provider.profile(uuid) != current['profiles'][uuid]:
            raise ValueError('DNS connection changed after archival; retry to preserve its newer values')
        provider.modify(uuid, row['fields'])
    provider.reload(original['units'])
    after = observe(files, provider, uid)
    if after['files'] != original['files'] or after['units'] != original['units'] or any(
            after['profiles'].get(uuid) != row for uuid, row in original['profiles'].items()):
        raise ValueError('DNS restore did not reach the recorded settings; original and later values remain saved')
    save(journal / 'restore.json', {'schema': 1, 'status': 'restored'})
    return {'status': 'restored', 'journal': str(journal), 'laterValuesArchived': True}


def main():
    if os.getuid() != 0:
        raise ValueError('Native DNS recovery requires explicit root authorization')
    action, *args = sys.argv[1:]
    if action == 'directory' and not args:
        print(directory())
    elif action == 'preserve' and not args:
        print(preserve())
    elif action == 'restore' and len(args) == 1:
        print(json.dumps(restore(Path(args[0]))))
    else:
        raise ValueError('Expected directory, preserve, or restore CHECKPOINT')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        sys.exit('tam-dns: ' + str(error))
