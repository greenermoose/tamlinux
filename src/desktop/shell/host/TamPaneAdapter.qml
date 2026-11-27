import QtQuick
import Quickshell
import Quickshell.Io
import "protocol_model.js" as ProtocolModel
import "tam_pane_model.js" as PaneModel

// tam-pane compositor adapter: standard Wayland facts come from ProtocolState,
// and missing state/actions/events use native Unix domain sockets to
// $TAM_PANE_SOCKET with automatic reconnection. No Hyprland imports or shells.
QtObject {
  id: adapter

  property var host: null
  // Optional override for tests; defaults to $TAM_PANE_SOCKET or
  // $XDG_RUNTIME_DIR/tam-pane/$WAYLAND_DISPLAY.sock.
  property string socketPathOverride: ""
  readonly property string socketPath: {
    if (socketPathOverride !== "") return socketPathOverride
    var explicit = Quickshell.env("TAM_PANE_SOCKET") || ""
    if (explicit !== "") return explicit
    var runtime = Quickshell.env("XDG_RUNTIME_DIR") || ""
    var wayland = Quickshell.env("WAYLAND_DISPLAY") || ""
    if (runtime === "" || wayland === "" || wayland.indexOf("/") !== -1) return ""
    return runtime.replace(/\/+$/, "") + "/tam-pane/" + wayland + ".sock"
  }

  readonly property var focusGrab: null
  readonly property bool liveActions: Quickshell.env("TAMLINUX_COMPOSITOR_LIVE_ACTIONS") === "1"

  // Standard Wayland outputs and ext-workspace-v1 tags (polled, never bound).
  readonly property ProtocolState protocolState: ProtocolState {
    perOutput: true
    allowMultipleActive: true
    onSnapshotChanged: adapter.publish()
  }

  property var monitorsState: []
  property var tagsState: ({})
  property var windowsState: []
  property string bindingsText: ""
  property string activeKeymap: ""
  property var keyboardsState: []
  property string typedKeyboardName: ""
  property string publishedKey: ""

  property bool eventSubscribed: false
  property int eventBackoffMs: 250
  property int rpcBackoffMs: 250
  property var rpcQueue: []
  property var activeRpc: null
  property int rpcBytes: 0
  readonly property int maxRpcBytes: 524288
  readonly property int maxBackoffMs: 2000

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function validName(name) {
    return PaneModel.validName(String(name || ""))
  }

  function validAppName(name) {
    return PaneModel.validAppName(String(name || ""))
  }

  function validTag(id) {
    return PaneModel.validTag(id)
  }

  function nextBackoff(current) {
    return Math.min(maxBackoffMs, Math.max(250, current * 2))
  }

  // ---- Facade actions ----

  function focusWorkspace(id, outputName) {
    if (!validTag(id)) {
      note("compositor-action rejected focus-workspace")
      return
    }
    var number = Number(id)
    var out = outputName ? String(outputName) : ""
    if (out !== "" && !validName(out)) {
      note("compositor-action rejected focus-workspace")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded focus-workspace " + number + (out ? " " + out : ""))
      return
    }
    note("compositor-action live focus-workspace " + number + (out ? " " + out : ""))
    if (out !== "" && protocolState.activate(number, out)) return
    enqueueRpc("dispatch tag view " + number + (out ? " " + out : ""), "dispatch")
  }

  function toggleWorkspace(id, outputName) {
    if (!validTag(id)) {
      note("compositor-action rejected toggle-workspace")
      return
    }
    var number = Number(id)
    var out = outputName ? String(outputName) : ""
    if (out !== "" && !validName(out)) {
      note("compositor-action rejected toggle-workspace")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded toggle-workspace " + number + (out ? " " + out : ""))
      return
    }
    note("compositor-action live toggle-workspace " + number + (out ? " " + out : ""))
    enqueueRpc("dispatch tag toggle_view " + number + (out ? " " + out : ""), "dispatch")
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
    enqueueRpc("dispatch monitor focus " + output, "dispatch")
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
    enqueueRpc("dispatch dpms " + word + " " + output, "set-dpms")
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
    enqueueRpc("dispatch focus_app " + app, "dispatch")
  }

  function switchKeyboardLayout(name) {
    var keyboard = String(name || "")
    if (keyboard !== "" && !validName(keyboard)) {
      note("compositor-action rejected switch-keyboard-layout")
      return
    }
    if (!liveActions) {
      note("compositor-action recorded switch-keyboard-layout " + keyboard)
      return
    }
    note("compositor-action live switch-keyboard-layout " + keyboard)
    enqueueRpc(keyboard ? ("dispatch keyboard next " + keyboard) : "dispatch keyboard next", "switch-keyboard-layout")
  }

  function requestPointerPosition(token) {
    enqueueRpc("cursor", "cursor", token)
  }

  function rereadMonitors() {
    enqueueRead("monitors")
  }

  function refreshKeyboards() {
    enqueueRead("keyboards")
  }

  function syncAll() {
    enqueueRead("monitors")
    enqueueRead("tags")
    enqueueRead("windows")
    enqueueRead("binds")
    enqueueRead("keyboards")
  }

  // ---- RPC queue over rpcSocket ----

  function enqueueRead(label) {
    // Coalesce duplicate pending read-only requests.
    for (var i = 0; i < rpcQueue.length; i++) {
      if (rpcQueue[i].label === label && rpcQueue[i].cmd === label) return
    }
    enqueueRpc(label, label, -1)
  }

  function enqueueRpc(cmd, label, token) {
    var next = rpcQueue.slice()
    next.push({ cmd: cmd, label: label, token: token === undefined ? -1 : token })
    rpcQueue = next
    pumpRpc()
  }

  function pumpRpc() {
    if (activeRpc || rpcQueue.length === 0) return
    if (!rpcSocket.connected) {
      if (socketPath !== "" && !rpcReconnectTimer.running) rpcReconnectTimer.start()
      return
    }
    var job = rpcQueue[0]
    rpcQueue = rpcQueue.slice(1)
    activeRpc = { cmd: job.cmd, label: job.label, token: job.token, sawOk: false, lines: [] }
    rpcBytes = 0
    rpcTimeout.restart()
    rpcSocket.write(job.cmd + "\n")
    rpcSocket.flush()
  }

  function finishRpc(ok, errMsg) {
    rpcTimeout.stop()
    var job = activeRpc
    activeRpc = null
    if (!job) return
    if (ok) {
      if (job.label === "monitors") {
        monitorsState = PaneModel.parseMonitors(job.lines)
        publish()
      } else if (job.label === "tags") {
        tagsState = PaneModel.parseTags(job.lines)
        publish()
      } else if (job.label === "windows") {
        windowsState = PaneModel.parseWindows(job.lines)
        publish()
      } else if (job.label === "binds") {
        bindingsText = PaneModel.parseBindsToJson(job.lines)
        publish()
      } else if (job.label === "keyboards") {
        var kb = PaneModel.parseKeyboards(job.lines)
        keyboardsState = kb.keyboards
        activeKeymap = kb.activeKeymap
        if (host && host.applyKeyboards) host.applyKeyboards(keyboardsState, typedKeyboardName)
        publish()
      } else if (job.label === "cursor") {
        if (host) host.pointerPositionReady(job.token, PaneModel.parseCursor(job.lines))
      } else if (job.label === "set-dpms") {
        enqueueRead("monitors")
      } else if (job.label === "switch-keyboard-layout") {
        enqueueRead("keyboards")
      }
    } else {
      note("compositor-adapter tam-pane rpc-error " + job.label + " " + String(errMsg || ""))
      if (job.label === "cursor" && host) host.pointerPositionReady(job.token, null)
    }
    pumpRpc()
  }

  function handleRpcLine(raw) {
    if (!activeRpc) return
    var line = String(raw || "").replace(/\r$/, "")
    if (!activeRpc.sawOk) {
      if (line === "OK") {
        activeRpc.sawOk = true
        return
      }
      if (line.indexOf("ERR ") === 0 || line === "ERR") {
        finishRpc(false, line.substring(4))
        return
      }
      finishRpc(false, "unexpected-reply")
      return
    }
    if (line === "END") {
      finishRpc(true, "")
      return
    }
    rpcBytes += line.length + 1
    if (rpcBytes <= maxRpcBytes) activeRpc.lines.push(line)
  }

  // ---- Event stream over eventSocket ----

  function handleEventLine(raw) {
    var line = String(raw || "").replace(/\r$/, "")
    if (!eventSubscribed) {
      if (line === "OK") {
        eventSubscribed = true
        note("compositor-adapter tam-pane subscribed")
      }
      return
    }
    var ev = PaneModel.parseLine(line)
    if (!ev || ev.kind !== "event") return
    var kind = ev.eventKind
    if (kind === "tag.change" || kind === "window.open" || kind === "window.close" ||
        kind === "window.focus" || kind === "window.change" || kind === "monitor.add" || kind === "monitor.remove" ||
        kind === "monitor.focus") {
      enqueueRead("monitors")
      enqueueRead("tags")
      enqueueRead("windows")
    } else if (kind === "output.power") {
      enqueueRead("monitors")
    } else if (kind === "keyboard.layout") {
      if (validName(ev.fields.name || "")) typedKeyboardName = ev.fields.name
      enqueueRead("keyboards")
    } else if (kind === "config.reload") {
      enqueueRead("binds")
      enqueueRead("keyboards")
      enqueueRead("monitors")
    }
  }

  // ---- Snapshot publication ----

  function publish() {
    if (!host) return
    var ipc = PaneModel.buildIpcSnapshot({
      monitors: monitorsState,
      tags: tagsState,
      windows: windowsState,
      bindingsText: bindingsText,
      activeKeymap: activeKeymap
    })
    var merged = ProtocolModel.combine(protocolState.snapshot, ipc, { perOutput: true })
    var key = JSON.stringify(merged)
    if (key === publishedKey) return
    publishedKey = key
    host.applySnapshot(merged)
  }

  // ---- Sockets & timers ----

  readonly property Socket eventSocket: Socket {
    path: adapter.socketPath
    connected: false
    parser: SplitParser {
      onRead: function(data) { adapter.handleEventLine(data) }
    }
    onError: function() {
      adapter.eventSubscribed = false
      if (adapter.socketPath !== "" && !adapter.eventReconnectTimer.running) {
        adapter.eventReconnectTimer.interval = adapter.eventBackoffMs
        adapter.eventBackoffMs = adapter.nextBackoff(adapter.eventBackoffMs)
        adapter.eventReconnectTimer.restart()
      }
    }
    onConnectionStateChanged: {
      if (connected) {
        adapter.eventBackoffMs = 250
        adapter.eventReconnectTimer.stop()
        adapter.eventSubscribed = false
        write("subscribe all\n")
        flush()
        adapter.syncAll()
      } else {
        adapter.eventSubscribed = false
        if (adapter.socketPath !== "") {
          adapter.eventReconnectTimer.interval = adapter.eventBackoffMs
          adapter.eventBackoffMs = adapter.nextBackoff(adapter.eventBackoffMs)
          adapter.eventReconnectTimer.restart()
        }
      }
    }
  }

  readonly property Timer eventReconnectTimer: Timer {
    interval: 250
    repeat: false
    onTriggered: {
      if (adapter.socketPath !== "" && !adapter.eventSocket.connected)
        adapter.eventSocket.connected = true
    }
  }

  readonly property Socket rpcSocket: Socket {
    path: adapter.socketPath
    connected: false
    parser: SplitParser {
      onRead: function(data) { adapter.handleRpcLine(data) }
    }
    onError: function() {
      if (adapter.socketPath !== "" && !adapter.rpcReconnectTimer.running) {
        adapter.rpcReconnectTimer.interval = adapter.rpcBackoffMs
        adapter.rpcBackoffMs = adapter.nextBackoff(adapter.rpcBackoffMs)
        adapter.rpcReconnectTimer.restart()
      }
    }
    onConnectionStateChanged: {
      if (connected) {
        adapter.rpcBackoffMs = 250
        adapter.rpcReconnectTimer.stop()
        adapter.pumpRpc()
      } else {
        if (adapter.activeRpc) {
          var dropped = adapter.activeRpc
          adapter.activeRpc = null
          adapter.rpcTimeout.stop()
          if (dropped.label === "cursor" && adapter.host) {
            adapter.host.pointerPositionReady(dropped.token, null)
          } else if (dropped.cmd === dropped.label) {
            adapter.enqueueRead(dropped.label)
          }
        }
        if (adapter.socketPath !== "") {
          adapter.rpcReconnectTimer.interval = adapter.rpcBackoffMs
          adapter.rpcBackoffMs = adapter.nextBackoff(adapter.rpcBackoffMs)
          adapter.rpcReconnectTimer.restart()
        }
      }
    }
  }

  readonly property Timer rpcReconnectTimer: Timer {
    interval: 250
    repeat: false
    onTriggered: {
      if (adapter.socketPath !== "" && !adapter.rpcSocket.connected)
        adapter.rpcSocket.connected = true
    }
  }

  readonly property Timer rpcTimeout: Timer {
    interval: 4000
    repeat: false
    onTriggered: {
      if (adapter.activeRpc) {
        adapter.note("compositor-adapter tam-pane rpc-timeout " + adapter.activeRpc.label)
        adapter.rpcSocket.connected = false
      }
    }
  }

  Component.onCompleted: {
    if (socketPath !== "") {
      eventSocket.connected = true
      rpcSocket.connected = true
      syncAll()
    }
  }
}
