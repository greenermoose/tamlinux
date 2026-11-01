import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "shell/services/keybindings/dev-trial"


class TrialHandoverTest(unittest.TestCase):
    def test_uninstall_preserves_trial_when_macro_bindings_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            state = home / ".local/state/tamlinux/dev-trials"
            state.mkdir(parents=True)
            record = state / "keybinding-explorer.json"
            record.write_text("{}")
            runner = home / ".local/dev/bin/tam-macro"
            runner.parent.mkdir(parents=True)
            runner.write_text("working runner")
            bindings = home / ".config/tamlinux/hypr/macros.lua"
            bindings.parent.mkdir(parents=True)
            bindings.write_text("existing bindings")
            env = {**os.environ, "HOME": tmp, "XDG_CONFIG_HOME": str(home / ".config"),
                   "XDG_STATE_HOME": str(home / ".local/state")}
            env.pop("TAMLINUX_HYPR_MACROS_FILE", None)
            result = subprocess.run([str(SCRIPT), "uninstall"], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("packaged handover", result.stderr)
            self.assertEqual(runner.read_text(), "working runner")
            self.assertEqual(bindings.read_text(), "existing bindings")
            self.assertTrue(record.exists())


if __name__ == "__main__":
    unittest.main()
