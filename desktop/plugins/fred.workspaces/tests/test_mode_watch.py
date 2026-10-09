"""Every bar shows the same desktop mode at once.

The mode letter on each bar follows the shared desktop-mode file through a
FileView watch. A watch whose directory was missing when the bar started is
never armed, so after any helper command every copy re-reads the state files
(which arms the watch), and the 30-second status check re-reads the mode file
too. A click shows the next mode at once and must not start a status check,
which could read the old mode before the helper writes the new one.

These read the QML source; the behaviour was confirmed in the Tamlinux shell's
isolated proof, where the state directory does not exist at start.
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


def between(first, last):
    """The source from one landmark to the next."""
    i = QML.index(first)
    return QML[i:QML.index(last, i)]


class ModeWatchTests(unittest.TestCase):
    def test_reload_re_reads_both_state_files(self):
        body = block(r'function reloadStateFiles\(\)')
        self.assertIn('modeFile.reload()', body)
        self.assertIn('monitorsFile.reload()', body)

    def test_every_helper_exit_reloads_every_copy(self):
        action = between('id: actionProcess', 'id: actionWatchdog')
        exited = action[action.index('onExited'):]
        self.assertIn('root.broadcastWorkspaces("reloadStateFiles")', exited)
        self.assertLess(exited.index('reloadStateFiles'), exited.index('root.runNextAction()'))

    def test_status_check_re_reads_the_mode_file(self):
        self.assertIn('modeFile.reload()', block(r'id: modeStatusProcess'))

    def test_a_click_does_not_start_a_status_check(self):
        button = between('text: root.barDeviated ? "F" : root.desktopModeLetter()', 'IpcHandler {')
        pressed = button[button.index('onPressed'):]
        self.assertIn('runDesktopCommand(["toggle"])', pressed)
        self.assertNotIn('modeRefreshTimer', pressed)
        self.assertNotIn('modeStatusProcess', pressed)


if __name__ == '__main__':
    unittest.main()
