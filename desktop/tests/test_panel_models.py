"""Behaviour tests for the panel and bar-widget models."""

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

AUDIO_MODEL = SHELL_DIR / "panels" / "audio" / "Model.js"
BLUETOOTH_MODEL = SHELL_DIR / "panels" / "bluetooth" / "Model.js"
NETWORK_MODEL = SHELL_DIR / "panels" / "network" / "Model.js"
POWER_MODEL = SHELL_DIR / "panels" / "power" / "Model.js"
WIFIQR_MODEL = SHELL_DIR / "panels" / "wifiqr" / "Model.js"
KEYBOARD_LAYOUT_MODEL = SHELL_DIR / "bar" / "widgets" / "KeyboardLayoutModel.js"
TRAY_MODEL = SHELL_DIR / "bar" / "widgets" / "TrayModel.js"

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


@unittest.skipUnless(shutil.which("node"), "node missing")
class WifiQrModelTests(unittest.TestCase):
    """The pure functions in panels/wifiqr/Model.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(WIFIQR_MODEL, expression, *texts)

    def test_parse_qr_output_empty_and_null(self):
        self.assertEqual(
            self.run_expr("M.parseQrOutput('')"),
            {"meta": {"iface": "", "security": "", "ssid": ""}, "matrix": {"rows": [], "size": 0}},
        )
        self.assertEqual(
            self.run_expr("M.parseQrOutput(null)"),
            {"meta": {"iface": "", "security": "", "ssid": ""}, "matrix": {"rows": [], "size": 0}},
        )

    def test_parse_qr_output_valid_meta_and_matrix(self):
        raw = "meta\twlan0\tWPA-PSK\tHomeNetwork\n10\n01"
        self.assertEqual(
            self.run_expr("M.parseQrOutput(TEXTS[0])", raw),
            {
                "meta": {"iface": "wlan0", "security": "WPA-PSK", "ssid": "HomeNetwork"},
                "matrix": {"rows": ["10", "01"], "size": 2},
            },
        )

    def test_parse_qr_output_ssid_with_tabs(self):
        raw = "meta\twlan0\tWPA-PSK\tHome\tWiFi\tNetwork\n1"
        self.assertEqual(
            self.run_expr("M.parseQrOutput(TEXTS[0])", raw),
            {
                "meta": {"iface": "wlan0", "security": "WPA-PSK", "ssid": "Home\tWiFi\tNetwork"},
                "matrix": {"rows": ["1"], "size": 1},
            },
        )

    def test_parse_qr_output_meta_short_fields(self):
        raw = "meta\twlan0\n1"
        self.assertEqual(
            self.run_expr("M.parseQrOutput(TEXTS[0])", raw),
            {
                "meta": {"iface": "wlan0", "security": "", "ssid": ""},
                "matrix": {"rows": ["1"], "size": 1},
            },
        )

    def test_parse_qr_output_without_meta_header(self):
        raw = "10\n01"
        self.assertEqual(
            self.run_expr("M.parseQrOutput(TEXTS[0])", raw),
            {
                "meta": {"iface": "", "security": "", "ssid": ""},
                "matrix": {"rows": ["10", "01"], "size": 2},
            },
        )

    def test_parse_qr_output_meta_not_at_start(self):
        # Line containing meta\\t not at start must not be treated as meta header (mutant M2 check)
        raw = "prefix meta\twlan0\tWPA\tSSID\n1"
        self.assertEqual(
            self.run_expr("M.parseQrOutput(TEXTS[0])", raw),
            {
                "meta": {"iface": "", "security": "", "ssid": ""},
                "matrix": {"rows": [], "size": 0},
            },
        )

    def test_parse_qr_matrix_empty(self):
        self.assertEqual(self.run_expr("M.parseQrMatrix([])"), {"rows": [], "size": 0})

    def test_parse_qr_matrix_valid_square(self):
        self.assertEqual(
            self.run_expr("M.parseQrMatrix(['101', '010', '111'])"),
            {"rows": ["101", "010", "111"], "size": 3},
        )

    def test_parse_qr_matrix_non_square_count(self):
        self.assertEqual(
            self.run_expr("M.parseQrMatrix(['10', '01', '11'])"),
            {"rows": [], "size": 0},
        )

    def test_parse_qr_matrix_jagged_row_length(self):
        self.assertEqual(
            self.run_expr("M.parseQrMatrix(['10', '0'])"),
            {"rows": [], "size": 0},
        )

    def test_parse_qr_matrix_non_binary_chars(self):
        self.assertEqual(
            self.run_expr("M.parseQrMatrix(['12', '01'])"),
            {"rows": [], "size": 0},
        )
        self.assertEqual(
            self.run_expr("M.parseQrMatrix(['1a', '01'])"),
            {"rows": [], "size": 0},
        )


@unittest.skipUnless(shutil.which("node"), "node missing")
class TrayModelTests(unittest.TestCase):
    """The pure functions in bar/widgets/TrayModel.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(TRAY_MODEL, expression, *texts)

    def test_item_named_null_and_empty(self):
        self.assertEqual(self.run_expr("M.itemNamed(null, 'localsend')"), False)
        self.assertEqual(self.run_expr("M.itemNamed({}, 'localsend')"), False)

    def test_item_named_matches_id_start(self):
        # Matches at index 0 (mutant M6 check)
        self.assertEqual(self.run_expr("M.itemNamed({ id: 'localsend' }, 'localsend')"), True)

    def test_item_named_matches_id_substring(self):
        self.assertEqual(self.run_expr("M.itemNamed({ id: 'org.localsend.app' }, 'localsend')"), True)

    def test_item_named_matches_title_and_tooltip(self):
        self.assertEqual(self.run_expr("M.itemNamed({ title: 'LocalSend Transfer' }, 'localsend')"), True)
        self.assertEqual(self.run_expr("M.itemNamed({ tooltipTitle: 'LOCALSEND Active' }, 'localsend')"), True)

    def test_item_named_no_match(self):
        self.assertEqual(
            self.run_expr("M.itemNamed({ id: 'slack', title: 'Slack', tooltipTitle: 'Slack' }, 'localsend')"),
            False,
        )

    def test_entry_id_string(self):
        self.assertEqual(self.run_expr("M.entryId('tamlinux.dropbox')"), "tamlinux.dropbox")
        self.assertEqual(self.run_expr("M.entryId('')"), "")

    def test_entry_id_object_with_id(self):
        self.assertEqual(self.run_expr("M.entryId({ id: 'tamlinux.dropbox' })"), "tamlinux.dropbox")
        self.assertEqual(self.run_expr("M.entryId({ id: 123 })"), "123")

    def test_entry_id_object_with_empty_or_null_id(self):
        self.assertEqual(self.run_expr("M.entryId({ id: '' })"), "")
        self.assertEqual(self.run_expr("M.entryId({ id: null })"), "")
        self.assertEqual(self.run_expr("M.entryId({ id: undefined })"), "")
        self.assertEqual(self.run_expr("M.entryId({})"), "")

    def test_entry_id_null_and_non_object(self):
        self.assertEqual(self.run_expr("M.entryId(null)"), "")
        self.assertEqual(self.run_expr("M.entryId(123)"), "")

    def test_layout_has_widget_null_and_empty(self):
        self.assertEqual(self.run_expr("M.layoutHasWidget(null, 'tamlinux.dropbox')"), False)
        self.assertEqual(self.run_expr("M.layoutHasWidget({}, 'tamlinux.dropbox')"), False)

    def test_layout_has_widget_found_in_sections(self):
        self.assertEqual(
            self.run_expr("M.layoutHasWidget({ left: ['tamlinux.dropbox'] }, 'tamlinux.dropbox')"),
            True,
        )
        self.assertEqual(
            self.run_expr("M.layoutHasWidget({ center: [{ id: 'tamlinux.dropbox' }] }, 'tamlinux.dropbox')"),
            True,
        )
        self.assertEqual(
            self.run_expr("M.layoutHasWidget({ right: ['tamlinux.dropbox'] }, 'tamlinux.dropbox')"),
            True,
        )

    def test_layout_has_widget_not_found(self):
        self.assertEqual(
            self.run_expr("M.layoutHasWidget({ left: ['other'], center: ['other2'], right: [] }, 'tamlinux.dropbox')"),
            False,
        )

    def test_owned_by_shell_localsend(self):
        self.assertEqual(self.run_expr("M.ownedByShell({ id: 'localsend' }, null)"), True)

    def test_owned_by_shell_dropbox(self):
        layout_with = "{ right: ['tamlinux.dropbox'] }"
        layout_without = "{ right: ['other'] }"
        self.assertEqual(self.run_expr(f"M.ownedByShell({{ id: 'dropbox' }}, {layout_with})"), True)
        self.assertEqual(self.run_expr(f"M.ownedByShell({{ id: 'dropbox' }}, {layout_without})"), False)

    def test_owned_by_shell_other_item_and_null(self):
        layout = "{ right: ['tamlinux.dropbox'] }"
        self.assertEqual(self.run_expr(f"M.ownedByShell({{ id: 'slack' }}, {layout})"), False)
        self.assertEqual(self.run_expr("M.ownedByShell(null, null)"), False)


@unittest.skipUnless(shutil.which("node"), "node missing")
class KeyboardLayoutModelTests(unittest.TestCase):
    """The pure functions in bar/widgets/KeyboardLayoutModel.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(KEYBOARD_LAYOUT_MODEL, expression, *texts)

    def test_layout_briefs_empty_and_null(self):
        self.assertEqual(self.run_expr("M.layoutBriefs('')"), {})
        self.assertEqual(self.run_expr("M.layoutBriefs(null)"), {})

    def test_layout_briefs_yaml_parsing(self):
        yaml = (
            "- layout: 'us'\n"
            "  variant: ''\n"
            "  brief: 'en'\n"
            "  description: English (US)\n"
            "- layout: 'fr'\n"
            "  brief: fr\n"
            "  description: French\n"
        )
        self.assertEqual(
            self.run_expr("M.layoutBriefs(TEXTS[0])", yaml),
            {"English (US)": "en", "French": "fr"},
        )

    def test_layout_briefs_orphan_description_ignored(self):
        yaml = "  description: Orphan Layout\n"
        self.assertEqual(self.run_expr("M.layoutBriefs(TEXTS[0])", yaml), {})

    def test_layout_briefs_reset_on_dash(self):
        yaml = (
            "  brief: 'en'\n"
            "- layout: 'de'\n"
            "  description: German\n"
        )
        self.assertEqual(self.run_expr("M.layoutBriefs(TEXTS[0])", yaml), {})

    def test_short_label_empty_and_null(self):
        self.assertEqual(self.run_expr("M.shortLabel('', {})"), "")
        self.assertEqual(self.run_expr("M.shortLabel(null, {})"), "")

    def test_short_label_brief_lookup_two_letters(self):
        self.assertEqual(self.run_expr("M.shortLabel('English (US)', { 'English (US)': 'en' })"), "EN")

    def test_short_label_brief_with_hyphen_script(self):
        self.assertEqual(self.run_expr("M.shortLabel('Burmese (Zawgyi)', { 'Burmese (Zawgyi)': 'my-zwg' })"), "MY")

    def test_short_label_brief_custom_word(self):
        self.assertEqual(self.run_expr("M.shortLabel('Custom', { 'Custom': 'dvorak' })"), "DVO")

    def test_short_label_fallback_first_word(self):
        # Substring capped at 3 chars (mutant M7 check)
        self.assertEqual(self.run_expr("M.shortLabel('English (US)', {})"), "ENG")
        self.assertEqual(self.run_expr("M.shortLabel('Portuguese (Brazil)')"), "POR")
        self.assertEqual(self.run_expr("M.shortLabel('US')"), "US")

    def test_short_label_inherited_member(self):
        self.assertEqual(self.run_expr("M.shortLabel('constructor', {})"), "CON")

    def test_event_keyboard_name_null_and_empty(self):
        self.assertEqual(self.run_expr("M.eventKeyboardName(null)"), "")
        self.assertEqual(self.run_expr("M.eventKeyboardName({})"), "")
        self.assertEqual(self.run_expr("M.eventKeyboardName({ data: '' })"), "")

    def test_event_keyboard_name_parse_method(self):
        self.assertEqual(
            self.run_expr("M.eventKeyboardName({ parse: function(n) { return ['at-kbd', 'layout']; } })"),
            "at-kbd",
        )

    def test_event_keyboard_name_parse_exception_fallback(self):
        self.assertEqual(
            self.run_expr("M.eventKeyboardName({ parse: function() { throw new Error(); }, data: 'fallback,layout' })"),
            "fallback",
        )

    def test_event_keyboard_name_data_string(self):
        self.assertEqual(self.run_expr("M.eventKeyboardName({ data: 'usb-kbd,English' })"), "usb-kbd")

    def test_event_keyboard_name_virtual_fcitx(self):
        self.assertEqual(self.run_expr("M.eventKeyboardName({ data: 'hl-virtual-keyboard,English' })"), "")
        self.assertEqual(self.run_expr("M.eventKeyboardName({ data: 'hl-virtual-keyboard-fcitx,English' })"), "")

    def test_is_typed_keyboard_untyped_prefixes(self):
        self.assertEqual(self.run_expr("M.isTypedKeyboard('hl-virtual-keyboard')"), False)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('power-button')"), False)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('sleep-button')"), False)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('lid-switch')"), False)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('video-bus')"), False)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('power-button-0')"), False)

    def test_is_typed_keyboard_typed_names(self):
        self.assertEqual(self.run_expr("M.isTypedKeyboard('at-translated-set-2-keyboard')"), True)
        self.assertEqual(self.run_expr("M.isTypedKeyboard('logitech-wireless')"), True)

    def test_is_typed_keyboard_empty_and_null(self):
        self.assertEqual(self.run_expr("M.isTypedKeyboard('')"), True)
        self.assertEqual(self.run_expr("M.isTypedKeyboard(null)"), True)

    def test_select_keyboard_empty(self):
        self.assertEqual(self.run_expr("M.selectKeyboard(null, 'k1')"), None)
        self.assertEqual(self.run_expr("M.selectKeyboard([], 'k1')"), None)

    def test_select_keyboard_matches_named_event(self):
        expr = "M.selectKeyboard([{ name: 'k1', active_layout_index: 0 }, { name: 'k2', active_layout_index: 1 }], 'k1')"
        self.assertEqual(self.run_expr(expr), {"name": "k1", "active_layout_index": 0})

    def test_select_keyboard_fallback_furthest_advanced(self):
        expr = "M.selectKeyboard([{ name: 'k1', active_layout_index: 0 }, { name: 'k2', active_layout_index: 2 }], 'other')"
        self.assertEqual(self.run_expr(expr), {"name": "k2", "active_layout_index": 2})

    def test_select_keyboard_fallback_tie_picks_first(self):
        expr = "M.selectKeyboard([{ name: 'k1', active_layout_index: 1 }, { name: 'k2', active_layout_index: 1 }], 'other')"
        self.assertEqual(self.run_expr(expr), {"name": "k1", "active_layout_index": 1})

    def test_select_keyboard_missing_active_layout_index(self):
        expr = "M.selectKeyboard([{ name: 'k1' }], 'other')"
        self.assertEqual(self.run_expr(expr), {"name": "k1"})


@unittest.skipUnless(shutil.which("node"), "node missing")
class PowerModelTests(unittest.TestCase):
    """The pure functions in panels/power/Model.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(POWER_MODEL, expression, *texts)

    def test_clamp_index_zero_or_negative_length(self):
        self.assertEqual(self.run_expr("M.clampIndex(2, 0)"), 0)
        self.assertEqual(self.run_expr("M.clampIndex(2, -1)"), 0)

    def test_clamp_index_negative_index(self):
        self.assertEqual(self.run_expr("M.clampIndex(-2, 5)"), 0)

    def test_clamp_index_within_range(self):
        self.assertEqual(self.run_expr("M.clampIndex(0, 5)"), 0)
        self.assertEqual(self.run_expr("M.clampIndex(2, 5)"), 2)
        self.assertEqual(self.run_expr("M.clampIndex(4, 5)"), 4)

    def test_clamp_index_upper_bound(self):
        # Clamped to length - 1, not length (mutant M3 check)
        self.assertEqual(self.run_expr("M.clampIndex(5, 5)"), 4)
        self.assertEqual(self.run_expr("M.clampIndex(10, 5)"), 4)
        self.assertEqual(self.run_expr("M.clampIndex(1, 1)"), 0)
        self.assertEqual(self.run_expr("M.clampIndex(2, 2)"), 1)

    def test_select_profile_index_empty(self):
        self.assertEqual(self.run_expr("M.selectProfileIndex(0, 1, null)"), 0)
        self.assertEqual(self.run_expr("M.selectProfileIndex(0, 1, [])"), 0)

    def test_select_profile_index_stepping(self):
        profiles = "['saver', 'balanced', 'perf']"
        self.assertEqual(self.run_expr(f"M.selectProfileIndex(1, 1, {profiles})"), 2)
        self.assertEqual(self.run_expr(f"M.selectProfileIndex(2, 1, {profiles})"), 2)
        self.assertEqual(self.run_expr(f"M.selectProfileIndex(1, -1, {profiles})"), 0)
        self.assertEqual(self.run_expr(f"M.selectProfileIndex(0, -1, {profiles})"), 0)

    def test_parse_key_value_empty(self):
        self.assertEqual(self.run_expr("M.parseKeyValue('')"), {})
        self.assertEqual(self.run_expr("M.parseKeyValue(null)"), {})

    def test_parse_key_value_skips_invalid_lines(self):
        raw = "notab\n\tstartingtab\nk1\t  v1  \nk2\tv2"
        self.assertEqual(
            self.run_expr("M.parseKeyValue(TEXTS[0])", raw),
            {"k1": "v1", "k2": "v2"},
        )

    def test_parse_profiles_empty(self):
        self.assertEqual(
            self.run_expr("M.parseProfiles('')"),
            {"profiles": [], "activeProfile": "", "profileIndex": 0},
        )

    def test_parse_profiles_populated_and_active(self):
        raw = "saver\t0\nbalanced\t1\nperf\t0\n"
        self.assertEqual(
            self.run_expr("M.parseProfiles(TEXTS[0], 1)", raw),
            {"profiles": ["saver", "balanced", "perf"], "activeProfile": "balanced", "profileIndex": 1},
        )

    def test_parse_profiles_clamps_previous_index(self):
        raw = "saver\t0\nbalanced\t1\n"
        self.assertEqual(
            self.run_expr("M.parseProfiles(TEXTS[0], 10)", raw),
            {"profiles": ["saver", "balanced"], "activeProfile": "balanced", "profileIndex": 1},
        )
        self.assertEqual(
            self.run_expr("M.parseProfiles(TEXTS[0])", raw),
            {"profiles": ["saver", "balanced"], "activeProfile": "balanced", "profileIndex": 0},
        )

    def test_profile_icon_named_profiles(self):
        self.assertEqual(self.run_expr("M.profileIcon('power-saver')"), "\U000f032a")
        self.assertEqual(self.run_expr("M.profileIcon('balanced')"), "\U000f029a")
        self.assertEqual(self.run_expr("M.profileIcon('performance')"), "\U000f04c5")
        self.assertEqual(self.run_expr("M.profileIcon('unknown')"), "\U000f0084")
        self.assertEqual(self.run_expr("M.profileIcon('')"), "\U000f0084")
        self.assertEqual(self.run_expr("M.profileIcon(null)"), "\U000f0084")

    def test_battery_fraction_not_present_or_null(self):
        self.assertEqual(self.run_expr("M.batteryFraction(null)"), 0)
        self.assertEqual(self.run_expr("M.batteryFraction({ isPresent: false, percentage: 0.8 })"), 0)

    def test_battery_fraction_clamped_range(self):
        self.assertEqual(self.run_expr("M.batteryFraction({ isPresent: true, percentage: 0.75 })"), 0.75)
        self.assertEqual(self.run_expr("M.batteryFraction({ isPresent: true, percentage: -0.2 })"), 0)
        self.assertEqual(self.run_expr("M.batteryFraction({ isPresent: true, percentage: 1.5 })"), 1)

    def test_charge_threshold_active_not_present_or_on_battery(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        self.assertEqual(self.run_expr(f"M.chargeThresholdActive(null, false, {states})"), False)
        self.assertEqual(self.run_expr(f"M.chargeThresholdActive({{ isPresent: false }}, false, {states})"), False)
        self.assertEqual(self.run_expr(f"M.chargeThresholdActive({{ isPresent: true }}, true, {states})"), False)

    def test_charge_threshold_active_states(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        # Discharging is false
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 1 }}, false, {states})"),
            False,
        )
        # PendingCharge is true
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 4 }}, false, {states})"),
            True,
        )
        # FullyCharged: fraction < 0.99 is true, >= 0.99 is false
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 3 }}, false, {states})"),
            True,
        )
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 1.0, state: 3 }}, false, {states})"),
            False,
        )
        # Unknown state is false
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 99 }}, false, {states})"),
            False,
        )

    def test_charge_threshold_active_charging_rate_and_time(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        # Charging with fraction >= 0.99 is false
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.99, state: 2, changeRate: 0.1 }}, false, {states})"),
            False,
        )
        # changeRate <= 0.2 is true
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 2, changeRate: 0.1 }}, false, {states})"),
            True,
        )
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 2, changeRate: 0.2 }}, false, {states})"),
            True,
        )
        # changeRate > 0.2 and timeToFull >= 8h (28800) is true
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 2, changeRate: 0.5, timeToFull: 28800 }}, false, {states})"),
            True,
        )
        # changeRate > 0.2 and timeToFull < 8h is false
        self.assertEqual(
            self.run_expr(f"M.chargeThresholdActive({{ isPresent: true, percentage: 0.8, state: 2, changeRate: 0.5, timeToFull: 28799 }}, false, {states})"),
            False,
        )

    def test_battery_icon_not_present(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        self.assertEqual(self.run_expr(f"M.batteryIcon(null, false, {states})"), "")
        self.assertEqual(self.run_expr(f"M.batteryIcon({{ isPresent: false }}, false, {states})"), "")

    def test_battery_icon_threshold_and_fully_charged(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        # threshold active uses defaultIcons
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 0.55, state: 4 }}, false, {states})"),
            "\U000f007f",
        )
        # fully charged not on battery returns fully charged glyph
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 1.0, state: 3 }}, false, {states})"),
            "\U000f0085",
        )

    def test_battery_icon_charging_and_discharging_levels(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        # not on battery, charging: changeRate=1.0 and timeToFull=3600 ensures threshold is false
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 0.05, state: 2, changeRate: 1.0, timeToFull: 3600 }}, false, {states})"),
            "\U000f089c",
        )
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 0.95, state: 2, changeRate: 1.0, timeToFull: 3600 }}, false, {states})"),
            "\U000f0085",
        )
        # on battery (discharging)
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 0.05, state: 1 }}, true, {states})"),
            "\U000f007a",
        )
        self.assertEqual(
            self.run_expr(f"M.batteryIcon({{ isPresent: true, percentage: 0.95, state: 1 }}, true, {states})"),
            "\U000f0079",
        )

    def test_mode_label_not_present(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        self.assertEqual(self.run_expr(f"M.modeLabel(null, false, {states})"), "")
        self.assertEqual(self.run_expr(f"M.modeLabel({{ isPresent: false }}, false, {states})"), "")

    def test_mode_label_states(self):
        states = "{ Discharging: 1, Charging: 2, FullyCharged: 3, PendingCharge: 4 }"
        # Threshold
        self.assertEqual(
            self.run_expr(f"M.modeLabel({{ isPresent: true, percentage: 0.8, state: 4 }}, false, {states})"),
            "Threshold",
        )
        # On battery
        self.assertEqual(
            self.run_expr(f"M.modeLabel({{ isPresent: true, percentage: 0.8, state: 1 }}, true, {states})"),
            "On battery",
        )
        # Fully charged
        self.assertEqual(
            self.run_expr(f"M.modeLabel({{ isPresent: true, percentage: 1.0, state: 3, changeRate: 1.0, timeToFull: 3600 }}, false, {states})"),
            "Fully charged",
        )
        # Charging
        self.assertEqual(
            self.run_expr(f"M.modeLabel({{ isPresent: true, percentage: 0.8, state: 2, changeRate: 1.0, timeToFull: 3600 }}, false, {states})"),
            "Charging",
        )


@unittest.skipUnless(shutil.which("node"), "node missing")
class BluetoothModelTests(unittest.TestCase):
    """The pure functions in panels/bluetooth/Model.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(BLUETOOTH_MODEL, expression, *texts)

    def test_device_label_null_and_empty(self):
        self.assertEqual(self.run_expr("M.deviceLabel(null)"), "")
        self.assertEqual(self.run_expr("M.deviceLabel({})"), "")

    def test_device_label_device_name_precedence(self):
        self.assertEqual(self.run_expr("M.deviceLabel({ deviceName: 'Dev', name: 'Other' })"), "Dev")

    def test_device_label_name_fallback_and_trim(self):
        self.assertEqual(self.run_expr("M.deviceLabel({ name: '  My Speaker  ' })"), "My Speaker")

    def test_to_array_null_and_empty(self):
        self.assertEqual(self.run_expr("M.toArray(null)"), [])
        self.assertEqual(self.run_expr("M.toArray(undefined)"), [])

    def test_to_array_array_copy(self):
        self.assertEqual(self.run_expr("M.toArray(['a', 'b'])"), ["a", "b"])

    def test_to_array_array_like(self):
        self.assertEqual(self.run_expr("M.toArray({ 0: 'a', 1: 'b', length: 2 })"), ["a", "b"])
        self.assertEqual(self.run_expr("M.toArray({ length: 0 })"), [])
        self.assertEqual(self.run_expr("M.toArray({ length: -1 })"), [])

    def test_is_uuid_like_null_and_empty(self):
        self.assertEqual(self.run_expr("M.isUuidLike('')"), False)
        self.assertEqual(self.run_expr("M.isUuidLike(null)"), False)

    def test_is_uuid_like_valid_formats(self):
        self.assertEqual(self.run_expr("M.isUuidLike('12345678-1234-1234-1234-123456789abc')"), True)
        self.assertEqual(self.run_expr("M.isUuidLike('123456789abcdef0123456789abcdef0')"), True)
        self.assertEqual(self.run_expr("M.isUuidLike('0x1234')"), True)
        self.assertEqual(self.run_expr("M.isUuidLike('0000110a-0000-1000-8000-00805f9b34fb')"), True)

    def test_is_uuid_like_invalid(self):
        self.assertEqual(self.run_expr("M.isUuidLike('Sony XM4')"), False)
        self.assertEqual(self.run_expr("M.isUuidLike('1234')"), False)

    def test_is_address_like(self):
        # 6 octets matches, 5 octets does not (mutant M4 check)
        self.assertEqual(self.run_expr("M.isAddressLike('00:11:22:33:44:55')"), True)
        self.assertEqual(self.run_expr("M.isAddressLike('00-11-22-33-44-55')"), True)
        self.assertEqual(self.run_expr("M.isAddressLike('AA:BB:CC:DD:EE:FF')"), True)
        self.assertEqual(self.run_expr("M.isAddressLike('00:11:22:33:44')"), False)
        self.assertEqual(self.run_expr("M.isAddressLike('00:11:22:33:44:55:66')"), False)
        self.assertEqual(self.run_expr("M.isAddressLike('00:11:22:33:44:zz')"), False)
        self.assertEqual(self.run_expr("M.isAddressLike('')"), False)
        self.assertEqual(self.run_expr("M.isAddressLike(null)"), False)

    def test_normalized_address(self):
        self.assertEqual(self.run_expr("M.normalizedAddress('')"), "")
        self.assertEqual(self.run_expr("M.normalizedAddress(null)"), "")
        self.assertEqual(self.run_expr("M.normalizedAddress('00:11:22:AA:BB:CC')"), "001122aabbcc")
        self.assertEqual(self.run_expr("M.normalizedAddress('00-11-22-aa-bb-cc')"), "001122aabbcc")

    def test_has_human_name(self):
        self.assertEqual(self.run_expr("M.hasHumanName(null)"), False)
        self.assertEqual(self.run_expr("M.hasHumanName({})"), False)
        self.assertEqual(self.run_expr("M.hasHumanName({ name: '00:11:22:33:44:55' })"), False)
        self.assertEqual(self.run_expr("M.hasHumanName({ name: '0000110a-0000-1000-8000-00805f9b34fb' })"), False)
        self.assertEqual(self.run_expr("M.hasHumanName({ name: 'AirPods Pro' })"), True)

    def test_node_props(self):
        self.assertEqual(self.run_expr("M.nodeProps(null)"), {})
        self.assertEqual(self.run_expr("M.nodeProps({ ready: false, properties: { a: 1 } })"), {})
        self.assertEqual(self.run_expr("M.nodeProps({ ready: true, properties: { 'node.name': 'test' } })"), {"node.name": "test"})

    def test_node_text(self):
        node = "{ name: 'n1', description: 'd1', ready: true, properties: { 'device.name': 'dn1' } }"
        text = self.run_expr(f"M.nodeText({node})")
        self.assertEqual("n1" in text and "d1" in text and "dn1" in text, True)

    def test_bluetooth_sink_matches_device_null_and_non_sink(self):
        self.assertEqual(self.run_expr("M.bluetoothSinkMatchesDevice(null, { name: 'dev' })"), False)
        self.assertEqual(self.run_expr("M.bluetoothSinkMatchesDevice({ isSink: false }, { name: 'dev' })"), False)
        self.assertEqual(self.run_expr("M.bluetoothSinkMatchesDevice({ isSink: true, isStream: true }, { name: 'dev' })"), False)
        self.assertEqual(self.run_expr("M.bluetoothSinkMatchesDevice({ isSink: true }, null)"), False)

    def test_bluetooth_sink_matches_device_by_address_and_label(self):
        node_addr = "{ isSink: true, ready: true, properties: { 'bluez5.address': '00:11:22:33:44:55' } }"
        device_addr = "{ address: '00-11-22-33-44-55' }"
        self.assertEqual(self.run_expr(f"M.bluetoothSinkMatchesDevice({node_addr}, {device_addr})"), True)

        node_label = "{ isSink: true, description: 'Sony XM4' }"
        device_label = "{ name: 'Sony XM4' }"
        self.assertEqual(self.run_expr(f"M.bluetoothSinkMatchesDevice({node_label}, {device_label})"), True)

        device_mismatch = "{ name: 'Other Device', address: '99:99:99:99:99:99' }"
        self.assertEqual(self.run_expr(f"M.bluetoothSinkMatchesDevice({node_label}, {device_mismatch})"), False)

    def test_sorted_by_label(self):
        expr = "M.sortedByLabel([{ name: 'Zebra' }, { name: 'Apple' }, { name: 'Mango' }])"
        self.assertEqual(self.run_expr(expr), [{"name": "Apple"}, {"name": "Mango"}, {"name": "Zebra"}])

    def test_device_row(self):
        self.assertEqual(self.run_expr("M.deviceRow(null)"), None)
        self.assertEqual(
            self.run_expr("M.deviceRow({})"),
            {
                "address": "",
                "name": "",
                "deviceName": "",
                "connected": False,
                "state": -1,
                "batteryAvailable": False,
                "battery": 0,
                "pairing": False,
            },
        )
        populated = "{ address: '00:11', name: 'N', deviceName: 'DN', connected: true, state: 2, batteryAvailable: true, battery: 80, pairing: true }"
        self.assertEqual(
            self.run_expr(f"M.deviceRow({populated})"),
            {
                "address": "00:11",
                "name": "N",
                "deviceName": "DN",
                "connected": True,
                "state": 2,
                "batteryAvailable": True,
                "battery": 80,
                "pairing": True,
            },
        )

    def test_device_lists(self):
        devices = (
            "["
            "{ name: 'C1', connected: true },"
            "{ name: 'K1', paired: true },"
            "{ name: 'D1' },"
            "{ name: '00:11:22:33:44:55' }"  # Filtered out (not human name)
            "]"
        )
        self.assertEqual(
            self.run_expr(f"M.deviceLists({devices})"),
            {
                "connected": [{"name": "C1", "connected": True}],
                "known": [{"name": "K1", "paired": True}],
                "discovered": [{"name": "D1"}],
            },
        )

    def test_clone_map(self):
        self.assertEqual(self.run_expr("M.cloneMap(null)"), {})
        self.assertEqual(self.run_expr("M.cloneMap({ a: 1, b: 2 })"), {"a": 1, "b": 2})

    def test_pending_action(self):
        self.assertEqual(self.run_expr("M.pendingAction(null, 'addr')"), "")
        self.assertEqual(self.run_expr("M.pendingAction({}, 'addr')"), "")
        self.assertEqual(self.run_expr("M.pendingAction({ 'addr': 'pair' }, 'addr')"), "pair")

    def test_with_pending_action(self):
        self.assertEqual(self.run_expr("M.withPendingAction({ a: '1' }, null, 'pair')"), {"a": "1"})
        self.assertEqual(self.run_expr("M.withPendingAction({}, 'addr', 'pair')"), {"addr": "pair"})
        self.assertEqual(self.run_expr("M.withPendingAction({ 'addr': 'pair' }, 'addr', '')"), {})

    def test_visible_sections(self):
        lists = "{ connected: [1], known: [2], discovered: [3] }"
        self.assertEqual(self.run_expr(f"M.visibleSections({lists}, false)"), ["connected", "known"])
        self.assertEqual(self.run_expr(f"M.visibleSections({lists}, true)"), ["connected", "known", "discovered"])
        self.assertEqual(self.run_expr("M.visibleSections({}, true)"), [])

    def test_section_devices(self):
        lists = "{ connected: ['c'], known: ['k'], discovered: ['d'] }"
        self.assertEqual(self.run_expr("M.sectionDevices(null, 'connected')"), [])
        self.assertEqual(self.run_expr(f"M.sectionDevices({lists}, 'connected')"), ["c"])
        self.assertEqual(self.run_expr(f"M.sectionDevices({lists}, 'known')"), ["k"])
        self.assertEqual(self.run_expr(f"M.sectionDevices({lists}, 'discovered')"), ["d"])
        self.assertEqual(self.run_expr(f"M.sectionDevices({lists}, 'other')"), [])


@unittest.skipUnless(shutil.which("node"), "node missing")
class AudioModelTests(unittest.TestCase):
    """The pure functions in panels/audio/Model.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(AUDIO_MODEL, expression, *texts)

    def test_is_playback_stream(self):
        self.assertEqual(self.run_expr("M.isPlaybackStream(null)"), False)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: false })"), False)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: true, isSink: true })"), True)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: true, type: 'Stream/Output/Audio' })"), True)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: true, type: 'AudioOutStream' })"), True)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: true, type: 'Output' })"), True)
        self.assertEqual(self.run_expr("M.isPlaybackStream({ isStream: true, type: 'Input' })"), False)

    def test_is_audio_source(self):
        self.assertEqual(self.run_expr("M.isAudioSource(null)"), False)
        self.assertEqual(self.run_expr("M.isAudioSource({ audio: true })"), True)
        self.assertEqual(self.run_expr("M.isAudioSource({ type: 'Audio/Source' })"), True)
        self.assertEqual(self.run_expr("M.isAudioSource({ type: 'AudioSource' })"), True)
        self.assertEqual(self.run_expr("M.isAudioSource({ type: 'Source' })"), True)
        self.assertEqual(self.run_expr("M.isAudioSource({ type: 'Sink' })"), False)

    def test_list_snapshot(self):
        self.assertEqual(self.run_expr("M.listSnapshot(null)"), [])
        self.assertEqual(self.run_expr("M.listSnapshot({})"), [])
        self.assertEqual(self.run_expr("M.listSnapshot([1, 2])"), [1, 2])

    def test_output_volume_name(self):
        self.assertEqual(self.run_expr("M.outputVolumeName(0.5, true)"), "Muted")
        self.assertEqual(self.run_expr("M.outputVolumeName(0, false)"), "Silenced")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.14, false)"), "Whisper")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.15, false)"), "Murmur")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.29, false)"), "Murmur")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.30, false)"), "Easy listening")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.49, false)"), "Easy listening")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.50, false)"), "Steady groove")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.69, false)"), "Steady groove")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.70, false)"), "Cranked up")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.84, false)"), "Cranked up")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.85, false)"), "Party mode")
        self.assertEqual(self.run_expr("M.outputVolumeName(0.99, false)"), "Party mode")
        self.assertEqual(self.run_expr("M.outputVolumeName(1.00, false)"), "Concert hall")
        self.assertEqual(self.run_expr("M.outputVolumeName(1.20, false)"), "Concert hall")

    def test_parse_sink_availability(self):
        # parts[1] !== "0" means "1" is true, "0" is false (mutant M5 check)
        self.assertEqual(self.run_expr("M.parseSinkAvailability('')"), {})
        self.assertEqual(
            self.run_expr("M.parseSinkAvailability('sink1\\t1\\nsink2\\t0\\ninvalid')"),
            {"sink1": True, "sink2": False},
        )

    def test_friendly_device_label(self):
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('sof-soundwire Speakers')"), "Speakers")
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('built-in audio Analog Output')"), "Analog")
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('built-in audio Stereo Input')"), "Stereo")
        # Notice /^built-?in audio\s+/i does not match a space between 'built' and 'in'
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('built in audio Stereo Input')"), "built in audio Stereo")
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('Internal Microphones')"), "Internal Microphone")
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel('')"), "")
        self.assertEqual(self.run_expr("M.friendlyDeviceLabel(null)"), "")

    def test_node_props(self):
        self.assertEqual(self.run_expr("M.nodeProps(null)"), {})
        self.assertEqual(self.run_expr("M.nodeProps({ ready: false, properties: { a: 1 } })"), {})
        self.assertEqual(self.run_expr("M.nodeProps({ ready: true, properties: { 'node.nick': 'DAC' } })"), {"node.nick": "DAC"})

    def test_node_label(self):
        self.assertEqual(self.run_expr("M.nodeLabel(null)"), "Unknown")
        self.assertEqual(self.run_expr("M.nodeLabel({ nickname: 'My DAC' })"), "My DAC")
        self.assertEqual(self.run_expr("M.nodeLabel({ nick: 'My DAC' })"), "My DAC")
        self.assertEqual(self.run_expr("M.nodeLabel({ ready: true, properties: { 'node.nick': 'My DAC' } })"), "My DAC")
        self.assertEqual(self.run_expr("M.nodeLabel({ ready: true, properties: { 'device.profile.description': 'Stereo Output' } })"), "Stereo")
        self.assertEqual(self.run_expr("M.nodeLabel({ description: 'Generic Audio' })"), "Generic Audio")
        self.assertEqual(self.run_expr("M.nodeLabel({ ready: true, properties: { 'node.description': 'Generic Audio' } })"), "Generic Audio")
        self.assertEqual(self.run_expr("M.nodeLabel({ name: 'alsa_output.pci' })"), "alsa_output.pci")
        self.assertEqual(self.run_expr("M.nodeLabel({})"), "Unknown")

    def test_is_headphones(self):
        self.assertEqual(self.run_expr("M.isHeadphones(null)"), False)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'my-headphones' })"), True)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'my-headset' })"), True)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'my-earbud' })"), True)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'my-earphone' })"), True)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'my-airpod' })"), True)
        self.assertEqual(self.run_expr("M.isHeadphones({ name: 'desktop-speakers' })"), False)

    def test_sink_glyph(self):
        self.assertEqual(self.run_expr("M.sinkGlyph(null)"), "\U000f04c3")
        self.assertEqual(self.run_expr("M.sinkGlyph({ name: 'my-headphones' })"), "\U000f02cb")
        self.assertEqual(self.run_expr("M.sinkGlyph({ name: 'bluetooth-speaker' })"), "\U000f00af")
        self.assertEqual(self.run_expr("M.sinkGlyph({ name: 'hdmi-audio' })"), "\U000f0379")
        self.assertEqual(self.run_expr("M.sinkGlyph({ name: 'displayport-audio' })"), "\U000f0379")
        self.assertEqual(self.run_expr("M.sinkGlyph({ name: 'line-out' })"), "\U000f04c3")

    def test_source_glyph(self):
        self.assertEqual(self.run_expr("M.sourceGlyph(null)"), "\U000f036c")
        self.assertEqual(self.run_expr("M.sourceGlyph({ name: 'headset-mic' })"), "\U000f02cb")
        self.assertEqual(self.run_expr("M.sourceGlyph({ name: 'bluetooth-mic' })"), "\U000f00af")
        self.assertEqual(self.run_expr("M.sourceGlyph({ name: 'webcam-mic' })"), "\U000f0100")
        self.assertEqual(self.run_expr("M.sourceGlyph({ name: 'camera-mic' })"), "\U000f0100")
        self.assertEqual(self.run_expr("M.sourceGlyph({ name: 'internal-mic' })"), "\U000f036c")

    def test_friendly_stream_label(self):
        self.assertEqual(self.run_expr("M.friendlyStreamLabel('')"), "")
        self.assertEqual(self.run_expr("M.friendlyStreamLabel(null)"), "")
        self.assertEqual(self.run_expr("M.friendlyStreamLabel('spotify')"), "Spotify")
        self.assertEqual(self.run_expr("M.friendlyStreamLabel('Firefox')"), "Firefox")

    def test_stream_label_key(self):
        self.assertEqual(self.run_expr("M.streamLabelKey('  Spotify  ')"), "spotify")

    def test_stream_label_is_generic(self):
        self.assertEqual(self.run_expr("M.streamLabelIsGeneric('audio-src')"), True)
        self.assertEqual(self.run_expr("M.streamLabelIsGeneric('AUDIO-SRC')"), True)
        self.assertEqual(self.run_expr("M.streamLabelIsGeneric('firefox')"), False)

    def test_raw_stream_label(self):
        self.assertEqual(self.run_expr("M.rawStreamLabel(null)"), "")
        self.assertEqual(
            self.run_expr("M.rawStreamLabel({ ready: true, properties: { 'application.name': 'App' }, description: 'Desc' })"),
            "App",
        )
        self.assertEqual(self.run_expr("M.rawStreamLabel({ description: 'Desc', name: 'Node' })"), "Desc")
        self.assertEqual(
            self.run_expr("M.rawStreamLabel({ ready: true, properties: { 'media.name': 'Media' }, name: 'Node' })"),
            "Media",
        )
        self.assertEqual(
            self.run_expr("M.rawStreamLabel({ ready: true, properties: { 'node.name': 'NodeProp' }, name: 'Node' })"),
            "NodeProp",
        )
        self.assertEqual(self.run_expr("M.rawStreamLabel({ name: 'Node' })"), "Node")

    def test_mpris_player_label(self):
        self.assertEqual(self.run_expr("M.mprisPlayerLabel(null)"), "")
        self.assertEqual(self.run_expr("M.mprisPlayerLabel({ identity: 'Spotify' })"), "Spotify")
        self.assertEqual(self.run_expr("M.mprisPlayerLabel({ desktopEntry: 'vlc' })"), "vlc")

    def test_mpris_player_is_proxy(self):
        self.assertEqual(self.run_expr("M.mprisPlayerIsProxy({ dbusName: 'org.mpris.MediaPlayer2.playerctld' })"), True)
        self.assertEqual(self.run_expr("M.mprisPlayerIsProxy({ desktopEntry: 'playerctld' })"), True)
        self.assertEqual(self.run_expr("M.mprisPlayerIsProxy({ dbusName: 'org.mpris.MediaPlayer2.spotify' })"), False)

    def test_stream_represents_mpris_player(self):
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('', 'Spotify')"), False)
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('Spotify', '')"), False)
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('Spotify', 'Spotify')"), True)
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('Spotify Premium', 'Spotify')"), True)
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('VLC', 'VLC media player')"), True)
        self.assertEqual(self.run_expr("M.streamRepresentsMprisPlayer('Firefox', 'Spotify')"), False)

    def test_mpris_labels_for(self):
        p1 = "{ identity: 'Spotify', isPlaying: true, canPlay: true }"
        p2 = "{ identity: 'vlc', isPlaying: true, canPlay: true }"
        p_proxy = "{ identity: 'playerctld', desktopEntry: 'playerctld', isPlaying: true, canPlay: true }"
        p_paused = "{ identity: 'mpv', isPlaying: false, canPlay: true }"

        # Single playing candidate
        self.assertEqual(self.run_expr(f"M.mprisLabelsFor([{p1}], function() {{ return true; }})"), "Spotify")
        # Single playing proxy candidate when no playing regular
        self.assertEqual(self.run_expr(f"M.mprisLabelsFor([{p_proxy}], function() {{ return true; }})"), "playerctld")
        # Single paused regular candidate
        self.assertEqual(self.run_expr(f"M.mprisLabelsFor([{p_paused}], function() {{ return true; }})"), "mpv")
        # Multiple candidates returns empty string
        self.assertEqual(self.run_expr(f"M.mprisLabelsFor([{p1}, {p2}], function() {{ return true; }})"), "")
        # Empty players list returns empty string
        self.assertEqual(self.run_expr("M.mprisLabelsFor([], function() { return true; })"), "")

    def test_matching_mpris_stream_label(self):
        p = "{ identity: 'Spotify', isPlaying: true, canPlay: true }"
        self.assertEqual(self.run_expr(f"M.matchingMprisStreamLabel('audio-src', [{p}])"), "")
        self.assertEqual(self.run_expr(f"M.matchingMprisStreamLabel('Spotify', [{p}])"), "Spotify")

    def test_unmatched_mpris_stream_label(self):
        p = "{ identity: 'vlc', isPlaying: true, canPlay: true }"
        self.assertEqual(self.run_expr(f"M.unmatchedMprisStreamLabel('firefox', [{p}], [])"), "")
        self.assertEqual(self.run_expr(f"M.unmatchedMprisStreamLabel('audio-src', [{p}], [])"), "vlc")

    def test_stream_label(self):
        p = "{ identity: 'Spotify', isPlaying: true, canPlay: true }"
        self.assertEqual(self.run_expr("M.streamLabel(null, [], [])"), "Stream")
        self.assertEqual(self.run_expr(f"M.streamLabel({{ name: 'spotify' }}, [{p}], [])"), "Spotify")
        self.assertEqual(self.run_expr("M.streamLabel({ name: 'audio-src' }, [], [])"), "audio-src")
        self.assertEqual(self.run_expr("M.streamLabel({}, [], [])"), "Stream")

    def test_stream_represents_player(self):
        p = "{ identity: 'Spotify', isPlaying: true, canPlay: true }"
        self.assertEqual(self.run_expr("M.streamRepresentsPlayer(null, null, [], [])"), False)
        self.assertEqual(self.run_expr(f"M.streamRepresentsPlayer({{ name: 'spotify' }}, {p}, [{p}], [])"), True)
        self.assertEqual(self.run_expr(f"M.streamRepresentsPlayer({{ name: 'audio-src' }}, {p}, [{p}], [{{ name: 'audio-src' }}])"), True)
        self.assertEqual(self.run_expr(f"M.streamRepresentsPlayer({{ name: 'firefox' }}, {p}, [{p}], [])"), False)


@unittest.skipUnless(shutil.which("node"), "node missing")
class NetworkModelTests(unittest.TestCase):
    """The pure functions in panels/network/Model.js."""

    def run_expr(self, expression: str, *texts: str):
        return run_model(NETWORK_MODEL, expression, *texts)

    def test_parse_network_status_empty(self):
        self.assertEqual(
            self.run_expr("M.parseNetworkStatus('')"),
            {"kind": "disconnected", "label": "", "signalStrength": -1, "frequency": ""},
        )
        self.assertEqual(
            self.run_expr("M.parseNetworkStatus(null)"),
            {"kind": "disconnected", "label": "", "signalStrength": -1, "frequency": ""},
        )

    def test_parse_network_status_populated(self):
        raw = "wifi\tHomeNet\t75\t5ghz\n"
        self.assertEqual(
            self.run_expr("M.parseNetworkStatus(TEXTS[0])", raw),
            {"kind": "wifi", "label": "HomeNet", "signalStrength": 75, "frequency": "5ghz"},
        )

    def test_wifi_icon_for_ranges(self):
        self.assertEqual(self.run_expr("M.wifiIconFor(0)"), "\U000f092f")
        self.assertEqual(self.run_expr("M.wifiIconFor(20)"), "\U000f092f")
        self.assertEqual(self.run_expr("M.wifiIconFor(21)"), "\U000f091f")
        self.assertEqual(self.run_expr("M.wifiIconFor(40)"), "\U000f091f")
        self.assertEqual(self.run_expr("M.wifiIconFor(41)"), "\U000f0922")
        self.assertEqual(self.run_expr("M.wifiIconFor(60)"), "\U000f0922")
        self.assertEqual(self.run_expr("M.wifiIconFor(61)"), "\U000f0925")
        self.assertEqual(self.run_expr("M.wifiIconFor(80)"), "\U000f0925")
        self.assertEqual(self.run_expr("M.wifiIconFor(81)"), "\U000f0928")
        self.assertEqual(self.run_expr("M.wifiIconFor(100)"), "\U000f0928")

    def test_connection_icon_types(self):
        self.assertEqual(self.run_expr("M.connectionIcon('wifi', 75)"), "\U000f0925")
        self.assertEqual(self.run_expr("M.connectionIcon('ethernet', 0)"), "\U000f0200")
        self.assertEqual(self.run_expr("M.connectionIcon('disconnected', 0)"), "\U000f092e")

    def test_format_header_speed_invalid_and_zero(self):
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(null)"), "")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed('')"), "")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(0)"), "")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(-10)"), "")

    def test_format_header_speed_megabit_and_gigabit(self):
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(100)"), "100mbit")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(999)"), "999mbit")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(1000)"), "1gbit")
        self.assertEqual(self.run_expr("M.formatHeaderSpeed(2500)"), "2.5gbit")

    def test_format_header_freq_invalid(self):
        self.assertEqual(self.run_expr("M.formatHeaderFreq(null)"), "")
        self.assertEqual(self.run_expr("M.formatHeaderFreq('')"), "")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(0)"), "")

    def test_format_header_freq_bounds(self):
        # Boundaries testing 2.4ghz, 5ghz, 6ghz, 60ghz and fallbacks (mutant M1 check: 5925 returns 6ghz, not 5ghz)
        self.assertEqual(self.run_expr("M.formatHeaderFreq(2399)"), "2.4ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(2400)"), "2.4ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(2499)"), "2.4ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(2500)"), "2.5ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(4899)"), "4.9ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(4900)"), "5ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(5924)"), "5ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(5925)"), "6ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(7124)"), "6ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(7125)"), "7.1ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(56999)"), "57.0ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(57000)"), "60ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(70999)"), "60ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(71000)"), "71ghz")
        self.assertEqual(self.run_expr("M.formatHeaderFreq(3000)"), "3ghz")

    def test_header_detail(self):
        self.assertEqual(self.run_expr("M.headerDetail({ type: 'ethernet', speed: 1000 })"), "1gbit")
        self.assertEqual(self.run_expr("M.headerDetail({ type: 'wifi' })"), "")
        self.assertEqual(self.run_expr("M.headerDetail(null)"), "")

    def test_band_label(self):
        self.assertEqual(self.run_expr("M.bandLabel('auto')"), "Auto")
        self.assertEqual(self.run_expr("M.bandLabel('')"), "")
        self.assertEqual(self.run_expr("M.bandLabel(null)"), "")
        self.assertEqual(self.run_expr("M.bandLabel('5')"), "5ghz")

    def test_band_section_title(self):
        self.assertEqual(self.run_expr("M.bandSectionTitle('5', '5')"), "WI-FI BAND")
        self.assertEqual(self.run_expr("M.bandSectionTitle('auto', '5')"), "WI-FI BAND: 5GHZ")
        self.assertEqual(self.run_expr("M.bandSectionTitle('auto', '')"), "WI-FI BAND")

    def test_band_tooltip(self):
        self.assertEqual(self.run_expr("M.bandTooltip('auto')"), "Let Wi-Fi pick the band")
        self.assertEqual(self.run_expr("M.bandTooltip('')"), "")
        self.assertEqual(self.run_expr("M.bandTooltip(null)"), "")
        self.assertEqual(self.run_expr("M.bandTooltip('5')"), "Stay on 5ghz")

    def test_parse_band_status(self):
        self.assertEqual(
            self.run_expr("M.parseBandStatus('')"),
            {"band": "", "selected": "auto", "available": []},
        )
        raw = "band\t5\nselected\tauto\navailable\t2.4 5 6\n"
        self.assertEqual(
            self.run_expr("M.parseBandStatus(TEXTS[0])", raw),
            {"band": "5", "selected": "auto", "available": ["2.4", "5", "6"]},
        )

    def test_decode_iw_ssid(self):
        self.assertEqual(self.run_expr("M.decodeIwSsid('HomeWiFi')"), "HomeWiFi")
        self.assertEqual(self.run_expr("M.decodeIwSsid('Cafe\\\\x20WiFi')"), "Cafe WiFi")
        self.assertEqual(self.run_expr("M.decodeIwSsid('\\\\x01Control')"), "\\x01Control")
        self.assertEqual(self.run_expr("M.decodeIwSsid('\\\\x7fDelete')"), "\\x7fDelete")
        self.assertEqual(self.run_expr("M.decodeIwSsid('\\\\xZZ')"), "\\xZZ")

    def test_parse_key_value(self):
        self.assertEqual(self.run_expr("M.parseKeyValue('')"), {})
        raw = "key\tval\nssid\tCafe\\x20WiFi\nnotab\n"
        self.assertEqual(
            self.run_expr("M.parseKeyValue(TEXTS[0])", raw),
            {"key": "val", "ssid": "Cafe WiFi"},
        )

    def test_throughput_state(self):
        sample1 = "{ iface: 'wlan0', rx_bytes: '1000', tx_bytes: '500' }"
        # First sample initializes rates to 0
        state1 = self.run_expr(f"M.throughputState(null, {sample1}, 1000)")
        self.assertEqual(
            state1,
            {
                "prevIface": "wlan0",
                "prevRxBytes": 1000,
                "prevTxBytes": 500,
                "prevSampleTime": 1000,
                "downloadRate": 0,
                "uploadRate": 0,
            },
        )

        # Interface change resets rates to 0
        state_diff_iface = self.run_expr(
            f"M.throughputState({json.dumps(state1)}, {{ iface: 'eth0', rx_bytes: '2000', tx_bytes: '1000' }}, 2000)"
        )
        self.assertEqual(state_diff_iface["prevIface"], "eth0")
        self.assertEqual(state_diff_iface["downloadRate"], 0)

        # dt > 0 calculates throughput rate
        sample2 = "{ iface: 'wlan0', rx_bytes: '3000', tx_bytes: '1500' }"
        state2 = self.run_expr(f"M.throughputState({json.dumps(state1)}, {sample2}, 2000)")
        self.assertEqual(state2["downloadRate"], 2)
        self.assertEqual(state2["uploadRate"], 1)

        # dt <= 0 retains previous rate
        state3 = self.run_expr(f"M.throughputState({json.dumps(state2)}, {sample2}, 2000)")
        self.assertEqual(state3["downloadRate"], 2)
        self.assertEqual(state3["uploadRate"], 1)

    def test_ping_latency_state(self):
        sample1 = "{ iface: 'wlan0', router_ping_ms: '5.0', internet_ping_ms: '20.0' }"
        state1 = self.run_expr(f"M.pingLatencyState(null, {sample1}, 5, 5)")
        self.assertEqual(
            state1,
            {
                "pingIface": "wlan0",
                "routerPingSamples": [5],
                "internetPingSamples": [20],
                "routerPingLatency": 5,
                "internetPingLatency": 20,
                "internetPingPacketLoss": 0,
            },
        )

        sample2 = "{ iface: 'wlan0', router_ping_ms: '10.0', internet_ping_ms: null }"
        state2 = self.run_expr(f"M.pingLatencyState({json.dumps(state1)}, {sample2}, 5, 5)")
        self.assertEqual(state2["routerPingLatency"], 7.5)
        self.assertEqual(state2["internetPingPacketLoss"], 50)

    def test_ping_packet_loss_percent(self):
        self.assertEqual(self.run_expr("M.pingPacketLossPercent([])"), 0)
        self.assertEqual(self.run_expr("M.pingPacketLossPercent([10, null, 20, null])"), 50)
        self.assertEqual(self.run_expr("M.pingPacketLossPercent([10, 20])"), 0)

    def test_format_packet_loss(self):
        self.assertEqual(self.run_expr("M.formatPacketLoss(50, false)"), "--")
        self.assertEqual(self.run_expr("M.formatPacketLoss(0, true)"), "0%")
        self.assertEqual(self.run_expr("M.formatPacketLoss(-5, true)"), "0%")
        self.assertEqual(self.run_expr("M.formatPacketLoss(25, true)"), "25%")

    def test_format_bytes(self):
        self.assertEqual(self.run_expr("M.formatBytes(-1)"), "0 B")
        self.assertEqual(self.run_expr("M.formatBytes(500)"), "500 B")
        self.assertEqual(self.run_expr("M.formatBytes(2048)"), "2.0 KB")
        self.assertEqual(self.run_expr("M.formatBytes(5 * 1024 * 1024)"), "5.0 MB")
        self.assertEqual(self.run_expr("M.formatBytes(2.5 * 1024 * 1024 * 1024)"), "2.50 GB")

    def test_format_rate(self):
        self.assertEqual(self.run_expr("M.formatRate(1024)"), "1.0 KB/s")

    def test_format_ping_latency(self):
        self.assertEqual(self.run_expr("M.formatPingLatency(10, false)"), "--")
        self.assertEqual(self.run_expr("M.formatPingLatency(-1, true)"), "Timeout")
        self.assertEqual(self.run_expr("M.formatPingLatency('invalid', true)"), "Timeout")
        self.assertEqual(self.run_expr("M.formatPingLatency(4.56, true)"), "4.6 ms")
        self.assertEqual(self.run_expr("M.formatPingLatency(25.4, true)"), "25 ms")
        self.assertEqual(self.run_expr("M.formatPingLatency(0, true)"), "0 ms")

    def test_wifi_row(self):
        self.assertEqual(self.run_expr("M.wifiRow(null)"), None)
        # undefined properties like security are omitted from JSON serialization
        self.assertEqual(
            self.run_expr("M.wifiRow({})"),
            {"connected": False, "known": False, "ssid": "", "signal": 0},
        )
        self.assertEqual(
            self.run_expr("M.wifiRow({ security: null })"),
            {"connected": False, "known": False, "ssid": "", "signal": 0, "security": None},
        )
        net = "{ connected: true, known: true, name: 'Home', signalStrength: 0.85, security: 'WPA2' }"
        self.assertEqual(
            self.run_expr(f"M.wifiRow({net})"),
            {"connected": True, "known": True, "ssid": "Home", "signal": 85, "security": "WPA2"},
        )

    def test_sort_wifi_rows(self):
        rows = (
            "["
            "{ ssid: 'c', signal: 10, connected: false, known: false },"
            "{ ssid: 'b', signal: 50, connected: false, known: true },"
            "{ ssid: 'a', signal: 20, connected: true, known: true }"
            "]"
        )
        self.assertEqual(
            self.run_expr(f"M.sortWifiRows({rows})"),
            [
                {"ssid": "a", "signal": 20, "connected": True, "known": True},
                {"ssid": "b", "signal": 50, "connected": False, "known": True},
                {"ssid": "c", "signal": 10, "connected": False, "known": False},
            ],
        )

    def test_wifi_section_title(self):
        self.assertEqual(self.run_expr("M.wifiSectionTitle([], 0)"), "")
        self.assertEqual(self.run_expr("M.wifiSectionTitle([{ known: true }], -1)"), "")
        self.assertEqual(self.run_expr("M.wifiSectionTitle([{ known: true }], 5)"), "")

        nets = "[{ known: true }, { known: true }, { known: false }, { known: false }]"
        self.assertEqual(self.run_expr(f"M.wifiSectionTitle({nets}, 0)"), "KNOWN NETWORKS")
        self.assertEqual(self.run_expr(f"M.wifiSectionTitle({nets}, 1)"), "")
        self.assertEqual(self.run_expr(f"M.wifiSectionTitle({nets}, 2)"), "OTHER NETWORKS")
        self.assertEqual(self.run_expr(f"M.wifiSectionTitle({nets}, 3)"), "")

    def test_requires_credentials(self):
        self.assertEqual(self.run_expr("M.requiresCredentials('open', 'open', 'owe')"), False)
        self.assertEqual(self.run_expr("M.requiresCredentials('owe', 'open', 'owe')"), False)
        self.assertEqual(self.run_expr("M.requiresCredentials('wpa-psk', 'open', 'owe')"), True)

    def test_can_forget_network(self):
        self.assertEqual(self.run_expr("M.canForgetNetwork(null)"), False)
        self.assertEqual(self.run_expr("M.canForgetNetwork({ known: true, connected: false })"), True)
        self.assertEqual(self.run_expr("M.canForgetNetwork({ known: true, connected: true })"), False)
        self.assertEqual(self.run_expr("M.canForgetNetwork({ known: false, connected: false })"), False)

    def test_enterprise_connect_script(self):
        script = self.run_expr("M.enterpriseConnectScript")
        self.assertEqual(isinstance(script, str), True)
        self.assertEqual("u=$(uuidgen)" in script, True)
        self.assertEqual("nmcli connection add type wifi" in script, True)

    def test_network_failure_reason(self):
        reasons = "{ NoSecrets: 1, WifiAuthTimeout: 2, WifiNetworkLost: 3, WifiClientDisconnected: 4, WifiClientFailed: 5 }"
        self.assertEqual(self.run_expr(f"M.networkFailureReason(1, true, {reasons})"), "Passphrase required")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(1, false, {reasons})"), "Failed to connect")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(2, true, {reasons})"), "Wrong password")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(2, false, {reasons})"), "Failed to connect")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(3, false, {reasons})"), "Network lost")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(4, false, {reasons})"), "Disconnected")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(5, false, {reasons})"), "Connection failed")
        self.assertEqual(self.run_expr(f"M.networkFailureReason(99, false, {reasons})"), "Failed to connect")

    def test_should_reprompt_passphrase(self):
        reasons = "{ NoSecrets: 1, WifiAuthTimeout: 2, WifiNetworkLost: 3 }"
        self.assertEqual(self.run_expr(f"M.shouldRepromptPassphrase(1, false, {reasons})"), False)
        self.assertEqual(self.run_expr(f"M.shouldRepromptPassphrase(1, true, {reasons})"), True)
        self.assertEqual(self.run_expr(f"M.shouldRepromptPassphrase(2, true, {reasons})"), True)
        self.assertEqual(self.run_expr(f"M.shouldRepromptPassphrase(3, true, {reasons})"), False)


if __name__ == "__main__":
    unittest.main()
