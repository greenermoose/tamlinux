"""Source checks for the session services the host owns. These tests do not start Quickshell."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
SERVICES = DESKTOP / "shell" / "services"
NOTIFICATIONS = SERVICES / "notifications"
OSD = SERVICES / "osd"
CLIPBOARD = SERVICES / "clipboard"
EMOJIS = SERVICES / "emojis"


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
            CLIPBOARD / "Service.qml",
            CLIPBOARD / "ClipboardHistory.js",
            CLIPBOARD / "capture.sh",
            CLIPBOARD / "paste-text.sh",
            CLIPBOARD / "paste-file.sh",
            CLIPBOARD / "open.sh",
            CLIPBOARD / "components" / "ConfirmDialog.qml",
            CLIPBOARD / "components" / "PointerMoveGate.qml",
            EMOJIS / "Service.qml",
            EMOJIS / "EmojiSearch.js",
            EMOJIS / "insert.sh",
        ):
            self.assertIn("LICENSE-omarchy", path.read_text(encoding="utf-8"), path.name)

    def test_services_use_the_host_modules(self):
        for path in (
            NOTIFICATIONS / "Service.qml",
            NOTIFICATIONS / "components" / "NotificationCard.qml",
            OSD / "Service.qml",
            CLIPBOARD / "Service.qml",
            CLIPBOARD / "components" / "ConfirmDialog.qml",
            EMOJIS / "Service.qml",
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

    def test_clipboard_target_state_and_helpers(self):
        text = (CLIPBOARD / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-clipboard"', text)
        self.assertIn('target: "clipboard"', text)
        for method in ("toggle()", "open()", "close()", "count()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn('"/tamlinux/clipboard"', text)
        self.assertIn('Quickshell.shellDir + "/services/clipboard"', text)
        # Reaps only its own watchers, never another shell's.
        self.assertIn("wl-paste .*--watch .*/services/clipboard/capture", text)
        self.assertIn('"setpriv", "--pdeathsig", "TERM"', text)

    def test_clipboard_helpers_use_tamlinux_state(self):
        for name in ("capture.sh", "paste-text.sh", "open.sh"):
            text = (CLIPBOARD / name).read_text(encoding="utf-8")
            self.assertIn("/tamlinux/clipboard", text, name)
            self.assertNotIn("/state/omarchy", text, name)
            self.assertNotIn("omarchy-", text.split("\n\n", 2)[-1], name)
        for name in ("capture.sh", "paste-text.sh", "paste-file.sh", "open.sh"):
            self.assertTrue((CLIPBOARD / name).stat().st_mode & 0o111, name + " is not executable")
        # Sensitive selections (password managers) are never recorded.
        self.assertIn("x-kde-passwordManagerHint", (CLIPBOARD / "capture.sh").read_text(encoding="utf-8"))
        # Opened programs run in their own scope, not the services unit.
        self.assertEqual((CLIPBOARD / "open.sh").read_text(encoding="utf-8").count("exec setsid uwsm-app --"), 3)

    def test_emojis_target_data_and_helper(self):
        text = (EMOJIS / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-emojis"', text)
        self.assertIn('target: "emojis"', text)
        for method in ("toggle()", "open()", "close()", "count()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn('Quickshell.shellDir + "/services/emojis"', text)
        self.assertIn('root.serviceDir + "/emojis.json"', text)
        emojis = json.loads((EMOJIS / "emojis.json").read_text(encoding="utf-8"))
        self.assertGreater(len(emojis), 1000)
        self.assertTrue(all(isinstance(item.get("e"), str) and item["e"] for item in emojis))
        helper = EMOJIS / "insert.sh"
        self.assertTrue(helper.stat().st_mode & 0o111, "insert.sh is not executable")
        body = helper.read_text(encoding="utf-8")
        self.assertNotIn("omarchy-", body.split("\n\n", 2)[-1])
        # Offered as sensitive, so the clipboard history never records it.
        self.assertIn("wl-copy --type text/plain --sensitive --foreground", body)

    def test_services_are_named_and_statically_imported(self):
        text = (DESKTOP / "shell" / "host" / "Services.qml").read_text(encoding="utf-8")
        self.assertIn('readonly property var known: ["notifications", "osd", "clipboard", "emojis"]', text)
        self.assertIn('import "../services/clipboard" as Clipboard', text)
        self.assertIn('import "../services/emojis" as Emojis', text)
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
