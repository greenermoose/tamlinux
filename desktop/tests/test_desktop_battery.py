#!/usr/bin/env python3
"""Unit tests for DesktopTestRunner and TelemetryLogger."""

import json
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP))

loader = importlib.machinery.SourceFileLoader("test_battery", str(DESKTOP / "test-battery"))
spec = importlib.util.spec_from_loader("test_battery", loader)
tb = importlib.util.module_from_spec(spec)
sys.modules["test_battery"] = tb
loader.exec_module(tb)
DesktopTestRunner = tb.DesktopTestRunner
TelemetryLogger = tb.TelemetryLogger


class TestDesktopTestBattery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_telemetry_logger_lifecycle(self):
        logger = TelemetryLogger(self.out_dir)
        logger.log_event("test_step", step=1, name="Init")
        logger.record_assertion("Phase 0", "Baseline captured", True, "Details here")
        logger.record_assertion("Phase 1", "Bar present", False, "Missing layer")
        logger.write_summary(12.34, aborted_reason=None, human_notes="All looks smooth")
        logger.close()

        self.assertTrue(logger.events_path.exists())
        self.assertTrue(logger.summary_path.exists())

        events = [json.loads(line) for line in logger.events_path.read_text().splitlines() if line]
        self.assertEqual(events[0]["kind"], "test_step")
        self.assertEqual(events[1]["kind"], "assertion")
        self.assertEqual(events[1]["name"], "Baseline captured")

        summary_text = logger.summary_path.read_text()
        self.assertIn("# Tamlinux Desktop Test Battery — Run Summary", summary_text)
        self.assertIn("1/2 assertions passed", summary_text)
        self.assertIn("All looks smooth", summary_text)

    def test_runner_pacing_calculations(self):
        runner_1x = DesktopTestRunner(speed=1.0, output_dir=self.out_dir, dry_run=True)
        self.assertAlmostEqual(runner_1x.step_pace(), 0.10, places=2)
        self.assertAlmostEqual(runner_1x.ws_pace(), 0.50, places=2)

        runner_2x = DesktopTestRunner(speed=2.0, output_dir=self.out_dir, dry_run=True)
        self.assertAlmostEqual(runner_2x.step_pace(), 0.05, places=2)
        self.assertAlmostEqual(runner_2x.ws_pace(), 0.25, places=2)

    def test_runner_dry_run_execution(self):
        runner = DesktopTestRunner(
            speed=2.0,
            output_dir=self.out_dir,
            staging_workspace=10,
            watch=False,
            dry_run=True,
        )
        ok = runner.run(phases=[0, 1, 2, 3, 4, 5, 6])
        self.assertTrue(ok)
        self.assertTrue(runner.telemetry.summary_path.exists())
        summary = runner.telemetry.summary_path.read_text()
        self.assertIn("PASS", summary)


if __name__ == "__main__":
    unittest.main()
