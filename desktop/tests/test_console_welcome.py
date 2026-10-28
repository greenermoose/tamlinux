import importlib.util
import os
import pathlib
import pty
import subprocess
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "console_welcome", pathlib.Path(__file__).parents[1] / "session/console-welcome.py"
)
welcome = importlib.util.module_from_spec(spec)
spec.loader.exec_module(welcome)


class ConsoleWelcomeTest(unittest.TestCase):
    def test_selected_identity_and_generic_fallback(self):
        selected = welcome.render("Blue Sparkler", "0.5.5")
        self.assertIn("Cultivar:  Blue Sparkler 0.5.5", selected)
        self.assertNotIn("Cultivar:", welcome.render())
        self.assertTrue(selected.isascii())
        with self.assertRaises(ValueError):
            welcome.render("Blue Sparkler", None)

    def test_rejects_agetty_escapes_and_control_characters(self):
        for bad in ("Blue\\n", "Blue\nSparkler", "\x1b[2J", "", "X" * 81):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                welcome.render(bad, "0.5.5")

    def test_agetty_expands_host_and_kernel(self):
        with tempfile.TemporaryDirectory() as temp:
            issue = pathlib.Path(temp) / "welcome.issue"
            issue.write_text(welcome.render("Blue Sparkler", "0.5.5"))
            master, slave = pty.openpty()
            try:
                subprocess.run(
                    ["agetty", "--show-issue", "--issue-file", str(issue)],
                    stdin=slave, stdout=slave, stderr=slave, check=True,
                )
                result = os.read(master, 8192).decode()
            finally:
                os.close(master)
                os.close(slave)
        self.assertIn("Welcome to Tamlinux!", result)
        self.assertIn("       /\\\r\n      /\\/\\\r\n     ///\\\\\\       Welcome to Tamlinux!", result)
        self.assertIn("Cultivar:  Blue Sparkler 0.5.5", result)
        self.assertIn("Kernel:    " + os.uname().release, result)
        self.assertNotIn("\\S{PRETTY_NAME}", result)


if __name__ == "__main__":
    unittest.main()
