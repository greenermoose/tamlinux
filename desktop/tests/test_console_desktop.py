"""Console identity, duplicate-session refusal and literal installed dispatch."""
import importlib.util
import json
import os
import fcntl
from pathlib import Path
import pty
import signal
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "session"
spec = importlib.util.spec_from_file_location("console_desktop", SOURCE / "console.py")
console = importlib.util.module_from_spec(spec)
spec.loader.exec_module(console)


class ConsoleDesktop(unittest.TestCase):
    def session(self, **changes):
        values = dict(Active="yes", Remote="no", Type="tty", Class="user", User="1000",
                      VTNr="1", Seat="seat0", Id="7")
        values.update(changes)
        return "\n".join(f"{key}={value}" for key, value in values.items())

    def check(self, session=None, units="[]", tty="/dev/tty1", uid=1000, foreground=True):
        with patch.object(console, "query", side_effect=[session or self.session(), units]) as command:
            return console.session_environment(tty, uid, foreground, command)

    def test_foreground_text_login_supplies_actual_identity(self):
        self.assertEqual(self.check(), dict(XDG_SESSION_ID="7", XDG_SEAT="seat0",
                                           XDG_VTNR="1", XDG_SESSION_TYPE="tty"))
        self.assertEqual(self.check(self.session(VTNr="3"), tty="/dev/tty3")["XDG_VTNR"], "3")

    def test_remote_graphical_foreign_inactive_and_wrong_vt_sessions_are_refused(self):
        for changes in (dict(Remote="yes"), dict(Type="wayland"), dict(User="1001"),
                        dict(Active="no"), dict(VTNr="2"), dict(Seat=""), dict(Id=""), dict(Class="greeter")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.check(self.session(**changes))

    def test_ssh_root_and_background_invocations_are_refused_before_bus_queries(self):
        for changes in (dict(tty="/dev/pts/0"), dict(uid=0), dict(foreground=False)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.check(**changes)

    def test_active_and_stopping_sessions_are_refused_without_waiting(self):
        for state in ("active", "activating", "deactivating", "reloading"):
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.check(units=json.dumps([dict(active=state)]))
        self.check(units='[{"active":"inactive"},{"active":"failed"}]')

    def test_unknown_bus_state_is_not_permission_to_start(self):
        for units in ("invalid", "{}", '[{}]'):
            with self.subTest(units=units), self.assertRaises((ValueError, KeyError)):
                self.check(units=units)
        with patch.object(console, "query", side_effect=subprocess.TimeoutExpired("loginctl", 3)) as command:
            with self.assertRaises(subprocess.TimeoutExpired):
                console.session_environment("/dev/tty1", 1000, True, command)

    def test_dispatch_clears_stale_graphics_and_refreshes_login_identity(self):
        with tempfile.TemporaryDirectory(prefix="console home ") as temp:
            endpoint = Path(temp) / "tam-hyprland-session"
            endpoint.touch(mode=0o755)
            identity = self.check()
            with patch.object(sys, "argv", ["console.py", str(endpoint)]), \
                    patch.object(console.os, "ttyname", return_value="/dev/tty1"), \
                    patch.object(console.os, "isatty", return_value=True), \
                    patch.object(console.os, "tcgetpgrp", return_value=os.getpgrp()), \
                    patch.object(console, "session_environment", return_value=identity), \
                    patch.dict(os.environ, {"WAYLAND_DISPLAY": "stale", "XDG_SESSION_ID": "stale"}), \
                    patch.object(console, "guarded_session", return_value=23) as execute:
                self.assertEqual(console.main(), 23)
            path, env = execute.call_args.args
            self.assertEqual(path, endpoint)
            self.assertNotIn("WAYLAND_DISPLAY", env)
            self.assertEqual(env["XDG_SESSION_ID"], "7")

    def test_help_does_not_require_a_tty_or_start_anything(self):
        result = subprocess.run([sys.executable, "-I", str(SOURCE / "console.py"), "/missing", "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: tam-desktop", result.stdout)

    def test_console_is_held_through_desktop_exit_and_unknown_cleanup(self):
        # Real terminal line discipline and signals: an ordinary pipe cannot
        # prove that Ctrl-Z/Ctrl-C or queued input cannot reach the login shell.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            endpoint = root / "desktop"
            endpoint.write_text(
                f'#!{sys.executable}\nimport pathlib,time\n'
                f'root=pathlib.Path({temp!r})\n'
                '(root / "ready").touch()\n'
                'deadline=time.monotonic()+10\n'
                'while not (root / "exit").exists() and time.monotonic()<deadline: time.sleep(.02)\n'
                'raise SystemExit(23)\n')
            endpoint.chmod(0o755)
            runner = root / "runner.py"
            runner.write_text(
                'import importlib.util,os,pathlib\n'
                f'spec=importlib.util.spec_from_file_location("console", {str(SOURCE / "console.py")!r})\n'
                'console=importlib.util.module_from_spec(spec)\nspec.loader.exec_module(console)\n'
                f'root=pathlib.Path({temp!r})\n'
                'def probe():\n'
                '    (root / "cleanup").touch()\n'
                '    if not (root / "stopped").exists(): raise OSError("bus unavailable")\n'
                '    return False\n'
                'raise SystemExit(console.guarded_session(root / "desktop", dict(os.environ), probe))\n')
            master, slave = pty.openpty()
            original = termios.tcgetattr(slave)

            def controlling_terminal():
                os.setsid()
                fcntl.ioctl(0, termios.TIOCSCTTY, 0)

            child = subprocess.Popen([sys.executable, str(runner)], stdin=slave,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     preexec_fn=controlling_terminal)
            def wait_file(name):
                deadline = time.monotonic() + 5
                while not (root / name).exists():
                    if child.poll() is not None or time.monotonic() > deadline:
                        self.fail(f"guard did not reach {name}; exit={child.poll()}")
                    time.sleep(.02)

            try:
                wait_file("ready")
                mode = termios.tcgetattr(slave)
                self.assertFalse(mode[3] & (termios.ISIG | termios.ECHO))
                os.write(master, b'\x1a\x03echo SHOULD_NOT_REACH_SHELL\npartial')
                os.kill(child.pid, signal.SIGTSTP)
                time.sleep(.1)
                self.assertIsNone(child.poll())
                status = Path(f"/proc/{child.pid}/status").read_text()
                self.assertNotIn("State:\tT", status)
                (root / "exit").touch()
                wait_file("cleanup")
                self.assertIsNone(child.poll())
                self.assertFalse(termios.tcgetattr(slave)[3] & termios.ISIG)
                (root / "stopped").touch()
                stdout, stderr = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 23, (stdout, stderr))
                self.assertEqual(termios.tcgetattr(slave), original)
                os.set_blocking(slave, False)
                with self.assertRaises(BlockingIOError):
                    os.read(slave, 4096)
            finally:
                (root / "exit").touch()
                (root / "stopped").touch()
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=5)
                os.close(master)
                os.close(slave)

    def test_failed_exec_restores_console_and_signal_handlers(self):
        master, slave = pty.openpty()
        original = termios.tcgetattr(slave)
        handlers = {s: signal.getsignal(s) for s in (signal.SIGTSTP, signal.SIGTERM)}
        try:
            with patch.object(console.termios, "tcgetattr", return_value=original), \
                    patch.object(console.termios, "tcsetattr") as setattrs, \
                    patch.object(console.subprocess, "Popen", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    console.guarded_session(Path("/missing"), {})
            self.assertEqual(setattrs.call_args.args, (0, termios.TCSAFLUSH, original))
            self.assertEqual({s: signal.getsignal(s) for s in handlers}, handlers)
        finally:
            os.close(master)
            os.close(slave)

    def test_external_termination_stops_graphics_before_releasing_console(self):
        master, slave = pty.openpty()
        original = termios.tcgetattr(slave)
        child = Mock(returncode=-signal.SIGTERM)

        def terminate_while_waiting():
            child.wait.side_effect = None
            os.kill(os.getpid(), signal.SIGTERM)

        child.wait.side_effect = terminate_while_waiting
        probe = Mock(side_effect=[True, False])
        try:
            with patch.object(console.termios, "tcgetattr", return_value=original), \
                    patch.object(console.termios, "tcsetattr"), \
                    patch.object(console.subprocess, "Popen", return_value=child), \
                    patch.object(console.subprocess, "run") as stop, \
                    patch.object(console.time, "sleep"):
                self.assertEqual(console.guarded_session(Path("/desktop"), {}, probe), 143)
            child.terminate.assert_called_once()
            stop.assert_called_once_with(["/usr/bin/uwsm", "stop"],
                                         stdin=subprocess.DEVNULL, timeout=10, check=True)
            self.assertEqual(probe.call_count, 2)
        finally:
            os.close(master)
            os.close(slave)

    def test_public_help_needs_no_native_providers_or_installed_session_tree(self):
        result = subprocess.run(["/bin/sh", str(SOURCE / "desktop"), "--help"],
                                env={"PATH": "/nonexistent"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: tam-desktop", result.stdout)
