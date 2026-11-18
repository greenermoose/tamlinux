import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from transaction import Installation, PAYLOAD_CURRENT, inventory, write_json


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
        first = self.retain("first", {"usr/bin/tam": "first", "usr/bin/old": "obsolete"})
        self.system.start(None, first)
        second = self.retain("second", {"usr/bin/tam": "second"})
        return first, second

    def test_upgrade_idempotence_and_rollback_preserve_local_trees(self):
        local = [
            self.root / "usr/local/bin/tam",
            self.root / "usr/local/lib/libtam.a",
            self.root / "home/alice/.local/bin/tam",
            self.root / "home/bob/.local/share/doc/tam/readme",
        ]
        for command in local:
            command.parent.mkdir(parents=True)
            command.write_text("local version")
            command.chmod(0o700)
        with self.system.locked():
            first, second = self.install_pair()
            self.system.start(first, second)
            self.assertFalse((self.root / "usr/bin/old").exists())
            self.system.start(second, second)
            self.assertEqual(self.system.current()["previous"], first)
            self.system.start(second, first)
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "first")
        self.assertEqual((self.root / "usr/bin/old").read_text(), "obsolete")
        for command in local:
            self.assertEqual(command.read_text(), "local version")
            self.assertEqual(command.stat().st_mode & 0o777, 0o700)

    def test_runtime_switch_and_recovery(self):
        entry = PAYLOAD_CURRENT + "/share/tamlinux/version"
        with self.system.locked():
            first = self.retain("first", {entry: "first"})
            second = self.retain("second", {entry: "second"})
            self.system.start(None, first)
            self.system.start(first, second)
            self.assertEqual((self.root / entry).read_text(), "second")
            self.assertEqual(self.system.runtime.readlink(), Path("versions") / second)
            self.system.start(second, first)
        self.assertEqual((self.root / entry).read_text(), "first")

    def test_destination_redirect_is_refused(self):
        local = self.root / "usr/local/bin"
        local.mkdir(parents=True)
        (self.root / "usr/bin").symlink_to(local)
        with self.system.locked():
            first = self.retain("first", {"usr/bin/tam": "first"})
            with self.assertRaisesRegex(ValueError, "unsafe system directory"):
                self.system.start(None, first)
        self.assertFalse((local / "tam").exists())
        self.assertFalse(self.system.pending.exists())

    def test_modified_legacy_owned_path_is_refused(self):
        with self.system.locked():
            first, second = self.install_pair()
            (self.root / "usr/bin/old").write_text("administrator edit")
            with self.assertRaisesRegex(ValueError, "unmanaged or modified destination"):
                self.system.start(first, second)
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "first")
        self.assertEqual((self.root / "usr/bin/old").read_text(), "administrator edit")

    def test_resume_after_interruption(self):
        with self.system.locked():
            first, second = self.install_pair()
            with patch("transaction.copy_file", side_effect=OSError("interrupted")):
                with self.assertRaisesRegex(OSError, "interrupted"):
                    self.system.start(first, second)
            self.assertTrue(self.system.pending.exists())
            self.assertFalse((self.root / "usr/bin/old").exists())
            self.system.complete()
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "second")
        self.assertEqual(self.system.current()["current"], second)

    def test_rollback_after_interruption(self):
        with self.system.locked():
            first, second = self.install_pair()
            with patch("transaction.copy_file", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    self.system.start(first, second)
            self.system.complete(reverse=True)
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "first")
        self.assertEqual((self.root / "usr/bin/old").read_text(), "obsolete")
        self.assertEqual(self.system.current()["current"], first)

    def test_lock_rejects_second_transaction(self):
        with self.system.locked(), self.assertRaises(BlockingIOError), self.system.locked():
            self.fail("second holder entered")


if __name__ == "__main__":
    unittest.main()
