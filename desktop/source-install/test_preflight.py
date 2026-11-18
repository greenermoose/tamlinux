import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import preflight


@unittest.skipUnless(Path("/usr/bin/pacman").is_file(), "requires native Pacman")
class RuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.release = self.root / "usr/lib/os-release"
        self.release.parent.mkdir(parents=True)
        self.release.write_text("ID=arch\n")
        self.db = self.root / "var/lib/pacman/local"
        self.db.mkdir(parents=True)
        (self.db / "ALPM_DB_VERSION").write_text("9\n")

    def add_package(self, name, version, paths=()):
        entry = self.db / f"{name}-{version}"
        entry.mkdir()
        (entry / "desc").write_text(f"%NAME%\n{name}\n\n%VERSION%\n{version}\n\n")
        (entry / "files").write_text("%FILES%\n" + "\n".join(paths) + "\n\n")

    def test_missing_and_outdated_providers(self):
        self.add_package("hyprland", "0.55-1")
        problems = preflight.runtime_problems(self.root)
        self.assertIn("missing Arch package dependency: hyprland>=0.56", problems)
        self.assertIn("missing Arch package dependency: quickshell>=0.3", problems)
        self.assertIn("missing native executable /usr/bin/qs (Arch package: quickshell)", problems)

    def test_unsupported_host(self):
        self.release.write_text("ID=debian\n")
        self.assertIn("requires x86_64 Arch Linux", preflight.runtime_problems(self.root)[0])

    def test_native_command_cannot_be_satisfied_by_local_override(self):
        self.add_package("quickshell", "0.3.2-1", ("usr/bin/qs",))
        local = self.root / "home/user/.local/bin"
        local.mkdir(parents=True)
        (local / "qs").touch(mode=0o755)
        system = self.root / "usr/bin"
        system.mkdir()
        (system / "qs").symlink_to(local / "qs")
        with patch.dict(os.environ, {"PATH": str(local)}):
            self.assertIn("missing native executable /usr/bin/qs (Arch package: quickshell)",
                          preflight.runtime_problems(self.root))
        (system / "quickshell").touch(mode=0o755)
        (system / "qs").unlink()
        (system / "qs").symlink_to("quickshell")
        self.assertFalse(any("/usr/bin/qs " in p for p in preflight.runtime_problems(self.root)))

    def test_unreadable_database_fails_closed(self):
        shutil.rmtree(self.db)
        with self.assertRaisesRegex(ValueError, "cannot read the local Pacman database"):
            preflight.ownership_problems(self.root, ["usr/bin/tam"])

    def test_owned_destination_missing_from_disk(self):
        self.add_package("tam-nut", "0.14.0-1", ("usr/bin/start",))
        self.assertFalse((self.root / "usr/bin/start").exists())
        self.assertEqual(preflight.ownership_problems(self.root, ["usr/bin/start", "usr/bin/tam"]),
                         ["source destination /usr/bin/start is owned by Arch package tam-nut"])


class BuildPreflightTests(unittest.TestCase):
    def test_missing_tools_include_arch_packages(self):
        problems = preflight.build_problems({"PATH": "/nonexistent"})
        self.assertIn("cc (Arch package: gcc)", problems)
        self.assertIn("pkg-config (Arch package: pkgconf)", problems)
