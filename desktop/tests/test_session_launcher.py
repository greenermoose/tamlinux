"""Exercise the delivered launcher, gate and watchdog with isolated providers."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "session"
spec = importlib.util.spec_from_file_location("wait_stopped", SOURCE / "wait-stopped.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class SessionLauncherTests(unittest.TestCase):
    def test_slow_stopping_session_waits_and_timeout_refuses_start(self):
        now = [0]
        def sleep(seconds): now[0] += seconds
        states = iter([True] * 34 + [False])
        gate.wait(lambda: next(states), lambda: now[0], sleep)
        self.assertEqual(now[0], 17)
        with self.assertRaises(TimeoutError):
            gate.wait(lambda: True, lambda: now[0], sleep, timeout=2)
        self.assertEqual(now[0], 19)

    def test_deactivating_unit_and_lingering_compositor_block_start(self):
        for active, pgrep, expected in [("deactivating", 1, True), ("inactive", 0, True),
                                         ("failed", 1, False), ("active", 1, True)]:
            with patch.object(gate.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 0, json.dumps([{"active": active}])),
                subprocess.CompletedProcess([], pgrep, b"")]):
                self.assertEqual(gate.busy(), expected)

    def test_provider_failure_never_means_stopped(self):
        with patch.object(gate.subprocess, "run", side_effect=subprocess.TimeoutExpired("systemctl", 2)):
            with self.assertRaises(subprocess.TimeoutExpired): gate.busy()

    def test_installed_symlink_preserves_identity_config_argv_and_failure(self):
        with tempfile.TemporaryDirectory(prefix="launcher home ") as temp:
            root = Path(temp)
            session = root / "package/share/tamlinux/session"
            session.mkdir(parents=True)
            binary = root / "package/bin"
            binary.mkdir()
            homebin = root / "home/.local/bin"
            homebin.mkdir(parents=True)
            config = root / "config with spaces/tamlinux/session/hyprland.lua"
            config.parent.mkdir(parents=True)
            config.touch()
            for name in ("tam-theme-init", "tam-session-init"):
                path = homebin / name
                path.write_text("#!/bin/sh\nexit 0\n")
                path.chmod(0o755)
            # Only the system provider is replaced; the entry resolves its own
            # immutable session directory through the managed symlink.
            uwsm = root / "uwsm"
            uwsm.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            uwsm.chmod(0o755)
            start = binary / "tam-hyprland-session"
            start.write_text((SOURCE / "start").read_text().replace("/usr/bin/uwsm", '"' + str(uwsm) + '"'))
            start.chmod(0o755)
            link = homebin / start.name
            link.symlink_to(start)
            (session / "wait-stopped.py").write_text("pass\n")
            env = {"PATH": "/usr/bin:/bin", "HOME": str(root / "home"),
                   "XDG_CONFIG_HOME": str(config.parents[2])}
            result = subprocess.run([str(link)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            argv = json.loads(result.stdout)
            self.assertEqual(argv, ["start", "-e", "-D", "Hyprland", "--", str(session / "Hyprland"),
                                    "--config", str(config)])
            self.assertEqual(Path(argv[5]).name, "Hyprland")
            (session / "wait-stopped.py").write_text("raise SystemExit(23)\n")
            result = subprocess.run([str(link)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 23)
            self.assertEqual(result.stdout, "")

    def test_watchdog_passes_compositor_arguments_literally(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            provider = root / "watchdog"
            provider.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            provider.chmod(0o755)
            wrapper = root / "Hyprland"
            wrapper.write_text((SOURCE / "Hyprland").read_text().replace("/usr/bin/start-hyprland", str(provider)))
            result = subprocess.run(["sh", str(wrapper), "--config", "/a path/config.lua"],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), ["--path", "/usr/bin/Hyprland", "--", "--config", "/a path/config.lua"])
