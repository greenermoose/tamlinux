import QtQuick
import Tam.Commons

Item {
  id: root
  property string text: ""
  property var bar: null
  property color foreground: bar ? bar.foreground : Color.foreground
  property string fontFamily: bar ? bar.fontFamily : Style.font.family
  property bool clickable: false
  signal clicked()

  implicitWidth: parent ? parent.width : footerLabel.implicitWidth
  implicitHeight: Style.space(22)

  Text {
    id: footerLabel
    anchors.centerIn: parent
    textFormat: Text.PlainText
    text: root.text
    font.family: root.fontFamily
    font.pixelSize: Style.font.caption
    color: root.foreground
    opacity: (root.clickable && mouseArea.containsMouse) ? 0.9 : 0.45
    font.underline: root.clickable && mouseArea.containsMouse
    horizontalAlignment: Text.AlignHCenter

    MouseArea {
      id: mouseArea
      anchors.fill: parent
      enabled: root.clickable
      hoverEnabled: root.clickable
      cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
      onClicked: root.clicked()
    }
  }
}
