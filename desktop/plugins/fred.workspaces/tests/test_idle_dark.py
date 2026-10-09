"""A monitor this bar blanked stays dark until something wakes it.

The shell's facade may still report a monitor lit after this bar has blanked
it: Hyprland sends no DPMS event, so the facade only learns of the blank on
its next monitor read. Taking that stale report as "lit" cleared the dark
state, and cursor entry then had nothing to wake. A lit report counts only
after the facade has reported the blank.

These read the QML source; the behaviour is checked live in the Tamlinux shell.
"""

import re
import unittest
from pathlib import Path

QML = (Path(__file__).resolve().parents[1] / 'Workspaces.qml').read_text(encoding='utf-8')


def block(start):
    """The brace-balanced block that opens on the first line matching start."""
    match = re.search(start, QML)
    if not match:
        raise AssertionError(f'not found: {start}')
    depth, i = 0, QML.index('{', match.start())
    for j in range(i, len(QML)):
        depth += {'{': 1, '}': -1}.get(QML[j], 0)
        if depth == 0:
            return QML[i:j + 1]
    raise AssertionError(f'unbalanced: {start}')


class IdleDarkTests(unittest.TestCase):
    def test_blank_waits_for_the_facade_to_confirm(self):
        self.assertIn('root.blankUnconfirmed = true', block(r'function blankMonitor\('))

    def test_stale_lit_report_does_not_clear_own_blank(self):
        probe = block(r'function probeDpmsState\(')
        guard = 'else if (root.isMonitorDark && root.blankUnconfirmed) return'
        self.assertIn('if (dark) root.blankUnconfirmed = false', probe)
        self.assertIn(guard, probe)
        self.assertLess(probe.index(guard), probe.index('root.isMonitorDark = dark'))

    def test_wake_and_reset_clear_the_pending_blank(self):
        for name in (r'function wakeMonitor\(', r'function resetIdle\('):
            self.assertIn('root.blankUnconfirmed = false', block(name))


if __name__ == '__main__':
    unittest.main()
