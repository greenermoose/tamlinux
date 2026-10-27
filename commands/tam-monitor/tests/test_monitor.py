"""No real console ioctls or monitor writes: sysfs, devices and tools are fixtures."""

import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import termios
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_BIN = ROOT / "build/tam-monitor-fixture"
PRODUCT_BIN = ROOT / "build/tam-monitor"


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.drm = self.root / "drm"
        self.backlight = self.root / "backlight"
        self.bin_dir = self.root / "bin"
        self.tool_log = self.root / "tools.log"
        self.ddc_state = self.root / "ddc_value"
        self.ddc_mode = self.root / "ddc_mode"
        self.drm.mkdir()
        self.backlight.mkdir()
        self.bin_dir.mkdir()
        self.ddc_state.write_text("50\n")
        self.ddc_mode.write_text("ok\n")
        self._install_fake_tools()

    def _install_fake_tools(self):
        ddc = self.bin_dir / "tam-brightness-display-ddc"
        ddc.write_text(
            "#!/bin/sh\n"
            f'mode=$(cat "{self.ddc_mode}")\n'
            'if [ "$mode" = "denied" ]; then\n'
            '  echo "permission denied" >&2\n'
            '  exit 1\n'
            'fi\n'
            'if [ $# -eq 2 ] && [ "$mode" != "stale" ]; then\n'
            '  val="${2%\\%}"\n'
            f'  printf "%s\\n" "$val" > "{self.ddc_state}"\n'
            'fi\n'
            f'cat "{self.ddc_state}"\n'
        )
        ddc.chmod(0o755)

        hw = self.bin_dir / "tam-hw-display"
        hw.write_text("#!/bin/sh\necho intel_backlight\n")
        hw.chmod(0o755)

        bctl = self.bin_dir / "brightnessctl"
        bctl.write_text(
            "#!/bin/sh\n"
            'val="${4%\\%}"\n'
            f'printf "%s\\n" "$val" > "{self.backlight}/intel_backlight/brightness"\n'
        )
        bctl.chmod(0o755)

    def env(self, **extra):
        e = {
            "PATH": f"{self.bin_dir}:/usr/bin:/bin",
            "TAM_MONITOR_FIXTURE_DRM": str(self.drm),
            "TAM_MONITOR_FIXTURE_BACKLIGHT": str(self.backlight),
            "TAM_MONITOR_FIXTURE_TOOL_LOG": str(self.tool_log),
        }
        e.update(extra)
        return e

    def calls(self):
        if not self.tool_log.exists():
            return []
        return [line.split("\t") for line in self.tool_log.read_text().splitlines() if line]

    def clear_calls(self):
        if self.tool_log.exists():
            self.tool_log.unlink()

    def run_mon(self, *args, **env_extra):
        return subprocess.run(
            [str(FIXTURE_BIN), *args],
            env=self.env(**env_extra),
            text=True,
            capture_output=True,
            timeout=5,
        )

    def discover(self, probe=True):
        args = ["list", "--json"]
        if not probe:
            args.append("--no-probe")
        p = self.run_mon(*args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def connector(self, name="card1-DP-1", status="connected"):
        path = self.drm / name
        path.mkdir(exist_ok=True)
        (path / "status").write_text(status)
        (path / "enabled").write_text("enabled")
        return path

    def test_without_graphical_environment_and_no_probe(self):
        self.connector()
        item, = self.discover(probe=False)
        self.assertEqual(item["connection"], "connected")
        self.assertIsNone(item["brightness"])
        self.assertEqual(self.calls(), [])
        p = self.run_mon("brightness", "DP-1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(int(p.stdout.strip()), 50)
        self.assertFalse(any("hypr" in str(c) or "qs" in c for c in self.calls()))

    def test_ddc_write_is_verified_and_hotplug_remapped(self):
        path = self.connector()
        p = self.run_mon("brightness", "DP-1", "75")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(int(p.stdout.strip()), 75)
        self.assertEqual(
            self.calls()[-2:],
            [["tam-brightness-display-ddc", "DP-1", "75%"],
             ["tam-brightness-display-ddc", "DP-1"]],
        )
        (path / "status").write_text("disconnected")
        self.clear_calls()
        p2 = self.run_mon("brightness", "card1-DP-1", "50")
        self.assertNotEqual(p2.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_brightness_rejects_invalid_values_before_hardware(self):
        self.connector()
        for value in ("0", "-1", "101", "4294967297", "-4294967295",
                      "9223372036854775807", "9999999999999999999999999",
                      "", "1x", " 1", "+1"):
            with self.subTest(value=value):
                self.clear_calls()
                result = self.run_mon("brightness", "DP-1", value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.calls(), [])
        for value in ("1", "100"):
            self.assertEqual(self.run_mon("brightness", "DP-1", value).returncode, 0)

    def test_helper_timeout_survives_early_pipe_close(self):
        self.connector()
        helper = self.bin_dir / "tam-brightness-display-ddc"
        helper.write_text("#!/bin/sh\nexec 1>&- 2>&-\nsleep 1.2\n")
        helper.chmod(0o755)
        start = time.monotonic()
        result = self.run_mon("brightness", "DP-1", TAM_MONITOR_FIXTURE_TOOL_TIMEOUT_MS="100")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out", result.stderr)
        self.assertLess(time.monotonic() - start, 0.9)

    def test_stale_hardware_write_is_failure(self):
        self.connector()
        self.ddc_mode.write_text("stale\n")
        p = self.run_mon("brightness", "DP-1", "75")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("verification failed", p.stderr)

    def test_permission_failure_is_unknown_not_off(self):
        self.connector()
        self.ddc_mode.write_text("denied\n")
        item, = self.discover(probe=True)
        self.assertIsNone(item["brightness"])
        self.assertIn("permission denied", item["brightness_detail"])

    def test_ambiguous_card_connector_disables_ddc(self):
        self.connector()
        self.connector("card2-DP-1")
        items = self.discover(probe=True)
        self.assertTrue(all(not x["brightness_backend"] for x in items))
        p = self.run_mon("brightness", "card1-DP-1", "50")
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_internal_backlight_and_ambiguous_internal_mapping(self):
        self.connector("card1-eDP-1")
        device = self.backlight / "intel_backlight"
        device.mkdir()
        (device / "brightness").write_text("40")
        (device / "max_brightness").write_text("100")
        p = self.run_mon("brightness", "eDP-1", "65")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(int(p.stdout.strip()), 65)
        self.assertIn(["brightnessctl", "-d", "intel_backlight", "set", "65%"], self.calls())
        self.connector("card2-eDP-2")
        self.clear_calls()
        items = self.discover(probe=True)
        self.assertTrue(all(not x["brightness_backend"] for x in items))
        self.assertEqual(self.calls(), [])

    def test_out_of_range_brightness_never_writes(self):
        self.connector()
        for value in (0, -1, 101):
            p = self.run_mon("brightness", "DP-1", str(value))
            self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_removed_and_malformed_connector_metadata(self):
        self.connector(status="unknown\x1b[31m\nvalue")
        self.connector("card1-evil;command")
        item, = self.discover(probe=True)
        self.assertEqual(item["identity"], "EDID unavailable")
        self.assertEqual(self.calls(), [])
        p = self.run_mon("brightness", "bad\x1b[31m\nvalue")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("\x1b", p.stderr)

    def test_valid_edid_and_control_characters(self):
        path = self.connector()
        edid = bytearray(128)
        edid[:8] = b"\0\xff\xff\xff\xff\xff\xff\0"
        edid[8:10] = (0x10AC).to_bytes(2, "big")  # DEL
        edid[54:59] = b"\0\0\0\xfc\0"
        edid[59:72] = b"Fixture\x1b LCD\n "
        edid[127] = -sum(edid) % 256
        (path / "edid").write_bytes(edid)
        self.assertIn("Fixture? LCD", self.discover(probe=False)[0]["identity"])
        edid[127] ^= 1
        (path / "edid").write_bytes(edid)
        self.assertEqual(self.discover(probe=False)[0]["identity"], "EDID unavailable")

    def test_no_probe_skips_hardware_queries(self):
        self.connector()
        self.discover(probe=False)
        self.assertEqual(self.calls(), [])


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vt_state = self.root / "vt_state"
        self.vt_state.write_text("yes\n")
        self.consoleblank = self.root / "consoleblank"
        self.consoleblank.write_text("300\n")

    def test_rejects_pseudoterminal_and_foreign_owned_vt(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        p = subprocess.run(
            [str(PRODUCT_BIN), "idle", "5"],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3
        )
        self.assertNotEqual(p.returncode, 0)
        env = dict(os.environ, TAM_MONITOR_FIXTURE_VT="1", TAM_MONITOR_FIXTURE_VT_FOREIGN="1")
        p2 = subprocess.run(
            [str(FIXTURE_BIN), "idle", "5"],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, timeout=3
        )
        self.assertNotEqual(p2.returncode, 0)
        self.assertIn("belong to the calling user", p2.stderr)

    def test_inactive_graphical_or_background_cannot_change_idle(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        for state_text, bg in (("no\n", ""), ("yes\n", "1")):
            self.vt_state.write_text(state_text)
            env = dict(
                os.environ,
                TAM_MONITOR_FIXTURE_VT="1",
                TAM_MONITOR_FIXTURE_VT_STATE=str(self.vt_state),
                TAM_MONITOR_FIXTURE_VT_BG=bg,
                TAM_MONITOR_FIXTURE_CONSOLEBLANK=str(self.consoleblank),
            )
            p = subprocess.run(
                [str(FIXTURE_BIN), "idle", "5"],
                stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True, timeout=3
            )
            self.assertNotEqual(p.returncode, 0)
            r, _, _ = select.select([master], [], [], 0.05)
            self.assertEqual(r, [])

    def test_idle_uses_only_console_timer_sequence(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        env = dict(
            os.environ,
            TAM_MONITOR_FIXTURE_VT="1",
            TAM_MONITOR_FIXTURE_VT_STATE=str(self.vt_state),
            TAM_MONITOR_FIXTURE_CONSOLEBLANK=str(self.consoleblank),
        )
        p = subprocess.run(
            [str(FIXTURE_BIN), "idle", "5"],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, text=True, timeout=3, start_new_session=True,
            preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0),
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        r, _, _ = select.select([master], [], [], 0.5)
        self.assertTrue(r)
        self.assertIn(b"\x1b[9;5]", os.read(master, 64))
        p_bad = subprocess.run(
            [str(FIXTURE_BIN), "idle", "61"],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, text=True, timeout=3,
        )
        self.assertNotEqual(p_bad.returncode, 0)

    def test_idle_readback_rejects_a_failed_timer_change(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        self.consoleblank.write_text("0\n")
        env = dict(
            os.environ,
            TAM_MONITOR_FIXTURE_VT="1",
            TAM_MONITOR_FIXTURE_VT_STATE=str(self.vt_state),
            TAM_MONITOR_FIXTURE_CONSOLEBLANK=str(self.consoleblank),
        )
        p = subprocess.run(
            [str(FIXTURE_BIN), "idle", "5"],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, text=True, timeout=3, start_new_session=True,
            preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0),
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("verification failed", p.stderr)


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_timeout_kills_helper_descendants(self):
        child_pid = self.root / "child.pid"
        drm = self.root / "drm"
        bin_dir = self.root / "bin"
        drm.mkdir()
        bin_dir.mkdir()
        conn = drm / "card1-DP-1"
        conn.mkdir()
        (conn / "status").write_text("connected")
        (conn / "enabled").write_text("enabled")
        ddc = bin_dir / "tam-brightness-display-ddc"
        ddc.write_text(
            f"#!{sys.executable}\n"
            "import os, time\n"
            "pid = os.fork()\n"
            f"if pid: open({str(child_pid)!r}, 'w').write(str(pid))\n"
            "time.sleep(30)\n"
        )
        ddc.chmod(0o755)
        env = dict(
            os.environ,
            PATH=f"{bin_dir}:/usr/bin:/bin",
            TAM_MONITOR_FIXTURE_DRM=str(drm),
            TAM_MONITOR_FIXTURE_TOOL_TIMEOUT_MS="200",
        )
        p = subprocess.run(
            [str(FIXTURE_BIN), "brightness", "DP-1"],
            env=env, text=True, capture_output=True, timeout=5,
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("timed out", p.stderr)
        pid = int(child_pid.read_text())
        status = Path(f"/proc/{pid}/stat")
        self.assertTrue(not status.exists() or status.read_text().split()[2] == "Z")

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
        events = self.root / "events"
        state = self.root / "active"
        state.write_text("yes\n")
        master, slave = pty.openpty()
        original = termios.tcgetattr(slave)
        env = dict(
            os.environ,
            TAM_MONITOR_FIXTURE_VT="1",
            TAM_MONITOR_FIXTURE_VT_STATE=str(state),
            TAM_MONITOR_FIXTURE_VT_EVENTS=str(events),
        )
        proc = subprocess.Popen(
            [str(FIXTURE_BIN), "blank", "--seconds", str(seconds)],
            stdin=slave, stdout=slave, stderr=slave,
            env=env, close_fds=True, start_new_session=True,
            preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0),
        )
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
        state.write_text("no\n")
        self.assertEqual(proc.wait(timeout=4), 0)
        self.assertEqual(events.read_text(), "blank\n")

    def test_ctrl_c_recovers_and_restores_terminal(self):
        proc, master, slave, original, events, state = self.owner(10)
        os.write(master, b"\x03")
        self.assertEqual(proc.wait(timeout=4), 130)
        self.assertEqual(events.read_text(), "blank\nwake\n")
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_tui_pty_quit_and_resize_without_console(self):
        drm = self.root / "drm"
        drm.mkdir()
        conn = drm / "card1-DP-1"
        conn.mkdir()
        (conn / "status").write_text("connected")
        (conn / "enabled").write_text("enabled")
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        original = termios.tcgetattr(slave)
        termios.tcsetwinsize(slave, (24, 80))
        env = dict(
            os.environ,
            TERM="xterm",
            TAM_MONITOR_FIXTURE_DRM=str(drm),
            TAM_MONITOR_FIXTURE_VT="deny",
        )
        proc = subprocess.Popen(
            [str(FIXTURE_BIN)],
            stdin=slave, stdout=slave, stderr=slave, env=env,
        )
        self.addCleanup(lambda: proc.kill() if proc.poll() is None else None)
        ready, _, _ = select.select([master], [], [], 3)
        self.assertTrue(ready)
        output = os.read(master, 8192)
        termios.tcsetwinsize(slave, (5, 30))
        os.kill(proc.pid, signal.SIGWINCH)
        os.write(master, b"boq")  # Console actions are rejected in PTY, UI remains usable.
        self.assertEqual(proc.wait(timeout=4), 0, output)
        self.assertEqual(termios.tcgetattr(slave), original)

    def test_cli_bad_arguments_and_piped_tui_fail_cleanly(self):
        for args in (["blank", "--seconds", "0"], ["idle", "61"], ["layout"], []):
            result = subprocess.run(
                [str(PRODUCT_BIN), *args],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=3,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(b"Traceback", result.stderr)

    def test_installed_command_metadata_without_desktop(self):
        prefix = self.root / "installed"
        subprocess.run(
            ["make", "install", f"PREFIX={prefix}"],
            cwd=ROOT, check=True, capture_output=True,
        )
        command = prefix / "bin/tam-monitor"
        env = {"PATH": os.environ["PATH"]}
        result = subprocess.run(
            [str(command), "list", "--json", "--no-probe"],
            env=env, capture_output=True, timeout=3, check=True,
        )
        self.assertIsInstance(json.loads(result.stdout), list)
        self.assertTrue((prefix / "share/doc/tam-monitor/README.md").exists())


if __name__ == "__main__":
    unittest.main()
