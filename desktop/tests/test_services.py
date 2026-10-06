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
IMAGEPICKER = SERVICES / "imagepicker"
REMINDERS = SERVICES / "reminders"
MENU = SERVICES / "menu"
BACKGROUND = SERVICES / "background"
POLKIT = SERVICES / "polkit"
MEDIA = SERVICES / "media"
IDLE = SERVICES / "idle"
BATTERY = SERVICES / "battery"


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
            IMAGEPICKER / "Service.qml",
            IMAGEPICKER / "ImagePickerModel.js",
            IMAGEPICKER / "list.sh",
            REMINDERS / "Service.qml",
            REMINDERS / "ReminderFlowModel.js",
            REMINDERS / "reminder.sh",
            MENU / "Service.qml",
            MENU / "MenuModel.js",
            MENU / "AppLibrary.qml",
            MENU / "AppSearch.js",
            MENU / "hidden-entries.sh",
            BACKGROUND / "Service.qml",
            BACKGROUND / "components" / "ScreenMoveRemap.qml",
            POLKIT / "Service.qml",
            POLKIT / "PolkitModel.js",
            MEDIA / "Service.qml",
            MEDIA / "MediaModel.js",
            IDLE / "Service.qml",
            IDLE / "IdleModel.js",
            BATTERY / "Service.qml",
            BATTERY / "BatteryModel.js",
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
            IMAGEPICKER / "Service.qml",
            REMINDERS / "Service.qml",
            MENU / "Service.qml",
            MENU / "AppLibrary.qml",
            POLKIT / "Service.qml",
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

    def test_imagepicker_target_and_helper(self):
        text = (IMAGEPICKER / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-imagepicker"', text)
        self.assertIn('target: "imagepicker"', text)
        for method in ("open(", "preload(", "cancel(", "count()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn('Quickshell.shellDir + "/services/imagepicker"', text)
        self.assertIn('root.serviceDir + "/list.sh"', text)
        self.assertNotIn("OMARCHY_", text)
        # Paths from a request reach the shell as arguments, never as script text.
        self.assertNotIn("shellQuote", text)
        self.assertIn('["sh", "-c", \': > "$1"\', "sh", path]', text)
        helper = IMAGEPICKER / "list.sh"
        self.assertTrue(helper.stat().st_mode & 0o111, "list.sh is not executable")
        body = helper.read_text(encoding="utf-8")
        self.assertIn("/tamlinux/image-picker", body)
        self.assertNotIn("omarchy", body.split("\n\n", 2)[-1])

    def test_reminders_target_and_helper(self):
        text = (REMINDERS / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-reminders"', text)
        self.assertIn('target: "reminders"', text)
        for method in ("toggle()", "open()", "close()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn('Quickshell.shellDir + "/services/reminders"', text)
        self.assertIn('root.serviceDir + "/reminder.sh"', text)
        self.assertNotIn("OMARCHY_", text)
        helper = REMINDERS / "reminder.sh"
        self.assertTrue(helper.stat().st_mode & 0o111, "reminder.sh is not executable")
        body = helper.read_text(encoding="utf-8").split("\n\n", 2)[-1]
        for command in ("omarchy-reminder", "omarchy-shell", "omarchy-notification"):
            self.assertNotIn(command, body)
        self.assertIn('"tamlinux-reminder-*.timer"', body)
        self.assertIn('/tamlinux-reminders"', body)
        # Toasts are typed D-Bus values, never notify-send arguments.
        self.assertIn("busctl --user -- call", body)
        self.assertNotIn("notify-send", body)

    def test_menu_target_files_and_actions(self):
        text = (MENU / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-menu"', text)
        self.assertIn('target: "menu"', text)
        for method in ("toggle(route: string)", "summon(route: string)", "open(payloadJson: string)", "close()", "refresh()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn('Quickshell.env("TAMLINUX_MENU_DEFAULT")', text)
        self.assertIn('Quickshell.env("TAMLINUX_MENU_EXTENSION")', text)
        self.assertIn('"/tamlinux/menu"', text)
        self.assertNotIn(".config/omarchy", text)
        # Actions outlive a restart of the services unit.
        self.assertIn('"systemd-run", "--user", "--scope"', text)
        # Select/input answers are arguments, never shell text.
        self.assertIn('\'printf "%s\\\\n" "$1" > "$2"; : > "$3"\', "sh", String(selection)', text)
        self.assertNotIn("Util.shellQuote", text)
        # The application library is loaded on demand and owned by the menu.
        self.assertIn("id: appLibraryLoader", text)
        self.assertIn("active: false", text)
        library = (MENU / "AppLibrary.qml").read_text(encoding="utf-8")
        self.assertIn('Quickshell.env("TAMLINUX_MENU_HIDES")', library)
        self.assertIn('Quickshell.env("TAMLINUX_APP_REMOVER")', library)
        self.assertIn('root.serviceDir + "/hidden-entries.sh"', library)
        self.assertNotIn("omarchy-shell", library)
        self.assertNotIn("omarchy-remove-launcher-entry", library)
        helper = MENU / "hidden-entries.sh"
        self.assertTrue(helper.stat().st_mode & 0o111, "hidden-entries.sh is not executable")

    def test_background_link_watch_and_routes(self):
        text = (BACKGROUND / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-background"', text)
        self.assertIn("WlrLayershell.layer: WlrLayer.Background", text)
        self.assertIn('target: "background"', text)
        for method in ("refresh()", "set(path: string)", "setInstant(path: string)",
                       "transition(fromPath: string, path: string)", "current()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn("function themeTransition(fromPath: string, path: string, finalPath: string, colorsB64: string, shellB64: string)", text)
        self.assertIn('Quickshell.env("TAMLINUX_BACKGROUND_LINK")', text)
        self.assertIn('"/tamlinux/background"', text)
        # The link is watched by a child that dies with the host, and read by argument.
        self.assertIn('["setpriv", "--pdeathsig", "TERM", "inotifywait"', text)
        self.assertIn('["readlink", "-f", root.currentBackgroundLink]', text)
        # Double-clicks open menu routes; nothing runs a shell string here.
        self.assertIn('root.openRoute(mouse.button === Qt.RightButton ? "theme" : "background")', text)
        self.assertNotIn('"bash"', text)
        self.assertNotIn("omarchy-", text.split("\n\n", 1)[-1])
        self.assertNotIn("qs.Commons", text)

    def test_polkit_agent_path_layer_and_target(self):
        text = (POLKIT / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('WlrLayershell.namespace: "tamlinux-polkit"', text)
        self.assertIn("WlrKeyboardFocus.Exclusive", text)
        self.assertIn('path: "/org/tamlinux/PolkitAgent"', text)
        self.assertIn('target: "polkit"', text)
        for method in ("state()", "ping()"):
            self.assertIn("function " + method, text)
        # The IPC target only reports; it cannot submit or cancel a request.
        ipc = text.split('target: "polkit"', 1)[1].split("PanelWindow", 1)[0]
        self.assertNotIn("submit", ipc)
        self.assertNotIn("cancel", ipc)
        # The lid check is a fixed script that reads /proc, with no helper command.
        self.assertIn("/proc/acpi/button/lid/*/state", text)
        self.assertNotIn("omarchy-", text.split("\n\n", 1)[-1])
        self.assertIn('path: "/etc/pam.d/polkit-1"', text)
        model = (POLKIT / "PolkitModel.js").read_text(encoding="utf-8")
        for name in ("promptLooksFingerprint", "fingerprintConfiguredFromPamConfig", "authorizationLabel"):
            self.assertIn("function " + name, model)

    def test_media_target_and_osd(self):
        text = (MEDIA / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('target: "media"', text)
        for method in (
            "status()", "playPause()", "next()", "previous()", "play()", "pause()", "stop()",
            "sourceNext()", "sourcePrevious()", "sourceSwitch()", "sourceSwitchPrevious()", "ping()",
        ):
            self.assertIn("function " + method, text)
        # Each action goes to the injected host OSD, not a shell summon.
        self.assertIn("property var osd: null", text)
        self.assertIn("osd.open(JSON.stringify(", text)
        # The stop key acts through MPRIS Stop and shows the stop icon.
        self.assertIn("player.stop()", text)
        self.assertIn('iconName = "media-stop"', text)
        self.assertIn('n === "media-stop"', (OSD / "OsdModel.js").read_text(encoding="utf-8"))
        body = text.split("\n\n", 1)[-1]
        self.assertNotIn("summon", body)
        self.assertNotIn("omarchy", body)
        model = (MEDIA / "MediaModel.js").read_text(encoding="utf-8")
        for name in ("isProxyPlayer", "playerHasPlaybackStream", "trackChanged", "osdMessage"):
            self.assertIn("function " + name, model)

    def test_idle_target_state_and_commands(self):
        text = (IDLE / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('target: "idle"', text)
        for method in ("status()", "debug()", "enable()", "disable()", "toggle()", "ping()"):
            self.assertIn("function " + method, text)
        # Stay Awake is one file, named by the environment, written by argument.
        self.assertIn('Quickshell.env("TAMLINUX_STAY_AWAKE_FILE")', text)
        self.assertIn('"/.local/state/tamlinux/stay-awake"', text)
        self.assertIn('\'mkdir -p -- "$1" && touch -- "$2"\', "bash", root.stayAwakeStateDir, root.stayAwakeStatePath]', text)
        self.assertIn('["rm", "-f", "--", root.stayAwakeStatePath]', text)
        # The timeouts are off unless configured.
        self.assertIn('Quickshell.env("TAMLINUX_IDLE_SCREENSAVER")', text)
        self.assertIn('Quickshell.env("TAMLINUX_IDLE_LOCK")', text)
        self.assertIn("enabled: root.idleEnabled && root.plan.enabled", text)
        # Screensaver windows come from Wayland toplevels, not compositor events.
        self.assertIn("ToplevelManager.toplevels", text)
        self.assertIn('screensaverClass: "org.tamlinux.screensaver"', text)
        for command in ('"tam-launch-screensaver"', '"tam-system-lock"', '"tam-system-wake"'):
            self.assertIn(command, text)
        body = text.split("\n\n", 1)[-1]
        self.assertNotIn("omarchy", body)
        self.assertNotIn("Hyprland", body)
        model = (IDLE / "IdleModel.js").read_text(encoding="utf-8")
        for name in ("secondsFromConfig", "cyclePlan", "screensaverWindowCount"):
            self.assertIn("function " + name, model)

    def test_battery_target_and_commands(self):
        text = (BATTERY / "Service.qml").read_text(encoding="utf-8")
        self.assertIn('target: "battery"', text)
        for method in ("status()", "ping()"):
            self.assertIn("function " + method, text)
        self.assertIn("import Quickshell.Services.UPower", text)
        # The warning and the profile switch run owned commands by argument.
        self.assertIn('["tam-battery-low", String(level)]', text)
        self.assertIn('["tam-powerprofiles-set", pendingPowerSource]', text)
        self.assertIn("readonly property int batteryThreshold: 10", text)
        body = text.split("\n\n", 1)[-1]
        self.assertNotIn("omarchy", body)
        self.assertNotIn("Hyprland", body)
        model = (BATTERY / "BatteryModel.js").read_text(encoding="utf-8")
        for name in ("batteryPercentage", "isDischarging", "shouldWarnLowBattery", "powerSource", "statusOf"):
            self.assertIn("function " + name, model)

    def test_menu_power_profiles_use_owned_commands(self):
        text = (MENU / "Service.qml").read_text(encoding="utf-8")
        self.assertIn("tam-powerprofiles-list 2>/dev/null", text)
        self.assertIn('"tam-powerprofiles-set autodetect "', text)
        self.assertNotIn("omarchy-powerprofiles", text)

    def test_services_are_named_and_statically_imported(self):
        text = (DESKTOP / "shell" / "host" / "Services.qml").read_text(encoding="utf-8")
        self.assertIn('readonly property var known: ["notifications", "osd", "clipboard", "emojis", "imagepicker", "reminders", "menu", "background", "polkit", "media", "idle", "nightlight", "battery", "theme", "keybindings", "panels"]', text)
        self.assertIn('import "../services/clipboard" as Clipboard', text)
        self.assertIn('import "../services/emojis" as Emojis', text)
        self.assertIn('import "../services/imagepicker" as ImagePicker', text)
        self.assertIn('import "../services/notifications" as Notifications', text)
        self.assertIn('import "../services/osd" as Osd', text)
        self.assertIn('import "../services/reminders" as Reminders', text)
        self.assertIn('import "../services/menu" as Menu', text)
        self.assertIn("Menu.Service { osd: osdLoader.item }", text)
        self.assertIn('import "../services/background" as Background', text)
        self.assertIn("Background.Service { menu: menuLoader.item }", text)
        self.assertIn('import "../services/polkit" as Polkit', text)
        self.assertIn("Polkit.Service {}", text)
        self.assertIn('import "../services/media" as Media', text)
        self.assertIn("Media.Service { osd: osdLoader.item }", text)
        self.assertIn('import "../services/idle" as Idle', text)
        self.assertIn("Idle.Service {}", text)
        self.assertIn('import "../services/battery" as Battery', text)
        self.assertIn("Battery.Service {}", text)
        self.assertIn("TAMLINUX_SERVICES", text)
        self.assertNotIn("Qt.resolvedUrl", text)

    def test_bar_can_be_switched_off(self):
        text = (DESKTOP / "shell" / "shell.qml").read_text(encoding="utf-8")
        self.assertIn('Quickshell.env("TAMLINUX_BAR") !== "0"', text)
        self.assertIn("proof.settingsReady && proof.barLayoutReady && proof.barFlagReady && proof.barEnabled ? proof.hostKeys : []", text)
        self.assertIn("Services {", text)


if __name__ == "__main__":
    unittest.main()
