import importlib.machinery
import importlib.util
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
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


class ConsoleDeployment(Fixture):
    def test_console_activation_and_recovery_do_not_start_graphics(self):
        inactive = subprocess.CompletedProcess([], 3, stdout='inactive\n', stderr='')
        with patch.object(deploy.subprocess, 'run', return_value=inactive), \
             patch.object(deploy, 'command') as command, \
             patch.object(self.app, 'wait_ready') as ready:
            self.app.activate()
            command.assert_called_once_with('home-manager', 'switch', '--flake',
                                            f'{self.config}#alex')
            ready.assert_not_called()
            command.reset_mock()
            self.app.restart_if_graphical()
            command.assert_not_called()

    def test_unknown_graphical_state_fails_closed(self):
        failed = subprocess.CompletedProcess([], 1, stdout='', stderr='bus unavailable')
        with patch.object(deploy.subprocess, 'run', return_value=failed):
            with self.assertRaises(deploy.DeploymentError):
                self.app.graphical_active()

    def test_active_graphical_session_still_restarts_and_checks_shell(self):
        active = subprocess.CompletedProcess([], 0, stdout='active\n', stderr='')
        with patch.object(deploy.subprocess, 'run', return_value=active), \
             patch.object(deploy, 'command') as command, \
             patch.object(self.app, 'require_unlocked_sessions') as unlocked, \
             patch.object(self.app, 'wait_ready') as ready:
            self.app.restart_if_graphical()
            unlocked.assert_called_once_with()
            command.assert_called_once_with('tam-restart-shell')
            ready.assert_called_once_with()

    def test_locked_graphical_session_is_detected_from_an_unlocked_console(self):
        sessions = json.dumps([
            {'uid': os.getuid(), 'class': 'user', 'session': 'console'},
            {'uid': os.getuid(), 'class': 'user', 'session': 'desktop'},
            {'uid': os.getuid(), 'class': 'manager', 'session': 'manager'},
            {'uid': os.getuid() + 1, 'class': 'user', 'session': 'other'},
        ])
        def run(*args, **kwargs):
            if args[1] == 'list-sessions':
                return sessions
            return {'console': 'no', 'desktop': 'yes'}[args[2]]
        with patch.object(self.app, 'check_clean'), \
             patch.object(self.app, 'graphical_active', return_value=True), \
             patch.object(deploy, 'command', side_effect=run) as cmd:
            with self.assertRaisesRegex(deploy.DeploymentError, 'unlock all'):
                self.app.preflight()
            self.assertFalse(any(call.args[0] == 'home-manager' for call in cmd.call_args_list))

    def test_lock_check_fails_closed_on_missing_or_unreadable_state(self):
        uid = os.getuid()
        for listing, lock in (('[]', 'no'), ('{}', 'no'), ('invalid', 'no'),
                              (json.dumps([{'uid': uid, 'class': 'user', 'session': '1'}]), ''),
                              (json.dumps([{'uid': uid, 'class': 'user', 'session': '../bad'}]), 'no')):
            with self.subTest(listing=listing, lock=lock), \
                 patch.object(deploy, 'command', side_effect=[listing, lock]):
                with self.assertRaisesRegex(deploy.DeploymentError, 'cannot verify session lock state'):
                    self.app.require_unlocked_sessions()

    def test_all_unlocked_user_sessions_pass(self):
        sessions = json.dumps([{'uid': os.getuid(), 'class': 'user', 'session': '1'},
                               {'uid': os.getuid(), 'class': 'user', 'session': '2'}])
        with patch.object(deploy, 'command', side_effect=[sessions, 'no', 'no']) as cmd:
            self.app.require_unlocked_sessions()
        self.assertEqual(cmd.call_count, 3)

    def test_login_manager_failure_does_not_permit_deployment(self):
        with patch.object(deploy, 'command', side_effect=subprocess.CalledProcessError(1, 'loginctl')):
            with self.assertRaisesRegex(deploy.DeploymentError, 'cannot verify session lock state'):
                self.app.require_unlocked_sessions()

    def test_recheck_blocks_restart_if_session_locked_after_activation(self):
        with patch.object(self.app, 'graphical_active', return_value=True), \
             patch.object(self.app, 'require_unlocked_sessions', side_effect=deploy.DeploymentError('locked')), \
             patch.object(deploy, 'command') as cmd:
            with self.assertRaisesRegex(deploy.DeploymentError, 'locked'):
                self.app.restart_if_graphical()
            cmd.assert_not_called()


class FirstInstall(Fixture):
    def setUp(self):
        super().setUp()
        self.app.revision_file.unlink()
        host = self.config / "hosts" / self.app.hostname / "host.json"
        host.parent.mkdir(parents=True)
        host.write_text("{}")
        self.calls = []
        self.initial = "/nix/store/fixture-first-generation"
        stack = self.enterContext(ExitStack())
        stack.enter_context(patch.object(self.app, "check_clean"))
        stack.enter_context(patch.object(self.app, "resolve", side_effect=lambda ref: ref))
        stack.enter_context(patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})))
        self.verify = stack.enter_context(patch.object(self.app, "verify", return_value=[]))
        self.record = stack.enter_context(patch.object(self.app, "record"))
        stack.enter_context(patch.object(self.app, "generation", return_value=self.initial))
        real_file = Path.is_file
        stack.enter_context(patch.object(Path, "is_file", lambda path:
                           str(path) == self.initial + "/activate" or real_file(path)))
        real_command = deploy.command

        def invoke(*args, **kwargs):
            self.calls.append(args)
            if args[:2] == ("nix", "build"):
                return self.initial
            if args == (self.initial + "/activate",):
                return ""
            if args[0] == "git":
                return real_command(*args, **kwargs)
            self.fail(f"first installation invoked an unexpected command: {args}")

        self.invoke = stack.enter_context(patch.object(deploy, "command", side_effect=invoke))

    def test_text_install_records_no_fictitious_rollback_and_never_promotes(self):
        self.app.init()
        state = self.app.read_state()
        self.assertTrue(state["firstInstall"])
        self.assertIsNone(state["previousGeneration"])
        self.assertIsNone(state["previousPin"])
        self.assertEqual(state["packages"], self.packages_main)
        self.assertIn((self.initial + "/activate",), self.calls)
        self.assertFalse(any(call[0] in ("systemctl", "home-manager", "tam-restart-shell", "tam-shell")
                             or "push" in call for call in self.calls))
        self.verify.assert_called_once_with({"tamlinux": self.tamlinux_main}, self.packages_main)

    def test_existing_and_dangling_profile_are_refused_before_pin(self):
        self.app.profile.parent.mkdir(parents=True)
        self.app.profile.symlink_to("/missing-generation")
        with self.assertRaisesRegex(deploy.DeploymentError, "existing installation"):
            self.app.init()
        self.assertEqual(self.calls, [])

    def test_existing_shell_is_refused(self):
        self.app.revision_file.write_text(self.tamlinux_main)
        with self.assertRaisesRegex(deploy.DeploymentError, "existing installation"):
            self.app.init()

    def test_unregistered_account_is_refused(self):
        (self.config / "hosts" / self.app.hostname / "host.json").unlink()
        with self.assertRaisesRegex(deploy.DeploymentError, "registered local host"):
            self.app.init()

    def test_test_assembly_requires_explicit_test_option(self):
        with self.assertRaisesRegex(deploy.DeploymentError, "not on main"):
            self.app.init(self.packages_new)
        self.assertFalse(any(call[:2] == ("nix", "build") for call in self.calls))
        self.app.init(self.packages_new, test=True)
        self.assertEqual(self.app.read_state()["stage"], "test")
        self.assertEqual(self.origin_head("tamlinux-packages", "main"), self.packages_main)

    def test_build_failure_restores_lock_without_initializing_state(self):
        before = self.app.lock.read_bytes()
        invoke = self.invoke.side_effect

        def fail_build(*args, **kwargs):
            if args[:2] == ("nix", "build"):
                raise subprocess.CalledProcessError(1, "nix build")
            return invoke(*args, **kwargs)

        self.invoke.side_effect = fail_build
        with self.assertRaises(subprocess.CalledProcessError):
            self.app.init()
        self.assertEqual(self.app.lock.read_bytes(), before)
        self.assertFalse(self.app.state_file.exists())

    def test_dirty_config_is_refused_before_build_or_activation(self):
        with patch.object(self.app, "check_clean", side_effect=deploy.DeploymentError("dirty config")):
            with self.assertRaisesRegex(deploy.DeploymentError, "dirty config"):
                self.app.init()
        self.assertEqual(self.calls, [])

    def test_verification_failure_records_partial_install_and_blocks_retry(self):
        self.verify.return_value = ["command missing"]
        with self.assertRaisesRegex(deploy.DeploymentError, "command missing"):
            self.app.init()
        self.assertFalse(self.app.state_file.exists())
        self.record.assert_not_called()
        attempt = self.app.state_file.with_name("first-install.json")
        self.assertIn("failed", json.loads(attempt.read_text())["status"])
        with self.assertRaisesRegex(deploy.DeploymentError, "previous first-install attempt"):
            self.app.init()

    def test_init_parser_requires_known_options_and_one_revision(self):
        self.assertEqual(deploy.parse(["init", "abc", "--test"]), ("init", ["abc"], {"test": True}))
        self.assertIsNone(deploy.parse(["init", "--untested"]))
        self.assertIsNone(deploy.parse(["init", "one", "two"]))


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

    def test_deployment_records_live_path_digests(self):
        (self.config / "system/live-paths").write_text("config/settings.json\nconfig/absent.json\n")
        (self.config / "config").mkdir()
        (self.config / "config/settings.json").write_text("{}\n")
        self.deploy_test()
        self.assertEqual(self.app.read_state()["livePaths"], {
            "config/settings.json": hashlib.sha256(b"{}\n").hexdigest(),
            "config/absent.json": None})

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
        generations = iter(["/nix/store/old-generation", "/nix/store/new-generation", "/nix/store/old-generation"])
        with patch.object(self.app, "preflight"), patch.object(self.app, "status"), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate", side_effect=deploy.DeploymentError("restart failed")), \
             patch.object(self.app, "generation", side_effect=lambda: next(generations)), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(self.app, "restart_if_graphical"), \
             patch.object(self.app, "verify", return_value=[]) as verify, \
             patch.object(deploy, "command", side_effect=self.passthrough):
            with self.assertRaises(deploy.DeploymentError):
                self.app.test()
        self.assertEqual((self.config / "flake.lock").read_bytes(), before)
        self.assertIn(("/nix/store/old-generation/activate",), self.activations)
        verify.assert_called_once_with({"tamlinux": self.tamlinux_main}, self.packages_main)
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

    def test_failed_install_reports_original_and_recovery_errors(self):
        with patch.object(self.app, "preflight"), \
             patch.object(self.app, "generation", side_effect=["/nix/store/old-generation", "/nix/store/new-generation"]), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_main), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate", side_effect=deploy.DeploymentError("switch failed")), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(deploy, "command", side_effect=OSError("restore failed")):
            with self.assertRaisesRegex(deploy.DeploymentError, "switch failed.*recovery also failed: restore failed.*before retrying"):
                self.app.install(self.packages_new, {"tamlinux": self.tamlinux_new}, "test")

    def test_failed_install_reports_recovery_generation_mismatch(self):
        with patch.object(self.app, "preflight"), \
             patch.object(self.app, "generation", side_effect=["/nix/store/old-generation", "/nix/store/new-generation", "/nix/store/new-generation"]), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_main), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate", side_effect=deploy.DeploymentError("switch failed")), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(deploy, "command") as command, patch.object(self.app, "restart_if_graphical") as restart:
            with self.assertRaisesRegex(deploy.DeploymentError, "switch failed.*recovery also failed: previous generation was not restored"):
                self.app.install(self.packages_new, {"tamlinux": self.tamlinux_new}, "test")
        command.assert_called_once_with("/nix/store/old-generation/activate")
        restart.assert_not_called()

    def test_failed_install_does_not_activate_recovery_when_session_locks(self):
        with patch.object(self.app, 'preflight'), \
             patch.object(self.app, 'generation', side_effect=['/nix/store/old-generation', '/nix/store/new-generation']), \
             patch.object(self.app, 'rollback_pin', return_value=self.packages_main), \
             patch.object(self.app, 'pin', side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, 'activate', side_effect=deploy.DeploymentError('switch failed')), \
             patch.object(self.app, 'graphical_active', return_value=True), \
             patch.object(self.app, 'require_unlocked_sessions', side_effect=deploy.DeploymentError('locked')), \
             patch.object(deploy, 'command') as cmd:
            with self.assertRaisesRegex(deploy.DeploymentError, 'switch failed.*recovery also failed: locked'):
                self.app.install(self.packages_new, {'tamlinux': self.tamlinux_new}, 'test')
        cmd.assert_not_called()

    def test_failed_install_reports_recovery_endpoint_mismatch_with_staged_lock(self):
        self.write_lock(self.packages_new, {})
        before = self.app.lock.read_bytes()
        old_pins = {"tamlinux": self.tamlinux_main}
        with patch.object(self.app, "preflight"), \
             patch.object(self.app, "generation", return_value="/nix/store/old-generation"), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_main), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate", side_effect=deploy.DeploymentError("switch failed")), \
             patch.object(self.app, "components", return_value=old_pins), \
             patch.object(self.app, "verify", return_value=["wrong shell endpoint"]) as verify:
            with self.assertRaisesRegex(deploy.DeploymentError, "switch failed.*recovery also failed: recovered endpoints"):
                self.app.install(self.packages_new, {"tamlinux": self.tamlinux_new}, "test")
        verify.assert_called_once_with(old_pins, self.packages_main)
        self.assertEqual(self.app.lock.read_bytes(), before)

    def test_failed_recording_reports_active_candidate_without_claiming_recovery(self):
        with patch.object(self.app, "preflight"), \
             patch.object(self.app, "generation", side_effect=["/nix/store/old-generation", "/nix/store/new-generation"]), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_main), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})), \
             patch.object(self.app, "activate"), patch.object(self.app, "verify", return_value=[]), \
             patch.object(self.app, "record", side_effect=OSError("record failed")), \
             patch.object(self.app, "save_state") as save:
            with self.assertRaisesRegex(deploy.DeploymentError, "activation succeeded but deployment recording failed: record failed.*before retrying"):
                self.app.install(self.packages_new, {"tamlinux": self.tamlinux_new}, "test")
        save.assert_not_called()
        self.assertEqual(self.app.locked(), self.packages_new)


class LivePaths(Fixture):
    """system/live-paths exempts only the listed files from the clean check."""

    def setUp(self):
        super().setUp()
        git(self.config, "init", "-q", "-b", "main")
        git(self.config, "config", "user.name", "Fixture")
        git(self.config, "config", "user.email", "fixture@example.invalid")
        settings = self.config / "config/tamlinux/shell/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"format": "HH:mm"}\n')
        (self.config / "home.nix").write_text("{ }\n")
        git(self.config, "add", "-A")
        git(self.config, "commit", "-qm", "consumer")

    def list_live(self, *entries):
        (self.config / "system/live-paths").write_text("# live links\n" + "".join(e + "\n" for e in entries))
        git(self.config, "add", "system/live-paths")
        git(self.config, "commit", "-qm", "live paths")

    def test_without_a_list_every_change_refuses(self):
        (self.config / "config/tamlinux/shell/settings.json").write_text('{"format": "h:mm AP"}\n')
        with self.assertRaisesRegex(deploy.DeploymentError, "settings.json"):
            self.app.check_clean()

    def test_a_listed_live_file_may_be_dirty(self):
        self.list_live("config/tamlinux/shell/settings.json")
        (self.config / "config/tamlinux/shell/settings.json").write_text('{"format": "h:mm AP"}\n')
        self.app.check_clean()
        self.assertEqual(self.app.live_digests(), {
            "config/tamlinux/shell/settings.json":
                hashlib.sha256(b'{"format": "h:mm AP"}\n').hexdigest()})

    def test_other_changes_still_refuse(self):
        self.list_live("config/tamlinux/shell/settings.json")
        (self.config / "config/tamlinux/shell/settings.json").write_text('{"format": "h:mm AP"}\n')
        (self.config / "home.nix").write_text("{ changed = true; }\n")
        with self.assertRaisesRegex(deploy.DeploymentError, "home.nix"):
            self.app.check_clean()
        git(self.config, "checkout", "--", "home.nix")
        (self.config / "untracked.txt").write_text("x\n")
        with self.assertRaisesRegex(deploy.DeploymentError, "untracked.txt"):
            self.app.check_clean()

    def test_the_list_itself_must_be_committed(self):
        self.list_live("config/tamlinux/shell/settings.json")
        (self.config / "system/live-paths").write_text("home.nix\n")
        with self.assertRaises(deploy.DeploymentError):
            self.app.check_clean()

    def test_invalid_entries_are_rejected(self):
        for entry in ("../outside", "/etc/passwd", "a b", "config/./x", ".git/config",
                      "system/live-paths", "config/*"):
            (self.config / "system/live-paths").write_text(entry + "\n")
            with self.subTest(entry=entry), self.assertRaises(deploy.DeploymentError):
                self.app.live_paths()


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
    def test_back_refuses_to_record_mismatched_restored_endpoints(self):
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "generation": "/nix/store/new-generation",
                             "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
        before_state = self.app.state_file.read_bytes()
        before_lock = self.app.lock.read_bytes()
        old_pins = {"tamlinux": self.tamlinux_main}
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(self.app, "generation", side_effect=["/nix/store/new-generation", "/nix/store/old-generation"]), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_new), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(deploy, "command"), patch.object(self.app, "restart_if_graphical"), \
             patch.object(self.app, "components", return_value=old_pins), \
             patch.object(self.app, "verify", return_value=["wrong shell endpoint"]) as verify, \
             patch.object(self.app, "pin") as pin, patch.object(self.app, "record") as record:
            with self.assertRaisesRegex(deploy.DeploymentError, "rollback may be incomplete.*restored endpoints"):
                self.app.back()
        verify.assert_called_once_with(old_pins, self.packages_main)
        pin.assert_not_called()
        record.assert_not_called()
        self.assertEqual(self.app.lock.read_bytes(), before_lock)
        self.assertEqual(self.app.state_file.read_bytes(), before_state)

    def test_back_refuses_to_record_wrong_generation(self):
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "generation": "/nix/store/new-generation",
                             "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
        before_state = self.app.state_file.read_bytes()
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(self.app, "generation", return_value="/nix/store/new-generation"), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_new), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(deploy, "command"), patch.object(self.app, "pin") as pin, \
             patch.object(self.app, "restart_if_graphical") as restart:
            with self.assertRaisesRegex(deploy.DeploymentError, "rollback may be incomplete.*previous generation was not activated"):
                self.app.back()
        pin.assert_not_called()
        restart.assert_not_called()
        self.assertEqual(self.app.state_file.read_bytes(), before_state)

    def test_back_reports_partial_outcome_after_activation_failure(self):
        for failing_step in ("restart_if_graphical", "pin"):
            with self.subTest(failing_step=failing_step):
                self.app.save_state({"stage": "test", "packages": self.packages_new,
                                     "generation": "/nix/store/new-generation",
                                     "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
                before_state = self.app.state_file.read_bytes()
                with patch.object(deploy.Path, "is_file", return_value=True), \
                     patch.object(self.app, "generation", side_effect=["/nix/store/new-generation", "/nix/store/old-generation"]), \
                     patch.object(self.app, "rollback_pin", return_value=self.packages_new), \
                     patch.object(self.app, "graphical_active", return_value=False), \
                     patch.object(deploy, "command") as command, \
                     patch.object(self.app, "restart_if_graphical") as restart, \
                     patch.object(self.app, "components", return_value={"tamlinux": self.tamlinux_main}), \
                     patch.object(self.app, "verify", return_value=[]), \
                     patch.object(self.app, "pin") as pin:
                    {"restart_if_graphical": restart, "pin": pin}[failing_step].side_effect = deploy.DeploymentError("injected failure")
                    with self.assertRaisesRegex(deploy.DeploymentError, "rollback may be incomplete.*injected failure.*before retrying"):
                        self.app.back()
                command.assert_called_once_with("/nix/store/old-generation/activate")
                self.assertEqual(self.app.state_file.read_bytes(), before_state)

    def test_back_refuses_unknown_session_before_changing_generation(self):
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "generation": "/nix/store/new-generation",
                             "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
        before_lock = self.app.lock.read_bytes()
        before_state = self.app.state_file.read_bytes()
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(self.app, "generation", return_value="/nix/store/new-generation"), \
             patch.object(self.app, "rollback_pin", return_value=self.packages_new), \
             patch.object(self.app, "graphical_active", side_effect=deploy.DeploymentError("unknown session")), \
             patch.object(deploy, "command") as command, patch.object(self.app, "pin") as pin:
            with self.assertRaisesRegex(deploy.DeploymentError, "unknown session"):
                self.app.back()
        command.assert_not_called()
        pin.assert_not_called()
        self.assertEqual(self.app.lock.read_bytes(), before_lock)
        self.assertEqual(self.app.state_file.read_bytes(), before_state)

    def test_back_refuses_locked_session_before_changing_generation(self):
        self.app.save_state({'stage': 'test', 'packages': self.packages_new,
                             'generation': '/nix/store/new-generation',
                             'previousGeneration': '/nix/store/old-generation', 'previousPin': self.packages_main})
        before_lock = self.app.lock.read_bytes()
        before_state = self.app.state_file.read_bytes()
        with patch.object(deploy.Path, 'is_file', return_value=True), \
             patch.object(self.app, 'generation', return_value='/nix/store/new-generation'), \
             patch.object(self.app, 'rollback_pin', return_value=self.packages_new), \
             patch.object(self.app, 'graphical_active', return_value=True), \
             patch.object(self.app, 'require_unlocked_sessions', side_effect=deploy.DeploymentError('locked')), \
             patch.object(deploy, 'command') as cmd, patch.object(self.app, 'pin') as pin:
            with self.assertRaisesRegex(deploy.DeploymentError, 'locked'):
                self.app.back()
        cmd.assert_not_called()
        pin.assert_not_called()
        self.assertEqual(self.app.lock.read_bytes(), before_lock)
        self.assertEqual(self.app.state_file.read_bytes(), before_state)

    def test_back_reactivates_and_restores_the_previous_pin(self):
        generation = self.root / "nix-store-sim"
        real_command = deploy.command
        self.write_lock(self.packages_new, {})
        self.app.revision_file.write_text(self.tamlinux_new + "\n")
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "generation": "/nix/store/new-generation",
                             "previousGeneration": "/nix/store/old-generation", "previousPin": self.packages_main})
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(deploy, "command", side_effect=lambda *args, **kwargs:
                          real_command(*args, **kwargs) if args[0] == "git" else "") as command, \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(self.app, "wait_ready") as ready, \
             patch.object(self.app, "status"), patch.object(self.app, "record"), \
             patch.object(self.app, "verify", return_value=[]) as verify, \
             patch.object(self.app, "generation", side_effect=["/nix/store/new-generation", "/nix/store/old-generation"]), \
             patch.object(self.app, "pin", side_effect=lambda rev: self.write_lock(rev, {})) as pin:
            self.app.back()
        command.assert_any_call("/nix/store/old-generation/activate")
        self.assertNotIn(("tam-restart-shell",), [call.args for call in command.call_args_list])
        ready.assert_not_called()
        pin.assert_called_once_with(self.packages_main)
        verify.assert_called_once_with({"tamlinux": self.tamlinux_main}, self.packages_main)
        state = self.app.read_state()
        self.assertEqual(state["previousPin"], self.packages_new)
        self.assertEqual(state["previousGeneration"], "/nix/store/new-generation")
        self.assertEqual(state["generation"], "/nix/store/old-generation")
        self.assertEqual(state["components"], {"tamlinux": self.tamlinux_main})
        self.write_lock(self.packages_new, {})
        self.app.revision_file.write_text(self.tamlinux_main + "\n")
        self.assertEqual(self.app.rollback_pin("/nix/store/old-generation"), self.packages_main)

    def test_back_uses_the_active_record_when_the_lock_is_staged(self):
        # Candidate c is active; the consumer lock has already been prepared
        # for d. Back to b must retain c, never d, as its roll-forward pin.
        self.write_lock(self.packages_main, {})
        self.app.revision_file.write_text(self.tamlinux_new)
        self.app.save_state({"stage": "test", "packages": self.packages_new,
                             "generation": "/nix/store/c-generation",
                             "previousGeneration": "/nix/store/b-generation", "previousPin": self.packages_main})
        with patch.object(deploy.Path, "is_file", return_value=True), \
             patch.object(deploy, "command"), patch.object(self.app, "wait_ready"), \
             patch.object(self.app, "graphical_active", return_value=False), \
             patch.object(self.app, "status"), patch.object(self.app, "record"), \
             patch.object(self.app, "verify", return_value=[]), \
             patch.object(self.app, "generation", side_effect=["/nix/store/c-generation", "/nix/store/b-generation"]), \
             patch.object(self.app, "components", side_effect=lambda rev: {"tamlinux": self.tamlinux_new if rev == self.packages_new else self.tamlinux_main}), \
             patch.object(self.app, "pin"):
            self.app.back()
        self.assertEqual(self.app.read_state()["previousPin"], self.packages_new)
        self.assertEqual(self.app.read_state()["previousGeneration"], "/nix/store/c-generation")

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
    def setUp(self):
        super().setUp()
        self.outputs = {
            "shell": str(self.root / "store/c-tamlinux-shell"),
            "plugins": str(self.root / "store/c-tamlinux-plugins"),
            "commands": str(self.root / "store/c-tamlinux-commands"),
            "tam": str(self.root / "store/tam-0.9.1"),
            "tools": str(self.root / "store/tamlinux-tools"),
            "pluginIds": ["fred.clock", "fred.workspaces"],
            "commandNames": ["tam-deploy", "tam-plugin", "tam-work"],
            "features": {"menu": True}, "manWrapper": True, "selectionRecord": True,
        }
        mock = patch.object(self.app, "expected_outputs", return_value=self.outputs)
        mock.start()
        self.addCleanup(mock.stop)

    def endpoint(self, path, target, directory=False):
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if directory:
            target.mkdir(exist_ok=True)
        else:
            target.write_text("fixture")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)

    def install(self, selected=None):
        if selected is None:
            selected = self.outputs["pluginIds"]
        self.app.revision_file.write_text(self.tamlinux_new + "\n")
        self.app.selection_file.write_text(json.dumps({"revision": self.tamlinux_new, "plugins": selected}))
        self.endpoint(self.app.shell_link, self.outputs["shell"] + "/share/tamlinux/shell", True)
        for name in selected:
            self.endpoint(self.app.plugins_dir / name, self.outputs["plugins"] + "/share/tamlinux/plugins/" + name, True)
        for name in self.outputs["commandNames"]:
            self.endpoint(self.app.bin_dir / name, self.outputs["commands"] + "/bin/" + name)
        for name, package in [("tam", "tam"), ("tam-man", "tam"), ("tam-file-select", "tools"), ("tam-menu", "shell")]:
            self.endpoint(self.app.bin_dir / name, self.outputs[package] + "/bin/" + name)
        self.endpoint(self.app.plugins_dir.parent / "menu/default.jsonc", self.outputs["shell"] + "/share/tamlinux/menu/default.jsonc")

    def verify(self):
        return self.app.verify({"tamlinux": self.tamlinux_new}, self.packages_new)

    def test_matching_install(self):
        self.install()
        self.assertEqual(self.verify(), [])

    def test_selected_subset_and_empty_selection(self):
        self.install(selected=["fred.clock"])
        self.assertEqual(self.verify(), [])
        (self.app.plugins_dir / "fred.clock").unlink()
        self.app.selection_file.write_text(json.dumps({"revision": self.tamlinux_new, "plugins": []}))
        self.assertEqual(self.verify(), [])

    def test_mixed_assembly_outputs_are_rejected(self):
        self.install()
        for path in [self.app.shell_link, self.app.plugins_dir / "fred.clock", self.app.bin_dir / "tam-deploy", self.app.bin_dir / "tam"]:
            target = Path(str(path.resolve()).replace("/store/", "/old-store/"))
            path.unlink()
            self.endpoint(path, target, path in [self.app.shell_link, self.app.plugins_dir / "fred.clock"])
        problems = self.verify()
        self.assertEqual(len(problems), 4)
        self.assertTrue(all("expected" in p for p in problems))

    def test_missing_endpoints_and_broken_links_are_rejected(self):
        self.install()
        for name in ["tam-plugin", "tam-work", "tam-menu", "tam-man", "tam-file-select"]:
            (self.app.bin_dir / name).unlink()
        (self.app.plugins_dir / "fred.clock").unlink()
        (self.app.bin_dir / "tam").resolve().unlink()
        problems = self.verify()
        self.assertEqual(len(problems), 7)
        self.assertTrue(all("missing" in p for p in problems))

    def test_selection_record_cannot_hide_unknown_or_duplicate_plugins(self):
        self.install()
        for selected in [["fred.unknown"], ["fred.clock", "fred.clock"], "fred.clock", [1]]:
            with self.subTest(selected=selected):
                self.app.selection_file.write_text(json.dumps({"revision": self.tamlinux_new, "plugins": selected}))
                self.assertTrue(any("selection record" in p for p in self.verify()))
        self.app.selection_file.unlink()
        self.assertTrue(any("selection record" in p for p in self.verify()))

    def test_unexpected_installed_plugin_is_rejected(self):
        self.install(selected=["fred.clock"])
        self.endpoint(self.app.plugins_dir / "fred.extra", self.outputs["plugins"] + "/share/tamlinux/plugins/fred.extra", True)
        self.assertTrue(any("unexpected installed plugin" in p for p in self.verify()))

    def test_old_assembly_without_selection_record_remains_verifiable(self):
        self.install()
        self.outputs["selectionRecord"] = False
        self.app.selection_file.unlink()
        self.assertEqual(self.verify(), [])

    def test_revision_mismatch_is_rejected(self):
        self.install()
        self.app.revision_file.write_text(self.tamlinux_main)
        self.assertTrue(any("shell revision" in p for p in self.verify()))

    def test_expected_outputs_are_evaluated_at_the_exact_commit_and_cached(self):
        with patch.object(self.app, "expected_outputs", deploy.Deployment.expected_outputs.__get__(self.app)), \
             patch.object(deploy, "command", return_value=json.dumps(self.outputs)) as command:
            self.app.expected_outputs(self.packages_new)
            self.app.expected_outputs(self.packages_new)
        command.assert_called_once()
        args = command.call_args.args
        self.assertIn("--no-write-lock-file", args)
        self.assertIn(f"git+file://{self.workspace / 'tamlinux-packages'}?rev={self.packages_new}#packages.{self.app.system}", args)


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


class FleetProfiles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.config = Path(self.temporary.name)
        self.name = os.uname().nodename
        self.user = deploy.getpass.getuser()
        self.directory = self.config / "hosts" / self.name
        self.directory.mkdir(parents=True)
        (self.directory / "host.json").write_text(json.dumps({"hostname": self.name, "username": self.user}))
        self.environment = patch.dict(os.environ, {"TAMLINUX_CONFIG_REPO": str(self.config),
                                                  "TAMLINUX_HOME_CONFIGURATION": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_registered_hostname_selects_explicit_output(self):
        self.assertEqual(deploy.Deployment().home_configuration, f"{self.user}@{self.name}")

    def test_unknown_local_hostname_never_falls_back_to_generic_profile(self):
        (self.directory / "host.json").unlink()
        with self.assertRaisesRegex(deploy.DeploymentError, "no registered host"):
            deploy.Deployment()

    def test_foreign_profile_override_is_rejected(self):
        with patch.dict(os.environ, {"TAMLINUX_HOME_CONFIGURATION": "someone@elsewhere"}):
            with self.assertRaisesRegex(deploy.DeploymentError, "another host"):
                deploy.Deployment()

    def test_bom_updates_only_local_state(self):
        state = self.directory / "state"
        state.mkdir()
        (state / "bom.json").write_text('{"components":{}}')
        foreign = self.config / "hosts/foreign/state"
        foreign.mkdir(parents=True)
        (foreign / "bom.json").write_text("untouched")
        changed = deploy.Deployment().update_bom({"stage": "fixture"})
        self.assertEqual(changed, [f"hosts/{self.name}/state/bom.json"])
        self.assertEqual((foreign / "bom.json").read_text(), "untouched")
        self.assertFalse((self.config / "system/bom.json").exists())

    def test_symlinked_bom_is_rejected(self):
        state = self.directory / "state"
        state.mkdir()
        other = self.config / "other.json"
        other.write_text('{"components":{}}')
        (state / "bom.json").symlink_to(other)
        with self.assertRaisesRegex(deploy.DeploymentError, "symlink BOM"):
            deploy.Deployment().update_bom({"stage": "fixture"})
        self.assertEqual(other.read_text(), '{"components":{}}')


class ShellReadiness(unittest.TestCase):
    palette = {"foreground": "#a9b1d6", "background": "#1a1b26",
               "accent": "#7aa2f7", "muted": "#414868"}

    def test_reachable_ipc_with_undefined_palette_is_not_ready(self):
        app = deploy.Deployment.__new__(deploy.Deployment)
        def reply(*args, **kwargs):
            return "pong" if args[1] == "reminders" else json.dumps(dict.fromkeys(self.palette, "undefined"))
        with patch.object(deploy, "command", side_effect=reply), patch.object(deploy.time, "sleep"):
            with self.assertRaisesRegex(deploy.DeploymentError, "valid theme palette"):
                app.wait_ready()

    def test_waits_for_theme_then_accepts_valid_palette(self):
        app = deploy.Deployment.__new__(deploy.Deployment)
        palettes = iter(['{"background":"undefined"}', 'not JSON', json.dumps(self.palette)])
        def reply(*args, **kwargs):
            return "pong" if args[1] == "reminders" else next(palettes)
        with patch.object(deploy, "command", side_effect=reply), patch.object(deploy.time, "sleep") as sleep:
            app.wait_ready()
        self.assertEqual(sleep.call_count, 2)

    def test_missing_theme_service_cannot_pass_readiness(self):
        app = deploy.Deployment.__new__(deploy.Deployment)
        def reply(*args, **kwargs):
            if args[1] == "reminders": return "pong"
            raise subprocess.CalledProcessError(1, args)
        with patch.object(deploy, "command", side_effect=reply), patch.object(deploy.time, "sleep"):
            with self.assertRaises(deploy.DeploymentError): app.wait_ready()


class Usage(unittest.TestCase):
    def test_rejects_unknown_commands(self):
        self.assertEqual(deploy.main(["deploy"]), 2)
        self.assertEqual(deploy.main(["test", "a", "b"]), 2)


if __name__ == "__main__":
    unittest.main()
