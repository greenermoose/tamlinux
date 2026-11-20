"""Exercise the native console entry with a private tool and version link."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class BundleActivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.source = cls.root / "source"
        shutil.copytree(SOURCE, cls.source, ignore=shutil.ignore_patterns("build"))
        cls.command = cls.root / "tam-start"
        cls.tool = cls.root / "bundle-tool"
        cls.current = cls.root / "current"
        flags = " ".join(
            f'-D{name}=\'"{path}"\''
            for name, path in (("TAM_BUNDLE_TOOL", cls.tool),
                               ("TAM_BUNDLE_CURRENT", cls.current),
                               ("TAM_START_EXECUTABLE", cls.command))
        )
        subprocess.run(["make", "--no-print-directory", "-C", str(cls.source),
                        "all", "CPPFLAGS=" + flags], capture_output=True, text=True, check=True)

    def setUp(self):
        self.command.unlink(missing_ok=True)
        shutil.copy2(self.source / "build/start", self.command)
        self.current.unlink(missing_ok=True)
        self.current.symlink_to("version/old")
        self.log = self.root / "actions"
        self.log.unlink(missing_ok=True)

    def helper(self, body):
        self.tool.write_text("#!/bin/sh\n" + body)
        self.tool.chmod(0o755)

    def test_failed_activation_keeps_the_menu_closed(self):
        self.helper("exit 4\n")
        run = subprocess.run([str(self.command)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("console remains available", run.stderr)

    def test_successful_switch_reexecutes_the_new_real_command(self):
        replacement = self.root / "replacement"
        replacement.write_text("#!/bin/sh\necho selected-new-version\n")
        replacement.chmod(0o755)
        self.helper(f"""printf '%s\\n' "$@" > "{self.log}"
ln -s version/new "{self.current}.new"
mv -Tf "{self.current}.new" "{self.current}"
mv -Tf "{replacement}" "{self.command}"
""")
        run = subprocess.run([str(self.command)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "selected-new-version\n")
        self.assertEqual(self.log.read_text(), "session-activate\n")

    def test_read_only_queries_preserve_their_entry_point(self):
        self.helper(f'touch "{self.log}"\nexit 4\n')
        run = subprocess.run([str(self.command), "--list"], text=True, capture_output=True,
                             env=dict(os.environ, START_MENU=str(SOURCE / "menu.json")))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
