"""Exercise client ordering with temporary stand-ins, never real privilege."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'tam-theme-set-browser'


class BrowserClient(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        bin_dir = root/'bin'; bin_dir.mkdir()
        self.policy = root/'policy'
        self.policy.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$POLICY_LOG"\nexit "${CHECK_STATUS:-0}"\n')
        self.policy.chmod(0o755)
        for name, body in (('chromium', 'exit 0'), ('pkexec', 'printf "%s\\n" "$*" >> "$PRIVILEGE_LOG"')):
            script = bin_dir/name; script.write_text('#!/bin/sh\n'+body+'\n'); script.chmod(0o755)
        (root/'refresh.py').write_text('import os\nfrom pathlib import Path\nPath(os.environ["REFRESH_LOG"]).write_text("refreshed")\n')
        source = SOURCE.read_text()
        assignment = 'adapter=/usr/bin/tam-theme-set-browser-policy'
        self.assertEqual(source.count(assignment), 1)
        self.client = root/'client'
        self.client.write_text(source.replace(assignment, 'adapter='+shlex.quote(str(self.policy))))
        self.client.chmod(0o755)
        self.policy_log = root/'policy.log'; self.privilege_log = root/'privilege.log'; self.refresh_log = root/'refresh.log'
        self.env = dict(os.environ, HOME=str(root/'home'), XDG_STATE_HOME=str(root/'state'),
                        PATH=str(bin_dir)+':'+os.defpath, POLICY_LOG=str(self.policy_log),
                        PRIVILEGE_LOG=str(self.privilege_log), REFRESH_LOG=str(self.refresh_log))

    def test_failed_preflight_does_not_request_privilege_or_refresh(self):
        result = subprocess.run([str(self.client)], env=self.env | {'CHECK_STATUS':'1'}, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Browser policy preflight failed', result.stderr)
        self.assertEqual(self.policy_log.read_text(), '--check\n')
        self.assertFalse(self.privilege_log.exists())
        self.assertFalse(self.refresh_log.exists())

    def test_successful_preflight_proceeds_to_privileged_adapter_and_refresh(self):
        result = subprocess.run([str(self.client)], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.policy_log.read_text(), '--check\n')
        self.assertEqual(self.privilege_log.read_text(), str(self.policy)+' 1c2027\n')
        self.assertEqual(self.refresh_log.read_text(), 'refreshed')
