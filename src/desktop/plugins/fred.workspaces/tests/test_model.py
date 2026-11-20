import json
import shutil
import subprocess
import unittest
from pathlib import Path


MODEL = Path(__file__).resolve().parents[1] / "Model.js"


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ReconcileOwnerTests(unittest.TestCase):
    def owner(self, previous, current, bar):
        script = ("const M=require(process.argv[1]);"
                  "process.stdout.write(JSON.stringify(M.reconcileOwner(%s,%s,%s)));"
                  % (json.dumps(previous), json.dumps(current), json.dumps(bar)))
        result = subprocess.run(["node", "-e", script, str(MODEL)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def owners(self, previous, current):
        return [bar for bar in current if self.owner(previous, current, bar)]

    def test_exactly_one_bar_owns_each_change(self):
        three = ["DP-1", "DP-2", "HDMI-A-1"]
        # The HP drops out (VT switch) and comes back: the Dell's bar owns both.
        self.assertEqual(self.owners(three, ["DP-1", "DP-2"]), ["DP-1"])
        self.assertEqual(self.owners(["DP-1", "DP-2"], three), ["DP-1"])

    def test_a_returning_output_never_owns_through_its_new_bar(self):
        # The Dell (first by name) returns: its new bar must not be the owner,
        # or nobody reconciles (new bars skip their first change).
        self.assertFalse(self.owner(["DP-2", "HDMI-A-1"], ["DP-1", "DP-2", "HDMI-A-1"], "DP-1"))
        self.assertEqual(self.owners(["DP-2", "HDMI-A-1"], ["DP-1", "DP-2", "HDMI-A-1"]), ["DP-2"])

    def test_no_surviving_output_falls_back_to_the_first_current(self):
        self.assertEqual(self.owners(["DP-3"], ["HDMI-A-1", "DP-2"]), ["DP-2"])
        self.assertEqual(self.owners([], ["DP-2", "DP-1"]), ["DP-1"])

    def test_bars_without_a_monitor_and_bad_input_never_own(self):
        self.assertFalse(self.owner(["DP-1"], ["DP-1"], ""))
        self.assertFalse(self.owner(["DP-1"], ["DP-1"], None))
        self.assertFalse(self.owner(["DP-1"], None, "DP-1"))
        self.assertFalse(self.owner(["DP-1"], [], "DP-1"))
        self.assertTrue(self.owner(None, ["DP-1", 7, ""], "DP-1"))


if __name__ == "__main__":
    unittest.main()
