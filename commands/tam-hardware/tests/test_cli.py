#!/usr/bin/env python3
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tam-hardware"
FIX = ROOT / "tests" / "fixtures"


class TamHardwareCli(unittest.TestCase):
    def env(self):
        e = os.environ.copy()
        e["TAM_HARDWARE_SYSFS_ROOT"] = str(FIX / "sysfs")
        e["TAM_HARDWARE_FIXTURE_CPU"] = str(FIX / "cpu.txt")
        return e

    def test_help(self):
        p = subprocess.run(
            [str(BIN), "--help"], capture_output=True, text=True, check=True
        )
        self.assertIn("tam-hardware", p.stdout)

    def test_version(self):
        for flag in ("--version", "-v"):
            with self.subTest(flag=flag):
                p = subprocess.run(
                    [str(BIN), flag], capture_output=True, text=True, check=True
                )
                self.assertEqual(p.stdout.strip(), "0.1.0")
                self.assertEqual(p.stderr, "")

    def test_unknown_option(self):
        p = subprocess.run(
            [str(BIN), "--bogus"], capture_output=True, text=True, env=self.env()
        )
        self.assertEqual(p.returncode, 1)
        self.assertIn("unknown option", p.stderr)

    def test_json_schema(self):
        p = subprocess.run(
            [str(BIN), "--json"],
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["cpu"]["brand"], "Fixture Ryzen Test CPU")
        self.assertEqual(doc["cpu"]["features"], ["aes", "avx", "avx2", "sse2", "sse4_1"])
        self.assertEqual(doc["dmi"]["product_name"], "Fixture Product")
        self.assertNotIn("board_serial", doc["dmi"])
        blob = json.dumps(doc)
        self.assertNotIn("SECRET", blob)

    def test_human(self):
        p = subprocess.run(
            [str(BIN)], capture_output=True, text=True, check=True, env=self.env()
        )
        self.assertIn("Fixture Ryzen Test CPU", p.stdout)
        self.assertIn("Architecture:", p.stdout)


if __name__ == "__main__":
    unittest.main()
