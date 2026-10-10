"""Exercise plugin helpers with the paths their QML consumers watch.

Fixtures contain both migrated and legacy data so a helper that silently
returns to the old namespace cannot pass. No live desktop actions run.
"""
import contextlib
import datetime
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGINS = Path(os.environ.get("TAM_PLUGIN_STORAGE_ROOT")
               or Path(__file__).resolve().parents[1] / "plugins")


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class PluginStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tam-plugin-storage-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / "config"
        self.cache = self.home / "cache"
        self.state = self.home / "state"
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"],
                    "XDG_CONFIG_HOME": str(self.config),
                    "XDG_CACHE_HOME": str(self.cache),
                    "XDG_STATE_HOME": str(self.state), "TZ": "UTC"}

    def run_helper(self, *args):
        result = subprocess.run(args, env=self.env, capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def clock_roundtrip(self):
        plugin = PLUGINS / "fred.clock"
        # Use the same no-path-override commands that BarWidget/Panel launch.
        date = (datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=1)).date().isoformat()
        output = self.run_helper(sys.executable, "-B", str(plugin / "manage-event.py"),
                                 "add", "--date", date, "--summary", "Storage fixture", "--all-day")
        uid = json.loads(output)["uid"]
        config = self.config / "tamlinux/clock"
        cache = self.cache / "tamlinux/clock/events.json"
        self.assertIn("Storage fixture", (config / "local.ics").read_text())
        self.assertEqual(json.loads((config / "calendars.json").read_text())[0]["path"],
                         str(config / "local.ics"))
        self.run_helper(sys.executable, "-B", str(plugin / "fetch-events.py"))
        self.assertEqual([e["summary"] for e in json.loads(cache.read_text())["events"]],
                         ["Storage fixture"])
        self.run_helper(sys.executable, "-B", str(plugin / "manage-event.py"), "delete", "--uid", uid)
        self.run_helper(sys.executable, "-B", str(plugin / "fetch-events.py"))
        self.assertEqual(json.loads(cache.read_text())["events"], [])
        self.assertFalse((self.config / "fred.clock").exists())
        self.assertFalse((self.cache / "fred.clock").exists())
        widget = (plugin / "BarWidget.qml").read_text()
        panel = (plugin / "Panel.qml").read_text()
        for path in ["/tamlinux/clock/calendars.json", "/tamlinux/clock/local.ics",
                     "/tamlinux/clock/events.json"]:
            self.assertIn('"' + path + '"', widget)
        self.assertIn('"/tamlinux/clock/events.json"', panel)

    def test_clock_edit_fetch_delete_with_xdg_homes(self):
        self.clock_roundtrip()

    def test_clock_edit_fetch_delete_with_default_homes(self):
        self.env = {k: v for k, v in self.env.items() if not k.startswith("XDG_")}
        self.config = self.home / ".config"
        self.cache = self.home / ".cache"
        self.clock_roundtrip()

    def test_workspace_state_and_preferences_agree_with_widget(self):
        plugin = PLUGINS / "fred.workspaces"
        config = self.config / "tamlinux/desktop-mode.conf"
        config.parent.mkdir(parents=True)
        config.write_text('left_monitor=DP-2\nright_monitor=DP-1\nunused_monitor_timeout=480\n')
        legacy = self.config / "omarchy/desktop-mode.conf"
        legacy.parent.mkdir()
        legacy.write_text('unused_monitor_timeout=1\n')
        with patch.dict(os.environ, self.env, clear=True):
            helper = load("storage_workspace", plugin / "tam-desktop-mode")
            self.assertEqual(helper.load_full_config()[:2], ("DP-2", "DP-1"))
            helper.atomic_write_state("desktop-mode", "windows\n")
            helper.atomic_write_state("desktop-monitors", '{"version":2,"monitors":["DP-2","DP-1"]}')
        prefs = self.run_helper(sys.executable, "-B", str(plugin / "tam-desktop-mode"), "preferences")
        self.assertEqual(json.loads(prefs), {"unusedMonitorTimeout": 480})
        self.env["TAMLINUX_DESKTOP_UNUSED_MONITOR_TIMEOUT"] = "120"
        self.assertEqual(json.loads(self.run_helper(sys.executable, "-B",
                         str(plugin / "tam-desktop-mode"), "preferences"))["unusedMonitorTimeout"], 120)
        self.assertEqual(self.run_helper(sys.executable, "-B", str(plugin / "tam-desktop-mode"), "status"),
                         (self.state / "tamlinux/desktop-mode").read_text())
        self.assertTrue((self.state / "tamlinux/desktop-monitors").is_file())
        self.assertFalse((self.state / "omarchy").exists())
        widget = (plugin / "Workspaces.qml").read_text()
        for path in ["/tamlinux/desktop-mode", "/tamlinux/desktop-monitors", "/tamlinux/desktop-mode.conf"]:
            self.assertIn('"' + path + '"', widget)

    def test_monitor_lists_and_loads_migrated_layouts(self):
        path = self.state / "tamlinux/monitor/profiles.json"
        path.parent.mkdir(parents=True, mode=0o700)
        layout = [{"name": "DP-1", "width": 1920, "height": 1080}]
        path.write_text(json.dumps({"schemaVersion": 1, "automatic": {},
                                   "user": [{"name": "Migrated", "savedAt": 1, "layout": layout}]}))
        path.chmod(0o600)
        with patch.dict(os.environ, self.env, clear=True):
            helper = load("storage_monitor", PLUGINS / "fred.monitor/fred-monitor-layout")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                helper.list_profiles()
            self.assertIn("Migrated", output.getvalue())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                helper.load_profile("user:Migrated")
            self.assertEqual(json.loads(output.getvalue())["layout"][0]["name"], "DP-1")
            with patch.object(helper, "capture_layout", return_value=helper.validate_layout(layout)), \
                    contextlib.redirect_stdout(io.StringIO()):
                helper.save_profile("New")
        self.assertEqual([p["name"] for p in json.loads(path.read_text())["user"]], ["Migrated", "New"])
        self.assertFalse((self.state / "fred.monitor").exists())

    def test_agent_pipeline_writes_the_widget_usage_directory(self):
        # Real updater with a deterministic sibling collector; no provider API.
        folder = self.home / "pipeline"
        folder.mkdir()
        updater = folder / "tam-agent-usage-update"
        shutil.copy2(PLUGINS / "fred.agents/bin/tam-agent-usage-update", updater)
        collector = folder / "tam-agent-usage-fixture"
        collector.write_text('#!/bin/sh\nprintf \'{"provider":"fixture"}\\n\'\n')
        collector.chmod(0o755)
        self.run_helper("bash", str(updater), "fixture")
        path = self.state / "tamlinux/agents/usage/fixture.json"
        self.assertEqual(json.loads(path.read_text()), {"provider": "fixture"})
        self.assertFalse((self.state / "omarchy").exists())
        self.assertIn('"/tamlinux/agents/usage"', (PLUGINS / "fred.agents/Main.qml").read_text())

    def test_agent_collectors_use_owned_cache(self):
        with patch.dict(os.environ, self.env, clear=True):
            for provider in ["antigravity", "claude", "codex", "cursor"]:
                with self.subTest(provider=provider):
                    helper = load("storage_" + provider, PLUGINS / f"fred.agents/bin/tam-agent-usage-{provider}")
                    self.assertEqual(helper.cache_root(), self.cache / "tamlinux/agents")
        self.assertFalse((self.cache / "omarchy").exists())

    def test_sysinfo_cache_stays_in_owned_namespace(self):
        with patch.dict(os.environ, self.env, clear=True):
            helper = load("storage_sysinfo", PLUGINS / "fred.sysinfo/sysinfo-probe.py")
            self.assertEqual(Path(helper.get_secure_cache_dir()), self.cache / "tamlinux/sysinfo")
            runtime = self.home / "runtime"
            runtime.mkdir(mode=0o700)
            os.environ["XDG_RUNTIME_DIR"] = str(runtime)
            self.assertEqual(Path(helper.get_secure_cache_dir()), runtime / "tamlinux/sysinfo")


if __name__ == "__main__":
    unittest.main()
