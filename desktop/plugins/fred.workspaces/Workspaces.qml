import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Tam.Commons
import Tam.Ui
import "."

BarWidget {
  id: root
  moduleName: "fred.workspaces"

  readonly property string pluginVersion: "2.0.4"

  property string desktopMode: "mac"
  property string leftMonitor: ""
  property string rightMonitor: ""
  property var monitorNames: []
  property var topologyMonitors: []
  property int topologySize: 3
  property var monitorSlots: ({})
  property bool degradedMode: false
  property int monitorCount: 1

  // Per-monitor idle blanking of unused monitors (Plan 08)
  // Timeout in seconds. 0 disables per-monitor blanking.
  property int ownedUnusedMonitorTimeout: 300
  readonly property int unusedMonitorTimeout: {
    var raw = root.setting("unusedMonitorTimeout", root.ownedUnusedMonitorTimeout)
    if (typeof raw === "number") return Math.max(0, raw)
    var num = parseInt(raw, 10)
    return isNaN(num) ? 300 : Math.max(0, num)
  }
  property bool isMonitorDark: false
  // Set when this bar blanks its monitor, cleared once the facade reports it
  // dark. Until then a "lit" report predates the blank and is ignored, or
  // cursor entry would find nothing to wake.
  property bool blankUnconfirmed: false
  // True while this bar's helper process runs; siblings read it through
  // anyHelperRunning() before acting on a wake.
  readonly property bool helperRunning: actionProcess.running

  onBarMonitorChanged: {
    Qt.callLater(root.probeDpmsState)
    Qt.callLater(root.trackMonitorIdle)
  }
  onUnusedMonitorTimeoutChanged: Qt.callLater(root.trackMonitorIdle)

  readonly property string modePath: {
    var stateHome = Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
    return stateHome + "/tamlinux/desktop-mode"
  }
  readonly property string monitorsPath: {
    var stateHome = Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
    return stateHome + "/tamlinux/desktop-monitors"
  }
  readonly property string canonicalHelperPath: {
    var resolved = String(Qt.resolvedUrl("tam-desktop-mode"))
    if (resolved.indexOf("file://") === 0) {
      return decodeURIComponent(resolved.substring(7))
    }
    return ""
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
    var commands = Quickshell.env("TAMLINUX_COMPOSITOR_COMMANDS")
    if (commands) env["TAMLINUX_COMPOSITOR_COMMANDS"] = commands
    var live = Quickshell.env("TAMLINUX_COMPOSITOR_LIVE_ACTIONS")
    if (live) env["TAMLINUX_COMPOSITOR_LIVE_ACTIONS"] = live
    for (var key of ["LEFT_MONITOR", "RIGHT_MONITOR", "TOPOLOGY", "UNUSED_MONITOR_TIMEOUT"]) {
      var name = "TAMLINUX_DESKTOP_" + key
      var value = Quickshell.env(name)
      if (value) env[name] = value
    }
    return env
  }

  function compositorOutputs() {
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    return comp && comp.outputs ? comp.outputs : []
  }

  function outputRecord(item) {
    if (!item || !item.name) return null
    var id = item.activeWorkspaceId > 0 ? item.activeWorkspaceId : 0
    return {
      name: String(item.name),
      x: typeof item.x === "number" ? item.x : 0,
      y: typeof item.y === "number" ? item.y : 0,
      description: String(item.description || ""),
      dpmsOn: item.dpmsOn !== false,
      focused: item.focused === true,
      special: item.special === true,
      activeWorkspace: id > 0 ? { id: id } : null
    }
  }

  readonly property var barMonitor: {
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var _rev = comp ? comp.revision : 0
    if (!(root.QsWindow && root.QsWindow.window && root.QsWindow.window.screen)) return null
    var screen = root.QsWindow.window.screen
    var wanted = comp && comp.outputForScreen ? comp.outputForScreen(screen) : ""
    if (!wanted) wanted = String(screen.name || "")
    var outputs = root.compositorOutputs()
    for (var i = 0; i < outputs.length; i++) {
      if (outputs[i] && String(outputs[i].name) === wanted) return root.outputRecord(outputs[i])
    }
    if (wanted && /^[A-Za-z0-9._-]{1,64}$/.test(wanted)) {
      return {
        name: wanted, x: 0, y: 0, description: "", dpmsOn: true,
        focused: false, special: false, activeWorkspace: null
      }
    }
    return null
  }

  function workspaceById(id) {
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var values = comp && comp.workspaces ? comp.workspaces : []
    for (var i = 0; i < values.length; i++) {
      if (values[i] && values[i].id === id) return values[i]
    }
    return null
  }

  function quickshellMonitorNames() {
    var records = []
    var monitors = root.compositorOutputs()
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
    var monitors = root.compositorOutputs()
    for (var i = 0; i < monitors.length; i++) {
      if (monitors[i] && monitors[i].name === name) return root.outputRecord(monitors[i])
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
    if (root.compositorOutputs().length <= 1) return true

    var monitors = root.compositorOutputs()
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
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var values = comp && comp.workspaces ? comp.workspaces : []
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

  // Windows mode only (Omarchy and Mac modes treat each monitor on its own):
  // may a window focus split the set? When a focus lands on a hidden
  // workspace (an app opening on a stale workspace, a window switcher, a
  // single-monitor dispatch) Hyprland moves just that monitor.
  //   true  (default) - the set splits: that monitor shows a hollow marker
  //                     and F until it is returned (click F) or the set is
  //                     moved (desktop click, SUPER+N)
  //   false           - the whole set follows to the focused monitor's desktop
  //   omarchy bar set fred.workspaces splitSet true|false
  readonly property bool splitSetAllowed: {
    var raw = root.setting("splitSet", true)
    if (typeof raw === "boolean") return raw
    var text = String(raw === undefined || raw === null ? "" : raw).trim().toLowerCase()
    if (text === "false" || text === "0" || text === "no" || text === "off") return false
    return true
  }

  // Last desktop the whole set showed together; where a deviated monitor
  // returns to.
  property int lastAlignedDesktop: 0

  function trackAlignment() {
    var state = setState()
    if (!state.split && state.setDesktop > 0) root.lastAlignedDesktop = state.setDesktop
  }

  // Windows-mode set state.
  //   split      - monitors are not showing one desktop as a set
  //   desktops   - { monitorName: desktop it shows }
  //   setDesktop - the desktop the set is on: the common desktop when aligned;
  //                when split, the desktop it showed before the split (falling
  //                back to the desktop most monitors still show)
  //   focused    - desktop on the focused monitor (0 if unknown)
  function setState() {
    var _rev = root.windowsRevision
    var none = { "split": false, "desktops": ({}), "setDesktop": 0, "focused": 0 }
    if (desktopMode !== "windows") return none
    var names = effectiveMonitorNames()
    if (names.length < 2) return none
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var focusedName = comp ? String(comp.focusedOutputName || "") : ""
    var desktops = {}
    var counts = {}
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
      desktops[names[i]] = desktop
      counts[desktop] = (counts[desktop] || 0) + 1
      if (common === 0) common = desktop
      else if (desktop !== common) split = true
      if (names[i] === focusedName) focusedDesktop = desktop
    }
    var setDesktop = common
    if (split) {
      if (root.lastAlignedDesktop > 0 && counts[root.lastAlignedDesktop]) {
        setDesktop = root.lastAlignedDesktop
      } else {
        var best = 0
        for (var d in counts) {
          if (counts[d] > best) { best = counts[d]; setDesktop = parseInt(d, 10) }
        }
      }
    }
    return { "split": split, "desktops": desktops, "setDesktop": setDesktop, "focused": focusedDesktop }
  }

  // Desktop this bar's own monitor shows (0 if unknown).
  function barDesktop() {
    var _rev = root.windowsRevision
    if (barMonitor === null || barMonitor.activeWorkspace === null) return 0
    var ws = barMonitor.activeWorkspace.id
    return ws >= 1 ? windowsDisplayId(ws) : 0
  }

  readonly property bool setIsSplit: setState().split
  // This bar's monitor has left the set's desktop.
  readonly property bool barDeviated: {
    var state = setState()
    if (!state.split || barMonitor === null) return false
    var mine = state.desktops[barMonitor.name]
    return typeof mine === "number" && mine !== state.setDesktop
  }

  Component.onCompleted: {
    Qt.callLater(root.trackAlignment)
    Qt.callLater(root.probeDpmsState)
    Qt.callLater(root.trackMonitorIdle)
    Qt.callLater(function() {
      root.idleLog("bar created; timeout=" + root.unusedMonitorTimeout
        + " s, monitors=" + JSON.stringify(root.effectiveMonitorNames()))
    })
  }

  function monitorHasWindows() {
    if (!barMonitor) return false
    if (barMonitor.special) return true
    if (!barMonitor.activeWorkspace) return false
    var ws = workspaceById(barMonitor.activeWorkspace.id)
    return ws !== null && ws.occupied === true
  }

  function monitorIsFocused() {
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var focusedName = comp ? String(comp.focusedOutputName || "") : ""
    return barMonitor !== null && focusedName !== "" && barMonitor.name === focusedName
  }

  function idleLog(message) {
    console.log("fred.workspaces idle " + (barMonitor ? String(barMonitor.name) : "?") + ": " + message)
  }

  // Why the monitor counts as in use, or "" when it does not.
  function inUseReason() {
    if (effectiveMonitorNames().length <= 1) return "single-monitor"
    if (monitorIsFocused()) return "focused"
    if (monitorHasWindows()) return "windows"
    return ""
  }

  function monitorInUse() {
    return inUseReason() !== ""
  }

  function trackMonitorIdle() {
    if (unusedMonitorTimeout <= 0 || effectiveMonitorNames().length <= 1) {
      if (idleBlankTimer.running) idleBlankTimer.stop()
      if (useSettle.running) useSettle.stop()
      if (root.isMonitorDark) {
        root.wakeMonitor(unusedMonitorTimeout <= 0 ? "blanking-disabled" : "single-monitor")
      }
      return
    }

    var reason = inUseReason()
    if (reason !== "") {
      // Nothing changes until the sighting has settled (useSettle).
      if (!useSettle.running) {
        root.pendingUseReason = reason
        useSettle.restart()
      }
    } else {
      if (useSettle.running) {
        useSettle.stop()
        if (root.isMonitorDark || idleBlankTimer.running) {
          root.idleLog("ignored transient " + root.pendingUseReason)
        }
      }
      if (!root.isMonitorDark && !idleBlankTimer.running) {
        idleBlankTimer.interval = root.unusedMonitorTimeout * 1000
        idleBlankTimer.restart()
        root.idleLog("blank timer armed (" + root.unusedMonitorTimeout + " s)")
      }
    }
  }

  // A monitor is not treated as in use on the first event that makes it look
  // so. The helper's own set operations (switch, realign, reconcile) focus
  // every monitor in turn and move workspaces between them, and Quickshell's
  // monitor/workspace model is inconsistent until that batch has settled, so
  // an unused monitor reads as focused or populated for a few milliseconds
  // (seconds while the GPU is stalled). Acting on that re-lit the blanked HP
  // on 2026-09-18 with only the centre monitor in use, and reset its blank
  // countdown on every desktop switch. Decide instead on settled state: 400 ms
  // after the first sighting, once every bar's helper has exited. Cursor
  // entry still wakes the monitor, ~0.4 s later.
  property string pendingUseReason: ""

  Timer {
    id: useSettle
    interval: 400
    repeat: false
    onTriggered: {
      if (root.anyHelperRunning()) {
        useSettle.restart()
        return
      }
      var reason = root.inUseReason()
      if (reason === "") {
        if (root.isMonitorDark || idleBlankTimer.running) {
          root.idleLog("ignored transient " + root.pendingUseReason)
        }
        return
      }
      if (idleBlankTimer.running) {
        idleBlankTimer.stop()
        root.idleLog("in use (" + reason + "); blank timer stopped")
      }
      if (root.isMonitorDark) root.wakeMonitor(reason)
    }
  }

  function anyHelperRunning() {
    if (actionProcess.running) return true
    var items = siblingWidgets()
    for (var i = 0; i < items.length; i++) {
      if (items[i] && items[i].helperRunning === true) return true
    }
    return false
  }

  function wakeMonitor(reason) {
    if (!barMonitor) return
    root.isMonitorDark = false
    root.blankUnconfirmed = false
    root.idleLog("wake (" + reason + ")")
    root.runDesktopCommand(["dpms-on", String(barMonitor.name)])
  }

  function blankMonitor() {
    if (!barMonitor || root.isMonitorDark) return
    var reason = inUseReason()
    if (reason !== "") {
      root.idleLog("blank skipped: " + reason)
      return
    }
    root.isMonitorDark = true
    root.blankUnconfirmed = true
    root.idleLog("blank after " + root.unusedMonitorTimeout + " s unused")
    root.runDesktopCommand(["dpms-off", String(barMonitor.name)])
  }

  function resetIdle() {
    if (useSettle.running) useSettle.stop()
    if (root.isMonitorDark) root.idleLog("dark state reset (resetIdle)")
    root.isMonitorDark = false
    root.blankUnconfirmed = false
    Qt.callLater(root.trackMonitorIdle)
  }

  // A bar created while its monitor is already dark has to know it, or
  // cursor entry can never wake that monitor. The facade publishes dpmsOn.
  function probeDpmsState() {
    if (!barMonitor) return
    var dark = barMonitor.dpmsOn === false
    if (dark) root.blankUnconfirmed = false
    else if (root.isMonitorDark && root.blankUnconfirmed) return
    if (dark !== root.isMonitorDark) {
      root.idleLog(dark ? "monitor already dark; adopting it" : "monitor is lit; dropping stale dark state")
      root.isMonitorDark = dark
      if (dark && idleBlankTimer.running) idleBlankTimer.stop()
      Qt.callLater(root.trackMonitorIdle)
    }
  }

  function siblingWidgets() {
    var fn = bar ? (bar.moduleWidgets || bar._moduleWidgets) : null
    var candidates = [root.moduleName, "fred.workspaces"]
    for (var c = 0; c < candidates.length; c++) {
      if (typeof fn === "function") {
        var found = fn(candidates[c])
        if (found && found.length > 0) return found
      }
    }
    return []
  }

  function broadcastWorkspaces(method) {
    var items = siblingWidgets()
    if (items.length > 0) {
      for (var i = 0; i < items.length; i++) {
        if (items[i] && typeof items[i][method] === "function") {
          items[i][method]()
        }
      }
    } else {
      if (typeof root[method] === "function") root[method]()
    }
  }

  Timer {
    id: idleBlankTimer
    interval: root.unusedMonitorTimeout * 1000
    repeat: false
    onTriggered: {
      root.blankMonitor()
    }
  }

  // Per-bar button state. Monitors still on the set's desktop keep the solid
  // marker; a deviated monitor shows a hollow marker on its own desktop.
  function displayFocused(displayId) {
    var state = setState()
    if (!state.split) return workspaceFocused(displayId)
    return !barDeviated && displayId === state.setDesktop
  }

  function displayPartial(displayId) {
    return setIsSplit && barDeviated && displayId === barDesktop()
  }

  // Bring this bar's monitor back to the set's desktop.
  function realignBarMonitor() {
    var state = setState()
    if (barMonitor === null || state.setDesktop < 1 || state.setDesktop > 10) return
    runDesktopCommand(["realign", String(barMonitor.name), String(state.setDesktop)])
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

  property string seenOutputs: ""
  property string seenFocus: ""
  property bool compositorSeen: false

  function onCompositorRevision() {
    root.windowsRevision++
    Qt.callLater(root.trackAlignment)
    Qt.callLater(root.trackMonitorIdle)
    Qt.callLater(root.probeDpmsState)
    var outputs = root.compositorOutputs()
    var names = []
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    var focus = (comp ? String(comp.focusedOutputName || "") : "") + "#"
      + (comp ? comp.focusedWorkspaceId : 0)
    for (var i = 0; i < outputs.length; i++) {
      if (!outputs[i]) continue
      names.push(String(outputs[i].name))
      focus += "|" + outputs[i].name + ":" + outputs[i].activeWorkspaceId
    }
    names.sort()
    var outputKey = names.join(",")
    if (!root.compositorSeen) {
      root.compositorSeen = true
      root.seenOutputs = outputKey
      root.seenFocus = focus
      return
    }
    if (outputKey !== root.seenOutputs) {
      root.seenOutputs = outputKey
      root.seenFocus = focus
      reconcileDebounce.restart()
      return
    }
    if (focus !== root.seenFocus) {
      root.seenFocus = focus
      followDebounce.restart()
    }
  }

  Connections {
    target: root.bar && root.bar.compositor ? root.bar.compositor : null
    function onRevisionChanged() { root.onCompositorRevision() }
  }

  // splitSet=false: realign the set to the focused monitor's desktop. Only
  // the bar on the focused monitor acts, so
  // three bars do not launch three concurrent switches; the debounce lets a
  // helper-driven batch switch settle before the set is judged split.
  Timer {
    id: followDebounce
    interval: 300
    repeat: false
    onTriggered: {
      if (root.splitSetAllowed || root.desktopMode !== "windows") return
      var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
      var focusedName = comp ? String(comp.focusedOutputName || "") : ""
      if (barMonitor === null || focusedName === "" || barMonitor.name !== focusedName) return
      var state = root.setState()
      if (!state.split) return
      var desktop = state.focused > 0 ? state.focused : state.setDesktop
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
    if (t.className) {
      app = String(t.className)
    } else if (t.wayland && t.wayland.appId) {
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
      if (!ws || !ws.windows) return []
      var list = []
      var toplevels = ws.windows
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
    var tip = ""
    try {
      var _rev = root.windowsRevision
      var isFocused = desktopMode === "windows" ? displayFocused(displayId) : workspaceFocused(displayId)
      var headerSuffix = isFocused ? " (Current)" : ""
      if (desktopMode === "windows" && displayPartial(displayId)) {
        headerSuffix = " (This display only — the set is on desktop " + setState().setDesktop
          + "; click to bring the set here)"
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
          tip = "Desktop " + displayId + headerSuffix + "\n(Empty)"
        } else {
          tip = lines.join("\n")
        }
      } else if (desktopMode === "mac") {
        var leftName = leftMonitor || "Left"
        var rightName = rightMonitor || "Right"
        var monitorName = (displayId % 2 === 1) ? leftName : rightName
        if (effectiveSetSize() === 1 || leftName === rightName) {
          monitorName = leftName
        }

        var macWindows = workspaceWindowSummaries(displayId)
        if (macWindows.length === 0) {
          tip = "Workspace " + displayId + " (" + monitorName + ")" + headerSuffix + "\n(Empty)"
        } else {
          var macLines = ["Workspace " + displayId + " (" + monitorName + ")" + headerSuffix]
          for (var m = 0; m < Math.min(macWindows.length, 6); m++) {
            macLines.push(macWindows[m])
          }
          if (macWindows.length > 6) {
            macLines.push("+" + (macWindows.length - 6) + " more")
          }
          tip = macLines.join("\n")
        }
      } else {
        var omarchyWindows = workspaceWindowSummaries(displayId)
        if (omarchyWindows.length === 0) {
          tip = "Workspace " + displayId + headerSuffix + "\n(Empty)"
        } else {
          var oLines = ["Workspace " + displayId + headerSuffix]
          for (var o = 0; o < Math.min(omarchyWindows.length, 6); o++) {
            oLines.push(omarchyWindows[o])
          }
          if (omarchyWindows.length > 6) {
            oLines.push("+" + (omarchyWindows.length - 6) + " more")
          }
          tip = oLines.join("\n")
        }
      }
    } catch (err) {
      console.log("[DEBUG] Error in workspaceTooltip: " + err)
      tip = "Desktop " + displayId
    }
    return tip + "\n\nfred.workspaces v" + root.pluginVersion
  }

  function workspaceOccupied(displayId) {
    var _rev = root.windowsRevision
    if (desktopMode !== "windows") {
      var workspace = workspaceById(displayId)
      return workspace !== null && workspace.occupied === true
    }

    var setSize = effectiveSetSize()
    for (var slot = 0; slot < setSize; slot++) {
      var workspace = workspaceById(windowsWorkspaceId(displayId, slot))
      if (workspace !== null && workspace.occupied === true) return true
    }
    return false
  }

  function workspaceFocused(displayId) {
    var _rev = root.windowsRevision
    if (desktopMode === "windows") {
      var names = effectiveMonitorNames()
      if (names.length === 0) {
        var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
        return comp !== null && comp.focusedWorkspaceId > 0
          && windowsDisplayId(comp.focusedWorkspaceId) === displayId
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
    var comp = root.bar && root.bar.compositor ? root.bar.compositor : null
    return comp !== null && comp.focusedWorkspaceId === displayId
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
      // The helper may have just created the state directory. A FileView
      // whose directory was missing when it started never watches, so every
      // copy re-reads now, which also arms its watch.
      root.broadcastWorkspaces("reloadStateFiles")
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

  function reloadStateFiles() {
    modeFile.reload()
    monitorsFile.reload()
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
        // first); re-read the file rather than the cached text. Re-reading
        // the mode file also arms its watch if its directory has appeared.
        monitorsFile.reload()
        modeFile.reload()
      }
    }

    onStarted: statusWatchdog.restart()
    onExited: statusWatchdog.stop()
  }

  FileView {
    path: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/tamlinux/desktop-mode.conf"
    watchChanges: true
    printErrors: false
    onFileChanged: if (!preferencesProcess.running) preferencesProcess.running = true
  }

  Process {
    id: preferencesProcess
    command: [root.canonicalHelperPath, "preferences"]
    clearEnvironment: true
    environment: root.processEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (text.length > 256) return
        try {
          var prefs = JSON.parse(text)
          if (typeof prefs.unusedMonitorTimeout === "number") root.ownedUnusedMonitorTimeout = Math.max(0, prefs.unusedMonitorTimeout)
        } catch (error) {}
      }
    }
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
    onTriggered: {
      if (!modeStatusProcess.running) modeStatusProcess.running = true
      if (!preferencesProcess.running) preferencesProcess.running = true
    }
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
        readonly property bool focused: root.desktopMode === "windows"
          ? root.displayFocused(modelData) : root.workspaceFocused(modelData)
        readonly property bool partial: root.displayPartial(modelData)

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
      // F: this display followed a window focus off the set's desktop.
      text: root.barDeviated ? "F" : root.desktopModeLetter()
      tooltipText: {
        var tip = ""
        if (root.barDeviated) {
          var state = root.setState()
          tip = "Followed focus: this display moved to desktop " + root.barDesktop()
            + " while the set is on desktop " + state.setDesktop
            + " (" + root.splitDetail() + ").\nClick to return this display to desktop "
            + state.setDesktop + ", or pick a desktop from the bar / SUPER+number to move the whole set."
        } else {
          var base = root.desktopMode === "omarchy"
            ? "Omarchy Desktop mode — click for Mac mode"
            : (root.desktopMode === "mac"
              ? "Mac Desktop mode — click for Windows mode"
              : "Windows Desktop mode — click for Omarchy mode")
          if (root.degradedMode && root.desktopMode === "windows") {
            base += " [" + root.effectiveMonitorNames().length + "/" + root.topologySize + " Displays Active]"
          }
          tip = base
        }
        return tip + "\n\nfred.workspaces v" + root.pluginVersion
      }
      horizontalMargin: 6
      verticalPadding: 6
      fixedWidth: root.vertical ? root.barSize : Style.space(20)
      fixedHeight: root.barSize
      onPressed: function() {
        if (root.barDeviated) {
          root.realignBarMonitor()
          return
        }
        // Show the next mode at once. The helper's exit re-reads the file;
        // a status check started now could read the old mode and undo this.
        root.desktopMode = root.nextDesktopMode()
        root.runDesktopCommand(["toggle"])
      }
    }
  }

  IpcHandler {
    target: "fred.workspaces"

    function resetIdle(): void { root.broadcastWorkspaces("resetIdle") }
  }
}
