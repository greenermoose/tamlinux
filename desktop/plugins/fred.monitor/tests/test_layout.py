import importlib.util
import importlib.machinery
import pathlib
import os
import stat
import tempfile
import unittest


PLUGIN = pathlib.Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("fred_monitor_layout", str(PLUGIN / "fred-monitor-layout"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
LAYOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAYOUT)


SAMPLE = [
    {"name": "DP-2", "enabled": True, "width": 1920, "height": 1080, "refreshRate": 60, "x": 0, "y": 720, "scale": 1.5, "transform": 0},
    {"name": "DP-1", "enabled": True, "width": 2560, "height": 1440, "refreshRate": 59.951, "x": 1280, "y": 0, "scale": 1, "transform": 0},
    {"name": "HDMI-A-1", "enabled": True, "width": 1920, "height": 1080, "refreshRate": 60, "x": 3840, "y": 360, "scale": 1, "transform": 0},
]


class LayoutTests(unittest.TestCase):
    def test_validation_and_rule(self):
        validated = LAYOUT.validate_layout(SAMPLE)
        self.assertEqual(validated[1]["name"], "DP-1")
        self.assertEqual(
            LAYOUT.lua_rule(validated[1]),
            'hl.monitor({ output = "DP-1", mode = "2560x1440@59.951", position = "1280x0", scale = 1, transform = 0, disabled = false })',
        )

    def test_rejects_unsafe_name_and_all_disabled(self):
        unsafe = [dict(SAMPLE[0], name='DP-1" }) os.execute("bad") --')]
        with self.assertRaises(LAYOUT.LayoutError):
            LAYOUT.validate_layout(unsafe)
        with self.assertRaises(LAYOUT.LayoutError):
            LAYOUT.validate_layout([dict(item, enabled=False) for item in SAMPLE])

    def test_disabled_output_may_have_zero_sized_runtime_state(self):
        layout = [dict(SAMPLE[0]), dict(SAMPLE[1], enabled=False, width=0, height=0, refreshRate=0)]
        validated = LAYOUT.validate_layout(layout)
        self.assertFalse(validated[1]["enabled"])

    def test_managed_block_replacement_preserves_surroundings(self):
        text = "before\n" + LAYOUT.START_MARKER + "\nold\n" + LAYOUT.END_MARKER + "\nafter\n"
        updated = LAYOUT.replace_managed_block(text, LAYOUT.validate_layout(SAMPLE))
        self.assertTrue(updated.startswith("before\n"))
        self.assertTrue(updated.endswith("\nafter\n"))
        self.assertIn('output = "HDMI-A-1"', updated)
        self.assertNotIn("\nold\n", updated)

    def test_layout_comparison_tolerates_refresh_rounding_but_not_geometry(self):
        expected = LAYOUT.validate_layout(SAMPLE)
        rounded = [dict(item) for item in expected]
        rounded[1]["refreshRate"] = 59.95
        self.assertTrue(LAYOUT.layouts_match(expected, rounded))
        moved = [dict(item) for item in rounded]
        moved[1]["x"] += 1
        self.assertFalse(LAYOUT.layouts_match(expected, moved))

    def test_persist_layout_only_replaces_managed_block(self):
        with tempfile.TemporaryDirectory() as temp:
            config = pathlib.Path(temp)
            hypr = config / "hypr"
            hypr.mkdir()
            target = hypr / "monitors.lua"
            target.write_text("before\n" + LAYOUT.START_MARKER + "\nold\n" + LAYOUT.END_MARKER + "\nafter\n")
            previous = os.environ.get("XDG_CONFIG_HOME")
            previous_state = os.environ.get("XDG_STATE_HOME")
            os.environ["XDG_CONFIG_HOME"] = temp
            os.environ["XDG_STATE_HOME"] = str(config / "state")
            try:
                LAYOUT.persist_layout(LAYOUT.validate_layout(SAMPLE))
            finally:
                if previous is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = previous
                if previous_state is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = previous_state
            updated = target.read_text()
            self.assertTrue(updated.startswith("before\n"))
            self.assertTrue(updated.endswith("\nafter\n"))
            self.assertNotIn("\nold\n", updated)
            backups = list((config / "state" / "fred.monitor" / "backups").glob("*.lua"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(stat.S_IMODE(backups[0].stat().st_mode), 0o600)

    def test_named_and_automatic_profiles_round_trip_privately(self):
        with tempfile.TemporaryDirectory() as temp:
            previous_state = os.environ.get("XDG_STATE_HOME")
            original_capture = LAYOUT.capture_layout
            os.environ["XDG_STATE_HOME"] = temp
            LAYOUT.capture_layout = lambda: LAYOUT.validate_layout(SAMPLE)
            try:
                LAYOUT.save_profile("Desk")
                LAYOUT.remember_automatic_profiles(SAMPLE, [dict(item, y=0) for item in SAMPLE])
                dir_fd = LAYOUT.open_profile_directory()
                try:
                    store = LAYOUT.read_profiles_at(dir_fd)
                    listing = LAYOUT.profile_listing(store)
                    self.assertEqual(
                        [item["id"] for item in listing],
                        ["automatic:previous", "automatic:last-saved", "user:Default", "user:Desk"],
                    )
                    self.assertEqual(LAYOUT.find_profile_layout(store, "user:Desk")[1]["name"], "DP-1")
                finally:
                    os.close(dir_fd)

                profile_file = pathlib.Path(temp) / "fred.monitor" / LAYOUT.PROFILES_FILE
                self.assertEqual(stat.S_IMODE(profile_file.stat().st_mode), 0o600)
                with self.assertRaises(LAYOUT.LayoutError):
                    LAYOUT.save_profile("desk")
                LAYOUT.delete_profile("user:Desk")
                dir_fd = LAYOUT.open_profile_directory()
                try:
                    ids = [item["id"] for item in LAYOUT.profile_listing(LAYOUT.read_profiles_at(dir_fd))]
                    self.assertNotIn("user:Desk", ids)
                finally:
                    os.close(dir_fd)
            finally:
                LAYOUT.capture_layout = original_capture
                if previous_state is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = previous_state

    def test_default_profile_is_seeded_and_last_layout_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            previous_state = os.environ.get("XDG_STATE_HOME")
            original_capture = LAYOUT.capture_layout
            os.environ["XDG_STATE_HOME"] = temp
            LAYOUT.capture_layout = lambda: LAYOUT.validate_layout(SAMPLE)
            try:
                dir_fd = LAYOUT.open_profile_directory()
                try:
                    store = LAYOUT.ensure_default_profile(dir_fd, LAYOUT.read_profiles_at(dir_fd))
                    self.assertEqual(
                        [item["id"] for item in LAYOUT.profile_listing(store)],
                        ["user:Default"],
                    )
                finally:
                    os.close(dir_fd)

                with self.assertRaisesRegex(LAYOUT.LayoutError, "at least one saved layout"):
                    LAYOUT.delete_profile("user:Default")

                LAYOUT.save_profile("Desk")
                LAYOUT.delete_profile("user:Default")
                dir_fd = LAYOUT.open_profile_directory()
                try:
                    self.assertEqual(
                        [item["id"] for item in LAYOUT.profile_listing(LAYOUT.read_profiles_at(dir_fd))],
                        ["user:Desk"],
                    )
                finally:
                    os.close(dir_fd)
            finally:
                LAYOUT.capture_layout = original_capture
                if previous_state is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = previous_state

    def test_profile_names_are_bounded(self):
        self.assertEqual(LAYOUT.validate_profile_name("Desk setup"), "Desk setup")
        with self.assertRaises(LAYOUT.LayoutError):
            LAYOUT.validate_profile_name("../escape")
        with self.assertRaises(LAYOUT.LayoutError):
            LAYOUT.validate_profile_name("x" * (LAYOUT.MAX_PROFILE_NAME + 1))


if __name__ == "__main__":
    unittest.main()
