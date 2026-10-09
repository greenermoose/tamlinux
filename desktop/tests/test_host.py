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
import session_start  # noqa: E402
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


class RegistryCommandTests(unittest.TestCase):
    """registry.py as a command: validate one plugin, map a plugins directory."""

    SCRIPT = DESKTOP / "shell" / "host" / "registry.py"

    def run_registry(self, *args):
        import subprocess
        return subprocess.run([sys.executable, "-I", str(self.SCRIPT), *args],
                              capture_output=True, text=True, timeout=20)

    def test_validate_prints_the_record_or_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fred.clock"
            root.mkdir()
            _manifest(root)
            done = self.run_registry("validate", str(root))
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)["id"], "fred.clock")
            (root / "BarWidget.qml").unlink()
            done = self.run_registry("validate", str(root))
            self.assertEqual(done.returncode, 1)
            self.assertIn("entry point does not exist", done.stderr)
            self.assertEqual(done.stdout, "")

    def test_entries_leave_a_bad_plugin_off_and_say_so(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name in ("fred.clock", "fred.weather", "fred.broken", "fred.misnamed"):
                (base / name).mkdir()
            _manifest(base / "fred.clock", "fred.clock")
            _manifest(base / "fred.weather", "fred.weather")
            _manifest(base / "fred.broken", "fred.broken", entry="Missing.qml")
            _manifest(base / "fred.misnamed", "fred.other")
            (base / ".fred.clock.test.1").mkdir()
            (base / "README").write_text("not a plugin\n", encoding="utf-8")
            done = self.run_registry("entries", str(base))
            self.assertEqual(done.returncode, 0, done.stderr)
            entries = json.loads(done.stdout)
            self.assertEqual(sorted(entries), ["fred.clock", "fred.weather"])
            self.assertTrue(entries["fred.clock"].endswith("/fred.clock/BarWidget.qml"))
            self.assertIn("left off the bar: fred.broken: entry point does not exist", done.stderr)
            self.assertIn("left off the bar: fred.misnamed: manifest id 'fred.other'", done.stderr)

    def test_entries_follow_a_linked_plugin_directory(self):
        # Home Manager links each deployed plugin directory into the store.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            store = base / "store-fred.clock"
            store.mkdir()
            _manifest(store, "fred.clock")
            plugins = base / "plugins"
            plugins.mkdir()
            (plugins / "fred.clock").symlink_to(store)
            entries, problems = registry.plugin_entries(plugins)
            self.assertEqual(problems, [])
            self.assertEqual(entries, {"fred.clock": str((store / "BarWidget.qml").resolve())})

    def test_usage_and_missing_directory(self):
        self.assertEqual(self.run_registry().returncode, 2)
        done = self.run_registry("entries", "/nonexistent/plugins")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(json.loads(done.stdout), {})
        self.assertIn("not a directory", done.stderr)


class SessionStartTests(unittest.TestCase):
    """The session unit's start script: plugin map, layout path, backend path."""

    def test_services_only_adds_nothing_but_the_import_and_backend_paths(self):
        env, notes = session_start.session_environment({"HOME": "/home/u", "TAMLINUX_BAR": "0"})
        self.assertEqual(notes, [])
        self.assertEqual(env["QML_IMPORT_PATH"], str(DESKTOP / "shell" / "modules"))
        self.assertEqual(env["TAMLINUX_COMPOSITOR_COMMANDS"], str(DESKTOP / "shell" / "host"))
        self.assertNotIn("TAMLINUX_PLUGIN_ENTRIES", env)
        self.assertNotIn("TAMLINUX_BAR_LAYOUT", env)

    def test_bar_maps_the_deployed_plugins_and_names_the_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config"
            plugins = config / "tamlinux" / "plugins"
            (plugins / "fred.clock").mkdir(parents=True)
            (plugins / "fred.broken").mkdir()
            _manifest(plugins / "fred.clock", "fred.clock")
            _manifest(plugins / "fred.broken", "fred.broken", entry="Missing.qml")
            env, notes = session_start.session_environment(
                {"HOME": "/home/u", "XDG_CONFIG_HOME": str(config)})
            self.assertEqual(env["TAMLINUX_BAR_LAYOUT"], str(config / "tamlinux" / "shell" / "layout.json"))
            entries = json.loads(env["TAMLINUX_PLUGIN_ENTRIES"])
            self.assertEqual(list(entries), ["fred.clock"])
            self.assertIn("left off the bar: fred.broken: entry point does not exist: Missing.qml", notes)
            self.assertIn("plugins: fred.clock", notes)
            backend = Path(env["TAMLINUX_COMPOSITOR_COMMANDS"])
            self.assertTrue((backend / "hyprland_backend.py").is_file())
            self.assertTrue((backend / "compositor_commands.py").is_file())

    def test_the_environment_wins(self):
        env, notes = session_start.session_environment({
            "HOME": "/home/u", "QML_IMPORT_PATH": "/x", "TAMLINUX_BAR_LAYOUT": "/l.json",
            "TAMLINUX_PLUGIN_ENTRIES": "{}", "TAMLINUX_COMPOSITOR_COMMANDS": "/c"})
        self.assertEqual((env["QML_IMPORT_PATH"], env["TAMLINUX_BAR_LAYOUT"], env["TAMLINUX_PLUGIN_ENTRIES"],
                          env["TAMLINUX_COMPOSITOR_COMMANDS"]),
                         ("/x", "/l.json", "{}", "/c"))
        self.assertEqual(notes, [])

    def test_no_plugins_directory_is_not_fatal(self):
        env, notes = session_start.session_environment(
            {"HOME": "/nonexistent-home", "TAMLINUX_PLUGINS_DIR": "/nonexistent/plugins"})
        self.assertEqual(json.loads(env["TAMLINUX_PLUGIN_ENTRIES"]), {})
        self.assertIn("plugins: none", notes)


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


class BarWindowTests(unittest.TestCase):
    def test_daily_bar_reserves_its_own_height(self):
        # ExclusionMode.Normal reserves only an explicit exclusiveZone (0 by
        # default); Auto reserves the bar's height.
        text = (DESKTOP / "shell" / "host" / "BarWindow.qml").read_text(encoding="utf-8")
        self.assertIn('=== "1" ? ExclusionMode.Auto : ExclusionMode.Ignore', text)
        self.assertNotIn("ExclusionMode.Normal", text)

    def test_tooltip_overlay_structure_and_version_footer(self):
        text = (DESKTOP / "shell" / "host" / "BarWindow.qml").read_text(encoding="utf-8")
        self.assertIn("parsedTooltip", text)
        self.assertIn("tipLabel", text)
        self.assertIn("tipFooterLabel", text)
        self.assertIn("Style.font.caption", text)
        self.assertIn("opacity: 0.45", text)
        self.assertIn("horizontalAlignment: Text.AlignHCenter", text)


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
