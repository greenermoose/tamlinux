import QtQuick
import Quickshell
import Quickshell.Wayland
import Tam.Commons

PanelWindow {
  id: win

  required property var shell
  property string hostKey: ""
  property var screenRef: null
  property bool loadsClock: false

  property alias surface: api
  signal clockReady(var widget)

  property string tooltipText: ""
  property real tooltipX: 0
  property var tooltipAnchor: null

  screen: screenRef
  color: Color.bar.background
  exclusionMode: ExclusionMode.Ignore
  implicitHeight: Style.bar.sizeHorizontal
  WlrLayershell.namespace: "tamlinux-proof-" + hostKey.replace("#", "-")
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
    hostKey: win.hostKey
    screen: win.screenRef
    barSize: win.implicitHeight
  }

  Row {
    anchors.left: parent.left
    anchors.leftMargin: 8
    anchors.verticalCenter: parent.verticalCenter
    spacing: 8

    Loader {
      id: clockLoader
      active: win.loadsClock && shell.clockEntry !== ""
      source: win.loadsClock ? shell.clockEntry : ""
      onLoaded: win.adopt(item, true)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE clock-load-failed host=" + win.hostKey)
      }
    }

    Loader {
      id: fixtureLoader
      active: shell.fixtureEntry !== "" && (!win.loadsClock || clockLoader.status === Loader.Ready || clockLoader.status === Loader.Error)
      source: shell.fixtureEntry
      onLoaded: win.adopt(item, false)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE fixture-load-failed host=" + win.hostKey)
      }
    }

    Loader {
      id: compositorLoader
      active: win.loadsClock && shell.compositorEntry !== ""
      source: win.loadsClock ? shell.compositorEntry : ""
      onLoaded: win.adopt(item, false)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE compositor-load-failed host=" + win.hostKey)
      }
    }

    Loader {
      id: uiLoader
      active: shell.uiEntry !== "" && (fixtureLoader.status === Loader.Ready || fixtureLoader.status === Loader.Error)
      source: shell.uiEntry
      onLoaded: win.adopt(item, false)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE ui-load-failed host=" + win.hostKey)
      }
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

  function adopt(item, isClock) {
    if (!item) return
    item.bar = api
    if (item.moduleName === "tamlinux.fixture") item.hostKey = hostKey
    if (item.moduleName === "tamlinux.compositor") {
      item.hostKey = hostKey
      item.screenRef = screenRef
    }
    if (item.moduleName === "tamlinux.ui") item.hostKey = hostKey
    var id = item.moduleName || (isClock ? "fred.clock" : "")
    item.settings = shell.entrySettings(id)
    if (item.bindHost) item.bindHost()
    api.registerWidget(item)
    if (isClock) {
      api.widget = item
      clockReady(item)
      var text = item.displayText || ""
      shell.evidence("ready screen=" + (screenRef ? screenRef.name || "" : "")
        + " host=" + hostKey
        + " format=" + String(item.configuredFormat || "")
        + " text=" + JSON.stringify(text))
      console.log("TAMLINUX_EVIDENCE clock-loaded host=" + hostKey)
    }
  }

  function firstClickTarget() {
    return api.clickTargets.length > 0 ? api.clickTargets[0] : null
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
    showTooltip(clockLoader.item || win, label + "\nscale " + Style.uiScale)
  }

  function logTooltip() {
    if (tooltipText === "") return
    console.log("TAMLINUX_EVIDENCE tooltip scale=" + Style.uiScale
      + " font=" + Style.font.bodySmall
      + " width=" + tipWindow.implicitWidth
      + " height=" + tipWindow.implicitHeight
      + " text=" + JSON.stringify(tooltipText))
  }

  Component.onCompleted: {
    shell.attachHost(win)
    console.log("TAMLINUX_EVIDENCE bar-created host=" + hostKey + " screen=" + (screenRef ? screenRef.name || "" : ""))
  }

  Component.onDestruction: {
    api.clearSurface()
    shell.unregisterHost(hostKey)
    shell.detachHost(win)
    console.log("TAMLINUX_EVIDENCE bar-destroyed host=" + hostKey + " screen=" + (screenRef ? screenRef.name || "" : ""))
  }

  PanelWindow {
    id: tipWindow
    visible: win.tooltipText !== ""
    screen: win.screenRef
    color: Color.tooltip.background
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "tamlinux-tooltip-" + win.hostKey.replace("#", "-")
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
