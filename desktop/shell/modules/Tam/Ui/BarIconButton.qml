import QtQuick
import Tam.Commons

WidgetButton {
  id: root

  property Component iconComponent: null
  property real slotSize: Style.bar.iconSlot
  property real opticalSize: Style.bar.iconCanvas
  property bool active: false
  property bool useActiveColor: true

  labelVisible: false
  hasVisualContent: text !== "" || iconComponent !== null
  fontSize: Style.bar.iconFont
  fixedWidth: vertical ? -1 : slotSize
  fixedHeight: vertical ? slotSize : -1
  foreground: active && useActiveColor ? Color.accent : (bar ? bar.barForeground : Color.foreground)

  Item {
    anchors.centerIn: parent
    width: root.opticalSize
    height: root.opticalSize

    OpticalGlyph {
      anchors.fill: parent
      visible: root.iconComponent === null
      text: root.text
      fontFamily: root.fontFamily
      fontSize: root.fontSize
      color: root.foreground
      rotation: root.textRotation
    }

    Loader {
      anchors.fill: parent
      active: root.iconComponent !== null
      sourceComponent: root.iconComponent
    }
  }
}
