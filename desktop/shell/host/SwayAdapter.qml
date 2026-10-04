import QtQuick
import Quickshell
import Quickshell.WindowManager
import Quickshell.I3
import Quickshell.I3._Ipc
import Quickshell.Io

// The only shell file that imports Quickshell.WindowManager or Quickshell.I3.
// swaymsg argv matches sway_commands.py and is not started. Live mutations
// use I3.dispatch with one fixed request, and only when the live flag is set.
QtObject {
  id: adapter

  property var host: null
  property string publishedKey: ""
  readonly property bool liveActions: Quickshell.env("TAMLINUX_COMPOSITOR_LIVE_ACTIONS") === "1"
  readonly property int bindsLimit: 262144
  readonly property int monitorsLimit: 262144
  readonly property int keymapLimit: 128
  readonly property int descriptionLimit: 128
  readonly property int windowLimit: 8
  readonly property int titleLimit: 80
  readonly property int classLimit: 64
  readonly property int workspaceListLimit: 64

  readonly property var closedEnv: ({ "PATH": "/usr/bin" })

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function safePath(path) {
    var text = String(path || "")
    if (text.indexOf("..") !== -1) return false
    return /^\/[A-Za-z0-9._\/-]{1,240}$/.test(text)
  }

  function validName(name) {
    return /^[A-Za-z0-9._-]{1,64}$/.test(String(name || ""))
  }

  function validWorkspace(id) {
    return /^(?:[1-9]|10)$/.test(String(id || ""))
  }

  function focusWorkspaceArgv(number) {
    return ["/usr/bin/swaymsg", "workspace", "number", String(number)]
  }

  function focusWorkspaceRequest(number) {
    return "workspace number " + String(number)
  }

  function focusOutputArgv(output) {
    return ["/usr/bin/swaymsg", "focus", "output", output]
  }

  function focusOutputRequest(output) {
    return "focus output " + output
  }

  function validAppName(name) {
    return /^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$/.test(String(name || ""))
  }

  // Case-insensitive app_id search. "." and "+" become classes so the
  // criteria string never carries a backslash.
  function focusAppRequest(app) {
    return '[app_id="(?i)' + app.replace(/[.+]/g, function(c) { return "[" + c + "]" }) + '"] focus'
  }

  function setDpmsArgv(output, word) {
    return ["/usr/bin/swaymsg", "output", output, "power", word]
  }

  function setDpmsRequest(output, word) {
    return "output " + output + " power " + word
  }

  function inputsArgv() {
    return ["/usr/bin/swaymsg", "-t", "get_inputs", "-r"]
  }

  function outputsArgv() {
    return ["/usr/bin/swaymsg", "-t", "get_outputs", "-r"]
  }

  function workspacesArgv() {
    return ["/usr/bin/swaymsg", "-t", "get_workspaces", "-r"]
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
    if (activateWindowset(number)) return
    I3.dispatch(focusWorkspaceRequest(number))
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
    I3.dispatch(focusOutputRequest(output))
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
    I3.dispatch(setDpmsRequest(output, word))
  }

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
    note("compositor-action live focus-app " + app)
    I3.dispatch(focusAppRequest(app))
  }

  function activateWindowset(number) {
    var sets = WindowManager.windowsets || []
    var total = sets.length || 0
    for (var i = 0; i < total; i++) {
      var set = sets[i]
      if (!set || !set.activate) continue
      var id = String(set.id || set.name || "")
      if (id !== String(number)) continue
      set.activate()
      return true
    }
    return false
  }

  function listCount(list) {
    if (!list) return 0
    if (typeof list.length === "number") return list.length
    if (list.values && typeof list.values.length === "number") return list.values.length
    return 0
  }

  function listAt(list, index) {
    if (!list) return null
    if (list.values) return list.values[index]
    return list[index]
  }

  function bounded(text, limit) {
    var raw = String(text || "")
    if (raw.length > limit) return raw.substring(0, limit)
    return raw
  }

  function boundedPosition(value) {
    if (typeof value !== "number" || !isFinite(value)) return 0
    var n = Math.round(value)
    if (n > 100000) return 100000
    if (n < -100000) return -100000
    return n
  }

  function workspaceNumber(value) {
    var text = String(value || "")
    if (!/^(?:[1-9]|10)$/.test(text)) return 0
    return Number(text)
  }

  function publishSnapshot(snapshot) {
    if (!host || !snapshot) return
    var outputs = snapshot.outputs || []
    var workspaces = snapshot.workspaces || []
    var focused = String(snapshot.focusedOutputName || "")
    var focusedWorkspace = Number(snapshot.focusedWorkspaceId || 0)
    var bindingsText = String(snapshot.bindingsText || "")
    var activeKeymap = String(snapshot.activeKeymap || "")
    var key = focused + "#" + focusedWorkspace + "#" + bindingsText.length + "#" + activeKeymap
    for (var n = 0; n < outputs.length; n++) {
      var output = outputs[n]
      if (!output) continue
      key += "|" + output.name + ":" + output.activeWorkspaceId + ":" + (output.dpmsOn ? "1" : "0")
    }
    for (var s = 0; s < workspaces.length; s++) {
      var space = workspaces[s]
      if (!space) continue
      var windows = space.windows ? space.windows.length : 0
      key += "|w" + space.id + ":" + space.output + ":" + windows
    }
    if (key === publishedKey) return
    publishedKey = key
    host.applySnapshot(snapshot)
  }

  function workspacesFromWindowsets() {
    var sets = WindowManager.windowsets || []
    var total = listCount(sets)
    if (total === 0) return null
    var spaces = []
    var focused = 0
    for (var i = 0; i < total && spaces.length < workspaceListLimit; i++) {
      var set = listAt(sets, i)
      if (!set) continue
      var number = workspaceNumber(set.id || set.name)
      if (number === 0) continue
      if (set.active && focused === 0) focused = number
      spaces.push({
        id: number,
        output: "",
        occupied: false,
        windows: []
      })
    }
    if (spaces.length === 0) return null
    spaces.sort(function(a, b) { return a.id - b.id })
    return { workspaces: spaces, focusedWorkspaceId: focused }
  }

  function workspacesFromI3() {
    var model = I3.workspaces
    var total = listCount(model)
    var spaces = []
    var focused = 0
    for (var i = 0; i < total && spaces.length < workspaceListLimit; i++) {
      var space = listAt(model, i)
      if (!space) continue
      var number = workspaceNumber(space.num || space.id)
      if (number === 0) continue
      var output = space.monitor && validName(space.monitor.name) ? String(space.monitor.name) : ""
      if (space.focused && focused === 0) focused = number
      spaces.push({ id: number, output: output, occupied: false, windows: [] })
    }
    spaces.sort(function(a, b) { return a.id - b.id })
    return { workspaces: spaces, focusedWorkspaceId: focused }
  }

  function publishLive() {
    if (!host) return
    var chosen = workspacesFromWindowsets()
    if (!chosen) chosen = workspacesFromI3()
    var model = I3.monitors
    var total = listCount(model)
    var outputs = []
    var focused = ""
    if (I3.focusedMonitor && validName(I3.focusedMonitor.name))
      focused = String(I3.focusedMonitor.name)
    for (var i = 0; i < total; i++) {
      var monitor = listAt(model, i)
      if (!monitor || !validName(monitor.name)) continue
      var wsId = 0
      if (monitor.activeWorkspace) wsId = workspaceNumber(monitor.activeWorkspace.num || monitor.activeWorkspace.id)
      var description = ""
      if (monitor.lastIpcObject) {
        var make = String(monitor.lastIpcObject.make || "")
        var modelName = String(monitor.lastIpcObject.model || "")
        description = bounded((make + " " + modelName).trim(), descriptionLimit)
      }
      outputs.push({
        name: String(monitor.name),
        focused: String(monitor.name) === focused,
        activeWorkspaceId: wsId,
        dpmsOn: monitor.power !== false,
        description: description,
        x: boundedPosition(monitor.x),
        y: boundedPosition(monitor.y),
        special: false
      })
    }
    outputs.sort(function(a, b) {
      if (a.name < b.name) return -1
      if (a.name > b.name) return 1
      return 0
    })
    publishSnapshot({
      outputs: outputs,
      focusedOutputName: focused,
      workspaces: chosen.workspaces,
      focusedWorkspaceId: chosen.focusedWorkspaceId,
      bindingsText: "",
      activeKeymap: ""
    })
  }

  function snapshotArgv(fixture) {
    var root = String(Quickshell.env("TAMLINUX_COMPOSITOR_COMMANDS") || "")
    if (!safePath(root)) return []
    return ["/usr/bin/python3", "-I", root + "/sway_snapshot.py", fixture]
  }

  function finishFixture(text) {
    var body = String(text || "")
    if (body.length > monitorsLimit) {
      note("compositor-adapter sway fixture capped")
      return
    }
    try {
      var snapshot = JSON.parse(body)
      if (!snapshot || !snapshot.outputs) {
        note("compositor-adapter sway fixture failed")
        return
      }
      publishSnapshot(snapshot)
      note("compositor-adapter sway bindings bytes=" + String(snapshot.bindingsText || "").length)
      note("compositor-adapter sway keymap " + String(snapshot.activeKeymap || ""))
    } catch (e) {
      note("compositor-adapter sway fixture failed")
    }
  }

  function startFixture(fixture) {
    var argv = snapshotArgv(fixture)
    if (argv.length !== 4) {
      note("compositor-adapter sway fixture rejected")
      return
    }
    snapshotProc.command = argv
    snapshotProc.running = true
  }

  readonly property Process snapshotProc: Process {
    id: snapshotProc
    clearEnvironment: true
    environment: adapter.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: adapter.finishFixture(String(text || ""))
    }
    stderr: StdioCollector { waitForEnd: true }
    onStarted: snapshotTerm.restart()
    onExited: snapshotTerm.stop()
  }

  readonly property Timer snapshotTerm: Timer {
    interval: 4000
    onTriggered: snapshotProc.signal(15)
  }

  Component.onCompleted: {
    var fixture = String(Quickshell.env("TAMLINUX_SWAY_FIXTURE") || "")
    if (fixture !== "") {
      if (!safePath(fixture)) {
        note("compositor-adapter sway fixture rejected")
        return
      }
      startFixture(fixture)
      return
    }
    publishLive()
  }
}
