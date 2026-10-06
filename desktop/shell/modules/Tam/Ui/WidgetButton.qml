import QtQuick
import Tam.Commons

Item {
  id: root

  property var bar: null
  property string text: ""
  property string fontFamily: bar ? bar.fontFamily : Style.font.family
  property real fontSize: Style.font.body
  property color foreground: bar ? bar.barForeground : Color.foreground
  property real horizontalMargin: 8.5
  property real verticalPadding: 6
  property real fixedWidth: -1
  property real fixedHeight: -1
  property bool labelVisible: true
  property bool hasVisualContent: text !== ""
  property string tooltipText: ""
  property bool hovered: false
  property bool tooltipHovered: false
  property var registeredBar: null
  // Bar indicators (BarIndicator) dim, conceal, and reveal their buttons.
  // The defaults leave every other button as it was.
  property real textRotation: 0
  property bool keepSpace: false
  property bool dimmed: false
  property bool concealed: false
  property bool interactive: true
  property bool pressable: true
  property bool maintainIndicatorReveal: false
  property var revealHost: bar

  signal pressed(int button)
  signal wheelMoved(real delta)

  function triggerPress(button) {
    if (root.bar && root.bar.hideTooltip) root.bar.hideTooltip(root)
    root.pressed(button)
  }

  function syncClickRegistration() {
    if (registeredBar && registeredBar.unregisterClickTarget)
      registeredBar.unregisterClickTarget(root)
    registeredBar = root.bar
    if (registeredBar && registeredBar.registerClickTarget)
      registeredBar.registerClickTarget(root)
  }

  function hideOwnTooltip() {
    if (root.bar && root.bar.hideTooltip) root.bar.hideTooltip(root)
  }

  onBarChanged: syncClickRegistration()
  onVisibleChanged: if (!visible) hideOwnTooltip()
  onInteractiveChanged: if (!interactive) hideOwnTooltip()
  onConcealedChanged: if (concealed) hideOwnTooltip()
  Component.onCompleted: syncClickRegistration()
  Component.onDestruction: {
    if (registeredBar && registeredBar.unregisterClickTarget)
      registeredBar.unregisterClickTarget(root)
  }

  readonly property bool vertical: bar ? bar.vertical : false
  readonly property int barSize: bar ? bar.barSize : Style.bar.sizeHorizontal
  readonly property real labelWidth: label.visible ? label.implicitWidth : 0

  opacity: concealed ? 0 : (dimmed ? 0.45 : 1)

  Behavior on opacity {
    NumberAnimation { duration: 140; easing.type: Easing.OutCubic }
  }

  implicitWidth: fixedWidth > 0 ? fixedWidth : (vertical ? barSize : Math.max(12, label.implicitWidth + Style.spaceReal(horizontalMargin) * 2))
  implicitHeight: fixedHeight > 0 ? fixedHeight : (vertical ? Math.max(12, label.implicitHeight + Style.spaceReal(verticalPadding) * 2) : barSize)

  Text {
    id: label
    visible: root.labelVisible
    anchors.centerIn: parent
    text: root.text
    color: root.foreground
    font.family: root.fontFamily
    font.pixelSize: root.fontSize
    rotation: root.textRotation
  }

  MouseArea {
    id: mouseArea
    anchors.fill: parent
    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
    enabled: root.interactive
    hoverEnabled: true
    cursorShape: root.pressable ? Qt.PointingHandCursor : Qt.ArrowCursor
    onEntered: {
      root.hovered = true
      root.tooltipHovered = root.tooltipText !== ""
      if (root.bar && root.bar.showTooltip) root.bar.showTooltip(root, root.tooltipText)
      if (root.maintainIndicatorReveal && root.revealHost && root.revealHost.setIndicatorItemHovered)
        root.revealHost.setIndicatorItemHovered(true)
    }
    onExited: {
      root.hovered = false
      root.tooltipHovered = false
      if (root.bar && root.bar.hideTooltip) root.bar.hideTooltip(root)
      if (root.maintainIndicatorReveal && root.revealHost && root.revealHost.setIndicatorItemHovered)
        root.revealHost.setIndicatorItemHovered(false)
    }
    onClicked: function(mouse) { if (root.pressable) root.triggerPress(mouse.button) }
    onWheel: function(wheel) { root.wheelMoved(wheel.angleDelta.y) }
  }
}
