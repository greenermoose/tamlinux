"""Normal plugin discovery uses the packaged catalog and makes no requests."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT.parents[1]


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
        self.env = os.environ | {
            'HOME': str(self.temp / 'home'), 'PATH': f'{self.bin}:{os.environ["PATH"]}',
            'FRED_LIVE_DIR': str(self.temp / 'plugins'),
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
        ids = ['workspaces', 'clock', 'sysinfo', 'monitor', 'weather', 'tides', 'keyboard', 'agents']
        for name in ids:
            with self.subTest(name=name):
                result = self.run_cli('info', f'fred.{name}')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'https://github.com/greenermoose/tamlinux/tree/main/desktop/plugins/fred.{name}',
                              result.stdout)

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
