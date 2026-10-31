"""Unit tests for the tam-macro command line tool."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

CMD = Path(__file__).resolve().parents[1] / "tam-macro"


class TamMacroTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.macros_file = Path(self.temp_dir.name) / "macros.json"
        self.hypr_file = Path(self.temp_dir.name) / "macros.lua"
        self.env = {
            **os.environ,
            "TAMLINUX_MACROS_FILE": str(self.macros_file),
            "TAMLINUX_HYPR_MACROS_FILE": str(self.hypr_file),
            "TAMLINUX_MACRO_SKIP_RELOAD": "1",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cmd(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CMD), *args],
            capture_output=True,
            text=True,
            env=self.env,
        )

    def test_version(self):
        res = self.run_cmd("--version")
        self.assertEqual(res.returncode, 0)
        self.assertIn("tam-macro 0.5.0", res.stdout)

    def test_config_directory_uses_xdg_then_home_then_account_home(self):
        get_config_dir = runpy.run_path(str(CMD))['get_config_dir']
        account = SimpleNamespace(pw_dir='/home/example')
        with patch('pwd.getpwuid', return_value=account), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_config_dir(), Path('/home/example/.config/tamlinux'))
            os.environ['HOME'] = ''
            self.assertEqual(get_config_dir(), Path('/home/example/.config/tamlinux'))
            os.environ['HOME'] = '/home/another'
            self.assertEqual(get_config_dir(), Path('/home/another/.config/tamlinux'))
            os.environ['XDG_CONFIG_HOME'] = '/tmp/example-config'
            self.assertEqual(get_config_dir(), Path('/tmp/example-config/tamlinux'))

    def test_add_and_list_macro(self):
        # Empty initially
        res = self.run_cmd("list")
        self.assertEqual(res.returncode, 0)
        self.assertIn("No macros configured", res.stdout)

        # Add macro
        res = self.run_cmd("add", "M", "Hello world!", "--desc", "Greeting")
        self.assertEqual(res.returncode, 0)

        # Check list output
        res = self.run_cmd("list")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Meta + Alt + M (Greeting): \"Hello world!\"", res.stdout)

        # Check list --json
        res = self.run_cmd("list", "--json")
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["key"], "M")
        self.assertEqual(data[0]["description"], "Greeting")
        self.assertEqual(data[0]["text"], "Hello world!")

        # Verify macros.lua was generated
        self.assertTrue(self.hypr_file.is_file())
        lua_content = self.hypr_file.read_text()
        self.assertIn('bind("SUPER + ALT + M", "Macro: Greeting", "tam-macro run M", { release = true })', lua_content)

    def test_update_existing_macro(self):
        self.run_cmd("add", "M", "First version", "--desc", "Initial")
        res = self.run_cmd("add", "m", "Second version", "--desc", "Updated")
        self.assertEqual(res.returncode, 0)

        res = self.run_cmd("list", "--json")
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["key"], "M")
        self.assertEqual(data[0]["description"], "Updated")
        self.assertEqual(data[0]["text"], "Second version")

    def test_remove_macro(self):
        self.run_cmd("add", "A", "Alpha")
        self.run_cmd("add", "B", "Beta")

        res = self.run_cmd("remove", "A")
        self.assertEqual(res.returncode, 0)

        res = self.run_cmd("list", "--json")
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["key"], "B")

        lua_content = self.hypr_file.read_text()
        self.assertNotIn("SUPER + ALT + A", lua_content)
        self.assertIn("SUPER + ALT + B", lua_content)

    def test_remove_nonexistent_fails(self):
        res = self.run_cmd("remove", "Z")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("no macro found for key 'Z'", res.stderr)

    def test_sync_command(self):
        # Write macros.json directly
        self.macros_file.write_text(json.dumps([
            {"key": "T", "description": "Test", "text": "Test sync"}
        ]))
        res = self.run_cmd("sync")
        self.assertEqual(res.returncode, 0)
        self.assertTrue(self.hypr_file.is_file())
        self.assertIn('bind("SUPER + ALT + T", "Macro: Test", "tam-macro run T", { release = true })', self.hypr_file.read_text())

    def test_generated_lua_has_no_blocking_calls(self):
        self.macros_file.write_text(json.dumps([
            {"key": "C", "description": "Continue", "text": "continue"}
        ]))
        res = self.run_cmd("sync")
        self.assertEqual(res.returncode, 0)
        content = self.hypr_file.read_text()
        self.assertNotIn("io.popen", content)
        self.assertNotIn("os.execute", content)
        self.assertNotIn(":close()", content)
        self.assertNotIn(":read()", content)
        self.assertIn('{ release = true }', content)

    def test_active_window_is_terminal(self):
        active_window_is_terminal = runpy.run_path(str(CMD))['active_window_is_terminal']
        with patch('subprocess.run') as mock_run:
            # Window with terminal tag
            mock_run.return_value = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"tags": ["default-opacity*", "terminal*"], "class": "other"}),
            )
            self.assertTrue(active_window_is_terminal())

            # Window with terminal class
            mock_run.return_value = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"tags": [], "class": "Foot"}),
            )
            self.assertTrue(active_window_is_terminal())

            # GUI application window (e.g. Cursor or browser)
            mock_run.return_value = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"tags": [], "class": "cursor"}),
            )
            self.assertFalse(active_window_is_terminal())

    def test_inject_text_uses_clipboard_and_sendkeystate(self):
        inject_text = runpy.run_path(str(CMD))['inject_text']
        calls = []

        def fake_run(cmd, *args, **kwargs):
            calls.append((cmd, kwargs))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch('time.sleep'), patch('subprocess.run', side_effect=fake_run):
            inject_text("hello world")

        # First call is wl-copy
        wl_copy_call = next((c for c in calls if c[0] == ["wl-copy"]), None)
        self.assertIsNotNone(wl_copy_call)
        self.assertEqual(wl_copy_call[1].get("input"), b"hello world")

        # Subsequent calls are sendkeystate down and up
        down_call = next((c for c in calls if c[0] and c[0][:3] == ["hyprctl", "dispatch", "sendkeystate"] and "down" in c[0][3]), None)
        up_call = next((c for c in calls if c[0] and c[0][:3] == ["hyprctl", "dispatch", "sendkeystate"] and "up" in c[0][3]), None)
        self.assertIsNotNone(down_call)
        self.assertIsNotNone(up_call)


if __name__ == "__main__":
    unittest.main()
