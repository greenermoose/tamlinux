import hashlib
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import transaction
from transaction import CULTIVAR_LINKS, Installation, PAYLOAD_CURRENT, inventory, write_json


class TransactionTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.root = self.scratch / "root"
        self.root.mkdir()
        self.system = Installation(self.root)

    def retain(self, version, files):
        stage = self.scratch / version
        payload = stage / "payload"
        for path, content in files.items():
            destination = payload / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
            destination.chmod(0o755)
        manifest = stage / "manifest.json"
        write_json(manifest, {"version": version, "files": inventory(payload)})
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.system.retain(stage, digest)
        return digest

    def install_pair(self):
        first = self.retain("first", {
            f"{PAYLOAD_CURRENT}/bin/tam": "first",
            "etc/profile.d/tamlinux.sh": "profile-1",
            "usr/lib/issue.d/70-tamlinux.issue": "issue-1",
        })
        self.system.start(None, first)
        second = self.retain("second", {
            f"{PAYLOAD_CURRENT}/bin/tam": "second",
            "etc/profile.d/tamlinux.sh": "profile-2",
        })
        return first, second

    def test_upgrade_idempotence_rollback_and_symlinks(self):
        local = [
            self.root / "usr/local/bin/tam",
            self.root / "home/alice/.local/bin/tam",
        ]
        for command in local:
            command.parent.mkdir(parents=True)
            command.write_text("local version")
            command.chmod(0o700)
        with self.system.locked():
            first, second = self.install_pair()
            self.system.start(first, second)
            self.assertFalse((self.root / "usr/lib/issue.d/70-tamlinux.issue").exists())
            self.assertEqual((self.root / PAYLOAD_CURRENT / "bin/tam").read_text(), "second")
            for rel, expected in CULTIVAR_LINKS:
                self.assertEqual((self.root / rel).readlink().as_posix(), expected)
            self.system.start(second, second)
            self.assertEqual(self.system.current()["previous"], first)
            self.system.start(second, first)
        self.assertEqual((self.root / PAYLOAD_CURRENT / "bin/tam").read_text(), "first")
        self.assertEqual((self.root / "etc/profile.d/tamlinux.sh").read_text(), "profile-1")
        self.assertEqual((self.root / "usr/lib/issue.d/70-tamlinux.issue").read_text(), "issue-1")
        for command in local:
            self.assertEqual(command.read_text(), "local version")

    def test_instant_symlink_rollback_and_pruning(self):
        entry = PAYLOAD_CURRENT + "/share/tamlinux/version"
        with self.system.locked():
            v1 = self.retain("v1", {entry: "0.6.36", "etc/profile.d/tamlinux.sh": "same"})
            self.system.start(None, v1)
            v2 = self.retain("v2", {entry: "0.6.37", "etc/profile.d/tamlinux.sh": "same"})
            self.system.start(v1, v2)
            v3 = self.retain("v3", {entry: "0.6.38", "etc/profile.d/tamlinux.sh": "same"})
            self.system.start(v2, v3)
            # v1 should be pruned automatically (only current=v3 + previous=v2 retained)
            self.assertFalse((self.system.versions / v1).exists())
            self.assertTrue((self.system.versions / v2).is_dir())
            self.assertTrue((self.system.versions / v3).is_dir())
            # Rollback from v3 to v2 with unchanged integration files does zero file copies.
            with patch("transaction.copy_file", side_effect=AssertionError("unexpected copy on rollback")):
                self.system.start(v3, v2)
            self.assertEqual((self.root / entry).read_text(), "0.6.37")
            self.assertEqual(self.system.runtime.readlink(), Path("versions") / v2)

    def test_destination_redirect_is_refused(self):
        local = self.root / "usr/local/etc"
        local.mkdir(parents=True)
        (self.root / "etc").symlink_to(local)
        with self.system.locked():
            first = self.retain("first", {"etc/profile.d/tamlinux.sh": "first"})
            with self.assertRaisesRegex(ValueError, "unsafe system directory"):
                self.system.start(None, first)
        self.assertFalse(self.system.pending.exists())

    def test_modified_integration_file_is_refused(self):
        with self.system.locked():
            first, second = self.install_pair()
            (self.root / "etc/profile.d/tamlinux.sh").write_text("admin edit")
            with self.assertRaisesRegex(ValueError, "unmanaged or modified destination"):
                self.system.start(first, second)

    def test_resume_and_rollback_after_interruption(self):
        with self.system.locked():
            first, second = self.install_pair()
            with patch("transaction.copy_file", side_effect=OSError("interrupted")):
                with self.assertRaisesRegex(OSError, "interrupted"):
                    self.system.start(first, second)
            self.assertTrue(self.system.pending.exists())
            self.system.complete()
            self.assertEqual(self.system.current()["current"], second)
            with patch("transaction.copy_file", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    self.system.start(second, first)
            self.system.complete(reverse=True)
            self.assertEqual(self.system.current()["current"], second)

    def test_uninstall_restores_bare_rootstock(self):
        with self.system.locked():
            # Seed a tam-bud /usr/bin/tam and /usr/share/doc/tamlinux directory first
            (self.root / "usr/bin").mkdir(parents=True)
            (self.root / "usr/bin/tam").write_text("bud-elf")
            (self.root / "usr/share/doc/tamlinux").mkdir(parents=True)
            (self.root / "usr/share/doc/tamlinux/index.html").write_text("bud-doc")
            first = self.retain("first", {
                f"{PAYLOAD_CURRENT}/bin/tam": "scion-tam",
                f"{PAYLOAD_CURRENT}/share/doc/index.html": "scion-doc",
                "etc/profile.d/tamlinux.sh": "profile",
            })
            self.system.start(None, first)
            self.assertTrue((self.root / "usr/bin/tam").is_symlink())
            self.assertTrue((self.root / "usr/share/doc/tamlinux").is_symlink())
            self.system.uninstall()
        self.assertFalse((self.root / "usr/bin/tam").exists())
        self.assertFalse((self.root / "usr/bin/tamlinux").exists())
        self.assertFalse((self.root / "usr/share/doc/tamlinux").exists())
        self.assertFalse((self.root / "etc/profile.d/tamlinux.sh").exists())
        self.assertFalse(self.system.active.exists())
        self.assertEqual(list(self.system.versions.iterdir()), [])

    def test_lock_rejects_second_transaction(self):
        with self.system.locked(), self.assertRaises(BlockingIOError), self.system.locked():
            self.fail("second holder entered")

    def test_install_under_restrictive_umask_keeps_world_readable_dirs(self):
        entry = PAYLOAD_CURRENT + "/share/tamlinux/version"
        old_umask = os.umask(0o077)
        try:
            with self.system.locked():
                first = self.retain("first", {"etc/profile.d/tamlinux.sh": "p", entry: "0.6.36"})
                self.system.start(None, first)
        finally:
            os.umask(old_umask)
        for path in (
            self.root / "usr",
            self.root / "usr/lib/tamlinux/versions",
            self.root / "usr/lib/tamlinux/versions" / first,
            self.root / "usr/lib/tamlinux/versions" / first / "share/tamlinux",
            self.root / "var/lib/tamlinux",
            self.root / "var/lib/tamlinux/manifests",
        ):
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o755, f"{path} had mode {oct(mode)}")

    def test_etc_shells_registration_and_uninstall(self):
        shells = self.root / "etc/shells"
        shells.parent.mkdir(parents=True, exist_ok=True)
        shells.write_text("/bin/sh\n/usr/bin/bash\n")
        shells.chmod(0o644)
        with self.system.locked():
            first, second = self.install_pair()
            self.assertEqual(
                shells.read_text().splitlines(),
                ["/bin/sh", "/usr/bin/bash", transaction.PACKAGED_SHELL],
            )
            self.system.start(first, second)
            self.assertEqual(
                shells.read_text().splitlines(),
                ["/bin/sh", "/usr/bin/bash", transaction.PACKAGED_SHELL],
            )
            self.system.uninstall()
        self.assertEqual(shells.read_text(), "/bin/sh\n/usr/bin/bash\n")
        self.assertEqual(stat.S_IMODE(shells.stat().st_mode), 0o644)


if __name__ == "__main__":
    unittest.main()
