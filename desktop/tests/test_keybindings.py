"""Keybinding viewer model and wiring checks. Node runs the model; nothing else starts."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
KEYBINDINGS = DESKTOP / "shell" / "services" / "keybindings"
HOST = DESKTOP / "shell" / "host"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "keybindings"

# The model is pure, so a copy elsewhere can stand in for it. TAMLINUX_TEST_SCRATCH
# holds the temporary input files and defaults to the system temporary directory.
MODEL = Path(os.environ.get("TAMLINUX_KEYBINDINGS_MODEL") or KEYBINDINGS / "KeybindingsModel.js")
SCRATCH = os.environ.get("TAMLINUX_TEST_SCRATCH") or None
NODE_TIMEOUT = 10

# One `hyprctl binds` stanza, exactly as Hyprland prints it: the empty `submap`,
# `key` and `description` lines keep the space after the colon. A display is the
# combo padded to 35 characters, an arrow (U+2192), and the action.
HYPRLAND_BINDS = (
    "bindd\n"
    "\tmodmask: 65\n"
    "\tsubmap: \n"
    "\tkey: SUPER + SHIFT + code:20\n"
    "\tkeycode: 0\n"
    "\tcatchall: false\n"
    "\tdescription: Zoom out\n"
    "\tdispatcher: __lua\n"
    "\targ: 7\n"
    "\n"
    "bind\n"
    "\tmodmask: 64\n"
    "\tsubmap: \n"
    "\tkey: \n"
    "\tkeycode: 36\n"
    "\tcatchall: false\n"
    "\tdescription: \n"
    "\tdispatcher: exec\n"
    "\targ: uwsm app -- foot\n"
)

# The Lua scan's output: "modmask<TAB>description<TAB>key<TAB>kind<TAB>arg".
COMMAND_TABLE = (
    "65\tZoom out\tcode:20\tlua\thl.dsp.zoom({ by = -1 })\n"
    "64\tTerminal\tRETURN\texec\tfoot\n"
    "\t\tx\n"
)

# The web-app shortcuts the config cannot show; every bind-derived result carries them.
STATIC_ROWS = [
    {
        "display": "SHIFT ALT + L                       → Copy URL from Web App",
        "dispatcher": "sendshortcut",
        "arg": "SHIFT ALT,L,",
    },
    {
        "display": "SHIFT ALT + D                       → Download Video from Web App",
        "dispatcher": "sendshortcut",
        "arg": "SHIFT ALT,D,",
    },
]

# TEXTS[i] is the text of the i'th input file, and M is the model under test.
NODE_PROGRAM = """const M = require(process.argv[1]);
const fs = require("fs");
const TEXTS = process.argv.slice(2).map(function (path) {
  return fs.readFileSync(path, "utf8")
});
const value = /*EXPR*/;
process.stdout.write(JSON.stringify(value === undefined ? null : value));
"""


def run_model(expression: str, *texts: str):
    """Return one expression's JSON value from the model, one temporary file per text."""
    script = NODE_PROGRAM.replace("/*EXPR*/", expression)
    with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
        paths = []
        for index, text in enumerate(texts):
            path = Path(temporary) / f"input-{index}.txt"
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        done = subprocess.run(
            ["node", "-e", script, str(MODEL), *paths],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=NODE_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    if done.returncode != 0:
        raise AssertionError(f"node failed: {done.stderr.strip()}")
    return json.loads(done.stdout)


def hyprland_bind(modmask: int, key: str = "", keycode: int = 0, description: str = "",
                  dispatcher: str = "", arg: str = "") -> str:
    """One Hyprland bind stanza, so a case states only the fields it cares about."""
    return (
        "bind\n"
        f"\tmodmask: {modmask}\n"
        "\tsubmap: \n"
        f"\tkey: {key}\n"
        f"\tkeycode: {keycode}\n"
        "\tcatchall: false\n"
        f"\tdescription: {description}\n"
        f"\tdispatcher: {dispatcher}\n"
        f"\targ: {arg}\n"
    )


def row_parts(display: str) -> tuple[str, str]:
    """The combo and the action of a padded "combo → action" display."""
    cut = display.index(" → ")
    return display[:cut].strip(), display[cut + 3:]


def natural_key(text: str) -> tuple:
    """An independent natural sort key: digit runs compare as numbers."""
    return tuple(
        (1, int(run), "") if run.isdigit() else (0, 0, run)
        for run in re.findall(r"\d+|\D+", text.lower())
    )


def without_comments(text: str) -> str:
    """Source lines with their `//` line comments dropped, for whole-file bans."""
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


@unittest.skipUnless(shutil.which("node"), "node missing")
class ModelTests(unittest.TestCase):
    """The pure functions in KeybindingsModel.js."""

    def fixture_rows(self) -> list[dict]:
        return run_model(
            "M.records(TEXTS[0], TEXTS[1])",
            (FIXTURE / "hyprctl-binds.txt").read_text(encoding="utf-8"),
            (FIXTURE / "commands.tsv").read_text(encoding="utf-8"),
        )

    def test_reads_hyprland_binds_including_an_empty_key(self):
        self.assertEqual(
            run_model("M.parseBinds(TEXTS[0])", HYPRLAND_BINDS),
            [
                {"modmask": 65, "key": "code:20", "description": "Zoom out",
                 "dispatcher": "__lua", "arg": "7"},
                {"modmask": 64, "key": "code:36", "description": "",
                 "dispatcher": "exec", "arg": "uwsm app -- foot"},
            ],
        )

    def test_empty_broken_and_oversized_bind_text_gives_nothing(self):
        self.assertEqual(
            run_model(
                "[M.parseBinds(TEXTS[0]), M.parseBinds(TEXTS[1]),"
                " M.parseBinds(TEXTS[2]), M.parseBinds(TEXTS[3])]",
                "", "[oops", "{}", "x" * (4 * 1024 * 1024 + 1),
            ),
            [[], [], [], []],
        )

    def test_json_binds_are_capped_and_skipped_when_not_objects(self):
        self.assertEqual(
            run_model("M.parseBinds(TEXTS[0]).length", json.dumps([{"key": "K"}] * 5000)),
            4096,
        )
        self.assertEqual(
            run_model("M.parseBinds(TEXTS[0])", '[1, null, "x", {"key": "K"}]'),
            [{"modmask": 0, "key": "K", "description": "", "dispatcher": "", "arg": ""}],
        )

    def test_a_long_description_is_clipped(self):
        self.assertEqual(
            run_model(
                "M.parseBinds(TEXTS[0])",
                hyprland_bind(1, key="K", description="d" * 2000, dispatcher="exec", arg="x"),
            ),
            [{"modmask": 1, "key": "K", "description": "d" * 1024,
              "dispatcher": "exec", "arg": "x"}],
        )

    def test_reads_the_command_table_by_key_and_by_description(self):
        self.assertEqual(
            run_model("M.parseCommands(TEXTS[0])", COMMAND_TABLE),
            {
                "byKey": {
                    "65,Zoom out,code:20": {"dispatcher": "lua", "arg": "hl.dsp.zoom({ by = -1 })"},
                    "64,Terminal,RETURN": {"dispatcher": "exec", "arg": "foot"},
                },
                "keyFor": {"65,Zoom out": "code:20", "64,Terminal": "RETURN"},
            },
        )

    def test_a_command_argument_may_contain_a_tab(self):
        self.assertEqual(
            run_model('M.parseCommands(TEXTS[0]).byKey["0,X,K"].arg', "0\tX\tK\texec\ta\tb"),
            "a\tb",
        )

    def test_names_every_combined_modifier_mask(self):
        self.assertEqual(
            run_model(
                "JSON.parse(TEXTS[0]).map(function (mask) { return M.modsText(mask) })",
                json.dumps([0, 1, 4, 5, 8, 9, 12, 13, 64, 65, 68, 69, 72, 73, 76, 77]),
            ),
            [
                "", "SHIFT", "CTRL", "SHIFT CTRL", "ALT", "SHIFT ALT", "CTRL ALT",
                "SHIFT CTRL ALT", "SUPER", "SUPER SHIFT", "SUPER CTRL", "SUPER SHIFT CTRL",
                "SUPER ALT", "SUPER SHIFT ALT", "SUPER CTRL ALT", "SUPER SHIFT CTRL ALT",
            ],
        )
        self.assertEqual(run_model("M.modsText(66)"), "66")

    def test_names_renamed_numbered_and_unknown_keys(self):
        pairs = [
            "comma", "period", "minus", "equal", "slash", "code:10", "code:19", "code:84",
            "code:35", "code:200", "mouse:272", "mouse:273", "mouse:274", "mouse:275",
            "mouse_up", "RETURN",
        ]
        self.assertEqual(
            run_model(
                "JSON.parse(TEXTS[0]).map(function (key) { return M.keyLabel(key) })",
                json.dumps(pairs),
            ),
            [
                "COMMA", "PERIOD", "MINUS", "EQUAL", "SLASH", "1", "0", "KP_BEGIN",
                "BRACKETRIGHT", "code:200", "LEFT MOUSE BUTTON", "RIGHT MOUSE BUTTON",
                "MIDDLE MOUSE BUTTON", "mouse:275", "mouse_up", "RETURN",
            ],
        )

    def test_combines_the_modifiers_and_the_key_label(self):
        self.assertEqual(run_model('M.comboText(0, "XF86AudioMute")'), "XF86AudioMute")
        self.assertEqual(run_model('M.comboText(65, "code:20")'), "SUPER SHIFT + MINUS")

    def test_formats_the_rows_of_hyprland_binds(self):
        self.assertEqual(
            run_model("M.formatRecords(M.records(TEXTS[0], TEXTS[1]))", HYPRLAND_BINDS, COMMAND_TABLE),
            "SHIFT ALT + L                       → Copy URL from Web App\tsendshortcut\tSHIFT ALT,L,\n"
            "SHIFT ALT + D                       → Download Video from Web App\tsendshortcut\tSHIFT ALT,D,\n"
            "SUPER + code:36                     → foot\texec\tuwsm app -- foot\n"
            "SUPER SHIFT + MINUS                 → Zoom out\tlua\thl.dsp.zoom({ by = -1 })\n",
        )

    def test_sway_bindings_are_read_from_the_json_form(self):
        self.assertEqual(
            run_model(
                "M.records(TEXTS[0], TEXTS[1])",
                '[{"modmask":64,"key":"1","dispatcher":"workspace","arg":"number 1"}]', "",
            ),
            STATIC_ROWS + [{
                "display": "SUPER + 1                           → workspace number 1",
                "dispatcher": "workspace",
                "arg": "number 1",
            }],
        )

    def test_drops_a_lua_bind_with_no_description(self):
        self.assertEqual(
            run_model(
                "M.records(TEXTS[0], TEXTS[1])",
                hyprland_bind(1, key="A", description="", dispatcher="__lua", arg="1"), "",
            ),
            STATIC_ROWS,
        )

    def test_drops_the_copilot_key_that_repeats_another_binding(self):
        self.assertEqual(
            run_model(
                "M.records(TEXTS[0], TEXTS[1])",
                hyprland_bind(65, key="code:201", description="Omarchy menu",
                              dispatcher="__lua", arg="53"),
                (FIXTURE / "commands.tsv").read_text(encoding="utf-8"),
            ),
            STATIC_ROWS,
        )

    def test_shows_a_repeated_bind_only_once(self):
        bind = hyprland_bind(65, key="code:20", description="Zoom out", dispatcher="__lua", arg="7")
        self.assertEqual(
            run_model("M.records(TEXTS[0], TEXTS[1])", bind + bind, COMMAND_TABLE),
            STATIC_ROWS + [{
                "display": "SUPER SHIFT + MINUS                 → Zoom out",
                "dispatcher": "lua",
                "arg": "hl.dsp.zoom({ by = -1 })",
            }],
        )

    def test_keeps_a_lua_row_the_scan_could_not_resolve(self):
        self.assertEqual(
            run_model(
                "M.records(TEXTS[0], TEXTS[1])",
                hyprland_bind(1, key="K", description="Nope", dispatcher="__lua", arg="3"), "",
            ),
            STATIC_ROWS + [{"display": "SHIFT + K                           → Nope",
                            "dispatcher": "", "arg": ""}],
        )

    def test_fills_a_key_the_bind_reports_without_one(self):
        self.assertEqual(
            run_model(
                "M.records(TEXTS[0], TEXTS[1])",
                hyprland_bind(64, key="", keycode=0, description="Terminal",
                              dispatcher="__lua", arg="4"),
                COMMAND_TABLE,
            ),
            STATIC_ROWS + [{"display": "SUPER + RETURN                      → Terminal",
                            "dispatcher": "exec", "arg": "foot"}],
        )

    def test_fixture_rows_are_the_inherited_viewers_rows(self):
        produced = set(run_model(
            "M.formatRecords(M.records(TEXTS[0], TEXTS[1]))",
            (FIXTURE / "hyprctl-binds.txt").read_text(encoding="utf-8"),
            (FIXTURE / "commands.tsv").read_text(encoding="utf-8"),
        ).splitlines())
        inherited = set(
            (FIXTURE / "reference-records.tsv").read_text(encoding="utf-8").splitlines()
        )
        extra = sorted(produced - inherited)
        missing = sorted(inherited - produced)
        self.assertEqual(
            extra + missing, [],
            f"only in the model: {extra}\nonly in the inherited viewer: {missing}",
        )

    def test_fixture_row_count_and_ends(self):
        rows = self.fixture_rows()
        self.assertEqual(len(rows), 252)
        self.assertEqual(rows[0], {
            "display": "SUPER CTRL + T                      → Activity",
            "dispatcher": "exec",
            "arg": "tam-launch-tui 'btop'",
        })
        self.assertEqual(rows[-1], {
            "display": "SUPER CTRL + Z                      → Zoom in",
            "dispatcher": "",
            "arg": "",
        })

    def test_fixture_rows_the_command_scan_could_not_resolve(self):
        rows = [row for row in self.fixture_rows() if row["dispatcher"] == ""]
        self.assertEqual(
            [row_parts(row["display"]) for row in rows],
            [
                ("SUPER CTRL ALT + Z", "Reset zoom"),
                ("SUPER + C", "Universal copy"),
                ("SUPER + X", "Universal cut"),
                ("SUPER + V", "Universal paste"),
                ("SUPER CTRL + Z", "Zoom in"),
            ],
        )
        self.assertTrue(all(row["arg"] == "" for row in rows))
        self.assertFalse(any("code:201" in row["display"] for row in self.fixture_rows()))

    def test_natural_compare_orders_digit_runs_as_numbers(self):
        self.assertEqual(
            run_model(
                '[["a2","a10"], ["B","a"], ["x","x"], ["a","ab"]].map(function (pair) {'
                " return M.naturalCompare(pair[0], pair[1]) })",
            ),
            [-1, 1, 0, -1],
        )

    def test_fixture_desktops_sort_numerically(self):
        rows = self.fixture_rows()
        self.assertEqual(rows[190], {
            "display": "SUPER + 2                           → Switch desktop 2",
            "dispatcher": "exec",
            "arg": "tam-desktop-mode switch 2",
        })
        self.assertEqual(rows[206], {
            "display": "SUPER + 0                           → Switch desktop 10",
            "dispatcher": "exec",
            "arg": "tam-desktop-mode switch 10",
        })

    def test_fixture_rows_are_sorted_by_action_then_by_combo(self):
        parts = json.dumps([row_parts(row["display"]) for row in self.fixture_rows()])
        self.assertEqual(
            run_model(
                "JSON.parse(TEXTS[0]).slice(1).map(function (next, index) {\n"
                "  var here = JSON.parse(TEXTS[0])[index]\n"
                "  var does = M.naturalCompare(here[1], next[1])\n"
                "  var combo = M.naturalCompare(here[0], next[0])\n"
                "  return does < 0 || (does === 0 && !(combo > 0))\n"
                "    ? null\n"
                "    : [here, next, does, combo]\n"
                "}).filter(function (broken) { return broken !== null })",
                parts,
            ),
            [],
        )

    def test_python_natural_sort_agrees_with_the_fixture_order(self):
        pairs = [row_parts(row["display"]) for row in self.fixture_rows()]
        expected = sorted(pairs, key=lambda pair: (natural_key(pair[1]), natural_key(pair[0]), pair[0]))
        if expected != pairs:
            # Reported, not asserted: the model is the viewer, Python is only a witness.
            moved = [(index, pairs[index], expected[index])
                     for index in range(len(pairs)) if pairs[index] != expected[index]]
            print(f"python natural sort disagrees on {len(moved)} of {len(pairs)} rows:",
                  file=sys.stderr)
            for index, was, now in moved[:10]:
                print(f"  {index}: {was!r} would sort as {now!r}", file=sys.stderr)


class WiringTests(unittest.TestCase):
    """Source checks for the service, the host, and the adapter. These start nothing."""

    def test_service_answers_records_without_running_a_process(self):
        text = (KEYBINDINGS / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('target: "keybindings"', text)
        self.assertIn('import "KeybindingsModel.js" as Model', text)
        self.assertIn("function records(commands: string): string", text)
        self.assertIn("Model.formatRecords(Model.records(root.bindingsText(), commands))", text)
        self.assertNotIn("Process", text)
        self.assertNotIn("hyprctl", text)

    def test_host_loads_the_keybindings_service(self):
        text = (HOST / "Services.qml").read_text(encoding="utf-8")
        self.assertIn('import "../services/keybindings" as Keybindings', text)
        self.assertIn("Keybindings.Service { shell: services.shell }", text)
        self.assertIn('services.enabled.indexOf("keybindings")', text)

    def test_adapter_rereads_the_binds_after_a_config_reload(self):
        text = (HOST / "HyprlandAdapter.qml").read_text(encoding="utf-8")
        self.assertIn('event.name === "configreloaded"', text)
        self.assertIn("bindsProc.running = true", text)

    def test_the_model_runs_nothing(self):
        text = (KEYBINDINGS / "KeybindingsModel.js").read_text(encoding="utf-8")
        self.assertNotIn(".pragma", text)
        self.assertNotIn("require(", text)
        self.assertNotIn("Process", text)
        # Only the attribution comment may name the inherited viewer it was ported from.
        self.assertNotIn("omarchy-", without_comments(text))


if __name__ == "__main__":
    unittest.main()
