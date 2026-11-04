"""Every QML child boundary must isolate the shell's graphics provider."""
from pathlib import Path
import re
import unittest

DESKTOP = Path(__file__).resolve().parents[1]


def block_end(text, start):
    depth = 0
    quote = None
    comment = None
    i = start
    while i < len(text):
        char, pair = text[i], text[i:i + 2]
        if comment == "line":
            if char == "\n": comment = None
        elif comment == "block":
            if pair == "*/": comment = None; i += 1
        elif quote:
            if char == "\\": i += 1
            elif char == quote: quote = None
        elif pair == "//": comment = "line"; i += 1
        elif pair == "/*": comment = "block"; i += 1
        elif char in "\"'`": quote = char
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise ValueError("Unclosed QML block")


def inventory(desktop=DESKTOP):
    rows = []
    for root in (desktop / "shell", desktop / "plugins"):
        for path in sorted(root.rglob("*.qml")):
            text = path.read_text()
            for match in re.finditer(r"(?<![\w.])Process\s*\{", text):
                body = text[match.end():block_end(text, match.end() - 1)]
                closed = bool(re.search(r"clearEnvironment\s*:\s*true", body))
                isolated = bool(re.search(r"environment\s*:\s*Util\.hostEnvironment\(", body))
                rows.append({"file": str(path.relative_to(desktop)),
                             "line": text.count("\n", 0, match.start()) + 1,
                             "kind": "Process", "closed": closed, "isolated": isolated})
            for match in re.finditer(r"Quickshell\.execDetached\(", text):
                rows.append({"file": str(path.relative_to(desktop)),
                             "line": text.count("\n", 0, match.start()) + 1,
                             "kind": "execDetached", "closed": False,
                             "isolated": text[match.end():].startswith("Util.hostArgv(")})
    return rows


def without_graphics_isolation(text):
    text = re.sub(r"(?m)^ *environment: Util\.hostEnvironment\(\)\n", "", text)
    start = 0
    while True:
        start = text.find("Util.hostArgv(", start)
        if start == -1: break
        opening = start + len("Util.hostArgv")
        # All detached calls use argv expressions. Reuse the quoted-block
        # scanner with parentheses to find the wrapper, never its arguments.
        end = block_end(text.translate(str.maketrans({"(": "{", ")": "}"})), opening)
        text = text[:start] + text[opening + 1:end] + text[end + 1:]
    return text


class LaunchEnvironment(unittest.TestCase):
    def test_every_child_boundary_is_isolated(self):
        rows = inventory()
        self.assertTrue(rows)
        self.assertEqual([r for r in rows if not (r["closed"] or r["isolated"])], [])

    def test_inheriting_processes_import_the_helper(self):
        for row in inventory():
            if row["isolated"]:
                with self.subTest(row=row):
                    self.assertRegex((DESKTOP / row["file"]).read_text(), r"(?m)^import Tam.Commons$")

    def test_no_alternate_process_api_bypasses_the_boundary(self):
        for root in (DESKTOP / "shell", DESKTOP / "plugins"):
            for path in root.rglob("*.qml"):
                # These APIs may replace the environment configured on Process.
                self.assertNotRegex(path.read_text(), r"\.(?:exec|startDetached)\s*\(", str(path))

    def test_host_environment_strips_shell_qt_and_path(self):
        """Fault H: menu launches must not inherit Nix Qt or shell PATH."""
        util = (DESKTOP / "shell/modules/Tam/Commons/Util.qml").read_text()
        for key in (
            "QT_PLUGIN_PATH",
            "NIXPKGS_QT6_QML_IMPORT_PATH",
            "QML_IMPORT_PATH",
            "QT_QPA_PLATFORM",
            "PATH",
        ):
            with self.subTest(key=key):
                self.assertIn(f'"{key}"', util)
        self.assertIn("TAMLINUX_LAUNCH_HOST_ENV", util)
        self.assertIn("TAMLINUX_HOST_PRESENT", util)
        self.assertIn("launchHostKeys", util)

    def test_session_start_records_launch_host_backups(self):
        import importlib.util

        path = DESKTOP / "shell/host/session_start.py"
        spec = importlib.util.spec_from_file_location("session_start", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        env = {
            "PATH": "/home/fred/.local/bin:/nix/store/aaaa/bin:/usr/bin",
            "QT_QPA_PLATFORM": "wayland",
            "QML_IMPORT_PATH": "/shell/modules",
            "QT_PLUGIN_PATH": "/nix/store/qt/plugins",
            "HOME": "/home/fred",
        }
        module.save_launch_host_environment(env, {
            "PATH": "/home/fred/.local/bin:/usr/local/bin:/usr/bin",
            "QT_QPA_PLATFORM": "wayland;xcb",
        })
        self.assertEqual(
            env["TAMLINUX_LAUNCH_HOST_ENV"],
            "QT_PLUGIN_PATH NIXPKGS_QT6_QML_IMPORT_PATH QML_IMPORT_PATH QT_QPA_PLATFORM PATH",
        )
        self.assertEqual(env["TAMLINUX_HOST_QT_QPA_PLATFORM"], "wayland;xcb")
        self.assertEqual(env["TAMLINUX_HOST_PATH"], "/home/fred/.local/bin:/usr/local/bin:/usr/bin")
        self.assertNotIn("TAMLINUX_HOST_QT_PLUGIN_PATH", env)
        self.assertNotIn("TAMLINUX_HOST_QML_IMPORT_PATH", env)
        self.assertIn("PATH", env["TAMLINUX_HOST_PRESENT"])
        self.assertIn("QT_QPA_PLATFORM", env["TAMLINUX_HOST_PRESENT"])
        self.assertNotIn("QT_PLUGIN_PATH", env["TAMLINUX_HOST_PRESENT"])


if __name__ == "__main__":
    unittest.main()
