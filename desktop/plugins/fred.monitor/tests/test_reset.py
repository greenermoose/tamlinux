import json
import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


PLUGIN = pathlib.Path(__file__).resolve().parents[1]
RESET = PLUGIN / "fred-monitor-reset"

# A stand-in for Tamlinux's host directory. Like the real backend, it imports
# its sibling module, so it only runs if that directory is on sys.path.
COMMANDS = 'MODESET = "Modesetting {} with {}Hz"\n'
BACKEND = textwrap.dedent('''
    import json
    import os
    import sys

    import compositor_commands

    MONITOR = {
        "name": "DP-2", "width": 1920, "height": 1080, "refreshRate": 60.0,
        "x": 0, "y": 288, "scale": 1.25, "dpmsStatus": True, "disabled": False,
        "availableModes": ["1920x1080@60.00Hz", "1920x1080@59.94Hz"],
    }

    def main(argv):
        state = os.environ["FAKE_STATE"]
        operation = argv[1]
        if operation in ("monitors", "monitors-all"):
            print(json.dumps([MONITOR]))
        elif operation == "monitor-rule":
            with open(state, "a") as handle:
                handle.write(json.dumps(argv[2:]) + "\\n")
        elif operation == "rollinglog":
            if os.path.exists(state):
                with open(state) as handle:
                    for line in handle:
                        rule = json.loads(line)
                        print(compositor_commands.MODESET.format(rule[0], rule[1]))
        else:
            return 2
        return 0

    if __name__ == "__main__":
        raise SystemExit(main(sys.argv))
''')


class ResetTests(unittest.TestCase):
    def run_reset(self, host, state):
        env = {
            "PATH": "/usr/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
            "TAMLINUX_COMPOSITOR_COMMANDS": str(host),
            "FAKE_STATE": str(state),
        }
        return subprocess.run(
            ["/usr/bin/bash", str(RESET), "DP-2"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def test_reset_imports_the_backend_and_retrains_then_restores(self):
        with tempfile.TemporaryDirectory() as temp:
            host = pathlib.Path(temp) / "host"
            host.mkdir()
            (host / "compositor_commands.py").write_text(COMMANDS)
            (host / "hyprland_backend.py").write_text(BACKEND)
            state = pathlib.Path(temp) / "rules"
            result = self.run_reset(host, state)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rules = [json.loads(line) for line in state.read_text().splitlines()]
            self.assertEqual(rules, [
                ["DP-2", "1920x1080@59.94", "0x288", "1.25"],
                ["DP-2", "1920x1080@60.00", "0x288", "1.25"],
            ])
            self.assertFalse((host / "__pycache__").exists())

    def test_backend_failure_is_not_reported_as_a_disconnected_monitor(self):
        with tempfile.TemporaryDirectory() as temp:
            host = pathlib.Path(temp) / "host"
            host.mkdir()
            (host / "compositor_commands.py").write_text("raise ImportError\n")
            (host / "hyprland_backend.py").write_text(BACKEND)
            result = self.run_reset(host, pathlib.Path(temp) / "rules")
            self.assertEqual(result.returncode, 1)
            self.assertIn("cannot read monitors", result.stderr)
            self.assertNotIn("not connected", result.stderr)


if __name__ == "__main__":
    unittest.main()
