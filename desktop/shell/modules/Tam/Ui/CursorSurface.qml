import QtQuick
import Tam.Commons

Rectangle {
  id: root

  property bool hasCursor: false
  property bool current: false
  property bool outline: false
  property bool bordered: false
  property bool hovered: false
  property color foreground: Color.foreground
  property color accent: Color.accent

  property color fill: Style.hoverFillFor(foreground, accent)
  property color currentFill: Style.selectedFillFor(foreground, accent)
  color: current ? currentFill : ((hovered || hasCursor) ? fill : "transparent")
  radius: Style.cornerRadius
  border.width: (outline || bordered) ? Style.normalBorderWidth : 0
  border.color: Style.normalBorderFor(foreground, accent)

  HoverHandler {
    onHoveredChanged: root.hovered = hovered
  }
}
