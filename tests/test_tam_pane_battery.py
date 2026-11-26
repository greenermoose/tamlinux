#!/usr/bin/env python3
"""Repeatable automated headless tam-pane battery for 0.7.0 Milestone 8.

Covers:
  1. Session selection (tam-desktop pane / hyprland / default) & Hyprland fallback.
  2. Multi-output tags (single-tag view, multi-tag toggle, per-output focus, DPMS).
  3. Shell actions (Quickshell + TamPaneAdapter + qs ipc on headless tam-pane).
  4. App launches (tam-last + tam-clam, tam-edit PTY save).
  5. Clipboard (paste-text.sh on tam-pane AND Hyprland fallback).
  6. Capture (tam-capture-region + tam-capture-screenshot via dispatch capture + grim).
"""
from __future__ import annotations

import os
from pathlib import Path
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "src/desktop"
HOST = DESKTOP / "shell/host"
COMMANDS = ROOT / "src/commands"
TAM_PANE_LUA = DESKTOP / "session/tam-pane.lua"
PASTE_HELPER = DESKTOP / "shell/services/clipboard/paste-text.sh"

sys.path.insert(0, str(ROOT / "tests"))
from headless_compositor import find_tam_pane
from quickshell_bin import quickshell_bin


def _find_bin(name: str) -> str | None:
    for candidate in (
        str(Path.home() / ".local/bin" / name),
        f"/usr/bin/tamlinux/{name}",
        shutil.which(name) or "",
    ):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


class TamPaneAutomatedBatteryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tam_pane = find_tam_pane(ROOT)
        if not self.tam_pane:
            self.skipTest("tam-pane binary not found")

        self.tmp = Path(tempfile.mkdtemp(prefix="tam-pane-m8-battery-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

        self.runtime_dir = self.tmp / "r"
        self.runtime_dir.mkdir(mode=0o700)
        self.config_dir = self.tmp / "config"
        self.config_dir.mkdir(mode=0o700)
        self.state_dir = self.tmp / "state"
        self.state_dir.mkdir(mode=0o700)
        self.cache_dir = self.tmp / "cache"
        self.cache_dir.mkdir(mode=0o700)
        self.pictures_dir = self.tmp / "Pictures"
        self.pictures_dir.mkdir(mode=0o700)

        self.bin_dir = self.tmp / "bin"
        self.bin_dir.mkdir()
        os.symlink(self.tam_pane, self.bin_dir / "tam-pane")
        for cmd_dir in COMMANDS.iterdir():
            exe = cmd_dir / cmd_dir.name
            if exe.is_file() and os.access(exe, os.X_OK):
                os.symlink(exe, self.bin_dir / cmd_dir.name)

        self.env = os.environ.copy()
        for drop in (
            "HYPRLAND_INSTANCE_SIGNATURE",
            "WAYLAND_DISPLAY",
            "TAM_PANE_SOCKET",
            "TAMLINUX_COMPOSITOR_BACKEND",
            "TAMLINUX_PLUGIN_ENTRIES",
        ):
            self.env.pop(drop, None)
        self.env.update({
            "HOME": str(self.tmp),
            "XDG_RUNTIME_DIR": str(self.runtime_dir),
            "XDG_CONFIG_HOME": str(self.config_dir),
            "XDG_STATE_HOME": str(self.state_dir),
            "XDG_CACHE_HOME": str(self.cache_dir),
            "XDG_CURRENT_DESKTOP": "tam-pane",
            "XDG_SESSION_TYPE": "wayland",
            "TAMLINUX_SCREENSHOT_DIR": str(self.pictures_dir),
            "TAMLINUX_COMPOSITOR_COMMANDS": str(HOST),
            "TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1",
            "PATH": f"{self.bin_dir}:{self.env.get('PATH', '/usr/bin')}",
            "WLR_BACKENDS": "headless",
            "WLR_HEADLESS_OUTPUTS": "2",
            "WLR_RENDERER": "pixman",
        })

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
        return subprocess.check_output(
            [self.tam_pane, "msg", *args], env=self.env, text=True, timeout=5
        )

    def test_session_selection_and_hyprland_fallback(self) -> None:
        sys.path.insert(0, str(DESKTOP / "source-install"))
        import session_settings  # noqa: E402

        # Hyprland session requirements are disjoint from tam-pane files so Hyprland
        # fallback still starts even when tam-pane.lua or tam-pane-portals.conf is absent.
        hypr_req = set(session_settings.required_for("hyprland"))
        pane_req = set(session_settings.required_for("pane"))
        self.assertTrue(hypr_req, "hyprland required session settings empty")
        self.assertTrue(pane_req, "pane required session settings empty")
        self.assertFalse(any("tam-pane" in str(item) for item in hypr_req), hypr_req)
        self.assertTrue(any("tam-pane" in str(item) for item in pane_req), pane_req)

        # Verify tam-desktop console launcher exposes pane + hyprland routes
        console_py = (DESKTOP / "session/console.py").read_text(encoding="utf-8")
        self.assertIn("tam-pane", console_py)
        self.assertIn("hyprland", console_py)

    def test_tags_capture_and_clipboard_with_hyprland_fallback(self) -> None:
        # 1. Multi-output tags & DPMS
        self._msg("dispatch", "monitor", "focus", "HEADLESS-1")
        self._msg("dispatch", "tag", "view", "2", "HEADLESS-1")
        self._msg("dispatch", "tag", "toggle_view", "4", "HEADLESS-1")
        tags = self._msg("tags")
        self.assertIn("monitor=HEADLESS-1\tview=10", tags)

        self._msg("dispatch", "dpms", "off", "HEADLESS-2")
        self.assertIn("dpms=0", self._msg("monitors"))
        self._msg("dispatch", "dpms", "on", "HEADLESS-2")

        # 2. Capture (region + screenshot PNG via dispatch capture + grim)
        matched = subprocess.check_output(
            [str(self.bin_dir / "tam-capture-region"), "fullscreen", "--match-monitor"],
            env=self.env,
            text=True,
            timeout=5,
        ).strip()
        self.assertEqual(matched, "monitor:HEADLESS-1")

        if shutil.which("grim"):
            shot = subprocess.check_output(
                [str(self.bin_dir / "tam-capture-screenshot"), "fullscreen", "save"],
                env=self.env,
                text=True,
                timeout=10,
            ).strip()
            shot_path = Path(shot)
            self.assertTrue(shot_path.is_file())
            self.assertTrue(shot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

        # 3. Clipboard paste-text.sh on both tam-pane and Hyprland fallback
        hist = self.state_dir / "tamlinux/clipboard"
        hist.mkdir(parents=True, exist_ok=True)
        (hist / "history.json").write_text('[{"type":"text","text":"m8-clip\\n"}]', encoding="utf-8")
        stub_dir = self.tmp / "clip-stubs"
        stub_dir.mkdir()
        (stub_dir / "wl-copy").write_text('#!/bin/sh\ncat > "$XDG_STATE_HOME/copied"\n', encoding="utf-8")
        (stub_dir / "wl-copy").chmod(0o755)
        (stub_dir / "tam-pane").write_text(
            '#!/bin/sh\nif [ "$1" = "msg" ] && [ "$2" = "windows" ]; then\n'
            '  printf "window\\tid=11\\tapp_id=tam-last\\tfocused=1\\n"\n'
            'elif [ "$1" = "msg" ] && [ "$2" = "dispatch" ]; then\n'
            '  shift 2; echo "$*" > "$XDG_STATE_HOME/pane_dispatch"\n'
            'fi\n',
            encoding="utf-8",
        )
        (stub_dir / "tam-pane").chmod(0o755)
        (stub_dir / "hyprctl").write_text(
            '#!/bin/sh\nif [ "$1" = "-j" ]; then printf \'{"class":"tam-last","address":"0x77"}\'; else echo ok; fi\n',
            encoding="utf-8",
        )
        (stub_dir / "hyprctl").chmod(0o755)

        pane_env = dict(self.env, PATH=f"{stub_dir}:{self.env['PATH']}")
        target = subprocess.check_output([str(PASTE_HELPER), "--capture-target"], env=pane_env, text=True).strip()
        self.assertEqual(target, "pane:11")
        subprocess.run([str(PASTE_HELPER), "--target", target, "--history-index", "0"], env=pane_env, check=True)
        self.assertEqual((self.state_dir / "pane_dispatch").read_text().strip(), "send_key Ctrl+Shift+V")

        hypr_env = dict(pane_env, HYPRLAND_INSTANCE_SIGNATURE="fallback-sig")
        hypr_target = subprocess.check_output([str(PASTE_HELPER), "--capture-target"], env=hypr_env, text=True).strip()
        self.assertEqual(hypr_target, "0x77")

    def test_shell_actions_and_app_launches_on_headless_tam_pane(self) -> None:
        # 1. Shell IPC action on headless tam-pane
        qs = quickshell_bin()
        qs_cli = str(Path(qs).with_name("qs"))
        if not os.access(qs_cli, os.X_OK):
            qs_cli = shutil.which("qs") or ""

        shell_work = self.tmp / "shell-copy"
        shutil.copytree(DESKTOP / "shell", shell_work)
        (shell_work / "m8-ipc.qml").write_text(
            "import QtQuick\n"
            "import Quickshell\n"
            "import Quickshell.Io\n"
            'import "host"\n'
            "ShellRoot {\n"
            "  Compositor { id: comp }\n"
            "  IpcHandler {\n"
            '    target: "m8-battery"\n'
            "    function backend(): string { return comp.backendName }\n"
            "  }\n"
            "  Timer { interval: 4000; running: true; onTriggered: Qt.quit() }\n"
            "}\n",
            encoding="utf-8",
        )
        shell_env = dict(
            self.env,
            QT_QPA_PLATFORM="wayland",
            QT_QUICK_BACKEND="software",
            QSG_RENDER_LOOP="basic",
            QML_IMPORT_PATH=str(shell_work / "modules"),
        )
        qs_proc = subprocess.Popen(
            [qs, "--no-color", "-p", str(shell_work / "m8-ipc.qml")],
            env=shell_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        ipc_reply = ""
        try:
            if qs_cli:
                for _ in range(30):
                    res = subprocess.run(
                        [qs_cli, "ipc", "-p", str(shell_work / "m8-ipc.qml"), "call", "m8-battery", "backend"],
                        env=shell_env,
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        ipc_reply = res.stdout.strip().strip('"')
                        break
                    time.sleep(0.1)
        finally:
            qs_proc.terminate()
            try:
                out, err = qs_proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                qs_proc.kill()
                out, err = qs_proc.communicate(timeout=2)
        if qs_cli:
            self.assertEqual(ipc_reply, "tam-pane", out + err)

        # 2. App launches: tam-last + tam-clam and tam-edit
        tam_last = _find_bin("tam-last")
        tam_clam = _find_bin("tam-clam")
        if tam_last and tam_clam:
            marker = self.tmp / "m8-app.txt"
            res = subprocess.run(
                [tam_last, "-e", tam_clam, "-c", f"echo M8_APP_OK > {marker}"],
                env=self.env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "M8_APP_OK")

        tam_edit = _find_bin("tam-edit")
        if tam_edit:
            scratch = self.tmp / "m8-edit.txt"
            scratch.write_text("line1\n", encoding="utf-8")
            mfd, sfd = pty.openpty()
            try:
                ed = subprocess.Popen(
                    [tam_edit, str(scratch)],
                    stdin=sfd,
                    stdout=sfd,
                    stderr=sfd,
                    env=self.env,
                    close_fds=True,
                )
                os.close(sfd)
                sfd = -1
                time.sleep(0.3)
                os.write(mfd, b"Z")
                time.sleep(0.15)
                os.write(mfd, b"\x13")
                time.sleep(0.2)
                os.write(mfd, b"\x11")
                deadline = time.monotonic() + 5.0
                while ed.poll() is None and time.monotonic() < deadline:
                    if select.select([mfd], [], [], 0.05)[0]:
                        try:
                            os.read(mfd, 4096)
                        except OSError:
                            break
                if ed.poll() is None:
                    ed.terminate()
                    ed.wait(timeout=2)
                self.assertEqual(ed.returncode, 0)
            finally:
                if sfd >= 0:
                    os.close(sfd)
                os.close(mfd)
            self.assertIn("Z", scratch.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
