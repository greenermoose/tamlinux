import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "native" / "pam-transaction.py"
SPEC = importlib.util.spec_from_file_location("pam_transaction", SCRIPT)
pam = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pam)

SDDM = (
    b"#%PAM-1.0\n\n"
    b"auth        include     system-login\n"
    b"-auth       optional    pam_kwallet5.so\n\n"
    b"account     include     system-login\n\n"
    b"password    include     system-login\n\n"
    b"session     optional    pam_keyinit.so          force revoke\n"
    b"session     include     system-login\n"
    b"-session    optional    pam_gnome_keyring.so    auto_start\n"
    b"-session    optional    pam_kwallet5.so         auto_start\n"
)
AUTOLOGIN = (
    b"#%PAM-1.0\n"
    b"auth        required    pam_env.so\n"
    b"auth        required    pam_shells.so\n"
    b"auth        required    pam_nologin.so\n"
    b"auth        required    pam_permit.so\n"
    b"auth        required    pam_faillock.so authsucc\n"
    b"-auth       optional    pam_gnome_keyring.so\n"
    b"-auth       optional    pam_kwallet5.so\n"
    b"account     include     system-local-login\n"
    b"password    include     system-local-login\n"
    b"session     include     system-local-login\n"
    b"-session    optional    pam_gnome_keyring.so auto_start\n"
    b"-session    optional    pam_kwallet5.so auto_start\n"
)


class PamTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "root"
        self.pam_dir = self.root / "etc/pam.d"
        self.pam_dir.mkdir(parents=True)
        self.sddm = self.pam_dir / "sddm"
        self.autologin = self.pam_dir / "sddm-autologin"
        self.sddm.write_bytes(SDDM)
        self.autologin.write_bytes(AUTOLOGIN)
        self.sddm.chmod(0o640)
        self.autologin.chmod(0o600)
        self.checkpoint = Path(self.temp.name) / "checkpoint"
        self.preserve = Path(self.temp.name) / "preserved-current"

    def tearDown(self):
        self.temp.cleanup()

    def test_baseline_hashes_pin_reviewed_inputs(self):
        self.assertEqual(hashlib.sha256(SDDM).hexdigest(), pam.BASELINE["etc/pam.d/sddm"]["sha256"])
        self.assertEqual(hashlib.sha256(AUTOLOGIN).hexdigest(), pam.BASELINE["etc/pam.d/sddm-autologin"]["sha256"])

    def test_apply_removes_only_three_hooks_and_preserves_metadata(self):
        pam.apply(self.root, self.checkpoint)
        self.assertEqual(self.sddm.read_bytes(), pam.transform(SDDM, 1, "sddm"))
        self.assertEqual(self.autologin.read_bytes(), pam.transform(AUTOLOGIN, 2, "sddm-autologin"))
        self.assertEqual(stat.S_IMODE(self.sddm.stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE(self.autologin.stat().st_mode), 0o600)
        record = json.loads((self.checkpoint / "transaction.json").read_text())
        self.assertEqual(record["state"], "applied")
        self.assertEqual(len(record["files"]), 2)

    def test_input_drift_refuses_before_checkpoint_or_writes(self):
        self.autologin.write_bytes(AUTOLOGIN + b"# later package change\n")
        original_sddm = self.sddm.read_bytes()
        original_autologin = self.autologin.read_bytes()
        with self.assertRaisesRegex(ValueError, "baseline hash drift"):
            pam.apply(self.root, self.checkpoint)
        self.assertFalse(self.checkpoint.exists())
        self.assertEqual(self.sddm.read_bytes(), original_sddm)
        self.assertEqual(self.autologin.read_bytes(), original_autologin)

    def test_interrupted_checkpoint_creation_can_be_retried(self):
        with mock.patch.object(pam, "write_record", side_effect=OSError("simulated checkpoint interruption")):
            with self.assertRaisesRegex(OSError, "simulated checkpoint interruption"):
                pam.apply(self.root, self.checkpoint)
        self.assertFalse(self.checkpoint.exists())
        pam.apply(self.root, self.checkpoint)
        self.assertEqual(json.loads((self.checkpoint / "transaction.json").read_text())["state"], "applied")

    def test_retry_completes_after_interruption_between_files(self):
        writer = pam.write_atomic
        calls = 0
        def interrupted(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated interruption")
            return writer(*args)
        with mock.patch.object(pam, "write_atomic", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                pam.apply(self.root, self.checkpoint)
        self.assertEqual(self.sddm.read_bytes(), pam.transform(SDDM, 1, "sddm"))
        self.assertEqual(self.autologin.read_bytes(), AUTOLOGIN)
        pam.apply(self.root, self.checkpoint)
        self.assertEqual(self.autologin.read_bytes(), pam.transform(AUTOLOGIN, 2, "sddm-autologin"))
        self.assertEqual(json.loads((self.checkpoint / "transaction.json").read_text())["state"], "applied")

    def test_restore_archives_later_writes_before_restoring_originals(self):
        pam.apply(self.root, self.checkpoint)
        later = self.autologin.read_bytes() + b"# later local write\n"
        self.autologin.write_bytes(later)
        pam.restore(self.root, self.checkpoint, self.preserve)
        self.assertEqual(self.sddm.read_bytes(), SDDM)
        self.assertEqual(self.autologin.read_bytes(), AUTOLOGIN)
        self.assertEqual((self.preserve / "sddm-autologin.bytes").read_bytes(), later)
        preserved = json.loads((self.preserve / "preserved.json").read_text())
        self.assertEqual(preserved["files"]["etc/pam.d/sddm-autologin"]["sha256"], hashlib.sha256(later).hexdigest())

    def test_restore_retry_finishes_after_interruption(self):
        pam.apply(self.root, self.checkpoint)
        writer = pam.write_atomic
        calls = 0
        def interrupted(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated restore interruption")
            return writer(*args)
        with mock.patch.object(pam, "write_atomic", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "simulated restore interruption"):
                pam.restore(self.root, self.checkpoint, self.preserve)
        pam.restore(self.root, self.checkpoint, self.preserve)
        self.assertEqual(self.sddm.read_bytes(), SDDM)
        self.assertEqual(self.autologin.read_bytes(), AUTOLOGIN)

    def test_refuses_symlink_pam_file(self):
        self.sddm.unlink()
        self.sddm.symlink_to(self.autologin)
        with self.assertRaisesRegex(ValueError, "non-regular"):
            pam.apply(self.root, self.checkpoint)
        self.assertFalse(self.checkpoint.exists())

    def test_live_operation_refuses_active_or_unverifiable_sddm(self):
        with mock.patch.object(pam.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="active\n")):
            with self.assertRaisesRegex(PermissionError, "must be verified inactive"):
                pam.require_stopped_sddm()
        with mock.patch.object(pam.subprocess, "run", return_value=mock.Mock(returncode=4, stdout="")):
            with self.assertRaisesRegex(PermissionError, "must be verified inactive"):
                pam.require_stopped_sddm()


if __name__ == "__main__":
    unittest.main()
