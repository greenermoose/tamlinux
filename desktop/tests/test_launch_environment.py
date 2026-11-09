"""Every QML child boundary must isolate the shell's graphics provider."""
from pathlib import Path
import json
import re
import shutil
import subprocess
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
    def evaluate_host_launch(self, environment, overrides=None):
        if not shutil.which('node'):
            self.skipTest('node is required to execute the launcher JavaScript')
        util = (DESKTOP / 'shell/modules/Tam/Commons/Util.qml').read_text()
        body = util[util.index('QtObject {') + len('QtObject {'):util.index('  function isPlainObject')]
        body = re.sub(r'readonly property var (\w+):', r'const \1 =', body)
        script = ('const values = ' + json.dumps(environment) + ';\n'
                  'const Quickshell = {env: key => values[key]};\n' + body + '\n'
                  'console.log(JSON.stringify({environment: hostEnvironment(' + json.dumps(overrides) + '),'
                  'argv: hostArgv(["/usr/bin/python3", "-I", "-c", '
                  + json.dumps('import json, os; print(json.dumps(dict(os.environ)))') + '])}));')
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True, timeout=10)
        return json.loads(result.stdout)

    def test_detached_child_receives_session_environment_not_shell_qt(self):
        keys = ['QT_PLUGIN_PATH', 'NIXPKGS_QT6_QML_IMPORT_PATH', 'QML_IMPORT_PATH', 'QT_QPA_PLATFORM', 'PATH']
        env = {key: '/shell/qt-private' for key in keys}
        env.update(TAMLINUX_LAUNCH_HOST_ENV=' '.join(keys), TAMLINUX_HOST_PRESENT='PATH QT_QPA_PLATFORM',
                   TAMLINUX_HOST_PATH='/session/bin:/usr/bin', TAMLINUX_HOST_QT_QPA_PLATFORM='wayland;xcb',
                   KEEP='caller-value')
        actual = self.evaluate_host_launch(env, {'KEEP': 'process-override'})
        self.assertEqual(actual['environment']['KEEP'], 'process-override')
        self.assertEqual(actual['environment']['QT_QPA_PLATFORM'], 'wayland;xcb')
        child = subprocess.run(actual['argv'], env=env, capture_output=True, text=True, check=True, timeout=10)
        child_env = json.loads(child.stdout)
        self.assertEqual(child_env['PATH'], '/session/bin:/usr/bin')
        self.assertEqual(child_env['QT_QPA_PLATFORM'], 'wayland;xcb')
        self.assertEqual(child_env['KEEP'], 'caller-value')
        for name in keys[:3]:
            self.assertNotIn(name, child_env)
        self.assertFalse(any(name.startswith('TAMLINUX_HOST_') for name in child_env))
        self.assertNotIn('TAMLINUX_LAUNCH_HOST_ENV', child_env)

    def test_explicitly_empty_session_variable_is_preserved(self):
        env = {'QT_PLUGIN_PATH': '/shell/plugins', 'TAMLINUX_HOST_QT_PLUGIN_PATH': '',
               'TAMLINUX_LAUNCH_HOST_ENV': 'QT_PLUGIN_PATH', 'TAMLINUX_HOST_PRESENT': 'QT_PLUGIN_PATH'}
        actual = self.evaluate_host_launch(env)
        self.assertEqual(actual['environment']['QT_PLUGIN_PATH'], '')
        child = subprocess.run(actual['argv'], env=env, capture_output=True, text=True, check=True, timeout=10)
        self.assertEqual(json.loads(child.stdout)['QT_PLUGIN_PATH'], '')

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
