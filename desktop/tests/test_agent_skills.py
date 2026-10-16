import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "skills"
spec = importlib.util.spec_from_file_location("agent_skills", SOURCE / "manage.py")
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)


class AgentSkills(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.data = self.home / "custom data"
        self.store = self.base / "immutable-skills"
        shutil.copytree(SOURCE, self.store, ignore=shutil.ignore_patterns("__pycache__"))
        (self.data / "tamlinux").mkdir(parents=True)
        (self.data / "tamlinux/skills").symlink_to(self.store)

    def install(self, managed=skills.DIRECTORIES):
        with contextlib.redirect_stdout(io.StringIO()):
            skills.install(self.home, self.data, managed)

    def issues(self):
        return skills.inspect(self.home, self.data, self.store)

    def test_fresh_install_custom_xdg_and_idempotence(self):
        self.assertTrue(self.issues())
        self.install()
        before = [(self.home / d / "tamlinux").lstat().st_ino for d in skills.DIRECTORIES]
        self.install()
        self.assertFalse(self.issues())
        self.assertEqual(before, [(self.home / d / "tamlinux").lstat().st_ino for d in skills.DIRECTORIES])

    def test_inherited_dangling_links_removed_and_guard_rejects_reappearance(self):
        for directory in skills.DIRECTORIES:
            root = self.home / directory
            root.mkdir(parents=True)
            for name in ("omarchy", "diagnose-crash", "other-inherited"):
                (root / name).symlink_to(f"/usr/share/omarchy/missing/skills/{name}")
        self.install()
        self.assertFalse(self.issues())
        planted = self.home / ".codex/skills/omarchy"
        planted.symlink_to("/usr/share/omarchy/missing")
        self.assertTrue(any("Inherited agent skill" in issue for issue in self.issues()))
        self.install()
        self.assertFalse(planted.is_symlink())
        self.assertFalse(self.issues())

    def test_personal_file_directory_and_foreign_link_preserved_before_any_changes(self):
        for kind in ("file", "directory", "link"):
            with self.subTest(kind=kind):
                entry = self.home / ".hermes/skills/diagnose-crash"
                entry.parent.mkdir(parents=True, exist_ok=True)
                if kind == "file":
                    entry.write_text("personal")
                elif kind == "directory":
                    entry.mkdir()
                else:
                    entry.symlink_to(self.base / "personal")
                with self.assertRaisesRegex(ValueError, "Preserving personal"):
                    self.install()
                self.assertFalse((self.home / ".agents/skills").exists())
                if entry.is_dir():
                    entry.rmdir()
                else:
                    entry.unlink()

    def test_similar_prefix_is_personal(self):
        entry = self.home / ".agents/skills/diagnose-crash"
        entry.parent.mkdir(parents=True)
        entry.symlink_to("/usr/share/omarchy-personal/diagnose-crash")
        with self.assertRaises(ValueError):
            self.install()
        self.assertEqual(str(entry.readlink()), "/usr/share/omarchy-personal/diagnose-crash")

    def test_shared_whole_directory_manager(self):
        shared = self.base / "personal skill collection"
        shared.mkdir()
        for agent in (".agents", ".claude"):
            (self.home / agent).mkdir()
            (self.home / agent / "skills").symlink_to(shared)
        for name in skills.SKILLS:
            (shared / name).symlink_to(self.data / "tamlinux/skills" / name)
        managed = skills.DIRECTORIES[2:]
        self.install(managed)
        self.assertFalse(self.issues())
        self.assertTrue((self.home / ".agents/skills").is_symlink())

    def test_missing_whole_directory_link_fails_before_cleanup(self):
        root = self.home / ".agents/skills"
        root.mkdir(parents=True)
        (root / "omarchy").symlink_to("/usr/share/omarchy/missing")
        with self.assertRaisesRegex(ValueError, "Whole-directory manager"):
            self.install(skills.DIRECTORIES[1:])
        self.assertTrue((root / "omarchy").is_symlink())

    def test_personal_omarchy_name_fails_without_removing_it(self):
        root = self.home / ".codex/skills"
        root.mkdir(parents=True)
        (root / "omarchy").mkdir()
        with self.assertRaisesRegex(ValueError, "personal entry named omarchy"):
            self.install()
        self.assertTrue((root / "omarchy").is_dir())

    def test_removed_generation_and_wrong_package_detected(self):
        self.install()
        alternate = self.base / "different-skills"
        shutil.copytree(self.store, alternate)
        self.assertTrue(skills.inspect(self.home, self.data, alternate))
        (self.data / "tamlinux/skills").unlink()
        self.assertTrue(self.issues())
        with contextlib.redirect_stdout(io.StringIO()):
            skills.uninstall(self.home, self.data, skills.DIRECTORIES)
        self.assertFalse((self.home / ".codex/skills/tamlinux").is_symlink())

    def test_non_directory_ancestor_preserved(self):
        (self.home / ".pi").write_text("personal")
        with self.assertRaisesRegex(ValueError, "non-directory"):
            self.install()
        self.assertFalse((self.home / ".agents/skills").exists())

    def test_symlink_cycle_preserved(self):
        root = self.home / ".codex/skills"
        root.mkdir(parents=True)
        (root / "tamlinux").symlink_to("tamlinux")
        with self.assertRaisesRegex(ValueError, "personal skill"):
            self.install()

    def test_corrupt_skill_payload_fails(self):
        (self.store / "diagnose-crash/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "selected skill data"):
            self.install()
        self.assertTrue(self.issues())

    def test_cli_rejects_wrong_selected_store_before_changes(self):
        result = subprocess.run(["python3", "-I", str(SOURCE / "manage.py"),
            "--install", "--home", str(self.home), "--data-home", str(self.data),
            "--store", str(self.base / "wrong-store")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("selected package", result.stderr)
        self.assertFalse((self.home / ".agents").exists())

    def test_crash_action_reads_delivered_skill_and_stops_if_missing(self):
        command = SOURCE.parents[1] / "commands/tam-agent-crash/tam-agent-crash"
        binaries = self.base / "bin"
        binaries.mkdir()
        (binaries / "coredumpctl").write_text("#!/bin/sh\nexit 0\n")
        (binaries / "tam-agent").write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        for binary in binaries.iterdir():
            binary.chmod(0o755)
        env = os.environ | {"HOME": str(self.home), "XDG_DATA_HOME": str(self.data),
            "PATH": str(binaries) + os.pathsep + os.environ["PATH"]}
        result = subprocess.run(["bash", str(command), "123", "test-process"],
            env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.data / "tamlinux/skills/diagnose-crash/SKILL.md"), result.stdout)
        (self.store / "diagnose-crash/SKILL.md").unlink()
        result = subprocess.run(["bash", str(command), "123"], env=env,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Install the selected crash-diagnosis skill", result.stderr)


if __name__ == "__main__":
    unittest.main()
