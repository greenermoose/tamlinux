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

  readonly property QtObject tooltip: QtObject {
    property color background: "#101417"
    property color text: root.foreground
    property color border: "#8eb6c9"
  }
}
