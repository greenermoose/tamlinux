pragma Singleton
import QtQuick

// Owned palette for the clock proof. Tokens are local defaults; this singleton
// does not read a theme directory or a compositor.
QtObject {
  id: root

  property color foreground: "#d7dde2"
  property color background: "#14181c"
  property color accent: "#8eb6c9"
  property color accentText: "#f4f7f8"
  property color urgent: "#c46b6b"
  property color muted: "#7d8790"

  readonly property QtObject bar: QtObject {
    property color background: "#101417"
    property color text: root.foreground
  }

  readonly property QtObject popups: QtObject {
    property color background: "#1b2126"
    property color text: root.foreground
    property color border: "#3c4a54"
  }

  readonly property QtObject notifications: QtObject {
    property color background: root.popups.background
    property color text: root.foreground
    property color border: root.accent
    property color countdown: root.accent
  }

  // Full-screen pickers (clipboard and emojis now; the menu later) share
  // these surface tokens.
  readonly property QtObject menu: QtObject {
    property color background: root.popups.background
    property color text: root.foreground
    property color border: root.accent
    property color scrim: Qt.rgba(0.078, 0.094, 0.11, 0.5)
    property color selectedBackground: Qt.rgba(0.843, 0.867, 0.886, 0.08)
    property color selectedText: root.accent
  }

  // The image picker has no card surface: `scrim` is the full-screen wash.
  readonly property QtObject imagePicker: QtObject {
    property color scrim: Qt.rgba(0.078, 0.094, 0.11, 0.5)
    property color text: root.foreground
    property color selectedBorder: root.accent
    property color unselectedBorder: Qt.rgba(0.843, 0.867, 0.886, 0.28)
  }

  // The polkit prompt: one card on a full-screen scrim. The error tokens
  // colour a wrong password.
  readonly property QtObject polkit: QtObject {
    property color background: root.popups.background
    property color text: root.foreground
    property color textError: root.urgent
    property color accent: root.accent
    property color border: root.accent
    property color borderError: root.urgent
    property color scrim: Qt.rgba(0.078, 0.094, 0.11, 0.5)
  }

  readonly property QtObject tooltip: QtObject {
    property color background: "#101417"
    property color text: root.foreground
    property color border: "#8eb6c9"
  }
}
