#!/usr/bin/env python3
"""End-to-end headless tam-pane 0.2.8 tests for Milestone 6 controls."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TAM_PANE_LUA = ROOT / "src/desktop/session/tam-pane.lua"
COMMANDS_DIR = ROOT / "src/commands"


def find_tam_pane_bin() -> str | None:
    candidates = [
        os.environ.get("TAM_PANE_BIN", ""),
        str(ROOT.parent / "tam-pane/build/tam-pane"),
        shutil.which("tam-pane") or "",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def make_cmd_shim_dir(tmp: Path, tam_pane_bin: str) -> Path:
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    os.symlink(tam_pane_bin, bin_dir / "tam-pane")
    for cmd_dir in COMMANDS_DIR.iterdir():
        exe = cmd_dir / cmd_dir.name
        if exe.is_file() and os.access(exe, os.X_OK):
            os.symlink(exe, bin_dir / cmd_dir.name)
    return bin_dir


class TamPaneControlsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tam_pane = find_tam_pane_bin()
        if not self.tam_pane:
            self.skipTest("tam-pane binary not found")
        self.tmp = Path(tempfile.mkdtemp(prefix="tam-pane-controls-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

        self.runtime_dir = self.tmp / "runtime"
        self.runtime_dir.mkdir(mode=0o700)
        self.config_dir = self.tmp / "config"
        self.config_dir.mkdir(mode=0o700)
        self.state_dir = self.tmp / "state"
        self.state_dir.mkdir(mode=0o700)
        self.pictures_dir = self.tmp / "Pictures"
        self.pictures_dir.mkdir(mode=0o700)
        self.bin_dir = make_cmd_shim_dir(self.tmp, self.tam_pane)

        # Personal override file loaded by packaged tam-pane.lua via tp.include
        personal_dir = self.config_dir / "tam-pane"
        personal_dir.mkdir(parents=True)
        (personal_dir / "init.lua").write_text(
            "tp.config{ kb_layout = 'us,dk', kb_options = 'compose:ralt' }\n"
            "tp.monitor{ output = 'HEADLESS-1', position = { 0, 0 }, scale = 1.25 }\n"
            "tp.monitor{ output = 'HEADLESS-2', position = { 1280, 0 }, scale = 1.0 }\n"
            "tp.bind('Meta+Shift+F12', tp.dsp.spawn('true'), { desc = 'Personal override bind' })\n",
            encoding="utf-8",
        )

        # Pre-seed one macro and sync it into config/tamlinux/tam-pane/macros.lua
        macros_dir = self.config_dir / "tamlinux"
        macros_dir.mkdir(parents=True)
        (macros_dir / "macros.json").write_text(
            json.dumps([{"key": "M", "text": "hello-tam-pane", "description": "Greeting"}]),
            encoding="utf-8",
        )

        self.env = os.environ.copy()
        self.env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        self.env.pop("WAYLAND_DISPLAY", None)
        self.env.pop("TAM_PANE_SOCKET", None)
        self.env["HOME"] = str(self.tmp)
        self.env["XDG_RUNTIME_DIR"] = str(self.runtime_dir)
        self.env["XDG_CONFIG_HOME"] = str(self.config_dir)
        self.env["XDG_STATE_HOME"] = str(self.state_dir)
        self.env["TAMLINUX_SCREENSHOT_DIR"] = str(self.pictures_dir)
        self.env["TAMLINUX_MACRO_SKIP_RELOAD"] = "1"
        self.env["PATH"] = f"{self.bin_dir}:{self.env.get('PATH', '')}"
        self.env["WLR_BACKENDS"] = "headless"
        self.env["WLR_HEADLESS_OUTPUTS"] = "2"
        self.env["WLR_RENDERER"] = "pixman"

        # Generate tam-pane macros.lua before starting compositor
        subprocess.run(
            [str(self.bin_dir / "tam-macro"), "sync"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        pane_macros = self.config_dir / "tamlinux/tam-pane/macros.lua"
        self.assertTrue(pane_macros.is_file())
        self.assertIn("meta+alt+m", pane_macros.read_text(encoding="utf-8").lower())

        # Start headless two-output tam-pane with the packaged tam-pane.lua
        self.proc = subprocess.Popen(
            [self.tam_pane, "-c", str(TAM_PANE_LUA)],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(self._stop_compositor)

        sock = self._wait_for_socket()
        self.env["TAM_PANE_SOCKET"] = str(sock)
        self.env["WAYLAND_DISPLAY"] = sock.stem
        self.env.pop("TAMLINUX_MACRO_SKIP_RELOAD", None)
        self._msg("dispatch", "monitor", "focus", "HEADLESS-1")

    def _stop_compositor(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stderr:
            self.proc.stderr.close()

    def _wait_for_socket(self) -> Path:
        sock_dir = self.runtime_dir / "tam-pane"
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                out, err = self.proc.communicate()
                self.fail(f"tam-pane exited early ({self.proc.returncode}): {err}\n{out}")
            if sock_dir.is_dir():
                socks = sorted(sock_dir.glob("wayland-*.sock"))
                if socks:
                    return socks[0]
            time.sleep(0.05)
        self.fail("timed out waiting for tam-pane IPC socket")

    def _msg(self, *args: str) -> str:
        res = subprocess.run(
            [self.tam_pane, "msg", *args],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return res.stdout

    def test_monitors_personal_overrides_and_reload(self) -> None:
        monitors = self._msg("monitors")
        self.assertIn("name=HEADLESS-1", monitors)
        self.assertIn("name=HEADLESS-2", monitors)
        self.assertIn("scale=1.25", monitors)

        binds = self._msg("binds")
        self.assertIn("Personal override bind", binds)
        self.assertIn("Macro: Greeting", binds)
        self.assertIn("code:10", binds)

        # Live reload preserves personal overrides and macros
        self._msg("reload")
        binds_after = self._msg("binds")
        self.assertIn("Personal override bind", binds_after)
        self.assertIn("Macro: Greeting", binds_after)

        # Chord composer is active
        chord = self._msg("chord")
        self.assertIn("mode=idle", chord)

    def test_monitor_commands_dpms_and_scaling(self) -> None:
        focused = subprocess.run(
            [str(self.bin_dir / "tam-hyprland-monitor-focused")],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(focused, "HEADLESS-1")

        apple = subprocess.run(
            [str(self.bin_dir / "tam-hyprland-monitor-focused-apple"), focused],
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(apple.returncode, 0)

        # Query and change monitor scale via tam-hyprland-monitor-scaling
        scale_before = subprocess.run(
            [str(self.bin_dir / "tam-hyprland-monitor-scaling")],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(scale_before, "1.25")

        subprocess.run(
            [str(self.bin_dir / "tam-hyprland-monitor-scaling"), "2"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        scale_after = subprocess.run(
            [str(self.bin_dir / "tam-hyprland-monitor-scaling")],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(scale_after, "2")

        # DPMS off / on via tam-brightness-display
        subprocess.run(
            [str(self.bin_dir / "tam-brightness-display"), "off"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("dpms=0", self._msg("monitors"))
        subprocess.run(
            [str(self.bin_dir / "tam-brightness-display"), "on"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("dpms=1", self._msg("monitors"))

    def test_nightlight_capture_and_terminal_cwd_fallback(self) -> None:
        nl = subprocess.run(
            [str(self.bin_dir / "tam-toggle-nightlight"), "--status"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(nl.stdout)
        self.assertFalse(data["enabled"])
        self.assertEqual(data["temperature"], 6500)

        # Region fullscreen + match-monitor
        geo = subprocess.run(
            [str(self.bin_dir / "tam-capture-region"), "fullscreen"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertRegex(geo, r"^-?\d+,-?\d+ \d+x\d+$")

        matched = subprocess.run(
            [str(self.bin_dir / "tam-capture-region"), "fullscreen", "--match-monitor"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(matched, "monitor:HEADLESS-1")

        # Fullscreen screenshot save via authorized dispatch capture + grim
        if shutil.which("grim"):
            shot = subprocess.run(
                [str(self.bin_dir / "tam-capture-screenshot"), "fullscreen", "save"],
                env=self.env,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            shot_path = Path(shot)
            self.assertTrue(shot_path.is_file(), f"screenshot not created: {shot}")
            self.assertTrue(shot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

        # Terminal CWD falls back cleanly to $HOME when no window is focused
        cwd = subprocess.run(
            [str(self.bin_dir / "tam-cmd-terminal-cwd")],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(cwd, str(self.tmp))

        # Macro sync reloads live tam-pane cleanly
        subprocess.run(
            [str(self.bin_dir / "tam-macro"), "sync"],
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
