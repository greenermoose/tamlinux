"""Console identity, duplicate-session refusal and literal installed dispatch."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
                    patch.object(console.os, "execve") as execute:
                console.main()
            path, argv, env = execute.call_args.args
            self.assertEqual(path, endpoint)
            self.assertEqual(argv, [str(endpoint)])
            self.assertNotIn("WAYLAND_DISPLAY", env)
            self.assertEqual(env["XDG_SESSION_ID"], "7")

    def test_help_does_not_require_a_tty_or_start_anything(self):
        result = subprocess.run([sys.executable, "-I", str(SOURCE / "console.py"), "/missing", "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: tam-desktop", result.stdout)

    def test_public_help_needs_no_native_providers_or_installed_session_tree(self):
        result = subprocess.run(["/bin/sh", str(SOURCE / "desktop"), "--help"],
                                env={"PATH": "/nonexistent"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: tam-desktop", result.stdout)
