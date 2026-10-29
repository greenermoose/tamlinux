"""Exercise authentication placement with dark, removed and focused outputs."""
import json
from pathlib import Path
import subprocess
import unittest

MODEL = Path(__file__).resolve().parents[1] / 'shell/services/polkit/PolkitModel.js'


class PromptScreenTests(unittest.TestCase):
    def test_prompt_avoids_dark_outputs_and_handles_topology_changes(self):
        cases = [
            # MSI first in the screen list, dark; the user is on the Dell.
            (['MSI', 'Dell', 'HP'], [('MSI', False), ('Dell', True), ('HP', True)], 'Dell', 'Dell'),
            # Focus still points at a dark output: use a lit one instead.
            (['MSI', 'Dell'], [('MSI', False), ('Dell', True)], 'MSI', 'Dell'),
            # All dark: choose focused output so the service can wake it.
            (['MSI', 'Dell'], [('MSI', False), ('Dell', False)], 'Dell', 'Dell'),
            # A formerly focused monitor was unplugged.
            (['HP'], [('HP', True)], 'Dell', 'HP'),
            # No focus or compositor snapshot yet; retain a valid fallback.
            (['Dell'], [], '', 'Dell'),
            ([], [], 'Dell', None),
        ]
        script = '''const model = require(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map(c => {
  const result = model.promptScreen(c[0].map(name => ({name})),
    c[1].map(([name, dpmsOn]) => ({name, dpmsOn})), c[2]);
  return result ? result.name : null;
})));'''
        result = subprocess.run(['node', '-e', script, str(MODEL), json.dumps(cases)],
                                check=True, capture_output=True, text=True, timeout=5)
        self.assertEqual(json.loads(result.stdout), [case[3] for case in cases])


if __name__ == '__main__':
    unittest.main()
