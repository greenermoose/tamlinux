import QtQuick
import Tam.Commons

Rectangle {
  id: root
  property color foreground: Color.foreground
  property real strength: 0.16
  implicitWidth: 100
  implicitHeight: 1
  height: 1
  color: Qt.rgba(foreground.r, foreground.g, foreground.b, strength)
}
