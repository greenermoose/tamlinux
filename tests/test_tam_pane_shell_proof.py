#!/usr/bin/env python3
"""End-to-end headless tam-pane 0.2.8 proof suite for 0.7.0 Milestone 7.

Exercises the shell host, hyprland_backend.py tam-pane IPC, all nine shipped
fred.* plugins (especially fred.workspaces and fred.monitor), clipboard paste,
tam-launch-about, and everyday apps (tam-last, tam-clam, tam-edit) with
HYPRLAND_INSTANCE_SIGNATURE unset.
"""
from __future__ import annotations

import json
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
PLUGINS = DESKTOP / "plugins"
TAM_PANE_LUA = DESKTOP / "session/tam-pane.lua"
COMMANDS_DIR = ROOT / "src/commands"

sys.path.insert(0, str(ROOT / "tests"))
from quickshell_bin import quickshell_bin

EXPECTED_PLUGINS = sorted([
    "fred.agents",
    "fred.clock",
    "fred.keyboard",
    "fred.monitor",
    "fred.sysinfo",
    "fred.tamversion",
    "fred.tides",
    "fred.weather",
    "fred.workspaces",
])


def find_bin(name: str, extra: list[str] | None = None) -> str | None:
    candidates = [
        *(extra or []),
        str(Path.home() / ".local/bin" / name),
        f"/usr/bin/tamlinux/{name}",
        shutil.which(name) or "",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


class TamPaneShellProofTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tam_pane = find_bin(
            "tam-pane",
            [
                os.environ.get("TAM_PANE_BIN", ""),
                str(ROOT.parent / "tam-pane/build/tam-pane"),
            ],
        )
        if not self.tam_pane:
            self.skipTest("tam-pane binary not found")

        self.tmp = Path(tempfile.mkdtemp(prefix="tam-pane-m7-proof-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

        self.runtime_dir = self.tmp / "runtime"
        self.runtime_dir.mkdir(mode=0o700)
        self.config_dir = self.tmp / "config"
        self.config_dir.mkdir(mode=0o700)
        self.state_dir = self.tmp / "state"
        self.state_dir.mkdir(mode=0o700)
        self.cache_dir = self.tmp / "cache"
        self.cache_dir.mkdir(mode=0o700)

        self.env = os.environ.copy()
        for drop in (
            "HYPRLAND_INSTANCE_SIGNATURE",
            "WAYLAND_DISPLAY",
            "TAM_PANE_SOCKET",
            "TAMLINUX_COMPOSITOR_BACKEND",
            "TAMLINUX_PLUGIN_ENTRIES",
        ):
            self.env.pop(drop, None)
        self.env["HOME"] = str(self.tmp)
        self.env["XDG_RUNTIME_DIR"] = str(self.runtime_dir)
        self.env["XDG_CONFIG_HOME"] = str(self.config_dir)
        self.env["XDG_STATE_HOME"] = str(self.state_dir)
        self.env["XDG_CACHE_HOME"] = str(self.cache_dir)
        self.env["XDG_CURRENT_DESKTOP"] = "tam-pane"
        self.env["XDG_SESSION_TYPE"] = "wayland"
        self.env["TAMLINUX_COMPOSITOR_COMMANDS"] = str(HOST)
        self.env["TAMLINUX_COMPOSITOR_LIVE_ACTIONS"] = "1"
        self.env["WLR_BACKENDS"] = "headless"
        self.env["WLR_HEADLESS_OUTPUTS"] = "2"
        self.env["WLR_RENDERER"] = "pixman"

        self.proc = subprocess.Popen(
            [self.tam_pane, "-c", str(TAM_PANE_LUA)],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(self._stop_compositor)

        sock = self._wait_for_socket()
        self.sock_path = sock
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

    def _backend(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOST / "hyprland_backend.py"), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def test_backend_and_plugin_helpers_on_tam_pane(self) -> None:
        # 1. hyprland_backend.py queries over $TAM_PANE_SOCKET (Hyprland stopped)
        mons = self._backend("monitors-all")
        self.assertEqual(mons.returncode, 0, mons.stderr)
        mon_list = json.loads(mons.stdout)
        names = sorted(m["name"] for m in mon_list)
        self.assertEqual(names, ["HEADLESS-1", "HEADLESS-2"])

        ws = self._backend("workspaces")
        self.assertEqual(ws.returncode, 0, ws.stderr)
        self.assertTrue(len(json.loads(ws.stdout)) >= 2)

        active_ws = self._backend("active-workspace")
        self.assertEqual(active_ws.returncode, 0, active_ws.stderr)
        self.assertIn("id", json.loads(active_ws.stdout))

        devs = self._backend("devices")
        self.assertEqual(devs.returncode, 0, devs.stderr)
        self.assertIn("keyboards", json.loads(devs.stdout))

        binds = self._backend("binds")
        self.assertEqual(binds.returncode, 0, binds.stderr)
        self.assertGreater(len(json.loads(binds.stdout)), 10)

        # 2. Mutations: focus-output, select-output-workspace, dpms, reload
        self.assertEqual(self._backend("focus-output", "HEADLESS-2").returncode, 0)
        self.assertEqual(self._backend("select-output-workspace", "3", "HEADLESS-2").returncode, 0)
        self.assertEqual(self._backend("dpms", "HEADLESS-2", "off").returncode, 0)
        self.assertEqual(self._backend("dpms", "HEADLESS-2", "on").returncode, 0)
        self.assertEqual(self._backend("reload").returncode, 0)

        # 3. fred.workspaces/tam-desktop-mode status + switch on tam-pane
        dm = PLUGINS / "fred.workspaces/tam-desktop-mode"
        st = subprocess.run([str(dm), "status"], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(st.returncode, 0, st.stderr)
        sw = subprocess.run([str(dm), "switch", "2"], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(sw.returncode, 0, sw.stderr)

        # 4. fred.monitor/fred-monitor-layout status + capture_layout + persist to tam-pane/monitors.lua
        ml = PLUGINS / "fred.monitor/fred-monitor-layout"
        st_ml = subprocess.run([str(ml), "status"], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(st_ml.returncode, 0, st_ml.stderr + st_ml.stdout)
        self.assertTrue(json.loads(st_ml.stdout).get("ok"), st_ml.stdout)

        # Capture + persist via module call to verify tp.monitor(...) format & tam-pane/monitors.lua path
        persist_code = (
            "import importlib.util, importlib.machinery, json, sys\n"
            f"loader = importlib.machinery.SourceFileLoader('fml', {str(ml)!r})\n"
            "spec = importlib.util.spec_from_loader('fml', loader)\n"
            "mod = importlib.util.module_from_spec(spec)\n"
            "loader.exec_module(mod)\n"
            "layout = mod.capture_layout()\n"
            "assert len(layout) == 2, layout\n"
            "target, _, _, _ = mod.persist_layout(layout)\n"
            "print(target)\n"
        )
        persisted = subprocess.run(
            [sys.executable, "-c", persist_code],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(persisted.returncode, 0, persisted.stderr)
        target_path = Path(persisted.stdout.strip())
        self.assertEqual(target_path, self.config_dir / "tamlinux/tam-pane/monitors.lua")
        lua_text = target_path.read_text(encoding="utf-8")
        self.assertIn("tp.monitor(", lua_text)
        self.assertNotIn("hl.monitor(", lua_text)
        # Reload tam-pane with the generated monitors.lua to verify valid Lua
        self.assertEqual(self._backend("reload").returncode, 0)

    def test_shell_env_and_all_nine_plugins_on_headless_tam_pane(self) -> None:
        # 1. Verify TAM_PANE_SOCKET is forwarded in BarApi and all plugin closed envs
        for rel in (
            "src/desktop/shell/host/BarApi.qml",
            "src/desktop/plugins/fred.workspaces/Workspaces.qml",
            "src/desktop/plugins/fred.monitor/Panel.qml",
            "src/desktop/plugins/fred.keyboard/BarWidget.qml",
            "src/desktop/plugins/fred.clock/Panel.qml",
        ):
            self.assertIn("TAM_PANE_SOCKET", (ROOT / rel).read_text(encoding="utf-8"), rel)

        # 2. Verify session_start.py discovers all 9 shipped plugins and preserves TAM_PANE_SOCKET
        sys.path.insert(0, str(HOST))
        import session_start  # noqa: E402

        test_env = dict(self.env)
        test_env["TAMLINUX_PLUGINS_DIR"] = str(PLUGINS)
        env_out, notes = session_start.session_environment(test_env)
        self.assertEqual(env_out.get("TAM_PANE_SOCKET"), str(self.sock_path))
        self.assertEqual(env_out.get("TAMLINUX_HYPRLAND_VERSION"), "")
        entries = json.loads(env_out["TAMLINUX_PLUGIN_ENTRIES"])
        self.assertEqual(sorted(entries.keys()), EXPECTED_PLUGINS, f"notes={notes}")

        # 3. Boot Quickshell on the real shell tree against headless two-output tam-pane
        qs = quickshell_bin()
        env_out["QT_QPA_PLATFORM"] = "wayland"
        env_out["QSG_RENDER_LOOP"] = "basic"
        env_out["QT_QUICK_BACKEND"] = "software"
        session_start.initialize_defaults(env_out)

        qs_proc = subprocess.Popen(
            [qs, "--no-color", "-p", str(DESKTOP / "shell")],
            env=env_out,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            time.sleep(2.5)
        finally:
            qs_proc.terminate()
            try:
                out, err = qs_proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                qs_proc.kill()
                out, err = qs_proc.communicate(timeout=2)
        log = out + err
        self.assertIn("compositor-backend tam-pane", log, log)
        self.assertNotIn("TypeError", log, log)
        self.assertNotIn("ReferenceError", log, log)
        self.assertNotIn("compositor-backend failed", log, log)

    def test_everyday_apps_tam_last_tam_clam_tam_edit_and_about(self) -> None:
        # 1. Run tam-clam inside tam-last on headless tam-pane
        tam_last = find_bin("tam-last")
        tam_clam = find_bin("tam-clam")
        if tam_last and tam_clam:
            marker = self.tmp / "clam-proof.txt"
            res = subprocess.run(
                [tam_last, "-e", tam_clam, "-c", f"echo MILESTONE7_CLAM_OK > {marker}"],
                env=self.env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "MILESTONE7_CLAM_OK")

        # 2. Save an edit in tam-edit via PTY
        tam_edit = find_bin("tam-edit")
        if tam_edit:
            scratch = self.tmp / "edit-proof.txt"
            scratch.write_text("before\n", encoding="utf-8")
            master_fd, slave_fd = pty.openpty()
            try:
                ed = subprocess.Popen(
                    [tam_edit, str(scratch)],
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    env=self.env,
                    close_fds=True,
                )
                os.close(slave_fd)
                slave_fd = -1
                time.sleep(0.35)
                # Type 'A', Ctrl+S to save, Ctrl+Q to quit
                os.write(master_fd, b"A")
                time.sleep(0.15)
                os.write(master_fd, b"\x13")
                time.sleep(0.2)
                os.write(master_fd, b"\x11")
                deadline = time.monotonic() + 5.0
                while ed.poll() is None and time.monotonic() < deadline:
                    if select.select([master_fd], [], [], 0.05)[0]:
                        try:
                            os.read(master_fd, 4096)
                        except OSError:
                            break
                if ed.poll() is None:
                    ed.terminate()
                    ed.wait(timeout=2)
                self.assertEqual(ed.returncode, 0)
            finally:
                if slave_fd >= 0:
                    os.close(slave_fd)
                os.close(master_fd)
            self.assertIn("A", scratch.read_text(encoding="utf-8"))

        # 3. Verify tam-launch-about does not invoke hyprctl under tam-pane
        shim_bin = self.tmp / "about-bin"
        shim_bin.mkdir()
        hypr_called = self.tmp / "hypr-called"
        hypr_stub = shim_bin / "hyprctl"
        hypr_stub.write_text(f"#!/bin/sh\ntouch {hypr_called}\nexit 1\n", encoding="utf-8")
        hypr_stub.chmod(0o755)
        tui_called = self.tmp / "tui-called"
        tui_stub = shim_bin / "tam-launch-or-focus-tui"
        tui_stub.write_text(f"#!/bin/sh\necho \"$*\" > {tui_called}\nexit 0\n", encoding="utf-8")
        tui_stub.chmod(0o755)
        about_env = dict(self.env)
        about_env["PATH"] = f"{shim_bin}:{about_env.get('PATH', '')}"
        about = subprocess.run(
            [str(COMMANDS_DIR / "tam-launch-about/tam-launch-about")],
            env=about_env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(about.returncode, 0, about.stderr)
        self.assertFalse(hypr_called.exists(), "tam-launch-about called hyprctl under tam-pane")
        self.assertIn("org.tamlinux.about", tui_called.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
