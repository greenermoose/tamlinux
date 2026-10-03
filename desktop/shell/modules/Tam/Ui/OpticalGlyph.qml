import QtQuick
import Tam.Commons

Item {
  id: root
  property string text: ""
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.body
  property color color: Color.foreground

  Text {
    anchors.centerIn: parent
    text: root.text
    color: root.color
    font.family: root.fontFamily
    font.pixelSize: Math.max(1, Math.round(root.fontSize))
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
  }
}
