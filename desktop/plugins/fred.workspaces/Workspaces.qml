import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "fred.workspaces"

  property string desktopMode: "mac"
  property string leftMonitor: ""
  property string rightMonitor: ""
  property var monitorNames: []
  property var topologyMonitors: []
  property int topologySize: 3
  property var monitorSlots: ({})
  property bool degradedMode: false
  property int monitorCount: 1

  readonly property string modePath: {
    var stateHome = Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
    return stateHome + "/omarchy/desktop-mode"
  }
  readonly property string monitorsPath: {
    var stateHome = Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
    return stateHome + "/omarchy/desktop-monitors"
  }
  readonly property string canonicalHelperPath: {
    var resolved = String(Qt.resolvedUrl("omarchy-desktop-mode"))
    if (resolved.indexOf("file://") === 0) {
      return decodeURIComponent(resolved.substring(7))
    }
    return Quickshell.env("HOME") + "/.config/omarchy/plugins/fred.workspaces/omarchy-desktop-mode"
  }
  readonly property var processEnv: {
    var env = {
      "PATH": "/usr/bin:/bin",
      "HOME": Quickshell.env("HOME") || "",
      "LC_ALL": "C.UTF-8"
    }
    var xdgState = Quickshell.env("XDG_STATE_HOME")
    if (xdgState) env["XDG_STATE_HOME"] = xdgState
    var xdgConfig = Quickshell.env("XDG_CONFIG_HOME")
    if (xdgConfig) env["XDG_CONFIG_HOME"] = xdgConfig
    var xdgRuntime = Quickshell.env("XDG_RUNTIME_DIR")
    if (xdgRuntime) env["XDG_RUNTIME_DIR"] = xdgRuntime
    var sig = Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE")
    if (sig) env["HYPRLAND_INSTANCE_SIGNATURE"] = sig
    return env
  }

  readonly property var barMonitor: root.QsWindow && root.QsWindow.window
    ? Hyprland.monitorFor(root.QsWindow.window.screen)
    : null

  function workspaceById(id) {
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      if (values[i].id === id) return values[i]
    }
    return null
  }

  function quickshellMonitorNames() {
    var records = []
    var monitors = Hyprland.monitors.values
    for (var i = 0; i < monitors.length && records.length < 16; i++) {
      var monitor = monitors[i]
      var name = monitor && monitor.name ? String(monitor.name) : ""
      if (!/^[A-Za-z0-9._-]{1,64}$/.test(name)) continue
      var geometry = monitor.screen && monitor.screen.geometry ? monitor.screen.geometry : null
      var xVal = geometry ? geometry.x : (typeof monitor.x === "number" ? monitor.x : 0)
      var yVal = geometry ? geometry.y : (typeof monitor.y === "number" ? monitor.y : 0)
      records.push({
        "name": name,
        "x": xVal,
        "y": yVal
      })
    }
    records.sort(function(a, b) {
      if (a.x !== b.x) return a.x - b.x
      if (a.y !== b.y) return a.y - b.y
      return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0)
    })
    var names = []
    for (var j = 0; j < records.length; j++) names.push(records[j].name)
    return names
  }

  function effectiveMonitorNames() {
    if (monitorNames && monitorNames.length > 0) return monitorNames
    return quickshellMonitorNames()
  }

  function effectiveSetSize() {
    return Math.max(1, root.topologySize)
  }

  function slotForMonitor(name, index) {
    if (root.monitorSlots && typeof root.monitorSlots[name] === "number") {
      return root.monitorSlots[name]
    }
    if (root.topologyMonitors && root.topologyMonitors.length > 0) {
      var idx = root.topologyMonitors.indexOf(name)
      if (idx !== -1) return idx
    }
    return index
  }

  function windowsWorkspaceId(displayId, slot) {
    return (displayId - 1) * effectiveSetSize() + slot + 1
  }

  function windowsDisplayId(workspaceId) {
    return Math.floor((workspaceId - 1) / effectiveSetSize()) + 1
  }

  function monitorByName(name) {
    var monitors = Hyprland.monitors.values
    for (var i = 0; i < monitors.length; i++) {
      if (monitors[i].name === name) return monitors[i]
    }
    return null
  }

  function monitorRole(index, count, name) {
    if (count === 1) return "Display"
    if (count === 2) return index === 0 ? "Left" : "Right"
    if (count === 3) return index === 0 ? "Left" : (index === 1 ? "Center" : "Right")
    return name || ("Display " + String(index + 1))
  }

  function isLeftMonitor() {
    if (barMonitor === null) return true
    if (leftMonitor !== "") return barMonitor.name === leftMonitor
    if (Hyprland.monitors.values.length <= 1) return true

    var monitors = Hyprland.monitors.values
    if (monitors.length > 0) {
      var firstMon = monitors[0]
      for (var i = 1; i < monitors.length; i++) {
        var m = monitors[i]
        var mX = (m.screen && m.screen.geometry) ? m.screen.geometry.x : (typeof m.x === "number" ? m.x : 0)
        var firstX = (firstMon.screen && firstMon.screen.geometry) ? firstMon.screen.geometry.x : (typeof firstMon.x === "number" ? firstMon.x : 0)
        if (mX < firstX) firstMon = m
      }
      return barMonitor.name === firstMon.name
    }
    return true
  }

  function workspaceIds() {
    var _rev = root.windowsRevision
    if (desktopMode === "mac" && barMonitor !== null) {
      if (effectiveSetSize() === 1) {
        return [1, 2, 3, 4, 5]
      }
      return isLeftMonitor()
        ? [1, 3, 5, 7, 9]
        : [2, 4, 6, 8, 10]
    }

    if (desktopMode === "omarchy") return [1, 2, 3, 4, 5]

    var ids = [1, 2, 3, 4, 5]
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      var id = values[i].id
      var displayId = desktopMode === "windows" ? windowsDisplayId(id) : id
      var maximum = 10
      if (displayId > 0 && displayId <= maximum && ids.indexOf(displayId) === -1) ids.push(displayId)
    }
    ids.sort(function(left, right) { return left - right })
    return ids
  }

  property int windowsRevision: 0

  // Windows mode: what to do when the monitors stop showing one desktop as a
  // set (an app landing on a hidden workspace, a window switcher, a
  // single-monitor dispatch). "partial" marks the focused monitor's desktop
  // with a hollow indicator until a bar click or SUPER+N realigns the set;
  // "follow" realigns the set to the focused monitor's desktop automatically.
  //   omarchy bar set fred.workspaces splitSet follow|partial
  readonly property string splitSetMode: {
    var raw = String(root.setting("splitSet", "partial") || "").toLowerCase()
    return raw === "follow" ? "follow" : "partial"
  }

  // Last desktop the whole set showed together; where a click on "P" returns.
  property int lastAlignedDesktop: 0

  function trackAlignment() {
    var state = setState()
    if (state.aligned > 0) root.lastAlignedDesktop = state.aligned
  }

  // Windows-mode set state: { split, focused, aligned }.
  //   split   - monitors are not showing one desktop as a set
  //   focused - desktop on the focused monitor (0 if unknown)
  //   aligned - the common desktop when not split, else 0
  function setState() {
    var _rev = root.windowsRevision
    var none = { "split": false, "focused": 0, "aligned": 0 }
    if (desktopMode !== "windows") return none
    var names = effectiveMonitorNames()
    if (names.length < 2) return none
    var focusedName = Hyprland.focusedMonitor && Hyprland.focusedMonitor.name
      ? String(Hyprland.focusedMonitor.name) : ""
    var focusedDesktop = 0
    var common = 0
    var split = false
    for (var i = 0; i < names.length; i++) {
      var monitor = monitorByName(names[i])
      if (monitor === null || monitor.activeWorkspace === null) continue
      var ws = monitor.activeWorkspace.id
      if (ws < 1) continue
      var desktop = windowsDisplayId(ws)
      if (ws !== windowsWorkspaceId(desktop, slotForMonitor(names[i], i))) split = true
      if (common === 0) common = desktop
      else if (desktop !== common) split = true
      if (names[i] === focusedName) focusedDesktop = desktop
    }
    return { "split": split, "focused": focusedDesktop, "aligned": split ? 0 : common }
  }

  // Desktop shown on the focused monitor when the set is split, else 0.
  function splitDesktop() {
    var state = setState()
    if (!state.split) return 0
    return state.focused > 0 ? state.focused : 1
  }

  readonly property bool splitSet: splitDesktop() !== 0

  Component.onCompleted: Qt.callLater(root.trackAlignment)

  // Return the set to the desktop it showed before the split.
  function realignSet() {
    var target = root.lastAlignedDesktop > 0 ? root.lastAlignedDesktop : splitDesktop()
    if (target >= 1 && target <= 10) runDesktopCommand(["switch", String(target)])
  }

  function splitDetail() {
    var names = effectiveMonitorNames()
    var parts = []
    for (var i = 0; i < names.length; i++) {
      var monitor = monitorByName(names[i])
      if (monitor === null || monitor.activeWorkspace === null) continue
      var slot = slotForMonitor(names[i], i)
      parts.push(monitorRole(slot, effectiveSetSize(), names[i]) + " on desktop "
        + windowsDisplayId(monitor.activeWorkspace.id))
    }
    return parts.join(", ")
  }

  Connections {
    target: Hyprland
    // rawEvent carries a HyprlandIpcEvent (name + data), not the raw line.
    function onRawEvent(event) {
      root.windowsRevision++
      Qt.callLater(root.trackAlignment)
      var name = event && event.name ? String(event.name) : ""
      if (name === "monitoradded" || name === "monitorremoved"
          || name === "monitoraddedv2" || name === "monitorremovedv2") {
        reconcileDebounce.restart()
      } else if (name === "workspace" || name === "workspacev2" || name === "focusedmon"
          || name === "focusedmonv2") {
        followDebounce.restart()
      }
    }
  }

  // Follow-focus realignment. Only the bar on the focused monitor acts, so
  // three bars do not launch three concurrent switches; the debounce lets a
  // helper-driven batch switch settle before the set is judged split.
  Timer {
    id: followDebounce
    interval: 300
    repeat: false
    onTriggered: {
      if (root.splitSetMode !== "follow" || root.desktopMode !== "windows") return
      if (barMonitor === null || Hyprland.focusedMonitor === null
          || barMonitor.name !== Hyprland.focusedMonitor.name) return
      var desktop = root.splitDesktop()
      if (desktop >= 1 && desktop <= 10) root.runDesktopCommand(["switch", String(desktop)])
    }
  }

  Timer {
    id: reconcileDebounce
    interval: 350
    repeat: false
    onTriggered: {
      root.runDesktopCommand(["reconcile"])
    }
  }

  function formatToplevel(t) {
    if (!t) return ""
    var app = ""
    if (t.wayland && t.wayland.appId) {
      app = t.wayland.appId
    } else if (t.lastIpcObject && t.lastIpcObject["class"]) {
      app = t.lastIpcObject["class"]
    } else if (t.lastIpcObject && t.lastIpcObject.initialClass) {
      app = t.lastIpcObject.initialClass
    }

    var title = t.title || (t.wayland ? t.wayland.title : "") || (t.lastIpcObject ? t.lastIpcObject.title : "") || ""

    var cleanApp = app
    if (cleanApp) {
      if (cleanApp.indexOf("youtube") !== -1) {
        cleanApp = "YouTube"
      } else if (cleanApp.toLowerCase() === "google-chrome") {
        cleanApp = "Chrome"
      } else if (cleanApp.toLowerCase() === "org.mozilla.firefox") {
        cleanApp = "Firefox"
      } else if (cleanApp.toLowerCase() === "code") {
        cleanApp = "VS Code"
      } else {
        cleanApp = cleanApp.charAt(0).toUpperCase() + cleanApp.slice(1)
      }
    }

    if (title && cleanApp) {
      var suffix = " - " + cleanApp
      if (title.endsWith(suffix)) {
        title = title.substring(0, title.length - suffix.length)
      }
    }

    var maxLen = 40
    if (title.length > maxLen) {
      title = title.substring(0, maxLen - 3) + "..."
    }

    if (cleanApp && title && title.toLowerCase() !== cleanApp.toLowerCase()) {
      return cleanApp + ": " + title
    }
    return title || cleanApp || "Window"
  }

  function workspaceWindowSummaries(workspaceId) {
    try {
      var ws = workspaceById(workspaceId)
      if (!ws || !ws.toplevels || !ws.toplevels.values) return []
      var list = []
      var toplevels = ws.toplevels.values
      for (var i = 0; i < toplevels.length; i++) {
        var summary = formatToplevel(toplevels[i])
        if (summary && list.indexOf(summary) === -1) {
          list.push(summary)
        }
      }
      return list
    } catch (err) {
      return []
    }
  }

  function workspaceTooltip(displayId) {
    try {
      var _rev = root.windowsRevision
      var isFocused = workspaceFocused(displayId)
      var headerSuffix = isFocused ? " (Current)" : ""
      if (!isFocused && desktopMode === "windows" && splitDesktop() === displayId) {
        headerSuffix = " (Partial — focused monitor only; click to bring the set here)"
      }

      if (desktopMode === "windows") {
        var names = effectiveMonitorNames()
        var setSize = effectiveSetSize()
        var lines = ["Desktop " + displayId + headerSuffix]
        var totalWindows = 0
        var maxLines = 24

        for (var position = 0; position < names.length && lines.length < maxLines; position++) {
          var monName = names[position]
          var slot = slotForMonitor(monName, position)
          var wsId = windowsWorkspaceId(displayId, slot)
          var windows = workspaceWindowSummaries(wsId)
          totalWindows += windows.length
          var role = monitorRole(slot, setSize, monName || "")
          for (var w = 0; w < Math.min(windows.length, 3) && lines.length < maxLines; w++) {
            lines.push("[" + role + "] " + windows[w])
          }
          if (windows.length > 3 && lines.length < maxLines) {
            lines.push("[" + role + "] +" + (windows.length - 3) + " more")
          }
        }

        for (var s = 0; s < setSize && lines.length < maxLines; s++) {
          var topoName = (root.topologyMonitors && root.topologyMonitors[s]) || ""
          if (topoName && names.indexOf(topoName) === -1) {
            var parkedWsId = windowsWorkspaceId(displayId, s)
            var parkedWindows = workspaceWindowSummaries(parkedWsId)
            if (parkedWindows.length > 0) {
              totalWindows += parkedWindows.length
              var pRole = monitorRole(s, setSize, topoName) + " (Offline)"
              for (var pw = 0; pw < Math.min(parkedWindows.length, 3) && lines.length < maxLines; pw++) {
                lines.push("[" + pRole + "] " + parkedWindows[pw])
              }
              if (parkedWindows.length > 3 && lines.length < maxLines) {
                lines.push("[" + pRole + "] +" + (parkedWindows.length - 3) + " more")
              }
            }
          }
        }

        if (totalWindows === 0) {
          return "Desktop " + displayId + headerSuffix + "\n(Empty)"
        }
        return lines.join("\n")
      }

      if (desktopMode === "mac") {
        var leftName = leftMonitor || "Left"
        var rightName = rightMonitor || "Right"
        var monitorName = (displayId % 2 === 1) ? leftName : rightName
        if (effectiveSetSize() === 1 || leftName === rightName) {
          monitorName = leftName
        }

        var macWindows = workspaceWindowSummaries(displayId)
        if (macWindows.length === 0) {
          return "Workspace " + displayId + " (" + monitorName + ")" + headerSuffix + "\n(Empty)"
        }
        var macLines = ["Workspace " + displayId + " (" + monitorName + ")" + headerSuffix]
        for (var m = 0; m < Math.min(macWindows.length, 6); m++) {
          macLines.push(macWindows[m])
        }
        if (macWindows.length > 6) {
          macLines.push("+" + (macWindows.length - 6) + " more")
        }
        return macLines.join("\n")
      }

      var omarchyWindows = workspaceWindowSummaries(displayId)
      if (omarchyWindows.length === 0) {
        return "Workspace " + displayId + headerSuffix + "\n(Empty)"
      }
      var oLines = ["Workspace " + displayId + headerSuffix]
      for (var o = 0; o < Math.min(omarchyWindows.length, 6); o++) {
        oLines.push(omarchyWindows[o])
      }
      if (omarchyWindows.length > 6) {
        oLines.push("+" + (omarchyWindows.length - 6) + " more")
      }
      return oLines.join("\n")
    } catch (err) {
      console.log("[DEBUG] Error in workspaceTooltip: " + err)
      return "Desktop " + displayId
    }
  }

  function workspaceOccupied(displayId) {
    var _rev = root.windowsRevision
    if (desktopMode !== "windows") {
      var workspace = workspaceById(displayId)
      return workspace !== null && workspace.toplevels.values.length > 0
    }

    var setSize = effectiveSetSize()
    for (var slot = 0; slot < setSize; slot++) {
      var workspace = workspaceById(windowsWorkspaceId(displayId, slot))
      if (workspace !== null && workspace.toplevels.values.length > 0) return true
    }
    return false
  }

  function workspaceFocused(displayId) {
    var _rev = root.windowsRevision
    if (desktopMode === "windows") {
      var names = effectiveMonitorNames()
      if (names.length === 0) {
        return Hyprland.focusedWorkspace !== null
          && windowsDisplayId(Hyprland.focusedWorkspace.id) === displayId
      }
      for (var i = 0; i < names.length; i++) {
        var monitor = monitorByName(names[i])
        var slot = slotForMonitor(names[i], i)
        var expectedWs = windowsWorkspaceId(displayId, slot)
        if (monitor === null || monitor.activeWorkspace === null
            || monitor.activeWorkspace.id !== expectedWs) return false
      }
      return true
    }
    if (desktopMode === "mac") {
      return barMonitor !== null && barMonitor.activeWorkspace !== null
        && barMonitor.activeWorkspace.id === displayId
    }
    return Hyprland.focusedWorkspace !== null && Hyprland.focusedWorkspace.id === displayId
  }

  property var pendingActions: []

  Process {
    id: actionProcess
    clearEnvironment: true
    environment: root.processEnv

    stdout: StdioCollector {
      waitForEnd: false
      onDataChanged: {
        if (text.length > 128) {
          actionProcess.signal(9)
          actionProcess.running = false
        }
      }
    }

    onStarted: actionWatchdog.restart()
    onExited: function(exitCode, exitStatus) {
      actionWatchdog.stop()
      root.runNextAction()
    }
  }

  Timer {
    id: actionWatchdog
    interval: 5000
    repeat: false
    onTriggered: {
      if (actionProcess.running) {
        actionProcess.signal(9)
        actionProcess.running = false
      }
    }
  }

  function runNextAction() {
    if (pendingActions.length === 0) return
    var nextCmd = pendingActions.shift()
    actionProcess.command = nextCmd
    actionProcess.running = true
  }

  function runDesktopCommand(argsList) {
    var cmd = [root.canonicalHelperPath].concat(argsList)
    if (actionProcess.running) {
      if (pendingActions.length < 5) {
        pendingActions.push(cmd)
      }
    } else {
      actionProcess.command = cmd
      actionProcess.running = true
    }
  }

  function focusWorkspace(id) {
    var num = parseInt(id, 10)
    if (!isNaN(num) && num >= 1 && num <= 10) {
      runDesktopCommand(["switch", String(num)])
    }
  }

  function loadDesktopMode(raw) {
    var mode = String(raw || "").trim()
    if (mode.length > 16) return
    root.desktopMode = mode === "omarchy" || mode === "windows" ? mode : "mac"
  }

  function loadMonitors(raw) {
    if (!raw || raw.length > 8192) return
    try {
      var data = JSON.parse(raw)
      if (data && typeof data === "object") {
        var monRe = /^[A-Za-z0-9._-]{1,64}$/
        var names = []
        if (data.version >= 2 && Array.isArray(data.monitors) && data.monitors.length <= 16) {
          for (var i = 0; i < data.monitors.length; i++) {
            var name = data.monitors[i]
            if (typeof name !== "string" || !monRe.test(name) || names.indexOf(name) !== -1) {
              names = []
              break
            }
            names.push(name)
          }
        }
        root.monitorNames = names
        root.leftMonitor = typeof data.left === "string" && monRe.test(data.left)
          ? data.left
          : (names.length > 0 ? names[0] : "")
        root.rightMonitor = typeof data.right === "string" && monRe.test(data.right)
          ? data.right
          : (names.length > 0 ? names[names.length - 1] : "")
        root.monitorCount = names.length > 0
          ? names.length
          : (typeof data.count === "number" && data.count >= 1 && data.count <= 16 ? data.count : 1)

        if (typeof data.topology_size === "number" && data.topology_size >= 1) {
          root.topologySize = data.topology_size
        }
        if (Array.isArray(data.topology)) {
          var topo = []
          for (var t = 0; t < data.topology.length; t++) {
            if (typeof data.topology[t] === "string" && monRe.test(data.topology[t])) {
              topo.push(data.topology[t])
            }
          }
          root.topologyMonitors = topo
        }
        root.monitorSlots = data.slots && typeof data.slots === "object" ? data.slots : ({})
        root.degradedMode = !!data.degraded
      }
    } catch (e) {}
  }

  function nextDesktopMode() {
    if (desktopMode === "omarchy") return "mac"
    if (desktopMode === "mac") return "windows"
    return "omarchy"
  }

  function desktopModeLetter() {
    if (desktopMode === "omarchy") return "O"
    if (desktopMode === "windows") return "W"
    return "M"
  }

  readonly property real trailingGap: root.vertical ? 0 : Style.spaceReal(1.5)

  implicitWidth: grid.implicitWidth + trailingGap
  implicitHeight: grid.implicitHeight

  // FileView does not reload on its own: text() inside fileChanged is still
  // the previously loaded content. Route every change through reload() so
  // onLoaded always parses fresh bytes (same idiom as the stock shell).
  FileView {
    id: modeFile
    path: root.modePath
    watchChanges: true
    printErrors: false
    onLoaded: root.loadDesktopMode(text())
    onLoadFailed: root.loadDesktopMode("mac")
    onFileChanged: reload()
  }

  FileView {
    id: monitorsFile
    path: root.monitorsPath
    watchChanges: true
    printErrors: false
    onLoaded: root.loadMonitors(text())
    onLoadFailed: {}
    onFileChanged: reload()
  }

  Process {
    id: modeStatusProcess
    command: [root.canonicalHelperPath, "status"]
    clearEnvironment: true
    environment: root.processEnv

    stdout: StdioCollector {
      waitForEnd: false
      onDataChanged: {
        if (text.length > 64) {
          modeStatusProcess.signal(9)
          modeStatusProcess.running = false
        }
      }
      onStreamFinished: {
        if (text.length <= 64) {
          root.loadDesktopMode(text)
        }
        // The status run may have just rewritten desktop-monitors (a bar
        // built while a display was missing reads the degraded snapshot
        // first); re-read the file rather than the cached text.
        monitorsFile.reload()
      }
    }

    onStarted: statusWatchdog.restart()
    onExited: statusWatchdog.stop()
  }

  Timer {
    id: statusWatchdog
    interval: 2000
    repeat: false
    onTriggered: {
      if (modeStatusProcess.running) {
        modeStatusProcess.signal(9)
        modeStatusProcess.running = false
      }
    }
  }

  Timer {
    id: modeRefreshTimer
    interval: 30000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: if (!modeStatusProcess.running) modeStatusProcess.running = true
  }

  GridLayout {
    id: grid
    anchors.fill: parent
    anchors.rightMargin: root.trailingGap
    columns: root.vertical ? 1 : root.workspaceIds().length + 1
    columnSpacing: root.vertical ? 0 : Style.space(1)
    rowSpacing: root.vertical ? Style.space(2) : 0

    Repeater {
      model: root.workspaceIds()

      WidgetButton {
        required property int modelData

        readonly property bool occupied: root.workspaceOccupied(modelData)
        readonly property bool focused: root.workspaceFocused(modelData)
        readonly property bool partial: !focused && root.splitDesktop() === modelData

        bar: root.bar
        // Filled rounded square = the set shows this desktop; the outline twin
        // = only the focused monitor does (split set).
        text: focused ? "\uDB85\uDCFB"
          : (partial ? "\uDB85\uDCFC" : (modelData === 10 ? "0" : String(modelData)))
        tooltipText: root.workspaceTooltip(modelData)
        opacity: occupied || focused || partial ? 1 : 0.5
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(20)
        fixedHeight: root.barSize
        onPressed: function() { root.focusWorkspace(modelData) }
      }
    }

    WidgetButton {
      bar: root.bar
      text: root.splitSet ? "P" : root.desktopModeLetter()
      tooltipText: {
        if (root.splitSet) {
          var back = root.lastAlignedDesktop > 0 ? root.lastAlignedDesktop : root.splitDesktop()
          return "Partial desktop set: " + root.splitDetail()
            + "\nClick to return to desktop " + back
            + ", or pick a desktop from the bar / SUPER+number."
        }
        var base = root.desktopMode === "omarchy"
          ? "Omarchy Desktop mode — click for Mac mode"
          : (root.desktopMode === "mac"
            ? "Mac Desktop mode — click for Windows mode"
            : "Windows Desktop mode — click for Omarchy mode")
        if (root.degradedMode && root.desktopMode === "windows") {
          base += " [" + root.effectiveMonitorNames().length + "/" + root.topologySize + " Displays Active]"
        }
        return base
      }
      horizontalMargin: 6
      verticalPadding: 6
      fixedWidth: root.vertical ? root.barSize : Style.space(20)
      fixedHeight: root.barSize
      onPressed: function() {
        if (root.splitSet) {
          root.realignSet()
          return
        }
        root.desktopMode = root.nextDesktopMode()
        root.runDesktopCommand(["toggle"])
        modeRefreshTimer.restart()
      }
    }
  }
}
