import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CLI = Path(__file__).resolve().parents[1] / "tam-deploy"
loader = importlib.machinery.SourceFileLoader("tam_deploy", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
deploy = importlib.util.module_from_spec(spec)
loader.exec_module(deploy)


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True,
                                   stderr=subprocess.DEVNULL).strip()


class Fixture(unittest.TestCase):
    """A workspace with tamlinux and tamlinux-packages clones of bare origins."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.tamlinux_main = self.commit_repo("tamlinux", "shell", "first")
        self.tamlinux_new = self.commit("tamlinux", "shell", "second")
        self.push("tamlinux", self.tamlinux_new, "test", "develop")
        self.packages_main = self.commit_repo("tamlinux-packages", "flake.lock", self.assembly(self.tamlinux_main))
        self.packages_new = self.commit("tamlinux-packages", "flake.lock", self.assembly(self.tamlinux_new))
        self.push("tamlinux-packages", self.packages_new, "test", "develop")
        self.config = self.workspace / "config"
        (self.config / "system").mkdir(parents=True)
        self.write_lock(self.packages_main, original={"type": "github", "owner": "greenermoose",
                                                      "repo": "tamlinux-packages"})
        (self.config / "system/bom.json").write_text('{"components":{}}')
        self.env = patch.dict(os.environ, {
            "TAMLINUX_CONFIG_REPO": str(self.config), "TAMLINUX_WORKSPACE": str(self.workspace),
            "TAMLINUX_HOME_CONFIGURATION": "alex", "HOME": str(self.root / "home"),
            "XDG_DATA_HOME": str(self.root / "data"), "XDG_STATE_HOME": str(self.root / "state"),
            "XDG_CONFIG_HOME": str(self.root / "xdg-config"), "CLAUDECODE": "", "CODEX_THREAD_ID": ""})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = deploy.Deployment()
        self.app.revision_file.parent.mkdir(parents=True, exist_ok=True)
        self.app.revision_file.write_text(self.tamlinux_main + "\n")

    def commit_repo(self, name, path, text):
        origin = self.root / "origins" / f"{name}.git"
        origin.mkdir(parents=True)
        git(origin, "init", "-q", "--bare", "-b", "main")
        clone = self.workspace / name
        clone.mkdir(parents=True)
        git(clone, "init", "-q", "-b", "main")
        git(clone, "config", "user.name", "Fixture")
        git(clone, "config", "user.email", "fixture@example.invalid")
        git(clone, "remote", "add", "origin", str(origin))
        revision = self.commit(name, path, text)
        self.push(name, revision, "main", "test", "develop")
        return revision

    def commit(self, name, path, text):
        clone = self.workspace / name
        (clone / path).write_text(text)
        git(clone, "add", path)
        git(clone, "commit", "-qm", text[:40])
        return git(clone, "rev-parse", "HEAD")

    def push(self, name, revision, *branches):
        clone = self.workspace / name
        for branch in branches:
            git(clone, "push", "-q", "-f", "origin", f"{revision}:refs/heads/{branch}")
        git(clone, "fetch", "-q", "origin")

    def assembly(self, tamlinux_rev):
        return json.dumps({"nodes": {
            "root": {"inputs": {"tamlinux": "tamlinux", "nixpkgs": "nixpkgs"}},
            "tamlinux": {"locked": {"type": "github", "owner": "greenermoose", "repo": "tamlinux",
                                    "rev": tamlinux_rev}},
            "nixpkgs": {"locked": {"type": "github", "owner": "nixos", "repo": "nixpkgs", "rev": "n" * 40}},
        }})

    def write_lock(self, revision, original):
        (self.config / "flake.lock").write_text(json.dumps({"nodes": {
            "root": {"inputs": {"tamlinux-packages": "tamlinux-packages"}},
            "tamlinux-packages": {"locked": {"type": "github", "owner": "greenermoose",
                                             "repo": "tamlinux-packages", "rev": revision},
                                  "original": original}}}))

    def origin_head(self, name, branch):
        return git(self.root / "origins" / f"{name}.git", "rev-parse", branch)


class TestStage(Fixture):
    real_command = staticmethod(deploy.command)

    def passthrough(self, *args, **kwargs):
        if args[0] == "git":
            return self.real_command(*args, **kwargs)
        self.activations = getattr(self, "activations", []) + [args]
        return ""

    def deploy_test(self, **kwargs):
        with patch.object(self.app, "preflight"), patch.object(self.app, "activate"), \
             patch.object(self.app, "verify", return_value=[]), patch.object(self.app, "record") as record, \
             patch.object(self.app, "generation", return_value="/nix/store/old-generation"), \
             patch.object(self.app, "status"), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})) as pin:
            self.app.test(**kwargs)
        return pin, record

    def test_defaults_to_test_head_and_records_the_pin(self):
        pin, record = self.deploy_test()
        pin.assert_called_once_with(self.packages_new)
        record.assert_called_once()
        self.assertIn(self.packages_new[:12], record.call_args.args[0])
        state = self.app.read_state()
        self.assertEqual(state["stage"], "test")
        self.assertEqual(state["packages"], self.packages_new)
        self.assertEqual(state["components"], {"tamlinux": self.tamlinux_new})
        self.assertEqual(state["previousPin"], self.packages_main)
        bom = json.loads((self.config / "system/bom.json").read_text())
        self.assertEqual(bom["components"]["tamlinux"]["stage"], "test")

    def test_staged_lock_keeps_the_running_assembly_as_rollback_pin(self):
        self.write_lock(self.packages_new, {})
        self.app.save_state({"stage": "run", "packages": self.packages_main,
                             "generation": "/nix/store/old-generation"})
        self.deploy_test()
        self.assertEqual(self.app.read_state()["previousPin"], self.packages_main)

    def test_stale_record_does_not_override_the_matching_active_lock(self):
        self.app.save_state({"packages": self.packages_new,
                             "generation": "/nix/store/stale-generation"})
        self.deploy_test()
        self.assertEqual(self.app.read_state()["previousPin"], self.packages_main)

    def test_unknown_active_assembly_refuses_activation(self):
        self.write_lock(self.packages_new, {})
        with patch.object(self.app, "preflight"), \
             patch.object(self.app, "generation", return_value="/nix/store/old-generation"), \
             patch.object(self.app, "pin") as pin, patch.object(self.app, "activate") as activate:
            with self.assertRaisesRegex(deploy.DeploymentError, "active assembly for rollback"):
                self.app.test()
        pin.assert_not_called()
        activate.assert_not_called()

    def test_refuses_an_assembly_that_is_not_on_test(self):
        unfinished = self.commit("tamlinux-packages", "flake.lock", self.assembly(self.tamlinux_new) + " ")
        self.push("tamlinux-packages", unfinished, "develop")
        with self.assertRaisesRegex(deploy.DeploymentError, "not on test"):
            self.deploy_test(ref=unfinished)

    def test_refuses_a_component_that_is_not_on_test(self):
        unfinished = self.commit("tamlinux", "shell", "third")
        self.push("tamlinux", unfinished, "develop")
        candidate = self.commit("tamlinux-packages", "flake.lock", self.assembly(unfinished))
        self.push("tamlinux-packages", candidate, "test")
        with self.assertRaisesRegex(deploy.DeploymentError, "tamlinux .* is not on test"):
            self.deploy_test()

    def test_failed_activation_restores_lock_and_generation(self):
        before = (self.config / "flake.lock").read_bytes()
        generations = iter(["/nix/store/old-generation", "/nix/store/new-generation"])
        with patch.object(self.app, "preflight"), patch.object(self.app, "status"), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate", side_effect=deploy.DeploymentError("restart failed")), \
             patch.object(self.app, "generation", side_effect=lambda: next(generations)), \
             patch.object(deploy, "command", side_effect=self.passthrough):
            with self.assertRaises(deploy.DeploymentError):
                self.app.test()
        self.assertEqual((self.config / "flake.lock").read_bytes(), before)
        self.assertIn(("/nix/store/old-generation/activate",), self.activations)
        self.assertEqual(self.app.read_state(), {})

    def test_mismatched_install_fails_the_test(self):
        with patch.object(self.app, "preflight"), patch.object(self.app, "activate"), \
             patch.object(self.app, "status"), patch.object(self.app, "record") as record, \
             patch.object(self.app, "generation", return_value="/nix/store/old-generation"), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "verify", return_value=["shell revision x is not y"]):
            with self.assertRaisesRegex(deploy.DeploymentError, "do not match"):
                self.app.test()
        record.assert_not_called()


class RunStage(Fixture):
    def installed(self, revision, stage="test"):
        self.write_lock(revision, {})
        self.app.save_state({"stage": stage, "packages": revision,
                             "previousGeneration": "/nix/store/old", "previousPin": self.packages_main})

    def deploy_run(self, *args, problems=(), **kwargs):
        with patch.object(self.app, "verify", return_value=list(problems)), \
             patch.object(self.app, "status"), patch.object(self.app, "record"), \
             patch.object(self.app, "generation", return_value="/nix/store/new"), \
             patch.object(self.app, "install") as install:
            self.app.run(*args, **kwargs)
        return install

    def untested_assembly(self, *branches):
        product = self.commit("tamlinux", "shell", "unreleased")
        self.push("tamlinux", product, *branches)
        assembly = self.commit("tamlinux-packages", "flake.lock", self.assembly(product))
        self.push("tamlinux-packages", assembly, *branches)
        return product, assembly

    # tam-deploy run (no revision)

    def test_promotes_the_installed_test_without_reinstalling(self):
        self.installed(self.packages_new)
        install = self.deploy_run()
        install.assert_not_called()
        self.assertEqual(self.origin_head("tamlinux", "main"), self.tamlinux_new)
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_new)
        self.assertEqual(self.app.read_state()["stage"], "run")

    def test_reports_an_installed_main_commit(self):
        self.installed(self.packages_main, stage="run")
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            install = self.deploy_run()
        install.assert_not_called()
        self.assertIn(f"Already running main commit {self.packages_main}", out.getvalue())
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_main)

    def test_reinstalls_when_the_installation_drifted(self):
        self.installed(self.packages_new)
        install = self.deploy_run(problems=["fred.clock resolves outside"])
        install.assert_called_once_with(self.packages_new, {"tamlinux": self.tamlinux_new}, "run")
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_new)

    # tam-deploy run <revision>

    def test_unknown_revision_is_an_error(self):
        self.installed(self.packages_new)
        with self.assertRaisesRegex(deploy.DeploymentError, "no tamlinux-packages commit matches"):
            self.deploy_run("0" * 40)

    def test_main_commit_installs_without_moving_branches(self):
        self.installed(self.packages_new)
        install = self.deploy_run(self.packages_main[:12])
        install.assert_called_once_with(self.packages_main, {"tamlinux": self.tamlinux_main}, "run")
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_main)
        self.assertEqual(self.origin_head("tamlinux-packages", "test"), self.packages_new)

    def test_test_commit_installs_and_promotes(self):
        self.installed(self.packages_main, stage="run")
        install = self.deploy_run(self.packages_new)
        install.assert_called_once_with(self.packages_new, {"tamlinux": self.tamlinux_new}, "run")
        self.assertEqual(self.origin_head("tamlinux", "main"), self.tamlinux_new)
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_new)

    def test_develop_commit_needs_untested(self):
        self.installed(self.packages_new)
        product, assembly = self.untested_assembly("develop")
        with self.assertRaisesRegex(deploy.DeploymentError, "not tested yet: .*--untested"):
            self.deploy_run(assembly)
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_main)
        with patch("sys.stderr", new_callable=io.StringIO) as err:
            install = self.deploy_run(assembly, untested=True)
        self.assertIn("warning: running untested commits", err.getvalue())
        install.assert_called_once()
        for name, revision in (("tamlinux", product), ("tamlinux-packages", assembly)):
            self.assertEqual(self.origin_head(name, "test"), revision)
            self.assertEqual(self.origin_head(name, "main"), revision)

    def test_feature_branch_commit_is_untested(self):
        self.installed(self.packages_new)
        _, assembly = self.untested_assembly("feature/try")
        with self.assertRaisesRegex(deploy.DeploymentError, r"untracked"):
            self.deploy_run(assembly)

    def test_main_is_only_fast_forwarded(self):
        self.installed(self.packages_new)
        git(self.workspace / "tamlinux", "checkout", "-q", self.tamlinux_main)
        diverged = self.commit("tamlinux", "other", "elsewhere")
        git(self.workspace / "tamlinux", "push", "-q", "-f", "origin", f"{diverged}:refs/heads/main")
        with self.assertRaisesRegex(deploy.DeploymentError, "cannot fast-forward to: tamlinux "):
            self.deploy_run()
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_main)


class Arguments(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(deploy.parse(["run"]), ("run", [], {"untested": False}))
        self.assertEqual(deploy.parse(["run", "abc", "--untested"]), ("run", ["abc"], {"untested": True}))
        self.assertEqual(deploy.parse(["run", "--untested", "abc"]), ("run", ["abc"], {"untested": True}))
        self.assertEqual(deploy.parse(["test"]), ("test", [], {}))
        self.assertIsNone(deploy.parse(["run", "a", "b"]))
        self.assertIsNone(deploy.parse(["run", "--force"]))
        self.assertIsNone(deploy.parse(["test", "--untested"]))
        self.assertIsNone(deploy.parse(["status", "x"]))


class BackAndPin(Fixture):
    def test_back_reactivates_and_restores_the_previous_pin(self):
        generation = self.root / "nix-store-sim"
        real_command = deploy.command
        self.write_lock(self.packages_new, {})
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(deploy, "command", side_effect=lambda *args, **kwargs:
                          real_command(*args, **kwargs) if args[0] == "git" else "") as command, \
             patch.object(self.app, "wait_ready"), \
             patch.object(self.app, "status"), patch.object(self.app, "record"), \
             patch.object(self.app, "generation", side_effect=["/nix/store/new-generation", "/nix/store/old-generation"]), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})) as pin:
            self.app.back()
        command.assert_any_call("/nix/store/old-generation/activate")
        pin.assert_called_once_with(self.packages_main)
        state = self.app.read_state()
        self.assertEqual(state["previousPin"], self.packages_new)
        self.assertEqual(state["previousGeneration"], "/nix/store/new-generation")
        self.assertEqual(state["generation"], "/nix/store/old-generation")
        self.assertEqual(state["components"], {"tamlinux": self.tamlinux_main})
        self.write_lock(self.packages_new, {})
        self.assertEqual(self.app.rollback_pin("/nix/store/old-generation"), self.packages_main)

    def test_back_needs_a_recorded_deployment(self):
        with self.assertRaisesRegex(deploy.DeploymentError, "no recorded previous"):
            self.app.back()

    def test_pin_keeps_the_declared_source(self):
        declared = {"type": "github", "owner": "greenermoose", "repo": "tamlinux-packages"}

        def nix_lock(*args, **kwargs):
            self.write_lock(self.packages_new, {"type": "github", "owner": "greenermoose",
                                                "repo": "tamlinux-packages", "rev": self.packages_new})
        with patch.object(deploy, "command", side_effect=nix_lock) as command:
            self.app.pin(self.packages_new)
        self.assertIn(f"github:greenermoose/tamlinux-packages/{self.packages_new}", command.call_args.args)
        lock = json.loads((self.config / "flake.lock").read_text())
        self.assertEqual(lock["nodes"]["tamlinux-packages"]["original"], declared)
        self.assertEqual(lock["nodes"]["tamlinux-packages"]["locked"]["rev"], self.packages_new)


class Verify(Fixture):
    def link(self, path, target):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)

    def install(self, shell="/nix/store/a-tamlinux-shell-0.4.1/share/tamlinux/shell",
                plugin="/nix/store/b-tamlinux-plugins-0.4.1/share/tamlinux/plugins/fred.clock",
                command="/nix/store/c-tamlinux-commands-0.4.1/bin/tam-deploy"):
        self.app.revision_file.parent.mkdir(parents=True, exist_ok=True)
        self.app.revision_file.write_text(self.tamlinux_new + "\n")
        self.link(self.app.shell_link, shell)
        self.link(self.app.plugins_dir / "fred.clock", plugin)
        self.link(self.app.bin_dir / "tam-deploy", command)
        self.link(self.app.bin_dir / "tam", "/nix/store/d-tam-0.7.0/bin/tam")

    def test_matching_install(self):
        self.install()
        self.assertEqual(self.app.verify({"tamlinux": self.tamlinux_new}), [])

    def test_reports_each_mismatch(self):
        checkout = str(self.workspace / "tamlinux")
        self.install(shell=checkout, plugin=checkout, command=checkout)
        problems = self.app.verify({"tamlinux": self.tamlinux_main})
        self.assertEqual(len(problems), 4)
        self.assertTrue(any("shell revision" in p for p in problems))
        self.assertTrue(any("fred.clock" in p for p in problems))
        self.assertTrue(any("tam-deploy" in p for p in problems))


class ConfigurationLookupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def make_config(self, name, inputs=("tamlinux-packages",)):
        path = self.home / "Code/tamlinux" / name
        path.mkdir(parents=True)
        (path / "flake.lock").write_text(json.dumps({"nodes": {"root": {"inputs": {i: i for i in inputs}}}}))
        return path

    def test_environment_overrides_discovery(self):
        self.make_config("one")
        with patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": "/elsewhere"}):
            self.assertEqual(deploy.find_config_repo(self.home), Path("/elsewhere"))

    def test_single_checkout_with_plugins_is_found(self):
        config = self.make_config("workstation")
        self.make_config("tamlinux-packages", inputs=("nixpkgs", "tamlinux"))
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


class Usage(unittest.TestCase):
    def test_rejects_unknown_commands(self):
        self.assertEqual(deploy.main(["deploy"]), 2)
        self.assertEqual(deploy.main(["test", "a", "b"]), 2)


if __name__ == "__main__":
    unittest.main()
