import hashlib
from pathlib import Path
import tempfile
import unittest

from transaction import Installation, PAYLOAD_CURRENT, inventory, write_json
from verify import verify_root


class VerifyTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.root = self.scratch / "root"
        self.root.mkdir()
        self.system = Installation(self.root)
        # Seed minimal installed source stage
        stage = self.scratch / "stage"
        files = {
            f"{PAYLOAD_CURRENT}/bin/tam": ("#!/bin/sh\n", 0o755),
            f"{PAYLOAD_CURRENT}/VERSION": ("0.6.36\n", 0o644),
            f"{PAYLOAD_CURRENT}/share/tamlinux/version-notes.txt": (
                "Tamlinux 0.6.36 version notes\n\n- fix\n", 0o644
            ),
        }
        for rel, (content, mode) in files.items():
            target = stage / "payload" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            target.chmod(mode)
        manifest = stage / "manifest.json"
        write_json(manifest, {"version": "0.6.32", "files": inventory(stage / "payload")})
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        with self.system.locked():
            self.system.retain(stage, digest)
            self.system.start(None, digest)
        # Seed cursor theme, terminal, and browser executables
        for rel, content, mode in (
            ("usr/share/icons/default/index.theme", "[Icon Theme]\nInherits=Adwaita\n", 0o644),
            ("usr/share/icons/Adwaita/cursors/left_ptr", "cursor", 0o644),
            ("usr/bin/foot", "#!/bin/sh\n", 0o755),
            ("usr/bin/xdg-terminal-exec", "#!/bin/sh\n", 0o755),
            ("usr/bin/chromium", "#!/bin/sh\n", 0o755),
        ):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            p.chmod(mode)

    def test_verify_passes_on_intact_install(self):
        self.assertEqual(verify_root(self.root, check_runtime=False), [])

    def test_verify_catches_missing_cursor(self):
        (self.root / "usr/share/icons/Adwaita/cursors/left_ptr").unlink()
        problems = verify_root(self.root, check_runtime=False)
        self.assertTrue(any("cursor" in p for p in problems), problems)

    def test_verify_catches_bad_version_notes_header(self):
        notes = self.root / PAYLOAD_CURRENT / "share/tamlinux/version-notes.txt"
        notes.write_text("Tamlinux 0.6.36\n\n- missing words\n")
        problems = verify_root(self.root, check_runtime=False)
        self.assertTrue(any("version notes header" in p for p in problems), problems)

    def test_verify_catches_missing_terminal(self):
        (self.root / "usr/bin/foot").unlink()
        problems = verify_root(self.root, check_runtime=False)
        self.assertTrue(any("foot" in p for p in problems), problems)

    def test_verify_catches_missing_browser(self):
        (self.root / "usr/bin/chromium").unlink()
        problems = verify_root(self.root, check_runtime=False)
        self.assertTrue(any("chromium" in p for p in problems), problems)

    def test_verify_catches_unreadable_installed_file(self):
        tam = self.root / PAYLOAD_CURRENT / "bin/tam"
        tam.chmod(0o000)
        self.addCleanup(tam.chmod, 0o755)
        problems = verify_root(self.root, check_runtime=False)
        self.assertTrue(any("unreadable" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
