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


    def test_helper_completion_confirms_the_blank(self):
        # Without it, a monitor lit from elsewhere before the facade's next
        # monitor read kept its stale dark state for good (2026-11-18).
        done = block(r'function dpmsCommandFinished\(')
        self.assertIn('action === "dpms-off" && root.isMonitorDark && root.blankUnconfirmed', done)
        self.assertIn('root.blankUnconfirmed = false', done)
        self.assertIn('ActionQueue.finished(root, root.lastActionBusy, root.lastActionIncomplete, root.lastActionOk)',
                      QML)

    def test_adopted_dark_is_marked(self):
        probe = block(r'function probeDpmsState\(')
        self.assertIn('root.darkAdopted = dark', probe)
        for name in (r'function wakeMonitor\(', r'function blankMonitor\(', r'function resetIdle\('):
            self.assertIn('root.darkAdopted = false', block(name))

    def test_single_monitor_does_not_wake_adopted_dark(self):
        # hypridle blanked the toughbook's only panel; a shell restart adopted
        # that darkness and woke it at once, with nobody there. hypridle, still
        # idled, never blanked it again (2026-11-25).
        track = block(r'function trackMonitorIdle\(')
        self.assertIn('if (root.isMonitorDark && !root.darkAdopted) {', track)

    def test_session_wide_blank_is_left_to_the_idle_daemon(self):
        settle = block(r'id: useSettle')
        guard = 'if (root.darkAdopted && root.allOutputsDark())'
        self.assertIn(guard, settle)
        self.assertLess(settle.index(guard), settle.index('root.wakeMonitor(reason)'))
        self.assertIn('outputs[i].dpmsOn !== false', block(r'function allOutputsDark\('))

if __name__ == '__main__':
    unittest.main()
