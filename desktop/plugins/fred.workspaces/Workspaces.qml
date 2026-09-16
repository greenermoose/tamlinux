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
    return Math.max(1, effectiveMonitorNames().length)
  }

  function windowsWorkspaceId(displayId, monitorIndex) {
    return (displayId - 1) * effectiveSetSize() + monitorIndex + 1
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

  Connections {
    target: Hyprland
    function onRawEvent(event) {
      root.windowsRevision++
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

      if (desktopMode === "windows") {
        var names = effectiveMonitorNames()
        var setSize = Math.max(1, names.length)
        var lines = ["Desktop " + displayId + headerSuffix]
        var totalWindows = 0
        var maxLines = 24

        for (var position = 0; position < setSize && lines.length < maxLines; position++) {
          var wsId = windowsWorkspaceId(displayId, position)
          var windows = workspaceWindowSummaries(wsId)
          totalWindows += windows.length
          var role = monitorRole(position, setSize, names[position] || "")
          for (var w = 0; w < Math.min(windows.length, 3) && lines.length < maxLines; w++) {
            lines.push("[" + role + "] " + windows[w])
          }
          if (windows.length > 3 && lines.length < maxLines) {
            lines.push("[" + role + "] +" + (windows.length - 3) + " more")
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
    for (var position = 0; position < setSize; position++) {
      var workspace = workspaceById(windowsWorkspaceId(displayId, position))
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
      for (var position = 0; position < names.length; position++) {
        var monitor = monitorByName(names[position])
        if (monitor === null || monitor.activeWorkspace === null
            || monitor.activeWorkspace.id !== windowsWorkspaceId(displayId, position)) return false
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
    if (!raw || raw.length > 4096) return
    try {
      var data = JSON.parse(raw)
      if (data && typeof data === "object") {
        var monRe = /^[A-Za-z0-9._-]{1,64}$/
        var names = []
        if (data.version === 2 && Array.isArray(data.monitors) && data.monitors.length <= 16) {
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

  FileView {
    id: modeFile
    path: root.modePath
    watchChanges: true
    atomicWrites: true
    printErrors: false
    onLoaded: root.loadDesktopMode(text())
    onLoadFailed: root.loadDesktopMode("mac")
    onFileChanged: root.loadDesktopMode(text())
  }

  FileView {
    id: monitorsFile
    path: root.monitorsPath
    watchChanges: true
    atomicWrites: true
    printErrors: false
    onLoaded: root.loadMonitors(text())
    onLoadFailed: {}
    onFileChanged: root.loadMonitors(text())
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
        root.loadMonitors(monitorsFile.text())
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

        bar: root.bar
        text: focused ? "\uDB85\uDCFB" : (modelData === 10 ? "0" : String(modelData))
        tooltipText: root.workspaceTooltip(modelData)
        opacity: occupied || focused ? 1 : 0.5
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(20)
        fixedHeight: root.barSize
        onPressed: function() { root.focusWorkspace(modelData) }
      }
    }

    WidgetButton {
      bar: root.bar
      text: root.desktopModeLetter()
      tooltipText: root.desktopMode === "omarchy"
        ? "Omarchy Desktop mode — click for Mac mode"
        : (root.desktopMode === "mac"
          ? "Mac Desktop mode — click for Windows mode"
          : "Windows Desktop mode — click for Omarchy mode")
      horizontalMargin: 6
      verticalPadding: 6
      fixedWidth: root.vertical ? root.barSize : Style.space(20)
      fixedHeight: root.barSize
      onPressed: function() {
        root.desktopMode = root.nextDesktopMode()
        root.runDesktopCommand(["toggle"])
        modeRefreshTimer.restart()
      }
    }
  }
}
