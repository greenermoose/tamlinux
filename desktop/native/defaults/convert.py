#!/usr/bin/python3
"""Explicit, checkpointed native defaults. Never run from a package hook.

The CLI uses fixed host paths and requires root. Stop configuration writers
before apply/restore; reload services separately after inspecting the result.
plan is read-only. A checkpoint label is single-use, including after rollback.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
RECOVERY = HERE / 'native_recovery.py'
if not RECOVERY.exists():
    RECOVERY = HERE.parents[1] / 'migration/recovery.py'
spec = importlib.util.spec_from_file_location('native_file_recovery', RECOVERY)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

HOSTS = 'mymachines mdns_minimal [NOTFOUND=return] resolve files myhostname dns'
ARCH_HOSTS = ('mymachines resolve [!UNAVAIL=return] files myhostname dns',
              'mymachines resolve [!UNAVAIL=return] files myhostname dns myhostname',
              'files mymachines myhostname resolve [!UNAVAIL=return] dns')
DOCKER = {'log-driver': 'json-file', 'log-opts': {'max-size': '10m', 'max-file': '5'},
          'dns': ['172.17.0.1'], 'bip': '172.17.0.1/16'}
PAIRED = {
    'sudoers.d/70-tamlinux-passwd-tries': ('Defaults passwd_tries=10\n', 0o440),
    'systemd/resolved.conf.d/10-tamlinux-multicast.conf': ('[Resolve]\nLLMNR=no\nMulticastDNS=no\n', 0o644),
    'systemd/resolved.conf.d/20-tamlinux-docker-dns.conf': ('[Resolve]\nDNSStubListenerExtra=172.17.0.1\n', 0o644),
}
PATHS = ['security/faillock.conf', 'nsswitch.conf', 'cups/cups-files.conf',
         'docker/daemon.json', *PAIRED]
MANIFEST = {'schema': 1, 'scope': 'Native authentication, NSS, CUPS and Docker paired defaults',
            'paths': [{'root': 'config', 'path': p, 'exclude': []} for p in PATHS],
            'applicationRoots': {}, 'gtkKeys': [],
            'externalOwners': ['Services, packages, boot and user settings are separate transactions.']}


class Manifest:
    def read_text(self):
        return json.dumps(MANIFEST, sort_keys=True)

    def read_bytes(self):
        return self.read_text().encode()


r.MANIFEST = Manifest()


def inspect(path):
    r.parents(path)
    for parent in path.parents:
        if parent.name == 'etc':
            break
        if parent.exists():
            info = r.trusted(parent)
            if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o022:
                raise ValueError('Untrusted native config parent: ' + str(parent))
    if not path.exists() and not path.is_symlink():
        return {'kind': 'absent'}
    info = r.trusted(path)
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
        raise ValueError('Expected an owned, non-writable regular config: ' + str(path))
    data = r.read(path, 1024 * 1024)
    return {'kind': 'file', 'sha256': r.digest(data), 'mode': stat.S_IMODE(info.st_mode),
            'uid': info.st_uid, 'gid': info.st_gid}


def setting(text, key, value, accepted, separator=' = '):
    pattern = re.compile(r'^\s*' + re.escape(key) + r'(?:\s*=\s*|\s+)([^#\n]+?)[ \t]*(?:#.*)?$', re.M)
    matches = list(pattern.finditer(text))
    if len(matches) > 1 or any(m.group(1).strip() not in (*accepted, value) for m in matches):
        raise ValueError('Administrator setting conflicts: ' + key)
    if matches:
        if matches[0].group(1).strip() == value:
            return text
        return pattern.sub(lambda _: key + separator + value, text)
    return text + ('' if not text or text.endswith('\n') else '\n') + key + separator + value + '\n'


def plan(root):
    """Check every destination before a checkpoint or config write."""
    etc = root / 'etc'
    before = {p: inspect(etc / p) for p in PATHS}
    after = {}
    def text(p, required=False):
        if before[p]['kind'] == 'absent':
            if required:
                raise ValueError('Required Arch configuration missing: ' + p)
            return ''
        return r.read(etc / p, 1024 * 1024).decode('utf-8')

    after['security/faillock.conf'] = setting(text('security/faillock.conf', True), 'deny', '10', ('3',))
    nss = text('nsswitch.conf', True)
    lines = re.findall(r'^hosts:\s*(.*?)\s*$', nss, re.M)
    if len(lines) != 1 or ' '.join(lines[0].split()) not in (HOSTS, *ARCH_HOSTS):
        raise ValueError('Administrator hosts line conflicts; review NSS before conversion')
    after['nsswitch.conf'] = re.sub(r'^hosts:.*$', 'hosts: ' + HOSTS, nss, flags=re.M)
    if before['cups/cups-files.conf']['kind'] != 'absent':
        cups = text('cups/cups-files.conf')
        # Arch cups owns uid/gid 209. Preserve the old optional discovery group.
        for key, value, accepted in [('User', '209', ('cups', 'daemon')),
                                     ('Group', '209', ('cups', 'lp')),
                                     ('PeerCred', 'on', ('yes',))]:
            cups = setting(cups, key, value, accepted, ' ')
        if not re.search(r'^SystemGroup\s+cups-browsed sys root\s*$', cups, re.M):
            cups = setting(cups, 'SystemGroup', 'sys root', ('sys', 'root', 'lpadmin'), ' ')
        after['cups/cups-files.conf'] = cups
    docker = json.loads(text('docker/daemon.json') or '{}')
    if not isinstance(docker, dict):
        raise ValueError('Docker config must be an object')
    for key, value in DOCKER.items():
        if key in docker and docker[key] != value:
            raise ValueError('Administrator Docker setting conflicts: ' + key)
        docker[key] = value
    after['docker/daemon.json'] = json.dumps(docker, indent=2, sort_keys=True) + '\n'
    for p, (value, _) in PAIRED.items():
        if before[p]['kind'] != 'absent' and text(p) != value:
            raise ValueError('Existing Tamlinux pair conflicts: ' + p)
        after[p] = value
    changes = {}
    for p, value in after.items():
        old = before[p]
        mode = old.get('mode', PAIRED.get(p, ('', 0o644))[1])
        target = {'kind': 'file', 'sha256': r.digest(value.encode()), 'mode': mode,
                  'uid': old.get('uid', os.getuid()), 'gid': old.get('gid', os.getgid())}
        changes[p] = {'before': old, 'after': target, 'text': value}
    return {'schema': 1, 'root': str(root), 'changes': changes,
            'skipped': [p for p in PATHS if p not in changes]}


def apply(root, checkpoint, stop_after=None):
    locations = {'config': root / 'etc', 'home': root / 'root'}
    journal = checkpoint / 'conversion.json'
    if not checkpoint.exists():
        selected = plan(root)
        # Capture originals before publishing the plan or changing a file.
        r.preserve(locations, checkpoint)
        r.save(journal, selected)
    saved = r.load(checkpoint, locations)
    if not journal.exists():
        # A crash after preserve but before plan publication changed no config.
        if saved['status'] != 'preserved' or r.capture(saved['entries'], checkpoint / 'blobs') != saved['files']:
            raise ValueError('Incomplete checkpoint requires inspection')
        r.save(journal, plan(root))
    selected = json.loads(r.read(journal, r.MAX_RECORD))
    if saved['status'] != 'preserved' or selected['root'] != str(root):
        raise ValueError('Checkpoint has been restored or belongs to another root')
    # Interrupted retry accepts only original or exactly installed identities.
    for p, item in selected['changes'].items():
        if inspect(root / 'etc' / p) not in (item['before'], item['after']):
            raise ValueError('Configuration changed since checkpoint: ' + p)
    for index, (p, item) in enumerate(selected['changes'].items(), 1):
        destination = root / 'etc' / p
        if inspect(destination) == item['after']:
            continue
        # Keep conventional parent permissions for new config directories.
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        r.publish(destination, item['text'].encode(), item['after']['mode'])
        os.chown(destination, item['after']['uid'], item['after']['gid'])
        if inspect(destination) != item['after']:
            raise ValueError('Installed default differs: ' + p)
        if stop_after == index:
            raise InterruptedError('Injected conversion interruption')
    return selected


def restore(root, checkpoint):
    selected = json.loads(r.read(checkpoint / 'conversion.json', r.MAX_RECORD))
    if selected['root'] != str(root):
        raise ValueError('Checkpoint root differs')
    # Retain later uid/gid as well as the engine's bytes and mode archive.
    import time
    r.save(checkpoint / 'native-new-writes' / str(time.time_ns()),
           {p: inspect(root / 'etc' / p) for p in PATHS})
    # The recovery engine archives every current file before restoring originals.
    result = r.restore({'config': root / 'etc', 'home': root / 'root'}, checkpoint)
    for p, item in selected['changes'].items():
        if item['before']['kind'] == 'file':
            os.chown(root / 'etc' / p, item['before']['uid'], item['before']['gid'])
        if inspect(root / 'etc' / p) != item['before']:
            raise ValueError('Restored config identity differs: ' + p)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'apply', 'restore', 'status'])
    parser.add_argument('label', nargs='?')
    args = parser.parse_args()
    if os.getuid() != 0:
        parser.error('Root required; this command accepts no caller-supplied file paths')
    if args.action != 'plan' and (not args.label or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}', args.label)):
        parser.error('A bounded checkpoint label is required')
    lock = os.open('/run/lock/tamlinux-native-defaults.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(lock).st_uid != 0 or not stat.S_ISREG(os.fstat(lock).st_mode):
            raise ValueError('Invalid native lock')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root = Path('/')
        checkpoint = Path('/var/lib/tamlinux/native-defaults') / (args.label or 'unused')
        if args.action == 'plan':
            result = plan(root)
        elif args.action == 'apply':
            result = apply(root, checkpoint)
        elif args.action == 'restore':
            result = restore(root, checkpoint)
        else:
            result = r.load(checkpoint, {'config': root / 'etc', 'home': root / 'root'})
        print(json.dumps(result, sort_keys=True))
    finally:
        os.close(lock)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        sys.exit('Native defaults refused: ' + str(error))
