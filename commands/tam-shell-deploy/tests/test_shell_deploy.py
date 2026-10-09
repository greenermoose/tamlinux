"""Exercise the deployment boundary without activating Fred's desktop."""
import importlib.machinery
import importlib.util
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

CLI = Path(__file__).resolve().parents[1] / "tam-shell-deploy"
loader = importlib.machinery.SourceFileLoader("shell_deploy", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
deploy = importlib.util.module_from_spec(spec)
loader.exec_module(deploy)


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.source / "shell").write_text("first")
        self.git("add", ".")
        self.git("commit", "-qm", "first")
        self.old = self.git("rev-parse", "HEAD")
        (self.source / "shell").write_text("second")
        self.git("commit", "-qam", "second")
        self.new = self.git("rev-parse", "HEAD")
        self.config = self.root / "config"
        (self.config / "system").mkdir(parents=True)
        self.lock_doc = {"nodes": {"root": {"inputs": {"tamlinux": "tamlinux"}},
                                   "tamlinux": {"locked": {"rev": self.old}}}}
        (self.config / "flake.lock").write_text(json.dumps(self.lock_doc))
        (self.config / "system/bom.json").write_text('{"components":{}}')
        self.env = patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": str(self.config),
            "TAMLINUX_SOURCE_REPO": str(self.source), "XDG_DATA_HOME": str(self.root / "data"),
            "XDG_STATE_HOME": str(self.root / "state")})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = deploy.Deployment()
        self.app.revision_file.parent.mkdir(parents=True)
        self.app.revision_file.write_text(self.old)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], text=True).strip()

    def test_rejects_unmerged_branch_and_option_ref(self):
        self.git("checkout", "-qb", "unfinished")
        (self.source / "shell").write_text("unfinished")
        self.git("commit", "-qam", "unfinished")
        with self.assertRaises(subprocess.CalledProcessError):
            self.app.commit("unfinished")
        with self.assertRaises(subprocess.CalledProcessError):
            self.app.commit("--help")
        self.assertEqual(self.app.commit("main"), self.new)

    def test_test_override_leaves_lock_unchanged_and_records_rollback(self):
        before = self.app.lock.read_bytes()
        with patch.object(self.app, "preflight"), patch.object(self.app, "generation", return_value="previous"), \
             patch.object(self.app, "status"), patch.object(self.app, "switch") as switch:
            self.app.test(self.new)
        switch.assert_called_once_with(self.new, test=True)
        self.assertEqual(self.app.lock.read_bytes(), before)
        self.assertEqual(self.app.read_state(), {"previousGeneration": "previous", "testedCommit": self.new})

    def test_switch_uses_no_write_lock_for_test_only(self):
        self.app.revision_file.write_text(self.new)
        with patch.object(deploy, "command", return_value="pong") as command:
            self.app.switch(self.new, True)
        args = command.call_args_list[0].args
        self.assertIn("--no-write-lock-file", args)
        self.assertIn(self.app.url(self.new), args)
        with patch.object(deploy, "command", return_value="pong") as command:
            self.app.switch(self.new, False)
        self.assertNotIn("--override-input", command.call_args_list[0].args)

    def test_failed_switch_keeps_rollback_and_restores_pin(self):
        before = self.app.lock.read_bytes()
        def command(*args, **kwargs):
            self.app.lock.write_text('{"modified":true}')
        with patch.object(self.app, "preflight"), patch.object(self.app, "generation", return_value="previous"), \
             patch.object(self.app, "commit", return_value=self.new), patch.object(deploy, "command", side_effect=command), \
             patch.object(self.app, "switch", side_effect=deploy.DeploymentError("restart failed")):
            # A malformed pin from the mock also exercises failure restoration.
            with self.assertRaises(KeyError):
                self.app.run()
        self.assertEqual(self.app.lock.read_bytes(), before)
        self.assertEqual(self.app.read_state()["previousGeneration"], "previous")

    def test_back_rejects_removed_or_non_store_generation(self):
        self.app.save_state({"previousGeneration": str(self.root)})
        with self.assertRaises(deploy.DeploymentError):
            self.app.back()

    def test_back_invalidates_test_candidate_and_preserves_return_path(self):
        self.app.save_state({"previousGeneration": "/nix/store/fixture-generation", "testedCommit": self.new})
        with patch.object(Path, "is_file", return_value=True), \
             patch.object(self.app, "generation", return_value="current"), patch.object(self.app, "status"), \
             patch.object(self.app, "wait_ready") as ready, \
             patch.object(deploy, "command") as command:
            self.app.back()
        self.assertEqual(command.call_args_list[0].args, ("/nix/store/fixture-generation/activate",))
        self.assertEqual(self.app.read_state(), {"previousGeneration": "current"})
        ready.assert_called_once()

    def test_run_pins_the_active_test_and_records_that_generation(self):
        self.app.save_state({"testedCommit": self.old})
        with patch.object(self.app, "commit", return_value=self.old) as commit, \
             patch.object(self.app, "preflight"), patch.object(self.app, "generation", return_value="generation"), \
             patch.object(self.app, "switch") as switch, patch.object(self.app, "status"), \
             patch.object(deploy, "command", return_value=""), \
             patch.object(deploy.subprocess, "run", return_value=SimpleNamespace(returncode=1)), \
             patch.dict(os.environ, {"CODEX_THREAD_ID": "", "CLAUDECODE": ""}):
            self.app.run()
        commit.assert_called_once_with(self.old)
        switch.assert_called_once_with(self.old, test=False)
        bom = json.loads((self.config / "system/bom.json").read_text())
        self.assertEqual(bom["components"]["shell"], {"commit": self.old, "generation": "generation"})
        self.assertNotIn("testedCommit", self.app.read_state())

    def test_run_rejects_stale_test_before_mutation(self):
        self.app.save_state({"testedCommit": self.new})
        before = self.app.lock.read_bytes(), self.app.state_file.read_bytes()
        with patch.object(self.app, "commit") as commit, patch.object(self.app, "preflight") as preflight, \
             patch.object(deploy, "command") as command:
            with self.assertRaisesRegex(deploy.DeploymentError, "restore Test before Run"):
                self.app.run()
        commit.assert_not_called()
        preflight.assert_not_called()
        command.assert_not_called()
        self.assertEqual((self.app.lock.read_bytes(), self.app.state_file.read_bytes()), before)

    def test_status_reports_stale_test_and_fails(self):
        self.app.save_state({"testedCommit": self.new})
        output = io.StringIO()
        with patch.object(self.app, "generation", return_value="generation"), contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(deploy.DeploymentError, "not deployed"):
                self.app.status()
        self.assertIn("test override: off", output.getvalue())
        self.assertIn("saved Test candidate: " + self.new, output.getvalue())

    def test_status_accepts_matching_test_and_normal_run(self):
        with patch.object(self.app, "generation", return_value="generation"), contextlib.redirect_stdout(io.StringIO()):
            self.app.status()
            self.app.save_state({"testedCommit": self.old})
            self.app.status()


class ConfigurationLookupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def make_config(self, name):
        path = self.home / "Code/tamlinux" / name / "config/tamlinux/plugins"
        path.mkdir(parents=True)
        return path.parents[2]

    def test_environment_overrides_discovery(self):
        self.make_config("one")
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": "/elsewhere"}):
            self.assertEqual(deploy.find_config_repo(self.home), Path("/elsewhere"))

    def test_single_checkout_with_plugins_is_found(self):
        config = self.make_config("workstation")
        (self.home / "Code/tamlinux/product").mkdir()
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": ""}):
            self.assertEqual(deploy.find_config_repo(self.home), config)

    def test_missing_or_ambiguous_checkout_is_an_error(self):
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": ""}):
            with self.assertRaises(deploy.DeploymentError):
                deploy.find_config_repo(self.home)
            self.make_config("one")
            self.make_config("two")
            with self.assertRaises(deploy.DeploymentError):
                deploy.find_config_repo(self.home)

    def test_home_configuration_defaults_to_user(self):
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": str(self.home),
                                     "TAMLINUX_HOME_CONFIGURATION": ""}), \
             patch.object(deploy.getpass, "getuser", return_value="alice"):
            self.assertEqual(deploy.Deployment().home_configuration, "alice")
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": str(self.home),
                                     "TAMLINUX_HOME_CONFIGURATION": "alice@laptop"}):
            self.assertEqual(deploy.Deployment().home_configuration, "alice@laptop")


if __name__ == "__main__":
    unittest.main()
