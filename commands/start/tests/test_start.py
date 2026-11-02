import importlib.machinery
import importlib.util
import io
import os
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

start_path = pathlib.Path(__file__).parents[1] / "start"
loader = importlib.machinery.SourceFileLoader("start_cmd", str(start_path))
spec = importlib.util.spec_from_loader("start_cmd", loader)
start_mod = importlib.util.module_from_spec(spec)
sys.modules["start_cmd"] = start_mod
loader.exec_module(start_mod)


class TestStartCommand(unittest.TestCase):
    def test_syntax(self):
        res = subprocess.run([sys.executable, "-m", "py_compile", str(start_path)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Compilation failed: {res.stderr}")

    def test_help_flag(self):
        res = subprocess.run([str(start_path), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("First text-login orientation", res.stdout)
        self.assertIn("--list", res.stdout)
        self.assertIn("--check", res.stdout)

    def test_version_flag(self):
        res = subprocess.run([str(start_path), "--version"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("start (Tamlinux)", res.stdout)

    def test_list_flag(self):
        res = subprocess.run([str(start_path), "--list"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("cataclysm-dda", res.stdout)
        self.assertIn("frotz", res.stdout)
        self.assertIn("tam-desktop", res.stdout)
        self.assertIn("astroterm", res.stdout)

    def test_check_flag(self):
        res = subprocess.run([str(start_path), "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("activities installed", res.stdout)

    def test_menu_rendering_invariants(self):
        menu_text, num_map = start_mod.render_menu()
        self.assertIn("Tamlinux Activities & Start", menu_text)
        self.assertIn("Welcome to Tamlinux", menu_text)
        self.assertIn("Curated Games & Simulations", menu_text)
        self.assertIn("Launch Graphical Desktop", menu_text)
        self.assertIn("Return to shell prompt", menu_text)
        # Verify key map contains desktop and numbered activities
        self.assertIn("d", num_map)
        self.assertEqual(num_map["d"]["command"], ["tam-desktop"])
        self.assertIn("1", num_map)
        self.assertEqual(num_map["1"]["command"], ["tam", "hi"])

    def test_interactive_quit(self):
        # Giving 'q' to interactive_loop should cleanly return 0 without launching anything
        with patch("builtins.input", side_effect=["q"]), \
             patch("builtins.print"), \
             patch("subprocess.run") as mock_run:
            rc = start_mod.interactive_loop()
            self.assertEqual(rc, 0)
            mock_run.assert_not_called()

    def test_interactive_select_activity(self):
        # Selecting an installed activity (e.g. tam hi) calls tam hi, NEVER tam-desktop
        with patch("builtins.input", side_effect=["1", "q"]), \
             patch("builtins.print"), \
             patch.object(start_mod, "is_installed", return_value=True), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = start_mod.interactive_loop()
            self.assertEqual(rc, 0)
            mock_run.assert_called_once_with(["tam", "hi"])

    def test_interactive_select_desktop(self):
        # Selecting 'd' calls tam-desktop and then exits cleanly
        with patch("builtins.input", side_effect=["d"]), \
             patch("builtins.print"), \
             patch.object(start_mod, "is_installed", return_value=True), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = start_mod.interactive_loop()
            self.assertEqual(rc, 0)
            mock_run.assert_called_once_with(["tam-desktop"])


if __name__ == "__main__":
    unittest.main()
