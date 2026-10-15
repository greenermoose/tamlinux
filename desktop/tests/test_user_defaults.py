"""Per-user bash defaults and keyserver list: once, preserving, removable."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
BASE = DESKTOP / "user-defaults"
APPLY = BASE / "apply"
# The skeleton a fresh Arch account receives from the bash package.
SKELETON = """#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\\u@\\h \\W]\\$ '
"""


class UserDefaultsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tamlinux-user-defaults-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.record = self.home / ".local/state/tamlinux/user-defaults"
        self.bashrc = self.home / ".bashrc"
        self.conf = self.home / ".gnupg/dirmngr.conf"
        (self.home / ".config/bash").mkdir(parents=True)
        (self.home / ".config/bash/tamlinux").symlink_to(BASE / "bash")

    def run_apply(self, *args, ok=True):
        env = {"HOME": str(self.home), "PATH": "/usr/bin"}
        result = subprocess.run(["/usr/bin/python3", "-I", str(APPLY), *args], env=env,
                                capture_output=True, text=True, check=False)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        return result

    def bash(self, *args):
        env = {"HOME": str(self.home), "PATH": "/usr/bin", "TERM": "dumb"}
        return subprocess.run(["/usr/bin/bash", *args], env=env, capture_output=True, text=True,
                              check=False, cwd=self.home, stdin=subprocess.DEVNULL)

    def test_skeleton_bashrc_gets_blocks_once_and_loads_defaults(self):
        self.bashrc.write_text(SKELETON)
        self.bashrc.chmod(0o640)
        self.assertEqual(self.run_apply()["bashrc"], "blocks added")
        text = self.bashrc.read_text()
        self.assertTrue(text.startswith("# >>> tamlinux env >>>\n"))
        self.assertTrue(text.rstrip().endswith("# <<< tamlinux rc <<<"))
        self.assertIn(SKELETON, text)
        self.assertEqual(stat.S_IMODE(self.bashrc.stat().st_mode), 0o640)
        original = json.loads((self.record / "bashrc.original").read_text())
        self.assertEqual((original["kind"], original["text"]), ("file", SKELETON))
        self.assertEqual(stat.S_IMODE((self.record / "bashrc.original").stat().st_mode), 0o600)
        self.assertEqual(self.run_apply()["bashrc"], "already present")
        self.assertEqual(self.bashrc.read_text(), text)

        # Non-interactive shells (SSH commands) pass the env block before the
        # skeleton returns; interactive shells also load rc after the skeleton.
        quiet = self.bash("-c", ". ~/.bashrc; printf %s \"$PATH\"")
        self.assertIn(str(self.home / ".local/bin"), quiet.stdout.split(":"))
        interactive = self.bash("-i", "-c", "printf '%s|%s|%s' \"$EDITOR\" \"$HISTSIZE\" \"$(alias ..)\"")
        self.assertEqual(interactive.returncode, 0, interactive.stderr)
        self.assertEqual(interactive.stdout.splitlines()[-1],
                         "tam-launch-editor --inline|32768|alias ..='cd ..'")

    def test_linked_bashrc_is_left_to_its_manager(self):
        managed = self.home / "managed-bashrc"
        managed.write_text("# managed\n")
        self.bashrc.symlink_to(managed)
        self.assertEqual(self.run_apply()["bashrc"], "managed elsewhere; unchanged")
        self.assertEqual(os.readlink(self.bashrc), str(managed))
        self.assertEqual(managed.read_text(), "# managed\n")
        self.assertFalse((self.record / "bashrc.original").exists())

    def test_remove_keeps_later_edits_and_refuses_edited_blocks(self):
        self.bashrc.write_text(SKELETON)
        self.run_apply()
        edited = self.bashrc.read_text().replace("alias grep", "export LATER=1\nalias grep")
        self.bashrc.write_text(edited)
        self.assertEqual(self.run_apply("--remove")["bashrc"], "blocks removed")
        self.assertEqual(self.bashrc.read_text(), SKELETON.replace("alias grep", "export LATER=1\nalias grep"))
        self.assertEqual(self.run_apply("--remove")["bashrc"], "nothing to remove")

        self.run_apply()
        self.bashrc.write_text(self.bashrc.read_text().replace("~/.config/bash/tamlinux/rc ]]", "~/other ]]"))
        before = self.bashrc.read_text()
        self.assertEqual(self.run_apply("--remove", ok=False).returncode, 2)
        self.assertEqual(self.bashrc.read_text(), before)

    def test_absent_bashrc_is_created_and_removal_restores_absence(self):
        self.assertEqual(self.run_apply()["bashrc"], "blocks added")
        self.assertTrue(self.bashrc.is_file())
        self.run_apply("--remove")
        self.assertFalse(self.bashrc.exists())

    def test_dirmngr_written_once_private_and_removed_only_unchanged(self):
        self.assertEqual(self.run_apply()["dirmngr"], "written")
        self.assertEqual(self.conf.read_bytes(), (BASE / "gnupg/dirmngr.conf").read_bytes())
        self.assertEqual(stat.S_IMODE(self.conf.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.conf.parent.stat().st_mode), 0o700)
        self.assertEqual(self.run_apply()["dirmngr"], "present; unchanged")
        self.conf.unlink()
        self.assertEqual(self.run_apply()["dirmngr"], "removed by user; not recreated")
        self.assertFalse(self.conf.exists())

    def test_existing_dirmngr_is_never_replaced(self):
        self.conf.parent.mkdir(mode=0o700)
        self.conf.write_text("keyserver hkps://keys.openpgp.org\n")
        self.assertEqual(self.run_apply()["dirmngr"], "present; unchanged")
        self.assertEqual(self.conf.read_text(), "keyserver hkps://keys.openpgp.org\n")
        self.assertEqual(self.run_apply("--remove")["dirmngr"], "nothing to remove")
        self.assertTrue(self.conf.exists())

    def test_removal_keeps_a_changed_dirmngr(self):
        self.run_apply()
        self.conf.write_text(self.conf.read_text() + "keyserver hkps://keys.openpgp.org\n")
        self.assertEqual(self.run_apply("--remove")["dirmngr"], "changed since written; kept")
        self.assertTrue(self.conf.exists())
        self.run_apply()  # unchanged file: still not replaced
        self.assertIn("keys.openpgp.org", self.conf.read_text())

    def test_keyserver_values_and_payload_names(self):
        lines = [line for line in (BASE / "gnupg/dirmngr.conf").read_text().splitlines() if line]
        self.assertEqual(lines, ["keyserver hkps://keyserver.ubuntu.com", "keyserver hkps://pgp.surfnet.nl",
                                 "keyserver hkps://keys.mailvelope.com", "keyserver hkps://keyring.debian.org",
                                 "keyserver hkps://pgp.mit.edu", "connect-quick-timeout 4"])
        for path in BASE.rglob("*"):
            if path.is_file() and path.name not in ("LICENSE-bash", "README.md"):  # source-only attribution
                text = path.read_text().lower()
                for word in ("omarchy", "omacom", "/home/"):
                    self.assertNotIn(word, text, path)
        for path in [*(BASE / "bash").iterdir(), *(BASE / "bash/fns").iterdir()]:
            if path.is_file() and path.name != "inputrc":
                subprocess.run(["/usr/bin/bash", "-n", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
