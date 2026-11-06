#!/usr/bin/env python3
import os
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tam-open"


def make_tool(directory, name, body):
    path = directory / name
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)
    return path


def wait_for(path, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return path.exists()


class TamOpenCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bindir = self.tmp / "bin"
        self.bindir.mkdir()
        self.marker = self.tmp / "marker"
        self.env = os.environ.copy()
        self.env["PATH"] = str(self.bindir) + ":" + self.env.get("PATH", "")
        self.env.pop("WAYLAND_DISPLAY", None)
        self.env.pop("DISPLAY", None)
        self.env.pop("EDITOR", None)

    def run_cmd(self, *args, env=None, input_data=None):
        e = (env if env is not None else self.env).copy()
        return subprocess.run(
            [str(BIN), *args],
            capture_output=True,
            text=True,
            env=e,
            input=input_data,
        )

    def test_help(self):
        p = self.run_cmd("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("tam-open", p.stdout)

    def test_version(self):
        p = self.run_cmd("--version")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "0.1.0")

    def test_unknown_option(self):
        p = self.run_cmd("--bogus")
        self.assertEqual(p.returncode, 1)
        self.assertIn("unknown option", p.stderr)

    def test_no_target(self):
        p = self.run_cmd()
        self.assertEqual(p.returncode, 1)
        self.assertIn("Usage", p.stderr)

    def test_multiple_targets(self):
        a = self.tmp / "a.txt"
        b = self.tmp / "b.txt"
        a.write_text("a")
        b.write_text("b")
        p = self.run_cmd(str(a), str(b))
        self.assertEqual(p.returncode, 1)
        self.assertIn("only one target", p.stderr)

    def test_url_graphical(self):
        make_tool(self.bindir, "tam-launch-browser",
                  f'printf "%s\\n" "$@" > "{self.marker}"')
        env = self.env.copy()
        env["WAYLAND_DISPLAY"] = "wayland-1"
        p = self.run_cmd("https://example.com", env=env)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(wait_for(self.marker))
        self.assertIn("https://example.com", self.marker.read_text())

    def test_url_tty(self):
        make_tool(self.bindir, "lynx", f'printf "%s\\n" "$@" > "{self.marker}"')
        p = self.run_cmd("https://example.com")
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.assertIn("https://example.com", self.marker.read_text())

    def test_directory_tty(self):
        d = self.tmp / "dir"
        d.mkdir()
        (d / "file.txt").write_text("x")
        p = self.run_cmd(str(d))
        self.assertEqual(p.returncode, 0)
        self.assertIn("file.txt", p.stdout)

    def test_directory_graphical(self):
        make_tool(self.bindir, "tam-launch-nautilus",
                  f'printf "%s\\n" "$@" > "{self.marker}"')
        env = self.env.copy()
        env["DISPLAY"] = ":0"
        d = self.tmp / "dir2"
        d.mkdir()
        p = self.run_cmd(str(d), env=env)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(wait_for(self.marker))
        self.assertIn(str(d), self.marker.read_text())

    def test_pdf_graphical(self):
        make_tool(self.bindir, "zathura", f'printf "%s\\n" "$@" > "{self.marker}"')
        env = self.env.copy()
        env["WAYLAND_DISPLAY"] = "wayland-1"
        f = self.tmp / "doc.pdf"
        f.write_bytes(b"%PDF-1.4\n")
        p = self.run_cmd(str(f), env=env)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(wait_for(self.marker))
        self.assertIn(str(f), self.marker.read_text())

    def test_pdf_tty(self):
        make_tool(self.bindir, "pdftotext", 'printf "PDF TEXT\\n"')
        make_tool(self.bindir, "less", 'cat')
        f = self.tmp / "doc.pdf"
        f.write_bytes(b"%PDF-1.4\n")
        p = self.run_cmd(str(f))
        self.assertEqual(p.returncode, 0)
        self.assertIn("PDF TEXT", p.stdout)

    def test_image_tty_fails(self):
        import base64
        f = self.tmp / "image.png"
        f.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAAADUExURf8AABniCTcAAAAHdElNRQfqCwYNCDDPaNV+AAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDI2LTExLTA2VDEzOjA4OjQ4KzAwOjAwG85jWQAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyNi0xMS0wNlQxMzowODo0OCswMDowMGqT2+UAAAAodEVYdGRhdGU6dGltZXN0YW1wADIwMjYtMTEtMDZUMTM6MDg6NDgrMDA6MDA9hvo6AAAACklEQVQI12NgAAAAAgAB4iG8MwAAAABJRU5ErkJggg=="))
        p = self.run_cmd(str(f))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("text console", p.stderr)

    def test_text_file(self):
        make_tool(self.bindir, "micro", f'printf "%s\\n" "$@" > "{self.marker}"')
        f = self.tmp / "notes.txt"
        f.write_text("hello\n")
        p = self.run_cmd(str(f))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.assertIn(str(f), self.marker.read_text())

    def test_binary_fallback(self):
        make_tool(self.bindir, "hexyl", f'printf "%s\\n" "$@" > "{self.marker}"')
        f = self.tmp / "blob.bin"
        f.write_bytes(os.urandom(256))
        p = self.run_cmd(str(f))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.assertIn(str(f), self.marker.read_text())

    def test_edit_flag(self):
        make_tool(self.bindir, "hexedit", f'printf "%s\\n" "$@" > "{self.marker}"')
        f = self.tmp / "blob.bin"
        f.write_bytes(os.urandom(256))
        p = self.run_cmd("--edit", str(f))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())

    def test_unknown_fails_without_xdg(self):
        f = self.tmp / "mystery"
        f.write_bytes(os.urandom(64))
        env = self.env.copy()
        env["PATH"] = str(self.bindir)
        p = self.run_cmd(str(f), env=env)
        self.assertNotEqual(p.returncode, 0)
        # Ensure no silent success claim: diagnostic or fallback accepted.
        self.assertTrue(p.returncode == 0 or "no hex viewer" in p.stderr or "detected type" in p.stderr)

    def test_leading_dash_path(self):
        make_tool(self.bindir, "micro", f'printf "%s\\n" "$@" > "{self.marker}"')
        f = self.tmp / "-weird.txt"
        f.write_text("hi")
        p = self.run_cmd("--", str(f))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())

    def test_file_url(self):
        make_tool(self.bindir, "micro", f'printf "%s\\n" "$@" > "{self.marker}"')
        f = self.tmp / "notes.txt"
        f.write_text("hello")
        p = self.run_cmd("file://" + str(f))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
