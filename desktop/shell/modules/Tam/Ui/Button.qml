import QtQuick
import Tam.Commons

Rectangle {
  id: root

  property string text: ""
  property string iconText: ""
  property color foreground: Color.foreground
  property color accent: Color.accent
  property bool bordered: false
  property bool active: false
  property bool selected: false
  property bool hasCursor: false
  property bool iconSpinning: false
  property string tooltipText: ""
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.body
  property real iconSize: Style.font.icon
  property real horizontalPadding: -1
  property real verticalPadding: -1
  property var bar: null

  signal clicked()
  signal hovered(bool isHovered)

  readonly property real padX: horizontalPadding >= 0 ? horizontalPadding : Style.spacing.controlPaddingX
  readonly property real padY: verticalPadding >= 0 ? verticalPadding : Style.spacing.controlPaddingY

  implicitWidth: label.implicitWidth + (iconText !== "" ? icon.implicitWidth + 4 : 0) + padX * 2
  implicitHeight: Math.max(label.implicitHeight, icon.implicitHeight) + padY * 2
  radius: Style.cornerRadius
  color: (active || selected) ? Style.selectedFillFor(foreground, accent)
       : ((mouse.containsMouse || hasCursor) ? Style.hoverFillFor(foreground, accent) : "transparent")
  border.width: bordered ? Style.normalBorderWidth : 0
  border.color: accent

  Row {
    anchors.centerIn: parent
    spacing: root.iconText !== "" ? 4 : 0

    Text {
      id: icon
      visible: root.iconText !== ""
      text: root.iconText
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: root.iconSize

      RotationAnimation on rotation {
        running: root.iconSpinning
        loops: Animation.Infinite
        from: 0
        to: 360
        duration: 800
      }
    }

    Text {
      id: label
      text: root.text
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: root.fontSize
    }
  }

  MouseArea {
    id: mouse
    anchors.fill: parent
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onEntered: {
      root.hovered(true)
      if (root.bar && root.bar.showTooltip && root.tooltipText !== "") root.bar.showTooltip(root, root.tooltipText)
    }
    onExited: {
      root.hovered(false)
      if (root.bar && root.bar.hideTooltip) root.bar.hideTooltip(root)
    }
    onClicked: root.clicked()
  }
}
