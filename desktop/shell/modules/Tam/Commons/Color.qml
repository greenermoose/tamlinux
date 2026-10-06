pragma Singleton
import QtQuick

// Shared color tokens. Defaults keep isolated proofs independent. The theme
// service applies validated palettes and surface overrides without restarting.
QtObject {
  id: root

  property color foreground: "#d7dde2"
  property color background: "#14181c"
  property color accent: "#8eb6c9"
  property color accentText: "#f4f7f8"
  property color urgent: "#c46b6b"
  property color muted: "#7d8790"

  property var surfaceValues: ({})

  function pick(key, fallback) {
    var value = surfaceValues[key]
    return typeof value === "string" ? value : fallback
  }

  function applyPayload(payload) {
    if (!payload || !payload.palette || !payload.surfaces) return false
    var names = ["foreground", "background", "accent", "accentText", "urgent", "muted"]
    for (var i = 0; i < names.length; i++) {
      if (typeof payload.palette[names[i]] !== "string" ||
          !/^#[0-9a-fA-F]{6}$/.test(payload.palette[names[i]])) return false
    }
    for (var j = 0; j < names.length; j++) root[names[j]] = payload.palette[names[j]]
    var surfaces = {}
    for (var key in payload.surfaces) {
      var value = payload.surfaces[key]
      if (typeof value === "string" && /^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/.test(value)) surfaces[key] = value
    }
    surfaceValues = surfaces
    return true
  }

  readonly property QtObject bar: QtObject {
    property color background: root.pick("bar.background", root.background)
    property color text: root.pick("bar.text", root.foreground)
  }

  readonly property QtObject popups: QtObject {
    property color background: root.pick("popups.background", root.background)
    property color text: root.pick("popups.text", root.foreground)
    property color border: root.pick("popups.border", root.accent)
  }

  readonly property QtObject notifications: QtObject {
    property color background: root.pick("notifications.background", root.popups.background)
    property color text: root.pick("notifications.text", root.foreground)
    property color border: root.pick("notifications.border", root.accent)
    property color countdown: root.pick("notifications.countdown", root.accent)
  }

  // The menu and full-screen clipboard/emoji pickers share these tokens.
  readonly property QtObject menu: QtObject {
    property color background: root.pick("menu.background", root.popups.background)
    property color text: root.pick("menu.text", root.foreground)
    property color border: root.pick("menu.border", root.accent)
    property color scrim: root.pick("menu.scrim", Util.alpha(root.background, 0.5))
    property color selectedBackground: root.pick("menu.selected-background", Util.alpha(root.foreground, 0.08))
    property color selectedText: root.pick("menu.selected-text", root.accent)
  }

  // The image picker has no card surface: `scrim` is the full-screen wash.
  readonly property QtObject imagePicker: QtObject {
    property color scrim: root.pick("image-picker.scrim", Util.alpha(root.background, 0.5))
    property color text: root.pick("image-picker.text", root.foreground)
    property color selectedBorder: root.pick("image-picker.selected-border", root.accent)
    property color unselectedBorder: root.pick("image-picker.unselected-border", Util.alpha(root.foreground, 0.28))
  }

  // The polkit prompt: one card on a full-screen scrim. The error tokens
  // colour a wrong password.
  readonly property QtObject polkit: QtObject {
    property color background: root.pick("polkit.background", root.popups.background)
    property color text: root.pick("polkit.text", root.foreground)
    property color textError: root.pick("polkit.text-error", root.urgent)
    property color accent: root.pick("polkit.accent", root.accent)
    property color border: root.pick("polkit.border", root.accent)
    property color borderError: root.pick("polkit.border-error", root.urgent)
    property color scrim: root.pick("polkit.scrim", Util.alpha(root.background, 0.5))
  }

  readonly property QtObject tooltip: QtObject {
    property color background: root.pick("tooltip.background", root.background)
    property color text: root.pick("tooltip.text", root.foreground)
    property color border: root.pick("tooltip.border", root.accent)
  }
}
