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


if __name__ == "__main__":
    unittest.main()
