import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Ui
import qs.Commons
import "Model.js" as Model

Panel {
  id: root
  moduleName: "omarchy.monitor"
  ipcTarget: "omarchy.monitor"
  manageIpc: false

  readonly property string pluginVersion: "1.2.3"
  readonly property var monitorEnv: ["HOME", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "HYPRLAND_INSTANCE_SIGNATURE", "DBUS_SESSION_BUS_ADDRESS", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"]

  property int brightnessPercent: 0
  property int pendingBrightnessPercent: 0
  property string pendingBrightnessMonitor: ""
  property bool brightnessAvailable: false
  property string focusedMonitor: ""
  property string monitorScale: ""
  property var displays: []
  property var draftDisplays: []
  property int enabledDisplayCount: 0
  property var displayCache: ({})
  property string expandedCard: ""
  property string layoutAlignment: "bottom"
  property string layoutToken: ""
  property int layoutCountdown: 0
  property string layoutMessage: ""
  property bool identifyVisible: false
  property bool helpVisible: false
  property bool cardDropdownOpen: false
  property var savedProfiles: []
  property string selectedProfileId: ""
  property bool profileNameVisible: false
  property string profileDeleteArmed: ""

  readonly property int cardGap: Style.space(10)
  readonly property int cardCount: Math.max(1, draftDisplays.length || displays.length)
  readonly property int enabledDraftCount: {
    var count = 0
    for (var i = 0; i < draftDisplays.length; i++) if (draftDisplays[i].enabled) count++
    return count
  }
  readonly property bool draftDirty: draftDisplays.length > 0
    && Model.layoutSignature(draftDisplays) !== Model.layoutSignature(displays)
  readonly property int draftDirtyCount: {
    var count = 0
    for (var i = 0; i < draftDisplays.length; i++) {
      var live = findDisplay(draftDisplays[i].name)
      if (!live || Model.layoutSignature([draftDisplays[i]]) !== Model.layoutSignature([live])) count++
    }
    return count
  }

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
  readonly property var alignmentOptions: [
    { value: "top", label: "Align: Top" },
    { value: "center", label: "Align: Center" },
    { value: "bottom", label: "Align: Bottom" }
  ]
  readonly property var orientationOptions: [
    { value: "0", label: "Landscape" },
    { value: "1", label: "Portrait" },
    { value: "2", label: "Flipped" },
    { value: "3", label: "Portrait flipped" }
  ]
  readonly property var keyboardShortcuts: [
    { keys: "Home", action: "Show or hide keyboard help" },
    { keys: "I", action: "Toggle monitor identification overlays" },
    { keys: "Arrow keys / H J K L", action: "Navigate or adjust the selected control" },
    { keys: "Enter / Space", action: "Activate the selected control" },
    { keys: "D", action: "Toggle DPMS for the selected monitor" },
    { keys: "R", action: "Reset / retrain the selected monitor" },
    { keys: "[ / ]", action: "Move the selected monitor left / right" },
    { keys: "A", action: "Apply staged display changes" },
    { keys: "Tab / Shift+Tab", action: "Switch between open panels" },
    { keys: "Esc / Q", action: "Close help, then close the panel" }
  ]

  // Text size slider — curated macOS-style notches (px)
  readonly property var textSizeStops: [9, 10, 11, 12, 14, 16, 20]
  property int textSizePreviewIndex: -1
  property bool reflowingText: false

  function markReflowing() {
    root.reflowingText = true
    reflowSettle.restart()
  }

  // Focus and keyboard navigation
  property string focusSection: ""
  property int cardSubRow: 0
  property int cardSubItem: 0
  property bool cursorActive: false

  readonly property var visibleSections: {
    var list = []
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

  function findDraftDisplay(name) {
    for (var i = 0; i < draftDisplays.length; i++) {
      if (draftDisplays[i] && draftDisplays[i].name === name) return draftDisplays[i]
    }
    return null
  }

  function monitorForButton() {
    var window = button && button.QsWindow ? button.QsWindow.window : null
    var name = window && window.screen ? window.screen.name : ""
    return findDisplay(name) || findDisplay(focusedMonitor) || (displays.length > 0 ? displays[0] : null)
  }

  function cloneDisplays(source) {
    return JSON.parse(JSON.stringify(source || []))
  }

  function resetDraft() {
    draftDisplays = cloneDisplays(Model.sortDisplays(displays))
    layoutMessage = ""
  }

  function layoutPayload() {
    return draftDisplays.map(function(display) {
      return {
        name: display.name,
        enabled: !!display.enabled,
        width: Number(display.width),
        height: Number(display.height),
        refreshRate: Number(display.refreshRate),
        x: Number(display.x),
        y: Number(display.y),
        scale: Number(display.scale),
        transform: Number(display.transform || 0)
      }
    })
  }

  function replaceDraft(name, changes, realign) {
    layoutMessage = ""
    var next = cloneDisplays(draftDisplays)
    for (var i = 0; i < next.length; i++) {
      if (next[i].name !== name) continue
      for (var key in changes) next[i][key] = changes[key]
      if (changes.scale !== undefined) {
        next[i].logicalWidth = Math.round(next[i].width / Number(changes.scale))
        next[i].logicalHeight = Math.round(next[i].height / Number(changes.scale))
      }
      break
    }
    draftDisplays = realign ? Model.alignDisplays(next, layoutAlignment) : Model.sortDisplays(next)
  }

  function setAlignment(alignment) {
    layoutMessage = ""
    layoutAlignment = alignment
    draftDisplays = Model.alignDisplays(draftDisplays, alignment)
  }

  function moveDraftDisplay(name, delta) {
    layoutMessage = ""
    draftDisplays = Model.moveDisplay(draftDisplays, name, delta, layoutAlignment)
  }

  function setMonitorMode(name, mode) {
    if (!mode || Number(mode.width) <= 0 || Number(mode.height) <= 0) return
    var draft = findDraftDisplay(name)
    if (!draft) return
    var rates = mode.rates || []
    var refresh = Number(draft.refreshRate)
    if (rates.length > 0 && rates.every(function(rate) { return Math.abs(Number(rate) - refresh) >= 0.05 })) {
      refresh = Number(rates[0])
    }
    replaceDraft(name, {
      width: Number(mode.width),
      height: Number(mode.height),
      refreshRate: refresh,
      availableRates: rates
    }, true)
  }

  function setMonitorModeValue(name, value) {
    var draft = findDraftDisplay(name)
    if (!draft) return
    var modes = draft.availableModes || []
    for (var i = 0; i < modes.length; i++) {
      var candidate = modes[i]
      if ((candidate.width + "x" + candidate.height) === value) {
        setMonitorMode(name, candidate)
        return
      }
    }
  }

  function profileOptions() {
    if (savedProfiles.length === 0) return [{ value: "", label: "No saved layouts yet" }]
    return savedProfiles.map(function(profile) {
      return { value: String(profile.id || ""), label: String(profile.name || "Saved layout") }
    })
  }

  function refreshProfiles() {
    if (!profileListProc.running) profileListProc.launch()
  }

  function saveNamedProfile(name) {
    var clean = String(name || "").trim()
    if (clean === "" || profileSaveProc.running || draftDirty || layoutToken !== "") return
    layoutMessage = "Saving layout…"
    profileSaveProc.args = [Model.helperPath("fred-monitor-layout"), "profile-save", clean]
    profileSaveProc.launch()
  }

  function restoreSelectedProfile() {
    if (selectedProfileId === "" || profileLoadProc.running || layoutToken !== "") return
    layoutMessage = "Loading saved layout…"
    profileLoadProc.args = [Model.helperPath("fred-monitor-layout"), "profile-load", selectedProfileId]
    profileLoadProc.launch()
  }

  function deleteSelectedProfile() {
    if (selectedProfileId.indexOf("user:") !== 0 || profileDeleteProc.running) return
    if (profileDeleteArmed !== selectedProfileId) {
      profileDeleteArmed = selectedProfileId
      layoutMessage = "Press Delete again to remove this saved layout"
      profileDeleteTimer.restart()
      return
    }
    profileDeleteTimer.stop()
    profileDeleteArmed = ""
    profileDeleteProc.args = [Model.helperPath("fred-monitor-layout"), "profile-delete", selectedProfileId]
    profileDeleteProc.launch()
  }

  function stageProfileLayout(layout) {
    if (!Array.isArray(layout)) {
      layoutMessage = "Saved layout is invalid"
      return
    }
    var byName = ({})
    for (var i = 0; i < layout.length; i++) byName[layout[i].name] = layout[i]
    if (layout.length !== displays.length) {
      layoutMessage = "Saved layout does not match the connected displays"
      return
    }
    var merged = cloneDisplays(displays)
    for (var j = 0; j < merged.length; j++) {
      var saved = byName[merged[j].name]
      if (!saved) {
        layoutMessage = "Saved layout does not match the connected displays"
        return
      }
      if (!saved.enabled) {
        layoutMessage = "Layouts that disable a display are deferred to a future version"
        return
      }
      merged[j].enabled = true
      merged[j].width = Number(saved.width)
      merged[j].height = Number(saved.height)
      merged[j].refreshRate = Number(saved.refreshRate)
      merged[j].x = Number(saved.x)
      merged[j].y = Number(saved.y)
      merged[j].scale = Number(saved.scale)
      merged[j].transform = Number(saved.transform || 0)
      merged[j].logicalWidth = Model.logicalWidth ? Model.logicalWidth(merged[j]) : Math.round(merged[j].width / merged[j].scale)
      merged[j].logicalHeight = Model.logicalHeight ? Model.logicalHeight(merged[j]) : Math.round(merged[j].height / merged[j].scale)
    }
    draftDisplays = Model.sortDisplays(merged)
    layoutMessage = "Saved layout loaded — review it, then Apply"
  }

  function setMonitorTransform(name, transform) {
    replaceDraft(name, { transform: Number(transform) }, true)
  }

  function toggleIdentify() {
    identifyVisible = !identifyVisible
  }

  function toggleHelp() {
    helpVisible = !helpVisible
  }

  function closeHelpOrPanel() {
    if (helpVisible) helpVisible = false
    else close()
  }

  function toggleHighlightedDpms() {
    var d = getTargetDisplay()
    if (!d || !d.name || !d.enabled) return
    if (root.dpmsSafetyMonitor === d.name) root.restoreDpms()
    else if (d.dpmsStatus) root.setDpmsOffWithSafety(d.name)
    else root.setDpmsOn(d.name)
  }

  function moveHighlighted(delta) {
    var d = getTargetDisplay()
    if (d && d.name && d.enabled) root.moveDraftDisplay(d.name, delta)
  }

  function handleShortcut(text) {
    if (text === "q" || text === "Q") root.closeHelpOrPanel()
    else if (text === "i" || text === "I") root.toggleIdentify()
    else if (text === "r" || text === "R") root.resetHighlighted()
    else if (text === "d" || text === "D") root.toggleHighlightedDpms()
    else if (text === "[") root.moveHighlighted(-1)
    else if (text === "]") root.moveHighlighted(1)
    else if (text === "a" || text === "A") root.applyDraft()
  }

  function applyDraft() {
    if (!draftDirty || layoutToken !== "" || layoutProc.running) return
    layoutMessage = "Applying preview…"
    layoutProc.stdinText = JSON.stringify(layoutPayload())
    layoutProc.args = [Model.helperPath("fred-monitor-layout"), "preview"]
    layoutProc.launch()
  }

  function keepLayout() {
    if (layoutToken === "" || layoutKeepProc.running) return
    layoutKeepProc.args = [Model.helperPath("fred-monitor-layout"), "keep", layoutToken]
    layoutKeepProc.launch()
  }

  function revertLayout() {
    if (layoutToken === "" || layoutRevertProc.running) return
    layoutRevertProc.args = [Model.helperPath("fred-monitor-layout"), "revert", layoutToken]
    layoutRevertProc.launch()
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
    if (display.enabled) {
      rows.push("scale")
      if (display.brightnessAvailable) rows.push("brightness")
      if (display.availableRates && display.availableRates.length > 0) rows.push("rate")
      rows.push("actions")
    }
    return rows
  }

  function moveCursor(delta) {
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
          }
        }
      }
    }
  }

  function moveCursorH(delta) {
    if (focusSection.indexOf("card_") === 0) {
      var name = focusSection.substring(5)
      var d = findDisplay(name)
      if (!d) return
      var subRows = cardSubRows(d)
      var rowName = cardSubRow < subRows.length ? subRows[cardSubRow] : "header"

      if (rowName === "header") {
        cardSubItem = 0
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
        cardSubItem = 0
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
        toggleCardExpanded(d.name)
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
        if (root.dpmsSafetyMonitor === d.name) restoreDpms()
        else if (d.dpmsStatus) setDpmsOffWithSafety(d.name)
        else setDpmsOn(d.name)
      }
    }
  }

  function toggleCardExpanded(name) {
    root.expandedCard = name
    root.focusSection = "card_" + name
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
    root.displays = Model.sortDisplays(state.displays)
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
    if (!root.draftDirty && root.layoutToken === "") {
      root.draftDisplays = root.cloneDisplays(root.displays)
    }
  }

  function updateHoverState(raw) {
    var state = Model.parseState(raw)
    var merged = []
    for (var i = 0; i < state.displays.length; i++) {
      var fresh = Object.assign({}, state.displays[i])
      var prior = root.findDisplay(fresh.name)
      if (prior) {
        fresh.brightness = prior.brightness
        fresh.brightnessAvailable = prior.brightnessAvailable
      }
      merged.push(fresh)
    }
    root.displays = Model.sortDisplays(merged)
    root.enabledDisplayCount = state.enabledDisplayCount
    if (state.focusedMonitor) root.focusedMonitor = state.focusedMonitor
    if (!root.draftDirty && root.layoutToken === "") root.draftDisplays = root.cloneDisplays(root.displays)
    Qt.callLater(function() {
      if (button.tooltipHovered && !root.opened && root.bar) root.bar.showTooltip(button, button.tooltipText)
    })
  }

  function effectiveScale(scale) {
    return Model.normalizeScale(scale)
  }

  function brightnessName(percent) {
    return Model.brightnessName(percent)
  }

  // --- Display Management Actions ---
  function setMonitorScale(name, scale) {
    if (!name || !Model.isValidOutputName(name)) return
    var d = findDraftDisplay(name)
    if (!d) return
    var clean = Model.cleanScale(scale, d.width, d.height)
    if (clean === "") clean = Model.normalizeScale(scale)
    if (clean === "") return

    replaceDraft(name, { scale: Number(clean) }, true)
  }

  function setMonitorRefreshRate(name, rate) {
    if (!name || !Model.isValidOutputName(name)) return
    var d = findDraftDisplay(name)
    if (!d) return
    var rateNum = Number(rate)
    if (!isFinite(rateNum) || rateNum <= 0) return

    replaceDraft(name, { refreshRate: rateNum }, false)
  }

  function setMonitorBrightness(monitorName, percent) {
    if (!monitorName || !Model.isValidOutputName(monitorName)) return
    var target = findDisplay(monitorName)
    if (!target || !target.brightnessAvailable) return
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
    var draftList = root.cloneDisplays(root.draftDisplays)
    for (var j = 0; j < draftList.length; j++) {
      if (draftList[j].name === monitorName) draftList[j].brightness = p
    }
    root.draftDisplays = draftList

    if (monitorName === root.focusedMonitor) {
      root.brightnessPercent = p
      root.pendingBrightnessPercent = p
    }

    root.pendingBrightnessMonitor = monitorName
    root.pendingBrightnessPercent = p
    brightnessDebounce.restart()
  }

  function flushMonitorBrightness() {
    if (root.pendingBrightnessMonitor === "") return
    if (setBrightnessProc.running) {
      brightnessDebounce.restart()
      return
    }
    var monitorName = root.pendingBrightnessMonitor
    var percent = root.pendingBrightnessPercent
    root.pendingBrightnessMonitor = ""
    setBrightnessProc.args = [Model.helperPath("fred-monitor-state"), "--set-brightness", monitorName, String(percent)]
    setBrightnessProc.launch()
  }

  function previewMonitorBrightness(monitorName, percent) {
    root.setMonitorBrightness(monitorName, percent)
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
    function identify() { root.toggleIdentify() }
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
      layoutStatusProc.launch()
      refreshProfiles()
      if (displays.length > 0) {
        var targetName = root.focusedMonitor || displays[0].name
        root.expandedCard = targetName
        root.focusSection = "card_" + targetName
        root.cardSubRow = 0
        root.cardSubItem = 0
      } else root.focusSection = ""
      cursorActive = false
    } else {
      root.helpVisible = false
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

  Timer {
    id: profileDeleteTimer
    interval: 4000
    onTriggered: root.profileDeleteArmed = ""
  }

  Timer {
    id: layoutCountdownTimer
    interval: 1000
    repeat: true
    running: root.layoutToken !== ""
    onTriggered: {
      root.layoutCountdown = Math.max(0, root.layoutCountdown - 1)
      if (root.layoutCountdown === 0) {
        root.layoutToken = ""
        root.layoutMessage = "Preview timed out — previous layout restored"
        root.draftDisplays = []
        root.refresh()
      }
    }
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

  Launch {
    id: hoverStateProc
    exe: "/usr/bin/python3"
    args: [Model.helperPath("fred-monitor-state"), "--fast"]
    envKeys: root.monitorEnv
    deadlineMs: 3000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.updateHoverState(String(text || "").trim())
    }
  }

  Launch {
    id: layoutProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 10000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          if (result.ok) {
            root.layoutToken = String(result.token || "")
            root.layoutCountdown = Number(result.seconds || 15)
            root.layoutMessage = "Preview applied"
          } else {
            root.layoutMessage = String(result.error || "Could not apply layout")
          }
        } catch (error) {
          root.layoutMessage = "Could not read layout helper response"
        }
        layoutProc.stdinText = ""
        root.refresh()
      }
    }
  }

  Launch {
    id: layoutKeepProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 8000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          if (!result.ok) {
            root.layoutMessage = String(result.error || "Could not save layout")
            return
          }
          root.layoutToken = ""
          root.layoutCountdown = 0
          root.layoutMessage = result.profileWarning
            ? "Layout saved; automatic recovery snapshot failed"
            : "Layout saved"
          root.displays = root.cloneDisplays(root.draftDisplays)
          root.refreshProfiles()
          root.refresh()
        } catch (error) {
          root.layoutMessage = "Could not read save response"
        }
      }
    }
  }

  Launch {
    id: layoutRevertProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 8000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          root.layoutMessage = result.ok ? "Previous layout restored" : String(result.error || "Could not restore layout")
          if (result.ok) {
            root.layoutToken = ""
            root.layoutCountdown = 0
            root.draftDisplays = []
            root.refresh()
          }
        } catch (error) {
          root.layoutMessage = "Could not read restore response"
        }
      }
    }
  }

  Launch {
    id: layoutStatusProc
    exe: "/usr/bin/python3"
    args: [Model.helperPath("fred-monitor-layout"), "status"]
    envKeys: root.monitorEnv
    deadlineMs: 4000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          if (result.ok && result.pending) {
            root.layoutToken = String(result.token || "")
            root.layoutCountdown = Number(result.seconds || 0)
            root.layoutMessage = "Preview applied"
          }
        } catch (error) {}
      }
    }
  }

  Launch {
    id: profileListProc
    exe: "/usr/bin/python3"
    args: [Model.helperPath("fred-monitor-layout"), "profile-list"]
    envKeys: root.monitorEnv
    deadlineMs: 4000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          root.savedProfiles = result.ok && Array.isArray(result.profiles) ? result.profiles : []
          var found = false
          for (var i = 0; i < root.savedProfiles.length; i++) {
            if (root.savedProfiles[i].id === root.selectedProfileId) found = true
          }
          if (!found) root.selectedProfileId = root.savedProfiles.length > 0 ? String(root.savedProfiles[0].id) : ""
        } catch (error) {
          root.savedProfiles = []
        }
      }
    }
  }

  Launch {
    id: profileSaveProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 6000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          if (!result.ok) {
            root.layoutMessage = String(result.error || "Could not save layout")
            return
          }
          root.profileNameVisible = false
          root.selectedProfileId = String(result.profile.id || "")
          root.layoutMessage = "Saved current layout as “" + String(result.profile.name || "Layout") + "”"
          root.refreshProfiles()
        } catch (error) {
          root.layoutMessage = "Could not read saved-layout response"
        }
      }
    }
  }

  Launch {
    id: profileLoadProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 5000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          if (result.ok) root.stageProfileLayout(result.layout)
          else root.layoutMessage = String(result.error || "Could not load saved layout")
        } catch (error) {
          root.layoutMessage = "Could not read saved-layout response"
        }
      }
    }
  }

  Launch {
    id: profileDeleteProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 5000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(String(text || "{}"))
          root.layoutMessage = result.ok ? "Saved layout deleted" : String(result.error || "Could not delete saved layout")
          if (result.ok) {
            root.selectedProfileId = ""
            root.refreshProfiles()
          }
        } catch (error) {
          root.layoutMessage = "Could not read saved-layout response"
        }
      }
    }
  }

  Timer {
    id: brightnessDebounce
    interval: 180
    repeat: false
    onTriggered: root.flushMonitorBrightness()
  }

  Launch {
    id: setBrightnessProc
    exe: "/usr/bin/python3"
    envKeys: root.monitorEnv
    deadlineMs: 15000
    stdout: StdioCollector { waitForEnd: true }
    onRunningChanged: if (!running && root.pendingBrightnessMonitor !== "") brightnessDebounce.restart()
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
    tooltipText: Model.formatHover(root.monitorForButton(), root.displays, root.pluginVersion)
    onTooltipHoveredChanged: {
      if (tooltipHovered && !root.opened && !hoverStateProc.running) hoverStateProc.launch()
    }
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

  Variants {
    model: root.identifyVisible ? Quickshell.screens : []

    delegate: Component {
      PanelWindow {
        required property var modelData
        readonly property var identifiedDisplay: root.findDisplay(modelData.name)
        screen: modelData
        visible: root.identifyVisible
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "fred-monitor-identify"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        anchors { top: true; bottom: true; left: true; right: true }
        mask: Region {}

        Rectangle {
          anchors.centerIn: parent
          width: Math.min(parent.width * 0.72, Style.space(420))
          height: Style.space(150)
          radius: Style.cornerRadius
          color: Qt.rgba(0.04, 0.04, 0.05, 0.92)
          border.color: Color.accent
          border.width: Style.space(2)

          Column {
            anchors.centerIn: parent
            width: parent.width - Style.space(24)
            spacing: Style.space(6)
            Text {
              width: parent.width
              horizontalAlignment: Text.AlignHCenter
              textFormat: Text.PlainText
              text: {
                var label = Model.positionLabel(identifiedDisplay ? identifiedDisplay.name : "", root.displays)
                return label ? label + " Monitor" : "Monitor"
              }
              color: "white"
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.display
              font.bold: true
            }
            Text {
              width: parent.width
              horizontalAlignment: Text.AlignHCenter
              textFormat: Text.PlainText
              text: identifiedDisplay ? (identifiedDisplay.name + " · " + Model.displayIdentity(identifiedDisplay)) : modelData.name
              color: "white"
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.title
              elide: Text.ElideRight
            }
          }
        }
      }
    }
  }

  // --- Main Panel Window ---
  MonitorPanelWindow {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    centerOnBar: true
    contentWidth: panel.fittedContentWidth(panel.availableCardWidth)
    contentHeight: panel.fittedContentHeight(panelColumn.implicitHeight, panel.availableCardHeight)

    Item {
      Shortcut {
        sequence: "Home"
        enabled: root.opened
        onActivated: root.toggleHelp()
      }
    }

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      blocked: root.cardDropdownOpen || profileNameField.activeFocus
        || alignmentDropdown.popupOpen || profileDropdown.popupOpen
      onMoveRequested: function(dx, dy) {
        if (!root.cursorActive) { root.cursorActive = true; return }
        if (dy !== 0) root.moveCursor(dy)
        else if (dx !== 0) root.moveCursorH(dx)
      }
      onActivateRequested: if (root.cursorActive) root.activateCursor()
      onCloseRequested: root.closeHelpOrPanel()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onTextKey: function(t) { root.handleShortcut(t) }

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

          // ---------- Header: title · layout controls · close ----------
          Item {
            width: parent.width
            implicitHeight: headerRow.implicitHeight

            RowLayout {
              id: headerRow
              anchors.fill: parent
              spacing: Style.space(8)

              Text {
                textFormat: Text.PlainText
                text: root.enabledDisplayCount > 1 ? "󰍺" : "󰍹"
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.display
                Layout.alignment: Qt.AlignVCenter
              }

              Text {
                textFormat: Text.PlainText
                text: "Display: " + Model.monitorCountLabel(root.enabledDisplayCount)
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
                elide: Text.ElideRight
                Layout.alignment: Qt.AlignVCenter
              }

              Button {
                id: identifyButton
                visible: root.enabledDisplayCount > 1
                bordered: true
                active: root.identifyVisible
                iconText: "󰍹"
                text: "Identify"
                fontSize: Style.font.caption
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.toggleIdentify()
              }

              Dropdown {
                id: alignmentDropdown
                Layout.preferredWidth: Style.space(150)
                Layout.alignment: Qt.AlignVCenter
                showLabel: false
                value: root.layoutAlignment
                options: root.alignmentOptions
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
                onChanged: function(newValue) { root.setAlignment(newValue) }
              }

              Button {
                visible: root.draftDirty && root.layoutToken === ""
                text: "Discard changes"
                bordered: true
                fontSize: Style.font.caption
                tooltipText: "Throw away staged monitor edits and reload the current live arrangement"
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.resetDraft()
              }

              Item { Layout.fillWidth: true }

              Button {
                text: "Home for help"
                tooltipText: "Show keyboard shortcuts"
                fontSize: Style.font.caption
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.toggleHelp()
              }

              Text {
                textFormat: Text.PlainText
                text: "Esc to close"
                color: Qt.darker(root.bar.foreground, 1.35)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                Layout.alignment: Qt.AlignVCenter
              }

              Button {
                bordered: true
                text: "×"
                tooltipText: "Close"
                fontSize: Style.font.body
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.close()
              }
            }
          }

          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(10)

            Column {
              width: parent.width
              spacing: Style.space(6)

              PanelSectionHeader {
                text: "SAVED LAYOUTS"
                foreground: root.bar.foreground
                fontFamily: root.bar.fontFamily
              }

              Row {
                width: parent.width
                spacing: Style.space(6)

                Dropdown {
                  id: profileDropdown
                  width: Math.min(Style.space(250), Math.max(Style.space(170), parent.width - profileButtons.width - Style.space(12)))
                  showLabel: false
                  value: root.selectedProfileId
                  options: root.profileOptions()
                  foreground: root.bar.foreground
                  fontFamily: root.bar.fontFamily
                  onChanged: function(newValue) {
                    root.selectedProfileId = newValue
                    root.profileDeleteArmed = ""
                  }
                }

                Row {
                  id: profileButtons
                  spacing: Style.space(6)

                  Button {
                    text: "Restore"
                    bordered: true
                    fontSize: Style.font.caption
                    enabled: root.selectedProfileId !== "" && root.layoutToken === ""
                    opacity: enabled ? 1 : 0.4
                    tooltipText: "Load into the cards for review; Apply is still required"
                    onClicked: root.restoreSelectedProfile()
                  }
                  Button {
                    text: "Save current"
                    bordered: true
                    fontSize: Style.font.caption
                    enabled: !root.draftDirty && root.layoutToken === ""
                    opacity: enabled ? 1 : 0.4
                    tooltipText: enabled ? "Save the verified live layout" : "Apply or discard pending changes first"
                    onClicked: {
                      root.profileNameVisible = !root.profileNameVisible
                      if (root.profileNameVisible) Qt.callLater(function() { profileNameField.forceActiveFocus() })
                    }
                  }
                  Button {
                    text: root.profileDeleteArmed === root.selectedProfileId ? "Delete?" : "Delete"
                    bordered: true
                    fontSize: Style.font.caption
                    enabled: root.selectedProfileId.indexOf("user:") === 0 && root.savedProfiles.length > 1
                    opacity: enabled ? 1 : 0.4
                    tooltipText: enabled
                      ? "Delete this named layout"
                      : (root.savedProfiles.length <= 1
                         ? "At least one restorable layout is always kept"
                         : "Automatic recovery layouts cannot be deleted")
                    onClicked: root.deleteSelectedProfile()
                  }
                }
              }

              Row {
                visible: root.profileNameVisible
                width: parent.width
                spacing: Style.space(6)

                TextField {
                  id: profileNameField
                  width: Math.min(Style.space(300), parent.width - saveProfileButton.width - Style.space(6))
                  placeholderText: "Layout name, e.g. Desk"
                  maximumLength: 40
                  foreground: root.bar.foreground
                  onAccepted: root.saveNamedProfile(text)
                }
                Button {
                  id: saveProfileButton
                  text: "Save"
                  bordered: true
                  active: profileNameField.text.trim() !== ""
                  fontSize: Style.font.caption
                  onClicked: root.saveNamedProfile(profileNameField.text)
                }
              }

              Text {
                width: parent.width
                textFormat: Text.PlainText
                text: "Restore only stages a saved arrangement. Apply previews it with the 15-second safety timer."
                color: Qt.darker(root.bar.foreground, 1.5)
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                wrapMode: Text.Wrap
              }
            }

            Row {
              id: displayRow
              width: parent.width
              spacing: root.cardGap

              Repeater {
                model: root.draftDisplays

                DisplayCard {
                  required property var modelData
                  required property int index

                  display: modelData
                  cardIndex: index
                  availableWidth: Math.max(1,
                    Math.floor((displayRow.width - root.cardGap * Math.max(0, root.cardCount - 1)) / root.cardCount))
                }
              }
            }
          }

          // ---------- Global Settings ----------
          PanelSeparator {
            foreground: root.bar.foreground
          }

          Column {
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              implicitHeight: Math.max(globalSettingsHeader.implicitHeight, textSizePx.implicitHeight)

              PanelSectionHeader {
                id: globalSettingsHeader
                text: "GLOBAL SETTINGS · ALL MONITORS"
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

            Text {
              width: parent.width
              textFormat: Text.PlainText
              text: "Text Size changes fonts in the Omarchy shell, GTK apps, and terminals everywhere. Per-monitor Scale changes the size of all content on that display and its usable workspace."
              color: Qt.darker(root.bar.foreground, 1.5)
              font.family: root.bar.fontFamily
              font.pixelSize: Style.font.caption
              wrapMode: Text.Wrap
            }

            CursorSurface {
              id: textSizeRow
              width: parent.width
              height: textSizeSlider.implicitHeight + Style.spacing.controlGap
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
            }
          }

          Rectangle {
            visible: root.draftDirty || root.layoutToken !== "" || root.layoutMessage !== ""
            width: parent.width
            implicitHeight: transactionRow.implicitHeight + Style.space(14)
            radius: Style.cornerRadius
            color: root.layoutToken !== "" ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.14) : Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.05)
            border.color: root.layoutToken !== "" ? Color.accent : Qt.rgba(root.bar.foreground.r, root.bar.foreground.g, root.bar.foreground.b, 0.12)
            border.width: 1

            Row {
              id: transactionRow
              anchors.centerIn: parent
              spacing: Style.space(8)
              Text {
                text: root.layoutToken !== "" ? ("Keep this layout? " + root.layoutCountdown + "s") : (root.layoutMessage || (root.draftDirtyCount + " display" + (root.draftDirtyCount === 1 ? "" : "s") + " changed"))
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.caption
                anchors.verticalCenter: parent.verticalCenter
              }
              Button {
                visible: root.layoutToken === ""
                text: "Apply"
                iconText: "󰄬"
                bordered: true
                active: root.draftDirty
                fontSize: Style.font.caption
                onClicked: root.applyDraft()
              }
              Button {
                visible: root.layoutToken !== ""
                text: "Keep"
                bordered: true
                active: true
                fontSize: Style.font.caption
                onClicked: root.keepLayout()
              }
              Button {
                visible: root.layoutToken !== ""
                text: "Revert"
                bordered: true
                fontSize: Style.font.caption
                onClicked: root.revertLayout()
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

      Rectangle {
        id: helpOverlay
        anchors.fill: parent
        visible: root.helpVisible
        z: 100
        color: Qt.rgba(0, 0, 0, 0.62)

        MouseArea {
          anchors.fill: parent
          onClicked: root.helpVisible = false
        }

        Rectangle {
          anchors.centerIn: parent
          width: Math.min(parent.width - Style.space(24), Style.space(620))
          height: helpColumn.implicitHeight + Style.space(24)
          radius: Style.cornerRadius
          color: Color.popups.background
          border.color: Color.popups.border
          border.width: Math.max(1, Style.normalBorderWidth)

          MouseArea {
            anchors.fill: parent
            onClicked: function(mouse) { mouse.accepted = true }
          }

          Column {
            id: helpColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Style.space(12)
            spacing: Style.space(8)

            RowLayout {
              width: parent.width

              Text {
                text: "Keyboard shortcuts"
                color: root.bar.foreground
                font.family: root.bar.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
                Layout.fillWidth: true
              }

              Button {
                text: "×"
                bordered: true
                tooltipText: "Close help"
                onClicked: root.helpVisible = false
              }
            }

            PanelSeparator {
              foreground: root.bar.foreground
            }

            Repeater {
              model: root.keyboardShortcuts

              Item {
                required property var modelData
                width: helpColumn.width
                implicitHeight: Math.max(helpKeys.implicitHeight, helpAction.implicitHeight)

                Text {
                  id: helpKeys
                  width: Style.space(165)
                  textFormat: Text.PlainText
                  text: modelData.keys
                  color: Color.accent
                  font.family: root.bar.fontFamily
                  font.pixelSize: Style.font.body
                  font.bold: true
                }

                Text {
                  id: helpAction
                  anchors.left: helpKeys.right
                  anchors.right: parent.right
                  textFormat: Text.PlainText
                  text: modelData.action
                  color: root.bar.foreground
                  font.family: root.bar.fontFamily
                  font.pixelSize: Style.font.body
                  wrapMode: Text.Wrap
                }
              }
            }

            Text {
              width: parent.width
              horizontalAlignment: Text.AlignHCenter
              text: "Press Home, Esc, or Q to close help"
              color: Qt.darker(root.bar.foreground, 1.35)
              font.family: root.bar.fontFamily
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
    required property real availableWidth

    readonly property bool isCardFocused: root.focusSection === ("card_" + display.name)
    readonly property bool isExpanded: true
    readonly property var subRows: root.cardSubRows(display)
    readonly property string currentSubRow: isCardFocused && root.cardSubRow < subRows.length ? subRows[root.cardSubRow] : ""
    readonly property var cardResetInfo: root.resetStatus[display.name]
    readonly property bool isResetting: root.resetRunningMonitor === display.name || (!!cardResetInfo && cardResetInfo.status === "running")
    readonly property string resetMsg: cardResetInfo ? cardResetInfo.message : ""
    readonly property string posLabel: Model.positionLabel(display.name, root.draftDisplays)
    readonly property var availableScalesList: Model.availableScales(root.scalePresets, display.width, display.height)
    readonly property int activeScaleIdx: Model.matchingScaleIndex(availableScalesList, display.scale, display.width, display.height)
    readonly property var resolutionOptions: (display.availableModes || []).map(function(mode) {
      return { value: mode.width + "x" + mode.height, label: mode.width + " × " + mode.height }
    })

    width: availableWidth
    radius: Style.cornerRadius
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
        implicitHeight: headerRow.implicitHeight

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

        RowLayout {
          id: headerRow
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(5)

          Text {
            text: card.display.enabled ? "󰍹" : "󰍺"
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.title
            Layout.preferredWidth: Style.space(20)
            horizontalAlignment: Text.AlignHCenter
            Layout.alignment: Qt.AlignVCenter
          }

          Text {
            textFormat: Text.PlainText
            text: card.display.name
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.body
            font.bold: true
            Layout.alignment: Qt.AlignVCenter
          }

          Text {
            textFormat: Text.PlainText
            text: Model.cardIdentity(card.display)
            color: Qt.darker(root.bar.foreground, 1.3)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            elide: Text.ElideRight
            Layout.fillWidth: true
            Layout.minimumWidth: Style.space(54)
            Layout.alignment: Qt.AlignVCenter
          }

          Text {
            visible: card.posLabel !== ""
            textFormat: Text.PlainText
            text: card.posLabel
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.bold: true
            Layout.alignment: Qt.AlignVCenter
          }

          Button {
            visible: card.display.enabled
            text: "←"
            bordered: true
            fontSize: Style.font.caption
            horizontalPadding: Style.spacing.xs
            tooltipText: "Move " + card.display.name + " left"
            enabled: card.cardIndex > 0
            opacity: enabled ? 1 : 0.4
            Layout.alignment: Qt.AlignVCenter
            onClicked: root.moveDraftDisplay(card.display.name, -1)
          }

          Button {
            visible: card.display.enabled
            text: "→"
            bordered: true
            fontSize: Style.font.caption
            horizontalPadding: Style.spacing.xs
            tooltipText: "Move " + card.display.name + " right"
            enabled: card.cardIndex < root.enabledDraftCount - 1
            opacity: enabled ? 1 : 0.4
            Layout.alignment: Qt.AlignVCenter
            onClicked: root.moveDraftDisplay(card.display.name, 1)
          }

          Rectangle {
            visible: card.display.focused
            radius: Math.max(2, Style.cornerRadius / 2)
            color: Color.accent
            implicitWidth: focusedBadgeText.implicitWidth + Style.space(8)
            implicitHeight: focusedBadgeText.implicitHeight + Style.space(2)
            Layout.alignment: Qt.AlignVCenter

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

          Button {
            id: cardResetBtn
            visible: card.display.enabled
            bordered: true
            fontSize: Style.font.caption
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            horizontalPadding: Style.spacing.xs
            verticalPadding: Style.spacing.controlPaddingY
            Layout.alignment: Qt.AlignVCenter

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

      // Resolution and orientation pickers
      Row {
        visible: card.isExpanded && card.display.enabled && card.display.availableModes && card.display.availableModes.length > 0
        width: parent.width
        spacing: Style.space(8)

        Column {
          width: (parent.width - parent.spacing) / 2
          spacing: Style.space(4)

          PanelSectionHeader {
            text: "RESOLUTION"
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
          }

          Dropdown {
            id: resolutionDropdown
            width: parent.width
            showLabel: false
            value: card.display.width + "x" + card.display.height
            options: card.resolutionOptions
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            onPopupOpenChanged: root.cardDropdownOpen = popupOpen
            onChanged: function(newValue) { root.setMonitorModeValue(card.display.name, newValue) }
          }
        }

        Column {
          width: (parent.width - parent.spacing) / 2
          spacing: Style.space(4)

          PanelSectionHeader {
            text: "ORIENTATION"
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
          }

          Dropdown {
            id: orientationDropdown
            width: parent.width
            showLabel: false
            value: String(card.display.transform || 0)
            options: root.orientationOptions
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            onPopupOpenChanged: root.cardDropdownOpen = popupOpen
            onChanged: function(newValue) { root.setMonitorTransform(card.display.name, Number(newValue)) }
          }
        }
      }

      // Per-output scale
      Column {
        visible: card.isExpanded && card.display.enabled
        width: parent.width
        spacing: Style.space(4)

        Item {
          width: parent.width
          implicitHeight: Math.max(cardScaleHeader.implicitHeight, cardScaleValue.implicitHeight)

          PanelSectionHeader {
            id: cardScaleHeader
            text: "SCALE"
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            id: cardScaleValue
            textFormat: Text.PlainText
            text: {
              var idx = cardScaleSlider.dragging ? Math.round(cardScaleSlider.liveValue) : card.activeScaleIdx
              if (idx < 0 || idx >= card.availableScalesList.length) return root.effectiveScale(card.display.scale) + "×"
              return root.effectiveScale(card.availableScalesList[idx]) + "×"
            }
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.bold: true
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
          }
        }

        Text {
          width: parent.width
          textFormat: Text.PlainText
          text: "Sizes everything on this display and changes its usable workspace."
          color: Qt.darker(root.bar.foreground, 1.5)
          font.family: root.bar.fontFamily
          font.pixelSize: Style.font.caption
          wrapMode: Text.Wrap
        }

        CursorSurface {
          id: cardScaleRow
          width: parent.width
          height: cardScaleSlider.implicitHeight + Style.spacing.controlGap
          hasCursor: card.isCardFocused && card.currentSubRow === "scale"
          onHasCursorChanged: if (hasCursor) root.ensureCursorVisible(card)
          foreground: root.bar.foreground
          outline: true

          PanelSlider {
            id: cardScaleSlider
            bar: root.bar
            anchors.fill: parent
            anchors.leftMargin: Style.space(4)
            anchors.rightMargin: Style.space(4)
            minimum: 0
            maximum: Math.max(0, card.availableScalesList.length - 1)
            step: 1
            integer: true
            tickCount: card.availableScalesList.length
            value: Math.max(0, card.activeScaleIdx)
            onMoved: function(v) { root.cardSubItem = Math.round(v) }
            onReleased: function(v) {
              var idx = Math.round(v)
              if (idx >= 0 && idx < card.availableScalesList.length)
                root.setMonitorScale(card.display.name, card.availableScalesList[idx])
            }
          }

          HoverHandler {
            onHoveredChanged: if (hovered && !root.reflowingText) {
              root.cursorActive = true
              root.focusSection = "card_" + card.display.name
              root.cardSubRow = card.subRows.indexOf("scale")
              root.cardSubItem = Math.max(0, card.activeScaleIdx)
            }
          }
        }
      }

      // Brightness follows Scale so the two per-display sliders stay together.
      Column {
        visible: card.isExpanded && card.display.enabled
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
            opacity: card.display.brightnessAvailable ? 1 : 0.45
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
          }

          Text {
            id: cardBrightnessVal
            textFormat: Text.PlainText
            text: card.display.brightnessAvailable
              ? ((cardBrightnessSlider.dragging ? Math.round(cardBrightnessSlider.liveValue) : (card.display.brightness || 0)) + "%")
              : "Unavailable"
            color: Qt.darker(root.bar.foreground, 1.4)
            opacity: card.display.brightnessAvailable ? 1 : 0.55
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
          enabled: card.display.brightnessAvailable
          opacity: enabled ? 1 : 0.32
          hasCursor: enabled && card.isCardFocused && card.currentSubRow === "brightness"
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
            enabled: card.display.brightnessAvailable
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

        Text {
          visible: !card.display.brightnessAvailable
          width: parent.width
          textFormat: Text.PlainText
          text: "Brightness control is not available for this monitor."
          color: Qt.darker(root.bar.foreground, 1.5)
          font.family: root.bar.fontFamily
          font.pixelSize: Style.font.caption
          wrapMode: Text.Wrap
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

      // DPMS is an immediate, stateful control. Reset lives in the card header.
      Column {
        visible: card.isExpanded && card.display.enabled
        width: parent.width
        spacing: Style.space(4)

        RowLayout {
          width: parent.width
          spacing: Style.space(6)

          PanelSectionHeader {
            text: "DPMS"
            foreground: root.bar.foreground
            fontFamily: root.bar.fontFamily
          }

          Item {
            Layout.fillWidth: true
          }

          Text {
            text: card.display.dpmsStatus ? "On" : "Off"
            color: card.display.dpmsStatus ? Color.accent : Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.bold: true
            Layout.alignment: Qt.AlignVCenter
          }

          ToggleSwitch {
            id: dpmsToggle
            checked: card.display.dpmsStatus
            busy: actionProc.running
            hasCursor: card.isCardFocused && card.currentSubRow === "actions"
            foreground: root.bar.foreground
            accent: Color.accent
            Layout.alignment: Qt.AlignVCenter
            onToggled: {
              if (card.display.dpmsStatus) root.setDpmsOffWithSafety(card.display.name)
              else root.setDpmsOn(card.display.name)
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
        }

        Row {
          visible: root.dpmsSafetyMonitor === card.display.name
          spacing: Style.space(4)
          anchors.horizontalCenter: parent.horizontalCenter

          Button {
            bordered: true
            fontSize: Style.font.caption
            foreground: Color.accent
            text: "Restore (" + root.dpmsCountdown + "s)"
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
    }
  }
}
