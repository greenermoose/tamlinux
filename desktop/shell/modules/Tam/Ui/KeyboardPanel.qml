import QtQuick
import Quickshell
import Quickshell.Wayland
import Tam.Commons

// Layer-shell calendar card. fred.clock already calls this shape: anchorItem,
// owner, bar, open, centerOnBar, focusTarget, fittedContentWidth/Height, and
// child content. Clicks outside the card close it. The bar strip is forwarded
// to registered click targets so the clock button still receives them.
PanelWindow {
  id: root

  property Item anchorItem: null
  property QtObject bar: null
  property var owner: null
  property int margin: Style.gapsOut
  property int padding: Style.spacing.popupPadding
  property int contentWidth: Style.space(280)
  property int contentHeight: Style.space(200)
  property bool centerOnBar: false
  property bool open: false
  property int gap: Style.gapsOut
  property Item focusTarget: null

  default property alias contentItem: contentHolder.children

  readonly property var anchorWindow: anchorItem ? anchorItem.QsWindow.window : null
  readonly property string barPos: bar ? bar.position : "top"
  readonly property real screenW: screen ? screen.width : 0
  readonly property real screenH: screen ? screen.height : 0
  readonly property real barW: anchorWindow ? anchorWindow.width : 0
  readonly property real barH: anchorWindow ? anchorWindow.height : (bar ? bar.barSize : 0)
  readonly property real availableCardWidth: screenW > 0 ? Math.max(120, screenW - margin * 2) : 0
  readonly property real availableCardHeight: screenH > 0
    ? Math.max(120, screenH - barH - gap - margin) : 0

  function close() {
    if (owner && "close" in owner) owner.close()
    else root.open = false
  }

  function fittedContentWidth(width, cap) {
    var desired = Math.max(1, Number(width) || 1)
    var maxWidth = root.availableCardWidth > 0 ? root.availableCardWidth : desired
    if (cap !== undefined && Number(cap) > 0) maxWidth = Math.min(maxWidth, Number(cap))
    return Math.round(Math.min(desired, maxWidth))
  }

  function fittedContentHeight(implicitHeight, cap) {
    var desired = Math.max(root.padding * 2, (Number(implicitHeight) || 0) + root.padding * 2)
    var maxHeight = root.availableCardHeight > 0 ? root.availableCardHeight : desired
    if (cap !== undefined && Number(cap) > 0) maxHeight = Math.min(maxHeight, Number(cap))
    return Math.round(Math.min(desired, maxHeight))
  }

  readonly property point cardOrigin: {
    if (!bar) return Qt.point(margin, margin)
    var x = screenW / 2 - contentWidth / 2
    var y = barPos === "bottom" ? screenH - barH - contentHeight - gap : barH + gap
    if (!centerOnBar && anchorItem && anchorWindow) {
      var pos = anchorItem.mapToItem(anchorWindow.contentItem, 0, 0)
      if (barPos === "top" || barPos === "bottom")
        x = pos.x + anchorItem.width / 2 - contentWidth / 2
    }
    x = Math.max(margin, Math.min(x, Math.max(margin, screenW - contentWidth - margin)))
    y = Math.max(margin, Math.min(y, Math.max(margin, screenH - contentHeight - margin)))
    return Qt.point(Math.round(x), Math.round(y))
  }

  screen: anchorWindow ? anchorWindow.screen : null
  visible: open
  color: "transparent"
  exclusionMode: ExclusionMode.Ignore
  WlrLayershell.namespace: "tamlinux-clock-panel"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: open ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

  anchors {
    top: true
    bottom: true
    left: true
    right: true
  }

  onOpenChanged: {
    console.log("TAMLINUX_EVIDENCE popup-open=" + (open ? "true" : "false"))
    if (open) console.log("TAMLINUX_EVIDENCE panel-focus ondemand")
    if (!bar) return
    if (open) {
      if (bar.requestPopout) bar.requestPopout(owner || root)
      if (focusTarget) Qt.callLater(function() {
        if (root.open && root.focusTarget) root.focusTarget.forceActiveFocus()
      })
    } else if (bar.releasePopout) {
      bar.releasePopout(owner || root)
    }
  }

  Component.onDestruction: console.log("TAMLINUX_EVIDENCE popup-destroyed")

  function inBarRegion(px, py) {
    var strip = Math.max(bar ? bar.barSize : 0, barH) + gap
    if (barPos === "bottom") return py >= screenH - strip
    if (barPos === "top") return py <= strip
    return false
  }

  function forwardBarClick(px, py, button) {
    if (!anchorWindow || !bar || !bar.clickTargets) return false
    var localY = barPos === "bottom" ? py - (screenH - barH) : py
    var targets = bar.clickTargets
    for (var i = targets.length - 1; i >= 0; i--) {
      var target = targets[i]
      if (!target || !target.triggerPress) continue
      var pos = anchorWindow.itemPosition(target)
      if (px >= pos.x && px <= pos.x + target.width && localY >= pos.y && localY <= pos.y + target.height) {
        target.triggerPress(button)
        return true
      }
    }
    return false
  }

  MouseArea {
    id: dismissArea
    anchors.fill: parent
    enabled: root.open
    acceptedButtons: Qt.AllButtons
    onClicked: function(mouse) {
      if (root.inBarRegion(mouse.x, mouse.y) && root.forwardBarClick(mouse.x, mouse.y, mouse.button))
        return
      console.log("TAMLINUX_EVIDENCE popup-outside-click")
      root.close()
    }
  }

  Variants {
    model: root.open ? Quickshell.screens : []
    delegate: Component {
      PanelWindow {
        required property var modelData
        screen: modelData
        visible: root.open && !!root.screen && modelData.name !== root.screen.name
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "tamlinux-clock-panel-dismiss"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }
        MouseArea {
          anchors.fill: parent
          acceptedButtons: Qt.AllButtons
          onPressed: root.close()
        }
      }
    }
  }

  Rectangle {
    id: card
    x: root.cardOrigin.x
    y: root.cardOrigin.y
    width: root.contentWidth
    height: root.contentHeight
    radius: Style.cornerRadius
    color: Color.popups.background
    border.width: 1
    border.color: Color.popups.border

    MouseArea {
      anchors.fill: parent
      acceptedButtons: Qt.AllButtons
    }

    Item {
      id: contentHolder
      anchors.fill: parent
      anchors.margins: root.padding
    }
  }
}
