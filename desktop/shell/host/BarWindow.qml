import QtQuick
import Quickshell
import Quickshell.Wayland
import Tam.Commons

PanelWindow {
  id: win

  required property var screenRef
  required property var shell

  signal clockReady(var widget)

  property string tooltipText: ""
  property real tooltipX: 0
  property var tooltipAnchor: null

  screen: screenRef
  color: Color.bar.background
  exclusionMode: ExclusionMode.Ignore
  implicitHeight: Style.bar.sizeHorizontal
  WlrLayershell.namespace: "tamlinux-clock-proof"
  WlrLayershell.layer: WlrLayer.Top
  WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

  anchors {
    left: true
    right: true
    bottom: true
  }

  BarApi {
    id: api
    host: win
    shell: win.shell
    barSize: win.implicitHeight
  }

  Loader {
    id: clockLoader
    active: shell.clockEntry !== ""
    source: shell.clockEntry
    onLoaded: {
      api.widget = item
      item.bar = api
      item.settings = shell.clockEntrySettings()
      win.clockReady(item)
      console.log("TAMLINUX_EVIDENCE clock-loaded")
    }
    onStatusChanged: {
      if (status === Loader.Error)
        console.log("TAMLINUX_EVIDENCE clock-load-failed")
    }
  }

  Text {
    anchors.left: parent.left
    anchors.leftMargin: 8
    anchors.verticalCenter: parent.verticalCenter
    visible: clockLoader.status === Loader.Error
    color: Color.urgent
    text: "fred.clock failed to load"
    font.pixelSize: Style.font.body
  }

  function showTooltip(target, text) {
    tooltipAnchor = target
    tooltipText = String(text || "")
    if (target && target.mapToItem) {
      var pos = target.mapToItem(contentItem, 0, 0)
      tooltipX = Math.max(0, pos.x)
    }
    Qt.callLater(logTooltip)
  }

  function hideTooltip(target) {
    if (!target || tooltipAnchor === target) tooltipText = ""
  }

  function probeTooltip() {
    var label = api.widget ? ("fred.clock v" + (api.widget.pluginVersion || "")) : "fred.clock"
    showTooltip(clockLoader.item, label + "\nscale " + Style.uiScale)
  }

  function logTooltip() {
    if (tooltipText === "") return
    console.log("TAMLINUX_EVIDENCE tooltip scale=" + Style.uiScale
      + " font=" + Style.font.bodySmall
      + " width=" + tipWindow.implicitWidth
      + " height=" + tipWindow.implicitHeight
      + " text=" + JSON.stringify(tooltipText))
  }

  Component.onCompleted: console.log("TAMLINUX_EVIDENCE bar-created screen=" + (screenRef.name || ""))
  Component.onDestruction: console.log("TAMLINUX_EVIDENCE bar-destroyed screen=" + (screenRef.name || ""))

  PanelWindow {
    id: tipWindow
    visible: win.tooltipText !== ""
    screen: win.screenRef
    color: Color.tooltip.background
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "tamlinux-clock-tooltip"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    anchors.bottom: true
    anchors.left: true
    margins.bottom: win.implicitHeight + Style.space(6)
    margins.left: Math.round(win.tooltipX)
    implicitWidth: tipLabel.implicitWidth + Style.spacing.controlPaddingX * 2
    implicitHeight: tipLabel.implicitHeight + Style.spacing.controlPaddingY * 2

    Text {
      id: tipLabel
      anchors.centerIn: parent
      text: win.tooltipText
      color: Color.tooltip.text
      font.family: Style.font.family
      font.pixelSize: Style.font.bodySmall
    }

    Rectangle {
      anchors.fill: parent
      color: "transparent"
      radius: Style.cornerRadius
      border.width: 1
      border.color: Color.tooltip.border
    }
  }
}
