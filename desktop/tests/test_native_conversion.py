"""Exercise actual native conversion and later-write recovery in isolated roots."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'native/defaults/convert.py'
spec = importlib.util.spec_from_file_location('native_defaults_conversion', SOURCE)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class NativeConversionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.checkpoint = self.root / 'state/checkpoint'
        self.write('security/faillock.conf', '# Arch default\n# deny = 3\n')
        self.write('nsswitch.conf', 'passwd: files systemd\nhosts: ' + c.ARCH_HOSTS[0] + '\n')

    def write(self, p, text, mode=0o644):
        target = self.root / 'etc' / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        target.chmod(mode)
        return target

    def test_fresh_pairs_and_later_write_rollback(self):
        original = (self.root / 'etc/nsswitch.conf').read_bytes()
        selected = c.apply(self.root, self.checkpoint)
        self.assertEqual(selected['skipped'], ['cups/cups-files.conf'])
        self.assertIn('deny = 10', (self.root / 'etc/security/faillock.conf').read_text())
        self.assertEqual(json.loads((self.root / 'etc/docker/daemon.json').read_text()), c.DOCKER)
        self.assertEqual((self.root / 'etc/sudoers.d/70-tamlinux-passwd-tries').stat().st_mode & 0o777, 0o440)
        self.write('docker/daemon.json', '{"later": true}\n', 0o640)
        result = c.restore(self.root, self.checkpoint)
        self.assertEqual(result['status'], 'restored')
        self.assertEqual((self.root / 'etc/nsswitch.conf').read_bytes(), original)
        self.assertFalse((self.root / 'etc/docker/daemon.json').exists())
        records = [json.loads(p.read_text()) for p in (self.checkpoint / 'new-writes').glob('*.json')]
        entry = records[0]['files'][str(self.root / 'etc/docker/daemon.json')]
        self.assertEqual((self.checkpoint / 'blobs' / entry['blob']).read_text(), '{"later": true}\n')
        self.assertEqual(entry['mode'], 0o640)
        with self.assertRaises(ValueError):
            c.apply(self.root, self.checkpoint)

    def test_existing_values_modes_and_unrelated_settings_survive(self):
        self.write('security/faillock.conf', '# private policy comment\ndeny = 10\nunlock_time = 900\n', 0o640)
        self.write('cups/cups-files.conf', 'User 209\nGroup 209\nSystemGroup cups-browsed sys root\nPeerCred on\n', 0o640)
        self.write('docker/daemon.json', json.dumps({**c.DOCKER, 'live-restore': True}))
        originals = {p: (self.root / 'etc' / p).read_bytes() for p in
                     ['security/faillock.conf', 'cups/cups-files.conf', 'docker/daemon.json']}
        c.apply(self.root, self.checkpoint)
        c.apply(self.root, self.checkpoint)
        self.assertTrue(json.loads((self.root / 'etc/docker/daemon.json').read_text())['live-restore'])
        self.assertEqual((self.root / 'etc/cups/cups-files.conf').stat().st_mode & 0o777, 0o640)
        c.restore(self.root, self.checkpoint)
        for p, data in originals.items():
            self.assertEqual((self.root / 'etc' / p).read_bytes(), data)

    def test_conflicts_are_checked_before_any_write(self):
        for p, text in [('docker/daemon.json', '{"dns":["8.8.8.8"]}'),
                        ('sudoers.d/70-tamlinux-passwd-tries', 'Defaults passwd_tries=2\n'),
                        ('cups/cups-files.conf', 'User administrator\n')]:
            target = self.write(p, text)
            with self.assertRaises(ValueError):
                c.apply(self.root, self.checkpoint)
            self.assertFalse(self.checkpoint.exists())
            self.assertNotIn('deny = 10', (self.root / 'etc/security/faillock.conf').read_text())
            target.unlink()

    def test_interruption_retry_and_changed_destination_refusal(self):
        with self.assertRaises(InterruptedError):
            c.apply(self.root, self.checkpoint, stop_after=2)
        original_checkpoint = (self.checkpoint / 'checkpoint.json').read_bytes()
        self.write('nsswitch.conf', 'hosts: files dns # later edit\n')
        with self.assertRaisesRegex(ValueError, 'changed since checkpoint'):
            c.apply(self.root, self.checkpoint)
        c.restore(self.root, self.checkpoint)
        # A new transaction can now be interrupted and resumed without replacing originals.
        second = self.root / 'state/second'
        with self.assertRaises(InterruptedError):
            c.apply(self.root, second, stop_after=1)
        c.apply(self.root, second)
        c.restore(self.root, second)
        self.assertEqual(json.loads(original_checkpoint)['status'], 'preserved')

    def test_redirected_file_and_parent_refuse(self):
        target = self.root / 'etc/security/faillock.conf'
        target.unlink()
        target.symlink_to('/etc/security/faillock.conf')
        with self.assertRaises(ValueError):
            c.plan(self.root)
        target.unlink()
        target.parent.rmdir()
        target.parent.symlink_to(self.root / 'elsewhere', target_is_directory=True)
        with self.assertRaises(ValueError):
            c.plan(self.root)


if __name__ == '__main__':
    unittest.main()
