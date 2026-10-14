"""Execute the real read-only update preflight against recovery/transaction data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

COMMANDS=Path(__file__).resolve().parents[2]


class UpdatePreflight(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.artifact=self.root/'recovery'
        self.artifact.write_bytes(b'actual prepared recovery bytes')
        self.record=self.root/'ready.json'
        self.value={'schema':1,'ready':True,'operation':'native-update',
            'recoveryArtifacts':[{'path':str(self.artifact),'sha256':hashlib.sha256(self.artifact.read_bytes()).hexdigest()}],
            'approvedProviderVersions':{'hyprland':'0.56.3-1'}}

    def validate(self,updates='',firmware=False):
        name='tam-update-firmware' if firmware else 'tam-update'
        script=(COMMANDS/name/name).read_text()
        code=script.split("<<'PYTHON'\n",1)[1].split('\nPYTHON',1)[0]
        self.record.write_text(json.dumps(self.value))
        return subprocess.run([sys.executable,'-I','-c',code,str(self.record),updates],
                              capture_output=True,text=True,timeout=3)

    def test_approved_provider_transaction_requires_matching_recovery_bytes(self):
        self.assertEqual(self.validate('hyprland 0.56.2-4.1 -> 0.56.3-1').returncode,0)
        self.artifact.write_bytes(b'later changed backup')
        self.assertNotEqual(self.validate('hyprland 0.56.2-4.1 -> 0.56.3-1').returncode,0)

    def test_unreviewed_carried_provider_update_is_refused(self):
        result=self.validate('aquamarine 0.15.1-1.1 -> 0.16.0-1')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Stage the maintained aquamarine',result.stderr)

    def test_malformed_update_preview_is_refused(self):
        self.assertNotEqual(self.validate('unexpected update format').returncode,0)

    def test_wrong_operation_or_absent_recovery_never_authorizes(self):
        for change in [{'operation':'other'},{'ready':False},{'recoveryArtifacts':[]}]:
            before=dict(self.value);self.value.update(change)
            self.assertNotEqual(self.validate().returncode,0)
            self.value=before

    def test_linked_recovery_artifact_requires_explicit_review(self):
        self.artifact.unlink();self.artifact.symlink_to('unavailable-backup')
        self.assertNotEqual(self.validate().returncode,0)

    def test_firmware_recovery_is_separate_and_rehashed(self):
        self.assertNotEqual(self.validate(firmware=True).returncode,0)
        self.value['operation']='firmware-update'
        self.assertEqual(self.validate(firmware=True).returncode,0)
        self.artifact.write_bytes(b'changed firmware recovery')
        self.assertNotEqual(self.validate(firmware=True).returncode,0)
