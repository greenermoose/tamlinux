import QtQuick
import Tam.Commons

Text {
  id: root

  property color foreground: Color.foreground
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.caption

  color: root.foreground
  font.family: root.fontFamily
  font.pixelSize: root.fontSize
  elide: Text.ElideRight
}
