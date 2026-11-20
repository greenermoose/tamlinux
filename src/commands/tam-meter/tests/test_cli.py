#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
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

    def _make_sysfs(self, tmp, hwmons=None, power_supply=None):
        sysfs = Path(tmp) / "sysfs"
        (sysfs / "class" / "hwmon").mkdir(parents=True, exist_ok=True)
        if hwmons:
            for name, entries in hwmons.items():
                d = sysfs / "class" / "hwmon" / name
                d.mkdir(parents=True, exist_ok=True)
                (d / "name").write_text(entries.get("name", "") + "\n")
                for k, v in entries.items():
                    if k == "name":
                        continue
                    (d / k).write_text(str(v) + "\n")
        if power_supply:
            ps = sysfs / "class" / "power_supply"
            ps.mkdir(parents=True, exist_ok=True)
            for bat, entries in power_supply.items():
                d = ps / bat
                d.mkdir(parents=True, exist_ok=True)
                for k, v in entries.items():
                    (d / k).write_text(str(v) + "\n")
        # procfs minimal
        procfs = Path(tmp) / "procfs"
        procfs.mkdir(parents=True, exist_ok=True)
        (procfs / "stat").write_text("cpu  100 0 50 800 10 0 0 0 0 0\nintr 1\nctxt 2\n")
        (procfs / "meminfo").write_text("MemAvailable: 42000000 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n")
        return sysfs, procfs

    def test_reading_coretemp_no_power(self):
        with tempfile.TemporaryDirectory() as tmp:
            sysfs, procfs = self._make_sysfs(tmp, hwmons={
                "hwmon0": {"name": "coretemp", "temp1_input": 42000},
            })
            env = os.environ.copy()
            env["TAM_METER_SYSFS_ROOT"] = str(sysfs)
            env["TAM_METER_PROC_ROOT"] = str(procfs)
            p = subprocess.run(
                [str(BIN), "reading", "--settle", "0", "--minutes", "0.01", "--interval", "0.2", "--json"],
                capture_output=True, text=True, check=True, env=env,
            )
            doc = json.loads(p.stdout)
            self.assertEqual(p.returncode, 0)
            self.assertIsNone(doc["power"])
            self.assertEqual(doc["temperature"]["mean_c"], 42.0)

    def test_now_battery_discharge(self):
        with tempfile.TemporaryDirectory() as tmp:
            sysfs, procfs = self._make_sysfs(tmp, power_supply={
                "BAT0": {"status": "Discharging", "power_now": 6500000},
            })
            env = os.environ.copy()
            env["TAM_METER_SYSFS_ROOT"] = str(sysfs)
            env["TAM_METER_PROC_ROOT"] = str(procfs)
            p = subprocess.run(
                [str(BIN), "now", "--json"],
                capture_output=True, text=True, check=True, env=env,
            )
            doc = json.loads(p.stdout)
            self.assertEqual(doc["power_w"], 6.5)


if __name__ == "__main__":
    unittest.main()
