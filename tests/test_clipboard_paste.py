"""Exercise the clipboard helper with a temporary history and compositor."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "src/desktop/shell/services/clipboard/paste-text.sh"


class ClipboardPaste(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        history = self.root / "tamlinux/clipboard"
        history.mkdir(parents=True)
        (history / "history.json").write_text('[{"type":"text","text":"one\\ntwo\\n"}]')
        self.env = dict(os.environ, PATH=f"{self.root}:{os.environ['PATH']}",
                        XDG_STATE_HOME=tmp.name, ACTIVE="0x123", CLASS="tam-last")
        self.stub("wl-copy", 'cat > "$XDG_STATE_HOME/copied"')
        self.stub("wtype", 'echo "$*" >> "$XDG_STATE_HOME/keys"')
        self.stub("hyprctl", """if [ "$1" = "-j" ]; then
            printf '{"class":"%s","address":"%s"}' "$CLASS" "$ACTIVE"
        else
            echo "$2" >> "$XDG_STATE_HOME/keys"
            echo ok
        fi""")

    def stub(self, name, body):
        path = self.root / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def helper(self, *args, check=True):
        return subprocess.run([HELPER, *args], env=self.env, capture_output=True,
                              text=True, check=check)

    def test_paste_to_original_terminal(self):
        target = self.helper("--capture-target").stdout.strip()
        self.assertEqual(target, "0x123")
        self.helper("--target", target, "--history-index", "0")
        self.assertEqual((self.root / "copied").read_bytes(), b"one\ntwo\n")
        keys = (self.root / "keys").read_text().splitlines()
        self.assertEqual(keys, [
            f"hl.dsp.send_key_state({{ mods = 'CTRL SHIFT', key = 'V', state = '{state}', window = 'address:0x123' }})"
            for state in ("down", "up")])

    def test_focus_change_copies_without_sending_keys(self):
        result = self.helper("--target", "0xabc", "--history-index", "0", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "copied").exists())
        self.assertFalse((self.root / "keys").exists())

    def test_other_application_uses_shift_insert(self):
        self.env["CLASS"] = "foot"
        target = self.helper("--capture-target").stdout.strip()
        self.assertEqual(target, "other")
        self.helper("--target", target, "--history-index", "0")
        self.assertEqual((self.root / "keys").read_text().strip(), "-M shift -k Insert -m shift")
