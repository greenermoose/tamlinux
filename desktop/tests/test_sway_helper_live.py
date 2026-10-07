# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in IPC checks against a new private headless Sway, never the desktop.

TAMLINUX_TEST_SWAY_HELPERS=1 python3 -m unittest discover -s desktop/tests \
    -p test_sway_helper_live.py -v

Requires Sway with the headless backend. This proves IPC behavior, not physical
display retraining, persistent configuration, or existing helper integration.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

HOST = Path(__file__).resolve().parents[1] / "shell" / "host"
sys.path.insert(0, str(HOST))
import sway_helper_executor as executor


@unittest.skipUnless(os.environ.get("TAMLINUX_TEST_SWAY_HELPERS") == "1",
                     "opt-in private headless Sway IPC proof")
class PrivateSwayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="tam-sway-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.config = cls.root / "sway.conf"
        cls.config.write_text("xwayland disable\noutput HEADLESS-1 mode 1280x720\n"
                              "output HEADLESS-2 mode 1280x720 pos 1280 0\n")
        cls.log = (cls.root / "sway.log").open("wb")
        cls.addClassCleanup(cls.log.close)
        cls.process = subprocess.Popen(("/usr/bin/sway", "-c", str(cls.config)),
            stdin=subprocess.DEVNULL, stdout=cls.log, stderr=cls.log,
            env={"HOME": str(cls.root), "XDG_RUNTIME_DIR": str(cls.root),
                 "PATH": "/usr/bin", "WLR_BACKENDS": "headless",
                 "WLR_HEADLESS_OUTPUTS": "2", "WLR_LIBINPUT_NO_DEVICES": "1",
                 "WLR_RENDERER": "pixman"}, start_new_session=True)
        cls.addClassCleanup(cls.stop_sway)
        for _ in range(100):
            candidates = list(cls.root.glob("sway-ipc.*.sock"))
            if candidates:
                cls.socket_path = str(candidates[0])
                result = executor.execute("monitors-all", socket_path=cls.socket_path)
                if result.ok:
                    break
            if cls.process.poll() is not None:
                raise RuntimeError("private Sway startup failed: " +
                                   (cls.root / "sway.log").read_text(errors="replace")[-4096:])
            time.sleep(.05)
        else:
            raise RuntimeError("private Sway did not provide valid output facts")

    @classmethod
    def stop_sway(cls):
        cls.process.terminate()
        try:
            cls.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            cls.process.kill()
            cls.process.wait()

    def run_operation(self, operation, payload=None, *, live=True):
        return executor.execute(operation, payload, socket_path=self.socket_path, live=live)

    def require_success(self, operation, payload=None):
        result = self.run_operation(operation, payload)
        self.assertTrue(result.ok, repr(result))
        return result

    def setUp(self):
        self.require_success("reload")

    def test_reads_join_real_outputs_and_default_seat_focus(self):
        facts = self.require_success("monitors-all").data
        self.assertEqual({fact.name for fact in facts}, {"HEADLESS-1", "HEADLESS-2"})
        self.assertEqual(sum(fact.focused for fact in facts), 1)
        focus = self.require_success("active-workspace").data
        self.assertEqual(focus.output, next(fact.name for fact in facts if fact.focused))
        self.assertEqual(focus.name, next(fact.workspace_name for fact in facts if fact.focused))

    def test_helper_workspace_160_does_not_toggle_on_repeated_focus(self):
        self.require_success("focus-workspace", 160)
        self.require_success("focus-workspace", 160)
        self.assertEqual(self.require_success("active-workspace").data.number, 160)
        self.require_success("focus-output", "HEADLESS-2")
        self.assertEqual(self.require_success("active-workspace").data.output, "HEADLESS-2")
        self.require_success("move-workspace-fallback", [160, "HEADLESS-1"])
        focus = self.require_success("active-workspace").data
        self.assertEqual((focus.number, focus.output), (160, "HEADLESS-1"))

    def test_monitor_rule_keeps_pixels_separate_from_scaled_layout(self):
        self.require_success("monitor-rule", ["HEADLESS-2", "1600x900@60", "-1600x100", 1.25, 0])
        fact = next(fact for fact in self.require_success("monitors").data if fact.name == "HEADLESS-2")
        self.assertEqual((fact.pixel_mode.width, fact.pixel_mode.height), (1600, 900))
        self.assertEqual((fact.logical_rect.x, fact.logical_rect.y), (-1600, 100))
        self.assertEqual((fact.logical_rect.width, fact.logical_rect.height), (1280, 720))
        self.assertEqual(fact.scale, 1.25)

    def test_record_only_mutation_leaves_focus_unchanged(self):
        before = self.require_success("active-workspace").data
        result = self.run_operation("focus-workspace", 159, live=False)
        self.assertEqual(result.state, "recorded")
        self.assertFalse(result.ok)
        self.assertEqual(self.require_success("active-workspace").data, before)

    def test_disabled_output_is_retained_only_in_all_outputs(self):
        self.require_success("monitor-rule", ["HEADLESS-2", "disabled"])
        facts = self.require_success("monitors-all").data
        disabled = next(fact for fact in facts if fact.name == "HEADLESS-2")
        self.assertFalse(disabled.enabled)
        self.assertIsNone(disabled.pixel_mode)
        self.assertIsNone(disabled.workspace_number)
        self.assertEqual({fact.name for fact in self.require_success("monitors").data}, {"HEADLESS-1"})

    def test_partial_batch_failure_does_not_hide_applied_commands(self):
        result = self.run_operation("batch", [["focus-workspace", 158],
                                    ["focus-output", "MISSING-9"], ["focus-workspace", 157]])
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "command-failed")
        self.assertTrue(result.may_have_changed)
        self.assertEqual(result.outcome.succeeded_indexes, (0,))
        self.assertEqual(result.outcome.failed_indexes, (1,))
        self.assertEqual(result.outcome.unreported_indexes, (2,))
        self.assertEqual(self.require_success("active-workspace").data.number, 158)


if __name__ == "__main__":
    unittest.main()
