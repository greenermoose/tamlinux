import QtQuick
import Tam.Commons
import Tam.Commons as Commons

Rectangle {
  id: root
  property color foreground: Commons.Color.foreground
  property real strength: 0.16
  implicitWidth: 100
  implicitHeight: 1
  height: 1
  color: Qt.rgba(foreground.r, foreground.g, foreground.b, strength)
}
