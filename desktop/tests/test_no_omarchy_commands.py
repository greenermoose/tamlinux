"""No QML or JavaScript file in the shell names an Omarchy command (plan 18 step 0.3.2 item 7)."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
SHELL = (
    Path(os.environ["TAMLINUX_SHELL_DIR"])
    if os.environ.get("TAMLINUX_SHELL_DIR")
    else DESKTOP / "shell"
)

SCRATCH = os.environ.get("TAMLINUX_TEST_SCRATCH") or None
if not SCRATCH:
    worktree = Path(__file__).resolve().parents[2]
    for agent in ("agy", "opencode"):
        agent_scratch = Path.home() / "Code" / "tamlinux" / "worktrees" / agent / "scratch"
        if f"worktrees/{agent}" in str(worktree) and agent_scratch.is_dir():
            SCRATCH = str(agent_scratch)

# Omarchy commands the shell still runs until plan 18 step 0.3.2 item 7.
# Item 7 deletes each entry as it moves the call to tam-*; when the set is
# empty, delete it.
PENDING_0_3_2 = {
    ("host/BarApi.qml", "omarchy-agent"),
    ("host/BarApi.qml", "omarchy-launch-terminal"),
    ("host/BarApi.qml", "omarchy-menu-timezone"),
    ("host/BarApi.qml", "omarchy-notification-send"),
    ("shell.qml", "omarchy-agent"),
}

TOKEN_RE = re.compile(r"(?<![A-Za-z0-9._-])omarchy-[A-Za-z0-9-]*[A-Za-z0-9]")
WIRE_NAMES = frozenset({"omarchy-action", "omarchy-glyph", "omarchy-exec-argv"})
SHELL_SUFFIXES = frozenset({".qml", ".js"})
REGEX_PUNCT = frozenset("(:,=!&|?{};+-*%<>~^[(")
REGEX_WORDS = frozenset({"return", "typeof", "case"})
QUOTES = "\"'`"


def _shell_files(shell: Path) -> list[Path]:
    """Every scanned file: *.qml and *.js under shell, recursively."""
    files = [
        path
        for path in shell.rglob("*")
        if path.is_file() and path.suffix in SHELL_SUFFIXES
    ]
    files.sort(key=lambda path: path.relative_to(shell).as_posix())
    return files


def _regex_starts(text: str, index: int) -> bool:
    """Does the '/' at index begin a regular-expression literal?"""
    previous = index - 1
    while previous >= 0 and text[previous] in " \t\r\n":
        previous -= 1
    if previous < 0:
        return True
    char = text[previous]
    if char in "+-" and previous > 0 and text[previous - 1] == char:
        # `i++ / 2` and `i-- / 2` divide; only a lone + or - opens one.
        return False
    if char in REGEX_PUNCT:
        return True
    if char.isalnum() or char in "_$":
        start = previous
        while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
            start -= 1
        return text[start + 1:previous + 1] in REGEX_WORDS
    return False


def _scan(text: str) -> list[tuple[int, str]]:
    """(line, token) for every Omarchy command named in a string literal."""
    found: list[tuple[int, str]] = []
    i = 0
    line = 1
    n = len(text)
    while i < n:
        char = text[i]
        if char == "\n":
            line += 1
            i += 1
            continue
        if char == "/" and text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if char == "/" and text.startswith("/*", i):
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    line += 1
                i += 1
            i = min(i + 2, n)
            continue
        if char in QUOTES:
            quote = char
            start_line = line
            i += 1
            content: list[str] = []
            while i < n:
                char = text[i]
                if char == "\\" and i + 1 < n:
                    content.append(char)
                    content.append(text[i + 1])
                    if text[i + 1] == "\n":
                        line += 1
                    i += 2
                    continue
                if char == quote:
                    i += 1
                    break
                if char == "\n":
                    if quote != "`":
                        break
                    line += 1
                content.append(char)
                i += 1
            body = "".join(content)
            for match in TOKEN_RE.finditer(body):
                found.append(
                    (start_line + body[: match.start()].count("\n"), match.group(0))
                )
            continue
        if char == "/" and _regex_starts(text, i):
            i += 1
            in_class = False
            while i < n:
                char = text[i]
                if char == "\\" and i + 1 < n:
                    if text[i + 1] == "\n":
                        line += 1
                    i += 2
                    continue
                if char == "\n":
                    break
                if char == "[":
                    in_class = True
                elif char == "]":
                    in_class = False
                elif char == "/" and not in_class:
                    i += 1
                    break
                i += 1
            continue
        i += 1
    return found


def find_commands(shell: Path) -> list[tuple[str, int, str]]:
    """Sorted (path relative to shell, line, token); wire names removed."""
    found: list[tuple[str, int, str]] = []
    for path in _shell_files(shell):
        relative = path.relative_to(shell).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for line, token in _scan(text):
            if token in WIRE_NAMES:
                continue
            found.append((relative, line, token))
    found.sort()
    return found


def check(
    found: list[tuple[str, int, str]], pending: set[tuple[str, str]]
) -> tuple[list[str], list[str]]:
    """Split found pairs into new (not exempt) and stale (exempt but gone)."""
    first_line: dict[tuple[str, str], int] = {}
    for path, line, token in found:
        pair = (path, token)
        if pair not in first_line or line < first_line[pair]:
            first_line[pair] = line
    pending_pairs = set(pending)
    new = sorted(
        f"{path}:{line}: {token}"
        for (path, token), line in first_line.items()
        if (path, token) not in pending_pairs
    )
    stale = sorted(
        f"{path}: {token}"
        for (path, token) in pending_pairs - set(first_line)
    )
    return new, stale


class RealTree(unittest.TestCase):
    """The rule over the real shell directory."""

    def test_k1_shell_matches_pending_set(self) -> None:
        new, stale = check(find_commands(SHELL), PENDING_0_3_2)
        hint = (
            "new ones must use tam-*; stale ones are deleted from PENDING_0_3_2"
        )
        self.assertEqual(
            (new, stale), ([], []), "\n".join(new + stale + [hint])
        )

    def test_k2_shell_file_inventory(self) -> None:
        scanned = [path.relative_to(SHELL).as_posix() for path in _shell_files(SHELL)]
        self.assertGreaterEqual(len(scanned), 90)
        for name in (
            "host/BarApi.qml",
            "shell.qml",
            "services/polkit/PolkitModel.js",
        ):
            self.assertIn(name, scanned)


class Scanner(unittest.TestCase):
    """find_commands on small trees written to scratch."""

    def scan(self, files: dict[str, str]) -> list[tuple[str, int, str]]:
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            root = Path(tmp)
            for name, content in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            return find_commands(root)

    def test_s1_double_quoted_path(self) -> None:
        found = self.scan({"a.qml": 'x: "/usr/bin/omarchy-agent"'})
        self.assertEqual(found, [("a.qml", 1, "omarchy-agent")])

    def test_s2_single_quoted_arguments(self) -> None:
        found = self.scan({"a.js": "run('omarchy-agent --pick')"})
        self.assertEqual(found, [("a.js", 1, "omarchy-agent")])

    def test_s3_template_literal(self) -> None:
        found = self.scan({"a.js": "var t = `omarchy-tmpl ${x}`"})
        self.assertEqual(found, [("a.js", 1, "omarchy-tmpl")])

    def test_s4_line_comments(self) -> None:
        found = self.scan({"a.js": "// omarchy-one\nvar a = 1 // omarchy-two"})
        self.assertEqual(found, [])

    def test_s5_block_comment(self) -> None:
        found = self.scan(
            {"a.qml": "/* omarchy-one\nomarchy-two */\nx: \"omarchy-three\""}
        )
        self.assertEqual(found, [("a.qml", 3, "omarchy-three")])

    def test_s6_comment_markers_inside_string(self) -> None:
        found = self.scan({"a.js": 'var u = "// omarchy-instring"'})
        self.assertEqual(found, [("a.js", 1, "omarchy-instring")])

    def test_s7_escape_does_not_end_string(self) -> None:
        found = self.scan({"a.js": r'var e = "a\"b"; var f = "omarchy-after"'})
        self.assertEqual(found, [("a.js", 1, "omarchy-after")])

    def test_s8_quote_inside_regular_expression(self) -> None:
        found = self.scan(
            {
                "a.js": r'var q = s.replace(/"/g, "")'
                + "\n"
                + r'var r = "omarchy-afterregex"'
            }
        )
        self.assertEqual(found, [("a.js", 2, "omarchy-afterregex")])

    def test_s9_single_quote_inside_regular_expression(self) -> None:
        found = self.scan(
            {"a.js": r"var q = s.split(/'/) // omarchy-comment" + "\n" + "var ok = 1"}
        )
        self.assertEqual(found, [])

    def test_s10_division_is_not_a_regular_expression(self) -> None:
        found = self.scan(
            {"a.js": 'var w = a / b; var v = c / d; var s = "omarchy-div"'}
        )
        self.assertEqual(found, [("a.js", 1, "omarchy-div")])

    def test_s10b_division_after_increment_or_decrement(self) -> None:
        found = self.scan(
            {"a.js": 'var n = i++ / 2; var s = "omarchy-inc"\nvar m = j-- / 2; var t = "omarchy-dec"'}
        )
        self.assertEqual(found, [("a.js", 1, "omarchy-inc"), ("a.js", 2, "omarchy-dec")])

    def test_s11_regular_expression_after_return(self) -> None:
        found = self.scan(
            {"a.js": r'return /"[/]"/.test(s) ? "omarchy-ret" : ""'}
        )
        self.assertEqual(found, [("a.js", 1, "omarchy-ret")])

    def test_s12_wire_names_removed(self) -> None:
        found = self.scan(
            {
                "a.js": 'var a = "omarchy-action"; var b = \'omarchy-glyph\'; '
                'var c = "omarchy-exec-argv"'
            }
        )
        self.assertEqual(found, [])

    def test_s13_lookalike_wire_names_kept(self) -> None:
        found = self.scan(
            {
                "a.js": 'var a = "omarchy-exec-argv2"; '
                'var b = "omarchy-actions"'
            }
        )
        self.assertEqual(
            found,
            [
                ("a.js", 1, "omarchy-actions"),
                ("a.js", 1, "omarchy-exec-argv2"),
            ],
        )

    def test_s14_token_boundaries(self) -> None:
        found = self.scan(
            {
                "a.js": 'var a = "org.omarchy-x"; var b = "my_omarchy-x"; '
                'var c = "x-omarchy-x"; var d = "omarchy-"'
            }
        )
        self.assertEqual(found, [])

    def test_s15_other_file_types_skipped(self) -> None:
        found = self.scan(
            {"notes.txt": '"omarchy-text"', "qmldir": '"omarchy-text"'}
        )
        self.assertEqual(found, [])

    def test_s16_nested_directories(self) -> None:
        found = self.scan({"x/y/Deep.qml": 'x: "omarchy-deep"'})
        self.assertEqual(found, [("x/y/Deep.qml", 1, "omarchy-deep")])


class PendingSet(unittest.TestCase):
    """check against the pending exemptions."""

    def test_p1_exempt_found(self) -> None:
        found = [("a.qml", 3, "omarchy-a")]
        pending = {("a.qml", "omarchy-a")}
        self.assertEqual(check(found, pending), ([], []))

    def test_p2_extra_found(self) -> None:
        found = [("a.qml", 3, "omarchy-a"), ("b.js", 7, "omarchy-b")]
        pending = {("a.qml", "omarchy-a")}
        self.assertEqual(check(found, pending), (["b.js:7: omarchy-b"], []))

    def test_p3_stale_exemption(self) -> None:
        found: list[tuple[str, int, str]] = []
        pending = {("a.qml", "omarchy-a")}
        self.assertEqual(check(found, pending), ([], ["a.qml: omarchy-a"]))

    def test_p4_new_and_stale(self) -> None:
        found = [("b.js", 2, "omarchy-a")]
        pending = {("a.qml", "omarchy-a")}
        self.assertEqual(
            check(found, pending), (["b.js:2: omarchy-a"], ["a.qml: omarchy-a"])
        )

    def test_p5_one_pair_on_several_lines(self) -> None:
        found = [("a.qml", 3, "omarchy-a"), ("a.qml", 9, "omarchy-a")]
        pending = {("a.qml", "omarchy-a")}
        self.assertEqual(check(found, pending), ([], []))


if __name__ == "__main__":
    unittest.main()
