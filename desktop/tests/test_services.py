"""Source checks for the session services the host owns. These tests do not start Quickshell."""

from __future__ import annotations

import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
SERVICES = DESKTOP / "shell" / "services"
NOTIFICATIONS = SERVICES / "notifications"
OSD = SERVICES / "osd"


class ServiceSourceTests(unittest.TestCase):
    def test_vendored_files_keep_the_notice(self):
        license_text = (SERVICES / "LICENSE-omarchy").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) David Heinemeier Hansson", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        for path in (
            NOTIFICATIONS / "Service.qml",
            NOTIFICATIONS / "NotificationLogic.js",
            NOTIFICATIONS / "components" / "NotificationCard.qml",
            OSD / "Service.qml",
            OSD / "OsdModel.js",
        ):
            self.assertIn("LICENSE-omarchy", path.read_text(encoding="utf-8"), path.name)

    def test_services_use_the_host_modules(self):
        for path in (
            NOTIFICATIONS / "Service.qml",
            NOTIFICATIONS / "components" / "NotificationCard.qml",
            OSD / "Service.qml",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn("import Tam.Commons", text, path.name)
            self.assertNotIn("qs.Commons", text, path.name)
            self.assertNotIn("qs.Ui", text, path.name)
            self.assertNotIn("OMARCHY_PATH", text, path.name)
            self.assertNotIn("/bin/omarchy-", text, path.name)

    def test_notifications_state_and_focus(self):
        text = (NOTIFICATIONS / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('"/.local/state/tamlinux/"', text)
        self.assertNotIn("/.local/state/omarchy", text)
        self.assertIn("shell.compositor.focusApp(", text)
        self.assertIn('WlrLayershell.namespace: "tamlinux-notifications"', text)
        self.assertIn('target: "notifications"', text)

    def test_osd_target_and_layer(self):
        text = (OSD / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-osd"', text)
        self.assertIn('target: "osd"', text)
        for method in ("show(payloadJson: string)", "close()", "state()", "ping()"):
            self.assertIn("function " + method, text)
        # Visual only: the overlay must never take input from the desktop.
        self.assertIn("mask: Region {}", text)
        self.assertIn("WlrKeyboardFocus.None", text)

    def test_services_are_named_and_statically_imported(self):
        text = (DESKTOP / "shell" / "host" / "Services.qml").read_text(encoding="utf-8")
        self.assertIn('readonly property var known: ["notifications", "osd"]', text)
        self.assertIn('import "../services/notifications" as Notifications', text)
        self.assertIn('import "../services/osd" as Osd', text)
        self.assertIn("TAMLINUX_SERVICES", text)
        self.assertNotIn("Qt.resolvedUrl", text)

    def test_bar_can_be_switched_off(self):
        text = (DESKTOP / "shell" / "shell.qml").read_text(encoding="utf-8")
        self.assertIn('Quickshell.env("TAMLINUX_BAR") !== "0"', text)
        self.assertIn("proof.settingsReady && proof.barEnabled ? proof.hostKeys : []", text)
        self.assertIn("Services {", text)


if __name__ == "__main__":
    unittest.main()
