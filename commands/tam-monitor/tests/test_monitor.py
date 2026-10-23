"""No real console ioctls or monitor writes: sysfs, devices and tools are fixtures."""

import fcntl
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import signal
import stat
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "tam-monitor"
loader = importlib.machinery.SourceFileLoader("monitor", str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
loader.exec_module(m)


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.drm = self.root / "drm"
        self.backlight = self.root / "backlight"
        self.drm.mkdir()
        self.backlight.mkdir()
        self.calls = []
        self.value = 50
        self.hw = m.Hardware(self.drm, self.backlight, self.run_tool)

    def run_tool(self, args):
        self.calls.append(args)
        if args[0] == "tam-brightness-display-ddc":
            if len(args) == 3:
                self.value = int(args[-1].removesuffix("%"))
            return str(self.value)
        if args[0] == "tam-hw-display":
            return "intel_backlight"
        if args[0] == "brightnessctl":
            (self.backlight / "intel_backlight/brightness").write_text(args[-1].removesuffix("%"))
            return ""
        self.fail(args)

    def connector(self, name="card1-DP-1", status="connected"):
        path = self.drm / name
        path.mkdir()
        (path / "status").write_text(status)
        (path / "enabled").write_text("enabled")
        return path

    def test_without_graphical_environment_and_no_probe(self):
        self.connector()
        with patch.dict(os.environ, {}, clear=True):
            item, = self.hw.discover(False)
        self.assertEqual(item.connection, "connected")
        self.assertEqual(item.brightness, None)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.hw.read_brightness(item), 50)
        self.assertFalse(any("hypr" in str(c) or "qs" in c for c in self.calls))

    def test_ddc_write_is_verified_and_hotplug_remapped(self):
        path = self.connector()
        self.assertEqual(self.hw.set_brightness("DP-1", 75), 75)
        self.assertEqual(self.calls[-2:], [["tam-brightness-display-ddc", "DP-1", "75%"],
                                         ["tam-brightness-display-ddc", "DP-1"]])
        (path / "status").write_text("disconnected")
        self.calls.clear()
        with self.assertRaises(m.MonitorError):
            self.hw.set_brightness("card1-DP-1", 50)
        self.assertEqual(self.calls, [])

    def test_stale_hardware_write_is_failure(self):
        self.connector()
        self.hw.run = lambda args: "50"
        with self.assertRaisesRegex(m.MonitorError, "verification failed"):
            self.hw.set_brightness("DP-1", 75)

    def test_permission_failure_is_unknown_not_off(self):
        self.connector()
        def denied(args):
            raise m.MonitorError("permission denied")
        self.hw.run = denied
        item, = self.hw.discover()
        self.assertIsNone(item.brightness)
        self.assertIn("permission denied", item.brightness_detail)

    def test_ambiguous_card_connector_disables_ddc(self):
        self.connector()
        self.connector("card2-DP-1")
        self.assertTrue(all(not x.brightness_backend for x in self.hw.discover()))
        with self.assertRaises(m.MonitorError):
            self.hw.set_brightness("card1-DP-1", 50)
        self.assertFalse(self.calls)

    def test_internal_backlight_and_ambiguous_internal_mapping(self):
        self.connector("card1-eDP-1")
        device = self.backlight / "intel_backlight"
        device.mkdir()
        (device / "brightness").write_text("40")
        (device / "max_brightness").write_text("100")
        self.assertEqual(self.hw.set_brightness("eDP-1", 65), 65)
        self.assertIn(["brightnessctl", "-d", "intel_backlight", "set", "65%"], self.calls)
        self.connector("card2-eDP-2")
        self.calls.clear()
        self.assertTrue(all(not x.brightness_backend for x in self.hw.discover()))
        self.assertFalse(self.calls)

    def test_out_of_range_brightness_never_writes(self):
        self.connector()
        for value in (0, -1, 101):
            with self.assertRaises(m.MonitorError):
                self.hw.set_brightness("DP-1", value)
        self.assertEqual(self.calls, [])

    def test_removed_and_malformed_connector_metadata(self):
        self.connector(status="unknown")
        self.connector("card1-evil;command")
        item, = self.hw.discover()
        self.assertEqual(item.identity, "EDID unavailable")
        self.assertFalse(self.calls)
        self.assertEqual(m.clean("bad\x1b[31m\nvalue"), "bad?[31m?value")

    def test_valid_edid_and_control_characters(self):
        path = self.connector()
        edid = bytearray(128)
        edid[:8] = b"\0\xff\xff\xff\xff\xff\xff\0"
        edid[8:10] = (0x10AC).to_bytes(2, "big")  # DEL
        edid[54:59] = b"\0\0\0\xfc\0"
        edid[59:72] = b"Fixture\x1b LCD\n "
        edid[127] = -sum(edid) % 256
        (path / "edid").write_bytes(edid)
        self.assertIn("Fixture? LCD", self.hw.discover(False)[0].identity)
        edid[127] ^= 1
        (path / "edid").write_bytes(edid)
        self.assertEqual(self.hw.discover(False)[0].identity, "EDID unavailable")

    def test_cancel_stops_further_hardware_queries(self):
        import threading
        self.connector()
        event = threading.Event()
        event.set()
        self.hw.discover(cancel=event)
        self.assertFalse(self.calls)


class ConsoleTests(unittest.TestCase):
    def console(self):
        info = type("Info", (), dict(st_mode=stat.S_IFCHR, st_rdev=os.makedev(4, 2), st_uid=os.getuid()))
        with patch.object(os, "fstat", return_value=info):
            return m.Console(80)

    def test_rejects_pseudoterminal_and_foreign_owned_vt(self):
        master, slave = pty.openpty()
        try:
            with self.assertRaises(m.MonitorError):
                m.Console(slave)
        finally:
            os.close(master)
            os.close(slave)
        console = self.console()
        with patch.object(os, "fstat", return_value=type("Info", (), dict(
                st_mode=stat.S_IFCHR, st_rdev=os.makedev(4, 2), st_uid=os.getuid() + 1))):
            with self.assertRaises(m.MonitorError):
                m.Console(80)

    def test_inactive_graphical_or_background_cannot_change_idle(self):
        console = self.console()
        for active, group in ((False, os.getpgrp()), (True, os.getpgrp() + 1)):
            with patch.object(console, "active_text", return_value=active), \
                    patch.object(os, "tcgetpgrp", return_value=group), patch.object(os, "write") as write:
                with self.assertRaises(m.MonitorError):
                    console.idle(5)
                write.assert_not_called()

    def test_idle_uses_only_console_timer_sequence(self):
        console = self.console()
        with patch.object(console, "active_text", return_value=True), \
                patch.object(os, "tcgetpgrp", return_value=os.getpgrp()), patch.object(os, "write") as write, \
                patch.object(termios, "tcdrain"), patch.object(m, "console_idle_seconds", return_value=300):
            self.assertTrue(console.idle(5))
            write.assert_called_once_with(80, b"\x1b[9;5]")
            with self.assertRaises(m.MonitorError):
                console.idle(61)

    def test_idle_readback_rejects_a_failed_timer_change(self):
        console = self.console()
        with patch.object(console, "require_active"), patch.object(os, "write"), \
                patch.object(termios, "tcdrain"), patch.object(m, "console_idle_seconds", return_value=0):
            with self.assertRaisesRegex(m.MonitorError, "verification failed"):
                console.idle(5)

    def test_readonly_vt_state_distinguishes_graphical_mode(self):
        console = self.console()
        state = {"active": 2, "mode": 0}
        def ioctl(fd, code, buffer):
            buffer[0] = state["active"] if code == m.VT_GETSTATE else state["mode"]
        with patch.object(fcntl, "ioctl", side_effect=ioctl):
            self.assertTrue(console.active_text())
            state["mode"] = 1
            self.assertFalse(console.active_text())
            state.update(mode=0, active=3)
            self.assertFalse(console.active_text())


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_timeout_kills_helper_descendants(self):
        child_pid = self.root / "child.pid"
        script = self.root / "hang.py"
        script.write_text("import os,time\npid=os.fork()\n"
                          f"if pid: open({str(child_pid)!r},'w').write(str(pid))\n"
                          "time.sleep(30)\n")
        with patch.object(m, "CALL_TIMEOUT", 0.2):
            with self.assertRaisesRegex(m.MonitorError, "timed out"):
                m.run_tool([sys.executable, str(script)])
        pid = int(child_pid.read_text())
        # A killed descendant may briefly remain a zombie until its reaper runs.
        status = Path(f"/proc/{pid}/stat")
        self.assertTrue(not status.exists() or status.read_text().split()[2] == "Z")

    def harness(self):
        events = self.root / "events"
        state = self.root / "active"
        state.write_text("yes")
        script = self.root / "harness.py"
        script.write_text(f'''
import importlib.machinery,importlib.util,sys,os,termios
sys.dont_write_bytecode=True
from pathlib import Path
loader=importlib.machinery.SourceFileLoader("monitor",{str(SOURCE)!r})
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;loader.exec_module(m)
m.__file__=__file__
class FakeConsole:
    def __init__(self,fd): self.fd=fd
    def require_active(self,pgrp=None):
        if not self.active_text(): raise m.MonitorError("inactive VT")
    def active_text(self): return Path({str(state)!r}).read_text()=="yes"
    def blank(self):
        with open({str(events)!r},"a") as f: f.write("blank\\n")
    def wake(self):
        with open({str(events)!r},"a") as f: f.write("wake\\n")
m.Console=FakeConsole
if sys.argv[1]=="__guard": sys.exit(m.main())
os.login_tty(int(sys.argv[1]))
console=FakeConsole(os.dup(0))
try: m.blank_console(console,int(sys.argv[2]))
except KeyboardInterrupt: sys.exit(130)
''')
        return script, events, state

    def wait_text(self, path, text, proc=None):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            if path.exists() and text in path.read_text():
                return
            if proc and proc.poll() is not None:
                self.fail(f"process exited {proc.returncode} before {text}: {path.read_text() if path.exists() else ''}")
            time.sleep(0.02)
        self.fail(f"missing {text}")

    def owner(self, seconds=2):
        script, events, state = self.harness()
        master, slave = pty.openpty()
        original = termios.tcgetattr(slave)
        proc = subprocess.Popen([sys.executable, str(script), str(slave), str(seconds)],
                                pass_fds=(slave,), start_new_session=True)
        self.addCleanup(lambda: proc.kill() if proc.poll() is None else None)
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        self.wait_text(events, "blank", proc)
        return proc, master, slave, original, events, state

    def test_guard_wakes_on_timeout_and_restores_terminal(self):
        proc, master, slave, original, events, state = self.owner(1)
        self.assertEqual(proc.wait(timeout=4), 0)
        self.assertEqual(events.read_text(), "blank\nwake\n")
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_wake_key_is_consumed_and_terminal_restored(self):
        proc, master, slave, original, events, state = self.owner(10)
        os.write(master, b"x")
        self.assertEqual(proc.wait(timeout=4), 0)
        self.assertEqual(events.read_text(), "blank\nwake\n")
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_guard_survives_owner_sigkill_and_hangup(self):
        proc, master, slave, original, events, state = self.owner(10)
        proc.kill()
        proc.wait(timeout=3)
        self.wait_text(events, "wake")

    def test_stopped_owner_cannot_stop_timeout_recovery(self):
        proc, master, slave, original, events, state = self.owner(1)
        os.kill(proc.pid, signal.SIGSTOP)
        try:
            self.wait_text(events, "wake")
        finally:
            os.kill(proc.pid, signal.SIGCONT)
        self.assertEqual(proc.wait(timeout=4), 0)
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_switching_vt_does_not_wake_the_other_session(self):
        proc, master, slave, original, events, state = self.owner(10)
        state.write_text("no")
        self.assertEqual(proc.wait(timeout=4), 0)
        self.assertEqual(events.read_text(), "blank\n")

    def test_ctrl_c_recovers_and_restores_terminal(self):
        proc, master, slave, original, events, state = self.owner(10)
        os.write(master, b"\x03")
        self.assertEqual(proc.wait(timeout=4), 130)
        self.assertEqual(events.read_text(), "blank\nwake\n")
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_curses_pty_quit_and_resize_without_console(self):
        harness = self.root / "tui.py"
        harness.write_text(f'''
import importlib.machinery,importlib.util,sys
sys.dont_write_bytecode=True
loader=importlib.machinery.SourceFileLoader("monitor",{str(SOURCE)!r})
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;loader.exec_module(m)
class Hardware:
    def discover(self,*args): return [m.Monitor("card1-DP-1","DP-1","Fixture","connected","enabled")]
m.Hardware=Hardware
def no_console(): raise m.MonitorError("fixture PTY")
m.Console.open=no_console
sys.exit(m.main([]))
''')
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        original = termios.tcgetattr(slave)
        termios.tcsetwinsize(slave, (24, 80))
        env = dict(os.environ, TERM="xterm")
        proc = subprocess.Popen([sys.executable, str(harness)], stdin=slave, stdout=slave, stderr=slave, env=env)
        self.addCleanup(lambda: proc.kill() if proc.poll() is None else None)
        ready, _, _ = select.select([master], [], [], 3)
        self.assertTrue(ready)
        output = os.read(master, 8192)
        termios.tcsetwinsize(slave, (5, 30))
        os.kill(proc.pid, signal.SIGWINCH)
        os.write(master, b"bq")  # Console action is rejected, UI remains usable.
        self.assertEqual(proc.wait(timeout=4), 0, output)
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_cli_bad_arguments_and_piped_tui_fail_cleanly(self):
        for args in (["blank", "--seconds", "0"], ["idle", "61"], ["layout"], []):
            result = subprocess.run([sys.executable, str(SOURCE), *args], stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=3)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(b"Traceback", result.stderr)

    def test_installed_command_metadata_without_desktop(self):
        prefix = self.root / "installed"
        subprocess.run(["make", "install", f"PREFIX={prefix}"], cwd=SOURCE.parent, check=True,
                       capture_output=True)
        command = prefix / "bin/tam-monitor"
        env = {"PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run([str(command), "list", "--json", "--no-probe"],
                                env=env, capture_output=True, timeout=3, check=True)
        self.assertIsInstance(json.loads(result.stdout), list)
        self.assertTrue((prefix / "share/doc/tam-monitor/README.md").exists())


if __name__ == "__main__":
    unittest.main()
