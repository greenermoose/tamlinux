"""Unit tests for the tam-macro command line tool."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
        self.assertIn('bind("SUPER + ALT + M", "Macro: Greeting", "tam-macro run M")', lua_content)

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
        self.assertIn('bind("SUPER + ALT + T", "Macro: Test", "tam-macro run T")', self.hypr_file.read_text())


if __name__ == "__main__":
    unittest.main()
