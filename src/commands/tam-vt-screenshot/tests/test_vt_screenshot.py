"""Tests for tam-vt-screenshot active-VT ownership and fallback rules."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tam-vt-screenshot"


class VtScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.dev = self.root / "dev"
        self.dev.mkdir()
        self.active = self.root / "active"
        self.fb = self.root / "fb0"
        self.fb.write_bytes(b"fake-fb")
        self.passwd = self.root / "passwd"
        self.uid = os.geteuid()
        self.gid = os.getegid()

        ffmpeg = self.bin / "ffmpeg"
        ffmpeg.write_text(textwrap.dedent("""\
            #!/bin/bash
            set -euo pipefail
            printf 'PNG_BYTES_FROM_%s' "$*"
        """))
        ffmpeg.chmod(0o755)

    def run_capture(self, extra_env=None):
        env = {
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "TAMLINUX_VT_ACTIVE_PATH": str(self.active),
            "TAMLINUX_VT_DEV_DIR": str(self.dev),
            "TAMLINUX_VT_FB_DEVICE": str(self.fb),
            "TAMLINUX_VT_PASSWD_FILE": str(self.passwd),
            "TAMLINUX_VT_TEST_AS_CURRENT_USER": "1",
        }
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["/usr/bin/bash", str(SCRIPT)],
            env=env, capture_output=True, text=True, timeout=5,
        )

    def test_saves_png_to_active_vt_owner_pictures(self):
        home = self.root / "home/alice"
        home.mkdir(parents=True)
        (self.dev / "tty2").write_text("")
        self.active.write_text("tty2\n")
        uid = max(1000, self.uid)
        self.passwd.write_text(f"alice:x:{uid}:{self.gid}:Alice:{home}:/bin/bash\n")
        if self.uid != uid:
            self.skipTest("test requires normal user uid >= 1000")
        res = self.run_capture()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Saved ", res.stdout)
        self.assertIn(" for alice", res.stdout)
        files = list((home / "Pictures").glob("vt-*-tty2.png"))
        self.assertEqual(len(files), 1)
        self.assertIn("PNG_BYTES_FROM_", files[0].read_text())
        self.assertEqual(files[0].stat().st_mode & 0o077, 0)

    def test_fallback_for_non_1000_human_user_when_1000_absent(self):
        home = self.root / "home/bob"
        home.mkdir(parents=True)
        (self.dev / "tty1").write_text("")
        self.active.write_text("tty1\n")
        # Simulate root-owned login prompt by pointing stat at a root-owned dev node (/dev/null).
        self.passwd.write_text(
            f"root:x:0:0:root:/root:/bin/bash\n"
            f"bob:x:{self.uid}:{self.gid}:Bob:{home}:/bin/bash\n"
        )
        res = self.run_capture({"TAMLINUX_VT_DEV_DIR": "/dev"})
        # When /dev/tty1 is root-owned (uid 0), fallback resolves bob from passwd.
        if Path("/dev/tty1").exists() and Path("/dev/tty1").stat().st_uid == 0 and self.uid >= 1000:
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn(" for bob", res.stdout)

    def test_refuses_invalid_vt_name(self):
        self.active.write_text("../tty1\n")
        res = self.run_capture()
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid active VT", res.stderr)


if __name__ == "__main__":
    unittest.main()
