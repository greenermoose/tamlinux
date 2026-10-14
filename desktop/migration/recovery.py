#!/usr/bin/env python3
"""Finite user-settings checkpoints; preserve later writes before restoring.

Stop settings writers before preserve/restore. Links are saved without following
them. Home Manager links restore identity; generation retention remains separate.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

MANIFEST = Path(__file__).with_name('recovery-paths.json')
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_ENTRIES = 20000
MAX_RECORD = 16 * 1024 * 1024
MAX_VAULTS = 32


def digest(data):
    return hashlib.sha256(data).hexdigest()


def trusted(path, directory=False):
    info = path.lstat()
    if info.st_uid != os.getuid():
        raise ValueError('Recovery owner mismatch: ' + str(path))
    if directory and (not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077):
        raise ValueError('Recovery directory must be private: ' + str(path))
    return info


def parents(path):
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Redirected settings parent: ' + str(path))


def publish(path, data, mode=0o600):
    parents(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.tamlinux-recovery-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            os.fchmod(handle.fileno(), mode)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        sync(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def sync(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, doc):
    data = (json.dumps(doc, indent=2, sort_keys=True) + '\n').encode()
    if len(data) > MAX_RECORD:
        raise ValueError('Recovery record exceeds limit')
    publish(path, data)


def read(path, limit):
    parents(path)
    info = trusted(path)
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError('Expected bounded regular recovery/settings file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        actual = os.fstat(fd)
        if (actual.st_dev, actual.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError('File changed while opening')
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            data = handle.read(limit + 1)
        after = os.fstat(fd)
        if len(data) > limit or (actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('File changed while reading')
        return data
    finally:
        os.close(fd)


def relative(value):
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts or str(path) != value:
        raise ValueError('Invalid relative recovery path')
    return path


def selections(locations):
    manifest = json.loads(MANIFEST.read_text())
    entries = []
    selected = list(manifest['paths'])
    if 'settingsSource' in locations:
        selected += [{**item, 'root': 'settingsSource'} for item in manifest['paths'] if item['root'] == 'config']
    for name, root in locations.items():
        if name in ('claude', 't3code'):
            default = locations['home'] / ('.claude' if name == 'claude' else '.t3')
            if root == default:
                continue  # The standard HOME paths already cover this root.
            application = name
        elif re.fullmatch(r'obsidianVault(?:[0-9]|[12][0-9]|3[01])', name):
            application = 'obsidianVault'
        else:
            continue
        selected += [{'root': name, 'path': path, 'exclude': []}
                     for path in manifest['applicationRoots'][application]]
    for item in selected:
        root = locations[item['root']]
        if not root.is_absolute():
            raise ValueError('Recovery roots must be absolute')
        if '..' in root.parts:
            raise ValueError('Recovery roots must not contain parent traversal')
        path = root / relative(item['path'])
        excluded = [str(path / relative(value)) for value in item['exclude']]
        entries.append({'path': str(path), 'exclude': excluded})
    paths = [Path(item['path']) for item in entries]
    if any(a == b or a in b.parents or b in a.parents
           for i, a in enumerate(paths) for b in paths[i+1:]):
        raise ValueError('Recovery scopes overlap; select distinct HOME/XDG roots')
    return manifest, entries


def capture(entries, blobs):
    result = {}
    total = 0
    def visit(path, excluded):
        nonlocal total
        if str(path) in excluded:
            return
        if len(result) >= MAX_ENTRIES:
            raise ValueError('Settings entry limit exceeded')
        parents(path)
        if not path.exists() and not path.is_symlink():
            result[str(path)] = {'kind': 'absent'}
            return
        info = trusted(path)
        if not stat.S_ISLNK(info.st_mode) and stat.S_IMODE(info.st_mode) > 0o777:
            raise ValueError('Unsupported special settings permissions: ' + str(path))
        if stat.S_ISLNK(info.st_mode):
            result[str(path)] = {'kind': 'link', 'link': os.readlink(path)}
        elif stat.S_ISDIR(info.st_mode):
            if info.st_mode & 0o700 != 0o700:
                raise ValueError('Settings directory needs owner read/write/search permissions')
            result[str(path)] = {'kind': 'directory', 'mode': stat.S_IMODE(info.st_mode)}
            for child in sorted(path.iterdir()):
                visit(child, excluded)
        elif stat.S_ISREG(info.st_mode):
            data = read(path, MAX_FILE)
            total += len(data)
            if total > MAX_TOTAL:
                raise ValueError('Settings byte limit exceeded')
            key = digest(data)
            blob = blobs / key
            if not blob.exists():
                publish(blob, data)
            elif digest(read(blob, MAX_FILE)) != key:
                raise ValueError('Recovery blob was modified')
            result[str(path)] = {'kind': 'file', 'blob': key, 'mode': stat.S_IMODE(info.st_mode)}
        else:
            raise ValueError('Unsupported settings object: ' + str(path))
    for entry in entries:
        visit(Path(entry['path']), set(entry['exclude']))
    return result


def gtk_read(executable, keys):
    if not executable or not Path(executable).is_absolute():
        raise ValueError('GTK recovery requires an absolute dconf executable')
    values = {}
    for key in keys:
        value = subprocess.check_output([str(executable), 'read', key], text=True, timeout=15)
        if len(value) > 65536:
            raise ValueError('GTK value exceeds limit')
        values[key] = value.strip() or None
    return values


def preserve(locations, directory, dconf=None, audio=None):
    manifest, entries = selections(locations)
    parents(directory)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    trusted(directory, True)
    doc = {'schema': 1, 'kind': 'settings-checkpoint', 'status': 'collecting',
           'manifestSHA256': digest(MANIFEST.read_bytes()),
           'roots': {k: str(v) for k, v in locations.items()}, 'entries': entries,
           'scope': manifest['scope'], 'externalOwners': manifest['externalOwners']}
    save(directory / 'checkpoint.json', doc)
    doc['files'] = capture(entries, directory / 'blobs')
    # A managed link can lead to mutable checkout bytes. Retaining the link
    # alone would leave those bytes changed after rollback. Configuration
    # targets must be immutable or covered by this finite checkpoint.
    for name,value in doc['files'].items():
        path=Path(name)
        config_roots=[locations['config']]+([locations['settingsSource']] if 'settingsSource' in locations else [])
        config_roots += [locations['home']/'.claude', locations['home']/'.t3']
        config_roots += [root for key,root in locations.items()
                         if key in ('claude','t3code') or key.startswith('obsidianVault')]
        if value['kind']!='link' or not any(path.is_relative_to(root) for root in config_roots) or not path.exists():
            continue
        target=path.resolve()
        covered=any((target==Path(entry['path']) or Path(entry['path']) in target.parents)
                    and not any(target==Path(p) or Path(p) in target.parents for p in entry['exclude']) for entry in entries)
        if not target.is_relative_to('/nix/store') and not covered:
            raise ValueError('Mutable configuration link target is not covered by selected recovery roots: '+str(path))
    doc['gtk'] = gtk_read(dconf, manifest['gtkKeys']) if dconf else None
    doc['audio'] = audio_read(audio) if audio else None
    validate_files(doc['files'], entries, directory / 'blobs')
    doc['status'] = 'preserved'
    save(directory / 'checkpoint.json', doc)
    return doc


def validate_files(files, entries, blobs):
    if not isinstance(files, dict) or len(files) > MAX_ENTRIES:
        raise ValueError('Invalid recovery file inventory')
    for entry in entries:
        if entry['path'] not in files:
            raise ValueError('Missing selected recovery root')
    total = 0
    for name, value in files.items():
        path = Path(name)
        allowed = [entry for entry in entries if path == Path(entry['path'])
                   or Path(entry['path']) in path.parents]
        if len(allowed) != 1 or not path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError('Unlisted recovery destination')
        if any(path == Path(excluded) or Path(excluded) in path.parents
               for excluded in allowed[0]['exclude']):
            raise ValueError('Recovery record includes excluded journal')
        if path != Path(allowed[0]['path']):
            if files.get(str(path.parent), {}).get('kind') != 'directory':
                raise ValueError('Recovery parent is not a recorded directory')
        kind = value.get('kind')
        if kind in ('file', 'directory'):
            mode = value.get('mode')
            if type(mode) is not int or not 0 <= mode <= 0o777:
                raise ValueError('Invalid recovery permission mode')
        if kind == 'file':
            key = value.get('blob', '')
            if not re.fullmatch('[0-9a-f]{64}', key):
                raise ValueError('Invalid recovery blob')
            data = read(blobs / key, MAX_FILE)
            if digest(data) != key:
                raise ValueError('Recovery blob digest mismatch')
            total += len(data)
        elif kind == 'link':
            if not isinstance(value.get('link'), str) or '\0' in value['link']:
                raise ValueError('Invalid recovery link')
        elif kind not in ('directory', 'absent'):
            raise ValueError('Invalid recovery kind')
    if total > MAX_TOTAL:
        raise ValueError('Recovery bytes exceed limit')


def load(directory, locations):
    parents(directory)
    trusted(directory, True)
    doc = json.loads(read(directory / 'checkpoint.json', MAX_RECORD))
    manifest, entries = selections(locations)
    if (doc.get('schema') != 1 or doc.get('kind') != 'settings-checkpoint'
            or doc.get('manifestSHA256') != digest(MANIFEST.read_bytes())
            or doc.get('roots') != {k: str(v) for k, v in locations.items()}
            or doc.get('entries') != entries):
        raise ValueError('Checkpoint does not match selected user/manifest')
    if doc.get('status') not in ('preserved', 'restoring', 'restored'):
        raise ValueError('Checkpoint did not complete preservation')
    validate_files(doc['files'], entries, directory / 'blobs')
    if doc['gtk'] is not None and (not isinstance(doc['gtk'], dict)
            or set(doc['gtk']) != set(manifest['gtkKeys'])
            or any(v is not None and (not isinstance(v, str) or len(v) > 65536)
                   for v in doc['gtk'].values())):
        raise ValueError('Invalid GTK recovery inventory')
    audio_validate(doc.get('audio'))
    return doc


def restore(locations, directory, dconf=None, stop_after=None, audio=None):
    doc = load(directory, locations)
    current = capture(doc['entries'], directory / 'blobs')
    gtk = gtk_read(dconf, list(doc['gtk'])) if doc['gtk'] is not None else None
    audio_current = audio_read(audio) if doc.get('audio') is not None else None
    # Save the complete current tree before the first deletion/replacement.
    later = {'schema': 1, 'files': current, 'gtk': gtk, 'audio': audio_current}
    name = digest(json.dumps(later, sort_keys=True).encode()) + '.json'
    save(directory / 'new-writes' / name, later)
    doc['status'] = 'restoring'
    save(directory / 'checkpoint.json', doc)
    if audio_current is not None:
        if audio_read(audio) != audio_current:
            raise ValueError('Audio changed after archival; retry to preserve newer values')
        if audio_current['active'] == 'active':
            audio_call(audio, 'systemctl', '--user', 'stop', AUDIO_UNIT)
    original = doc['files']
    changes = 0
    def changed():
        nonlocal changes
        changes += 1
        return stop_after is not None and changes >= stop_after
    # Children first: never traverse a saved or newly introduced symlink.
    for name in sorted(current, key=lambda p: (-len(Path(p).parts), p)):
        old = current[name]
        desired = original.get(name, {'kind': 'absent'})
        if old == desired or old['kind'] == 'absent':
            continue
        if old['kind'] == 'directory' and desired['kind'] == 'directory':
            continue
        path = Path(name)
        parents(path)
        if old['kind'] == 'directory':
            info = trusted(path)
            observed = {'kind': 'directory', 'mode': stat.S_IMODE(info.st_mode)} if stat.S_ISDIR(info.st_mode) else None
        else:
            observed = capture([{'path': name, 'exclude': []}], directory / 'blobs')[name]
        if observed != old:
            raise ValueError('Settings changed after preservation; retry to archive the newer writes')
        if old['kind'] == 'directory':
            path.rmdir()  # Refuses an unobserved concurrent new file.
        else:
            path.unlink()
        sync(path.parent)
        if changed():
            return doc
    for name in sorted(original, key=lambda p: (len(Path(p).parts), p)):
        value = original[name]
        if value['kind'] == 'absent':
            continue
        path = Path(name)
        parents(path)
        if value['kind'] != 'directory':
            observed = capture([{'path': name, 'exclude': []}], directory / 'blobs')[name]
            if observed == value:
                continue
            if observed['kind'] != 'absent':
                raise ValueError('A new settings writer appeared during restoration; retry to archive its writes')
        if value['kind'] == 'directory':
            path.mkdir(parents=True, mode=0o700, exist_ok=True)
            path.chmod(value['mode'])
            sync(path.parent)
        elif value['kind'] == 'file':
            publish(path, read(directory / 'blobs' / value['blob'], MAX_FILE), value['mode'])
        else:
            path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            temporary = path.parent / ('.tamlinux-recovery-link-' + str(time.time_ns()))
            try:
                temporary.symlink_to(value['link'])
                os.replace(temporary, path)
                sync(path.parent)
            finally:
                temporary.unlink(missing_ok=True)
        if changed():
            return doc
    if doc['gtk'] is not None:
        latest = gtk_read(dconf, list(doc['gtk']))
        if latest != gtk:
            save(directory / 'new-writes' / (digest(json.dumps(latest, sort_keys=True).encode()) + '.json'),
                 {'schema': 1, 'files': {}, 'gtk': latest})
        for key, value in doc['gtk'].items():
            args = ['reset', key] if value is None else ['write', key, value]
            subprocess.run([str(dconf), *args], check=True, timeout=15)
        if gtk_read(dconf, list(doc['gtk'])) != doc['gtk']:
            raise ValueError('GTK restore did not reach recorded user values')
    if capture(doc['entries'], directory / 'blobs') != original:
        raise ValueError('Settings changed during restoration; originals and later writes remain saved')
    if audio_current is not None:
        audio_restore(audio, doc['audio'])
    doc['status'] = 'restored'
    save(directory / 'checkpoint.json', doc)
    return doc


AUDIO_UNIT = 'tamlinux-speaker-tuning.service'


def audio_call(tools, name, *args, negative=False):
    if not tools or set(tools) != {'systemctl', 'pactl'} or not all(
            Path(value).is_absolute() for value in tools.values()):
        raise ValueError('Audio recovery requires absolute systemctl and pactl providers')
    result = subprocess.run([str(tools[name]), *args], capture_output=True, text=True, timeout=20)
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError('Audio response exceeds limit')
    if result.returncode and not negative:
        raise ValueError('Audio provider refused ' + name + ' ' + args[0])
    return result.stdout.strip()


def audio_validate(doc):
    if doc is None:
        return
    if not isinstance(doc, dict) or set(doc) != {'unit', 'active', 'enabled', 'defaults', 'devices'}:
        raise ValueError('Invalid audio recovery inventory')
    if doc['unit'] != AUDIO_UNIT or doc['active'] not in ('active', 'inactive') or doc['enabled'] not in ('enabled', 'disabled', 'static', 'not-found'):
        raise ValueError('Unsupported tuning service state')
    if not isinstance(doc['defaults'], dict) or set(doc['defaults']) != {'sink', 'source'}:
        raise ValueError('Invalid audio default inventory')
    if not isinstance(doc['devices'], dict) or set(doc['devices']) != {'sink', 'source'}:
        raise ValueError('Invalid audio device inventory')
    for kind, devices in doc['devices'].items():
        if not isinstance(devices, dict) or not 1 <= len(devices) <= 128:
            raise ValueError('Expected bounded connected audio devices')
        if doc['defaults'][kind] not in devices:
            raise ValueError('Audio default is not a captured device')
        for name, value in devices.items():
            if not isinstance(name, str) or not name or name.startswith('-') or len(name) > 512 or any(c in name for c in '\0\n\r'):
                raise ValueError('Invalid audio device name')
            if not isinstance(value, dict) or set(value) != {'mute', 'volume'} or type(value['mute']) is not bool:
                raise ValueError('Invalid audio device settings')
            volume = value['volume']
            if not isinstance(volume, dict) or not 1 <= len(volume) <= 64 or any(
                    not isinstance(channel, str) or not channel or type(level) is not int or not 0 <= level <= 2147483647
                    for channel, level in volume.items()):
                raise ValueError('Unsupported audio channels/volume; preserve separately')


def audio_read(tools):
    active = audio_call(tools, 'systemctl', '--user', 'is-active', AUDIO_UNIT, negative=True)
    enabled = audio_call(tools, 'systemctl', '--user', 'is-enabled', AUDIO_UNIT, negative=True)
    devices = {}; defaults = {}
    for kind in ('sink', 'source'):
        rows = json.loads(audio_call(tools, 'pactl', '--format=json', 'list', kind + 's'))
        if not isinstance(rows, list) or len(rows) > 128:
            raise ValueError('Invalid audio provider device list')
        devices[kind] = {}
        for row in rows:
            name = row['name']
            if name in devices[kind]:
                raise ValueError('Duplicate audio device name')
            devices[kind][name] = {'mute': row['mute'], 'volume': {
                channel: value['value'] for channel, value in row['volume'].items()}}
        defaults[kind] = audio_call(tools, 'pactl', 'get-default-' + kind)
    doc = {'unit': AUDIO_UNIT, 'active': active, 'enabled': enabled,
           'defaults': defaults, 'devices': devices}
    audio_validate(doc)
    return doc


def audio_restore(tools, original):
    audio_validate(original)
    audio_call(tools, 'systemctl', '--user', 'daemon-reload')
    enabled = audio_call(tools, 'systemctl', '--user', 'is-enabled', AUDIO_UNIT, negative=True)
    if enabled != original['enabled']:
        raise ValueError('Tuning enablement differs; inspect unselected service links before retry')
    if original['active'] == 'active':
        audio_call(tools, 'systemctl', '--user', 'start', AUDIO_UNIT)
    current = audio_read(tools)
    # Original endpoints/channels must still exist; no substitutions by index.
    for kind, devices in original['devices'].items():
        for name, value in devices.items():
            channels = current['devices'][kind].get(name, {}).get('volume', {})
            if set(channels) != set(value['volume']):
                raise ValueError('Original audio device/channels unavailable: ' + name)
    for kind, devices in original['devices'].items():
        for name, value in devices.items():
            channels = current['devices'][kind][name]['volume']
            audio_call(tools, 'pactl', 'set-' + kind + '-volume', name,
                       *[str(value['volume'][channel]) for channel in channels])
            audio_call(tools, 'pactl', 'set-' + kind + '-mute', name, '1' if value['mute'] else '0')
        audio_call(tools, 'pactl', 'set-default-' + kind, original['defaults'][kind])
    observed = audio_read(tools)
    if observed['active'] != original['active'] or observed['enabled'] != original['enabled'] or observed['defaults'] != original['defaults'] or any(
            observed['devices'][kind].get(name) != value
            for kind, devices in original['devices'].items() for name, value in devices.items()):
        raise ValueError('Audio restoration did not reach original values')
