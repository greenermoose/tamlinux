"""Exercise the native entry against the installed user endpoint without UWSM."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ENTRY = Path(__file__).resolve().parents[1] / "native/integration/session"


class NativeLogin(unittest.TestCase):
    def test_renamed_endpoint_preserves_spaced_home_and_exit_status(self):
        with tempfile.TemporaryDirectory(prefix="login home ") as directory:
            home = Path(directory)
            endpoint = home / ".local/bin/tam-desktop"
            endpoint.parent.mkdir(parents=True)
            endpoint.write_text('#!/bin/sh\nprintf "%s\\n" "$HOME"\nexit 23\n')
            endpoint.chmod(0o755)
            result = subprocess.run(["sh", str(ENTRY)], env={**os.environ, "HOME": directory},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 23)
            self.assertEqual(result.stdout, directory + "\n")

    def test_old_endpoint_cannot_hide_missing_new_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            endpoint = Path(directory) / ".local/bin/tamlinux-hyprland-session"
            endpoint.parent.mkdir(parents=True)
            endpoint.write_text('#!/bin/sh\necho stale\n')
            endpoint.chmod(0o755)
            result = subprocess.run(["sh", str(ENTRY)], env={**os.environ, "HOME": directory},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertIn("Install the Tamlinux user generation", result.stderr)
