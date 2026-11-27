#!/usr/bin/env python3
"""Behavioral tests for Tamlinux Milestones 11-14 wired to tam-pane 0.2.17."""

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "src" / "commands"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class TestTamPaneMilestones11To14(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="tam-pane-m11-14-")
        self.tmp_path = Path(self.tmp.name)
        self.bin_dir = self.tmp_path / "bin"
        self.bin_dir.mkdir()
        self.log_file = self.tmp_path / "calls.log"
        self.state_file = self.tmp_path / "state.json"

        # Symlink all real commands we may call transitively so PATH works.
        for cmd_dir in COMMANDS.iterdir():
            exe = cmd_dir / cmd_dir.name
            if exe.is_file():
                target = self.bin_dir / cmd_dir.name
                if not target.exists():
                    target.symlink_to(exe)

        # Stub tam-notification-send & tam-shell as no-ops logging calls.
        for name in ("tam-notification-send", "tam-shell"):
            stub = self.bin_dir / name
            if stub.is_symlink() or stub.exists():
                stub.unlink()
            write_executable(
                stub,
                f"#!/bin/bash\nprintf '%s %s\\n' {name!r} \"$*\" >> {str(self.log_file)!r}\n",
            )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        env["TAM_PANE_SOCKET"] = str(self.tmp_path / "fake.sock")
        env["PATH"] = f"{self.bin_dir}:{env.get('PATH', '')}"
        env["XDG_RUNTIME_DIR"] = str(self.tmp_path)
        env["XDG_STATE_HOME"] = str(self.tmp_path / "state")
        env["XDG_CONFIG_HOME"] = str(self.tmp_path / "config")
        if extra:
            env.update(extra)
        return env

    def install_mock_tam_pane(self, script_body: str) -> None:
        stub = self.bin_dir / "tam-pane"
        if stub.is_symlink() or stub.exists():
            stub.unlink()
        write_executable(stub, "#!/bin/bash\n" + script_body)

    def test_milestone_11_sleep_lock_queries_lock_state(self) -> None:
        self.install_mock_tam_pane(
            f"""
printf 'tam-pane %s\\n' "$*" >> {str(self.log_file)!r}
case "$*" in
  "msg lock")
    printf 'locked\\n' > {str(self.state_file)!r}
    exit 0
    ;;
  "msg lock_state")
    if [[ -f {str(self.state_file)!r} ]]; then
      printf 'lock\\tlocked=1\\tactive=1\\tlocker_running=1\\tsurfaces=1\\toutputs=1\\n'
    else
      printf 'lock\\tlocked=0\\tactive=0\\tlocker_running=0\\tsurfaces=0\\toutputs=1\\n'
    fi
    exit 0
    ;;
  *) exit 0 ;;
esac
"""
        )
        # Stub tam-hyprland-monitor-clamshell so sleep-lock stays focused on lock_state.
        clamshell = self.bin_dir / "tam-hyprland-monitor-clamshell"
        clamshell.unlink()
        write_executable(clamshell, "#!/bin/bash\nexit 0\n")

        res = subprocess.run(
            [str(COMMANDS / "tam-system-sleep-lock" / "tam-system-sleep-lock"), "2000"],
            env=self.make_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        log = self.log_file.read_text()
        self.assertIn("tam-pane msg lock\n", log)
        self.assertIn("tam-pane msg lock_state\n", log)

    def test_milestone_12_nightlight_uses_native_gamma(self) -> None:
        self.install_mock_tam_pane(
            f"""
printf 'tam-pane %s\\n' "$*" >> {str(self.log_file)!r}
case "$*" in
  "msg gamma")
    if [[ -f {str(self.state_file)!r} ]]; then
      cat {str(self.state_file)!r}
    else
      printf 'gamma\\ttemperature=6500\\tenabled=0\\n'
    fi
    ;;
  "msg dispatch gamma 4000")
    printf 'gamma\\ttemperature=4000\\tenabled=1\\n' > {str(self.state_file)!r}
    ;;
  "msg dispatch gamma reset")
    printf 'gamma\\ttemperature=6500\\tenabled=0\\n' > {str(self.state_file)!r}
    ;;
esac
"""
        )
        cmd = str(COMMANDS / "tam-toggle-nightlight" / "tam-toggle-nightlight")
        env = self.make_env()

        # Initially off
        r0 = subprocess.run([cmd, "--status"], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(r0.stdout), {"enabled": False, "temperature": 6500})

        # Toggle on -> 4000K
        subprocess.run([cmd], env=env, check=True)
        r1 = subprocess.run([cmd, "--status"], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(r1.stdout), {"enabled": True, "temperature": 4000})

        # Toggle off -> reset (6500K)
        subprocess.run([cmd], env=env, check=True)
        r2 = subprocess.run([cmd, "--status"], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(r2.stdout), {"enabled": False, "temperature": 6500})

    def test_milestone_12_capture_region_uses_native_freeze(self) -> None:
        self.install_mock_tam_pane(
            f"""
printf 'tam-pane %s\\n' "$*" >> {str(self.log_file)!r}
case "$*" in
  "msg monitors")
    printf 'monitor\\tname=DP-1\\tx=0\\ty=0\\tw=1920\\th=1080\\tfocused=1\\tenabled=1\\n'
    ;;
  "msg windows")
    exit 0
    ;;
esac
"""
        )
        write_executable(self.bin_dir / "slurp", "#!/bin/bash\necho '10,20 300x200'\n")
        cmd = str(COMMANDS / "tam-capture-region" / "tam-capture-region")
        res = subprocess.run([cmd, "region", "--keep-freeze"], env=self.make_env(), capture_output=True, text=True, check=True)
        lines = res.stdout.strip().splitlines()
        self.assertEqual(lines, ["tam-pane-freeze", "10,20 300x200"])
        log = self.log_file.read_text()
        self.assertIn("tam-pane msg dispatch freeze on\n", log)
        self.assertNotIn("freeze off", log)

        # Without --keep-freeze, freeze off runs on exit.
        self.log_file.unlink()
        res2 = subprocess.run([cmd, "region"], env=self.make_env(), capture_output=True, text=True, check=True)
        self.assertEqual(res2.stdout.strip(), "10,20 300x200")
        log2 = self.log_file.read_text()
        self.assertIn("tam-pane msg dispatch freeze on\n", log2)
        self.assertIn("tam-pane msg dispatch freeze off\n", log2)

    def test_milestone_13_devices_laptop_clamshell_and_windows(self) -> None:
        self.install_mock_tam_pane(
            f"""
printf 'tam-pane %s\\n' "$*" >> {str(self.log_file)!r}
case "$*" in
  "msg devices")
    printf 'device\\ttype=keyboard\\tname=AT Translated Set 2 keyboard\\n'
    printf 'device\\ttype=pointer\\tname=SynPS/2 Synaptics TouchPad\\n'
    printf 'device\\ttype=touch\\tname=ELAN Touchscreen\\n'
    ;;
  "msg monitors")
    printf 'monitor\\tname=eDP-1\\tx=0\\ty=0\\tw=1920\\th=1080\\tfocused=1\\tlayout=dwindle\\tdpms=1\\tdescription=Panel\\tenabled=1\\n'
    printf 'monitor\\tname=DP-2\\tx=1920\\ty=0\\tw=1920\\th=1080\\tfocused=0\\tlayout=dwindle\\tdpms=1\\tdescription=Ext\\tenabled=1\\n'
    ;;
  "msg windows")
    printf 'window\\tmonitor=eDP-1\\tid=0x11\\tpid=100\\ttags=1\\tfocused=1\\tfloating=0\\tfullscreen=0\\tpinned=0\\n'
    printf 'window\\tmonitor=DP-2\\tid=0x22\\tpid=101\\ttags=1\\tfocused=0\\tfloating=0\\tfullscreen=0\\tpinned=0\\n'
    ;;
  "msg focused")
    printf 'window\\tmonitor=eDP-1\\tid=0x11\\tpid=100\\ttags=1\\tfocused=1\\tfloating=0\\tfullscreen=0\\tpinned=0\\n'
    ;;
esac
"""
        )
        # Stub tam-hw-clamshell to report lid closed (exit 0).
        clamshell_hw = self.bin_dir / "tam-hw-clamshell"
        if clamshell_hw.is_symlink() or clamshell_hw.exists():
            clamshell_hw.unlink()
        write_executable(clamshell_hw, "#!/bin/bash\nexit 0\n")

        env = self.make_env()

        # Touchpad & touchscreen
        r_tp = subprocess.run([str(COMMANDS / "tam-hw-touchpad" / "tam-hw-touchpad")], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(r_tp.stdout.strip(), "SynPS/2 Synaptics TouchPad")
        r_ts = subprocess.run([str(COMMANDS / "tam-hw-touchscreen" / "tam-hw-touchscreen")], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(r_ts.stdout.strip(), "ELAN Touchscreen")

        # Laptop monitor & external active & clamshell
        r_lap = subprocess.run([str(COMMANDS / "tam-hyprland-monitor-laptop" / "tam-hyprland-monitor-laptop")], env=env, capture_output=True, text=True, check=True)
        self.assertEqual(r_lap.stdout.strip(), "eDP-1")
        r_ext = subprocess.run([str(COMMANDS / "tam-hyprland-monitor-external-active" / "tam-hyprland-monitor-external-active")], env=env)
        self.assertEqual(r_ext.returncode, 0)

        subprocess.run([str(COMMANDS / "tam-hyprland-monitor-clamshell" / "tam-hyprland-monitor-clamshell")], env=env, check=True)
        subprocess.run([str(COMMANDS / "tam-hyprland-focus-app" / "tam-hyprland-focus-app"), "foot"], env=env, check=True)
        subprocess.run([str(COMMANDS / "tam-hyprland-window-pop" / "tam-hyprland-window-pop"), "900", "600"], env=env, check=True)
        subprocess.run([str(COMMANDS / "tam-hyprland-window-close-all" / "tam-hyprland-window-close-all")], env=env, check=True)
        subprocess.run([str(COMMANDS / "tam-hyprland-workspace-layout-toggle" / "tam-hyprland-workspace-layout-toggle")], env=env, check=True)

        log = self.log_file.read_text()
        self.assertIn("tam-pane msg dispatch monitor disable eDP-1\n", log)
        self.assertIn("tam-pane msg dispatch focus_app foot\n", log)
        self.assertIn("tam-pane msg dispatch float on 0x11\n", log)
        self.assertIn("tam-pane msg dispatch resize_exact 900 600 0x11\n", log)
        self.assertIn("tam-pane msg dispatch center 0x11\n", log)
        self.assertIn("tam-pane msg dispatch pin on 0x11\n", log)
        self.assertIn("tam-pane msg dispatch raise 0x11\n", log)
        self.assertIn("tam-pane msg dispatch close 0x11\n", log)
        self.assertIn("tam-pane msg dispatch close 0x22\n", log)
        self.assertIn("tam-pane msg dispatch tag view 1\n", log)
        self.assertIn("tam-pane msg dispatch layout set scroller\n", log)

    def test_milestone_14_theme_template_and_reload(self) -> None:
        self.install_mock_tam_pane(
            f"printf 'tam-pane %s\\n' \"$*\" >> {str(self.log_file)!r}\n"
        )
        env = self.make_env()

        # tam-restart-hyprctl reloads tam-pane under tam-pane
        subprocess.run([str(COMMANDS / "tam-restart-hyprctl" / "tam-restart-hyprctl")], env=env, check=True)
        self.assertIn("tam-pane msg reload\n", self.log_file.read_text())

        # tam-pane.lua.tpl renders valid Lua with hex border colors
        stage = self.tmp_path / "theme-stage"
        stage.mkdir()
        (stage / "colors.toml").write_text(
            'accent = "#7aa2f7"\nbackground = "#1a1b26"\nforeground = "#c0caf5"\n',
            encoding="utf-8",
        )
        tpl_env = self.make_env(
            {
                "TAMLINUX_THEME_STAGE": str(stage),
                "TAMLINUX_ASSETS_DIR": str(ROOT / "src" / "desktop" / "assets"),
            }
        )
        subprocess.run(
            [str(COMMANDS / "tam-theme-set-templates" / "tam-theme-set-templates")],
            env=tpl_env,
            check=True,
        )
        rendered = (stage / "tam-pane.lua").read_text(encoding="utf-8")
        self.assertIn('border_color_focused = "#7aa2f7"', rendered)
        self.assertIn('border_color_unfocused = "#595959"', rendered)


if __name__ == "__main__":
    unittest.main()
