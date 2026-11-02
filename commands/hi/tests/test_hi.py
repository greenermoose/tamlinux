import os
import pathlib
import subprocess
import tempfile
import unittest


class TestHiCommand(unittest.TestCase):
    def setUp(self):
        self.cmd_path = pathlib.Path(__file__).parents[1] / "hi"

    def test_syntax(self):
        result = subprocess.run(["sh", "-n", str(self.cmd_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Shell syntax error: {result.stderr}")

    def test_forwards_to_tam_hi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            log_file = tmp_path / "tam_called.log"
            mock_tam = tmp_path / "tam"
            mock_tam.write_text(f"""#!/bin/sh
echo "$@" >> "{log_file}"
exit 0
""")
            mock_tam.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

            result = subprocess.run([str(self.cmd_path), "--pipe"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(log_file.exists())
            self.assertEqual(log_file.read_text().strip(), "hi --pipe")

    def test_missing_tam_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            env = os.environ.copy()
            # PATH without tam
            env["PATH"] = empty_dir

            result = subprocess.run([str(self.cmd_path)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("not found on PATH", result.stderr)


if __name__ == "__main__":
    unittest.main()
