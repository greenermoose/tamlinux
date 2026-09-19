import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons
import "Model.js" as Model

Panel {
  id: root
  moduleName: "omarchy.monitor"
  ipcTarget: "omarchy.monitor"
  manageIpc: false

  readonly property string pluginVersion: "1.0.0"
  readonly property var monitorEnv: ["HOME", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "HYPRLAND_INSTANCE_SIGNATURE", "DBUS_SESSION_BUS_ADDRESS", "XDG_CONFIG_HOME", "XDG_DATA_HOME"]

  property int brightnessPercent: 0
  property int pendingBrightnessPercent: 0
  property bool brightnessAvailable: false
  property string focusedMonitor: ""
  property string monitorScale: ""
  property var displays: []
  property int enabledDisplayCount: 0
  property var displayCache: ({})
  property string expandedCard: ""

  // Retraining state
  property string resetRunningMonitor: ""
  property var resetStatus: ({})
  property string lastResetOutput: ""

  // DPMS safety state
  property string dpmsSafetyMonitor: ""
  property int dpmsCountdown: 10

  // Touchpad wheel accumulator
  property real wheelAccumulator: 0

  readonly property var scalePresets: ["1", "1.25", "1.6", "2", "3", "4"]

  // Text size slider — curated macOS-style notches (px)
  readonly property var textSizeStops: [9, 10, 11, 12, 14, 16, 20]
  property int textSizePreviewIndex: -1
  property bool reflowingText: false

  function markReflowing() {
    root.reflowingText = true
    reflowSettle.restart()
  }

  // Focus and keyboard navigation
  // focusSection: "textsize" or "card_" + display.name
  property string focusSection: "textsize"
  property int cardSubRow: 0
  property int cardSubItem: 0
  property bool cursorActive: false

  readonly property var visibleSections: {
    var list = ["textsize"]
    for (var i = 0; i < displays.length; i++) {
      if (displays[i] && displays[i].name) {
        list.push("card_" + displays[i].name)
      }
    }
    return list
  }

  function findDisplay(name) {
    for (var i = 0; i < displays.length; i++) {
      if (displays[i] && displays[i].name === name) return displays[i]
    }
    return null
  }

  function findDisplayIndex(name) {
    for (var i = 0; i < displays.length; i++) {
      if (displays[i] && displays[i].name === name) return i
    }
    return -1
  }

  function getTargetDisplay() {
    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var d = findDisplay(name)
      if (d) return d
    }
    return findDisplay(root.focusedMonitor) || (displays.length > 0 ? displays[0] : null)
  }

  function cardSubRows(display) {
    if (!display) return ["header"]
    var rows = ["header"]
    if (root.expandedCard === display.name && display.enabled) {
      if (display.brightnessAvailable) rows.push("brightness")
      rows.push("scale")
      if (display.availableRates && display.availableRates.length > 0) rows.push("rate")
      rows.push("actions")
    }
    return rows
  }

  function moveCursor(delta) {
    if (focusSection === "textsize") {
      if (delta > 0 && displays.length > 0) {
        var first = displays[0]
        focusSection = "card_" + first.name
        root.expandedCard = first.name
        cardSubRow = 0
        cardSubItem = 0
      }
      return
    }

    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var currentDisp = findDisplay(name)
      var subRows = cardSubRows(currentDisp)

      if (delta > 0) {
        if (cardSubRow < subRows.length - 1) {
          cardSubRow = cardSubRow + 1
          cardSubItem = 0
        } else {
          var idx = findDisplayIndex(name)
          if (idx < displays.length - 1) {
            var next = displays[idx + 1]
            focusSection = "card_" + next.name
            root.expandedCard = next.name
            cardSubRow = 0
            cardSubItem = 0
          }
        }
      } else {
        if (cardSubRow > 0) {
          cardSubRow = cardSubRow - 1
          cardSubItem = 0
        } else {
          var pIdx = findDisplayIndex(name)
          if (pIdx > 0) {
            var prev = displays[pIdx - 1]
            focusSection = "card_" + prev.name
            root.expandedCard = prev.name
            var prevRows = cardSubRows(prev)
            cardSubRow = prevRows.length - 1
            cardSubItem = 0
          } else {
            focusSection = "textsize"
            cardSubRow = 0
            cardSubItem = 0
          }
        }
      }
    }
  }

  function moveCursorH(delta) {
    if (focusSection === "textsize") {
      adjustTextSize(delta)
      return
    }

    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var d = findDisplay(name)
      if (!d) return
      var subRows = cardSubRows(d)
      var rowName = cardSubRow < subRows.length ? subRows[cardSubRow] : "header"

      if (rowName === "header") {
        if (delta > 0) cardSubItem = 1
        else if (delta < 0) cardSubItem = 0
      } else if (rowName === "brightness") {
        var curB = d.brightness !== undefined ? d.brightness : 50
        setMonitorBrightness(d.name, curB + delta * 5)
      } else if (rowName === "scale") {
        var scales = Model.availableScales(scalePresets, d.width, d.height)
        var sIdx = cardSubItem + delta
        if (sIdx < 0) sIdx = 0
        if (sIdx >= scales.length) sIdx = scales.length - 1
        cardSubItem = sIdx
      } else if (rowName === "rate") {
        var rates = d.availableRates || []
        var rIdx = cardSubItem + delta
        if (rIdx < 0) rIdx = 0
        if (rIdx >= rates.length) rIdx = rates.length - 1
        cardSubItem = rIdx
      } else if (rowName === "actions") {
        var aIdx = cardSubItem + delta
        if (aIdx < 0) aIdx = 0
        if (aIdx > 1) aIdx = 1
        cardSubItem = aIdx
      }
    }
  }

  function activateCursor() {
    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var d = findDisplay(name)
      if (!d) return
      var subRows = cardSubRows(d)
      var rowName = cardSubRow < subRows.length ? subRows[cardSubRow] : "header"

      if (rowName === "header") {
        if (cardSubItem === 1) {
          toggleDisplay(d.name, d.enabled)
        } else {
          toggleCardExpanded(d.name)
        }
      } else if (rowName === "scale") {
        var scales = Model.availableScales(scalePresets, d.width, d.height)
        if (cardSubItem >= 0 && cardSubItem < scales.length) {
          setMonitorScale(d.name, scales[cardSubItem])
        }
      } else if (rowName === "rate") {
        var rates = d.availableRates || []
        if (cardSubItem >= 0 && cardSubItem < rates.length) {
          setMonitorRefreshRate(d.name, rates[cardSubItem])
        }
      } else if (rowName === "actions") {
        if (cardSubItem === 0) {
          if (root.dpmsSafetyMonitor === d.name) {
            restoreDpms()
          } else if (d.dpmsStatus) {
            setDpmsOffWithSafety(d.name)
          } else {
            setDpmsOn(d.name)
          }
        } else if (cardSubItem === 1) {
          resetDisplay(d.name)
        }
      }
    }
  }

  function toggleCardExpanded(name) {
    if (root.expandedCard === name) {
      root.expandedCard = ""
    } else {
      root.expandedCard = name
    }
  }

  function clampCursor() {
    var sections = visibleSections
    if (!sections || !sections.length) return
    if (sections.indexOf(focusSection) < 0) {
      focusSection = sections[0]
      cardSubRow = 0
      cardSubItem = 0
      return
    }
    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var d = findDisplay(name)
      var subRows = cardSubRows(d)
      if (cardSubRow >= subRows.length) {
        cardSubRow = Math.max(0, subRows.length - 1)
        cardSubItem = 0
      }
    }
  }

  function ensureCursorVisible(item) {
    if (!item || !scrollArea) return
    var flick = scrollArea.contentItem
    if (!flick || flick.contentY === undefined) return
    var pt = item.mapToItem(flick.contentItem || flick, 0, 0)
    var top = pt.y
    var bottom = top + (item.height || 0)
    var viewTop = flick.contentY
    var viewBottom = viewTop + flick.height
    var margin = 6
    if (top < viewTop + margin) flick.contentY = Math.max(0, top - margin)
    else if (bottom > viewBottom - margin)
      flick.contentY = bottom + margin - flick.height
  }

  function updateState(raw) {
    var state = Model.parseState(raw)
    root.displays = state.displays
    root.enabledDisplayCount = state.enabledDisplayCount
    if (state.focusedMonitor) {
      root.focusedMonitor = state.focusedMonitor
    }

    for (var i = 0; i < root.displays.length; i++) {
      var d = root.displays[i]
      if (d && d.name && d.enabled) {
        root.displayCache[d.name] = {
          name: d.name,
          width: d.width,
          height: d.height,
          refreshRate: d.refreshRate,
          x: d.x,
          y: d.y,
          scale: d.scale
        }
      }
    }

    var focusedDisp = root.findDisplay(root.focusedMonitor)
    if (focusedDisp) {
      root.brightnessAvailable = focusedDisp.brightnessAvailable
      if (focusedDisp.brightnessAvailable && !brightnessDebounce.running) {
        root.brightnessPercent = focusedDisp.brightness
      }
      root.monitorScale = Model.normalizeScale(String(focusedDisp.scale || 1))
    } else if (root.displays.length > 0) {
      var first = root.displays[0]
      root.brightnessAvailable = first.brightnessAvailable
      if (first.brightnessAvailable && !brightnessDebounce.running) {
        root.brightnessPercent = first.brightness
      }
      root.monitorScale = Model.normalizeScale(String(first.scale || 1))
    }

    if (root.expandedCard === "" && root.displays.length > 0) {
      root.expandedCard = root.focusedMonitor || root.displays[0].name
    }
  }

  function effectiveScale(scale) {
    return Model.normalizeScale(scale)
  }

  function brightnessName(percent) {
    return Model.brightnessName(percent)
  }

  // --- Display Management Actions ---
  function toggleDisplay(name, enabled) {
    if (!name || !Model.isValidOutputName(name)) return
    if (enabled && root.enabledDisplayCount <= 1) return

    var lua = ""
    if (enabled) {
      lua = 'hl.monitor({ output = "' + name + '", disabled = true })'
    } else {
      var d = root.findDisplay(name)
      var cached = root.displayCache[name] || {}
      var width = (d && d.width) ? d.width : (cached.width || 1920)
      var height = (d && d.height) ? d.height : (cached.height || 1080)
      var rate = (d && d.refreshRate) ? Math.round(d.refreshRate) : (cached.refreshRate ? Math.round(cached.refreshRate) : 60)
      var x = (d && d.x !== undefined) ? d.x : (cached.x !== undefined ? cached.x : 0)
      var y = (d && d.y !== undefined) ? d.y : (cached.y !== undefined ? cached.y : 0)
      var scale = (d && d.scale) ? d.scale : (cached.scale || 1)

      var mode = width + "x" + height + "@" + rate
      var pos = x + "x" + y
      lua = 'hl.monitor({ output = "' + name + '", mode = "' + mode + '", position = "' + pos + '", scale = ' + scale + ', disabled = false })'
    }

    actionProc.exe = "/usr/bin/hyprctl"
    actionProc.args = ["eval", lua]
    actionProc.launch()
  }

  function setMonitorScale(name, scale) {
    if (!name || !Model.isValidOutputName(name)) return
    var d = findDisplay(name)
    if (!d) return
    var clean = Model.cleanScale(scale, d.width, d.height)
    if (clean === "") clean = Model.normalizeScale(scale)
    if (clean === "") return

    var rate = d.refreshRate ? Math.round(d.refreshRate) : 60
    var mode = d.width + "x" + d.height + "@" + rate
    var pos = (d.x !== undefined ? d.x : 0) + "x" + (d.y !== undefined ? d.y : 0)
    var lua = 'hl.monitor({ output = "' + d.name + '", mode = "' + mode + '", position = "' + pos + '", scale = ' + clean + ' })'

    actionProc.exe = "/usr/bin/hyprctl"
    actionProc.args = ["eval", lua]
    actionProc.launch()
  }

  function setMonitorRefreshRate(name, rate) {
    if (!name || !Model.isValidOutputName(name)) return
    var d = findDisplay(name)
    if (!d) return
    var rateNum = Number(rate)
    if (!isFinite(rateNum) || rateNum <= 0) return

    var mode = d.width + "x" + d.height + "@" + rateNum
    var pos = (d.x !== undefined ? d.x : 0) + "x" + (d.y !== undefined ? d.y : 0)
    var scale = d.scale || 1
    var lua = 'hl.monitor({ output = "' + d.name + '", mode = "' + mode + '", position = "' + pos + '", scale = ' + scale + ' })'

    actionProc.exe = "/usr/bin/hyprctl"
    actionProc.args = ["eval", lua]
    actionProc.launch()
  }

  function setMonitorBrightness(monitorName, percent) {
    if (!monitorName || !Model.isValidOutputName(monitorName)) return
    var p = Model.clampBrightness(percent)

    // Update locally so UI responds immediately
    var dList = []
    for (var i = 0; i < root.displays.length; i++) {
      var item = Object.assign({}, root.displays[i])
      if (item.name === monitorName) {
        item.brightness = p
      }
      dList.push(item)
    }
    root.displays = dList

    if (monitorName === root.focusedMonitor) {
      root.brightnessPercent = p
      root.pendingBrightnessPercent = p
    }

    setBrightnessProc.exe = "/usr/share/omarchy/bin/omarchy-brightness-display"
    setBrightnessProc.args = ["--no-osd", "--monitor", monitorName, p + "%"]
    setBrightnessProc.launch()
  }

  function previewMonitorBrightness(monitorName, percent) {
    var p = Model.clampBrightness(percent)
    for (var i = 0; i < root.displays.length; i++) {
      if (root.displays[i].name === monitorName) {
        root.displays[i].brightness = p
        break
      }
    }
    if (monitorName === root.focusedMonitor) {
      root.brightnessPercent = p
    }
    brightnessDebounce.restart()
  }

  function setBrightness(value) {
    var target = root.focusedMonitor || (root.displays.length > 0 ? root.displays[0].name : "")
    if (target) setMonitorBrightness(target, value)
  }

  function showBrightnessOsd(percent) {
    if (!bar || !bar.shell) return
    bar.shell.summon("omarchy.osd", JSON.stringify({
      icon: "brightness",
      value: percent
    }))
  }

  // --- DPMS Controls & Safety Timer ---
  function setDpmsOffWithSafety(name) {
    if (!name || !Model.isValidOutputName(name)) return
    root.dpmsSafetyMonitor = name
    root.dpmsCountdown = 10
    actionProc.exe = "/usr/bin/hyprctl"
    actionProc.args = ["eval", 'hl.dispatch(hl.dsp.dpms({ action = "disable", monitor = "' + name + '" }))']
    actionProc.launch()
  }

  function confirmDpmsOff() {
    root.dpmsSafetyMonitor = ""
    dpmsSafetyTimer.stop()
  }

  function restoreDpms() {
    var mon = root.dpmsSafetyMonitor
    root.dpmsSafetyMonitor = ""
    dpmsSafetyTimer.stop()
    if (mon) {
      actionProc.exe = "/usr/bin/hyprctl"
      actionProc.args = ["eval", 'hl.dispatch(hl.dsp.dpms({ action = "enable", monitor = "' + mon + '" }))']
      actionProc.launch()
    }
  }

  function setDpmsOn(name) {
    if (!name || !Model.isValidOutputName(name)) return
    if (root.dpmsSafetyMonitor === name) {
      root.dpmsSafetyMonitor = ""
      dpmsSafetyTimer.stop()
    }
    actionProc.exe = "/usr/bin/hyprctl"
    actionProc.args = ["eval", 'hl.dispatch(hl.dsp.dpms({ action = "enable", monitor = "' + name + '" }))']
    actionProc.launch()
  }

  Timer {
    id: dpmsSafetyTimer
    interval: 1000
    repeat: true
    running: root.dpmsSafetyMonitor !== ""
    onTriggered: {
      root.dpmsCountdown--
      if (root.dpmsCountdown <= 0) {
        root.restoreDpms()
      }
    }
  }

  // --- Display Retraining (Reset) ---
  function resetDisplay(name) {
    if (!name || !Model.isValidOutputName(name)) return "invalid output name"
    if (resetProc.running) return "reset already running"

    var d = findDisplay(name)
    if (!d) return "output not found"

    root.resetRunningMonitor = name
    root.lastResetOutput = ""
    var copy = Object.assign({}, root.resetStatus)
    copy[name] = { status: "running", message: "Retraining…" }
    root.resetStatus = copy

    resetProc.exe = "/usr/bin/bash"
    resetProc.args = [Model.helperPath("fred-monitor-reset"), name]
    resetProc.launch()
    return "resetting " + name
  }

  function resetHighlighted() {
    var d = getTargetDisplay()
    if (d && d.name) root.resetDisplay(d.name)
  }

  // --- Text Size Controls ---
  function nearestTextStop(px) {
    var best = 0
    var bestDist = 1e9
    for (var i = 0; i < textSizeStops.length; i++) {
      var d = Math.abs(textSizeStops[i] - px)
      if (d < bestDist) { bestDist = d; best = i }
    }
    return best
  }

  function currentTextIndex() {
    return textSizePreviewIndex >= 0 ? textSizePreviewIndex : nearestTextStop(Style.font.baseSize)
  }

  function displayedTextPx() {
    return textSizePreviewIndex >= 0 ? textSizeStops[textSizePreviewIndex] : Style.font.baseSize
  }

  function setTextSize(px) {
    textScaleProc.exe = "/usr/share/omarchy/bin/omarchy-display-text-size"
    textScaleProc.args = [String(px)]
    textScaleProc.launch()
  }

  function adjustTextSize(deltaSteps) {
    var idx = currentTextIndex() + deltaSteps
    if (idx < 0) idx = 0
    if (idx > textSizeStops.length - 1) idx = textSizeStops.length - 1
    markReflowing()
    textSizePreviewIndex = idx
    setTextSize(textSizeStops[idx])
  }

  // --- IPC Methods ---
  function brightnessIpc(percent) {
    var value = Number(percent)
    root.setBrightness(value)
    return "got " + root.pendingBrightnessPercent
  }

  function stateIpc() {
    return JSON.stringify({
      version: root.pluginVersion,
      brightness: root.brightnessPercent,
      brightnessAvailable: root.brightnessAvailable,
      focusedMonitor: root.focusedMonitor,
      scale: root.monitorScale,
      displays: root.displays,
      resetRunning: root.resetRunningMonitor,
      resetStatus: root.resetStatus,
      expandedCard: root.expandedCard,
      dpmsSafetyMonitor: root.dpmsSafetyMonitor
    })
  }

  IpcHandler {
    target: "omarchy.monitor"

    function brightness(percent: string): string { return root.brightnessIpc(percent) }
    function state(): string { return root.stateIpc() }
    function reset(name: string): string { return root.resetDisplay(name) }
    function open() { root.open() }
    function close() { root.close() }
    function toggle() { root.toggle() }
    function show() { root.open() }
    function hide() { root.close() }
  }

  function refresh() {
    stateProc.launch()
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component.onCompleted: refresh()

  onOpenedChanged: {
    if (opened) {
      refresh()
      if (displays.length > 0) {
        var targetName = root.focusedMonitor || displays[0].name
        root.expandedCard = targetName
        root.focusSection = "card_" + targetName
        root.cardSubRow = 0
        root.cardSubItem = 0
      } else {
        root.focusSection = "textsize"
      }
      cursorActive = false
    } else {
      if (root.dpmsSafetyMonitor !== "") {
        root.restoreDpms()
      }
    }
  }

  onDisplaysChanged: clampCursor()
  onVisibleSectionsChanged: clampCursor()

  Timer {
    interval: 5000
    running: root.opened
    repeat: true
    onTriggered: root.refresh()
  }

  // --- External Processes ---
  Launch {
    id: stateProc
    exe: "/usr/bin/python3"
    args: [Model.helperPath("fred-monitor-state")]
    envKeys: root.monitorEnv
    deadlineMs: 6000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var raw = String(text || "").trim()
        root.updateState(raw)
      }
    }
  }

  Timer {
    id: brightnessDebounce
    interval: 180
    repeat: false
    onTriggered: {
      var d = root.findDisplay(root.focusedMonitor)
      if (d && d.brightness !== undefined) {
        root.setMonitorBrightness(d.name, d.brightness)
      }
    }
  }

  Launch {
    id: setBrightnessProc
    exe: "/usr/share/omarchy/bin/omarchy-brightness-display"
    envKeys: root.monitorEnv
    deadlineMs: 5000
    stdout: StdioCollector { waitForEnd: true }
  }

  Launch {
    id: actionProc
    envKeys: root.monitorEnv
    deadlineMs: 10000
    stdout: StdioCollector { waitForEnd: true }
    onRunningChanged: if (!running) root.refresh()
  }

  Launch {
    id: resetProc
    envKeys: root.monitorEnv
    deadlineMs: 35000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var lines = String(text || "").trim().split("\n")
        if (lines.length > 0) root.lastResetOutput = lines[lines.length - 1]
      }
    }
  }

  Connections {
    target: resetProc
    function onExited(exitCode) {
      var mon = root.resetRunningMonitor
      if (mon !== "") {
        var copy = Object.assign({}, root.resetStatus)
        if (exitCode === 0) {
          copy[mon] = { status: "success", message: "Retrained" }
        } else {
          copy[mon] = { status: "error", message: "Failed — press again" }
        }
        root.resetStatus = copy
        resetClearTimer.restart()
        root.resetRunningMonitor = ""
      }
      root.refresh()
    }
  }

  Timer {
    id: resetClearTimer
    interval: 4000
    repeat: false
    onTriggered: {
      root.resetStatus = ({})
    }
  }

  Launch {
    id: textScaleProc
    exe: "/usr/share/omarchy/bin/omarchy-display-text-size"
    envKeys: root.monitorEnv
    deadlineMs: 5000
    stdout: StdioCollector { waitForEnd: true }
  }

  Timer {
    id: reflowSettle
    interval: 300
    repeat: false
    onTriggered: root.reflowingText = false
  }

  Connections {
    target: Style
    function onFontBaseSizeChanged() {
      root.markReflowing()
      if (root.textSizePreviewIndex >= 0
          && root.nearestTextStop(Style.font.baseSize) === root.textSizePreviewIndex)
        root.textSizePreviewIndex = -1
    }
  }

  // --- Top Bar Icon ---
  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: Quickshell.screens.length > 1 ? "󰍺" : "󰍹"
    tooltipText: "Display\n\nfred.monitor v" + root.pluginVersion
    onPressed: function(b) { root.toggle() }
    onWheelMoved: function(delta) {
      if (!root.brightnessAvailable) return
      var wheel = Util.wheelSteps(root.wheelAccumulator, delta)
      root.wheelAccumulator = wheel.remainder
      if (wheel.steps === 0) return
      root.setBrightness(root.brightnessPercent + wheel.steps * 5)
      root.showBrightnessOsd(root.brightnessPercent)
    }
  }

  // --- Main Panel Window ---
  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(400))
    contentHeight: panel.fittedContentHeight(panelColumn.implicitHeight, Style.space(620))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onMoveRequested: function(dx, dy) {
        if (!root.cursorActive) { root.cursorActive = true; return }
        if (dy !== 0) root.moveCursor(dy)
        else if (dx !== 0) root.moveCursorH(dx)
      }
      onActivateRequested: if (root.cursorActive) root.activateCursor()
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onTextKey: function(t) {
        if (t === "r" || t === "R") root.resetHighlighted()
      }

      ScrollView {
        id: scrollArea
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: panelColumn.implicitHeight > height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        Binding {
          target: scrollArea.contentItem
          property: "interactive"
          value: panelColumn.implicitHeight > scrollArea.height
        }

        Column {
          id: panelColumn
          width: scrollArea.availableWidth
          spacing: Style.space(12)

          // ---------- Hero: display icon · title/status ----------
          Item {
            width: parent.width
            implicitHeight: Math.max(heroIcon.implicitHeight, heroLabels.implicitHeight)

            Text {
              id: heroIcon
              textFormat: Text.PlainText
              text: root.displays.length > 1 ? "󰍺" : "󰍹"
              color: root.bar.foreground
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.display
              anchors.left: parent.left
              anchors.verticalCenter: parent.verticalCenter
            }

            Column {
              id: heroLabels
              anchors.left: heroIcon.right
              anchors.leftMargin: Style.space(14)
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(2)

              Text {
                text: "Display"
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
                elide: Text.ElideRight
                width: parent.width
              }

              Text {
                id: heroLabel
                textFormat: Text.PlainText
                text: {
                  var fd = root.findDisplay(root.focusedMonitor)
                  if (fd && fd.brightnessAvailable) {
                    return root.brightnessName(fd.brightness).toUpperCase()
                  }
                  return (root.enabledDisplayCount + " ACTIVE DISPLAYS").toUpperCase()
                }
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
                font.letterSpacing: 1.2
                elide: Text.ElideRight
                width: parent.width
              }
            }
          }

          // ---------- Text size ----------
          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              implicitHeight: Math.max(textSizeHeader.implicitHeight, textSizePx.implicitHeight)

              PanelSectionHeader {
                id: textSizeHeader
                text: "TEXT SIZE"
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                id: textSizePx
                textFormat: Text.PlainText
                text: (textSizeSlider.dragging
                       ? root.textSizeStops[Math.round(textSizeSlider.liveValue)]
                       : root.displayedTextPx()) + "px"
                color: Qt.darker(root.bar.foreground, 1.4)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
                anchors.right: parent.right
                anchors.rightMargin: Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
              }
            }

            CursorSurface {
              id: textSizeRow
              width: parent.width
              height: textSizeSlider.implicitHeight + Style.spacing.controlGap
              hasCursor: root.cursorActive && root.focusSection === "textsize"
              onHasCursorChanged: if (hasCursor) root.ensureCursorVisible(textSizeRow)
              foreground: root.bar.foreground
              outline: true

              PanelSlider {
                id: textSizeSlider
                bar: root.bar
                anchors.fill: parent
                anchors.leftMargin: Style.space(6)
                anchors.rightMargin: Style.space(6)
                minimum: 0
                maximum: root.textSizeStops.length - 1
                step: 1
                integer: true
                tickCount: root.textSizeStops.length
                value: root.currentTextIndex()
                onReleased: function(v) { root.setTextSize(root.textSizeStops[Math.round(v)]) }
              }

              HoverHandler {
                onHoveredChanged: if (hovered && !root.reflowingText) {
                  root.cursorActive = true
                  root.focusSection = "textsize"
                  root.cardSubRow = 0
                  root.cardSubItem = 0
                }
              }
            }
          }

          // ---------- Displays Section ----------
          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(10)

            PanelSectionHeader {
              text: "DISPLAYS"
              foreground: root.bar.foreground
              fontFamily: root.bar.fontFamily
            }

            Repeater {
              model: root.displays

              DisplayCard {
                required property var modelData
                required property int index

                display: modelData
                cardIndex: index
              }
            }
          }

          Item {
            width: parent.width
            height: Style.space(4)
          }

          // ---------- Version Footer ----------
          Item {
            width: parent.width
            height: Style.space(22)

            Text {
              anchors.centerIn: parent
              textFormat: Text.PlainText
              text: "fred.monitor v" + root.pluginVersion
              color: root.bar ? root.bar.foreground : Color.foreground
              opacity: 0.45
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.caption
            }
          }
        }
      }
    }
  }

  // --- Display Card Component ---
  component DisplayCard: Rectangle {
    id: card
    required property var display
    required property int cardIndex

    readonly property bool isCardFocused: root.focusSection === ("card_" + display.name)
    readonly property bool isExpanded: root.expandedCard === display.name
    readonly property var subRows: root.cardSubRows(display)
    readonly property string currentSubRow: isCardFocused && root.cardSubRow < subRows.length ? subRows[root.cardSubRow] : ""
    readonly property var cardResetInfo: root.resetStatus[display.name]
    readonly property bool isResetting: root.resetRunningMonitor === display.name || (cardResetInfo && cardResetInfo.status === "running")
    readonly property string resetMsg: cardResetInfo ? cardResetInfo.message : ""
    readonly property string posLabel: Model.positionLabel(display.name, root.displays)
    readonly property var availableScalesList: Model.availableScales(root.scalePresets, display.width, display.height)
    readonly property int activeScaleIdx: Model.matchingScaleIndex(availableScalesList, display.scale, display.width, display.height)
    readonly property bool canToggle: display && (!display.enabled || root.enabledDisplayCount > 1)

    width: panelColumn.width
    radius: Style.radius.md
    color: isCardFocused
      ? Style.selectedFillFor(root.bar.foreground, Color.accent)
      : Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.04)
    border.color: isCardFocused
      ? Color.accent
      : Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.12)
    border.width: 1

    implicitHeight: cardInnerCol.implicitHeight + Style.space(16)

    Column {
      id: cardInnerCol
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.top: parent.top
      anchors.margins: Style.space(8)
      spacing: Style.space(8)

      // Header row
      Item {
        width: parent.width
        implicitHeight: Math.max(headerRow.implicitHeight, headerControls.implicitHeight)

        MouseArea {
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onEntered: if (!root.reflowingText) {
            root.cursorActive = true
            root.focusSection = "card_" + card.display.name
            root.cardSubRow = 0
            root.cardSubItem = 0
          }
          onClicked: root.toggleCardExpanded(card.display.name)
        }

        Row {
          id: headerRow
          anchors.left: parent.left
          anchors.right: headerControls.left
          anchors.rightMargin: Style.space(8)
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(8)

          Text {
            text: card.display.enabled ? "󰍹" : "󰍺"
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.title
            width: Style.space(20)
            horizontalAlignment: Text.AlignHCenter
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            textFormat: Text.PlainText
            text: card.display.name
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.body
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            visible: card.display.model || card.display.make
            textFormat: Text.PlainText
            text: card.display.model || card.display.make || ""
            color: Qt.darker(root.bar.foreground, 1.3)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            elide: Text.ElideRight
            width: Math.min(Style.space(100), implicitWidth)
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            visible: card.posLabel !== ""
            textFormat: Text.PlainText
            text: card.posLabel
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
          }

          Rectangle {
            visible: card.display.focused
            radius: Style.radius.sm
            color: Color.accent
            implicitWidth: focusedBadgeText.implicitWidth + Style.space(8)
            implicitHeight: focusedBadgeText.implicitHeight + Style.space(2)
            anchors.verticalCenter: parent.verticalCenter

            Text {
              id: focusedBadgeText
              anchors.centerIn: parent
              textFormat: Text.PlainText
              text: "focused"
              color: Color.accentText || "#ffffff"
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.caption * 0.9
              font.bold: true
            }
          }
        }

        Row {
          id: headerControls
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(6)

          Button {
            bordered: true
            active: card.display.enabled
            hasCursor: card.isCardFocused && card.currentSubRow === "header" && root.cardSubItem === 1
            iconText: card.display.enabled ? "󰄬" : ""
            text: card.display.enabled ? "" : "Off"
            fontSize: Style.font.caption
            horizontalPadding: Style.space(6)
            verticalPadding: Style.space(2)
            tooltipText: card.display.enabled
              ? (card.canToggle ? "Disable display" : "Cannot disable only active display")
              : "Enable display"
            opacity: (card.display.enabled && !card.canToggle) ? 0.4 : 1.0
            onClicked: if (card.canToggle) root.toggleDisplay(card.display.name, card.display.enabled)
            onHovered: function(h) {
              if (h && !root.reflowingText) {
                root.cursorActive = true
                root.focusSection = "card_" + card.display.name
                root.cardSubRow = 0
                root.cardSubItem = 1
              }
            }
          }

          Text {
            text: card.isExpanded ? "󰅀" : "󰅂"
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.body
            anchors.verticalCenter: parent.verticalCenter
          }
        }
      }

      // Facts row
      Text {
        visible: card.isExpanded
        width: parent.width
        textFormat: Text.PlainText
        text: Model.formatFacts(card.display)
        color: Qt.darker(root.bar.foreground, 1.4)
        font.family: root.bar.fontFamily
        font.pixelSize: Style.font.caption
        wrapMode: Text.Wrap
      }

      // Divider inside card
      PanelSeparator {
        visible: card.isExpanded && card.display.enabled
        foreground: root.bar.foreground
      }

      // Brightness slider (only if controllable)
      Column {
        visible: card.isExpanded && card.display.enabled && card.display.brightnessAvailable
        width: parent.width
        spacing: Style.space(4)

        Item {
          width: parent.width
          implicitHeight: Math.max(cardBrightnessHeader.implicitHeight, cardBrightnessVal.implicitHeight)

          PanelSectionHeader {
            id: cardBrightnessHeader
            text: "BRIGHTNESS"
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            id: cardBrightnessVal
            textFormat: Text.PlainText
            text: (cardBrightnessSlider.dragging ? Math.round(cardBrightnessSlider.liveValue) : (card.display.brightness || 0)) + "%"
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.bold: true
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
          }
        }

        CursorSurface {
          id: cardBrightnessRow
          width: parent.width
          height: cardBrightnessSlider.implicitHeight + Style.spacing.controlGap
          hasCursor: card.isCardFocused && card.currentSubRow === "brightness"
          onHasCursorChanged: if (hasCursor) root.ensureCursorVisible(card)
          foreground: root.bar.foreground
          outline: true

          PanelSlider {
            id: cardBrightnessSlider
            bar: root.bar
            anchors.fill: parent
            anchors.leftMargin: Style.space(4)
            anchors.rightMargin: Style.space(4)
            minimum: 1
            maximum: 100
            step: 1
            integer: true
            value: card.display.brightness !== undefined ? card.display.brightness : 50
            onMoved: function(v) { root.previewMonitorBrightness(card.display.name, v) }
            onReleased: function(v) { root.setMonitorBrightness(card.display.name, Math.round(v)) }
          }

          HoverHandler {
            onHoveredChanged: if (hovered && !root.reflowingText) {
              root.cursorActive = true
              root.focusSection = "card_" + card.display.name
              root.cardSubRow = card.subRows.indexOf("brightness")
              root.cardSubItem = 0
            }
          }
        }
      }

      // Scale presets
      Column {
        visible: card.isExpanded && card.display.enabled
        width: parent.width
        spacing: Style.space(4)

        PanelSectionHeader {
          text: "SCALE"
          foreground: root.bar.foreground
          fontFamily: root.bar.fontFamily
        }

        Grid {
          id: cardScaleGrid
          width: parent.width
          columns: card.availableScalesList.length
          spacing: Style.spacing.xs

          readonly property real cellWidth: card.availableScalesList.length > 0
            ? (width - spacing * (columns - 1)) / columns
            : 0

          Repeater {
            model: card.availableScalesList

            Button {
              required property string modelData
              required property int index

              width: cardScaleGrid.cellWidth
              text: root.effectiveScale(modelData) + "x"
              fontSize: Style.font.caption
              foreground: root.bar.foreground
              fontFamily: root.bar.fontFamily
              horizontalPadding: Style.spacing.xs
              verticalPadding: Style.spacing.controlPaddingY
              bordered: true
              active: card.activeScaleIdx === index
              hasCursor: card.isCardFocused && card.currentSubRow === "scale" && root.cardSubItem === index

              onClicked: root.setMonitorScale(card.display.name, modelData)
              onHovered: function(h) {
                if (h && !root.reflowingText) {
                  root.cursorActive = true
                  root.focusSection = "card_" + card.display.name
                  root.cardSubRow = card.subRows.indexOf("scale")
                  root.cardSubItem = index
                }
              }
            }
          }
        }
      }

      // Refresh rate chips
      Column {
        visible: card.isExpanded && card.display.enabled && card.display.availableRates && card.display.availableRates.length > 0
        width: parent.width
        spacing: Style.space(4)

        PanelSectionHeader {
          text: "REFRESH RATE"
          foreground: root.bar.foreground
          fontFamily: root.bar.fontFamily
        }

        Flow {
          width: parent.width
          spacing: Style.spacing.xs

          Repeater {
            model: card.display.availableRates || []

            Button {
              required property real modelData
              required property int index

              readonly property bool isCurrentRate: Math.abs(modelData - card.display.refreshRate) < 0.05
              text: (Math.round(modelData) === modelData ? modelData : modelData.toFixed(2)) + " Hz"
              fontSize: Style.font.caption
              foreground: root.bar.foreground
              fontFamily: root.bar.fontFamily
              horizontalPadding: Style.spacing.sm
              verticalPadding: Style.spacing.controlPaddingY
              bordered: true
              active: isCurrentRate
              hasCursor: card.isCardFocused && card.currentSubRow === "rate" && root.cardSubItem === index

              onClicked: root.setMonitorRefreshRate(card.display.name, modelData)
              onHovered: function(h) {
                if (h && !root.reflowingText) {
                  root.cursorActive = true
                  root.focusSection = "card_" + card.display.name
                  root.cardSubRow = card.subRows.indexOf("rate")
                  root.cardSubItem = index
                }
              }
            }
          }
        }
      }

      // Action row: DPMS and Reset
      Row {
        visible: card.isExpanded && card.display.enabled
        width: parent.width
        spacing: Style.space(8)

        // DPMS control
        Item {
          implicitWidth: dpmsBtn.implicitWidth
          implicitHeight: dpmsBtn.implicitHeight

          Button {
            id: dpmsBtn
            visible: root.dpmsSafetyMonitor !== card.display.name
            bordered: true
            fontSize: Style.font.caption
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            iconText: card.display.dpmsStatus ? "󰶐" : "󰶑"
            text: card.display.dpmsStatus ? "DPMS Off" : "DPMS On"
            hasCursor: card.isCardFocused && card.currentSubRow === "actions" && root.cardSubItem === 0
            tooltipText: card.display.dpmsStatus ? "Turn display off with 10s auto-on safety" : "Turn display on"

            onClicked: {
              if (card.display.dpmsStatus) {
                root.setDpmsOffWithSafety(card.display.name)
              } else {
                root.setDpmsOn(card.display.name)
              }
            }
            onHovered: function(h) {
              if (h && !root.reflowingText) {
                root.cursorActive = true
                root.focusSection = "card_" + card.display.name
                root.cardSubRow = card.subRows.indexOf("actions")
                root.cardSubItem = 0
              }
            }
          }

          Row {
            visible: root.dpmsSafetyMonitor === card.display.name
            spacing: Style.space(4)

            Button {
              bordered: true
              fontSize: Style.font.caption
              foreground: Color.accent
              text: "Restore (" + root.dpmsCountdown + "s)"
              hasCursor: card.isCardFocused && card.currentSubRow === "actions" && root.cardSubItem === 0
              onClicked: root.restoreDpms()
            }

            Button {
              bordered: true
              fontSize: Style.font.caption
              text: "Keep Off"
              onClicked: root.confirmDpmsOff()
            }
          }
        }

        Item {
          Layout.fillWidth: true
          width: Style.space(4)
        }

        // Reset button
        Button {
          id: cardResetBtn
          bordered: true
          fontSize: Style.font.caption
          foreground: root.bar.foreground
          fontFamily: root.bar.fontFamily
          horizontalPadding: Style.spacing.xs
          verticalPadding: Style.spacing.controlPaddingY
          hasCursor: card.isCardFocused && card.currentSubRow === "actions" && root.cardSubItem === 1
          onHasCursorChanged: if (hasCursor) root.ensureCursorVisible(card)

          iconSpinning: card.isResetting
          iconText: card.isResetting ? "󰑐" : (card.cardResetInfo && card.cardResetInfo.status === "success" ? "󰄬" : (card.cardResetInfo && card.cardResetInfo.status === "error" ? "󰅚" : ""))
          text: {
            if (card.isResetting) return "Retraining…"
            if (card.cardResetInfo && card.cardResetInfo.status === "success") return "Retrained"
            if (card.cardResetInfo && card.cardResetInfo.status === "error") return "Failed"
            return "Reset"
          }
          tooltipText: card.resetMsg !== "" ? card.resetMsg : "Retrain display link"

          onClicked: root.resetDisplay(card.display.name)
          onHovered: function(h) {
            if (h && !root.reflowingText) {
              root.cursorActive = true
              root.focusSection = "card_" + card.display.name
              root.cardSubRow = card.subRows.indexOf("actions")
              root.cardSubItem = 1
            }
          }
        }
      }
    }
  }
}
