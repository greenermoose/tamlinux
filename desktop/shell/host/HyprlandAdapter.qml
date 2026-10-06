import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

// The only shell file that imports Quickshell.Hyprland or starts hyprctl.
// Command text matches compositor_commands.py. There is no generic hyprctl argv.
QtObject {
  id: adapter

  property var host: null
  // PopupCard creates one per popup: Hyprland's focus grab clears on a click
  // outside the listed windows.
  readonly property Component focusGrab: Component { HyprlandFocusGrab {} }
  property var queue: []
  property var dpmsByName: ({})
  property string currentLabel: ""
  property string publishedKey: ""
  property bool ingested: false
  property var doneReads: ({})
  property int bindsReads: 0
  property string bindingsText: ""
  property string activeKeymap: ""
  property string typedKeyboardName: ""
  property bool devicesPending: false
  readonly property int keyboardLimit: 16
  readonly property bool liveActions: Quickshell.env("TAMLINUX_COMPOSITOR_LIVE_ACTIONS") === "1"
  readonly property int bindsLimit: 262144
  readonly property int devicesLimit: 262144
  readonly property int monitorsLimit: 262144
  readonly property int keymapLimit: 128
  readonly property int descriptionLimit: 128
  readonly property int windowLimit: 8
  readonly property int titleLimit: 80
  readonly property int classLimit: 64
  readonly property int workspaceListLimit: 64

  readonly property var closedEnv: {
    var env = { "PATH": "/usr/bin" }
    var runtime = Quickshell.env("XDG_RUNTIME_DIR") || ""
    var signature = Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") || ""
    if (runtime !== "") env["XDG_RUNTIME_DIR"] = runtime
    if (signature !== "") env["HYPRLAND_INSTANCE_SIGNATURE"] = signature
    return env
  }

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function validName(name) {
    return /^[A-Za-z0-9._-]{1,64}$/.test(String(name || ""))
  }

  function validAppName(name) {
    return /^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$/.test(String(name || ""))
  }

  function windowAddress(value) {
    var hex = String(value || "").replace(/^0x/, "")
    if (!/^[0-9a-fA-F]{1,16}$/.test(hex)) return ""
    return "0x" + hex.toLowerCase()
  }

  function validWorkspace(id) {
    return /^(?:[1-9]|10)$/.test(String(id || ""))
  }

  function bindsCommand() {
    return ["/usr/bin/hyprctl", "binds"]
  }

  function devicesCommand() {
    return ["/usr/bin/hyprctl", "-j", "devices"]
  }

  function monitorsCommand() {
    return ["/usr/bin/hyprctl", "-j", "monitors"]
  }

  function focusWorkspace(id) {
    if (!validWorkspace(id)) {
      note("compositor-action rejected focus-workspace")
      return
    }
    var number = String(id)
    if (!liveActions) {
      note("compositor-action recorded focus-workspace " + number)
      return
    }
    note("compositor-action live focus-workspace " + number)
    enqueue(["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ workspace = "' + number + '" })'], "dispatch")
  }

  // switchxkblayout is a hyprctl command rather than a dispatcher, so it runs
  // as one rather than through the dispatch socket.
  function switchKeyboardLayout(name) {
    var keyboard = String(name || "")
    if (!validName(keyboard)) {
      note("compositor-action rejected switch-keyboard-layout")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded switch-keyboard-layout " + keyboard)
      return
    }
    note("compositor-action live switch-keyboard-layout " + keyboard)
    enqueue(["/usr/bin/hyprctl", "switchxkblayout", keyboard, "next"], "switch-keyboard-layout")
  }

  function refreshKeyboards() {
    rereadDevices()
  }

  function focusOutput(name) {
    var output = String(name || "")
    if (!validName(output)) {
      note("compositor-action rejected focus-output")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded focus-output " + output)
      return
    }
    note("compositor-action live focus-output " + output)
    enqueue(["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ monitor = "' + output + '" })'], "dispatch")
  }

  function setDpms(name, on) {
    var output = String(name || "")
    var enabled = on === true || on === "on"
    var disabled = on === false || on === "off"
    if (!validName(output) || enabled === disabled) {
      note("compositor-action rejected set-dpms")
      return
    }
    var word = enabled ? "on" : "off"
    if (!liveActions) {
      note("compositor-action recorded set-dpms " + output + " " + word)
      return
    }
    note("compositor-action live set-dpms " + output + " " + word)
    enqueue([
      "/usr/bin/hyprctl",
      "dispatch",
      'hl.dsp.dpms({ action = "' + word + '", monitor = "' + output + '" })'
    ], "dispatch")
  }

  property string pendingApp: ""

  // Focus the first window whose class contains name (case-insensitive).
  // Agent terminals share one class and keep the program in initialTitle.
  function focusApp(name) {
    var app = String(name || "")
    if (!validAppName(app)) {
      note("compositor-action rejected focus-app")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded focus-app " + app)
      return
    }
    pendingApp = app
    Hyprland.refreshToplevels()
    focusAppTimer.restart()
  }

  function addressForApp(app) {
    var needle = app.toLowerCase()
    var toplevels = Hyprland.toplevels && Hyprland.toplevels.values ? Hyprland.toplevels.values : []
    var agent = ""
    for (var i = 0; i < toplevels.length; i++) {
      var toplevel = toplevels[i]
      if (!toplevel) continue
      var ipc = toplevel.lastIpcObject || {}
      var cls = ""
      if (toplevel.wayland && toplevel.wayland.appId) cls = String(toplevel.wayland.appId)
      else if (ipc["class"]) cls = String(ipc["class"])
      if (cls.toLowerCase().indexOf(needle) !== -1) return windowAddress(toplevel.address)
      if (agent === "" && String(ipc.initialClass || "") === "org.omarchy.agent"
          && String(ipc.initialTitle || "").toLowerCase().indexOf(needle) !== -1)
        agent = windowAddress(toplevel.address)
    }
    return agent
  }

  function finishFocusApp() {
    var app = pendingApp
    pendingApp = ""
    if (app === "") return
    var address = addressForApp(app)
    if (address === "") {
      note("compositor-action focus-app no-window " + app)
      return
    }
    note("compositor-action live focus-app " + app)
    enqueue(["/usr/bin/hyprctl", "dispatch", 'hl.dsp.focus({ window = "address:' + address + '" })'], "dispatch")
  }

  readonly property Timer focusAppTimer: Timer {
    interval: 150
    onTriggered: adapter.finishFocusApp()
  }

  function enqueue(argv, label) {
    var next = queue.slice()
    next.push({ argv: argv, label: label })
    queue = next
    pump()
  }

  function pump() {
    if (reader.running || queue.length === 0) return
    var job = queue[0]
    queue = queue.slice(1)
    currentLabel = job.label
    ingested = false
    reader.command = job.argv
    reader.running = true
  }

  function bounded(text, limit) {
    var raw = String(text || "")
    if (raw.length > limit) return raw.substring(0, limit)
    return raw
  }

  // A read already in flight may predate the change that asked for this one,
  // so remember the request and read again once it lands.
  function rereadDevices() {
    if (devicesProc.running) {
      devicesPending = true
      return
    }
    devicesPending = false
    doneReads.devices = false
    devicesProc.running = true
  }

  // Reads run once each; the bindings are read again after a reload, the
  // devices whenever the keyboard layout widget asks.
  function rereadBinds() {
    if (bindsProc.running) return
    doneReads.binds = false
    bindsProc.running = true
  }

  function finishRead(label, text) {
    if (doneReads[label]) return
    doneReads[label] = true
    var body = String(text || "")
    if (label === "binds") {
      bindingsText = bounded(body, bindsLimit)
      bindsReads = bindsReads + 1
      note("compositor-adapter hyprctl binds bytes=" + bindingsText.length)
      if (body.length > bindsLimit) note("compositor-adapter capped binds")
    } else if (label === "devices") {
      var devices = bounded(body, devicesLimit)
      note("compositor-adapter hyprctl devices bytes=" + devices.length)
      if (body.length > devicesLimit) note("compositor-adapter capped devices")
      activeKeymap = keymapFrom(devices)
      if (host && host.applyKeyboards) host.applyKeyboards(keyboardsFrom(devices), typedKeyboardName)
    } else if (label === "monitors") {
      var monitors = bounded(body, monitorsLimit)
      note("compositor-adapter hyprctl monitors bytes=" + monitors.length)
      if (body.length > monitorsLimit) note("compositor-adapter capped monitors")
      ingestMonitors(monitors)
    }
    publish()
  }

  function keymapFrom(text) {
    try {
      var data = JSON.parse(text || "")
      var boards = data && data.keyboards ? data.keyboards : []
      var fallback = ""
      for (var i = 0; i < boards.length; i++) {
        var board = boards[i]
        if (!board || !board.active_keymap) continue
        var name = String(board.active_keymap)
        if (name.indexOf("\n") !== -1 || name.indexOf("\r") !== -1) continue
        if (name.length > keymapLimit) name = name.substring(0, keymapLimit)
        if (board.main) return name
        if (fallback === "") fallback = name
      }
      return fallback
    } catch (e) {
      return ""
    }
  }

  // The keyboards in `hyprctl -j devices`, bounded and with only the fields
  // the layout widget reads. Mirrors compositor_commands.keyboards_from.
  function keyboardsFrom(text) {
    try {
      var data = JSON.parse(text || "")
      var boards = data && Array.isArray(data.keyboards) ? data.keyboards : []
      var list = []
      for (var i = 0; i < boards.length && list.length < keyboardLimit; i++) {
        var board = boards[i]
        if (!board || !validName(board.name)) continue
        var keymap = String(board.active_keymap || "")
        if (keymap.indexOf("\n") !== -1 || keymap.indexOf("\r") !== -1) keymap = ""
        var index = Number(board.active_layout_index)
        list.push({
          name: String(board.name),
          layout: board.layout === undefined || board.layout === null ? null : String(board.layout).substring(0, keymapLimit),
          activeKeymap: keymap.substring(0, keymapLimit),
          activeLayoutIndex: isFinite(index) && index >= 0 ? Math.floor(index) : 0,
          main: board.main === true
        })
      }
      return list
    } catch (e) {
      return []
    }
  }

  // activelayout's data is "<keyboard>,<layout>": the keyboard being typed
  // on, whatever holds the main flag. fcitx5's virtual keyboard is not one.
  function noteActiveLayout(data) {
    var name = String(data || "").split(",")[0]
    if (validName(name) && name.indexOf("hl-virtual-keyboard") !== 0) typedKeyboardName = name
  }

  function ingestMonitors(text) {
    try {
      var data = JSON.parse(text || "")
      if (!data || !data.length) return
      var map = {}
      for (var i = 0; i < data.length; i++) {
        var item = data[i]
        if (!item || !validName(item.name)) continue
        if (item.dpmsStatus === false) map[item.name] = false
        else if (item.dpmsStatus === true) map[item.name] = true
      }
      dpmsByName = map
    } catch (e) {
      note("compositor-adapter hyprctl monitors failed")
    }
  }

  function boundedDescription(monitor) {
    var text = ""
    if (monitor && monitor.description) text = String(monitor.description)
    else if (monitor && monitor.lastIpcObject && monitor.lastIpcObject.description)
      text = String(monitor.lastIpcObject.description)
    text = text.replace(/\r/g, " ").replace(/\n/g, " ")
    if (text.length > descriptionLimit) text = text.substring(0, descriptionLimit)
    return text
  }

  function boundedPosition(value) {
    if (typeof value !== "number" || !isFinite(value)) return 0
    var n = Math.round(value)
    if (n > 100000) return 100000
    if (n < -100000) return -100000
    return n
  }

  function windowSummary(toplevel) {
    if (!toplevel) return null
    var cls = ""
    if (toplevel.wayland && toplevel.wayland.appId) cls = String(toplevel.wayland.appId)
    else if (toplevel.lastIpcObject && toplevel.lastIpcObject["class"]) cls = String(toplevel.lastIpcObject["class"])
    var title = String(toplevel.title || "")
    if (cls === "" && title === "") return null
    if (cls.length > classLimit) cls = cls.substring(0, classLimit)
    if (title.length > titleLimit) title = title.substring(0, titleLimit - 3) + "..."
    return { className: cls, title: title }
  }

  function refreshFromHyprland() {
    publish()
  }

  function publish() {
    if (!host) return
    var focused = ""
    if (Hyprland.focusedMonitor && validName(Hyprland.focusedMonitor.name))
      focused = String(Hyprland.focusedMonitor.name)
    var focusedWorkspace = 0
    if (Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id > 0)
      focusedWorkspace = Hyprland.focusedWorkspace.id
    var monitors = Hyprland.monitors && Hyprland.monitors.values ? Hyprland.monitors.values : []
    var outputs = []
    for (var i = 0; i < monitors.length; i++) {
      var monitor = monitors[i]
      if (!monitor || !validName(monitor.name)) continue
      var wsId = 0
      if (monitor.activeWorkspace && monitor.activeWorkspace.id > 0)
        wsId = monitor.activeWorkspace.id
      var dpmsOn = true
      if (dpmsByName && dpmsByName[monitor.name] === false) dpmsOn = false
      else if (dpmsByName && dpmsByName[monitor.name] === true) dpmsOn = true
      else if (monitor.lastIpcObject && monitor.lastIpcObject.dpmsStatus === false) dpmsOn = false
      var special = false
      if (monitor.activeSpecialWorkspace && monitor.activeSpecialWorkspace.id)
        special = monitor.activeSpecialWorkspace.id !== 0
      outputs.push({
        name: String(monitor.name),
        focused: String(monitor.name) === focused,
        activeWorkspaceId: wsId,
        dpmsOn: dpmsOn,
        description: boundedDescription(monitor),
        x: boundedPosition(monitor.x),
        y: boundedPosition(monitor.y),
        special: special
      })
    }
    outputs.sort(function(a, b) {
      if (a.name < b.name) return -1
      if (a.name > b.name) return 1
      return 0
    })
    var spaces = Hyprland.workspaces && Hyprland.workspaces.values ? Hyprland.workspaces.values : []
    var workspaces = []
    for (var w = 0; w < spaces.length && workspaces.length < workspaceListLimit; w++) {
      var space = spaces[w]
      if (!space || !(space.id > 0)) continue
      var outputName = space.monitor && validName(space.monitor.name) ? String(space.monitor.name) : ""
      var windows = []
      var toplevels = space.toplevels && space.toplevels.values ? space.toplevels.values : []
      var occupied = toplevels.length > 0
      for (var t = 0; t < toplevels.length && windows.length < windowLimit; t++) {
        var summary = windowSummary(toplevels[t])
        if (summary) windows.push(summary)
      }
      workspaces.push({
        id: space.id,
        output: outputName,
        occupied: occupied,
        windows: windows
      })
    }
    workspaces.sort(function(a, b) { return a.id - b.id })
    var key = focused + "#" + focusedWorkspace + "#" + bindsReads + "#" + bindingsText.length + "#" + activeKeymap
    for (var n = 0; n < outputs.length; n++) {
      key += "|" + outputs[n].name + ":" + outputs[n].activeWorkspaceId + ":" + (outputs[n].dpmsOn ? "1" : "0")
      key += ":" + (outputs[n].special ? "s" : "") + ":" + outputs[n].x + "," + outputs[n].y + ":" + outputs[n].description
    }
    for (var s = 0; s < workspaces.length; s++) {
      key += "|w" + workspaces[s].id + ":" + workspaces[s].output + ":" + workspaces[s].windows.length
    }
    if (key === publishedKey) return
    publishedKey = key
    host.applySnapshot({
      outputs: outputs,
      focusedOutputName: focused,
      workspaces: workspaces,
      focusedWorkspaceId: focusedWorkspace,
      bindingsText: bindingsText,
      activeKeymap: activeKeymap
    })
  }

  readonly property Process bindsProc: Process {
    id: bindsProc
    clearEnvironment: true
    environment: adapter.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: adapter.finishRead("binds", String(text || ""))
    }
    stderr: StdioCollector { waitForEnd: true }
    onStarted: bindsTerm.restart()
    onExited: bindsTerm.stop()
  }

  readonly property Timer bindsTerm: Timer {
    interval: 4000
    onTriggered: bindsProc.signal(15)
  }

  readonly property Process devicesProc: Process {
    id: devicesProc
    clearEnvironment: true
    environment: adapter.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: adapter.finishRead("devices", String(text || ""))
    }
    stderr: StdioCollector { waitForEnd: true }
    onStarted: devicesTerm.restart()
    onExited: {
      devicesTerm.stop()
      if (adapter.devicesPending) adapter.rereadDevices()
    }
  }

  readonly property Timer devicesTerm: Timer {
    interval: 4000
    onTriggered: devicesProc.signal(15)
  }

  readonly property Process monitorsProc: Process {
    id: monitorsProc
    clearEnvironment: true
    environment: adapter.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: adapter.finishRead("monitors", String(text || ""))
    }
    stderr: StdioCollector { waitForEnd: true }
    onStarted: monitorsTerm.restart()
    onExited: monitorsTerm.stop()
  }

  readonly property Timer monitorsTerm: Timer {
    interval: 4000
    onTriggered: monitorsProc.signal(15)
  }

  readonly property Process reader: Process {
    id: reader
    clearEnvironment: true
    environment: adapter.closedEnv
    stdout: StdioCollector {
      id: collector
      waitForEnd: true
    }
    stderr: StdioCollector { waitForEnd: true }
    onStarted: adapter.termTimer.restart()
    onExited: {
      adapter.termTimer.stop()
      adapter.killTimer.stop()
      adapter.ingested = false
      adapter.pump()
    }
  }

  readonly property Timer termTimer: Timer {
    interval: 4000
    onTriggered: {
      reader.signal(15)
      adapter.killTimer.restart()
    }
  }

  readonly property Timer killTimer: Timer {
    interval: 3000
    onTriggered: reader.signal(9)
  }

  readonly property Connections hyprlandEvents: Connections {
    target: Hyprland
    function onFocusedMonitorChanged() { adapter.refreshFromHyprland() }
    function onFocusedWorkspaceChanged() { adapter.refreshFromHyprland() }
    // Re-read the bindings after the config reloads, so the keybinding
    // viewer never shows stale ones.
    // A layout switch, or a reload that adds a layout, changes what the
    // keyboard layout widget shows, so read the devices again too.
    function onRawEvent(event) {
      if (!event) return
      var name = String(event.name || "")
      if (name === "configreloaded") {
        adapter.rereadBinds()
        adapter.rereadDevices()
      } else if (name.indexOf("activelayout") !== -1) {
        if (name === "activelayout") adapter.noteActiveLayout(event.data)
        adapter.rereadDevices()
      }
    }
  }

  readonly property Timer refreshTimer: Timer {
    interval: 400
    running: true
    repeat: false
    onTriggered: adapter.refreshFromHyprland()
  }

  Component.onCompleted: {
    refreshFromHyprland()
    bindsProc.command = bindsCommand()
    devicesProc.command = devicesCommand()
    monitorsProc.command = monitorsCommand()
    bindsProc.running = true
    devicesProc.running = true
    monitorsProc.running = true
  }
}
