"""Installed protocol handlers at the owned webapp-launch boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

COMMANDS = Path(__file__).resolve().parents[2]


class WebappHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = tempfile.TemporaryDirectory(prefix='tam-webapp-handlers-')
        cls.addClassCleanup(cls.stage.cleanup)
        cls.prefix = Path(cls.stage.name)
        for kind in ('zoom',):
            subprocess.run(['make', 'install', f'PREFIX={cls.prefix}'],
                           cwd=COMMANDS / ('tam-webapp-handler-' + kind),
                           capture_output=True, check=True)
        # No browser, network or graphical session is opened by these tests.
        recorder = cls.prefix / 'bin/tam-launch-webapp'
        recorder.write_text(f'#!{sys.executable}\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        recorder.chmod(0o755)
        for name in ('sed',):
            (cls.prefix / 'bin' / name).symlink_to(shutil.which(name))

    def launch(self, kind, *args):
        result = subprocess.run([str(self.prefix / 'bin' / ('tam-webapp-handler-' + kind)), *args],
                                env={'PATH': str(self.prefix / 'bin'), 'LC_ALL': 'C'},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_zoom_protocols_meeting_password_and_parameter_order(self):
        for scheme in ('zoommtg', 'zoomus'):
            with self.subTest(scheme=scheme):
                self.assertEqual(self.launch('zoom', scheme + '://zoom.us/join?confno=123456&pwd=a%2Bb&uname=Guest'),
                                 ['https://app.zoom.us/wc/join/123456?pwd=a%2Bb'])
                self.assertEqual(self.launch('zoom', scheme + '://zoom.us/join?pwd=secret&confno=123456'),
                                 ['https://app.zoom.us/wc/join/123456?pwd=secret'])
                self.assertEqual(self.launch('zoom', scheme + '://zoom.us/join?confno=123456'),
                                 ['https://app.zoom.us/wc/join/123456'])

    def test_zoom_missing_or_unrecognized_protocol_uses_home(self):
        for args in ((), ('https://zoom.us/join?confno=123',), ('zoommtg://zoom.us/join',),
                     ('zoomus://zoom.us/join?confno=&pwd=secret',)):
            with self.subTest(args=args):
                self.assertEqual(self.launch('zoom', *args), ['https://app.zoom.us/wc/home'])

    def test_protocol_data_stays_one_literal_argument(self):
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / 'must-not-exist'
            payload = f'$(touch {sentinel}); "quoted" *'
            self.assertEqual(self.launch('zoom', 'zoommtg://zoom.us/join?confno=123&pwd=' + payload),
                             ['https://app.zoom.us/wc/join/123?pwd=' + payload])
            self.assertFalse(sentinel.exists())


if __name__ == '__main__':
    unittest.main()
