import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

CLI = Path(__file__).resolve().parents[1] / "tam-fleet"
loader = importlib.machinery.SourceFileLoader("tam_fleet", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
fleet = importlib.util.module_from_spec(spec)
loader.exec_module(fleet)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                   stderr=subprocess.DEVNULL).strip()


class FleetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root / "config"
        self.registry = self.root / "registry"
        for root in [self.config, self.registry]:
            root.mkdir()
            git(root, "init", "-q")
            git(root, "config", "user.name", "Fixture")
            git(root, "config", "user.email", "fixture@example.invalid")
        for path, text in {"flake.nix": "{ }", "capabilities/desktop-common.nix": "{ }",
                           "hardware.md": "# Test hardware", "system/MANIFEST": "# shared\n"}.items():
            dest = self.config / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
        (self.registry / "README-systems.md").write_text(f"# Fleet\n\n{fleet.BEGIN}\n{fleet.END}\n")
        self.fleet = fleet.Fleet(self.config, self.registry)
        for name in ["alpha", "beta"]:
            self.fleet.register(name, "tester", "test machine", "hardware.md", ["desktop-common"],
                                "x86_64-linux", "/home/tester")
        self.commit()

    def commit(self):
        for root in [self.config, self.registry]:
            git(root, "add", "--all")
            git(root, "commit", "-qm", "fixture", "--allow-empty")

    def local(self, name="alpha"):
        return patch.object(fleet.os, "uname", return_value=SimpleNamespace(nodename=name))

    def observed(self, *args, **kwargs):
        if args[0] == "pacman":
            return "package-" + args[1]
        return self.original_run(*args, **kwargs)

    def test_register_is_explicit_and_does_not_clone_other_hosts(self):
        root = self.config / "hosts/beta"
        self.assertEqual(list((root / "system").iterdir()), [root / "system/MANIFEST"])
        self.assertFalse((root / "state").exists())
        self.assertNotIn("alpha", (root / "home.nix").read_text())
        self.fleet.check()

    def test_repeat_registration_preserves_existing_identity(self):
        with self.assertRaisesRegex(fleet.FleetError, "already registered"):
            self.fleet.register("alpha", "tester", "replacement", "hardware.md", [], "x86_64-linux", None)

    def test_rejects_traversal_before_any_writes(self):
        for name in ["../escape", "Alpha", "a/b", "-bad", "two.names"]:
            with self.assertRaises(fleet.FleetError):
                self.fleet.register(name, "tester", "bad", "hardware.md", [], "x86_64-linux", None)
        self.assertFalse((self.root / "escape").exists())

    def test_rejects_unknown_capability_without_partial_registration(self):
        with self.assertRaisesRegex(fleet.FleetError, "unknown capability"):
            self.fleet.register("gamma", "tester", "test", "hardware.md", ["unreviewed"], "x86_64-linux", None)
        self.assertFalse((self.config / "hosts/gamma").exists())

    def test_rejects_mismatched_filename_id_and_hostname(self):
        path = self.registry / "alpha.md"
        path.write_text(path.read_text().replace('id = "alpha"', 'id = "beta"'))
        with self.assertRaisesRegex(fleet.FleetError, "agree uniquely"):
            self.fleet.check()

    def test_detects_missing_active_profile(self):
        path = self.registry / "alpha.md"
        path.write_text(path.read_text().replace('status = "planned"', 'status = "active"'))
        (self.config / "hosts/alpha").rename(self.config / "alpha-away")
        with self.assertRaisesRegex(fleet.FleetError, "missing host directory"):
            self.fleet.check()

    def test_detects_orphan_host_and_missing_hardware(self):
        (self.config / "hosts/orphan").mkdir()
        with self.assertRaisesRegex(fleet.FleetError, "without registry"):
            self.fleet.check()
        (self.config / "hosts/orphan").rmdir()
        (self.config / "hardware.md").unlink()
        with self.assertRaisesRegex(fleet.FleetError, "missing local hardware"):
            self.fleet.check()

    def test_detects_broken_local_link(self):
        path = self.registry / "alpha.md"
        path.write_text(path.read_text() + "\n[missing](missing.md)\n")
        with self.assertRaisesRegex(fleet.FleetError, "missing linked page"):
            self.fleet.check()

    def test_stale_index_fails_and_index_repairs_only_generated_block(self):
        path = self.registry / "alpha.md"
        path.write_text(path.read_text().replace('role = "test machine"', 'role = "new role"'))
        with self.assertRaisesRegex(fleet.FleetError, "index is stale"):
            self.fleet.check()
        self.fleet.index()
        self.fleet.check()
        self.assertTrue((self.registry / "README-systems.md").read_text().startswith("# Fleet\n\n"))

    def test_cross_host_capture_is_refused_before_observation(self):
        with self.local("beta"), patch.object(fleet, "run") as run:
            with self.assertRaisesRegex(fleet.FleetError, "capture refused"):
                self.fleet.capture("alpha")
            run.assert_not_called()

    def test_captures_from_both_hosts_never_write_shared_or_neighbor_state(self):
        self.original_run = fleet.run
        shared = (self.config / "system/MANIFEST").read_bytes()
        with patch.object(fleet, "run", side_effect=self.observed), patch.object(fleet.Path, "home", return_value=self.root):
            with self.local("alpha"):
                self.fleet.capture("alpha")
            alpha = {p.name: p.read_bytes() for p in (self.config / "hosts/alpha/state").iterdir()}
            with self.local("beta"):
                self.fleet.capture("beta")
            self.assertEqual(alpha, {p.name: p.read_bytes() for p in (self.config / "hosts/alpha/state").iterdir()})
        self.assertEqual((self.config / "system/MANIFEST").read_bytes(), shared)
        self.assertFalse((self.config / "system/bom.json").exists())
        self.assertEqual(json.loads((self.config / "hosts/beta/state/bom.json").read_text())["hostname"], "beta")

    def test_capture_preserves_uncommitted_state(self):
        state = self.config / "hosts/alpha/state"
        state.mkdir()
        (state / "bom.json").write_text("user edits")
        with self.local(), self.assertRaisesRegex(fleet.FleetError, "local edits"):
            self.fleet.capture("alpha")
        self.assertEqual((state / "bom.json").read_text(), "user edits")

    def test_symlinked_state_cannot_overwrite_neighbor(self):
        (self.config / "hosts/beta/state").mkdir()
        (self.config / "hosts/alpha/state").symlink_to("../beta/state", target_is_directory=True)
        self.commit()
        self.original_run = fleet.run
        with self.local(), patch.object(fleet, "run", side_effect=self.observed), patch.object(fleet.Path, "home", return_value=self.root):
            with self.assertRaisesRegex(fleet.FleetError, "symlink destination"):
                self.fleet.capture("alpha")
        self.assertEqual(list((self.config / "hosts/beta/state").iterdir()), [])

    def test_root_union_and_capability_opt_in(self):
        root = self.config / "hosts/alpha/system"
        (root / "etc").mkdir()
        (root / "etc/example").write_text("host only\n")
        (root / "MANIFEST").write_text("/etc/example 640\n")
        self.assertEqual(self.fleet.root_files("alpha"), [(root / "etc/example", "/etc/example", 0o640)])
        self.assertEqual(self.fleet.root_files("beta"), [])
        fragment = root / "capabilities/optional/MANIFEST"
        fragment.parent.mkdir(parents=True)
        fragment.write_text("/etc/missing 644\n")
        # An unselected root fragment cannot leak into this machine's preview.
        self.assertEqual(len(self.fleet.root_files("alpha")), 1)

    def test_root_traversal_and_duplicate_are_refused(self):
        root = self.config / "hosts/alpha/system"
        (root / "MANIFEST").write_text("/../etc/passwd 644\n")
        with self.assertRaisesRegex(fleet.FleetError, "invalid root target"):
            self.fleet.root_files("alpha")
        (root / "etc").mkdir()
        (root / "etc/example").write_text("host")
        (root / "MANIFEST").write_text("/etc/example 644\n/etc/example 755\n")
        with self.assertRaisesRegex(fleet.FleetError, "duplicate root target"):
            self.fleet.root_files("alpha")

    def test_failed_reconciliation_never_marks_machine_current(self):
        before = (self.registry / "alpha.md").read_bytes()
        index = (self.registry / "README-systems.md").read_bytes()
        with self.local(), patch.object(self.fleet, "check", side_effect=[None, fleet.FleetError("not installed")]):
            with self.assertRaisesRegex(fleet.FleetError, "not installed"):
                self.fleet.reconcile("alpha")
        self.assertEqual((self.registry / "alpha.md").read_bytes(), before)
        self.assertEqual((self.registry / "README-systems.md").read_bytes(), index)
        self.assertFalse((self.config / "hosts/alpha/state/reconciliation.json").exists())

    def test_successful_fixture_reconciliation_commits_only_host_paths(self):
        self.original_run = fleet.run
        (self.config / "unrelated").write_text("neighbor work")
        with self.local(), patch.object(fleet, "run", side_effect=self.observed), \
             patch.object(fleet.Path, "home", return_value=self.root), patch.object(self.fleet, "check"):
            self.fleet.reconcile("alpha", commit=True)
        self.assertIn("last_reconciled", self.fleet.records()["alpha"])
        self.assertEqual(self.fleet.records()["alpha"]["status"], "active")
        self.assertEqual(self.fleet.records()["beta"]["status"], "planned")
        self.assertIn("?? unrelated", git(self.config, "status", "--short"))
        self.assertNotIn("unrelated", git(self.config, "show", "--format=", "--name-only", "HEAD"))
        self.assertFalse((self.config / "hosts/beta/state").exists())

    def test_writer_lock_refuses_concurrent_capture(self):
        with self.fleet.locked():
            with self.assertRaisesRegex(fleet.FleetError, "another fleet writer"):
                with self.fleet.locked():
                    self.fail("second writer acquired lock")


if __name__ == "__main__":
    unittest.main()
