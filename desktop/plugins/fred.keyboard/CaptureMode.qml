import QtQuick
import Quickshell.Wayland
import qs.Ui
import qs.Commons

// Capture mode: a ShortcutInhibitor wrapped in the control that turns it on
// and the indicator that says it is on.
//
// Hyprland matches keybinds before the focused surface sees the key, so a
// panel-scoped listener never receives Super+K - the combination fires its
// command instead. The keyboard-shortcuts-inhibit protocol suspends that
// matching for this window while it holds keyboard focus, and only then:
// every bound combination then reaches the panel verbatim, and nothing typed
// anywhere else is affected or visible (plan section 2a).
//
// `wanted` is the plugin's own switch and the single source of truth. The
// inhibitor's `enabled` is driven from it imperatively rather than bound,
// because Quickshell writes `enabled = false` itself when the compositor
// cancels an inhibitor, and that write would silently break a binding. The
// compositor grants or refuses the request; `active` reports the outcome.
//
// The mode is deliberately off by default and must be switched on inside the
// panel. Opening the panel never disables the system's shortcuts on its own.
//
// While on, the panel also records mouse clicks and wheel steps (the
// inhibitor covers Hyprland's mouse binds too), so nothing inside the card
// is clickable, this toggle included: Escape is the way out, and the banner
// says so.
Item {
  id: root

  // The QsWindow whose focus the inhibitor is tied to (the panel window).
  required property var window

  // The user's switch. Flip it; the inhibitor follows.
  property bool wanted: false

  // Granted by the compositor and in force right now.
  readonly property bool active: inhibitor.active

  // Emitted when the compositor withdrew a live inhibitor; `wanted` has
  // already been reset to false when this fires.
  signal cancelled()

  implicitHeight: column.implicitHeight

  onWantedChanged: inhibitor.enabled = root.wanted

  ShortcutInhibitor {
    id: inhibitor
    window: root.window
    enabled: false
    onCancelled: {
      root.wanted = false
      root.cancelled()
    }
    // Keep the two in step if anything else writes `enabled`.
    onEnabledChanged: if (inhibitor.enabled !== root.wanted) root.wanted = inhibitor.enabled
  }

  Column {
    id: column
    width: parent.width
    spacing: Style.spacing.sm

    Toggle {
      width: parent.width
      label: "Capture mode"
      description: root.wanted
        ? (root.active
           ? "Hyprland shortcuts are paused while this panel is focused. " +
             "Every key combination and mouse action reaches the board " +
             "instead of running."
           : "Requested; waiting for the compositor to grant it. " +
             "Click the panel if it does not have focus.")
        : "Off. Bound combinations such as Super+K still run their command " +
          "and never reach this panel."
      checked: root.wanted
      onClicked: root.wanted = !root.wanted
    }

    // Loud on purpose: in this state the machine's shortcuts genuinely do
    // not work, and the user needs to see both that and the way out.
    Rectangle {
      visible: root.active
      width: parent.width
      implicitHeight: bannerText.implicitHeight + Style.spacing.sm * 2
      radius: Math.max(2, Style.space(3))
      color: Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.18)
      border.width: 1
      border.color: Color.accent

      Text {
        id: bannerText
        anchors.fill: parent
        anchors.margins: Style.spacing.sm
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
        font.bold: true
        color: Color.foreground
        text: "CAPTURE ON - keys and mouse clicks are recorded here, not acted " +
              "on. Press Esc to exit capture mode. Click anywhere outside the " +
              "panel to exit the plugin."
      }
    }
  }
}
