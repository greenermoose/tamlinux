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
            self.assertIn("packaged macro runner is unavailable", result.stderr)
            self.assertEqual(runner.read_text(), "working runner")
            self.assertEqual(bindings.read_text(), "existing bindings")
            self.assertTrue(record.exists())

    def test_uninstall_syncs_packaged_runner_before_removing_trial(self):
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
            bindings.write_text("old trial bindings")
            data = home / ".config/tamlinux/macros.json"
            data.write_text("saved macros")
            package = home / ".local/bin/tam-macro"
            package.parent.mkdir(parents=True)
            package.write_text('#!/bin/sh\nprintf "%s" "$HOME/.local/bin/tam-macro" > "$TAMLINUX_HYPR_MACROS_FILE"\n')
            package.chmod(0o755)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            (fake_bin / "pkill").write_text("#!/bin/sh\nexit 0\n")
            (fake_bin / "pkill").chmod(0o755)
            env = {**os.environ, "HOME": tmp, "XDG_CONFIG_HOME": str(home / ".config"),
                   "XDG_STATE_HOME": str(home / ".local/state"),
                   "TAMLINUX_HYPR_MACROS_FILE": str(bindings),
                   "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"]}
            env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
            env.pop("TAMLINUX_BIN", None)
            result = subprocess.run([str(SCRIPT), "uninstall"], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(bindings.read_text(), str(package))
            self.assertEqual(data.read_text(), "saved macros")
            self.assertFalse(runner.exists())
            self.assertFalse(record.exists())

    def test_failed_sync_or_stale_reference_keeps_trial(self):
        for content in ("exit 1", 'printf "%s" "$HOME/.local/dev/bin/tam-macro" > "$TAMLINUX_HYPR_MACROS_FILE"'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
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
                bindings.write_text("old bindings")
                package = home / ".local/bin/tam-macro"
                package.parent.mkdir(parents=True)
                package.write_text("#!/bin/sh\n" + content + "\n")
                package.chmod(0o755)
                env = {**os.environ, "HOME": tmp, "XDG_STATE_HOME": str(home / ".local/state"),
                       "TAMLINUX_HYPR_MACROS_FILE": str(bindings)}
                env.pop("TAMLINUX_BIN", None)
                result = subprocess.run([str(SCRIPT), "uninstall"], env=env,
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("trial retained", result.stderr)
                self.assertTrue(runner.exists())
                self.assertTrue(record.exists())


if __name__ == "__main__":
    unittest.main()
