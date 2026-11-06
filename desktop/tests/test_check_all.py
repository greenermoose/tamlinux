"""Tests for desktop/check-all, run against a small throwaway repository."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "check-all"
loader = importlib.machinery.SourceFileLoader("check_all", str(SCRIPT))
spec = importlib.util.spec_from_loader("check_all", loader)
check_all = importlib.util.module_from_spec(spec)
loader.exec_module(check_all)

PASSING = "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): pass\n"
SKIPPING = ("import unittest\nclass T(unittest.TestCase):\n"
            "    @unittest.skip('no such device')\n    def test_skip(self): pass\n")
FAILING = "import unittest\nclass T(unittest.TestCase):\n    def test_no(self): self.fail('broken')\n"
SESSION_CHECK = ("import os, unittest\nclass T(unittest.TestCase):\n"
                 "    def test_clean(self): self.assertNotIn('TAMLINUX_BIN', os.environ)\n")


class Repository:
    def __init__(self, root, tests, dirty=None):
        self.root = Path(root)
        tools = self.root / "desktop"
        (tools / "tests").mkdir(parents=True)
        shutil.copy(SCRIPT, tools / "check-all")
        for name, text in tests.items():
            (tools / "tests" / name).write_text(text)
        command = self.root / "commands/tam-sample"
        command.mkdir(parents=True)
        (command / "Makefile").write_text("check:\n\t@true\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "fixture")
        for name, text in (dirty or {}).items():
            (tools / "tests" / name).write_text(text)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True)

    def run(self, *args, env=None):
        report = self.root.parent / "report.json"
        done = subprocess.run([sys.executable, str(self.root / "desktop/check-all"), "--report", str(report), *args],
                              env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=60)
        return done, json.loads(report.read_text()) if report.exists() else None


class Environment(unittest.TestCase):
    def test_session_variables_are_removed_and_the_rest_kept(self):
        env = check_all.clean_environment({
            "HOME": "/home/alex", "PATH": "/usr/bin", "PKG_CONFIG_PATH": "/dev/lib", "XDG_RUNTIME_DIR": "/run/user/1",
            "TAMLINUX_BIN": "x", "HYPRLAND_INSTANCE_SIGNATURE": "x", "WAYLAND_DISPLAY": "x", "DISPLAY": "x",
            "QT_QPA_PLATFORM": "x", "XDG_CURRENT_DESKTOP": "x", "XDG_SESSION_ID": "x"})
        self.assertEqual(sorted(env), ["HOME", "PATH", "PKG_CONFIG_PATH", "XDG_RUNTIME_DIR"])

    def test_opt_in_proofs_need_the_flag(self):
        self.assertNotIn("TAMLINUX_GTK_PROOF", check_all.clean_environment({}))
        env = check_all.clean_environment({}, proofs=True)
        self.assertEqual((env["TAMLINUX_GTK_PROOF"], env["TAMLINUX_DCONF_PROOF"]), ("1", "1"))


class Skips(unittest.TestCase):
    def test_reasons_come_from_verbose_output(self):
        output = "test_a (x.T.test_a) ... skipped 'no such device'\nOK (skipped=1)\n"
        self.assertEqual(check_all.parse_skips(output), ["no such device"])

    def test_a_skip_without_a_shown_reason_is_still_counted(self):
        self.assertEqual(check_all.parse_skips("OK (skipped=2)\n"), ["reason not shown"] * 2)


class Runs(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)

    def test_passing_suite_reports_units_and_skip_reasons(self):
        repository = Repository(self.base / "repo", {"test_a.py": PASSING, "test_b.py": SKIPPING})
        done, report = repository.run()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual([(unit["kind"], unit["name"]) for unit in report["units"]],
                         [("desktop", "test_a"), ("desktop", "test_b"), ("command", "tam-sample")])
        self.assertIn("1 in test_b: no such device", done.stdout)
        self.assertIn("PASSED", done.stdout)

    def test_failure_is_named_and_stops_with_status_one(self):
        repository = Repository(self.base / "repo", {"test_a.py": FAILING})
        done, report = repository.run()
        self.assertEqual(done.returncode, 1)
        self.assertFalse(report["passed"])
        self.assertIn("FAILED desktop test_a", done.stdout)
        self.assertIn("NOT PASSED", done.stdout)

    def test_uncommitted_edits_are_not_tested(self):
        repository = Repository(self.base / "repo", {"test_a.py": PASSING}, dirty={"test_a.py": FAILING})
        done, _ = repository.run()
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_units_do_not_see_session_variables(self):
        repository = Repository(self.base / "repo", {"test_a.py": SESSION_CHECK})
        done, _ = repository.run(env={"TAMLINUX_BIN": "/real/bin"})
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_unknown_revision_cannot_start(self):
        repository = Repository(self.base / "repo", {"test_a.py": PASSING})
        done, report = repository.run("--rev", "no-such-revision")
        self.assertEqual(done.returncode, 2)
        self.assertIsNone(report)


if __name__ == "__main__":
    unittest.main()
