import importlib.machinery
import importlib.util
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

start_path = pathlib.Path(__file__).parents[1] / "start"
loader = importlib.machinery.SourceFileLoader("start_cmd", str(start_path))
spec = importlib.util.spec_from_loader("start_cmd", loader)
start_mod = importlib.util.module_from_spec(spec)
sys.modules["start_cmd"] = start_mod
loader.exec_module(start_mod)


class TestStartCommand(unittest.TestCase):
    def test_syntax(self):
        res = subprocess.run(
            [sys.executable, "-m", "py_compile", str(start_path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Compilation failed: {res.stderr}")

    def test_help_flag(self):
        res = subprocess.run([str(start_path), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("workstation activities", res.stdout)
        self.assertIn("--list", res.stdout)
        self.assertIn("--check", res.stdout)

    def test_version_flag_uses_own_semver(self):
        res = subprocess.run(
            [str(start_path), "--version"], capture_output=True, text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertRegex(res.stdout.strip(), r"^start \d+\.\d+\.\d+$")
        version_file = (start_path.parent / "VERSION").read_text(encoding="utf-8").strip()
        self.assertIn(version_file, res.stdout)

    def test_list_flag_letters_and_desktop_first(self):
        res = subprocess.run([str(start_path), "--list"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        lines = [
            ln
            for ln in res.stdout.splitlines()
            if ln and not ln.startswith("─") and not ln.startswith("Letter")
        ]
        self.assertTrue(lines)
        first = lines[0]
        self.assertTrue(first.startswith("a "))
        self.assertIn("desktop", first)
        self.assertIn("tam-desktop", first)
        self.assertIn("cataclysm-dda", res.stdout)
        self.assertIn("frotz", res.stdout)

    def test_check_flag_shows_version_footer(self):
        res = subprocess.run([str(start_path), "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("activities installed", res.stdout)
        self.assertRegex(res.stdout, r"v\d+\.\d+\.\d+")

    def test_desktop_is_letter_a(self):
        mapping = start_mod.assign_letters()
        self.assertEqual(mapping["a"]["id"], "desktop")
        self.assertEqual(mapping["a"]["command"], ["tam-desktop"])
        self.assertEqual(mapping["a"]["label"], "Start graphical desktop shell")
        self.assertEqual(mapping["b"]["id"], "hi")

    def test_footer_hints_and_right_aligned_version(self):
        footer = start_mod.format_footer(80)
        plain = start_mod._ANSI_RE.sub("", footer)
        self.assertTrue(plain.startswith(start_mod.FOOTER_HINTS))
        self.assertTrue(plain.endswith(f"v{start_mod.VERSION}"))
        self.assertEqual(len(plain), 80)
        self.assertIn("Down/Up Arrow scroll", plain)
        self.assertIn("Home top", plain)
        self.assertIn("End bottom", plain)
        self.assertIn("Backspace quit", plain)

    def test_render_screen_shows_semver_and_attention(self):
        rows = start_mod.build_menu_rows()
        pages = start_mod.paginate_rows(rows, capacity=40)
        text = start_mod.render_screen(
            pages[0], 0, len(pages), attention_index=0, width=80, height=24
        )
        self.assertIn("Tamlinux Start", text)
        self.assertIn("Start graphical desktop shell", text)
        self.assertIn(f"v{start_mod.VERSION}", text)
        self.assertIn("Down/Up Arrow scroll", text)
        last = text.splitlines()[-1]
        self.assertTrue(start_mod._ANSI_RE.sub("", last).endswith(f"v{start_mod.VERSION}"))

    def test_paginate_respects_capacity(self):
        rows = start_mod.build_menu_rows()
        pages = start_mod.paginate_rows(rows, capacity=6)
        self.assertGreater(len(pages), 1)
        for page in pages:
            self.assertLessEqual(len(page), 6)

    def test_page_capacity_uses_terminal_height(self):
        self.assertEqual(
            start_mod.page_capacity(24),
            24 - start_mod.CHROME_TOP - start_mod.CHROME_BOTTOM,
        )
        self.assertEqual(start_mod.page_capacity(8), 1)

    def test_screen_diff_skips_unchanged_rows(self):
        writes: list[str] = []
        screen = start_mod.Screen(write_fn=writes.append)
        frame1 = ["alpha", "bravo", "charlie"]
        screen.update(frame1, width=10)
        first = "".join(writes)
        self.assertIn("\033[1;1H", first)
        self.assertIn("\033[2;1H", first)
        self.assertNotIn("\033[2J", first)  # no full clear on update

        writes.clear()
        frame2 = ["alpha", "BRAVO", "charlie"]  # only middle row changes
        changed = screen.update(frame2, width=10)
        self.assertEqual(changed, 1)
        second = "".join(writes)
        self.assertIn("\033[2;1H", second)
        self.assertNotIn("\033[1;1H", second)
        self.assertNotIn("\033[3;1H", second)
        self.assertNotIn("\033[2J", second)

    def test_screen_enter_uses_alternate_screen_once(self):
        writes: list[str] = []
        screen = start_mod.Screen(write_fn=writes.append)
        screen.enter()
        blob = "".join(writes)
        self.assertIn("\033[?1049h", blob)
        self.assertIn("\033[2J", blob)
        writes.clear()
        screen.update(["only"], width=4)
        self.assertNotIn("\033[2J", "".join(writes))
        writes.clear()
        screen.leave()
        self.assertIn("\033[?1049l", "".join(writes))

    def test_screen_flushes_after_paint(self):
        writes: list[str] = []
        flushes = {"n": 0}

        def flush():
            flushes["n"] += 1

        screen = start_mod.Screen(write_fn=writes.append, flush_fn=flush)
        screen.enter()
        self.assertGreaterEqual(flushes["n"], 1)
        before = flushes["n"]
        screen.update(["row-a", "row-b"], width=10)
        self.assertGreater(flushes["n"], before)
        # Default Screen must wire stdout.write/flush (not a no-flush lambda).
        default = start_mod.Screen()
        self.assertIs(default._write.__self__, start_mod.sys.stdout)
        self.assertEqual(default._write.__name__, "write")
        self.assertIs(default._flush_fn.__self__, start_mod.sys.stdout)
        self.assertEqual(default._flush_fn.__name__, "flush")

    def _run_loop_with_keys(self, keys, size=(80, 40)):
        key_iter = iter(keys)

        def fake_read(_fd):
            try:
                return next(key_iter)
            except StopIteration:
                return start_mod.KEY_BACKSPACE

        fake_screen = MagicMock()
        with patch.object(start_mod.sys.stdin, "isatty", return_value=True), \
             patch.object(start_mod.sys.stdout, "isatty", return_value=True), \
             patch.object(start_mod.termios, "tcgetattr", return_value=[]), \
             patch.object(start_mod.termios, "tcsetattr"), \
             patch.object(start_mod.tty, "setcbreak"), \
             patch.object(start_mod, "is_installed", return_value=True), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            rc = start_mod.interactive_loop(
                read_key_fn=fake_read,
                size_fn=lambda: size,
                screen=fake_screen,
            )
            return rc, mock_run, fake_screen

    def test_backspace_quits_without_running(self):
        rc, mock_run, screen = self._run_loop_with_keys([start_mod.KEY_BACKSPACE])
        self.assertEqual(rc, 0)
        mock_run.assert_not_called()
        screen.enter.assert_called()
        screen.leave.assert_called()

    def test_delete_quits_without_running(self):
        rc, mock_run, _ = self._run_loop_with_keys([start_mod.KEY_DELETE])
        self.assertEqual(rc, 0)
        mock_run.assert_not_called()

    def test_enter_runs_attention_and_exits(self):
        rc, mock_run, _ = self._run_loop_with_keys([start_mod.KEY_ENTER])
        self.assertEqual(rc, 0)
        mock_run.assert_called_once_with(["tam-desktop"])

    def test_right_arrow_runs_attention(self):
        rc, mock_run, _ = self._run_loop_with_keys([start_mod.KEY_RIGHT])
        self.assertEqual(rc, 0)
        mock_run.assert_called_once_with(["tam-desktop"])

    def test_letter_runs_matching_activity_and_exits(self):
        rc, mock_run, _ = self._run_loop_with_keys(["b"])
        self.assertEqual(rc, 0)
        mock_run.assert_called_once_with(["tam", "hi"])

    def test_down_then_enter_runs_second_item(self):
        rc, mock_run, _ = self._run_loop_with_keys([
            start_mod.KEY_DOWN,
            start_mod.KEY_ENTER,
        ])
        self.assertEqual(rc, 0)
        mock_run.assert_called_once_with(["tam", "hi"])

    def test_home_and_end_move_attention(self):
        rc, mock_run, _ = self._run_loop_with_keys([
            start_mod.KEY_END,
            start_mod.KEY_ENTER,
        ], size=(80, 12))
        self.assertEqual(rc, 0)
        mock_run.assert_called_once_with(["nethack"])

    def test_movement_redraws_without_full_clear(self):
        # Down then Backspace: Screen.update must never emit ESC[2J after enter.
        writes: list[str] = []
        screen = start_mod.Screen(write_fn=writes.append)
        keys = [start_mod.KEY_DOWN, start_mod.KEY_BACKSPACE]
        key_iter = iter(keys)

        def fake_read(_fd):
            try:
                return next(key_iter)
            except StopIteration:
                return start_mod.KEY_BACKSPACE

        with patch.object(start_mod.sys.stdin, "isatty", return_value=True), \
             patch.object(start_mod.sys.stdout, "isatty", return_value=True), \
             patch.object(start_mod.termios, "tcgetattr", return_value=[]), \
             patch.object(start_mod.termios, "tcsetattr"), \
             patch.object(start_mod.tty, "setcbreak"), \
             patch.object(start_mod, "is_installed", return_value=True):
            rc = start_mod.interactive_loop(
                read_key_fn=fake_read,
                size_fn=lambda: (80, 40),
                screen=screen,
            )
        self.assertEqual(rc, 0)
        # Strip the enter sequence (which may clear once), then assert updates do not.
        joined = "".join(writes)
        # After enter, subsequent updates are CUP+EL only.
        after_enter = joined.split("\033[?1049h", 1)[-1]
        # Drop the initial clear that belongs to enter.
        after_clear = after_enter.split("\033[2J", 1)[-1] if "\033[2J" in after_enter else after_enter
        self.assertNotIn("\033[2J", after_clear)

    def test_pmars_resolves_bundled_warriors(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            bin_dir = root / "bin"
            warriors = root / "share" / "pmars" / "warriors"
            bin_dir.mkdir(parents=True)
            warriors.mkdir(parents=True)
            exe = bin_dir / "pmars"
            exe.write_text("#!/bin/sh\n")
            exe.chmod(0o755)
            w1 = warriors / "excalibur.red"
            w2 = warriors / "sonofvain.red"
            w1.write_text(";redcode\n")
            w2.write_text(";redcode\n")
            pmars_item = next(a for a in start_mod.ACTIVITIES if a["id"] == "pmars")
            with patch("shutil.which", return_value=str(exe)):
                cmd = start_mod.resolve_command(pmars_item)
            self.assertEqual(cmd, ["pmars", "-e", str(w1), str(w2)])

    def test_frotz_empty_prompt_shows_version_and_returns(self):
        frotz_item = next(a for a in start_mod.ACTIVITIES if a["id"] == "frotz")
        with patch("builtins.input", side_effect=[""]), \
             patch("builtins.print"), \
             patch("subprocess.run") as mock_run:
            cmd = start_mod.resolve_command(frotz_item)
            self.assertIsNone(cmd)
            mock_run.assert_called_once_with(["frotz", "-v"])


if __name__ == "__main__":
    unittest.main()
