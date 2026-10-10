import QtQuick
import Quickshell
import Quickshell.Wayland
import Tam.Commons
import "TooltipParser.js" as TooltipParser

PanelWindow {
  id: win

  required property var shell
  property string hostKey: ""
  property var screenRef: null
  property bool loadsClock: false
  // Draw the shell's layout (BarLayout.qml) rather than the proof's row.
  readonly property bool layoutMode: shell.barLayout !== null

  property alias surface: api
  signal clockReady(var widget)

  property string tooltipText: ""
  readonly property var parsedTooltip: TooltipParser.parse(win.tooltipText)
  // The hovered item's center along the bar; the tooltip centers on it and
  // is kept a gap inside both screen edges, as Omarchy's bar does.
  property real tooltipCenterX: 0
  readonly property real tooltipGap: Style.space(6)
  readonly property real tooltipX: {
    var width = tipWindow.implicitWidth
    var left = tooltipCenterX - width / 2
    var right = win.width - width - tooltipGap
    return Math.max(tooltipGap, Math.min(left, right))
  }
  property var tooltipAnchor: null
  // "top" or "bottom", from the layout document (shell.barPosition).
  readonly property string position: shell.barPosition
  readonly property bool atBottom: position === "bottom"
  // Hidden stays mapped but parks off screen and gives up its exclusive
  // zone, as Omarchy's bar does (~/.local/state/tamlinux/toggles/bar-off).
  readonly property bool hidden: shell.barHidden
  readonly property bool transparent: shell.barTransparent

  screen: screenRef
  color: transparent ? "transparent" : Color.bar.background
  exclusionMode: !hidden && Quickshell.env("TAMLINUX_BAR_EXCLUSIVE") === "1" ? ExclusionMode.Auto : ExclusionMode.Ignore
  implicitHeight: Style.bar.sizeHorizontal
  WlrLayershell.namespace: "tamlinux-bar-" + hostKey.replace("#", "-")
  WlrLayershell.layer: WlrLayer.Top
  WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

  anchors {
    left: true
    right: true
    top: !win.atBottom
    bottom: win.atBottom
  }
  margins.top: hidden && !atBottom ? -implicitHeight : 0
  margins.bottom: hidden && atBottom ? -implicitHeight : 0
  onHiddenChanged: if (hidden) tooltipText = ""

  BarApi {
    id: api
    host: win
    shell: win.shell
    hostKey: win.hostKey
    screen: win.screenRef
    position: win.position
    transparent: win.transparent
    hidden: win.hidden
    barSize: win.implicitHeight
    layoutConfig: win.layoutMode ? shell.barLayout.layout : ({ "left": [], "center": [], "right": [] })
  }

  Loader {
    anchors.fill: parent
    active: win.layoutMode
    sourceComponent: Component {
      BarLayout {
        api: win.surface
        layout: shell.barLayout.layout
        centerAnchor: shell.barLayout.centerAnchor
        pluginEntries: shell.pluginEntries
        onAdoptRequested: function(item, id) { win.adopt(item, id === "fred.clock") }
      }
    }
  }

  Row {
    visible: !win.layoutMode
    anchors.left: parent.left
    anchors.leftMargin: 8
    anchors.verticalCenter: parent.verticalCenter
    spacing: 8

    Loader {
      id: clockLoader
      active: !win.layoutMode && win.loadsClock && shell.clockEntry !== ""
      source: win.loadsClock ? shell.clockEntry : ""
      onLoaded: win.adopt(item, true)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE clock-load-failed host=" + win.hostKey)
      }
    }

    Loader {
      id: fixtureLoader
      active: !win.layoutMode && shell.fixtureEntry !== "" && (!win.loadsClock || clockLoader.status === Loader.Ready || clockLoader.status === Loader.Error)
      source: shell.fixtureEntry
      onLoaded: win.adopt(item, false)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE fixture-load-failed host=" + win.hostKey)
      }
    }

    Loader {
      id: compositorLoader
      active: !win.layoutMode && win.loadsClock && shell.compositorEntry !== ""
      source: win.loadsClock ? shell.compositorEntry : ""
      onLoaded: win.adopt(item, false)
      onStatusChanged: {
        if (status === Loader.Error)
          console.log("TAMLINUX_EVIDENCE compositor-load-failed host=" + win.hostKey)
      }
    }

    Repeater {
      model: !win.layoutMode && (win.loadsClock || Quickshell.env("TAMLINUX_PLUGINS_ON_ALL") === "1") ? shell.extraEntries : []
      delegate: Loader {
        required property string modelData
        source: modelData
        onLoaded: win.adopt(item, false)
        onStatusChanged: {
          if (status === Loader.Error)
            console.log("TAMLINUX_EVIDENCE plugin-load-failed " + modelData)
        }
      }
    }

    Loader {
      id: uiLoader
      active: !win.layoutMode && shell.uiEntry !== "" && (fixtureLoader.status === Loader.Ready || fixtureLoader.status === Loader.Error)
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
    visible: !win.layoutMode && clockLoader.status === Loader.Error
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
      var pos = target.mapToItem(contentItem, target.width / 2, 0)
      tooltipCenterX = pos.x
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
      + " x=" + Math.round(tooltipX)
      + " barWidth=" + Math.round(win.width)
      + " side=" + (win.atBottom ? "above" : "below")
      + " height=" + tipWindow.implicitHeight
      + " text=" + JSON.stringify(tooltipText))
  }

  Component.onCompleted: {
    shell.attachHost(win)
    console.log("TAMLINUX_EVIDENCE bar-created host=" + hostKey + " screen=" + (screenRef ? screenRef.name || "" : "")
      + " position=" + position)
  }

  onPositionChanged: console.log("TAMLINUX_EVIDENCE bar-moved host=" + hostKey + " position=" + position)

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
    // On the side away from the screen edge: below a top bar, above a
    // bottom one.
    anchors.top: !win.atBottom
    anchors.bottom: win.atBottom
    anchors.left: true
    margins.top: win.atBottom ? 0 : win.implicitHeight + Style.space(6)
    margins.bottom: win.atBottom ? win.implicitHeight + Style.space(6) : 0
    margins.left: Math.round(win.tooltipX)
    implicitWidth: tipContent.implicitWidth + Style.spacing.controlPaddingX * 2
    implicitHeight: tipContent.implicitHeight + Style.spacing.controlPaddingY * 2

    Column {
      id: tipContent
      anchors.centerIn: parent
      spacing: (tipLabel.visible && tipFooterLabel.visible) ? Style.space(6) : 0

      Text {
        id: tipLabel
        visible: text !== ""
        anchors.horizontalCenter: parent.horizontalCenter
        text: win.parsedTooltip.body
        color: Color.tooltip.text
        font.family: Style.font.family
        font.pixelSize: Style.font.bodySmall
        horizontalAlignment: Text.AlignHCenter
      }

      Text {
        id: tipFooterLabel
        visible: text !== ""
        anchors.horizontalCenter: parent.horizontalCenter
        text: win.parsedTooltip.footer
        color: Color.tooltip.text
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
        opacity: 0.45
        horizontalAlignment: Text.AlignHCenter
      }
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
