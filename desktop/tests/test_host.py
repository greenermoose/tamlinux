"""Registry, settings, and clock-adapter checks for the shell proof."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP / "shell" / "host"))
sys.path.insert(0, str(DESKTOP / "adapters"))

import build_patch  # noqa: E402
import registry  # noqa: E402
import settings_store  # noqa: E402


def _manifest(root: Path, plugin_id: str = "fred.clock", entry: str = "BarWidget.qml") -> None:
    (root / "BarWidget.qml").write_text("import QtQuick\nItem {}\n", encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({
        "schemaVersion": 1,
        "id": plugin_id,
        "kinds": ["bar-widget"],
        "entryPoints": {"barWidget": entry},
    }), encoding="utf-8")


class RegistryTests(unittest.TestCase):
    def test_accepts_a_contained_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _manifest(root)
            record = registry.validate_directory(root)
            self.assertEqual(record["id"], "fred.clock")
            self.assertTrue(record["entry"].endswith("BarWidget.qml"))

    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _manifest(root)
            seen = set()
            registry.validate_directory(root, seen)
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root, seen)

    def test_accepts_two_plugins_and_rejects_a_repeated_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = base / "clock"
            second = base / "fixture"
            first.mkdir()
            second.mkdir()
            _manifest(first, "fred.clock")
            _manifest(second, "tamlinux.fixture")
            records = registry.validate_directories([first, second])
            self.assertEqual([item["id"] for item in records], ["fred.clock", "tamlinux.fixture"])
            again = base / "again"
            again.mkdir()
            _manifest(again, "fred.clock")
            with self.assertRaises(registry.RegistryError):
                registry.validate_directories([first, again])

    def test_rejects_malformed_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text("{", encoding="utf-8")
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root)

    def test_rejects_missing_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _manifest(root, entry="Missing.qml")
            (root / "BarWidget.qml").unlink()
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root)

    def test_rejects_parent_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _manifest(root, entry="../outside.qml")
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root)
            target = root / "real.qml"
            target.write_text("Item {}\n", encoding="utf-8")
            link = root / "linked.qml"
            link.symlink_to(target)
            _manifest(root, entry="linked.qml")
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root)
            outside_file = root / "secret"
            outside_file.write_text("x", encoding="utf-8")
            escaped = root / "sub"
            escaped.mkdir()
            (escaped / "jump").symlink_to(outside_file)
            _manifest(root, entry="sub/jump")
            with self.assertRaises(registry.RegistryError):
                registry.validate_directory(root)


class SettingsTests(unittest.TestCase):
    def test_round_trip_and_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "settings"
            directory.mkdir()
            os.chmod(directory, 0o700)
            path = settings_store.write_settings(directory, {
                "version": 1,
                "entries": {"fred.clock": {"id": "fred.clock", "format": "HH:mm", "badgeMinutes": 60}},
            }, {"fred.clock"})
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            loaded = settings_store.read_settings(path, {"fred.clock"})
            self.assertEqual(loaded["entries"]["fred.clock"]["format"], "HH:mm")
            with self.assertRaises(settings_store.SettingsError):
                settings_store.write_settings(directory, {
                    "version": 1,
                    "entries": {"other": {"id": "other"}},
                }, {"fred.clock"})
            with self.assertRaises(settings_store.SettingsError):
                settings_store.validate_document({
                    "version": 1,
                    "entries": {"fred.clock": {"id": "fred.clock", "format": {"bad": True}}},
                }, {"fred.clock"})

    def test_allows_each_registered_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "settings"
            directory.mkdir()
            os.chmod(directory, 0o700)
            allowed = {"fred.clock", "tamlinux.fixture"}
            path = settings_store.write_settings(directory, {
                "version": 1,
                "entries": {
                    "fred.clock": {"id": "fred.clock", "format": "HH:mm"},
                    "tamlinux.fixture": {"id": "tamlinux.fixture", "marker": "step2"},
                },
            }, allowed)
            loaded = settings_store.read_settings(path, allowed)
            self.assertEqual(loaded["entries"]["tamlinux.fixture"]["marker"], "step2")
            with self.assertRaises(settings_store.SettingsError):
                settings_store.validate_document({
                    "version": 1,
                    "entries": {"omarchy.osd": {"id": "omarchy.osd"}},
                }, allowed)

    def test_refuses_a_shared_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "open"
            directory.mkdir()
            os.chmod(directory, 0o755)
            with self.assertRaises(settings_store.SettingsError):
                settings_store.write_settings(directory, {
                    "version": 1,
                    "entries": {"fred.clock": {"id": "fred.clock"}},
                }, {"fred.clock"})


class FixtureTests(unittest.TestCase):
    def test_fixture_has_no_ipc_handler(self):
        text = (DESKTOP / "fixtures" / "panel" / "BarWidget.qml").read_text(encoding="utf-8")
        self.assertIn('moduleName: "tamlinux.fixture"', text)
        self.assertIn("manageIpc: false", text)
        self.assertNotIn("IpcHandler", text)
        shell = (DESKTOP / "shell" / "shell.qml").read_text(encoding="utf-8")
        self.assertEqual(shell.count('target: "tamlinux-shell"'), 1)
        self.assertNotIn('target: "tamlinux.fixture"', shell)


class AdapterTests(unittest.TestCase):
    def test_patch_matches_generator_and_drops_omarchy_routes(self):
        clock = build_patch.repo_default()
        if not (clock / ".git").exists():
            self.skipTest("clock checkout is not available")
        generated = build_patch.build_patch(clock)
        patch_path = DESKTOP / "adapters" / "clock-step1.patch"
        self.assertEqual(patch_path.read_text(encoding="utf-8"), generated)
        added = "\n".join(
            line[1:] for line in generated.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        self.assertIn('target: "tamlinux.clock"', added)
        self.assertNotIn('target: "omarchy.clock"', added)
        self.assertNotIn('target: "fred.clock"', added)
        self.assertNotIn("omarchy-menu-timezone", added)
        self.assertNotIn("qs.Commons", added)
        self.assertIn("TAMLINUX_CLOCK_OFFLINE", added)
        self.assertIn('reportUnsupported("timezone")', added)
        self.assertIn('reportUnsupported("event-edit")', added)


if __name__ == "__main__":
    unittest.main()
