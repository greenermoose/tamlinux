import QtQuick
import Tam.Commons

Item {
  id: root

  property string label: ""
  property string value: ""
  property var options: []
  property color foreground: Color.popups.text
  property color background: Color.popups.background
  property color accent: Color.accent
  property string fontFamily: Style.font.family
  property bool showLabel: true
  property bool hasCursor: false
  property bool opened: false

  readonly property bool popupOpen: opened

  signal changed(string value)
  signal hovered(bool isHovered)

  implicitWidth: Style.space(150)
  implicitHeight: Style.spacing.controlHeight

  function optionValue(option) {
    if (option && option.value !== undefined) return String(option.value)
    return String(option)
  }

  function optionLabel(option) {
    if (option && option.label !== undefined) return String(option.label)
    return String(option)
  }

  function currentLabel() {
    for (var i = 0; i < options.length; i++) {
      if (optionValue(options[i]) === value) return optionLabel(options[i])
    }
    return value
  }

  function open() { opened = true }
  function close() { opened = false }
  function toggle() { opened = !opened }

  function choose(option) {
    var next = optionValue(option)
    value = next
    opened = false
    changed(next)
  }

  Rectangle {
    anchors.fill: parent
    radius: Style.cornerRadius
    color: (mouse.containsMouse || root.hasCursor || root.opened) ? Style.hoverFillFor(root.foreground, root.accent) : root.background
    border.width: Style.normalBorderWidth
    border.color: root.opened ? root.accent : Color.popups.border

    Text {
      anchors.left: parent.left
      anchors.leftMargin: Style.spacing.sm
      anchors.right: parent.right
      anchors.rightMargin: Style.spacing.sm
      anchors.verticalCenter: parent.verticalCenter
      text: root.showLabel && root.label !== "" ? root.label : root.currentLabel()
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Style.font.bodySmall
      elide: Text.ElideRight
    }

    MouseArea {
      id: mouse
      anchors.fill: parent
      hoverEnabled: true
      onEntered: root.hovered(true)
      onExited: root.hovered(false)
      onClicked: root.toggle()
    }
  }
}
