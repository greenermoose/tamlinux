import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('release', Path(__file__).parents[1] / 'release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseSelectionTest(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.inputs = {'tamlinux': {'owner': 'greenermoose', 'repo': 'tamlinux', 'rev': 'b' * 40}}
        self.docs = {
            f'{release.API}/releases/latest': {'tag_name': '0.5.12', 'draft': False, 'prerelease': False},
            f'{release.API}/releases/tags/0.5.12': {'tag_name': '0.5.12', 'draft': False, 'prerelease': False},
            f'{release.API}/git/ref/tags/0.5.12': {'object': {'sha': self.sha, 'type': 'commit'}},
            f'{release.RAW}/{self.sha}/deliveries/tamlinux-0.5.12.json':
                {'schemaVersion': 1, 'id': 'tamlinux-0.5.12', 'version': '0.5.12', 'components': self.inputs.copy()},
            f'{release.RAW}/{self.sha}/flake.lock': {'root': 'root', 'nodes': {
                'root': {'inputs': {'tamlinux': 'tamlinux'}}, 'tamlinux': {'locked': self.inputs['tamlinux']}}},
        }

    def fetch(self, url):
        return self.docs[url]

    def test_latest_and_explicit_resolve_exact_record(self):
        self.assertEqual(release.resolve(fetch=self.fetch)['revision'], self.sha)
        self.assertEqual(release.resolve('0.5.12', self.fetch)['version'], '0.5.12')

    def test_unreleased_or_mismatched_records_fail(self):
        self.docs[f'{release.API}/releases/latest']['draft'] = True
        with self.assertRaises(release.ReleaseError):
            release.resolve(fetch=self.fetch)
        self.docs[f'{release.API}/releases/latest']['draft'] = False
        self.docs[f'{release.RAW}/{self.sha}/deliveries/tamlinux-0.5.12.json']['components'] = {}
        with self.assertRaises(release.ReleaseError):
            release.resolve(fetch=self.fetch)

    def test_invalid_user_version_is_rejected_before_fetch(self):
        with self.assertRaises(release.ReleaseError):
            release.resolve('../main', self.fetch)

    def test_annotated_tag_is_resolved_to_commit(self):
        tag_sha = 'c' * 40
        self.docs[f'{release.API}/git/ref/tags/0.5.12']['object'] = {'sha': tag_sha, 'type': 'tag'}
        self.docs[f'{release.API}/git/tags/{tag_sha}'] = {'object': {'sha': self.sha, 'type': 'commit'}}
        self.assertEqual(release.resolve(fetch=self.fetch)['revision'], self.sha)

    def test_malformed_metadata_fails_closed(self):
        self.docs[f'{release.API}/releases/latest'] = []
        with self.assertRaises(release.ReleaseError):
            release.resolve(fetch=self.fetch)
