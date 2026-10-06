import QtQuick
import QtQuick.Controls
import Tam.Commons

TextField {
  id: root

  property color foreground: Color.foreground
  property bool password: false
  // Paddings ported panels set; -1 keeps Qt's default padding.
  property real horizontalPadding: -1
  property real verticalPadding: -1
  leftPadding: horizontalPadding >= 0 ? horizontalPadding : padding
  rightPadding: horizontalPadding >= 0 ? horizontalPadding : padding
  topPadding: verticalPadding >= 0 ? verticalPadding : padding
  bottomPadding: verticalPadding >= 0 ? verticalPadding : padding

  color: foreground
  echoMode: password ? TextInput.Password : TextInput.Normal
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
