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
            "XDG_RUNTIME_DIR": self.temp_dir.name,
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
        self.assertIn('hl.bind("SUPER + ALT + m",', lua_content)
        self.assertIn('description = "Macro: Greeting"', lua_content)

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
        self.assertNotIn('hl.bind("SUPER + ALT + a"', lua_content)
        self.assertIn('hl.unbind("SUPER + ALT + a")', lua_content)
        self.assertIn('hl.bind("SUPER + ALT + b"', lua_content)

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
        self.assertIn('hl.bind("SUPER + ALT + t"', self.hypr_file.read_text())

    def test_sync_maps_punctuation_to_xkb_keysyms(self):
        self.macros_file.write_text(json.dumps([
            {"key": "/", "description": "Exit command", "text": "/exit"},
            {"key": ".", "description": "Dot", "text": "..."},
        ]))
        res = self.run_cmd("sync")
        self.assertEqual(res.returncode, 0)
        content = self.hypr_file.read_text()
        self.assertIn('hl.bind("SUPER + ALT + slash"', content)
        self.assertIn("run -- slash", content)
        self.assertIn('hl.bind("SUPER + ALT + period"', content)
        self.assertNotIn('SUPER + ALT + /', content)
        self.assertNotIn('SUPER + ALT + .', content)

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
        self.assertIn('{ release = true,', content)

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

    def test_named_and_symbol_keys_share_identity(self):
        canonical = runpy.run_path(str(CMD))["key_identity"]
        for alias, name in [("/", "SLASH"), ("backspace", "BACKSPACE"), ("'", "APOSTROPHE"),
                            ("\\", "BACKSLASH"), (";", "SEMICOLON"), (" ", "SPACE"),
                            ("PageUp", "PRIOR"), ("KP_Enter", "KP_ENTER"), ("F24", "F24"),
                            ("code:38", "CODE:38"), ("XF86AudioMute", "XF86AUDIOMUTE")]:
            self.assertEqual(canonical(alias), name)
            self.assertEqual(canonical(name), name)
        for invalid in ("$(touch /tmp/bad)", "BOGUS", "Super_L", "code:0", "code:999"):
            with self.assertRaises(ValueError):
                canonical(invalid)

    def test_alias_update_and_corrupt_file_preserved(self):
        self.assertEqual(self.run_cmd("add", "/", "first").returncode, 0)
        self.assertEqual(self.run_cmd("add", "slash", "second").returncode, 0)
        self.assertEqual(len(json.loads(self.macros_file.read_text())), 1)
        self.macros_file.write_text("invalid JSON")
        self.assertNotEqual(self.run_cmd("add", "B", "text").returncode, 0)
        self.assertEqual(self.macros_file.read_text(), "invalid JSON")

    def replace(self, macros, expected):
        return subprocess.run([sys.executable, str(CMD), "replace"], env=self.env,
                              input=json.dumps({"macros": macros, "expected": expected}),
                              text=True, capture_output=True)

    def test_replace_renames_and_rejects_stale_or_duplicate_data(self):
        old = [{"key": "/", "text": "hello", "description": ""}]
        self.assertEqual(self.replace(old, []).returncode, 0)
        new = [{"key": "Backspace", "text": "bye", "description": ""}]
        self.assertEqual(self.replace(new, old).returncode, 0)
        self.assertEqual(json.loads(self.macros_file.read_text())[0]["key"], "BACKSPACE")
        self.assertIn('hl.unbind("SUPER + ALT + slash")', self.hypr_file.read_text())
        self.assertNotIn('hl.bind("SUPER + ALT + slash"', self.hypr_file.read_text())
        before = self.macros_file.read_text()
        self.assertNotEqual(self.replace(old, old).returncode, 0)
        self.assertNotEqual(self.replace(old + [{"key": "SLASH", "text": "duplicate"}], new).returncode, 0)
        self.assertEqual(self.macros_file.read_text(), before)

    def test_generated_lua_executes_and_quotes_data(self):
        module = runpy.run_path(str(CMD))
        macros = module["validate_macros"]([
            {"key": key, "text": "arbitrary text", "description": 'quote " newline\nbackslash \\ café'}
            for key in ("/", "Backspace", "'", '"', ";", "\\", "`", "$", "(", "+", "code:38")])
        lua = module["generated_lua"](macros)
        quote = module["lua_string"]
        harness = "local bindings = {}\nlocal dispatched = nil\nhl = { get_active_window = function() return {address='0x1'} end, is_key_down = function() return false end, exec_cmd = function(c) dispatched = c end, unbind = function(k) bindings[k] = nil end, bind = function(k,c,o) bindings[k] = {c,o} end }\n"
        checks = []
        import shlex
        for m in macros:
            key = module["to_xkb_keysym"](m["key"])
            command = shlex.join([str(CMD), "run", "--", key])
            checks.append('bindings[' + quote("SUPER + ALT + " + key) + '][1]()')
            checks.append('assert(dispatched == ' + quote(command) + ')')
            checks.append('assert(bindings[' + quote("SUPER + ALT + " + key) + '][2].description == ' + quote("Macro: " + m["description"]) + ')')
        result = subprocess.run(["lua", "-"], input=harness + lua + "\n".join(checks), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_binding_waits_for_modifiers_and_cancels_on_focus_change(self):
        module = runpy.run_path(str(CMD))
        lua = module["generated_lua"]([{"key": "BACKSPACE", "text": "hi", "description": ""}])
        harness = """local callback, timer
local held, address, sent = true, '0x1', 0
hl = {
  get_active_window = function() return {address=address} end,
  is_key_down = function() return held end,
  exec_cmd = function() sent=sent+1 end,
  timer = function(f, opts) assert(opts.timeout == 20); timer=f end,
  unbind = function() end,
  bind = function(k, f, opts) callback=f end
}
"""
        checks = """
callback(); assert(sent == 0 and timer ~= nil)
held=false; timer(); assert(sent == 1)
held=true; callback(); address='0x2'; held=false; timer(); assert(sent == 1)
"""
        result = subprocess.run(["lua", "-"], input=harness+lua+checks, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failed_reload_restores_both_files(self):
        self.run_cmd("add", "A", "old")
        before = [p.read_text() for p in (self.macros_file, self.hypr_file)]
        module = runpy.run_path(str(CMD))
        with patch.dict(os.environ, self.env), patch.dict(module["commit_macros"].__globals__,
                {"reload_config": lambda: (_ for _ in ()).throw(ValueError("reload failed"))}):
            with self.assertRaisesRegex(ValueError, "reload failed"):
                module["commit_macros"]([{"key": "B", "text": "new"}])
        self.assertEqual([p.read_text() for p in (self.macros_file, self.hypr_file)], before)

    def injection(self, *, terminal=False, focus_change=False, down_error=False, clipboard_error=False):
        inject = runpy.run_path(str(CMD))["inject_text"]
        calls, probes = [], []
        def fake_run(cmd, *args, **kwargs):
            calls.append((cmd, kwargs))
            if cmd[:2] == ["hyprctl", "activewindow"]:
                probes.append(True)
                address = "0x2" if focus_change and len(probes) > 1 else "0x1"
                return SimpleNamespace(returncode=0, stdout=json.dumps({"address": address, "class": "foot" if terminal else "editor"}))
            if cmd[0] == "wl-copy" and clipboard_error:
                raise subprocess.CalledProcessError(1, cmd)
            if down_error and cmd[:2] == ["hyprctl", "dispatch"] and '"down"' in cmd[2]:
                raise subprocess.TimeoutExpired(cmd, 5)
            return SimpleNamespace(returncode=0, stdout="ok\n")
        error = None
        with patch.dict(os.environ, self.env), patch('time.sleep'), patch('subprocess.run', side_effect=fake_run):
            try:
                inject("hello\n世界")
            except (ValueError, subprocess.SubprocessError) as e:
                error = e
        return calls, error

    def test_inject_gui_and_terminal_balance_keys_and_preserve_text(self):
        for terminal in (False, True):
            calls, error = self.injection(terminal=terminal)
            self.assertIsNone(error)
            copied = next(c for c in calls if c[0][0] == "wl-copy")
            self.assertEqual(copied[1]["input"], "hello\n世界".encode())
            dispatches = [c[0][2] for c in calls if c[0][:2] == ["hyprctl", "dispatch"]]
            self.assertEqual(len(dispatches), 2)
            self.assertIn('"down"', dispatches[0]); self.assertIn('"up"', dispatches[1])
            for d in dispatches:
                self.assertIn('"address:0x1"', d)
                self.assertIn('"SHIFT"' if terminal else '"CTRL"', d)

    def test_focus_change_and_clipboard_failure_do_not_paste(self):
        for options in ({"focus_change": True}, {"clipboard_error": True}):
            calls, error = self.injection(**options)
            self.assertIsNotNone(error)
            self.assertFalse(any(c[0][:2] == ["hyprctl", "dispatch"] for c in calls))

    def test_timeout_still_releases_without_retrying_paste(self):
        calls, error = self.injection(down_error=True)
        self.assertIsNotNone(error)
        dispatches = [c[0][2] for c in calls if c[0][:2] == ["hyprctl", "dispatch"]]
        self.assertEqual(len(dispatches), 2)
        self.assertIn('"up"', dispatches[-1])
        self.assertFalse(any(c[0][0] == "wtype" for c in calls))

    def test_parallel_operation_is_rejected(self):
        module = runpy.run_path(str(CMD))
        with module["locked"](self.macros_file.with_suffix(".lock")):
            result = self.run_cmd("add", "M", "text")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("still running", result.stderr)


if __name__ == "__main__":
    unittest.main()
