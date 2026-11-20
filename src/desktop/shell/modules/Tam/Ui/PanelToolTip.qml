import QtQuick
import QtQuick.Controls
import Tam.Commons
import Tam.Commons as Commons

ToolTip {
  id: root
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.bodySmall
  delay: 400
  padding: Style.spacing.controlPaddingX
  contentItem: Text {
    text: root.text
    color: Commons.Color.tooltip.text
    font.family: root.fontFamily
    font.pixelSize: root.fontSize
  }
  background: Rectangle {
    color: Commons.Color.tooltip.background
    radius: Style.cornerRadius
    border.width: 1
    border.color: Commons.Color.tooltip.border
  }
}
