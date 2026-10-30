"""Exercise GNOME theme adapter failures without touching the user session."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT/'commands/tam-theme-set-gnome/tam-theme-set-gnome'


class GnomeThemeAdapter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.bin = root/'bin'
        self.bin.mkdir()
        self.log = root/'calls'
        self.env = dict(os.environ, HOME=str(root), XDG_STATE_HOME=str(root/'state'),
                        DBUS_SESSION_BUS_ADDRESS='unix:path=/unused', TEST_LOG=str(self.log),
                        PATH=str(self.bin)+':'+os.environ['PATH'])
        self.stub('tam-theme-color', 'if [ "${FAIL_COLOR:-}" = 1 ]; then exit 9; fi\nprintf "%s\\n" "${MODE:-dark}"')
        self.stub('gsettings', 'printf "%s\\n" "$*" >> "$TEST_LOG"\n'
                  'if [ "${FAIL_SETTING:-}" = "${3:-}" ]; then exit 5; fi')

    def stub(self, name, body):
        path = self.bin/name
        path.write_text('#!/bin/sh\n'+body+'\n')
        path.chmod(0o755)

    def run_adapter(self, **values):
        return subprocess.run([str(ADAPTER)], env=self.env | values, text=True, capture_output=True)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_failed_setting_stops_following_writes_and_returns_failure(self):
        for key, count in (('color-scheme', 1), ('gtk-theme', 2)):
            with self.subTest(key=key):
                self.log.unlink(missing_ok=True)
                result = self.run_adapter(FAIL_SETTING=key)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(self.calls()), count)

    def test_failed_mode_lookup_stops_before_writes(self):
        result = self.run_adapter(FAIL_COLOR='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_light_and_dark_write_expected_values(self):
        for mode, expected in (('light', ('prefer-light', 'Adwaita')), ('dark', ('prefer-dark', 'Adwaita-dark'))):
            with self.subTest(mode=mode):
                self.log.unlink(missing_ok=True)
                self.assertEqual(self.run_adapter(MODE=mode).returncode, 0)
                calls = self.calls()
                self.assertEqual(len(calls), 3)
                self.assertTrue(calls[0].endswith('color-scheme '+expected[0]))
                self.assertTrue(calls[1].endswith('gtk-theme '+expected[1]))
                self.assertTrue(calls[2].endswith('icon-theme Yaru-blue'))

    def test_no_session_defers_without_changes(self):
        self.assertEqual(self.run_adapter(DBUS_SESSION_BUS_ADDRESS='').returncode, 0)
        self.assertEqual(self.calls(), [])
