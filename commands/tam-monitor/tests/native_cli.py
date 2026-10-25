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
        for args in ([], ["list"], ["inspect"], ["inspect", "--fd", "-1"],
                     ["inspect", "--fd", "999999999999999999999999"],
                     ["inspect", "--fd", "12x"], ["inspect", "--fd", ""],
                     ["inspect", "--fd", "42", "--fd", "43"],
                     ["inspect", "--fd", "42", "--keep"],
                     ["inspect", "--fd", "42", "--keep", ""],
                     ["inspect", "--fd", "42", "--keep", "x" * 100]):
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

    def test_human_output(self):
        p = self.run_cli("inspect", "--fd", "42", "--keep", "DP-1")
        self.assertEqual(p.returncode, 0)
        self.assertIn("detach 2 connectors", p.stdout)
        self.assertIn("no display state changed", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
