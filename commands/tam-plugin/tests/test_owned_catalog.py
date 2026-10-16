"""Normal plugin discovery uses the packaged catalog and makes no requests."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT.parents[1]
PLUGINS = sorted((PRODUCT / 'desktop/plugins').glob('fred.*'))


class OwnedCatalog(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tam-plugin-catalog-')
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.bin = self.temp / 'bin'
        self.bin.mkdir()
        self.network_log = self.temp / 'network-attempt'
        blocked = self.bin / 'curl'
        blocked.write_text(f'#!{sys.executable}\nimport os, sys\n'
                           'with open(os.environ["TEST_NETWORK_LOG"], "a") as out:\n'
                           '    out.write(" ".join(sys.argv) + "\\n")\n'
                           'sys.exit(99)\n')
        blocked.chmod(0o755)
        cache = self.temp / 'home/.cache/tam-plugin/registry.json'
        cache.parent.mkdir(parents=True)
        cache.write_text(json.dumps({'sources': [{'plugins': {'fred.clock': {}},
                              'automatedSecurityBaseline': {'outcome': 'passed'}}]}))
        self.cache = cache
        # An installed plugin package, reached through one live link as Home
        # Manager provides it. The catalog is read from it, not a checkout.
        package = self.temp / 'store/tamlinux-plugins/share/tamlinux/plugins'
        for plugin in PLUGINS:
            shutil.copytree(plugin, package / plugin.name, symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__'))
        self.live = self.temp / 'plugins'
        self.live.mkdir()
        (self.live / 'fred.clock').symlink_to(package / 'fred.clock')
        self.env = os.environ | {
            'HOME': str(self.temp / 'home'), 'PATH': f'{self.bin}:{os.environ["PATH"]}',
            'FRED_LIVE_DIR': str(self.live),
            'TAMLINUX_SOURCE_REPO': str(self.temp / 'no-checkout'),
            'TAMLINUX_REGISTRY': str(PRODUCT / 'desktop/shell/host/registry.py'),
            'TEST_NETWORK_LOG': str(self.network_log),
        }

    def run_cli(self, *args):
        return subprocess.run([str(ROOT / 'tam-plugin'), *args], env=self.env,
                              capture_output=True, text=True, timeout=10)

    def test_discovery_is_offline_without_source_checkout(self):
        for args in [('list', '--all'), ('list', '--all', '--refresh'),
                     ('info', 'fred.clock'), ('search', 'clock')]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('fred.clock', result.stdout)
                self.assertNotIn('omarchy', result.stdout.lower())
                self.assertNotIn('Marketplace', result.stdout)
                self.assertFalse(self.network_log.exists())
        self.assertTrue(self.cache.exists())  # History isn't deleted.

    def test_catalog_links_are_maintained_product_sources(self):
        self.assertIn('fred.clock', [plugin.name for plugin in PLUGINS])
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin.name):
                result = self.run_cli('info', plugin.name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'https://github.com/greenermoose/tamlinux/tree/main/desktop/plugins/{plugin.name}',
                              result.stdout)
                description = json.loads((plugin / 'manifest.json').read_text())['description']
                self.assertIn(f'Description: {description}', result.stdout)

    def test_every_packaged_plugin_is_searchable(self):
        result = self.run_cli('search')
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = {line.split()[0] for line in result.stdout.splitlines()[1:]}
        self.assertEqual(listed, {plugin.name for plugin in PLUGINS})

    def test_plugin_from_another_repository_is_local(self):
        mine = self.live / 'fred.mine'
        mine.mkdir()
        (mine / 'manifest.json').write_text(json.dumps({
            'id': 'fred.mine', 'repository': 'https://example.org/mine.git', 'description': 'Mine'}))
        result = self.run_cli('search')
        self.assertNotIn('fred.mine', result.stdout)

    def test_unknown_local_plugin_gets_no_invented_repository(self):
        result = self.run_cli('info', 'fred.local')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no catalogued repository', result.stdout)
        self.assertNotIn('github.com', result.stdout)

    def test_upstream_comparison_is_explicitly_retired(self):
        result = self.run_cli('upstream-diff')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('verify <id>', result.stderr)
        self.assertNotIn('omarchy', result.stderr.lower())
        self.assertFalse(self.network_log.exists())


if __name__ == '__main__':
    unittest.main()
