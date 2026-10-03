import QtQuick
import QtQuick.Controls
import Tam.Commons

TextField {
  id: root

  property color foreground: Color.foreground

  color: foreground
  placeholderTextColor: Qt.darker(foreground, 1.4)
  font.family: Style.font.family
  font.pixelSize: Style.font.bodySmall
  selectByMouse: true
  background: Rectangle {
    color: "transparent"
    radius: Style.cornerRadius
    border.width: Style.spacing.hairline
    border.color: Style.normalBorderFor(root.foreground, Color.accent)
  }
}
