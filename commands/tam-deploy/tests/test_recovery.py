"""Recover isolated generations without Nix, component clones or a network."""
import hashlib
import json
import multiprocessing
import os
import shlex
import unittest
from pathlib import Path
from unittest.mock import patch

from test_deploy import Fixture, deploy


def hold_deploy_lock(config, ready, release):
    with deploy.Deployment().mutation_lock():
        ready.set()
        release.wait(10)


class TransactionRecovery(Fixture):
    def setUp(self):
        super().setUp()
        self.old, self.new = self.root / 'old-generation', self.root / 'new-generation'
        self.app.shell_link = self.app.home / '.local/share/tamlinux/shell'
        self.app.revision_file = self.app.home / '.local/share/tamlinux/shell-revision'
        self.app.plugins_dir = self.app.home / '.config/tamlinux/plugins'
        self.app.bin_dir = self.app.home / '.local/bin'
        self.app.profile.parent.mkdir(parents=True)
        self.outputs = {}
        for gen, revision in ((self.old, self.tamlinux_main), (self.new, self.tamlinux_new)):
            files = gen / 'home-files'
            package = self.root / (gen.name + '-package')
            shell = package / 'share/tamlinux/shell'
            shell.mkdir(parents=True)
            (package / 'share/tamlinux/source-revision').write_text(revision)
            (package / 'bin').mkdir()
            for command in ('tam', 'tam-file-select'):
                (package / 'bin' / command).write_text('fixture')
            service = package / 'tamlinux-shell.service'
            service.write_text('fixture unit')
            targets = {'.local/share/tamlinux/shell': shell,
                       '.local/share/tamlinux/shell-revision': package / 'share/tamlinux/source-revision',
                       '.config/systemd/user/tamlinux-shell.service': service,
                       '.local/bin/tam': package / 'bin/tam',
                       '.local/bin/tam-file-select': package / 'bin/tam-file-select'}
            lines = ['#!/bin/sh', 'set -eu', f'ln -sfn {shlex.quote(str(gen))} {shlex.quote(str(self.app.profile))}']
            for relative, target in targets.items():
                path = files / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target)
                live = self.app.home / relative
                live.parent.mkdir(parents=True, exist_ok=True)
                lines.append(f'ln -sfn {shlex.quote(str(path))} {shlex.quote(str(live))}')
            (gen / 'activate').write_text('\n'.join(lines) + '\n')
            (gen / 'activate').chmod(0o755)
            self.outputs[str(gen)] = {'shell': str(package), 'commands': str(package), 'plugins': str(package),
                                     'tam': str(package), 'tools': str(package), 'pluginIds': [], 'commandNames': [],
                                     'selectionRecord': False, 'manWrapper': False, 'features': {}}
        deploy.command(str(self.old / 'activate'))
        self.app.save_state({'generation': str(self.old), 'packages': self.packages_main,
                             'components': {'tamlinux': self.tamlinux_main}, 'stage': 'follow'})
        self.before = self.app.lock.read_bytes()
        self.app._outputs[self.packages_main] = self.outputs[str(self.old)]
        self.snapshot = deploy.Deployment.recovery_snapshot(self.app, str(self.old), self.packages_main, self.before)
        self.identifier = 'transaction-one'
        self.prepare()
        self.enterContext(patch.object(self.app, 'runtime_state', return_value={'graphical': False, 'revision': None}))
        self.enterContext(patch.object(self.app, 'graphical_active', return_value=False))
        self.enterContext(patch.object(self.app, 'activation_validators'))
        self.enterContext(patch.object(self.app, 'record'))
        self.enterContext(patch.object(self.app, 'git', side_effect=AssertionError('component checkout accessed')))
        self.enterContext(patch.object(self.app, 'components', side_effect=AssertionError('component metadata rediscovered')))
        real_match = deploy.re.fullmatch
        self.enterContext(patch.object(deploy.re, 'fullmatch', side_effect=lambda pattern, value, *args:
            True if pattern == r'/nix/store/[a-z0-9]{32}-home-manager-generation' and value == str(self.old)
            else real_match(pattern, value, *args)))

    def prepare(self):
        self.app._requested_transaction = self.identifier
        self.app.transaction(phase='prepared', baselineGeneration=str(self.old), baselineAssembly=self.packages_main,
                             targetAssembly=self.packages_new, targetGeneration=str(self.new), recovery=self.snapshot)

    def partial(self):
        deploy.command(str(self.new / 'activate'))
        self.write_lock(self.packages_new, {})
        self.app.transaction(phase='partial', targetPinSha256=hashlib.sha256(self.app.lock.read_bytes()).hexdigest())
        self.app._outputs.clear()  # Simulate a fresh process with no evaluated outputs.

    def test_offline_recovery_uses_snapshot_and_verifies_real_links(self):
        self.partial()
        self.app.recover(self.identifier)
        self.assertEqual(self.app.generation(), str(self.old))
        self.assertEqual(self.app.lock.read_bytes(), self.before)
        self.assertEqual(self.app.read_state(), self.snapshot['state'])
        self.assertEqual(json.loads(self.app.transaction_file.read_text())['phase'], 'recovered')
        self.assertEqual(self.app.verify(self.snapshot['components'], self.packages_main), [])
        history = self.app.state_file.parent / 'deploy-transactions' / (self.identifier + '.json')
        self.assertEqual(json.loads(history.read_text()), json.loads(self.app.transaction_file.read_text()))

    def test_already_restored_transaction_does_not_activate_again(self):
        self.app.transaction(phase='recovered')
        with patch.object(deploy, 'command', side_effect=AssertionError('unexpected activation')):
            self.app.recover(self.identifier)
            self.app.recover(self.identifier)
        self.assertEqual(self.app.generation(), str(self.old))

    def test_missing_generation_refused_before_mutation(self):
        self.partial()
        (self.old / 'activate').unlink()
        with self.assertRaisesRegex(deploy.DeploymentError, 'unavailable'):
            self.app.recover(self.identifier)
        self.assertEqual(self.app.generation(), str(self.new))
        self.assertEqual(self.app.locked(), self.packages_new)

    def test_stale_transaction_and_foreign_host_refused(self):
        self.partial()
        for changes in ({'id': 'newer'}, {'host': 'another-host'}, {'user': 'other-user'}, {'config': '/foreign'}):
            original = json.loads(self.app.transaction_file.read_text())
            data = {**original, **changes}
            self.app.transaction_file.write_text(json.dumps(data))
            with self.subTest(changes=changes), self.assertRaisesRegex(deploy.DeploymentError, 'stale or foreign'):
                self.app.recover(self.identifier)
            self.app.transaction_file.write_text(json.dumps(original))
        self.assertEqual(self.app.generation(), str(self.new))

    def test_later_pin_edits_and_unrelated_generations_are_preserved(self):
        self.partial()
        self.app.lock.write_text(self.app.lock.read_text() + '\n')
        with self.assertRaisesRegex(deploy.DeploymentError, 'pin was edited'):
            self.app.recover(self.identifier)
        self.assertEqual(self.app.generation(), str(self.new))

    def test_failed_endpoint_verification_is_not_reported_recovered(self):
        self.partial()
        (self.old / 'home-files/.local/bin/tam').unlink()
        with self.assertRaisesRegex(deploy.DeploymentError, 'recovery incomplete'):
            self.app.recover(self.identifier)
        tx = json.loads(self.app.transaction_file.read_text())
        self.assertEqual(tx['phase'], 'partial')
        self.assertIn('missing', tx['recoveryError'])

    def test_changed_baseline_token_refuses_before_fetch(self):
        baseline = self.app.baseline_token()
        self.app.lock.write_text(self.app.lock.read_text() + '\n')
        with self.assertRaisesRegex(deploy.DeploymentError, 'baseline changed'):
            self.app.follow('a' * 40, transaction_id='new-transaction', baseline_token=baseline)

    def test_legacy_snapshot_is_never_guessed(self):
        tx = json.loads(self.app.transaction_file.read_text())
        tx.pop('recovery')
        self.app.transaction_file.write_text(json.dumps(tx))
        with self.assertRaisesRegex(deploy.DeploymentError, 'legacy'):
            self.app.recover(self.identifier)

    def test_later_personal_edits_survive_and_conflict_is_reported(self):
        self.partial()
        path = self.app.home / '.manpath'
        path.write_text('later edit')
        backup = path.with_name('.manpath.pre-0.6.21')
        backup.write_text('original user file')
        self.app.transaction(backedUp=[{'path': str(path), 'backupPath': str(backup), 'relativePath': '.manpath'}])
        with self.assertRaisesRegex(deploy.DeploymentError, 'later user files preserved'):
            self.app.recover(self.identifier)
        self.assertEqual(path.read_text(), 'later edit')
        self.assertEqual(backup.read_text(), 'original user file')
        self.assertEqual(json.loads(self.app.transaction_file.read_text())['phase'], 'partial')

    def test_interrupted_backup_intent_restores_only_files_actually_moved(self):
        self.partial()
        path = self.app.home / '.manpath'
        backup = path.with_name('.manpath.pre-0.6.21')
        backup.write_text('original user file')
        self.app.transaction(backedUp=[{'path': str(path), 'backupPath': str(backup), 'relativePath': '.manpath'},
                                      {'path': str(self.app.home / '.untouched'),
                                       'backupPath': str(self.app.home / '.untouched.pre-0.6.21'),
                                       'relativePath': '.untouched'}])
        self.app.recover(self.identifier)
        self.assertEqual(path.read_text(), 'original user file')
        self.assertFalse(backup.exists())
        self.assertEqual(json.loads(self.app.transaction_file.read_text())['phase'], 'recovered')

    def test_parsers_require_complete_transaction_binding(self):
        args = ['follow', 'a' * 40, '--transaction', 'valid', '--expect-baseline', 'b' * 64]
        self.assertEqual(deploy.parse(args)[2], {'transaction_id': 'valid', 'baseline_token': 'b' * 64})
        self.assertEqual(deploy.parse(['recover', 'valid']), ('recover', ['valid'], {}))
        for args in (['recover', '../bad'], ['follow', 'a', '--transaction', 'valid'],
                     ['follow', 'a', '--transaction', '../bad', '--expect-baseline', 'b' * 64]):
            self.assertIsNone(deploy.parse(args))

    def test_all_cli_mutations_use_shared_deploy_lock(self):
        for argv in (['follow', 'a'], ['recover', 'valid'], ['back'], ['test'], ['run'],
                     ['init'], ['preflight', 'a' * 40], ['reconcile']):
            with self.subTest(argv=argv), self.app.mutation_lock(), patch.object(deploy, 'Deployment', return_value=self.app), \
                 patch.object(self.app, argv[0]) as action:
                self.assertEqual(deploy.main(argv), 1)
                action.assert_not_called()

    def test_two_processes_cannot_deploy_concurrently(self):
        ctx = multiprocessing.get_context('fork')
        ready, release = ctx.Event(), ctx.Event()
        process = ctx.Process(target=hold_deploy_lock, args=(str(self.config), ready, release))
        process.start()
        try:
            self.assertTrue(ready.wait(5))
            with self.assertRaisesRegex(deploy.DeploymentError, 'already in progress'):
                with self.app.mutation_lock():
                    self.fail('acquired twice')
        finally:
            release.set()
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join()
        self.assertEqual(process.exitcode, 0)


if __name__ == '__main__':
    unittest.main()
