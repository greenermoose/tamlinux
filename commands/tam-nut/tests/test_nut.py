from pathlib import Path
import subprocess
import unittest

CLI = Path(__file__).resolve().parents[1] / "tam-nut"


class BootstrapTests(unittest.TestCase):
    def test_first_command_explains_hardware_and_network_steps(self):
        result = subprocess.run(["bash", str(CLI)], capture_output=True, text=True, check=True)
        self.assertIn("/tam-nut inspect", result.stdout)
        self.assertIn("iwctl", result.stdout)

    def test_install_is_not_an_implicit_side_effect(self):
        result = subprocess.run(["bash", str(CLI), "install", "/dev/not-a-device"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown command", result.stderr)


if __name__ == "__main__":
    unittest.main()
