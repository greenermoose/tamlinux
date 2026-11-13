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
        self.deliveries = {self.packages_new: self.delivery}
        self.enterContext(patch.object(self.app, 'bundle_delivery', side_effect=self.deliveries.get))
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

    def next_delivery(self, revision, version):
        product = self.root / ('product-' + version)
        shutil.copytree(self.product, product)
        (product / 'BUNDLE').unlink();(product / 'MANIFEST').unlink()
        (product / 'placed/usr/bin/tam').write_text('#!/bin/sh\necho ' + version + '\n')
        self.raw('seal', product, '--format', '2', '--name', 'tamlinux', '--version', version,
                 '--source', 'tamlinux ' + self.tamlinux_new, '--source', 'packaging ' + 'a' * 40)
        fields = dict(line.split(' ', 1) for line in (product / 'BUNDLE').read_text().splitlines()
                      if line.startswith(('hash ', 'version ')))
        identifier = 'tamlinux-' + version + '-' + fields['hash'][7:19]
        archive = self.root / (version + '.tbundle');self.raw('pack', product, '-o', archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        shutil.copyfile(archive, Path(os.environ['XDG_CACHE_HOME']) / 'tamlinux/bundles' / (digest + '.tbundle'))
        delivery = dict(self.delivery, version=version,
            artifact={'bundleId': identifier, 'bundleHash': fields['hash'],
                      'name': identifier + '.tbundle', 'sha256': digest})
        self.deliveries[revision] = delivery
        return delivery

    def test_later_bundle_update_and_exact_back_then_nix_return(self):
        initial = self.prepare_bundle();self.app.activate_bundle(initial)
        revision = 'f' * 40
        delivery = self.next_delivery(revision, '9.8.8')
        self.app._requested_transaction = 'second-delivery'
        (self.app.home / '.bashrc').write_text('settings before second delivery\n')
        self.app.prepare_bundle(revision, delivery['components'], 'test')
        self.app.activate_bundle('second-delivery')
        self.assertEqual(self.app.locked(), revision)
        self.assertFalse(self.app.state_report()['problems'])
        (self.app.home / '.bashrc').write_text('settings after second delivery\n')
        self.app.back()
        self.assertEqual(self.app.locked(), self.packages_new)
        self.assertEqual((self.app.home / '.bashrc').read_text(), 'settings before second delivery\n')
        self.assertFalse(self.app.state_report()['problems'])
        self.app.back()
        self.assertEqual(self.app.locked(), self.packages_main)
        self.assertEqual(self.app.generation(), str(self.old))

    def test_later_update_can_return_directly_to_original_nix_generation(self):
        initial = self.prepare_bundle();self.app.activate_bundle(initial)
        revision = 'f' * 40;delivery = self.next_delivery(revision, '9.8.8')
        self.app._requested_transaction = 'second-delivery'
        self.app.prepare_bundle(revision, delivery['components'], 'test')
        self.app.activate_bundle('second-delivery')
        self.app.return_bundle_to_nix('second-delivery')
        self.assertEqual(self.app.generation(), str(self.old))
        self.assertEqual(self.app.locked(), self.packages_main)
        self.assertTrue((self.app.home / '.bashrc').is_symlink())

    def fresh_account(self):
        # Keep only the registered consumer/host, rootstock and carried bundle.
        self.app.profile.unlink();self.app.state_file.unlink()
        for path in sorted((self.app.home / '.local/bin').iterdir()):path.unlink()
        for relative in ('.bashrc', '.local/share/tamlinux/shell', '.local/share/tamlinux/shell-revision',
                         '.config/systemd/user/tamlinux-shell.service', '.config/tamlinux/session/hyprland.lua'):
            (self.app.home / relative).unlink()

    def test_first_account_bundle_without_nix_profile_and_undo(self):
        self.fresh_account()
        (self.app.home / '.bashrc').write_text('account before bundle\n')
        self.app.prepare_bundle_init(self.packages_new, self.delivery['components'], 'test')
        identifier = json.loads(self.app.transaction_file.read_text())['id']
        self.assertFalse(self.app.profile.exists())
        self.app.activate_bundle(identifier)
        self.assertFalse(self.app.state_report()['problems'])
        (self.app.home / '.bashrc').write_text('account after bundle\n')
        self.app.recover(identifier)
        self.assertEqual((self.app.home / '.bashrc').read_text(), 'account before bundle\n')
        self.assertFalse(self.app.state_file.exists())
        self.assertEqual(self.app.bundle_system_state()['live'], '-')

    def test_nix_references_added_after_prepare_refuse_before_conversion(self):
        identifier = self.prepare_bundle()
        self.personal.write_text('source /nix/store/old-path/setup\n')
        with self.assertRaisesRegex(deploy.DeploymentError, 'explicit native-path migration'):
            self.app.activate_bundle(identifier)
        self.privileged.assert_not_called()
        self.assertTrue((self.app.home / '.bashrc').is_symlink())

    def test_canceled_prepared_update_keeps_old_session_ready_and_allows_another_update(self):
        self.app.activate_bundle(self.prepare_bundle())
        revision = 'f' * 40;delivery = self.next_delivery(revision, '9.8.8')
        self.app._requested_transaction = 'second-delivery'
        self.app.prepare_bundle(revision, delivery['components'], 'test')
        actual = self.app.bundle_command
        def stop(*args):
            result = actual(*args)
            if args == ('prepare-settings',):raise Interrupted()
            return result
        with patch.object(self.app, 'bundle_command', side_effect=stop):
            with self.assertRaises(Interrupted):self.app.activate_bundle('second-delivery')
        self.app.recover('second-delivery')
        self.assertFalse(self.app.state_report()['problems'])
        self.app._requested_transaction = 'third-delivery'
        self.app.prepare_bundle(revision, delivery['components'], 'test')
        self.app.activate_bundle('third-delivery')
        self.assertFalse(self.app.state_report()['problems'])

    def test_update_recovery_retries_after_real_system_install_and_apply(self):
        for action in ('install', 'apply'):
            fixture = BundleMigration();fixture.setUp()
            try:
                fixture.app.activate_bundle(fixture.prepare_bundle())
                revision = 'f' * 40;delivery = fixture.next_delivery(revision, '9.8.8')
                fixture.app._requested_transaction = 'second-delivery'
                (fixture.app.home / '.bashrc').write_text('saved prior settings\n')
                fixture.app.prepare_bundle(revision, delivery['components'], 'test')
                fixture.app.activate_bundle('second-delivery')
                actual = fixture.app.bundle_privileged
                def stop(*args):
                    result = actual(*args)
                    if args[0] == action:raise Interrupted()
                    return result
                with patch.object(fixture.app, 'bundle_privileged', side_effect=stop):
                    with self.assertRaises(Interrupted):fixture.app.recover('second-delivery')
                fixture.app.recover('second-delivery')
                self.assertFalse(fixture.app.state_report()['problems'])
                self.assertEqual((fixture.app.home / '.bashrc').read_text(),'saved prior settings\n')
            finally:fixture.doCleanups()

    def test_first_account_undo_restores_absence_without_nix(self):
        self.fresh_account()
        self.app.prepare_bundle_init(self.packages_new, self.delivery['components'], 'test')
        identifier = json.loads(self.app.transaction_file.read_text())['id']
        self.app.activate_bundle(identifier)
        self.assertTrue((self.app.home / '.bashrc').is_file())
        self.app.recover(identifier)
        self.assertFalse(os.path.lexists(self.app.home / '.bashrc'))
        self.assertFalse(self.app.profile.exists())

    def test_short_console_helpers_are_bound_checked_and_preserve_foreign_scripts(self):
        identifier = self.prepare_bundle()
        self.app.console_helpers(identifier)
        for name in ('bundle-on.sh', 'bundle-undo.sh'):
            path = self.app.home / name
            subprocess.run(['sh', '-n', str(path)],check=True)
            self.assertIn(identifier, path.read_text())
            self.assertIn('/usr/bin/sha256sum', path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        self.app.console_helpers(identifier)
        path = self.app.home / 'bundle-undo.sh';path.write_text('personal script\n')
        with self.assertRaisesRegex(deploy.DeploymentError,'another step'):
            self.app.console_helpers(identifier)
        self.assertEqual(path.read_text(),'personal script\n')

    def _make_ux_delivery(self):
        product = self.root / 'product-ux'
        shutil.copytree(self.product, product)
        for name in ('tam', 'tam-file-select'):
            p = product / 'placed/usr/bin' / name
            p.chmod(0o755)
        (product / 'BUNDLE').unlink()
        (product / 'MANIFEST').unlink()
        settings_lines = [
            'format 1',
            'common .bashrc',
            'common .config/tamlinux/session/hyprland.lua',
            'common .config/tamlinux/backgrounds/',
            'common .config/tamlinux/clock/',
            'common .config/tamlinux/defaults/',
            'common .config/tamlinux/macros.json',
            'common .config/tamlinux/tam-edit/',
            'common .local/state/tamlinux/shell.toml',
            'common .local/state/tamlinux/current/theme.name',
            'common .local/state/tamlinux/current/background.selection',
            'common .local/state/tamlinux/defaults/editor',
            'common .local/state/tamlinux/settings/weather.json',
            'common .local/state/tamlinux/settings/tides.json',
            'common .local/state/tamlinux/toggles/',
            'host .local/state/tamlinux/desktop-mode',
            'host .local/state/tamlinux/toggles/hypr/',
            'common .local/state/tamlinux/workspace-layouts/',
        ]
        (product / 'SETTINGS').write_text('\n'.join(settings_lines) + '\n')
        self.raw('seal', product, '--format', '2', '--name', 'tamlinux', '--version', '9.8.8',
                 '--source', 'tamlinux ' + self.tamlinux_new, '--source', 'packaging ' + 'a' * 40)
        fields = dict(line.split(' ', 1) for line in (product / 'BUNDLE').read_text().splitlines()
                      if line.split(' ', 1)[0] in ('hash', 'name', 'version'))
        bundle_id = 'tamlinux-9.8.8-' + fields['hash'][7:19]
        archive = self.root / 'product-ux.tbundle'; self.raw('pack', product, '-o', archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        cached = Path(os.environ['XDG_CACHE_HOME']) / 'tamlinux/bundles' / (digest + '.tbundle')
        shutil.copyfile(archive, cached)
        return {'format': 1, 'backend': 'tam-bundle', 'version': '9.8.8',
                'recipeAssembly': 'a' * 40, 'components': {'tamlinux': self.tamlinux_new},
                'minimumTool': '0.13.0', 'rootstock': 'arch-systemd',
                'artifact': {'bundleId': bundle_id, 'bundleHash': fields['hash'],
                             'name': bundle_id + '.tbundle', 'sha256': digest}}

    def test_uncaptured_active_desktop_state_stops_preparation(self):
        state = self.app.home / '.local/state/tamlinux/current/theme.name'
        state.parent.mkdir(parents=True)
        state.write_text('personal-theme\n')
        with self.assertRaisesRegex(deploy.DeploymentError, 'portable capture support'):
            self.prepare_bundle()
        self.privileged.assert_not_called()
        self.assertTrue((self.app.home / '.bashrc').is_symlink())

    def test_portable_active_desktop_state_migrates_and_regenerates(self):
        self.deliveries[self.packages_new] = self._make_ux_delivery()
        desktop_root = Path(__file__).resolve().parents[3] / 'desktop'
        engine = desktop_root / 'theme/engine.py'
        assets = desktop_root / 'assets'
        helper_dir = self.root / 'theme-bin'; helper_dir.mkdir()
        for cmd in ('tam-theme-set-templates', 'tam-theme-color', 'tam-theme-colors-from-alacritty'):
            (helper_dir / cmd).symlink_to(desktop_root.parent / 'commands' / cmd / cmd)
        init_script = helper_dir / 'tam-theme-init'
        init_script.write_text(f'#!/bin/sh\nexec python3 "{engine}" initialize "$@"\n')
        init_script.chmod(0o755)
        self.enterContext(patch.dict(os.environ, {
            'TAMLINUX_THEME_INIT': str(init_script),
            'TAMLINUX_ASSETS_DIR': str(assets),
            'PATH': str(helper_dir) + ':' + os.environ['PATH'],
        }))
        home = self.app.home
        state = home / '.local/state/tamlinux'
        (state / 'theme-generations/tokyo-night.oldgen/backgrounds').mkdir(parents=True)
        gen_bg = state / 'theme-generations/tokyo-night.oldgen/backgrounds/0-winding-road.jpg'
        gen_bg.write_bytes(b'\xff\xd8\xff\xe0oldgen-bg')
        (state / 'current').mkdir(parents=True)
        (state / 'current/theme.name').write_text('tokyo-night\n')
        (state / 'current/background').symlink_to(gen_bg)
        (state / 'current/theme').mkdir()
        (state / 'current/theme/colors.toml').write_text('background = "#1a1b26"\n')
        (state / 'shell.toml').write_text('[font]\nbase-size = 13\n')
        (state / 'defaults').mkdir(); (state / 'defaults/editor').write_text('helix\n')
        (state / 'settings').mkdir()
        (state / 'settings/weather.json').write_text('{"city":"Boston"}\n')
        (state / 'settings/tides.json').write_text('{"station":"8443970"}\n')
        (state / 'toggles/hypr').mkdir(parents=True)
        (state / 'toggles/bar-off').write_text('1\n')
        (state / 'toggles/hypr/touchpad-disabled-name').write_text('tp0\n')
        (state / 'desktop-mode').write_text('auto\n')
        (state / 'desktop-current').write_text('1\n')
        (state / 'desktop-monitors').write_text('{"mode":"auto"}\n')
        (state / 'workspace-layouts').mkdir(); (state / 'workspace-layouts/1.lua').write_text('hl.workspace_rule({})\n')
        (home / '.config/tamlinux/clock').mkdir(parents=True); (home / '.config/tamlinux/clock/local.ics').write_text('CAL\n')
        (home / '.config/tamlinux/defaults').mkdir(parents=True); (home / '.config/tamlinux/defaults/agent').write_text('claude\n')
        (home / '.config/tamlinux/macros.json').write_text('{}\n')
        identifier = self.prepare_bundle()
        self.app.activate_bundle(identifier)
        self.assertTrue((state / 'current/background.selection').is_file())
        sel = json.loads((state / 'current/background.selection').read_text())
        self.assertEqual(sel, {'format': 1, 'kind': 'theme', 'theme': 'tokyo-night', 'file': '0-winding-road.jpg'})
        self.assertTrue((state / 'current/theme/colors.toml').is_file())
        self.assertTrue((state / 'current/background').resolve().is_file())
        self.assertNotIn('oldgen', (state / 'current/background').resolve().as_posix())
        self.assertEqual((state / 'shell.toml').read_text(), '[font]\nbase-size = 13\n')
        self.assertEqual((home / '.config/tamlinux/clock/local.ics').read_text(), 'CAL\n')
        self.assertEqual((state / 'desktop-current').read_text(), '1\n')
        # Broken background symlink stops migration before touching files.
        (state / 'current/background').unlink()
        (state / 'current/background').symlink_to(self.root / 'missing.jpg')
        audited_paths = [line.split()[1] for line in (self.root / 'product-ux/SETTINGS').read_text().splitlines()[1:]]
        with self.assertRaisesRegex(deploy.DeploymentError, 'dangling or unreadable'):
            self.app.audit_bundle_settings(audited_paths)

    def test_bundle_native_recovery_prefers_host_record_and_falls_back_to_system(self):
        self.assertEqual(self.app.bundle_native_recovery()['sha256'], self.native_recovery['sha256'])
        host_archive = self.root / 'host-native.pkg.tar.zst'
        host_archive.write_bytes(b'host-specific recovery archive')
        host_record = {
            'format': 1, 'host': self.app.hostname, 'package': 'tamlinux-native',
            'version': '1.0-1', 'archive': str(host_archive),
            'sha256': hashlib.sha256(host_archive.read_bytes()).hexdigest(),
        }
        host_path = self.config / 'hosts' / self.app.hostname / 'bundle-nix-recovery.json'
        host_path.parent.mkdir(parents=True, exist_ok=True)
        host_path.write_text(json.dumps(host_record))
        self.assertEqual(self.app.bundle_native_recovery()['archive'], str(host_archive))
        self.assertEqual(self.app.bundle_native_recovery()['sha256'], host_record['sha256'])
        # Symlink at host path is rejected instead of falling back to system/.
        target = self.root / 'linked-recovery.json'; target.write_text(json.dumps(host_record))
        host_path.unlink(); host_path.symlink_to(target)
        with self.assertRaisesRegex(deploy.DeploymentError, 'hosts/<hostname>/bundle-nix-recovery.json'):
            self.app.bundle_native_recovery()
        host_path.unlink()
        (self.config / 'system/bundle-nix-recovery.json').unlink()
        with self.assertRaisesRegex(deploy.DeploymentError, 'hosts/<hostname>/bundle-nix-recovery.json'):
            self.app.bundle_native_recovery()


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(BundleMigration(name) for name in BundleMigration.__dict__ if name.startswith('test_'))


if __name__ == '__main__':
    enter_namespace(__file__)
    unittest.main(verbosity=2)
