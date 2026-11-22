"""Execute the real read-only update preflight against recovery/transaction data."""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
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


class AurListingPolicy(unittest.TestCase):
    """K53 / D168: tam-update lists AUR updates; never upgrades them via yay."""

    def script(self):
        return (COMMANDS / 'tam-update' / 'tam-update').read_text()

    def test_refuses_unattended_yay_aur_upgrades(self):
        # Only non-comment code may invoke yay; the sole flag allowed is -Qua.
        code = '\n'.join(
            line.split('#', 1)[0]
            for line in self.script().splitlines()
        )
        invocations = re.findall(r'\byay\s+(-\S+)', code)
        self.assertEqual(invocations, ['-Qua'])
        self.assertNotRegex(code, r'\byay\s+-S(ua|yu)?(\s|$)')

    def test_lists_pending_aur_with_qua_only(self):
        text = self.script()
        self.assertIn('yay -Qua', text)
        self.assertIn('list_aur_updates', text)
        self.assertIn('review frozen recipes', text)

    def test_omarchy_repo_guard_matches_only_repo_column(self):
        text = self.script()
        self.assertIn("grep -qi '^omarchy '", text)
        self.assertNotIn("grep -qi 'omarchy'", text)

    def run_check(self, foreign_output, yay_output=None, checkupdates_output=""):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            pacman = bin_dir / "pacman"
            pacman.write_text(textwrap.dedent(f"""\
                #!/bin/bash
                if [[ "${{1:-}}" == "-Sl" ]]; then
                    printf 'core linux 7.3.5-1\\n'
                    exit 0
                fi
                if [[ "${{1:-}}" == "-Qm" ]]; then
                    printf '%s' {foreign_output!r}
                    [[ -n {foreign_output!r} ]]
                    exit $?
                fi
                exit 0
            """))
            pacman.chmod(0o755)
            checkupdates = bin_dir / "checkupdates"
            checkupdates.write_text(textwrap.dedent(f"""\
                #!/bin/bash
                if [[ -n {checkupdates_output!r} ]]; then
                    printf '%s' {checkupdates_output!r}
                    exit 0
                fi
                exit 2
            """))
            checkupdates.chmod(0o755)
            if yay_output is not None:
                yay = bin_dir / "yay"
                yay.write_text(textwrap.dedent(f"""\
                    #!/bin/bash
                    if [[ "${{1:-}}" != "-Qua" ]]; then
                        echo "forbidden yay flag: $*" >&2
                        exit 99
                    fi
                    printf '%s' {yay_output!r}
                    [[ -n {yay_output!r} ]]
                    exit $?
                """))
                yay.chmod(0o755)
            for tool in ("grep", "printf"):
                target = Path("/usr/bin") / tool
                if target.exists():
                    (bin_dir / tool).symlink_to(target)
            rewritten = (
                self.script()
                .replace("/usr/bin/pacman", str(pacman))
                .replace("/usr/bin/checkupdates", str(checkupdates))
            )
            runner = root / "tam-update"
            runner.write_text(rewritten)
            runner.chmod(0o755)
            return subprocess.run(
                ["/usr/bin/bash", str(runner), "--check"],
                env={"PATH": str(bin_dir)},
                capture_output=True, text=True, timeout=5,
            )

    def test_check_lists_pending_aur_and_frozen_recipe_instructions(self):
        res = self.run_check(
            "hyprland-plugin-hyprbars 0.56.2-3.1\nvisual-studio-code-bin 1.147.0-1\n",
            yay_output="visual-studio-code-bin 1.147.0-1 -> 1.148.0-1\n",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("visual-studio-code-bin 1.147.0-1 -> 1.148.0-1", res.stdout)
        self.assertIn("Installed foreign/local packages (pacman -Qm):", res.stderr)
        self.assertIn("hyprland-plugin-hyprbars 0.56.2-3.1", res.stderr)
        self.assertIn("Review frozen recipes in ~/pkgs", res.stderr)
        self.assertIn("never run unattended AUR upgrades", res.stderr)

    def test_check_without_yay_lists_foreign_packages_and_frozen_instructions(self):
        res = self.run_check("hyprland-plugin-hyprbars 0.57.2-1.1\n", yay_output=None)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("hyprland-plugin-hyprbars 0.57.2-1.1", res.stderr)
        self.assertIn("Review frozen recipes in ~/pkgs", res.stderr)

    def test_check_reports_explicit_none_when_no_foreign_packages_installed(self):
        res = self.run_check("", yay_output="")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("No foreign or AUR packages installed.", res.stderr)
