"""Border specs, wheel steps, and the typed action boundary. These tests launch nothing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP / "shell" / "host"))

import ui_contract as contract  # noqa: E402


class BorderTests(unittest.TestCase):
    def test_flat_and_surface_use_the_fallback(self):
        spec = contract.flat("#8eb6c9", 2)
        self.assertEqual(contract.top(spec), 2)
        self.assertEqual(contract.bottom(spec), 2)
        self.assertIsNone(spec["gradient"])
        popups = contract.surface_spec("popups", "border", "#3c4a54", 1)
        ignored = contract.surface_spec("/etc/passwd", "border", "#3c4a54", 1)
        self.assertEqual(popups, ignored)
        self.assertEqual(popups["color"], "#3c4a54")
        self.assertEqual(contract.top(popups), 1)

    def test_control_spec_picks_a_fallback_color(self):
        focus = contract.control_spec("focus", "#d7dde2", "#8eb6c9")
        hover = contract.control_spec("hover-cursor", "#d7dde2", "#8eb6c9")
        normal = contract.control_spec("normal", "#d7dde2", "#8eb6c9")
        self.assertEqual(focus["color"], "#8eb6c9")
        self.assertEqual(hover["color"], "#8eb6c9")
        self.assertEqual(normal["color"], "#d7dde2")
        self.assertEqual(contract.top(focus), 1)
        self.assertFalse(contract.needs_overlay(focus))
        self.assertTrue(contract.can_use_native(focus))
        self.assertFalse(contract.can_use_native(contract.none()))

    def test_rejects_a_bad_width(self):
        self.assertEqual(contract.top(contract.flat("#fff", -1)), 0)
        self.assertEqual(contract.top(contract.flat("#fff", float("nan"))), 0)
        self.assertEqual(contract.top(contract.flat("#fff", True)), 0)
        self.assertEqual(contract.top(None), 0)

    def test_proof_lines_match_the_contract(self):
        self.assertEqual(
            contract.proof_border_line(),
            "ui-border flat-top=2 surface-top=1 control-top=1 "
            "focus-accent=true normal-foreground=true overlay=false",
        )
        self.assertEqual(contract.proof_wheel_line(), "ui-wheel 1,0 0,60 1,0 0,-20")
        self.assertIn("display=24", contract.proof_token_line("1"))
        self.assertIn("base=15", contract.proof_token_line("1.25"))
        self.assertIn("control=35", contract.proof_token_line("1.25"))
        self.assertIn("slot=26", contract.proof_token_line("1.25"))


class WheelTests(unittest.TestCase):
    def test_notch_and_sign_change(self):
        self.assertEqual(contract.wheel_steps(0, 120), {"steps": 1, "remainder": 0})
        self.assertEqual(contract.wheel_steps(0, 240), {"steps": 1, "remainder": 0})
        self.assertEqual(contract.wheel_steps(0, 60), {"steps": 0, "remainder": 60})
        self.assertEqual(contract.wheel_steps(60, 60), {"steps": 1, "remainder": 0})
        self.assertEqual(contract.wheel_steps(100, -20), {"steps": 0, "remainder": -20})
        self.assertEqual(contract.wheel_steps(-30, -100), {"steps": -1, "remainder": -10})


class ActionBoundaryTests(unittest.TestCase):
    def test_actions_do_not_start_a_process(self):
        bar = (DESKTOP / "shell" / "host" / "BarApi.qml").read_text(encoding="utf-8")
        util = (DESKTOP / "shell" / "modules" / "Tam" / "Commons" / "Util.qml").read_text(encoding="utf-8")
        border = (DESKTOP / "shell" / "modules" / "Tam" / "Commons" / "Border.qml").read_text(encoding="utf-8")
        for name in ("pickAgent", "openTerminal", "notify", "openTimezoneMenu", "run"):
            self.assertIn(f"function {name}", bar)
        self.assertIn('recordAction("open-terminal btop")', bar)
        self.assertNotIn("execDetached", bar)
        self.assertNotIn("execDetached", util)
        self.assertIn("function wheelSteps", util)
        self.assertNotIn("hyprctl", bar)
        self.assertNotIn("Quickshell.Io", bar)
        self.assertNotIn("Process", bar)
        self.assertNotIn("sh -c", bar)
        self.assertNotIn("/usr/share/omarchy", border)
        self.assertNotIn("theme", border.lower())
        helper = Path(contract.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", helper)
        self.assertNotIn("Popen", helper)

    def test_new_qml_stays_off_hyprland(self):
        names = (
            "Border.qml", "BarIconButton.qml", "BorderSurface.qml", "CursorSurface.qml",
            "Dropdown.qml", "PanelHero.qml", "PanelSectionHeader.qml", "PanelSlider.qml",
            "ToggleSwitch.qml",
        )
        for name in names:
            matches = list(DESKTOP.rglob(name))
            self.assertEqual(len(matches), 1, name)
            text = matches[0].read_text(encoding="utf-8")
            self.assertNotIn("Quickshell.Hyprland", text, name)
            self.assertNotIn("hyprctl", text, name)
            self.assertNotIn("execDetached", text, name)

    def test_ui_fixture_is_not_a_plugin(self):
        text = (DESKTOP / "fixtures" / "ui" / "BarWidget.qml").read_text(encoding="utf-8")
        self.assertIn('moduleName: "tamlinux.ui"', text)
        self.assertNotIn("IpcHandler", text)
        self.assertNotIn("import Quickshell", text)
        self.assertNotIn("execDetached", text)


if __name__ == "__main__":
    unittest.main()
