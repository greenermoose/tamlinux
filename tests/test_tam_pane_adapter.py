"""Tests for TamPaneAdapter.qml, tam_pane_model.js, and two-output tam-pane integration."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quickshell_bin import quickshell_bin

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "src/desktop"
HOST = DESKTOP / "shell/host"


class MockTamPaneServer:
    """Two-output mock tam-pane Unix socket server supporting events and forced reconnect."""

    def __init__(self, sock_path: Path):
        self.sock_path = sock_path
        self.phase = 0  # 0=initial, 1=after actions/events, 2=after reconnect
        self.dispatches: list[str] = []
        self.event_conns: list[socket.socket] = []
        self.all_conns: list[socket.socket] = []
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()
        self.srv: socket.socket | None = None
        self.thread: threading.Thread | None = None
        self.restarted = threading.Event()

    def start(self) -> None:
        self._bind_listen()
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _bind_listen(self) -> None:
        if self.sock_path.exists():
            self.sock_path.unlink()
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(str(self.sock_path))
        s.listen(16)
        s.settimeout(0.1)
        self.srv = s

    def force_reconnect_with_phase2(self) -> None:
        with self.lock:
            self.phase = 2
            old_srv = self.srv
            self.srv = None
            conns = list(self.all_conns)
            self.all_conns.clear()
            self.event_conns.clear()
        for c in conns:
            try:
                c.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                c.close()
            except OSError:
                pass
        if old_srv:
            try:
                old_srv.close()
            except OSError:
                pass
        time.sleep(0.05)
        with self.lock:
            self._bind_listen()
        self.restarted.set()

    def stop(self) -> None:
        self.stop_flag.set()
        with self.lock:
            srv = self.srv
            self.srv = None
            conns = list(self.all_conns)
            self.all_conns.clear()
            self.event_conns.clear()
        if srv:
            try:
                srv.close()
            except OSError:
                pass
        for c in conns:
            try:
                c.close()
            except OSError:
                pass
        if self.sock_path.exists():
            try:
                self.sock_path.unlink()
            except OSError:
                pass

    def _accept_loop(self) -> None:
        while not self.stop_flag.is_set():
            with self.lock:
                srv = self.srv
            if srv is None:
                time.sleep(0.02)
                continue
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                time.sleep(0.02)
                continue
            with self.lock:
                self.all_conns.append(conn)
            threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()

    def _emit_event(self, line: str) -> None:
        data = (line + "\n").encode("utf-8")
        with self.lock:
            targets = list(self.event_conns)
        for c in targets:
            try:
                c.sendall(data)
            except OSError:
                pass

    def _reply(self, line: str) -> str:
        with self.lock:
            phase = self.phase
        if line == "monitors":
            if phase == 0:
                return (
                    "OK\n"
                    "monitor\tname=DP-1\tx=0\ty=0\tw=1920\th=1080\tusable_x=0\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=5\tprev_tags=1\tfocused=1\tlayout=dwindle\tdpms=1\tdescription=Primary\n"
                    "monitor\tname=HDMI-A-1\tx=1920\ty=0\tw=1920\th=1080\tusable_x=1920\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=2\tprev_tags=1\tfocused=0\tlayout=dwindle\tdpms=1\tdescription=Secondary\n"
                    "END\n"
                )
            if phase == 1:
                return (
                    "OK\n"
                    "monitor\tname=DP-1\tx=0\ty=0\tw=1920\th=1080\tusable_x=0\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=13\tprev_tags=5\tfocused=0\tlayout=dwindle\tdpms=1\tdescription=Primary\n"
                    "monitor\tname=HDMI-A-1\tx=1920\ty=0\tw=1920\th=1080\tusable_x=1920\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=2\tprev_tags=1\tfocused=1\tlayout=dwindle\tdpms=0\tdescription=Secondary\n"
                    "END\n"
                )
            return (
                "OK\n"
                "monitor\tname=DP-1\tx=0\ty=0\tw=1920\th=1080\tusable_x=0\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=1\tprev_tags=5\tfocused=1\tlayout=dwindle\tdpms=1\tdescription=Primary\n"
                "monitor\tname=HDMI-A-1\tx=1920\ty=0\tw=1920\th=1080\tusable_x=1920\tusable_y=0\tusable_w=1920\tusable_h=1080\tscale=1.00\ttags=2\tprev_tags=1\tfocused=0\tlayout=dwindle\tdpms=1\tdescription=Secondary\n"
                "END\n"
            )
        if line == "tags":
            if phase == 0:
                return (
                    "OK\n"
                    "tag\tmonitor=DP-1\tview=5\tprev_view=1\toccupied=5\tfocused=1\n"
                    "tag\tmonitor=HDMI-A-1\tview=2\tprev_view=1\toccupied=0\tfocused=0\n"
                    "END\n"
                )
            if phase == 1:
                return (
                    "OK\n"
                    "tag\tmonitor=DP-1\tview=13\tprev_view=5\toccupied=5\tfocused=0\n"
                    "tag\tmonitor=HDMI-A-1\tview=2\tprev_view=1\toccupied=0\tfocused=1\n"
                    "END\n"
                )
            return (
                "OK\n"
                "tag\tmonitor=DP-1\tview=1\tprev_view=5\toccupied=1\tfocused=1\n"
                "tag\tmonitor=HDMI-A-1\tview=2\tprev_view=1\toccupied=0\tfocused=0\n"
                "END\n"
            )
        if line == "windows":
            return (
                "OK\n"
                "window\tmonitor=DP-1\ttags=5\tfocused=1\tfloating=0\tfullscreen=0\tscratchpad=0\txwayland=0\tx=0\ty=0\tw=960\th=1080\tapp_id=tam-last\ttitle=Shell\\tTab\n"
                "END\n"
            )
        if line == "binds":
            return (
                "OK\n"
                "bind\tmods=Meta\tkey=Return\tlocked=0\taction=terminal\n"
                "bind\tmods=Meta+Shift\tkey=q\tlocked=0\taction=close\n"
                "END\n"
            )
        if line == "keyboards":
            keymap = "English (US)" if phase == 0 else ("German" if phase == 1 else "French")
            idx = phase
            return (
                "OK\n"
                f"keyboard\tname=main-kbd\tlayout=English (US),German,French\tactive_keymap={keymap}\tactive_layout_index={idx}\tmain=1\n"
                "END\n"
            )
        if line == "cursor":
            return "OK\ncursor\tx=450\ty=220\tmonitor=DP-1\nEND\n"
        if line.startswith("dispatch "):
            with self.lock:
                self.dispatches.append(line)
                if line == "dispatch keyboard next main-kbd":
                    self.phase = 1
            if line == "dispatch keyboard next main-kbd":
                threading.Timer(0.05, lambda: self._emit_event("event\tmonitor.focus\tmonitor=HDMI-A-1")).start()
                threading.Timer(0.07, lambda: self._emit_event("event\toutput.power\tmonitor=HDMI-A-1\tdpms=0")).start()
                threading.Timer(0.09, lambda: self._emit_event("event\tkeyboard.layout\tname=main-kbd\tactive_keymap=German\tactive_layout_index=1")).start()
                threading.Timer(0.25, self.force_reconnect_with_phase2).start()
            return "OK\nEND\n"
        return "ERR unknown command\n"

    def _handle_conn(self, conn: socket.socket) -> None:
        buf = b""
        try:
            while not self.stop_flag.is_set():
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line.startswith("subscribe"):
                        with self.lock:
                            self.event_conns.append(conn)
                        conn.sendall(b"OK\n")
                        continue
                    conn.sendall(self._reply(line).encode("utf-8"))
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass


def _stage_fixture(directory: Path) -> Path:
    config = directory / "config"
    (config / "host").mkdir(parents=True)
    (config / "services/keybindings").mkdir(parents=True)
    shutil.copyfile(ROOT / "tests/fixtures/tam-pane-adapter/shell.qml", config / "shell.qml")
    for name in (
        "Compositor.qml",
        "TamPaneAdapter.qml",
        "HyprlandAdapter.qml",
        "ProtocolState.qml",
        "ProtocolShadow.qml",
        "protocol_model.js",
        "tam_pane_model.js",
    ):
        shutil.copyfile(HOST / name, config / "host" / name)
    shutil.copyfile(
        DESKTOP / "shell/services/keybindings/KeybindingsModel.js",
        config / "services/keybindings/KeybindingsModel.js",
    )
    return config


class TamPaneAdapterTests(unittest.TestCase):
    def test_source_boundaries(self):
        qml = (HOST / "TamPaneAdapter.qml").read_text(encoding="utf-8")
        self.assertIn("import Quickshell.Io", qml)
        self.assertIn("ProtocolState", qml)
        self.assertIn("perOutput: true", qml)
        self.assertIn("allowMultipleActive: true", qml)
        self.assertIn("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", qml)
        for banned in ("Quickshell.Hyprland", "hyprctl", "Process", "sh -c", "bash"):
            self.assertNotIn(banned, qml)

        facade = (HOST / "Compositor.qml").read_text(encoding="utf-8")
        self.assertIn("TamPaneAdapter.qml", facade)
        self.assertIn("TAM_PANE_SOCKET", facade)
        self.assertIn("XDG_CURRENT_DESKTOP", facade)

    def test_mock_two_output_initial_events_actions_and_reconnect(self):
        qs = quickshell_bin()
        with tempfile.TemporaryDirectory(prefix="tamlinux-tampane-mock-") as directory:
            root = Path(directory)
            config = _stage_fixture(root)
            sock_path = root / "tam-pane.sock"
            server = MockTamPaneServer(sock_path)
            server.start()
            try:
                env = {
                    "PATH": "/usr/bin",
                    "HOME": directory,
                    "XDG_RUNTIME_DIR": directory,
                    "XDG_CONFIG_HOME": directory,
                    "XDG_CACHE_HOME": directory,
                    "QT_QPA_PLATFORM": "offscreen",
                    "QSG_RENDER_LOOP": "basic",
                    "TAM_PANE_SOCKET": str(sock_path),
                    "TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1",
                    "TAMLINUX_ADAPTER_TEST_MODE": "mock",
                }
                result = subprocess.run(
                    [qs, "--no-color", "-p", str(config)],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
            finally:
                server.stop()
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("TAMPANE_STAGE_INITIAL_OK", log)
        self.assertIn("TAMPANE_STAGE_ACTIONS_OK", log)
        self.assertIn("TAMPANE_STAGE_EVENTS_OK", log)
        self.assertIn("TAMPANE_ADAPTER_OK", log)
        self.assertNotIn("TAMPANE_ADAPTER_FAILED", log)
        self.assertNotIn("TypeError", log)
        self.assertNotIn("ReferenceError", log)
        self.assertIn("dispatch tag toggle_view 4 DP-1", server.dispatches)
        self.assertIn("dispatch monitor focus HDMI-A-1", server.dispatches)
        self.assertIn("dispatch dpms off HDMI-A-1", server.dispatches)
        self.assertIn("dispatch focus_app tam-last", server.dispatches)
        self.assertIn("dispatch keyboard next main-kbd", server.dispatches)

    def test_real_headless_two_output_tam_pane(self):
        qs = quickshell_bin()
        candidates = [
            os.environ.get("TAM_PANE_BIN", ""),
            str(ROOT.parent / "tam-pane/build/tam-pane"),
            shutil.which("tam-pane") or "",
        ]
        tam_pane = next((p for p in candidates if p and os.access(p, os.X_OK)), "")
        if not tam_pane:
            self.skipTest("tam-pane binary not available")
        ver = subprocess.run([tam_pane, "--version"], capture_output=True, text=True, timeout=5)
        ver_text = (ver.stdout + ver.stderr).strip()
        parts = ver_text.split()
        ver_tuple = tuple(int(x) for x in parts[-1].split(".")) if parts and all(x.isdigit() for x in parts[-1].split(".")) else ()
        if ver_tuple < (0, 2, 7):
            self.skipTest(f"tam-pane >= 0.2.7 required (got {ver_text!r})")

        with tempfile.TemporaryDirectory(prefix="tamlinux-tampane-headless-") as directory:
            root = Path(directory)
            config = _stage_fixture(root)
            pane_env = {
                "PATH": "/usr/bin",
                "HOME": directory,
                "XDG_RUNTIME_DIR": directory,
                "XDG_CONFIG_HOME": directory,
                "WLR_BACKENDS": "headless",
                "WLR_HEADLESS_OUTPUTS": "2",
                "WLR_RENDERER": "pixman",
            }
            pane = subprocess.Popen(
                [tam_pane],
                env=pane_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                sock_dir = root / "tam-pane"
                sock_path: Path | None = None
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if sock_dir.is_dir():
                        found = sorted(sock_dir.glob("*.sock"))
                        if found:
                            sock_path = found[0]
                            break
                    time.sleep(0.05)
                self.assertIsNotNone(sock_path, "headless tam-pane did not create IPC socket")
                env = {
                    "PATH": "/usr/bin",
                    "HOME": directory,
                    "XDG_RUNTIME_DIR": directory,
                    "XDG_CONFIG_HOME": directory,
                    "XDG_CACHE_HOME": directory,
                    "QT_QPA_PLATFORM": "offscreen",
                    "QSG_RENDER_LOOP": "basic",
                    "TAM_PANE_SOCKET": str(sock_path),
                    "TAMLINUX_COMPOSITOR_LIVE_ACTIONS": "1",
                    "TAMLINUX_ADAPTER_TEST_MODE": "headless",
                }
                result = subprocess.run(
                    [qs, "--no-color", "-p", str(config)],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
            finally:
                pane.terminate()
                try:
                    pane.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pane.kill()
                    pane.wait(timeout=5)
                if pane.stdout:
                    pane.stdout.close()
                if pane.stderr:
                    pane.stderr.close()
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("TAMPANE_ADAPTER_HEADLESS_OK", log)
        self.assertNotIn("TAMPANE_ADAPTER_FAILED", log)
        self.assertNotIn("TypeError", log)
        self.assertNotIn("ReferenceError", log)


if __name__ == "__main__":
    unittest.main()
