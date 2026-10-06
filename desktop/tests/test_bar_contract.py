"""Bar-widget contract: every reached name is declared where it is looked up."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(os.environ.get("TAMLINUX_CONTRACT_ROOT") or Path(__file__).resolve().parents[1])
SHELL = DESKTOP / "shell"
OMARCHY_UI = Path("/usr/share/omarchy/shell/Ui")
OMARCHY_UI_GONE = "Omarchy's Ui directory is gone (stage 0.6)"

SCRATCH = os.environ.get("TAMLINUX_TEST_SCRATCH") or None
if not SCRATCH:
    worktree = Path(__file__).resolve().parents[2]
    for agent in ("agy", "opencode"):
        agent_scratch = Path.home() / "Code" / "tamlinux" / "worktrees" / agent / "scratch"
        if f"worktrees/{agent}" in str(worktree) and agent_scratch.is_dir():
            SCRATCH = str(agent_scratch)

PROPERTY_RE = re.compile(
    r"(?:readonly\s+)?property\s+(?!alias\b)"
    r"([A-Za-z_][A-Za-z0-9_.<>,\[\]]*)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
ALIAS_RE = re.compile(r"(?:readonly\s+)?property\s+alias\s+([A-Za-z_][A-Za-z0-9_]*)")
FUNCTION_RE = re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)")
SIGNAL_RE = re.compile(r"\bsignal\s+([A-Za-z_][A-Za-z0-9_]*)")
GROUP_PROP_RE = re.compile(
    r"property\s+QtObject\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*QtObject\s*\{"
)
ROOT_TYPE_RE = re.compile(r"\s*([A-Z][A-Za-z0-9_]*)\s*\{")
TYPE_INST_RE = re.compile(r"(?<![A-Za-z0-9_.])([A-Z][A-Za-z0-9_]*)\s*\{")
SERVICE_RE = re.compile(r'firstPartyServiceFor\(\s*"([^"]*)"')
BINDING_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*:")

BAR_PREFIX = "bar."
BAR_SHELL_PREFIX = "bar.shell."
SINGLETONS = ("Style", "Color", "Util", "Border")


def strip_text(text: str) -> str:
    """Remove comments and empty string literals, honouring backslash escapes."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i = min(i + 2, n)
            continue
        if c in ('"', "'", "`"):
            quote = c
            out.append(c)
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == quote:
                    out.append(c)
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def string_literals(text: str) -> list[str]:
    """Contents of string literals in raw text, skipping comments."""
    lits: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i = min(i + 2, n)
            continue
        if c in ('"', "'"):
            quote = c
            i += 1
            chars: list[str] = []
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    chars.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == quote:
                    break
                chars.append(text[i])
                i += 1
            lits.append("".join(chars))
            i += 1
            continue
        i += 1
    return lits


def match_block(text: str, open_idx: int) -> str:
    """Return the text from text[open_idx] ('{') through its matching '}'."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i = min(i + 2, n)
            continue
        if c in ('"', "'", "`"):
            quote = c
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx : i + 1]
        i += 1
    return text[open_idx:]


def declared_names(text: str) -> set[str]:
    """Names declared by property/alias/function/signal in stripped text."""
    names: set[str] = set()
    for match in ALIAS_RE.finditer(text):
        names.add(match.group(1))
    for match in PROPERTY_RE.finditer(text):
        names.add(match.group(2))
    for match in FUNCTION_RE.finditer(text):
        names.add(match.group(1))
    for match in SIGNAL_RE.finditer(text):
        names.add(match.group(1))
    return names


def groups_from(text: str) -> dict[str, set[str]]:
    """Declared names of each `property QtObject G: QtObject {` group block."""
    groups: dict[str, set[str]] = {}
    for match in GROUP_PROP_RE.finditer(text):
        brace = text.find("{", match.start())
        if brace < 0:
            continue
        groups[match.group(1)] = declared_names(match_block(text, brace))
    return groups


def root_type_of(stripped: str) -> str | None:
    for line in stripped.splitlines():
        match = ROOT_TYPE_RE.match(line)
        if match:
            return match.group(1)
    return None


def type_chain(ui_dir: Path, type_name: str, cache: dict) -> set[str]:
    """Declared names of TYPE.qml plus its root type's chain; cycle-guarded."""
    key = (str(ui_dir), type_name)
    if key in cache:
        return cache[key]
    names: set[str] = set()
    seen: set[str] = set()
    current: str | None = type_name
    while current and current not in seen:
        seen.add(current)
        qml = ui_dir / f"{current}.qml"
        if not qml.is_file():
            break
        stripped = strip_text(qml.read_text(encoding="utf-8"))
        names |= declared_names(stripped)
        parent = root_type_of(stripped)
        if parent and (ui_dir / f"{parent}.qml").is_file():
            current = parent
        else:
            break
    cache[key] = names
    return names


def depth_one_bindings(block: str) -> set[str]:
    """Lowercase-first-letter `name:` bindings directly inside a TYPE block."""
    names: set[str] = set()
    i = 1
    n = len(block)
    depth = 0
    while i < n - 1:
        c = block[i]
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            match = BINDING_RE.match(block, i)
            if match and (i == 1 or block[i - 1] in " \t\n\r;{"):
                name = match.group(1)
                if name[:1].islower():
                    names.add(name)
                i = match.end()
                continue
        i += 1
    return names


def find_function_block(raw: str, name: str) -> str | None:
    token = f"function {name}"
    idx = 0
    while True:
        found = raw.find(token, idx)
        if found < 0:
            return None
        if found == 0 or not (raw[found - 1].isalnum() or raw[found - 1] == "_"):
            brace = raw.find("{", found)
            if brace >= 0:
                return match_block(raw, brace)
        idx = found + 1


def panel_shell_block(panel_host_raw: str) -> str | None:
    idx = panel_host_raw.find("id: panelShell")
    if idx < 0:
        return None
    brace = panel_host_raw.rfind("{", 0, idx)
    if brace < 0:
        return None
    return match_block(panel_host_raw, brace)


def qmldir_types(path: Path, *, second_word_for_singleton: bool) -> set[str]:
    types: set[str] = set()
    if not path.is_file():
        return types
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("module"):
            continue
        words = stripped_line.split()
        if not words:
            continue
        if second_word_for_singleton and words[0] == "singleton" and len(words) >= 2:
            types.add(words[1])
        elif not (second_word_for_singleton and words[0] == "singleton"):
            types.add(words[0])
    return types


class Lookups:
    def __init__(self, api, bar_shell, panel_shell, singletons, groups, tam_ui, omarchy_types, tam_ui_dir, omarchy_ui):
        self.api = api
        self.bar_shell = bar_shell
        self.panel_shell = panel_shell
        self.singletons = singletons
        self.groups = groups
        self.tam_ui = tam_ui
        self.omarchy_types = omarchy_types
        self.tam_ui_dir = tam_ui_dir
        self.omarchy_ui = omarchy_ui
        self.chain_cache: dict = {}


def load_lookups(desktop: Path, omarchy_ui: Path | None) -> Lookups:
    shell = desktop / "shell"
    api_raw = (shell / "host" / "BarApi.qml").read_text(encoding="utf-8")
    shell_raw = (shell / "shell.qml").read_text(encoding="utf-8")
    panel_host_raw = (shell / "host" / "PanelHost.qml").read_text(encoding="utf-8")
    ps_block = panel_shell_block(panel_host_raw)

    singletons: dict[str, set[str]] = {}
    groups: dict[str, dict[str, set[str]]] = {}
    for name in SINGLETONS:
        path = shell / "modules" / "Tam" / "Commons" / f"{name}.qml"
        stripped = strip_text(path.read_text(encoding="utf-8")) if path.is_file() else ""
        singletons[name] = declared_names(stripped)
        groups[name] = groups_from(stripped)

    tam_ui_dir = shell / "modules" / "Tam" / "Ui"
    tam_ui = qmldir_types(tam_ui_dir / "qmldir", second_word_for_singleton=False)
    if omarchy_ui is not None and omarchy_ui.is_dir():
        omarchy_types = qmldir_types(omarchy_ui / "qmldir", second_word_for_singleton=True)
    else:
        omarchy_types = set()

    return Lookups(
        api=declared_names(strip_text(api_raw)),
        bar_shell=declared_names(strip_text(shell_raw)),
        panel_shell=declared_names(strip_text(ps_block)) if ps_block else set(),
        singletons=singletons,
        groups=groups,
        tam_ui=tam_ui,
        omarchy_types=omarchy_types,
        tam_ui_dir=tam_ui_dir,
        omarchy_ui=omarchy_ui,
    )


def scanned_files(shell: Path) -> list[str]:
    paths: list[str] = []
    bar = shell / "bar"
    if bar.is_dir():
        paths.extend(p.relative_to(shell).as_posix() for p in bar.rglob("*.qml"))
    panels = shell / "panels"
    if panels.is_dir():
        paths.extend(p.relative_to(shell).as_posix() for p in panels.glob("*/Panel.qml"))
    return sorted(paths)


def _bar_lookbehind_ok(stripped: str, start: int) -> bool:
    """True when `bar` at start is not part of Style./Color. (word chars already excluded by regex)."""
    before = stripped[max(0, start - 7) : start]
    return not (before.endswith("Style.") or before.endswith("Color."))


def gaps_for_stripped(rel: str, stripped: str, raw: str, shell_names: set[str], lk: Lookups) -> list[str]:
    gaps: list[str] = []
    omarchy_available = lk.omarchy_ui is not None and lk.omarchy_ui.is_dir()

    # R1: bar.NAME; `root.bar.x` counts, `Style.bar.x` does not.
    for match in re.finditer(r"(?<![A-Za-z0-9_])bar\.([A-Za-z_][A-Za-z0-9_]*)", stripped):
        name = match.group(1)
        if name == "shell":
            continue
        if not _bar_lookbehind_ok(stripped, match.start()):
            continue
        if name not in lk.api:
            gaps.append(f"{rel}: {BAR_PREFIX}{name}")

    # R2: bar.shell.NAME; same lookbehind as R1.
    for match in re.finditer(
        r"(?<![A-Za-z0-9_])bar\.shell\.([A-Za-z_][A-Za-z0-9_]*)", stripped
    ):
        name = match.group(1)
        if not _bar_lookbehind_ok(stripped, match.start()):
            continue
        if name not in shell_names:
            gaps.append(f"{rel}: {BAR_SHELL_PREFIX}{name}")

    for match in re.finditer(
        r"(?<![A-Za-z0-9_.])shell\.([A-Za-z_][A-Za-z0-9_]*)", stripped
    ):
        if name := match.group(1):
            if name not in shell_names:
                gaps.append(f"{rel}: shell.{name}")

    for singleton in SINGLETONS:
        for match in re.finditer(
            rf"(?<![A-Za-z0-9_.]){singleton}\.([A-Za-z_][A-Za-z0-9_]*)", stripped
        ):
            name = match.group(1)
            if name not in lk.singletons[singleton]:
                gaps.append(f"{rel}: {singleton}.{name}")

    for singleton in ("Style", "Color"):
        for match in re.finditer(
            rf"(?<![A-Za-z0-9_.]){singleton}\.([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)",
            stripped,
        ):
            group_name, key = match.group(1), match.group(2)
            group_map = lk.groups.get(singleton, {})
            if group_name in group_map and key not in group_map[group_name]:
                gaps.append(f"{rel}: {singleton}.{group_name}.{key}")

    if omarchy_available:
        for match in TYPE_INST_RE.finditer(stripped):
            type_name = match.group(1)
            if type_name in lk.omarchy_types and type_name not in lk.tam_ui:
                gaps.append(f"{rel}: type {type_name}")
        for match in TYPE_INST_RE.finditer(stripped):
            type_name = match.group(1)
            if type_name not in lk.tam_ui:
                continue
            if lk.omarchy_ui is None or not (lk.omarchy_ui / f"{type_name}.qml").is_file():
                continue
            block = match_block(stripped, match.end() - 1)
            om_chain = type_chain(lk.omarchy_ui, type_name, lk.chain_cache)
            tam_chain = type_chain(lk.tam_ui_dir, type_name, lk.chain_cache)
            for name in depth_one_bindings(block):
                if name in om_chain and name not in tam_chain:
                    gaps.append(f"{rel}: {type_name}.{name}")

    if rel.startswith("bar/"):
        shell_raw_path = lk.tam_ui_dir.parents[2] / "shell.qml"
    else:
        shell_raw_path = lk.tam_ui_dir.parents[2] / "host" / "PanelHost.qml"
    if rel.startswith("bar/"):
        fn_block = find_function_block(shell_raw_path.read_text(encoding="utf-8"), "firstPartyServiceFor")
    else:
        ps = panel_shell_block(shell_raw_path.read_text(encoding="utf-8"))
        fn_block = find_function_block(ps, "firstPartyServiceFor") if ps else None
    service_lits = set(string_literals(fn_block)) if fn_block else set()
    for service_id in SERVICE_RE.findall(raw):
        if service_id not in service_lits:
            gaps.append(f"{rel}: service {service_id}")

    return gaps


def collect_gaps(desktop: Path, omarchy_ui: Path | None) -> tuple[list[str], list[str]]:
    shell = desktop / "shell"
    lk = load_lookups(desktop, omarchy_ui)
    gaps: list[str] = []
    files = scanned_files(shell)
    for rel in files:
        raw = (shell / rel).read_text(encoding="utf-8")
        # `bar?.shell?.x` reaches the same names as `bar.shell.x`; strings are
        # already emptied, so this cannot touch a literal.
        stripped = strip_text(raw).replace("?.", ".")
        if rel.startswith("bar/"):
            shell_names = lk.bar_shell
        else:
            shell_names = lk.panel_shell
        gaps.extend(gaps_for_stripped(rel, stripped, raw, shell_names, lk))
    return sorted(set(gaps)), files


def write_fake_tree(root: Path, *, omarchy: bool = True) -> Path:
    shell = root / "shell"
    (shell / "host").mkdir(parents=True, exist_ok=True)
    (shell / "modules" / "Tam" / "Commons").mkdir(parents=True, exist_ok=True)
    (shell / "modules" / "Tam" / "Ui").mkdir(parents=True, exist_ok=True)
    (shell / "bar" / "widgets").mkdir(parents=True, exist_ok=True)

    (shell / "host" / "BarApi.qml").write_text(
        "QtObject {\n"
        "  function run(command) {}\n"
        '  property color foreground: "#ffffff"\n'
        "}\n",
        encoding="utf-8",
    )
    (shell / "shell.qml").write_text(
        "ShellRoot {\n"
        "  function summon(id) { return true }\n"
        "}\n",
        encoding="utf-8",
    )
    (shell / "host" / "PanelHost.qml").write_text(
        "Item {\n"
        "  QtObject { id: panelShell; function hide() {} }\n"
        "  function summon() {}\n"
        "}\n",
        encoding="utf-8",
    )
    (shell / "modules" / "Tam" / "Commons" / "Style.qml").write_text(
        "QtObject {\n"
        "  property int cornerRadius: 8\n"
        "  readonly property QtObject bar: QtObject {\n"
        "    readonly property int iconSlot: 1\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    for name in ("Color", "Util", "Border"):
        (shell / "modules" / "Tam" / "Commons" / f"{name}.qml").write_text(
            "QtObject {}\n", encoding="utf-8"
        )
    (shell / "modules" / "Tam" / "Ui" / "qmldir").write_text(
        "module Tam.Ui\n"
        "BarIconButton 1.0 BarIconButton.qml\n"
        "WidgetButton 1.0 WidgetButton.qml\n",
        encoding="utf-8",
    )
    if omarchy:
        ui = root / "Ui"
        ui.mkdir(parents=True, exist_ok=True)
        (ui / "qmldir").write_text(
            "module qs.Ui\n"
            "BarIconButton 1.0 BarIconButton.qml\n"
            "WidgetButton 1.0 WidgetButton.qml\n"
            "BarIndicator 1.0 BarIndicator.qml\n",
            encoding="utf-8",
        )
        (ui / "WidgetButton.qml").write_text(
            "Item {\n"
            "  property real textRotation: 0\n"
            "}\n",
            encoding="utf-8",
        )
    return shell


class RuleTests(unittest.TestCase):
    """The readers on synthetic trees under scratch."""

    def run_contract(
        self,
        file_rel: str,
        content: str,
        *,
        extra: dict[str, str] | None = None,
        shell_qml: str | None = None,
        omarchy: bool = True,
    ) -> list[str]:
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            root = Path(temporary)
            shell = write_fake_tree(root, omarchy=omarchy)
            if shell_qml is not None:
                (shell / "shell.qml").write_text(shell_qml, encoding="utf-8")
            if extra:
                for rel, text in extra.items():
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")
            target = shell / file_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            omarchy_ui = root / "Ui" if omarchy else None
            gaps, _ = collect_gaps(root, omarchy_ui)
            return gaps

    def test_c1_bar_api_names_pass(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  x: root.bar.run()\n"
            "  y: bar.foreground\n"
            "}\n",
        )
        self.assertEqual(gaps, [])

    def test_c2_missing_bar_api_name(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  x: root.bar.layoutConfig\n"
            "}\n",
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: bar.layoutConfig"])

    def test_c3_comments_and_strings_are_stripped(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  // bar.nope\n"
            "  /* bar.nope2 */\n"
            '  s: "bar.nope3"\n'
            "}\n",
        )
        self.assertEqual(gaps, [])

    def test_c4_style_group_key(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  x: Style.bar.iconSlot\n"
            "  y: Style.bar.iconCanvas\n"
            "  z: Style.cornerRadius\n"
            "}\n",
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: Style.bar.iconCanvas"])

    def test_c5_shell_lookup_uses_shell_qml(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  x: Quickshell.execDetached([])\n"
            "  y: bar.shell.summon()\n"
            "  z: shell.hide()\n"
            "}\n",
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: shell.hide"])

    def test_c15_optional_chaining_is_seen(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  x: bar?.shell?.summon()\n"
            "  y: bar?.shell?.nope()\n"
            "  z: root.bar?.nope2\n"
            "}\n",
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: bar.nope2", "bar/widgets/W.qml: bar.shell.nope"])

    def test_c6_omarchy_only_type(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  BarIndicator {}\n"
            "}\n",
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: type BarIndicator"])

    def test_c7_omarchy_only_chain_key(self):
        tam_bar_icon = "WidgetButton {\n}\n"
        tam_widget = 'Item {\n  property string text: ""\n}\n'
        om_bar_icon = "WidgetButton {\n}\n"
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  BarIconButton { textRotation: 90 }\n"
            "}\n",
            extra={
                "shell/modules/Tam/Ui/BarIconButton.qml": tam_bar_icon,
                "shell/modules/Tam/Ui/WidgetButton.qml": tam_widget,
                "Ui/BarIconButton.qml": om_bar_icon,
            },
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: BarIconButton.textRotation"])

    def test_c8_tam_chain_declares_the_key(self):
        tam_bar_icon = "WidgetButton {\n}\n"
        tam_widget = 'Item {\n  property string text: ""\n  property real textRotation: 0\n}\n'
        om_bar_icon = "WidgetButton {\n}\n"
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  BarIconButton { textRotation: 90 }\n"
            "}\n",
            extra={
                "shell/modules/Tam/Ui/BarIconButton.qml": tam_bar_icon,
                "shell/modules/Tam/Ui/WidgetButton.qml": tam_widget,
                "Ui/BarIconButton.qml": om_bar_icon,
            },
        )
        self.assertEqual(gaps, [])

    def test_c9_service_id_missing_from_shell_function(self):
        shell_qml = (
            "ShellRoot {\n"
            "  function summon(id) { return true }\n"
            '  function firstPartyServiceFor(id) { if (id === "tamlinux.media") return null }\n'
            "}\n"
        )
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            '  x: bar.shell.firstPartyServiceFor("tamlinux.idle")\n'
            "}\n",
            shell_qml=shell_qml,
        )
        self.assertEqual(gaps, ["bar/widgets/W.qml: service tamlinux.idle"])

    def test_c10_service_id_present_in_shell_function(self):
        shell_qml = (
            "ShellRoot {\n"
            "  function summon(id) { return true }\n"
            '  function firstPartyServiceFor(id) { if (id === "tamlinux.media" || id === "tamlinux.idle") return null }\n'
            "}\n"
        )
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            '  x: bar.shell.firstPartyServiceFor("tamlinux.idle")\n'
            "}\n",
            shell_qml=shell_qml,
        )
        self.assertEqual(gaps, [])

    def test_c11_panel_shell_block_only(self):
        gaps = self.run_contract(
            "panels/p/Panel.qml",
            "Item {\n"
            "  x: shell.hide()\n"
            "  y: bar.shell.summon()\n"
            "}\n",
        )
        self.assertEqual(gaps, ["panels/p/Panel.qml: bar.shell.summon"])

    def test_c12_panel_singleton_gap(self):
        gaps = self.run_contract(
            "panels/p/Panel.qml",
            "Item {\n"
            "  x: Util.alpha(1)\n"
            "}\n",
        )
        self.assertEqual(gaps, ["panels/p/Panel.qml: Util.alpha"])

    def test_c13_type_chain_cycle_returns(self):
        extra = {
            "shell/modules/Tam/Ui/qmldir": (
                "module Tam.Ui\n"
                "BarIconButton 1.0 BarIconButton.qml\n"
                "WidgetButton 1.0 WidgetButton.qml\n"
                "A 1.0 A.qml\n"
                "B 1.0 B.qml\n"
            ),
            "shell/modules/Tam/Ui/A.qml": "B {\n}\n",
            "shell/modules/Tam/Ui/B.qml": "A {\n}\n",
            "Ui/qmldir": (
                "module qs.Ui\n"
                "BarIconButton 1.0 BarIconButton.qml\n"
                "WidgetButton 1.0 WidgetButton.qml\n"
                "BarIndicator 1.0 BarIndicator.qml\n"
                "A 1.0 A.qml\n"
                "B 1.0 B.qml\n"
            ),
            "Ui/A.qml": "B {\n}\n",
            "Ui/B.qml": "A {\n}\n",
        }
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  A { foo: 1 }\n"
            "}\n",
            extra=extra,
        )
        self.assertEqual(gaps, [])

    def test_c14_missing_omarchy_skips_r6_and_r8(self):
        gaps = self.run_contract(
            "bar/widgets/W.qml",
            "Item {\n"
            "  BarIndicator {}\n"
            "  z: Style.cornerRadius\n"
            "}\n",
            omarchy=False,
        )
        self.assertEqual(gaps, [])


class ContractTests(unittest.TestCase):
    """The real tree under DESKTOP."""

    def test_k1_real_tree_gap_list_is_empty(self):
        # Without Omarchy's Ui directory (stage 0.6) only R6 and R8 stop.
        omarchy = OMARCHY_UI if OMARCHY_UI.is_dir() else None
        gaps, _ = collect_gaps(DESKTOP, omarchy)
        if gaps:
            self.fail("\n".join(gaps))

    def test_k2_scanned_file_list(self):
        omarchy = OMARCHY_UI if OMARCHY_UI.is_dir() else None
        _, scanned = collect_gaps(DESKTOP, omarchy)
        shell = DESKTOP / "shell"
        bar_files = sorted(
            p.relative_to(shell).as_posix() for p in (shell / "bar").rglob("*.qml")
        )
        panel_files = sorted(
            p.relative_to(shell).as_posix() for p in (shell / "panels").glob("*/Panel.qml")
        )
        expected = set(bar_files) | set(panel_files)
        missing = sorted(expected - set(scanned))
        self.assertEqual(missing, [], f"scanned list missing {missing}")
        self.assertGreaterEqual(len(scanned), 15, f"scanned {len(scanned)} files")
        for rel in scanned:
            self.assertTrue(
                rel.startswith("bar/") or rel.startswith("panels/"),
                f"scanned file outside bar/ and panels/: {rel}",
            )

    def test_k3_lookup_targets_are_not_empty(self):
        omarchy = OMARCHY_UI if OMARCHY_UI.is_dir() else None
        lk = load_lookups(DESKTOP, omarchy)
        self.assertTrue(lk.api, "API is empty")
        self.assertTrue(lk.bar_shell, "BAR_SHELL is empty")
        self.assertTrue(lk.panel_shell, "PANEL_SHELL is empty")
        for name in SINGLETONS:
            self.assertTrue(lk.singletons[name], f"singleton {name} is empty")
        self.assertTrue(lk.groups.get("Style", {}).get("bar"), "GROUPS['Style']['bar'] is empty")
        self.assertTrue(lk.tam_ui, "TAM_UI is empty")


if __name__ == "__main__":
    unittest.main()
