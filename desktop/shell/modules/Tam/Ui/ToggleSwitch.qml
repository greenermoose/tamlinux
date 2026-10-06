import QtQuick
import Tam.Commons

Item {
  id: root

  property bool checked: false
  property bool busy: false
  property bool interactive: true
  property bool hasCursor: false
  // Accepted for ported panels; this switch draws no cursor ring to pad.
  property int cursorPad: Style.space(6)
  property color foreground: Color.foreground
  property color accent: Color.accent

  signal toggled()
  signal hovered(bool isHovered)

  // Ported panels show a tooltip while the pointer is over the switch.
  readonly property alias containsMouse: switchMouse.containsMouse

  property int trackHeight: Math.max(22, Math.round(Style.spacing.controlHeight * 0.55))
  property int trackWidth: Math.round(trackHeight * 1.9)
  property int knobSize: Math.max(6, Math.round(trackHeight * 0.72))

  implicitWidth: trackWidth
  implicitHeight: trackHeight

  Rectangle {
    anchors.fill: parent
    radius: height / 2
    color: root.checked ? Util.alpha(root.accent, 0.35) : Util.alpha(root.foreground, 0.16)
    border.width: Style.normalBorderWidth
    border.color: root.checked ? root.accent : Util.alpha(root.foreground, 0.4)
    opacity: root.busy ? 0.6 : 1

    Rectangle {
      width: root.knobSize
      height: root.knobSize
      radius: width / 2
      anchors.verticalCenter: parent.verticalCenter
      x: root.checked ? parent.width - width - 3 : 3
      color: root.checked ? root.accent : root.foreground
    }
  }

  MouseArea {
    id: switchMouse
    anchors.fill: parent
    hoverEnabled: true
    enabled: root.interactive && !root.busy
    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    onEntered: root.hovered(true)
    onExited: root.hovered(false)
    onClicked: {
      root.checked = !root.checked
      root.toggled()
    }
  }
}
