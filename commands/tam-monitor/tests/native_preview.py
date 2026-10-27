"""Real recovery processes/deadlines with link-time fake VT/session/DRM actions."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

class NativePreview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tam-monitor-preview-")
        self.log = Path(self.tmp.name) / "actions"
        self.log.touch()
        self.processes = []

    def tearDown(self):
        for p in self.processes:
            if p.poll() is None:
                os.kill(p.pid, signal.SIGCONT)
                p.terminate()
                p.communicate(timeout=4)
        self.tmp.cleanup()

    def start(self, seconds=1, **flags):
        env = dict(os.environ, TAM_MONITOR_FIXTURE_LOG=str(self.log),
                   TAM_MONITOR_RUNTIME_DIR=self.tmp.name)
        env.update({"TAM_MONITOR_FIXTURE_" + k: str(v) for k, v in flags.items()})
        p = subprocess.Popen([str(ROOT / "build/tam-monitor-preview-fixture"), "preview",
            "--card", "1", "--keep", "DP-1", "--seconds", str(seconds), "--json"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes.append(p)
        return p

    def actions(self):
        return [line.split() for line in self.log.read_text().splitlines()]

    def await_action(self, name):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            for action, pid in self.actions():
                if action == name:
                    return int(pid)
            time.sleep(0.01)
        self.fail(f"Missing {name}: {self.actions()}")

    def finish(self, p, success=True):
        stdout, stderr = p.communicate(timeout=5)
        self.assertEqual(p.returncode, 0 if success else 1, stderr)
        data = json.loads(stdout)
        self.assertEqual(data["ok"], success)
        return data

    def test_deadline_restores_before_release(self):
        p = self.start()
        worker = self.await_action("apply")
        self.assertNotEqual(worker, p.pid)
        self.assertEqual(os.getpgid(worker), worker)
        self.assertEqual(os.getsid(worker), os.getsid(p.pid))
        self.finish(p)
        self.assertEqual([a for a, _ in self.actions()],
                         ["acquire", "capture", "apply", "restore", "free", "release"])

    def test_owner_sigkill_recovers_independently(self):
        p = self.start()
        self.await_action("apply")
        p.kill()
        p.communicate(timeout=4)
        self.await_action("release")
        self.assertIn("restore", [a for a, _ in self.actions()])

    def test_stopped_owner_cannot_postpone_recovery(self):
        p = self.start()
        self.await_action("apply")
        os.kill(p.pid, signal.SIGSTOP)
        self.await_action("release")
        os.kill(p.pid, signal.SIGCONT)
        self.finish(p)
        self.assertIn("restore", [a for a, _ in self.actions()])

    def test_guard_sigkill_is_reported_as_failure(self):
        p = self.start(seconds=3)
        os.kill(self.await_action("apply"), signal.SIGKILL)
        self.finish(p, success=False)
        self.assertNotIn("restore", [a for a, _ in self.actions()])

    def test_stopped_guard_is_resumed_for_recovery(self):
        p = self.start()
        worker = self.await_action("apply")
        os.kill(worker, signal.SIGSTOP)
        stdout, stderr = p.communicate(timeout=15)
        self.assertEqual(p.returncode, 0, stderr)
        self.assertTrue(json.loads(stdout)["ok"])
        self.assertIn("restore", [a for a, _ in self.actions()])

    def test_guard_term_restores(self):
        p = self.start(seconds=3)
        os.kill(self.await_action("apply"), signal.SIGTERM)
        self.finish(p)
        self.assertIn("restore", [a for a, _ in self.actions()])

    def test_ui_interrupt_restores(self):
        p = self.start(seconds=3)
        self.await_action("apply")
        p.send_signal(signal.SIGINT)
        self.finish(p)
        self.assertIn("restore", [a for a, _ in self.actions()])

    def test_failed_commit_is_compensated(self):
        self.finish(self.start(COMMIT_FAIL=1), success=False)
        self.assertEqual([a for a, _ in self.actions()],
                         ["acquire", "capture", "apply", "restore", "free", "release"])

    def test_denied_acquisition_never_writes(self):
        self.finish(self.start(DENIED=1), success=False)
        self.assertEqual([a for a, _ in self.actions()], ["acquire"])

    def test_failed_capture_releases_without_write(self):
        self.finish(self.start(CAPTURE_FAIL=1), success=False)
        self.assertEqual([a for a, _ in self.actions()], ["acquire", "capture", "release"])

    def test_expiry_during_capture_prevents_apply(self):
        self.finish(self.start(SLOW_CAPTURE=1), success=False)
        self.assertNotIn("apply", [a for a, _ in self.actions()])

    def test_expiry_during_atomic_preparation_prevents_apply(self):
        self.finish(self.start(SLOW_TEST=1), success=False)
        self.assertNotIn("apply", [a for a, _ in self.actions()])

    def test_failed_restore_is_reported(self):
        self.finish(self.start(RESTORE_FAIL=1), success=False)
        self.assertIn("release", [a for a, _ in self.actions()])

    def test_vt_handoff_restores_then_releases(self):
        self.finish(self.start(PAUSE=1))
        self.assertEqual([a for a, _ in self.actions()][-3:], ["restore", "free", "release"])

    def test_hotplug_ends_selection_with_recovery(self):
        self.finish(self.start(HOTPLUG=1), success=False)
        self.assertEqual([a for a, _ in self.actions()][-3:], ["restore", "free", "release"])

    def test_hotplug_without_surviving_output_reports_loss_and_releases(self):
        data = self.finish(self.start(HOTPLUG=1, NO_OUTPUT=1), success=False)
        self.assertEqual(data["code"], 11)  # TAM_DISPLAY_RESTORE_FAILED
        self.assertEqual([a for a, _ in self.actions()][-3:], ["restore", "free", "release"])

    def test_hotplug_failed_restore_releases(self):
        data = self.finish(self.start(HOTPLUG=1, RESTORE_FAIL=1), success=False)
        self.assertEqual(data["code"], 11)
        self.assertEqual([a for a, _ in self.actions()][-3:], ["restore", "free", "release"])

    def test_revoke_does_not_replay_stale_state(self):
        self.finish(self.start(REVOKE=1), success=False)
        self.assertEqual([a for a, _ in self.actions()][-2:], ["free", "release"])
        self.assertNotIn("restore", [a for a, _ in self.actions()])

    def test_keep_shell_individual_wake_blank_and_restore(self):
        exe = str(ROOT / "build/tam-monitor-preview-fixture")
        shell_script = Path(self.tmp.name) / "session.sh"
        shell_script.write_text(
            "#!/bin/sh\n"
            "set -e\n"
            f'"{exe}" wake --monitor HDMI-A-1 --json\n'
            f'"{exe}" blank --monitor HDMI-A-1 --json\n'
            f'"{exe}" keep HDMI-A-1 --json\n'
            f'"{exe}" wake --all --json\n'
        )
        shell_script.chmod(0o755)
        env = dict(os.environ,
                   TAM_MONITOR_FIXTURE_LOG=str(self.log),
                   TAM_MONITOR_FIXTURE_VERBOSE="1",
                   TAM_MONITOR_RUNTIME_DIR=self.tmp.name,
                   TAM_MONITOR_SHELL=str(shell_script))
        os.chmod(self.tmp.name, 0o700)
        p = subprocess.Popen([exe, "keep", "DP-1", "--shell"],
                             env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes.append(p)
        stdout, stderr = p.communicate(timeout=5)
        self.assertEqual(p.returncode, 0, stderr)
        acts = [a for a, _ in self.actions()]
        self.assertIn("verify_cfb", acts)
        self.assertIn("keep:DP-1", acts)
        self.assertIn("wake:HDMI-A-1", acts)
        self.assertIn("blank:HDMI-A-1", acts)
        self.assertIn("keep:HDMI-A-1", acts)
        self.assertIn("vt_wake", acts)
        self.assertEqual(acts[-3:], ["restore", "free", "release"])

    def test_keep_cfb_mismatch_prevents_write(self):
        exe = str(ROOT / "build/tam-monitor-preview-fixture")
        os.chmod(self.tmp.name, 0o700)
        env = dict(os.environ,
                   TAM_MONITOR_FIXTURE_LOG=str(self.log),
                   TAM_MONITOR_FIXTURE_CFB_FAIL="1",
                   TAM_MONITOR_RUNTIME_DIR=self.tmp.name)
        p = subprocess.Popen([exe, "keep", "DP-1", "--seconds", "1", "--json"],
                             env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes.append(p)
        self.finish(p, success=False)
        acts = [a for a, _ in self.actions()]
        self.assertNotIn("apply", acts)
        self.assertEqual(acts, ["acquire", "capture", "free", "release"])

    def test_targeted_blank_monitors_restores_on_deadline(self):
        exe = str(ROOT / "build/tam-monitor-preview-fixture")
        os.chmod(self.tmp.name, 0o700)
        env = dict(os.environ,
                   TAM_MONITOR_FIXTURE_LOG=str(self.log),
                   TAM_MONITOR_FIXTURE_VERBOSE="1",
                   TAM_MONITOR_RUNTIME_DIR=self.tmp.name)
        p = subprocess.Popen([exe, "blank", "--monitor", "HDMI-A-1", "--seconds", "1", "--json"],
                             env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes.append(p)
        self.finish(p, success=True)
        acts = [a for a, _ in self.actions()]
        self.assertEqual(acts, ["acquire", "capture", "verify_cfb", "apply", "blank:HDMI-A-1", "restore", "free", "release"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
