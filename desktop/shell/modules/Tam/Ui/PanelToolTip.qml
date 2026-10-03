import QtQuick
import QtQuick.Controls
import Tam.Commons

ToolTip {
  id: root
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.bodySmall
  delay: 400
  padding: Style.spacing.controlPaddingX
  contentItem: Text {
    text: root.text
    color: Color.tooltip.text
    font.family: root.fontFamily
    font.pixelSize: root.fontSize
  }
  background: Rectangle {
    color: Color.tooltip.background
    radius: Style.cornerRadius
    border.width: 1
    border.color: Color.tooltip.border
  }
}
