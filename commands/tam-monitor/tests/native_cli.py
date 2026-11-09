"""Native feasibility CLI checks; no DRM device or session is contacted."""
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeCLI(unittest.TestCase):
    def run_cli(self, *args, fixture=True, **kwargs):
        exe = ROOT / "build" / ("tam-monitor-fixture" if fixture else "tam-monitor")
        return subprocess.run([str(exe), *args], text=True, capture_output=True,
                              timeout=5, **kwargs)

    def test_shared_crtc_and_framebuffer(self):
        p = self.run_cli("inspect", "--fd", "42", "--keep", "DP-1", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["driver"], 'fixture"driver\\')
        self.assertTrue(data["read_only"])
        self.assertFalse(data["restorable"])
        self.assertEqual(data["analysis"], dict(validated_by_kernel=False, keep=100,
                         detach=[101, 102], disable_crtcs=[11], disable_planes=[201]))
        self.assertEqual(data["connectors"][0]["object"]["properties"][0]["value"], "10")

    def test_other_retained_output(self):
        p = self.run_cli("inspect", "--fd", "42", "--keep", "HDMI-A-1", "--json")
        self.assertEqual(json.loads(p.stdout)["analysis"]["disable_crtcs"], [10])

    def test_missing_selection(self):
        p = self.run_cli("inspect", "--fd", "42", "--keep", "missing", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertFalse(json.loads(p.stdout)["ok"])

    def test_errors_are_machine_readable(self):
        for args in ([], ["list", "--bad"], ["inspect"], ["inspect", "--fd", "-1"],
                     ["inspect", "--fd", "999999999999999999999999"],
                     ["inspect", "--fd", "12x"], ["inspect", "--fd", ""],
                     ["inspect", "--fd", "42", "--fd", "43"],
                     ["inspect", "--fd", "42", "--keep"],
                     ["inspect", "--fd", "42", "--keep", ""],
                     ["inspect", "--fd", "42", "--keep", "x" * 100],
                     ["keep"], ["keep", "DP-1"], ["keep", "DP-1", "--shell", "--seconds", "5"],
                     ["blank", "--card", "1"], ["wake", "DP-1", "--all"]):
            with self.subTest(args=args):
                p = self.run_cli(*args, "--json")
                self.assertEqual(p.returncode, 1)
                self.assertFalse(json.loads(p.stdout)["ok"])

    def test_real_backend_rejects_non_drm_descriptor(self):
        with open(os.devnull) as stream:
            p = self.run_cli("inspect", "--fd", str(stream.fileno()), "--json",
                             fixture=False, pass_fds=(stream.fileno(),))
        self.assertEqual(p.returncode, 1)
        self.assertFalse(json.loads(p.stdout)["ok"])

    def test_help_is_explicit_about_lifetime(self):
        p = self.run_cli("--help", fixture=False)
        self.assertEqual(p.returncode, 0)
        self.assertIn("does not blank any monitor", p.stdout)

    def test_version_matches_header(self):
        header = (ROOT / "version.h").read_text()
        version = header.split('TAM_MONITOR_VERSION "', 1)[1].split('"', 1)[0]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        for flag in ("--version", "-v"):
            with self.subTest(flag=flag):
                p = self.run_cli(flag, fixture=False)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(p.stdout, f"tam-monitor {version}\n")

    def console_fixture(self, modes="DP-1=2560x1440,DP-2=1920x1080,HDMI-A-1=1920x1080",
                        drm_device=True):
        import struct
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="tam-monitor-console-"))
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        fb = tmp / "graphics/fb0"
        (fb / "device/drm/card1").mkdir(parents=True)
        (fb / "name").write_text("amdgpudrmfb\n")
        (fb / "virtual_size").write_text("2560,1440\n")
        (tmp / "dev/dri").mkdir(parents=True)
        var = [0] * 40
        var[0:4] = [1920, 1080, 2560, 1440]
        var[6] = 32
        (tmp / "dev/fb0").write_bytes(struct.pack("40I", *var))
        if drm_device:
            (tmp / "dev/dri/card1").write_bytes(b"")
        env = dict(os.environ, TAM_MONITOR_FIXTURE_GRAPHICS=str(tmp / "graphics"),
                   TAM_MONITOR_FIXTURE_DEV=str(tmp / "dev"),
                   TAM_MONITOR_FIXTURE_DRM=str(tmp / "drm"),
                   TAM_MONITOR_FIXTURE_CONSOLE_MODES=modes)
        return tmp, env

    @staticmethod
    def fb_size(tmp):
        import struct
        return struct.unpack("40I", (tmp / "dev/fb0").read_bytes())[0:2]

    def test_console_size_reports_area_and_views(self):
        tmp, env = self.console_fixture()
        p = self.run_cli("console-size", "--json", env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual((data["width"], data["height"]), (1920, 1080))
        self.assertEqual((data["max_width"], data["max_height"]), (2560, 1440))
        self.assertEqual((data["card"], data["modes_from"], data["changed"]), (1, "drm", False))
        self.assertEqual({o["connector"]: o["view"] for o in data["outputs"]},
                         {"DP-1": "partial", "DP-2": "full", "HDMI-A-1": "full"})
        p = self.run_cli("console-size", env=env)
        self.assertIn("console uses the top-left 1920x1080", p.stdout)

    def test_console_size_fits_one_monitor_then_all(self):
        tmp, env = self.console_fixture()
        p = self.run_cli("console-size", "DP-1", "--json", env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        data = json.loads(p.stdout)
        self.assertTrue(data["changed"] and data["verified"])
        self.assertEqual(self.fb_size(tmp), (2560, 1440))
        views = {o["connector"]: o["view"] for o in data["outputs"]}
        self.assertEqual(views, {"DP-1": "full", "DP-2": "cropped", "HDMI-A-1": "cropped"})
        p = self.run_cli("console-size", "card1-DP-1", "--json", env=env)
        self.assertFalse(json.loads(p.stdout)["changed"])
        p = self.run_cli("console-size", "--all", env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Console area set to 1920x1080", p.stdout)
        self.assertEqual(self.fb_size(tmp), (1920, 1080))
        p = self.run_cli("console-size", "2048x1152", "--json", env=env)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(self.fb_size(tmp), (2048, 1152))

    def test_console_size_all_ignores_dark_monitors(self):
        tmp, env = self.console_fixture(modes="DP-1=2560x1440,DP-2=0x0,HDMI-A-1=0x0")
        p = self.run_cli("console-size", "--all", "--json", env=env)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(self.fb_size(tmp), (2560, 1440))
        p = self.run_cli("console-size", "HDMI-A-1", "--json", env=env)
        self.assertEqual((p.returncode, json.loads(p.stdout)["code"]), (1, 6))

    def test_console_size_refuses_bad_or_oversized_requests(self):
        tmp, env = self.console_fixture()
        for args, code in ((["3840x2160"], 3), (["2561x1440"], 3), (["32x32"], 1),
                           (["2560x"], 1), (["2560"], 1), (["0x0"], 1), (["99999x1"], 1),
                           (["missing"], 6), (["DP-1", "DP-2"], 1), (["--all", "DP-1"], 1),
                           (["--fb"], 1), (["--fb", "32"], 1), (["--bogus"], 1),
                           (["--fb", "1"], 6), (["a/b"], 1)):
            with self.subTest(args=args):
                p = self.run_cli("console-size", *args, "--json", env=env)
                self.assertEqual(p.returncode, 1, p.stdout)
                data = json.loads(p.stdout)
                self.assertFalse(data["ok"])
                self.assertEqual(data["code"], code, data)
        self.assertEqual(self.fb_size(tmp), (1920, 1080))

    @unittest.skipIf(os.geteuid() == 0, "root bypasses file modes")
    def test_console_size_without_device_access(self):
        tmp, env = self.console_fixture()
        (tmp / "dev/fb0").chmod(0o444)
        p = self.run_cli("console-size", "DP-1", env=env)
        self.assertEqual(p.returncode, 1)
        self.assertIn("needs write access", p.stderr)
        self.assertIn("sudo ", p.stderr)
        self.assertIn("console-size DP-1", p.stderr)
        p = self.run_cli("console-size", "DP-1", "--json", env=env)
        self.assertEqual(json.loads(p.stdout)["code"], 8)
        (tmp / "dev/fb0").chmod(0o000)
        p = self.run_cli("console-size", "--json", env=env)
        self.assertEqual(p.returncode, 0, p.stdout)
        data = json.loads(p.stdout)
        self.assertIsNone(data["width"])
        self.assertEqual(data["max_width"], 2560)
        self.assertEqual({o["view"] for o in data["outputs"]}, {"unknown"})

    def test_console_size_falls_back_to_sysfs_modes(self):
        tmp, env = self.console_fixture(drm_device=False)
        for name, status, enabled, mode in (("card1-DP-1", "connected", "enabled", "2560x1440"),
                                            ("card1-DP-2", "connected", "disabled", "1920x1080"),
                                            ("card1-HDMI-A-1", "disconnected", "disabled", "")):
            d = tmp / "drm" / name
            d.mkdir(parents=True)
            (d / "status").write_text(status + "\n")
            (d / "enabled").write_text(enabled + "\n")
            (d / "modes").write_text(mode + "\n" if mode else "")
        p = self.run_cli("console-size", "--json", env=env)
        data = json.loads(p.stdout)
        self.assertEqual(data["modes_from"], "sysfs")
        self.assertEqual([o["connector"] for o in data["outputs"]], ["DP-1"])

    def test_preview_options_reject_before_access(self):
        for args in ([], ["--card", "64"], ["--card", "-1"],
                     ["--card", "1", "--keep", "DP-1", "--seconds", "0"],
                     ["--card", "1", "--keep", "DP-1", "--seconds", "61"],
                     ["--card", "1", "--keep", "", "--seconds", "1"],
                     ["--card", "1", "--card", "2"], ["--seconds", "2x"],
                     ["--card", "1", "--keep", "DP-1", "--seconds", "1", "--fd", "42"]):
            with self.subTest(args=args):
                p = self.run_cli("preview", *args, "--json", fixture=False)
                self.assertEqual(p.returncode, 1)
                self.assertEqual(json.loads(p.stdout)["code"], 1)

    def test_preview_refuses_a_pseudoterminal(self):
        import pty
        import select
        import time
        pid, fd = pty.fork()
        if pid == 0:
            os.execv(str(ROOT / "build/tam-monitor"), ["tam-monitor", "preview", "--card", "0",
                "--keep", "DP-1", "--seconds", "1", "--json"])
        data = b""
        result = 0
        try:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if select.select([fd], [], [], 0.1)[0]:
                    try:
                        part = os.read(fd, 4096)
                    except OSError:
                        break
                    if not part:
                        break
                    data += part
            result, status = os.waitpid(pid, os.WNOHANG)
            self.assertEqual(result, pid, data)
            self.assertEqual(os.waitstatus_to_exitcode(status), 1)
            self.assertIn(b'"ok":false', data)
            self.assertIn(b'"code":9', data)  # inactive VT
        finally:
            os.close(fd)
            if not result:
                os.kill(pid, 9)
                os.waitpid(pid, 0)

    def test_human_output(self):
        p = self.run_cli("inspect", "--fd", "42", "--keep", "DP-1")
        self.assertEqual(p.returncode, 0)
        self.assertIn("detach 2 connectors", p.stdout)
        self.assertIn("no display state changed", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
