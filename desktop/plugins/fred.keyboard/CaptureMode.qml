import QtQuick
import Quickshell.Wayland
import qs.Ui
import qs.Commons

// Capture mode: a ShortcutInhibitor wrapped in the box that turns it on and
// explains, inside the same box, what that means.
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
// The mode is deliberately off by default and must be switched on here.
// Opening the panel never disables the system's shortcuts on its own.
//
// While on, the panel also records mouse clicks and wheel steps (the
// inhibitor covers Hyprland's mouse binds too), so nothing inside the card
// is clickable, this switch included: it is drawn dimmed, the notice in the
// box says a click on it is recorded, and Escape is the way out.
BorderSurface {
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

  readonly property bool hot: rowMouse.containsMouse && !root.wanted
  readonly property color muted: Qt.rgba(Color.foreground.r, Color.foreground.g,
                                         Color.foreground.b, 0.65)

  implicitHeight: content.implicitHeight + Style.spacing.md * 2
  radius: Style.cornerRadius
  padding: Style.spacing.md
  leftPadding: Style.spacing.rowPaddingX
  rightPadding: Style.spacing.rowPaddingX

  // The box itself says which state it is in: accent border and fill while
  // the mode is live, the ordinary control chrome otherwise.
  borderSpec: root.active
    ? Border.controlSpec("focus", Color.foreground, Color.accent)
    : Border.controlSpec(root.hot ? "hover-cursor" : "normal", Color.foreground, Color.accent)
  color: root.active
    ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.10)
    : Style.controlFill(false, root.hot, Color.foreground, Color.accent)

  Behavior on color { ColorAnimation { duration: 100 } }

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
    id: content
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.top: parent.top
    anchors.leftMargin: root.contentLeftInset
    anchors.rightMargin: root.contentRightInset
    anchors.topMargin: root.contentTopInset
    spacing: Style.spacing.sm

    // Title, state line, and the switch. The row owns the click while the
    // mode is off; once on, the capture surface above owns every click.
    Item {
      width: parent.width
      height: Math.max(labels.implicitHeight, track.height)

      Column {
        id: labels
        anchors.left: parent.left
        anchors.right: track.left
        anchors.rightMargin: Style.spacing.rowPaddingX
        anchors.verticalCenter: parent.verticalCenter
        spacing: Style.spacing.xs

        Text {
          width: parent.width
          textFormat: Text.PlainText
          text: "Capture mode" + (root.active ? " - ON" : root.wanted ? " - requested" : "")
          color: root.active ? Color.accent : Color.foreground
          font.family: Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
          elide: Text.ElideRight
        }

        Text {
          width: parent.width
          textFormat: Text.PlainText
          wrapMode: Text.WordWrap
          text: root.wanted
            ? (root.active
               ? "Hyprland shortcuts are paused while this panel is focused. Every " +
                 "key combination and mouse action reaches the board instead of running."
               : "Waiting for the compositor to grant it. Click the panel if it does " +
                 "not have focus.")
            : "Off. Bound combinations such as Super+K still run their command and " +
              "never reach this panel. Switch on to inspect them."
          color: root.muted
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
        }
      }

      ToggleSwitch {
        id: track
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        checked: root.wanted
        interactive: false
        // Dimmed while on: a click here is recorded, not obeyed.
        opacity: root.wanted ? 0.35 : 1.0
        Behavior on opacity { NumberAnimation { duration: 100 } }
      }

      MouseArea {
        id: rowMouse
        anchors.fill: parent
        hoverEnabled: true
        enabled: !root.wanted
        cursorShape: Qt.PointingHandCursor
        onClicked: root.wanted = true
      }
    }

    // The notice lives inside the box so it reads as part of the mode. Loud
    // on purpose: in this state the machine's shortcuts genuinely do not
    // work, and the user needs to see both that and the way out.
    Rectangle {
      visible: root.active
      width: parent.width
      implicitHeight: notice.implicitHeight + Style.spacing.sm * 2
      radius: Math.max(2, Style.space(3))
      color: Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.18)
      border.width: 1
      border.color: Color.accent

      Text {
        id: notice
        anchors.fill: parent
        anchors.margins: Style.spacing.sm
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
        color: Color.foreground
        text: "Keys and mouse clicks are recorded here, not acted on - clicking the " +
              "switch above is recorded too. Press Esc to exit capture mode. Click " +
              "anywhere outside the panel to exit the plugin."
      }
    }
  }
}
