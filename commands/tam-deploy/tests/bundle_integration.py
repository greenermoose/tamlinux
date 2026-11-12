#!/usr/bin/env python3
"""Cross-layer temporary-root proof; always enter private PID/private proc."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_recovery import TransactionRecovery
from test_deploy import deploy

TOOLS = Path(__file__).resolve().parents[4] / 'tamlinux-tools'
sys.path.insert(0, str(TOOLS / 'tests/tam-bundle'))
from pid_namespace import enter_namespace, require_namespace
BIN = Path(os.environ.get('TAM_BUNDLE_BIN', TOOLS / 'bin/tam-bundle-test')).resolve()


class Interrupted(BaseException):
    pass


class BundleMigration(TransactionRecovery):
    def setUp(self):
        require_namespace()
        super().setUp()
        self.app.transaction_file.unlink()
        self.app._requested_transaction = 'bundle-migration'
        self.app.host_pin = self.config / 'hosts/fixture/state/assembly'
        self.app.host_pin.parent.mkdir(parents=True)
        self.app.host_pin.write_text(self.packages_main + '\n')
        self.enterContext(patch.object(self.app, 'components', side_effect=lambda rev:
            {'tamlinux': self.tamlinux_main if rev == self.packages_main else self.tamlinux_new}))
        self.enterContext(patch.object(self.app, 'recovery_snapshot', side_effect=lambda *args:
            deploy.Deployment.recovery_snapshot(self.app, *args)))
        self.enterContext(patch.object(self.app, 'check_clean'))
        self.enterContext(patch.object(self.app, 'require_unlocked_sessions'))
        self.enterContext(patch.object(self.app, 'update_bom', return_value=[]))
        self.stripped = self.root / 'bundle-generation'
        (self.stripped / 'home-files').mkdir(parents=True)
        (self.stripped / 'home-path/bin').mkdir(parents=True)
        (self.stripped / 'home-path/bin/own-tool').write_text('unrelated package')
        (self.stripped / 'activate').write_text('#!/bin/sh\nset -eu\nln -sfn "' +
            str(self.stripped) + '" "' + str(self.app.profile) + '"\n')
        (self.stripped / 'activate').chmod(0o755)
        self.enterContext(patch.object(self.app, 'build_bundle_profile', return_value=str(self.stripped)))
        self.native_archive = self.root / 'native.pkg.tar.zst'
        self.native_archive.write_bytes(b'native recovery fixture')
        self.native_recovery = {'format': 1, 'host': self.app.hostname, 'package': 'tamlinux-native',
            'version': '1.0-1', 'archive': str(self.native_archive),
            'sha256': hashlib.sha256(self.native_archive.read_bytes()).hexdigest()}
        (self.config / 'system/bundle-nix-recovery.json').write_text(json.dumps(self.native_recovery))
        actual_command = deploy.command
        def command(*args, **kwargs):
            if args[:2] in (('/usr/bin/pacman', '-Qp'), ('/usr/bin/pacman', '-Q')):
                return 'tamlinux-native 1.0-1'
            return actual_command(*args, **kwargs)
        self.enterContext(patch.object(deploy, 'command', side_effect=command))
        source = self.root / 'personal-bashrc'
        source.write_text('personal before preparation\n')
        self.personal = source
        endpoint = self.old / 'home-files/.bashrc';endpoint.symlink_to(source)
        (self.app.home / '.bashrc').symlink_to(endpoint)
        startup = self.old / 'home-files/.config/tamlinux/session/hyprland.lua'
        startup.parent.mkdir(parents=True)
        startup.write_text(f'dofile("{self.app.home}/.local/share/tamlinux/shell/../session/entry.lua")\n')
        live_start = self.app.home / '.config/tamlinux/session/hyprland.lua'
        live_start.parent.mkdir(parents=True)
        live_start.symlink_to(startup)
        # Model HM refusing real files, rather than ln silently overwriting them.
        activation = self.old / 'activate'
        old = activation.read_text()
        checks = []
        for relative in ('.bashrc', '.config/tamlinux/session/hyprland.lua'):
            live = self.app.home / relative
            checks.append(f'[ ! -e "{live}" ] || [ -L "{live}" ] || exit 19')
        activation.write_text(old.replace('set -eu\n', 'set -eu\n' + '\n'.join(checks) + '\n'))
        self.rootfs = self.root / 'rootfs'
        self.enterContext(patch.object(self.app, 'bundle_current_path',
                                      return_value=self.rootfs / 'usr/lib/tamlinux/current'))
        profile = self.rootfs / 'usr/share/tamlinux/rootstock'
        profile.mkdir(parents=True)
        (profile / 'profile').write_text('format 1\nallow usr/bin\n'
            'user-step user-units-reload required usr/share/tamlinux/rootstock/reload\n')
        (profile / 'reload').write_text('#!/bin/sh\nexit 0\n')
        (profile / 'reload').chmod(0o755)
        (profile / 'id').write_text('arch-systemd\n')
        database = self.rootfs / 'var/lib/pacman/local';database.mkdir(parents=True)
        (database / 'ALPM_DB_VERSION').write_text('9\n')
        self.product = self.root / 'product'
        for name in ('tam', 'tam-file-select'):
            path = self.product / 'placed/usr/bin' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#!/bin/sh\necho bundle\n');path.chmod(0o755)
        defaults = self.product / 'tree/defaults/home'
        defaults.mkdir(parents=True)
        (defaults / '.bashrc').write_text('product bash\n')
        path = defaults / '.config/tamlinux/session/hyprland.lua';path.parent.mkdir(parents=True)
        path.write_text('dofile("/usr/lib/tamlinux/current/share/tamlinux/session/entry.lua")\n')
        (self.product / 'SETTINGS').write_text('format 1\ncommon .bashrc\ncommon .config/tamlinux/session/hyprland.lua\n')
        self.raw('seal', self.product, '--format', '2', '--name', 'tamlinux', '--version', '9.8.7',
                 '--source', 'tamlinux ' + self.tamlinux_new, '--source', 'packaging ' + 'a' * 40)
        fields = dict(line.split(' ', 1) for line in (self.product / 'BUNDLE').read_text().splitlines()
                      if line.split(' ', 1)[0] in ('hash', 'name', 'version'))
        self.bundle_id = 'tamlinux-9.8.7-' + fields['hash'][7:19]
        archive = self.root / 'product.tbundle';self.raw('pack', self.product, '-o', archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        cache = self.root / 'cache';self.enterContext(patch.dict(os.environ, {'XDG_CACHE_HOME': str(cache)}))
        cached = cache / 'tamlinux/bundles' / (digest + '.tbundle');cached.parent.mkdir(parents=True)
        shutil.copyfile(archive, cached)
        self.delivery = {'format': 1, 'backend': 'tam-bundle', 'version': '9.8.7',
            'recipeAssembly': 'a' * 40, 'components': {'tamlinux': self.tamlinux_new},
            'minimumTool': '0.12.0', 'rootstock': 'arch-systemd',
            'artifact': {'bundleId': self.bundle_id, 'bundleHash': fields['hash'],
                         'name': self.bundle_id + '.tbundle', 'sha256': digest}}
        self.enterContext(patch.object(self.app, 'bundle_delivery', side_effect=lambda revision:
            self.delivery if revision == self.packages_new else None))
        self.enterContext(patch.object(self.app, 'bundle_command', side_effect=self.bundle))
        self.privileged = self.enterContext(patch.object(self.app, 'bundle_privileged', side_effect=self.bundle))
        self.enterContext(patch.object(self.app, 'dormant_bundle_hash', return_value=None))
        real_run = subprocess.run
        def run(args, *pos, **kw):
            if args == ['/usr/bin/tam-bundle', '--root', '/', 'status']:
                args = [str(BIN), '--root', str(self.rootfs), 'status']
            return real_run(args, *pos, **kw)
        self.enterContext(patch.object(deploy.subprocess, 'run', side_effect=run))

    def raw(self, *args):
        result = subprocess.run([str(BIN), *map(str, args)], capture_output=True, text=True)
        if result.returncode:
            self.fail(f'{result.args}: {result.returncode}\n{result.stdout}\n{result.stderr}')
        self.assertNotIn('ERROR: AddressSanitizer', result.stderr)
        self.assertNotIn('runtime error:', result.stderr)
        return result.stdout.strip()

    def bundle(self, *args):
        if args == ('--version',):
            return self.raw(*args)
        if args[:2] == ('--root', '/'):
            args = args[2:]
        return self.raw('--root', self.rootfs, *args)

    def prepare_bundle(self):
        self.app.prepare_bundle(self.packages_new, self.delivery['components'], 'test')
        return json.loads(self.app.transaction_file.read_text())['id']

    def test_exact_artifact_console_activation_and_saved_nix_return(self):
        identifier = self.prepare_bundle()
        self.assertEqual(self.app.locked(), self.packages_main)
        self.assertTrue((self.app.home / '.bashrc').is_symlink())
        self.privileged.assert_not_called()
        self.personal.write_text('edit after preparation\n')
        with patch.object(deploy, 'Deployment', return_value=self.app):
            self.assertEqual(deploy.main(['activate-bundle', identifier]), 0)
        self.assertEqual((self.app.home / '.bashrc').read_text(), 'edit after preparation\n')
        startup = self.app.home / '.config/tamlinux/session/hyprland.lua'
        self.assertFalse(startup.is_symlink())
        self.assertIn('/usr/lib/tamlinux/current/', startup.read_text())
        self.assertFalse(os.path.lexists(self.app.home / '.local/bin/tam'))
        self.assertEqual(self.app.locked(), self.packages_new)
        self.assertFalse(self.app.state_report()['problems'])
        (self.app.home / '.bashrc').write_text('later bundle edit\n')
        with patch.object(deploy, 'Deployment', return_value=self.app):
            self.assertEqual(deploy.main(['recover', identifier]), 0)
        self.assertEqual(self.app.locked(), self.packages_main)
        self.assertTrue((self.app.home / '.bashrc').is_symlink())
        self.assertEqual(self.personal.read_text(), 'edit after preparation\n')
        self.assertEqual(self.app.generation(), str(self.old))
        returned = self.app.migration(identifier).directory / 'returned'
        self.assertTrue(any(path.is_file() and path.read_text() == 'later bundle edit\n'
                            for path in returned.iterdir()))
        self.app.return_bundle_to_nix(identifier)

    def test_activation_retry_at_each_deployment_phase(self):
        # Individual fixtures below are fresh; durable system/settings tests
        # separately enumerate the C engine's internal transitions.
        for phase in ('bundle-converting', 'bundle-preparing-system', 'bundle-applying', 'bundle-recording'):
            fixture = BundleMigration();fixture.setUp()
            try:
                identifier = fixture.prepare_bundle()
                real = fixture.app.transaction
                def interrupt(**fields):
                    real(**fields)
                    if fields.get('phase') == phase:
                        raise Interrupted()
                with patch.object(fixture.app, 'transaction', side_effect=interrupt):
                    with self.assertRaises(Interrupted):fixture.app.activate_bundle(identifier)
                fixture.app.activate_bundle(identifier)
                fixture.app.return_bundle_to_nix(identifier)
                self.assertEqual(fixture.app.generation(), str(fixture.old))
            finally:
                fixture.doCleanups()

    def test_stale_identity_and_live_graphics_refuse_before_mutation(self):
        identifier = self.prepare_bundle()
        with self.assertRaises(deploy.DeploymentError):self.app.activate_bundle('another-transaction')
        with patch.object(self.app, 'graphical_active', return_value=True):
            with self.assertRaises(deploy.DeploymentError):self.app.activate_bundle(identifier)
        self.privileged.assert_not_called()
        self.assertTrue((self.app.home / '.bashrc').is_symlink())

    def test_native_restore_retains_its_separate_gate_and_retries_without_new_tool(self):
        identifier = self.prepare_bundle();self.app.activate_bundle(identifier)
        with patch.object(self.app, 'require_nix_native', side_effect=deploy.DeploymentError('native approval pending')):
            with self.assertRaisesRegex(deploy.DeploymentError, 'native approval'):
                self.app.return_bundle_to_nix(identifier)
        tx = json.loads(self.app.transaction_file.read_text())
        self.assertTrue(tx['bundleDetached'])
        self.assertEqual(tx['phase'], 'bundle-returning-native')
        with patch.object(self.app, 'bundle_system_state', side_effect=AssertionError('new tool no longer installed')):
            self.app.return_bundle_to_nix(identifier)
        self.assertEqual(self.app.generation(), str(self.old))

    def test_missing_or_corrupt_native_archive_stops_before_preparation(self):
        self.native_archive.write_bytes(b'changed')
        with self.assertRaisesRegex(deploy.DeploymentError, 'recorded hash'):
            self.prepare_bundle()
        self.privileged.assert_not_called()
        self.assertFalse(self.app.transaction_file.exists())

    def test_profile_that_still_supplies_product_commands_refuses(self):
        (self.stripped / 'home-path/bin/tam').write_text('stale product')
        with self.assertRaisesRegex(deploy.DeploymentError, 'still supplies tam'):
            self.app.verify_bundle_profile(str(self.stripped), {'entries': []})


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(BundleMigration(name) for name in BundleMigration.__dict__ if name.startswith('test_'))


if __name__ == '__main__':
    enter_namespace(__file__)
    unittest.main(verbosity=2)
