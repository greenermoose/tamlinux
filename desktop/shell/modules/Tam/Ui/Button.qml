import QtQuick
import Tam.Commons

Rectangle {
  id: root

  property string text: ""
  property color foreground: Color.foreground
  property color accent: Color.accent
  property bool bordered: false
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.body

  signal clicked()

  implicitWidth: label.implicitWidth + Style.spacing.controlPaddingX * 2
  implicitHeight: label.implicitHeight + Style.spacing.controlPaddingY * 2
  radius: Style.cornerRadius
  color: mouse.containsMouse ? Style.hoverFillFor(foreground, accent) : "transparent"
  border.width: bordered ? 1 : 0
  border.color: accent

  Text {
    id: label
    anchors.centerIn: parent
    text: root.text
    color: root.foreground
    font.family: root.fontFamily
    font.pixelSize: root.fontSize
  }

  MouseArea {
    id: mouse
    anchors.fill: parent
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onClicked: root.clicked()
  }
}
