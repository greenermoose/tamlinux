#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tam-boot"
FIX = ROOT / "tests" / "fixtures"


class TamBootCli(unittest.TestCase):
    def env(self):
        e = os.environ.copy()
        e["TAM_BOOT_LIST_FILE"] = str(FIX / "boots_list.txt")
        e["TAM_BOOT_JOURNAL_FILE"] = str(FIX / "journal_export_boot0.txt")
        return e

    def test_help(self):
        p = subprocess.run(
            [str(BIN), "--help"], capture_output=True, text=True, check=True
        )
        self.assertIn("tam-boot", p.stdout)
        self.assertIn("list", p.stdout)

    def test_version(self):
        for flag in ("--version", "-v"):
            with self.subTest(flag=flag):
                p = subprocess.run(
                    [str(BIN), flag], capture_output=True, text=True, check=True
                )
                self.assertEqual(p.stdout.strip(), "0.1.0")

    def test_explain_human(self):
        p = subprocess.run(
            [str(BIN)], capture_output=True, text=True, check=True, env=self.env()
        )
        self.assertIn("Boot da1124be", p.stdout)
        self.assertIn("waiting for you (disk passphrase)", p.stdout)
        self.assertIn("Machine time to text login:", p.stdout)

    def test_explain_json(self):
        p = subprocess.run(
            [str(BIN), "--json"], capture_output=True, text=True, check=True, env=self.env()
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["boot_id"], "da1124bec34949f28d123f0baa0e224c")
        self.assertAlmostEqual(doc["totals"]["firmware_s"], 9.98, places=2)
        self.assertAlmostEqual(doc["breakdown"]["passphrase_wait_s"], 8.16, places=1)
        self.assertTrue(doc["breakdown"]["has_passphrase_wait"])

    def test_list_human(self):
        p = subprocess.run(
            [str(BIN), "list"], capture_output=True, text=True, check=True, env=self.env()
        )
        self.assertIn("Boots in journal:", p.stdout)
        self.assertIn("da1124bec34949f28d123f0baa0e224c", p.stdout)

    def test_list_json(self):
        p = subprocess.run(
            [str(BIN), "list", "--json"], capture_output=True, text=True, check=True, env=self.env()
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["schema"], 1)
        self.assertGreaterEqual(len(doc["boots"]), 1)
        self.assertEqual(doc["boots"][-1]["boot_id"], "da1124bec34949f28d123f0baa0e224c")

    def test_passphrase_intermediate_message_excluded_and_slow_steps_sorted(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(textwrap.dedent("""\
                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=1000000
                MESSAGE=usb 1-1: new high-speed USB device

                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=1500000
                MESSAGE=amdgpu: DMUB initialized

                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=4000000
                MESSAGE=Key type encrypted registered

                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=5000000
                MESSAGE=clocksource: Watchdog remote CPU 11 read timed out

                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=11000000
                MESSAGE=PM: Image not found (code -22)

                _BOOT_ID=11111111222222223333333344444444
                _SOURCE_MONOTONIC_TIMESTAMP=11800000
                MESSAGE=BTRFS: device scanned
            """))
            path = Path(tf.name)
        self.addCleanup(path.unlink, missing_ok=True)
        e = self.env()
        e["TAM_BOOT_JOURNAL_FILE"] = str(path)
        p = subprocess.run([str(BIN), "--json"], capture_output=True, text=True, check=True, env=e)
        doc = json.loads(p.stdout)
        self.assertTrue(doc["breakdown"]["has_passphrase_wait"])
        self.assertAlmostEqual(doc["breakdown"]["passphrase_wait_s"], 7.0, places=2)
        steps = doc["slow_steps"]
        # Should contain 2.5s (1.5 -> 4.0), 0.8s (11.0 -> 11.8), 0.5s (1.0 -> 1.5), sorted descending
        # and NOT the 1.0s or 6.0s sub-gaps inside the passphrase prompt window (4.0 -> 11.0).
        self.assertEqual([round(s["duration_s"], 2) for s in steps], [2.5, 0.8, 0.5])
        for s in steps:
            self.assertNotIn("Watchdog remote CPU", s["description"])
            self.assertTrue(s["description"].endswith('"'))


if __name__ == "__main__":
    unittest.main()
