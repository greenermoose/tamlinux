"""`tam-plugin new` creates a valid plugin and places it in the default layout."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT.parents[1]
LAYOUT = Path('desktop/shell/bar/default-layout.json')


class NewPlugin(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tam-plugin-new-')
        self.addCleanup(temp.cleanup)
        self.product = Path(temp.name) / 'tamlinux'
        shutil.copytree(PRODUCT / 'desktop/shell/host', self.product / 'desktop/shell/host',
                        ignore=shutil.ignore_patterns('__pycache__'))
        (self.product / LAYOUT).parent.mkdir(parents=True)
        shutil.copy(PRODUCT / LAYOUT, self.product / LAYOUT)
        shutil.copytree(PRODUCT / 'desktop/plugins/fred.clock', self.product / 'desktop/plugins/fred.clock',
                        ignore=shutil.ignore_patterns('__pycache__'))
        self.original = (self.product / LAYOUT).read_text()
        self.env = os.environ | {
            'HOME': temp.name, 'FRED_LIVE_DIR': str(Path(temp.name) / 'plugins'),
            'TAMLINUX_SOURCE_REPO': str(self.product),
        }

    def run_cli(self, *args):
        return subprocess.run([str(ROOT / 'tam-plugin'), *args], env=self.env,
                              capture_output=True, text=True, timeout=20)

    def layout(self):
        return json.loads((self.product / LAYOUT).read_text())['layout']

    def test_creates_a_valid_plugin_before_the_anchor(self):
        result = self.run_cli('new', 'fred.example', '--description', 'Example "quoted" label',
                              '--section', 'center', '--before', 'fred.clock')
        self.assertEqual(result.returncode, 0, result.stderr)
        center = [entry['id'] for entry in self.layout()['center']]
        self.assertEqual(center[center.index('fred.clock') - 1], 'fred.example')
        # Only the new entry changes; the file keeps its one-entry-per-line form.
        added = [line for line in (self.product / LAYOUT).read_text().splitlines()
                 if line not in self.original.splitlines()]
        self.assertEqual(added, ['      { "id": "fred.example" },'])

        plugin = self.product / 'desktop/plugins/fred.example'
        manifest = json.loads((plugin / 'manifest.json').read_text())
        self.assertEqual((manifest['id'], manifest['name'], manifest['version']),
                         ('fred.example', 'Example', '0.1.0'))
        self.assertEqual(manifest['description'], 'Example "quoted" label')
        qml = (plugin / 'BarWidget.qml').read_text()
        self.assertEqual(re.findall(r'pluginVersion: "([^"]+)"', qml), [manifest['version']])
        self.assertIn('moduleName: "fred.example"', qml)
        for name in ('README.md', 'CHANGELOG.md'):
            self.assertTrue((plugin / name).is_file(), name)
        registry = self.product / 'desktop/shell/host/registry.py'
        subprocess.run(['python3', '-I', str(registry), 'validate', str(plugin)], check=True,
                       capture_output=True)

    def test_generated_widget_renders_offscreen(self):
        proof = PRODUCT / 'desktop/widget-proof'
        probe = subprocess.run([str(proof), '--help'], capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0, probe.stderr)
        result = self.run_cli('new', 'fred.example', '--description', 'Example label')
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = subprocess.run([str(proof), str(self.product / 'desktop/plugins/fred.example'),
                                   '--expect', 'Example'], capture_output=True, text=True, timeout=60)
        if rendered.returncode and 'no Quickshell found' in rendered.stderr:
            self.skipTest('no Quickshell available')
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)

    def test_default_placement_is_the_end_of_the_right_section(self):
        result = self.run_cli('new', 'fred.multi-word', '--description', 'Two words')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.layout()['right'][-1], {'id': 'fred.multi-word'})
        manifest = json.loads((self.product / 'desktop/plugins/fred.multi-word/manifest.json').read_text())
        self.assertEqual(manifest['name'], 'Multi Word')

    def test_no_layout_leaves_the_default_layout_alone(self):
        result = self.run_cli('new', 'fred.quiet', '--description', 'Off the bar', '--no-layout')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.product / LAYOUT).read_text(), self.original)

    def test_refusals_create_nothing(self):
        cases = [
            (('new', 'fred.clock', '--description', 'x'), 'already exists'),
            (('new', 'clock', '--description', 'x'), 'invalid plugin id'),
            (('new', 'fred.nodesc'), '--description'),
            (('new', 'fred.lost', '--description', 'x', '--before', 'fred.nowhere'), 'not in the right section'),
            (('new', 'fred.both', '--description', 'x', '--before', 'a', '--after', 'b'), 'not both'),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
        self.assertEqual(sorted(p.name for p in (self.product / 'desktop/plugins').iterdir()), ['fred.clock'])
        self.assertEqual((self.product / LAYOUT).read_text(), self.original)


if __name__ == '__main__':
    unittest.main()
