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

    def test_tam_pane_paste_to_original_terminal(self):
        self.env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        self.env["TAM_PANE_SOCKET"] = str(self.root / "pane.sock")
        self.env["PANE_ID"] = "42"
        self.env["PANE_APP"] = "tam-last"
        self.stub("tam-pane", """if [ "$1" = "msg" ] && [ "$2" = "windows" ]; then
            printf 'window\\tid=%s\\tapp_id=%s\\tfocused=1\\n' "$PANE_ID" "$PANE_APP"
        elif [ "$1" = "msg" ] && [ "$2" = "dispatch" ]; then
            shift 2
            echo "$*" >> "$XDG_STATE_HOME/pane_keys"
        fi""")
        target = self.helper("--capture-target").stdout.strip()
        self.assertEqual(target, "pane:42")
        self.helper("--target", target, "--history-index", "0")
        self.assertEqual((self.root / "copied").read_bytes(), b"one\ntwo\n")
        self.assertEqual((self.root / "pane_keys").read_text().strip(), "send_key Ctrl+Shift+V")

    def test_tam_pane_focus_change_copies_without_sending_keys(self):
        self.env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        self.env["TAM_PANE_SOCKET"] = str(self.root / "pane.sock")
        self.env["PANE_ID"] = "99"
        self.env["PANE_APP"] = "tam-last"
        self.stub("tam-pane", """if [ "$1" = "msg" ] && [ "$2" = "windows" ]; then
            printf 'window\\tid=%s\\tapp_id=%s\\tfocused=1\\n' "$PANE_ID" "$PANE_APP"
        elif [ "$1" = "msg" ] && [ "$2" = "dispatch" ]; then
            shift 2
            echo "$*" >> "$XDG_STATE_HOME/pane_keys"
        fi""")
        result = self.helper("--target", "pane:42", "--history-index", "0", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "copied").exists())
        self.assertFalse((self.root / "pane_keys").exists())

    def test_tam_pane_other_application_uses_shift_insert(self):
        self.env.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        self.env["TAM_PANE_SOCKET"] = str(self.root / "pane.sock")
        self.env["PANE_ID"] = "7"
        self.env["PANE_APP"] = "firefox"
        self.stub("tam-pane", """if [ "$1" = "msg" ] && [ "$2" = "windows" ]; then
            printf 'window\\tid=%s\\tapp_id=%s\\tfocused=1\\n' "$PANE_ID" "$PANE_APP"
        fi""")
        target = self.helper("--capture-target").stdout.strip()
        self.assertEqual(target, "other")
        self.helper("--target", target, "--history-index", "0")
        self.assertEqual((self.root / "keys").read_text().strip(), "-M shift -k Insert -m shift")
