#!/usr/bin/env python3
"""Unit tests for WaylandVirtualInput and input synthesis helpers."""

import unittest
from pathlib import Path
import sys

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP))

from virtual_input import (
    CHAR_TO_KEY,
    EVDEV_KEYS,
    MODIFIER_SPECS,
    EmergencyStopError,
    interpolate_path,
    parse_chord,
    resolve_evdev_key,
    resolve_modifiers,
    trigger_emergency_stop,
    wl_fixed_from_double,
)


class TestVirtualInputHelpers(unittest.TestCase):
    def test_resolve_evdev_key_names(self):
        self.assertEqual(resolve_evdev_key("ESCAPE"), 1)
        self.assertEqual(resolve_evdev_key("ESC"), 1)
        self.assertEqual(resolve_evdev_key("RETURN"), 28)
        self.assertEqual(resolve_evdev_key("ENTER"), 28)
        self.assertEqual(resolve_evdev_key("Q"), 16)
        self.assertEqual(resolve_evdev_key("BACKSPACE"), 14)
        self.assertEqual(resolve_evdev_key("SPACE"), 57)
        self.assertEqual(resolve_evdev_key("1"), 2)
        self.assertEqual(resolve_evdev_key("0"), 11)
        self.assertEqual(resolve_evdev_key("KP_1"), 79)

    def test_resolve_evdev_key_xkb_code(self):
        # code:10 is key '1' (evdev 2)
        self.assertEqual(resolve_evdev_key("code:10"), 2)
        # code:19 is key '0' (evdev 11)
        self.assertEqual(resolve_evdev_key("code:19"), 11)
        # code:87 is KP_1 (evdev 79)
        self.assertEqual(resolve_evdev_key("code:87"), 79)

    def test_resolve_modifiers(self):
        codes, mask = resolve_modifiers(["META", "SHIFT"])
        self.assertIn(EVDEV_KEYS["LEFTMETA"], codes)
        self.assertIn(EVDEV_KEYS["LEFTSHIFT"], codes)
        self.assertEqual(mask, MODIFIER_SPECS["META"][1] | MODIFIER_SPECS["SHIFT"][1])

        codes_ctrl_alt, mask_ctrl_alt = resolve_modifiers(["CTRL", "ALT"])
        self.assertIn(EVDEV_KEYS["LEFTCTRL"], codes_ctrl_alt)
        self.assertIn(EVDEV_KEYS["LEFTALT"], codes_ctrl_alt)
        self.assertEqual(
            mask_ctrl_alt, MODIFIER_SPECS["CTRL"][1] | MODIFIER_SPECS["ALT"][1]
        )

    def test_parse_chord(self):
        mods, key = parse_chord("META + RETURN")
        self.assertEqual(mods, ["META"])
        self.assertEqual(key, "RETURN")

        mods2, key2 = parse_chord("META + SHIFT + U")
        self.assertEqual(mods2, ["META", "SHIFT"])
        self.assertEqual(key2, "U")

        mods3, key3 = parse_chord("META + mouse:273")
        self.assertEqual(mods3, ["META"])
        self.assertEqual(key3, "mouse:273")

        mods4, key4 = parse_chord("CTRL + ALT + DELETE")
        self.assertEqual(mods4, ["CTRL", "ALT"])
        self.assertEqual(key4, "DELETE")

    def test_interpolate_path(self):
        pts = interpolate_path(0, 0, 100, 100, steps=5)
        self.assertTrue(len(pts) >= 2)
        self.assertEqual(pts[-1], (100, 100))
        # Ensure smooth monotonic progression
        for i in range(1, len(pts)):
            self.assertGreaterEqual(pts[i][0], pts[i - 1][0])
            self.assertGreaterEqual(pts[i][1], pts[i - 1][1])

    def test_wl_fixed_from_double(self):
        self.assertEqual(wl_fixed_from_double(0.0), 0)
        self.assertEqual(wl_fixed_from_double(1.0), 256)
        self.assertEqual(wl_fixed_from_double(0.5), 128)
        self.assertEqual(wl_fixed_from_double(-1.0), -256)

    def test_char_to_key_coverage(self):
        for ch in "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:'\",.<>/? \t\n":
            self.assertIn(ch, CHAR_TO_KEY)
            key_name, _ = CHAR_TO_KEY[ch]
            self.assertIn(key_name, EVDEV_KEYS)


if __name__ == "__main__":
    unittest.main()
