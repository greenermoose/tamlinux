"""Bundle discovery and read-only preparation through tam-deploy entry points."""
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
from unittest.mock import patch

from test_deploy import Fixture, deploy, git


class BundlePreflight(Fixture):
    def setUp(self):
        super().setUp()
        repository = self.app.repo('tamlinux-packages')
        recipe = repository / 'recipes/workstation'
        recipe.mkdir(parents=True)
        (recipe / 'tamlinux.lock').write_text(
            'format 1\ncomponent tamlinux https://example.invalid/product ' + self.tamlinux_new + '\n'
        )
        (repository / 'VERSION').write_text('9.8.7\n')
        git(repository, 'add', '--', 'VERSION', 'recipes/workstation/tamlinux.lock')
        git(repository, 'commit', '-qm', 'Frozen workstation recipe')
        self.recipe = git(repository, 'rev-parse', 'HEAD')
        self.payload = (
            'format 2\nname tamlinux\nversion 9.8.7\nhash sha256:' + 'a' * 64 + '\n'
            'source tamlinux ' + self.tamlinux_new + '\nsource packaging ' + self.recipe + '\n'
        ).encode()
        self.archive = self.root / 'source.tbundle'
        with tarfile.open(self.archive, 'w') as archive:
            entry = tarfile.TarInfo('BUNDLE')
            entry.size = len(self.payload)
            archive.addfile(entry, io.BytesIO(self.payload))
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.cache = self.root / 'cache'
        self.enterContext(patch.dict(os.environ, {'XDG_CACHE_HOME': str(self.cache)}))
        self.cached = self.cache / 'tamlinux/bundles' / (digest + '.tbundle')
        self.cached.parent.mkdir(parents=True)
        self.cached.write_bytes(self.archive.read_bytes())
        self.record = {
            'format': 1, 'backend': 'tam-bundle', 'version': '9.8.7',
            'recipeAssembly': self.recipe, 'components': {'tamlinux': self.tamlinux_new},
            'rootstock': 'arch-systemd', 'minimumTool': '0.11.0',
            'artifact': {'name': 'tamlinux-9.8.7-' + 'a' * 12 + '.tbundle',
                         'bundleId': 'tamlinux-9.8.7-' + 'a' * 12,
                         'bundleHash': 'sha256:' + 'a' * 64, 'sha256': digest},
        }
        (repository / 'deliveries').mkdir()
        self.revision = self.write_record(json.dumps(self.record))

    def write_record(self, text):
        return self.commit('tamlinux-packages', 'deliveries/tamlinux-9.8.7.json', text)

    def test_components_use_the_frozen_recipe(self):
        self.assertEqual(self.app.components(self.revision), self.record['components'])
        self.assertEqual(self.app.bundle_delivery(self.revision)['recipeAssembly'], self.recipe)
        self.assertIsNone(self.app.bundle_delivery(self.packages_main))

    def test_preflight_checks_the_exact_archive_without_nix_or_mutation(self):
        self.app.bundle_delivery(self.revision)
        baseline = {'profileGeneration': '/nix/store/retained-generation',
                    'assembly': self.packages_main}
        calls = []
        def bundle_command(*args):
            calls.append(args)
            return 'tam-bundle 0.11.0 (record format 2)' if args == ('--version',) else ''
        before = self.app.lock.read_bytes()
        with (
            patch.object(self.app, 'check_clean'),
            patch.object(self.app, 'require_consistent', return_value=baseline),
            patch.object(self.app, 'bundle_command', side_effect=bundle_command),
            patch.object(deploy, 'command', return_value='0') as commands,
        ):
            self.app.preflight(self.revision)
        self.assertEqual(calls, [('--version',), ('verify', str(self.cached)),
                                 ('needs', str(self.cached))])
        commands.assert_called_once_with('/usr/bin/vercmp', '0.11.0', '0.11.0', capture=True)
        self.assertEqual(self.app.lock.read_bytes(), before)
        self.assertFalse(self.app.transaction_file.exists())

        def needs_failure(*args):
            if args[0] == '--version':
                return 'tam-bundle 0.11.0 (record format 2)'
            if args[0] == 'needs':
                raise deploy.DeploymentError('missing native requirement')
            return ''
        with (
            patch.object(self.app, 'check_clean'),
            patch.object(self.app, 'require_consistent', return_value=baseline),
            patch.object(self.app, 'bundle_command', side_effect=needs_failure),
            patch.object(deploy, 'command', return_value='0'),
        ):
            with self.assertRaisesRegex(deploy.DeploymentError, 'missing native'):
                self.app.preflight(self.revision)
        self.assertFalse(self.app.transaction_file.exists())
        self.assertEqual(self.app._prepared_bundle_report['bundleId'], self.record['artifact']['bundleId'])

    def test_malformed_ambiguous_and_oversized_delivery_records_refuse(self):
        invalid = dict(self.record, unexpected='value')
        for text in (json.dumps(invalid),
                     json.dumps(self.record)[:-1] + ',"version":"9.8.7"}',
                     '{"payload":"' + 'x' * (1024 * 1024) + '"}'):
            with self.subTest(record=text[:80]):
                revision = self.write_record(text)
                with self.assertRaises(deploy.DeploymentError):
                    self.app.bundle_delivery(revision)
        invalid = dict(self.record, components={'tamlinux': self.tamlinux_main})
        revision = self.write_record(json.dumps(invalid))
        with self.assertRaisesRegex(deploy.DeploymentError, 'frozen recipe'):
            self.app.bundle_delivery(revision)

    def test_changed_missing_and_linked_cached_artifacts_refuse(self):
        self.cached.write_bytes(b'changed')
        with self.assertRaisesRegex(deploy.DeploymentError, 'cached bundle bytes'):
            self.app.bundle_artifact(self.record)
        self.cached.unlink()
        with self.assertRaises(FileNotFoundError):
            self.app.bundle_artifact(self.record)
        self.cached.symlink_to(self.archive)
        with self.assertRaises(OSError):
            self.app.bundle_artifact(self.record)

    def test_bootstrap_minimum_and_runtime_failure_stop_preflight(self):
        self.app.bundle_delivery(self.revision)
        baseline = {'profileGeneration': '/nix/store/retained-generation',
                    'assembly': self.packages_main}
        with (
            patch.object(self.app, 'check_clean'),
            patch.object(self.app, 'require_consistent', return_value=baseline),
            patch.object(self.app, 'bundle_command', return_value='tam-bundle 0.5.2 (record format 1)'),
            patch.object(deploy, 'command', return_value='-1'),
        ):
            with self.assertRaisesRegex(deploy.DeploymentError, 'requires tam-bundle'):
                self.app.preflight(self.revision)
        self.assertFalse(self.app.transaction_file.exists())
