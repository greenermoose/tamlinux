"""Parity tests for the bar layout model."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
SHELL_DIR = Path(os.environ.get("TAMLINUX_SHELL_DIR") or DESKTOP / "shell")

BAR_MODEL = SHELL_DIR / "bar" / "BarModel.js"
ORIGINAL = Path("/usr/share/omarchy/shell/plugins/bar/BarModel.js")

SCRATCH = os.environ.get("TAMLINUX_TEST_SCRATCH") or None
if not SCRATCH:
    worktree = Path(__file__).resolve().parents[2]
    agy_scratch = Path.home() / "Code" / "tamlinux" / "worktrees" / "agy" / "scratch"
    if "worktrees/agy" in str(worktree) and agy_scratch.is_dir():
        SCRATCH = str(agy_scratch)

NODE_TIMEOUT = 10

NODE_PROGRAM = """const M = require(process.argv[1]);
const fs = require("fs");
const TEXTS = process.argv.slice(2).map(function (path) {
  return fs.readFileSync(path, "utf8");
});
const value = /*EXPR*/;
process.stdout.write(JSON.stringify(value === undefined ? null : value));
"""


def run_model(model_path: Path | str, expression: str, *texts: str):
    """Return one expression's JSON value from the model, one temporary file per text."""
    script = NODE_PROGRAM.replace("/*EXPR*/", expression)
    with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
        paths = []
        for index, text in enumerate(texts):
            path = Path(temporary) / f"input-{index}.txt"
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        done = subprocess.run(
            ["node", "-e", script, str(model_path), *paths],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=NODE_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    if done.returncode != 0:
        raise AssertionError(f"node failed: {done.stderr.strip()}")
    return json.loads(done.stdout)


def wrapped(case: str, tray_id: str) -> str:
    return f'(function () {{ const TRAY = "{tray_id}"; return ({case}); }})()'


class _BarModelTestCase(unittest.TestCase):
    def check(self, case_id: str, expression: str, expected):
        with self.subTest(case=case_id):
            port = run_model(BAR_MODEL, wrapped(expression, "tamlinux.tray"))
            self.assertEqual(port, expected)
            if not ORIGINAL.is_file():
                self.skipTest(f"Parity skipped: {ORIGINAL} missing")
            original = run_model(ORIGINAL, wrapped(expression, "omarchy.tray"))
            mapped = json.loads(json.dumps(original).replace("omarchy.tray", "tamlinux.tray"))
            self.assertEqual(mapped, port)


@unittest.skipUnless(shutil.which("node"), "node missing")
class PositionAndEntries(_BarModelTestCase):
    """normalizePosition, entrySettings, entryId, moduleString, and the entry lookups."""

    def test_n1_normalize_position_top(self):
        self.check("N1", "M.normalizePosition('top')", "top")

    def test_n2_normalize_position_whitespace_trimmed(self):
        self.check("N2", "M.normalizePosition(' left ')", "left")

    def test_n3_normalize_position_invalid_defaults_to_top(self):
        self.check("N3", "M.normalizePosition('middle')", "top")

    def test_n4_normalize_position_uppercase_defaults_to_top(self):
        self.check("N4", "M.normalizePosition('BOTTOM')", "top")

    def test_n5_normalize_position_null_defaults_to_top(self):
        self.check("N5", "M.normalizePosition(null)", "top")

    def test_e1_entry_settings_drops_id(self):
        self.check("E1", "M.entrySettings({id:'a', x:1, y:'z'})", {"x": 1, "y": "z"})

    def test_e2_entry_settings_string_empty(self):
        self.check("E2", "M.entrySettings('a')", {})

    def test_e3_entry_settings_array_empty(self):
        self.check("E3", "M.entrySettings([1])", {})

    def test_e4_entry_settings_null_empty(self):
        self.check("E4", "M.entrySettings(null)", {})

    def test_i1_entry_id_string(self):
        self.check("I1", "M.entryId('a')", "a")

    def test_i2_entry_id_object_id(self):
        self.check("I2", "M.entryId({id:'b'})", "b")

    def test_i3_entry_id_numeric_id_stringified(self):
        self.check("I3", "M.entryId({id:5})", "5")

    def test_i4_entry_id_empty_string_id(self):
        self.check("I4", "M.entryId({id:''})", "")

    def test_i5_entry_id_null_id_empty(self):
        self.check("I5", "M.entryId({id:null})", "")

    def test_i6_entry_id_empty_object_empty(self):
        self.check("I6", "M.entryId({})", "")

    def test_i7_entry_id_primitive_number_empty(self):
        self.check("I7", "M.entryId(7)", "")

    def test_i8_entry_id_array_empty(self):
        self.check("I8", "M.entryId(['a'])", "")

    def test_s1_module_string_value_present(self):
        self.check("S1", "M.moduleString({id:'x', format:'HH'}, 'format', 'd')", "HH")

    def test_s2_module_string_missing_fallback(self):
        self.check("S2", "M.moduleString({id:'x'}, 'format', 'd')", "d")

    def test_s3_module_string_null_fallback(self):
        self.check("S3", "M.moduleString({id:'x', format:null}, 'format', 'd')", "d")

    def test_s4_module_string_number_and_boolean(self):
        self.check(
            "S4",
            "M.moduleString({id:'x', n:5, b:false}, 'n', 'd') + '|' + M.moduleString({id:'x', b:false}, 'b', 'd')",
            "5|false",
        )

    def test_s5_module_string_primitive_entry_fallback(self):
        self.check("S5", "M.moduleString('x', 'id', 'd')", "d")

    def test_x1_entry_index_found(self):
        self.check("X1", "M.entryIndex(['a', {id:'b'}, 'c'], 'b')", 1)

    def test_x2_entry_index_non_array_negative_one(self):
        self.check("X2", "M.entryIndex('abc', 'b')", -1)

    def test_x3_entries_before_found(self):
        self.check("X3", "M.entriesBefore(['a', {id:'b'}, 'c'], 'b')", ["a"])

    def test_x4_entries_before_first_empty(self):
        self.check("X4", "M.entriesBefore(['a', {id:'b'}, 'c'], 'a')", [])

    def test_x5_entries_before_missing_empty(self):
        self.check("X5", "M.entriesBefore(['a', 'b'], 'z')", [])

    def test_x6_entries_after_found(self):
        self.check("X6", "M.entriesAfter(['a', {id:'b'}, 'c'], 'b')", ["c"])

    def test_x7_entries_after_missing_empty(self):
        self.check("X7", "M.entriesAfter(['a', 'b'], 'z')", [])


@unittest.skipUnless(shutil.which("node"), "node missing")
class TrayAndSettingsDelta(_BarModelTestCase):
    """pinTrayToInner and inlineSettingsDelta. P5 and D10 pin inherited quirks: a second tray entry drops the first, and a key-order change counts as a settings change."""

    def test_p1_pin_tray_to_inner_right_pinned_first(self):
        self.check(
            "P1",
            "M.pinTrayToInner(['a', {id:TRAY, pinned:['x']}, 'b'], 'right')",
            [{"id": "tamlinux.tray", "pinned": ["x"]}, "a", "b"],
        )

    def test_p2_pin_tray_to_inner_left_pinned_last(self):
        self.check("P2", "M.pinTrayToInner(['a', TRAY, 'b'], 'left')", ["a", "b", "tamlinux.tray"])

    def test_p3_pin_tray_to_inner_no_tray_unchanged(self):
        self.check("P3", "M.pinTrayToInner(['a', 'b'], 'right')", ["a", "b"])

    def test_p4_pin_tray_to_inner_null_entries_empty(self):
        self.check("P4", "M.pinTrayToInner(null, 'right')", [])

    def test_p5_pin_tray_to_inner_duplicate_tray_drops_first(self):
        self.check(
            "P5",
            "M.pinTrayToInner([{id:TRAY, n:1}, 'a', {id:TRAY, n:2}], 'center')",
            ["a", {"id": "tamlinux.tray", "n": 2}],
        )

    def test_d1_inline_settings_delta_identical_empty(self):
        self.check(
            "D1",
            "M.inlineSettingsDelta({left:['a'], center:[{id:'c', f:1}], right:[]}, {left:['a'], center:[{id:'c', f:1}], right:[]})",
            [],
        )

    def test_d2_inline_settings_delta_single_value_changed(self):
        self.check(
            "D2",
            "M.inlineSettingsDelta({left:['a'], center:[{id:'c', f:1}], right:['r']}, {left:['a'], center:[{id:'c', f:2}], right:['r']})",
            [{"region": "center", "index": 0, "entry": {"id": "c", "f": 2}}],
        )

    def test_d3_inline_settings_delta_reordered_entries_null(self):
        self.check("D3", "M.inlineSettingsDelta({left:['a', 'b']}, {left:['b', 'a']})", None)

    def test_d4_inline_settings_delta_different_counts_null(self):
        self.check("D4", "M.inlineSettingsDelta({left:['a']}, {left:['a', 'b']})", None)

    def test_d5_inline_settings_delta_custom_module_change_null(self):
        self.check(
            "D5",
            "M.inlineSettingsDelta({left:[{id:'m', exec:'x'}]}, {left:[{id:'m', exec:'y'}]})",
            None,
        )

    def test_d6_inline_settings_delta_duplicate_ids_null(self):
        self.check(
            "D6",
            "M.inlineSettingsDelta({left:[{id:'d', v:1}], right:[{id:'d', v:1}]}, {left:[{id:'d', v:2}], right:[{id:'d', v:1}]})",
            None,
        )

    def test_d7_inline_settings_delta_null_base_null(self):
        self.check("D7", "M.inlineSettingsDelta(null, {left:[]})", None)

    def test_d8_inline_settings_delta_empty_objects_empty(self):
        self.check("D8", "M.inlineSettingsDelta({}, {})", [])

    def test_d9_inline_settings_delta_tray_pinned_changed(self):
        self.check(
            "D9",
            "M.inlineSettingsDelta({left:['a'], right:[{id:TRAY}]}, {left:['a'], right:[{id:TRAY, pinned:['nm-applet']}]})",
            [{"region": "right", "index": 0, "entry": {"id": "tamlinux.tray", "pinned": ["nm-applet"]}}],
        )

    def test_d10_inline_settings_delta_key_order_difference_reported(self):
        self.check(
            "D10",
            "M.inlineSettingsDelta({center:[{id:'c', f:1, g:2}]}, {center:[{id:'c', g:2, f:1}]})",
            [{"region": "center", "index": 0, "entry": {"id": "c", "g": 2, "f": 1}}],
        )


@unittest.skipUnless(shutil.which("node"), "node missing")
class CustomModules(_BarModelTestCase):
    """expandPath and the custom-module helpers."""

    def test_h1_expand_path_tilde_prefix(self):
        self.check("H1", "M.expandPath('~/x', '/h')", "/h/x")

    def test_h2_expand_path_dollar_home_prefix(self):
        self.check("H2", "M.expandPath('$HOME/y', '/h')", "/h/y")

    def test_h3_expand_path_absolute_unchanged(self):
        self.check("H3", "M.expandPath('/abs', '/h')", "/abs")

    def test_h4_expand_path_empty_returns_empty(self):
        self.check("H4", "M.expandPath('', '/h')", "")

    def test_h5_expand_path_null_returns_empty(self):
        self.check("H5", "M.expandPath(null, '/h')", "")

    def test_h6_expand_path_tilde_user_unchanged(self):
        self.check("H6", "M.expandPath('~x', '/h')", "~x")

    def test_f1_custom_module_safe_name_validation(self):
        self.check(
            "F1",
            "[M.customModuleSafeName('a'), M.customModuleSafeName('a..b'), M.customModuleSafeName('/a'), M.customModuleSafeName(''), M.customModuleSafeName(null)]",
            [True, False, False, False, False],
        )

    def test_t1_custom_module_type_detection(self):
        self.check(
            "T1",
            "[M.customModuleType({id:'m', type:'qml', exec:'x'}), M.customModuleType({id:'m', exec:'x'}), M.customModuleType({id:'m', source:'s'}), M.customModuleType({id:'m'}), M.customModuleType('m')]",
            ["qml", "command", "qml", "", ""],
        )

    def test_c1_custom_module_path_with_source(self):
        self.check("C1", "M.customModulePath({id:'m', source:'~/q.qml'}, '/h', '/c')", "/h/q.qml")

    def test_c2_custom_module_path_default_modules_dir(self):
        self.check("C2", "M.customModulePath({id:'m'}, '/h', '/c')", "/c/bar/modules/m.qml")

    def test_c3_custom_module_path_traversal_rejected(self):
        self.check("C3", "M.customModulePath({id:'../m'}, '/h', '/c')", "")

    def test_c4_custom_module_path_non_object_entry(self):
        self.check("C4", "M.customModulePath('m', '/h')", "/bar/modules/m.qml")


@unittest.skipUnless(shutil.which("node"), "node missing")
class SlotsAndDropTargets(_BarModelTestCase):
    """isDrawnSlot, pickDrawnSlot, pickPanelSlot, and nearestDropTarget. R7 pins an inherited quirk: on a tie the earlier slot wins."""

    def test_w1_is_drawn_slot_predicates(self):
        self.check(
            "W1",
            "[M.isDrawnSlot({visible:true, width:1, height:1}), M.isDrawnSlot({visible:true, width:0, height:1}), M.isDrawnSlot({visible:1, width:1, height:1}), M.isDrawnSlot(null)]",
            [True, False, False, False],
        )

    def test_w2_pick_drawn_slot_finds_first_drawn(self):
        self.check(
            "W2",
            "M.pickDrawnSlot([null, {n:'ph', visible:false, width:0, height:0}, {n:'drawn', visible:true, width:5, height:5}])",
            {"n": "drawn", "visible": True, "width": 5, "height": 5},
        )

    def test_w3_pick_drawn_slot_fallback_to_placeholder(self):
        self.check(
            "W3",
            "M.pickDrawnSlot([{n:'ph1', visible:false, width:0, height:0}, {n:'ph2', visible:true, width:0, height:4}])",
            {"n": "ph1", "visible": False, "width": 0, "height": 0},
        )

    def test_w4_pick_drawn_slot_null_returns_null(self):
        self.check("W4", "M.pickDrawnSlot(null)", None)

    def test_k1_pick_panel_slot_prefers_opened_panel(self):
        self.check(
            "K1",
            "M.pickPanelSlot([{slot:{n:'a', visible:true, width:1, height:1}, screenName:'DP-1', opened:false}, {slot:{n:'b', visible:true, width:1, height:1}, screenName:'DP-2', opened:true}], 'DP-1')",
            {"n": "b", "visible": True, "width": 1, "height": 1},
        )

    def test_k2_pick_panel_slot_matching_screen_name(self):
        self.check(
            "K2",
            "M.pickPanelSlot([{slot:{n:'a', visible:true, width:1, height:1}, screenName:'DP-1', opened:false}, {slot:{n:'b', visible:true, width:1, height:1}, screenName:'DP-2', opened:false}], 'DP-2')",
            {"n": "b", "visible": True, "width": 1, "height": 1},
        )

    def test_k3_pick_panel_slot_unmatched_screen_first_valid(self):
        self.check(
            "K3",
            "M.pickPanelSlot([{slot:{n:'a', visible:true, width:1, height:1}, screenName:'DP-1'}, null, {slot:{n:'b', visible:true, width:1, height:1}, screenName:'DP-2'}], 'HDMI-A-1')",
            {"n": "a", "visible": True, "width": 1, "height": 1},
        )

    def test_k4_pick_panel_slot_empty_screen_prefers_drawn(self):
        self.check(
            "K4",
            "M.pickPanelSlot([{slot:{n:'ph', visible:false, width:0, height:0}, screenName:'DP-1'}, {slot:{n:'drawn', visible:true, width:3, height:3}, screenName:'DP-1'}], '')",
            {"n": "drawn", "visible": True, "width": 3, "height": 3},
        )

    def test_k5_pick_panel_slot_non_array_returns_null(self):
        self.check("K5", "M.pickPanelSlot('x', 'DP-1')", None)

    def test_r1_nearest_drop_target_horizontal_after_midpoint(self):
        self.check(
            "R1",
            "M.nearestDropTarget([{slot:'a', x:0, width:10}, {slot:'b', x:20, width:10}], {x:16}, false)",
            {"slot": "b", "after": False},
        )

    def test_r2_nearest_drop_target_horizontal_before_midpoint(self):
        self.check(
            "R2",
            "M.nearestDropTarget([{slot:'a', x:0, width:10}, {slot:'b', x:20, width:10}], {x:14}, false)",
            {"slot": "a", "after": True},
        )

    def test_r3_nearest_drop_target_vertical_before_midpoint(self):
        self.check(
            "R3",
            "M.nearestDropTarget([{slot:'a', y:0, height:10}], {y:5}, true)",
            {"slot": "a", "after": False},
        )

    def test_r4_nearest_drop_target_vertical_after_midpoint(self):
        self.check(
            "R4",
            "M.nearestDropTarget([{slot:'a', y:0, height:10}], {y:6}, true)",
            {"slot": "a", "after": True},
        )

    def test_r5_nearest_drop_target_invalid_slots_null(self):
        self.check(
            "R5",
            "M.nearestDropTarget([{slot:'a', x:0, width:0}, {x:5, width:5}, null], {x:1}, false)",
            None,
        )

    def test_r6_nearest_drop_target_missing_axis_null(self):
        self.check("R6", "M.nearestDropTarget([{slot:'a', x:0, width:10}], {}, false)", None)

    def test_r7_nearest_drop_target_tie_picks_earlier_slot(self):
        self.check(
            "R7",
            "M.nearestDropTarget([{slot:'a', x:0, width:10}, {slot:'b', x:10, width:10}], {x:10}, false)",
            {"slot": "a", "after": True},
        )


@unittest.skipUnless(shutil.which("node"), "node missing")
class PortShape(_BarModelTestCase):
    """The port's header and the one intended difference from the original."""

    def test_z1_header_comments_and_blank_line(self):
        lines = BAR_MODEL.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(lines), 4)
        self.assertEqual(lines[0], "// Ported from omarchy 4.0.4 shell/plugins/bar/BarModel.js")
        self.assertEqual(
            lines[1],
            "// (MIT, Copyright (c) David Heinemeier Hansson; see ../services/LICENSE-omarchy).",
        )
        self.assertEqual(lines[2], "// Changes: owned module, id, and command names.")
        self.assertEqual(lines[3], "")

    def test_z2_body_parity_with_original(self):
        if not ORIGINAL.is_file():
            self.skipTest(f"Parity skipped: {ORIGINAL} missing")
        bar_lines = BAR_MODEL.read_text(encoding="utf-8").splitlines(keepends=True)
        bar_body = "".join(bar_lines[4:])
        orig_text = ORIGINAL.read_text(encoding="utf-8")
        mapped_orig = orig_text.replace("omarchy.tray", "tamlinux.tray")
        self.assertEqual(bar_body, mapped_orig)

    def test_z3_exported_keys_parity(self):
        self.check(
            "Z3",
            "Object.keys(M).sort()",
            [
                "customModulePath",
                "customModuleSafeName",
                "customModuleType",
                "entriesAfter",
                "entriesBefore",
                "entryId",
                "entryIndex",
                "entrySettings",
                "expandPath",
                "inlineSettingsDelta",
                "isDrawnSlot",
                "moduleString",
                "nearestDropTarget",
                "normalizePosition",
                "pickDrawnSlot",
                "pickPanelSlot",
                "pinTrayToInner",
            ],
        )

    def test_z4_no_omarchy_references_after_header(self):
        bar_lines = BAR_MODEL.read_text(encoding="utf-8").splitlines()
        body_lines = bar_lines[3:]
        self.assertNotIn("omarchy.", "\n".join(body_lines))


def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    for cls in [
        PositionAndEntries,
        TrayAndSettingsDelta,
        CustomModules,
        SlotsAndDropTargets,
        PortShape,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite
