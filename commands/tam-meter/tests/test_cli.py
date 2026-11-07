#!/usr/bin/env python3
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tam-meter"
FIX = ROOT / "tests" / "fixtures"


class TamMeterCli(unittest.TestCase):
    def env(self):
        e = os.environ.copy()
        e["TAM_METER_SYSFS_ROOT"] = str(FIX / "sysfs")
        e["TAM_METER_PROC_ROOT"] = str(FIX / "procfs")
        return e

    def test_help(self):
        p = subprocess.run(
            [str(BIN), "--help"], capture_output=True, text=True, check=True
        )
        self.assertIn("tam-meter", p.stdout)
        self.assertIn("reading", p.stdout)
        self.assertIn("now", p.stdout)
        self.assertIn("top", p.stdout)

    def test_version(self):
        for flag in ("--version", "-v"):
            with self.subTest(flag=flag):
                p = subprocess.run(
                    [str(BIN), flag], capture_output=True, text=True, check=True
                )
                self.assertEqual(p.stdout.strip(), "0.1.0")

    def test_unknown_command(self):
        p = subprocess.run(
            [str(BIN), "bogus"], capture_output=True, text=True
        )
        self.assertEqual(p.returncode, 1)
        self.assertIn("unknown command", p.stderr)

    def test_now_json(self):
        p = subprocess.run(
            [str(BIN), "now", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["power_w"], 4.12)
        self.assertEqual(doc["temp_c"], 38.5)
        self.assertIn("cpu_busy_percent", doc)

    def test_reading_json_quick(self):
        p = subprocess.run(
            [str(BIN), "reading", "--settle", "0", "--minutes", "0.01", "--interval", "0.2", "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["boot_id"], "da1124be")
        self.assertAlmostEqual(doc["power"]["mean_w"], 4.12, places=2)
        self.assertIn("busiest_processes", doc)


if __name__ == "__main__":
    unittest.main()
