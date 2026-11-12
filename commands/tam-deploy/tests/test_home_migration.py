"""Temporary-home proofs for exact Home Manager link conversion and return."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_deploy import deploy


class Crash(BaseException):
    pass


class HomeLinks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / 'home'
        self.generation = self.root / 'generation'
        self.files = self.generation / 'home-files'
        self.source = self.root / 'checkout'
        self.source.mkdir()
        (self.source / 'idle.conf').write_text('old idle\n')
        (self.source / 'unlisted.conf').write_text('preserved neighbour\n')
        self.endpoint('.config/hypr', self.source)
        self.endpoint('.bashrc', self.source / 'idle.conf')
        self.endpoint('.local/bin/tam-demo', self.source / 'idle.conf')
        self.endpoint('.local/bin/own-tool', self.source / 'idle.conf')
        self.journal = self.root / 'private/journal'
        self.app = deploy.HomeLinkMigration(self.home, self.journal)

    def endpoint(self, relative, source):
        expected = self.files / relative
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.symlink_to(source)
        live = self.home / relative
        live.parent.mkdir(parents=True, exist_ok=True)
        live.symlink_to(expected)

    def prepare(self):
        plan = self.app.plan(self.generation, ['.config/hypr/idle.conf', '.bashrc'],
                             ['.local/bin/tam-demo'])
        self.app.create(plan)
        return plan

    def assert_original(self):
        for relative in ('.config/hypr', '.bashrc', '.local/bin/tam-demo'):
            self.assertTrue(self.app.expected_link(self.home / relative, self.generation, relative))
        self.assertEqual((self.source / 'idle.conf').read_text(), 'old idle\n')

    def test_plan_is_read_only_and_conversion_reads_switch_time_values(self):
        plan = self.prepare()
        self.assert_original()
        self.assertEqual(len(plan['entries']), 3)
        (self.source / 'idle.conf').write_text('later edit\n')
        self.app.apply()
        self.assertFalse((self.home / '.config/hypr').is_symlink())
        self.assertFalse((self.home / '.bashrc').is_symlink())
        self.assertEqual((self.home / '.bashrc').read_text(), 'later edit\n')
        self.assertEqual((self.home / '.config/hypr/unlisted.conf').read_text(), 'preserved neighbour\n')
        self.assertFalse(os.path.lexists(self.home / '.local/bin/tam-demo'))
        self.assertTrue((self.home / '.local/bin/own-tool').is_symlink())
        self.assertEqual(self.journal.stat().st_mode & 0o777, 0o700)

    def test_return_preserves_bundle_era_edits_before_restoring_exact_links(self):
        plan = self.prepare()
        self.app.apply()
        (self.home / '.bashrc').write_text('bundle era edit\n')
        self.app.apply()  # completed conversion is not repeated
        self.app.restore()
        self.app.restore()
        self.assert_original()
        index = next(i for i, entry in enumerate(plan['entries']) if entry['path'] == '.bashrc')
        self.assertEqual((self.journal / 'returned' / str(index)).read_text(), 'bundle era edit\n')

    def test_foreign_and_lookalike_links_refuse_before_changes(self):
        live = self.home / '.bashrc'
        live.unlink(); live.symlink_to(self.source / 'idle.conf')
        with self.assertRaisesRegex(deploy.DeploymentError, 'differs from saved'):
            self.prepare()
        self.assertFalse(self.journal.exists())
        self.assertTrue((self.home / '.config/hypr').is_symlink())

    def test_linked_parent_and_malformed_journal_refuse(self):
        self.prepare()
        value = json.loads(self.app.record.read_text())
        value['entries'][0]['path'] = '../outside'
        deploy.atomic_json(self.app.record, value)
        with self.assertRaises(deploy.DeploymentError):
            self.app.apply()
        self.assert_original()

    def test_special_files_and_cycles_refuse_before_link_retirement(self):
        self.prepare()
        os.mkfifo(self.source / 'fifo')
        with self.assertRaisesRegex(deploy.DeploymentError, 'special file'):
            self.app.apply()
        self.assertTrue((self.home / '.config/hypr').is_symlink())
        (self.source / 'fifo').unlink()
        (self.source / 'cycle').symlink_to(self.source)
        with self.assertRaisesRegex(deploy.DeploymentError, 'cycle'):
            self.app.apply()
        self.assertTrue((self.home / '.config/hypr').is_symlink())

    def test_unexpected_return_endpoint_preserves_both_copies(self):
        self.prepare(); self.app.apply()
        endpoint = self.home / '.local/bin/tam-demo'
        endpoint.write_text('unrelated new command')
        with self.assertRaisesRegex(deploy.DeploymentError, 'unexpected endpoint'):
            self.app.restore()
        self.assertEqual(endpoint.read_text(), 'unrelated new command')

    def fault_run(self, operation, point=None):
        events = []
        real_sync, real_rename, real_atomic = self.app.sync, os.rename, deploy.atomic_json
        def step(name, operation, *args):
            result = operation(*args)
            events.append(name)
            if len(events) == point:
                raise Crash()
            return result
        with (patch.object(self.app, 'sync', side_effect=lambda *args: step('sync', real_sync, *args)),
              patch.object(deploy.os, 'rename', side_effect=lambda *args: step('rename', real_rename, *args)),
              patch.object(deploy, 'atomic_json', side_effect=lambda *args: step('record', real_atomic, *args))):
            try:
                operation()
            except Crash:
                pass
        return events

    def test_every_conversion_and_return_boundary_retries(self):
        # Fresh fixtures at each point also model losing all in-memory state.
        for operation in ('apply', 'restore'):
            probe = HomeLinks(); probe.setUp()
            try:
                probe.prepare()
                if operation == 'restore': probe.app.apply()
                count = len(probe.fault_run(getattr(probe.app, operation)))
            finally:
                probe.doCleanups()
            self.assertGreater(count, 10)
            for point in range(1, count + 1):
                with self.subTest(operation=operation, point=point):
                    fixture = HomeLinks(); fixture.setUp()
                    try:
                        fixture.prepare()
                        if operation == 'restore': fixture.app.apply()
                        fixture.fault_run(getattr(fixture.app, operation), point)
                        fixture.app = deploy.HomeLinkMigration(fixture.home, fixture.journal)
                        getattr(fixture.app, operation)()
                        if operation == 'apply': fixture.app.restore()
                        fixture.assert_original()
                    finally:
                        fixture.doCleanups()


if __name__ == '__main__':
    unittest.main()
