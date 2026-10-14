"""Native DNS recovery with real files and a bounded daemon fixture."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'commands/tam-dns/dns_recovery.py'
spec = importlib.util.spec_from_file_location('dns_recovery', SOURCE)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
CONNECTION = '11111111-2222-3333-4444-555555555555'
LATER_CONNECTION = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'


def profile(dns=''):
    return {'type': '802-3-ethernet', 'fields': {
        'ipv4.ignore-auto-dns': 'yes' if dns else 'no', 'ipv4.dns': dns,
        'ipv6.ignore-auto-dns': 'no', 'ipv6.dns': ''}}


class Daemon:
    def __init__(self):
        self.connections = {CONNECTION: profile()}
        self.services = {r.UNITS[0]: 'active', r.UNITS[1]: 'inactive'}
        self.fail_modify = False

    def profiles(self):
        return copy.deepcopy(self.connections)

    def profile(self, uuid):
        return copy.deepcopy(self.connections.get(uuid))

    def units(self):
        return dict(self.services)

    def modify(self, uuid, fields):
        if self.fail_modify:
            raise subprocess.CalledProcessError(1, ['nmcli', 'connection', 'modify'])
        self.connections[uuid]['fields'] = dict(fields)

    def reload(self, units):
        self.services = dict(units)


class DnsRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'private-recovery'
        self.files = (self.root/'etc/NetworkManager/dns.conf', self.root/'etc/systemd/resolved.conf')
        self.files[0].parent.mkdir(parents=True)
        self.files[0].write_bytes(b'original DNS config\n')
        self.files[0].chmod(0o640)
        self.files[1].parent.mkdir(parents=True)
        self.daemon = Daemon()

    def preserve(self):
        return r.preserve(self.base, self.files, self.daemon, os.getuid())

    def restore(self, journal):
        return r.restore(journal, self.base, self.files, self.daemon, os.getuid())

    def later(self):
        self.files[0].write_bytes(b'later DNS config\n')
        self.files[0].chmod(0o600)
        self.files[1].write_bytes(b'later resolved config\n')
        self.daemon.connections[CONNECTION] = profile('8.8.8.8')
        self.daemon.connections[LATER_CONNECTION] = profile('192.0.2.1')
        self.daemon.services[r.UNITS[1]] = 'active'

    def test_original_bytes_modes_absence_profile_fields_and_units_restore(self):
        journal = self.preserve()
        self.later()
        result = self.restore(journal)
        self.assertEqual(result['status'], 'restored')
        self.assertEqual(self.files[0].read_bytes(), b'original DNS config\n')
        self.assertEqual(self.files[0].stat().st_mode & 0o777, 0o640)
        self.assertFalse(self.files[1].exists())
        self.assertEqual(self.daemon.connections[CONNECTION], profile())
        self.assertEqual(self.daemon.connections[LATER_CONNECTION], profile('192.0.2.1'))
        self.assertEqual(self.daemon.services[r.UNITS[1]], 'inactive')
        archived = json.loads(next(journal.glob('later-*.json')).read_text())['state']
        self.assertEqual(archived['profiles'][CONNECTION], profile('8.8.8.8'))
        self.assertEqual(archived['units'][r.UNITS[1]], 'active')
        self.assertEqual(__import__('base64').b64decode(archived['files'][str(self.files[0])]['bytes']), b'later DNS config\n')
        self.restore(journal)

    def test_interrupted_restore_retries_and_keeps_additional_later_writes(self):
        journal = self.preserve()
        self.later()
        self.daemon.fail_modify = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.restore(journal)
        self.assertEqual(json.loads((journal/'restore.json').read_text())['status'], 'restoring')
        self.files[0].write_bytes(b'new write after interruption')
        self.daemon.fail_modify = False
        self.restore(journal)
        archives = [json.loads(p.read_text()) for p in journal.glob('later-*.json')]
        self.assertGreaterEqual(len(archives), 2)
        self.assertTrue(any(__import__('base64').b64decode(a['state']['files'][str(self.files[0])]['bytes']) == b'new write after interruption' for a in archives))

    def test_corrupt_original_or_unlisted_destination_blocks_all_native_writes(self):
        journal = self.preserve()
        original = json.loads((journal/'checkpoint.json').read_text())
        self.later()
        for kind in ('bytes', 'destination'):
            with self.subTest(kind=kind):
                doc = copy.deepcopy(original)
                if kind == 'bytes':
                    doc['before']['files'][str(self.files[0])]['bytes'] = 'Y29ycnVwdA=='
                else:
                    doc['before']['files'][str(self.root/'unrelated')] = {'present': False}
                # A recomputed envelope does not bypass per-file hashes or fixed paths.
                doc['beforeSha256'] = r.digest(r.encoded(doc['before']))
                r.save(journal/'checkpoint.json', doc)
                with self.assertRaises(ValueError):
                    self.restore(journal)
                self.assertEqual(self.files[0].read_bytes(), b'later DNS config\n')
                self.assertEqual(self.daemon.connections[CONNECTION], profile('8.8.8.8'))

    def test_missing_original_connection_blocks_before_file_changes(self):
        journal = self.preserve()
        self.later()
        del self.daemon.connections[CONNECTION]
        with self.assertRaises(ValueError):
            self.restore(journal)
        self.assertEqual(self.files[0].read_bytes(), b'later DNS config\n')
        self.assertFalse((journal/'restore.json').exists())

    def test_corrupt_existing_later_archive_blocks_overwrite(self):
        journal = self.preserve();self.later()
        current = r.observe(self.files, self.daemon, os.getuid())
        archive = journal / ('later-' + r.digest(r.encoded(current)) + '.json')
        r.save(archive, {'schema': 1, 'state': 'corrupt'})
        with self.assertRaises(ValueError):
            self.restore(journal)
        self.assertEqual(self.files[0].read_bytes(), b'later DNS config\n')

    def test_links_and_redirected_native_parents_are_refused(self):
        outside = self.root/'outside';outside.write_bytes(b'keep')
        self.files[0].unlink();self.files[0].symlink_to(outside)
        with self.assertRaises(ValueError):
            self.preserve()
        self.assertEqual(outside.read_bytes(), b'keep')

    def test_concurrent_writer_after_archival_is_preserved_on_retry(self):
        journal = self.preserve()
        self.later()
        save = r.save
        def write(path, value):
            save(path, value)
            if path == journal/'restore.json':
                self.files[0].write_bytes(b'concurrent latest values')
        with patch.object(r, 'save', side_effect=write):
            with self.assertRaises(ValueError):
                self.restore(journal)
        self.assertEqual(self.files[0].read_bytes(), b'concurrent latest values')
        self.restore(journal)
        self.assertEqual(self.files[0].read_bytes(), b'original DNS config\n')

    def test_non_root_cli_cannot_enable_fixture_overrides_or_mutate_native_state(self):
        if os.getuid() == 0:
            self.skipTest('Requires an unprivileged caller')
        result = subprocess.run([sys.executable, '-I', str(SOURCE), 'preserve'], text=True, capture_output=True,
                                env={**os.environ, 'TAMLINUX_NETWORK_RECOVERY': str(self.base)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('root authorization', result.stderr)
        self.assertFalse(self.base.exists())


if __name__ == '__main__':
    unittest.main()
