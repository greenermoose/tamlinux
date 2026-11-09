"""Exercise failed upgrades and recovery using a local fake deployment backend."""
import contextlib
import io
import json
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_cli import load


def hold_lock(root, ready, release):
    receipt = load('receipt')
    with receipt.Store(Path(root)):
        ready.set()
        release.wait(10)


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.cli = load('cli')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = self.cli.receipt.Store(self.root / 'workstation-upgrade')
        self.backend = self.root / 'deploy-transaction.json'
        self.profile = {'hostname': 'review-host', 'username': 'alex', 'architecture': 'x86_64-linux',
                        'config': str(self.root / 'config'), 'assembly': 'a' * 40,
                        'generation': '/nix/store/baseline', 'baselineToken': 'c' * 64, 'native': None}
        self.target = 'b' * 40
        self.plan = {'outcome': 'ready', 'reason': 'fixture', 'profile': dict(self.profile),
                     'version': '0.6.21', 'revision': self.target}
        self.calls = []
        self.mode = 'failed_apply'
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(mock.patch.object(self.cli, 'format_plan', return_value='fixture\n'))
        self.enterContext(mock.patch.object(self.cli.host, 'local_profile', side_effect=lambda: dict(self.profile)))
        self.deploy = self.enterContext(mock.patch.object(self.cli, 'run_deploy', side_effect=self.run_backend))

    def run_backend(self, *args):
        self.calls.append(args)
        if args[0] == 'follow':
            self.assertIn('--expect-baseline', args)
            if self.mode == 'preflight_failure':
                raise self.cli.UpgradeError('build failed before mutation')
            tx = args[args.index('--transaction') + 1]
            self.backend.write_text(json.dumps({'id': tx, 'phase': 'recovered' if self.mode == 'already_recovered' else 'partial'}))
            if self.mode == 'success':
                self.profile.update(assembly=self.target, generation='/nix/store/target')
                return
            if self.mode != 'already_recovered':
                self.profile.update(assembly=self.target, generation='/nix/store/target', baselineToken='d' * 64)
            raise self.cli.UpgradeError('activation failed')
        self.assertEqual(args[0], 'recover')
        self.assertEqual(args[1], json.loads(self.backend.read_text())['id'])
        if self.mode == 'recovery_failure':
            raise self.cli.UpgradeError('baseline generation missing')
        if self.mode != 'wrong_recovery':
            self.profile.update(assembly='a' * 40, generation='/nix/store/baseline', baselineToken='c' * 64)

    def apply(self):
        with self.store:
            return self.cli.apply_plan(self.plan, yes=True, store=self.store)

    def test_success_records_complete(self):
        self.mode = 'success'
        self.assertEqual(self.apply()['outcome'], 'complete')
        self.assertEqual(self.store.read_current()['phase'], 'complete')

    def test_successful_recovery_is_not_reported_as_failed_recovery(self):
        with self.assertRaisesRegex(self.cli.UpgradeError, '^upgrade failed and recovered: activation failed$'):
            self.apply()
        data = self.store.read_current()
        self.assertEqual(data['phase'], 'recovered')
        self.assertNotIn('recoveryError', data)
        self.assertEqual([c[0] for c in self.calls], ['follow', 'recover'])
        self.assertEqual(self.cli.status(self.store), 0)

    def test_backend_automatic_recovery_never_calls_back(self):
        self.mode = 'already_recovered'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'failed and recovered'):
            self.apply()
        self.assertEqual([c[0] for c in self.calls], ['follow', 'recover'])
        self.assertEqual(self.store.read_current()['phase'], 'recovered')

    def test_pre_activation_failure_does_not_recover_unrelated_deployment(self):
        self.mode = 'preflight_failure'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'before deployment; baseline unchanged'):
            self.apply()
        self.assertEqual([c[0] for c in self.calls], ['follow'])
        self.assertFalse(self.store.read_current()['recoveryRequired'])
        self.assertEqual(self.cli.status(self.store), 0)

    def test_failed_recovery_blocks_another_upgrade_even_if_target_is_noop(self):
        self.mode = 'recovery_failure'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'recovery incomplete'):
            self.apply()
        data = self.store.read_current()
        self.assertEqual(data['phase'], 'failed')
        self.assertEqual(data['error'], 'activation failed')
        self.assertEqual(data['recoveryError'], 'baseline generation missing')
        self.assertEqual(self.cli.status(self.store), 1)
        self.plan['outcome'] = 'no_change'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'incomplete upgrade'):
            self.apply()

    def test_recovery_verifies_both_assembly_and_generation(self):
        self.mode = 'wrong_recovery'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'recovery incomplete'):
            self.apply()
        self.assertTrue(self.store.read_current()['recoveryRequired'])

    def test_stale_baseline_refused_before_receipt_or_backend(self):
        self.profile['baselineToken'] = 'e' * 64
        with self.assertRaisesRegex(self.cli.UpgradeError, 'starting state changed'):
            self.apply()
        self.deploy.assert_not_called()
        self.assertIsNone(self.store.read_current())

    def test_cancellation_changes_nothing(self):
        with mock.patch.object(self.cli, 'confirm', return_value=False):
            with self.store, self.assertRaisesRegex(self.cli.UpgradeError, 'cancelled'):
                self.cli.apply_plan(self.plan, yes=False, store=self.store)
        self.deploy.assert_not_called()
        self.assertIsNone(self.store.read_current())

    def test_blocked_compatibility_changes_nothing(self):
        self.plan.update(outcome='blocked_native', reason='native mismatch', stops=['manual step'])
        with self.assertRaisesRegex(self.cli.UpgradeError, 'native mismatch'):
            self.apply()
        self.deploy.assert_not_called()
        self.assertIsNone(self.store.read_current())

    def interrupted(self):
        def interrupt(*args):
            tx = args[args.index('--transaction') + 1]
            self.backend.write_text(json.dumps({'id': tx, 'phase': 'activating'}))
            self.profile.update(assembly=self.target, generation='/nix/store/target')
            raise KeyboardInterrupt()
        with mock.patch.object(self.cli, 'run_deploy', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.apply()
        return self.store.read_current()['id']

    def test_interruption_has_durable_receipt_and_explicit_offline_recovery(self):
        tx = self.interrupted()
        self.assertEqual(self.store.read_current()['phase'], 'applying')
        with mock.patch.object(self.cli, 'build_plan', side_effect=AssertionError('network discovery')):
            with self.store:
                self.cli.recover(tx, yes=True, store=self.store)
        self.assertEqual(self.store.read_current()['phase'], 'recovered')
        calls = len(self.calls)
        self.cli.recover(tx, yes=True, store=self.store)
        self.assertEqual(len(self.calls), calls)

    def test_old_or_foreign_receipts_and_path_traversal_refused(self):
        tx = self.interrupted()
        for identifier in ('older', '../current'):
            with self.subTest(identifier=identifier), self.assertRaises(self.cli.UpgradeError):
                self.cli.recover(identifier, yes=True, store=self.store)
        self.profile['hostname'] = 'other-host'
        with self.assertRaisesRegex(self.cli.UpgradeError, 'legacy or foreign'):
            self.cli.recover(tx, yes=True, store=self.store)
        self.deploy.assert_not_called()

    def test_legacy_failed_receipt_cannot_be_recovered_by_guessing(self):
        self.store.write({'id': 'legacy', 'phase': 'failed', 'profile': self.profile['hostname']})
        with self.assertRaisesRegex(self.cli.UpgradeError, 'legacy or foreign'):
            self.cli.recover('legacy', yes=True, store=self.store)
        self.deploy.assert_not_called()

    def test_atomic_archive_and_current_record_failure_is_detected(self):
        self.store.write({'id': 'txn', 'phase': 'applying', 'baselineToken': 'a' * 64})
        original_replace = os.replace
        def fail_current(source, target):
            if Path(target) == self.store.current_path:
                raise OSError('injected interrupted publication')
            return original_replace(source, target)
        with mock.patch.object(self.cli.receipt.os, 'replace', side_effect=fail_current):
            with self.assertRaises(OSError):
                self.store.write({'id': 'txn', 'phase': 'failed'})
        self.assertEqual(self.store.read_current()['phase'], 'applying')
        with self.assertRaisesRegex(self.cli.UpgradeError, 'receipts disagree'):
            self.cli.recover('txn', yes=True, store=self.store)
        self.assertEqual(list(self.store.root.glob('.current.json-*')), [])

    def test_two_processes_cannot_upgrade_concurrently(self):
        ctx = multiprocessing.get_context('fork')
        ready, release = ctx.Event(), ctx.Event()
        process = ctx.Process(target=hold_lock, args=(str(self.store.root), ready, release))
        process.start()
        try:
            self.assertTrue(ready.wait(5))
            with self.assertRaisesRegex(self.cli.receipt.ReceiptError, 'already in progress'):
                with self.store:
                    self.fail('lock acquired twice')
        finally:
            release.set()
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join()
        self.assertEqual(process.exitcode, 0)


if __name__ == '__main__':
    unittest.main()
