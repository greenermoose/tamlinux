import QtQuick
import Tam.Commons

Row {
  id: root

  property Component iconComponent: null
  property string title: ""
  property string meta: ""
  property string detail: ""
  property color foreground: Color.foreground
  property string fontFamily: Style.font.family
  property real iconSize: Style.font.display

  spacing: Style.spacing.md

  Loader {
    width: root.iconSize
    height: root.iconSize
    active: root.iconComponent !== null
    sourceComponent: root.iconComponent
  }

  Column {
    spacing: Style.spacing.xs

    Text {
      text: root.title
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Style.font.title
    }

    Text {
      text: root.meta
      visible: root.meta !== ""
      color: root.foreground
      opacity: 0.7
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
    }

    Text {
      text: root.detail
      visible: root.detail !== ""
      color: root.foreground
      opacity: 0.7
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
    }
  }
}
