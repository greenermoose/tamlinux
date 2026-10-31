"""Native policy atomic writes and later-write preservation, without elevation."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('browser_policy',ROOT/'desktop/native/browser_policy.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BrowserPolicy(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.directory=self.root/'managed';self.directory.mkdir()
        self.path=self.directory/'tamlinux-color.json';self.recovery=self.root/'recovery'

    def apply(self,color='123abc'):
        return m.apply(color,[str(self.directory)],self.recovery,os.getuid())

    def test_native_write_and_explicit_restore_preserve_later_bytes(self):
        self.path.write_text('{"personal":"previous"}\n');self.path.chmod(0o640)
        journal=self.apply()
        self.assertEqual(json.loads(self.path.read_text())['BrowserThemeColor'],'#123abc')
        self.path.write_text('{"personal":"later"}\n')
        m.restore(journal,[str(self.directory)],os.getuid())
        self.assertEqual(self.path.read_text(),'{"personal":"previous"}\n')
        self.assertEqual(self.path.stat().st_mode & 0o777,0o640)
        later=json.loads(next(journal.glob('later-*.json')).read_text())
        self.assertEqual(base64.b64decode(later['state']['bytes']),b'{"personal":"later"}\n')
        m.restore(journal,[str(self.directory)],os.getuid())

    def test_absent_previous_policy_is_removed_only_after_recovery_copy(self):
        journal=self.apply();m.restore(journal,[str(self.directory)],os.getuid())
        self.assertFalse(self.path.exists());self.assertTrue(list(journal.glob('later-*.json')))

    def test_invalid_color_and_link_conflicts_stop_before_any_native_write(self):
        for color in ['ABCDEF','1234567','123abc;evil']:
            with self.assertRaises(ValueError):self.apply(color)
            self.assertFalse(self.recovery.exists())
        self.path.symlink_to('personal-unavailable-policy')
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(os.readlink(self.path),'personal-unavailable-policy')

    def test_missing_supported_browser_is_explicitly_unavailable(self):
        with self.assertRaisesRegex(ValueError,'No supported'):
            m.apply('123abc',[str(self.root/'absent')],self.recovery,os.getuid())

    def test_unlisted_root_destination_in_journal_is_refused(self):
        journal=self.apply();doc=json.loads((journal/'manifest.json').read_text())
        outside=self.root/'outside';outside.write_text('keep')
        doc['files'][0]['path']=str(outside);m.save(journal/'manifest.json',doc)
        with self.assertRaises(ValueError):m.restore(journal,[str(self.directory)],os.getuid())
        self.assertEqual(outside.read_text(),'keep')

    def test_preflight_of_all_destinations_prevents_partial_write(self):
        other=self.root/'unsafe';other.mkdir();other.chmod(0o777)
        with self.assertRaises(ValueError):m.apply('123abc',[str(self.directory),str(other)],self.recovery,os.getuid())
        self.assertFalse(self.path.exists());self.assertFalse(self.recovery.exists())

    def test_other_managed_theme_policy_is_refused_before_writing(self):
        other = self.directory/'personal-policy'
        for key, value in (('BrowserThemeColor', '#123abc'), ('BrowserColorScheme', 'device')):
            with self.subTest(key=key):
                contents = json.dumps({key: value, 'OtherPolicy': True})
                other.write_text(contents)
                with self.assertRaisesRegex(ValueError, 'theme policy.*personal-policy'):
                    self.apply()
                self.assertEqual(other.read_text(), contents)
                self.assertFalse(self.path.exists())
                self.assertFalse(self.recovery.exists())

    def test_unrelated_policy_is_preserved(self):
        other = self.directory/'personal-policy.json'
        original = '{"ShowHomeButton": true}\n'
        other.write_text(original)
        self.apply()
        self.assertEqual(other.read_text(), original)
        self.assertEqual(json.loads(self.path.read_text())['BrowserThemeColor'], '#123abc')

    def test_escaped_theme_key_is_detected(self):
        other = self.directory/'escaped.json'
        original = '{"BrowserTheme\\u0043olor":"#111111"}'
        other.write_text(original)
        with self.assertRaisesRegex(ValueError, 'theme policy.*escaped.json'):
            self.apply()
        self.assertEqual(other.read_text(), original)
        self.assertFalse(self.recovery.exists())

    def test_uninspectable_other_policy_stops_without_changes(self):
        other = self.directory/'personal-policy.json'
        other.write_text('{malformed')
        with self.assertRaisesRegex(ValueError, 'cannot inspect.*personal-policy'):
            self.apply()
        self.assertEqual(other.read_text(), '{malformed')
        self.assertFalse(self.path.exists())
        self.assertFalse(self.recovery.exists())
        other.unlink()
        other.symlink_to('/unavailable/personal-policy')
        with self.assertRaisesRegex(ValueError, 'cannot inspect.*personal-policy'):
            self.apply()
        self.assertTrue(other.is_symlink())
        self.assertFalse(self.path.exists())

    def test_chromium_json_extensions_preserve_unrelated_policy(self):
        other = self.directory/'comments.json'
        contents = ('{// line comment\n"ShowHomeButton": true, /* block */\n'
                    '"values": ["https://example.test/*literal*/", "BrowserThemeColor",],\n}')
        other.write_text(contents)
        self.apply()
        self.assertEqual(other.read_text(), contents)
        self.assertEqual(json.loads(self.path.read_text())['BrowserThemeColor'], '#123abc')

    def test_commented_policy_with_escaped_theme_key_still_conflicts(self):
        other = self.directory/'comments.json'
        contents = '{/* comment */ "BrowserTheme\\u0043olor": "#111111", // trailing\n}'
        other.write_text(contents)
        with self.assertRaisesRegex(ValueError, 'theme policy.*comments.json'):
            self.apply()
        self.assertEqual(other.read_text(), contents)
        self.assertFalse(self.path.exists())
        self.assertFalse(self.recovery.exists())

    def test_malformed_extensions_are_refused_before_writing(self):
        other = self.directory/'comments.json'
        for contents in ('{/* unterminated', '{,}', '{"x":[,]}',
                         '{"x":1,,}', '{"x":"bad\nstring"}', '{"x":NaN}'):
            with self.subTest(contents=contents):
                other.write_text(contents)
                with self.assertRaisesRegex(ValueError, 'cannot inspect.*comments.json'):
                    self.apply()
                self.assertEqual(other.read_text(), contents)
                self.assertFalse(self.path.exists())
                self.assertFalse(self.recovery.exists())

    def test_policy_inspection_is_bounded(self):
        for index in range(129):
            (self.directory/str(index)).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Too many browser policy entries'):
            self.apply()
        self.assertFalse(self.path.exists())
        self.assertFalse(self.recovery.exists())

    def test_other_browser_conflict_stops_before_any_write(self):
        other = self.root/'second-managed'; other.mkdir()
        policy = other/'other.json'; policy.write_text('{"BrowserThemeColor":"#ffffff"}')
        with self.assertRaisesRegex(ValueError, 'theme policy.*other.json'):
            m.apply('123abc', [str(self.directory), str(other)], self.recovery, os.getuid())
        self.assertFalse(self.path.exists())
        self.assertFalse((other/'tamlinux-color.json').exists())
        self.assertFalse(self.recovery.exists())

    def test_read_only_preflight_checks_conflicts_without_creating_journal(self):
        self.assertEqual(len(m.preflight([str(self.directory)], os.getuid())), 1)
        self.assertFalse(self.path.exists())
        self.assertFalse(self.recovery.exists())
        other = self.directory/'other.json'
        other.write_text('{"BrowserThemeColor":"#ffffff"}')
        with self.assertRaisesRegex(ValueError, 'theme policy.*other.json'):
            m.preflight([str(self.directory)], os.getuid())
        self.assertFalse(self.path.exists())
        self.assertFalse(self.recovery.exists())

    def test_check_command_is_available_without_root_and_cannot_apply(self):
        with patch.object(m, 'preflight') as preflight, \
             patch.object(m.os, 'geteuid', return_value=1000), \
             patch.object(m, 'apply') as apply:
            m.main(['--check'])
            preflight.assert_called_once_with(m.DIRECTORIES)
            apply.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'require root'):
                m.main(['123abc'])
            apply.assert_not_called()
