"""Native policy atomic writes and later-write preservation, without elevation."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

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
