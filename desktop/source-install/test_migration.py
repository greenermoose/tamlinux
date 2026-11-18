"""Exercise the real bundle transition under a private PID namespace."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from build import PRODUCT, revisions
import migration
from migration import BundleMigration
from transaction import Installation, inventory, write_json


@unittest.skipUnless(os.getpid() == 1 and Path("/proc/self/stat").read_text().startswith("1 "),
                     "run this module as PID 1 with private procfs")
class MigrationTests(unittest.TestCase):
    def put(self, path, content, mode=0o644):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(mode)

    def bundle(self, *args):
        return subprocess.check_output([migration.BUNDLE_TOOL, "--root", self.root, *args], text=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "root"
        self.system = Installation(self.root)
        self.move = BundleMigration(self.system)
        profile = self.root / "usr/share/tamlinux/rootstock"
        self.put(profile / "profile", "format 1\nallow usr/bin\nallow usr/share/doc\n")
        self.put(profile / "id", "arch-systemd\n")
        self.db = self.root / "var/lib/pacman/local"
        self.put(self.db / "ALPM_DB_VERSION", "9\n")
        self.package("tam-nut", "usr/bin/hi", "usr/bin/start")
        for name, command, arg in (("hi", "tam", " hi"), ("start", "tam-start", "")):
            self.put(self.root / "usr/bin" / name,
                     f'#!/bin/sh\nif [ -x /usr/bin/{command} ]; then\n'
                     f'    exec /usr/bin/{command}{arg} "$@"\nfi\n'
                     'exec /usr/bin/tam-nut welcome\n', 0o755)
        self.bundle_tree = self.base / "bundle"
        self.put(self.bundle_tree / "tree/version", "legacy")
        self.put(self.bundle_tree / "placed/usr/bin/tam", "legacy", 0o755)
        self.put(self.bundle_tree / "placed/usr/share/doc/tldr/legacy", "legacy tldr")
        self.put(self.bundle_tree / "placed/usr/share/doc/info/legacy", "legacy info")
        self.bundle("seal", self.bundle_tree, "--format", "2", "--name", "tamlinux",
                    "--version", "legacy", "--target", "arch x86_64 baseline x86-64-v2",
                    "--optional-doc", "info", "--optional-doc", "tldr")
        self.bundle_hash = next(line.split()[1] for line in
                                (self.bundle_tree / "BUNDLE").read_text().splitlines()
                                if line.startswith("hash "))
        self.original = self.base / "legacy.tbundle"
        self.bundle("pack", self.bundle_tree, "-o", self.original)
        self.sha256 = hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.bundle("install", self.original, "--docs", "tldr")
        self.bundle("apply")
        self.initial = self.make_stage("first")
        self.local = []
        for name in ("usr/local/bin/tam", "home/alice/.local/bin/tam", "home/bob/.local/bin/tam"):
            target = self.root / name
            self.put(target, "local", 0o700)
            link = target.with_name("local-link")
            link.symlink_to("tam")
            self.local.append((target, link))

    def package(self, name, *paths):
        self.put(self.db / f"{name}-1-1/desc", f"%NAME%\n{name}\n\n%VERSION%\n1-1\n\n")
        self.put(self.db / f"{name}-1-1/files", "%FILES%\n" + "\n".join(paths) + "\n\n")

    def make_stage(self, version):
        stage = self.base / version
        for name in ("hi", "start", "tam", "tam-start"):
            self.put(stage / "payload/usr/bin" / name, version, 0o755)
        self.put(stage / "payload/usr/lib/tamlinux/source/current/share/tamlinux/version", version)
        manifest = stage / "manifest.json"
        write_json(manifest, {"version": version, "files": inventory(stage / "payload"),
                              "components": revisions(PRODUCT.parent)})
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        with self.system.locked():
            self.system.retain(stage, digest)
        return digest

    def migrate(self):
        with self.system.locked():
            self.move.start(self.initial, self.original, self.sha256, self.bundle_hash)

    def assert_recovered(self):
        self.assertIn(f"bundle-hash: {self.bundle_hash}", self.bundle("check"))
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "legacy")
        self.assertFalse((self.root / "usr/lib/tamlinux/source/current").exists())
        self.assertTrue((self.root / "usr/share/doc/tldr/legacy").exists())
        self.assertFalse((self.root / "usr/share/doc/info/legacy").exists())
        self.assertFalse(self.system.pending.exists())

    def test_migrate_upgrade_and_recover(self):
        launchers = [self.root / "usr/bin" / name for name in ("hi", "start")]
        launcher_bytes = [path.read_bytes() for path in launchers]
        self.migrate()
        self.assertEqual((self.root / "usr/bin/tam").read_text(), "first")
        self.assertFalse((self.root / "usr/lib/tamlinux/current").exists())
        second = self.make_stage("second")
        build = self.base / "build"
        (build / "stages").mkdir(parents=True)
        receipt = build / "stages" / second
        (self.base / "second").rename(receipt)
        (build / "build").symlink_to(receipt)
        subprocess.run(["/usr/bin/make", "install", f"SOURCE_ROOT={self.root}",
                        f"SOURCE_BUILD={build}"], cwd=PRODUCT, check=True,
                       stdout=subprocess.PIPE)
        with self.system.locked():
            self.assertEqual((self.root / "usr/bin/tam").read_text(), "second")
            self.system.start(second, self.initial)
        self.original.unlink()
        shutil.rmtree(self.base / "first")
        shutil.rmtree(build)
        subprocess.run(["/usr/bin/python3", "-I", "-B", self.system.state / "recovery/transaction.py",
                        "rollback-bundle", "--root", self.root], cwd=self.base, check=True)
        self.assert_recovered()
        for path, expected in zip(launchers, launcher_bytes, strict=True):
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual(path.stat().st_mode & 0o777, 0o755)
        for target, link in self.local:
            self.assertEqual(target.read_text(), "local")
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            self.assertEqual(link.readlink(), Path("tam"))

    def test_reject_mismatched_inputs_and_unmanaged_collisions(self):
        with self.system.locked():
            with self.assertRaisesRegex(ValueError, "live bundle differs"):
                self.move.start(self.initial, self.original, self.sha256, "sha256:" + "0" * 64)
            with self.assertRaisesRegex(ValueError, "archive checksum differs"):
                self.move.start(self.initial, self.original, "0" * 64, self.bundle_hash)
            target = self.root / "usr/bin/tam-start"
            self.put(target, "foreign", 0o755)
            with self.assertRaisesRegex(ValueError, "unmanaged or modified destination"):
                self.move.start(self.initial, self.original, self.sha256, self.bundle_hash)
            self.assertEqual(target.read_text(), "foreign")
            target.unlink()
            launcher = self.root / "usr/bin/hi"
            original = launcher.read_text()
            self.put(launcher, "edited", 0o755)
            with self.assertRaisesRegex(ValueError, "expected intact tam-nut launcher"):
                self.move.start(self.initial, self.original, self.sha256, self.bundle_hash)
            self.put(launcher, original, 0o755)
            self.package("foreign", "usr/bin/start")
            with self.assertRaisesRegex(ValueError, "expected intact tam-nut launcher"):
                self.move.start(self.initial, self.original, self.sha256, self.bundle_hash)
        self.assertIn(f"bundle-hash: {self.bundle_hash}", self.bundle("check"))
        self.assertFalse(self.system.pending.exists())

    def test_interrupted_migration_and_recovery_resume(self):
        command = BundleMigration.command
        interrupted = {"detach", "restore"}

        def interrupt_after_command(instance, action, *args, **kwargs):
            output = command(instance, action, *args, **kwargs)
            if action in interrupted:
                interrupted.remove(action)
                raise OSError(f"interrupted after {action}")
            return output

        with patch.object(BundleMigration, "command", interrupt_after_command):
            with self.assertRaisesRegex(OSError, "after detach"):
                self.migrate()
            with self.system.locked():
                with patch("transaction.copy_file", side_effect=OSError("interrupted source placement")):
                    with self.assertRaisesRegex(OSError, "source placement"):
                        self.system.complete()
                self.system.complete()
                with self.assertRaisesRegex(OSError, "after restore"):
                    self.move.rollback()
                self.system.complete()
        self.assert_recovered()

    @unittest.skipUnless(os.environ.get("TAM_BUNDLE_TEST_BIN"), "requires fault-enabled tam-bundle")
    def test_interrupt_inside_bundle_transactions(self):
        run = subprocess.run

        def fault(action, point):
            def instrument(command, *args, **kwargs):
                if str(command[0]) == migration.BUNDLE_TOOL and command[3] == action:
                    command = [str(Path(os.environ["TAM_BUNDLE_TEST_BIN"]).resolve()), *command[1:]]
                    kwargs["env"] = kwargs["env"] | {"TAM_BUNDLE_FAULT": point,
                                                     "ASAN_OPTIONS": "detect_leaks=0"}
                return run(command, *args, **kwargs)
            return patch("migration.subprocess.run", instrument)

        with fault("detach", "detach-placed-unlink"):
            with self.assertRaises(subprocess.CalledProcessError) as result:
                self.migrate()
            self.assertEqual(result.exception.returncode, 99)
        with self.system.locked():
            self.system.complete()
            with fault("apply", "v2-placed-rename"):
                with self.assertRaises(subprocess.CalledProcessError) as result:
                    self.move.rollback()
                self.assertEqual(result.exception.returncode, 99)
            self.system.complete()
        self.assert_recovered()


if __name__ == "__main__":
    unittest.main()
