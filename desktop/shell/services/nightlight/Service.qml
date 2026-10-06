import QtQuick
import Quickshell.Io

// Night light state for the bar's indicator. The owned command
// tam-toggle-nightlight is the only writer: this service reads its --status
// JSON and runs it to flip the state, so keybindings, the menu, and the bar
// agree. The compositor contract replaces the command's hyprsunset calls at
// plan 18 step 0.4.1; nothing here talks to the compositor.
//
// IPC target "nightlight": status, refresh, enable, disable, toggle.
Item {
  id: root

  property bool stateLoaded: false
  property var temperature: null
  property bool enabled: false
  // A request made while the command is still running: true, false, or null.
  property var pending: null

  function note(message) {
    console.log("TAMLINUX_EVIDENCE nightlight " + message)
  }

  function refresh() {
    if (!statusProcess.running) statusProcess.running = true
  }

  function ingestStatus(text) {
    var parsed = null
    try {
      parsed = JSON.parse(String(text || "").trim())
    } catch (e) {
      parsed = null
    }
    if (!parsed || typeof parsed.enabled !== "boolean") {
      note("status-unreadable")
      return
    }
    root.enabled = parsed.enabled
    root.temperature = typeof parsed.temperature === "number" && isFinite(parsed.temperature) ? parsed.temperature : null
    root.stateLoaded = true
  }

  function setNightlight(value) {
    var wanted = !!value
    if (toggleProcess.running) {
      root.pending = wanted
      return
    }
    if (root.stateLoaded && root.enabled === wanted) return
    root.enabled = wanted
    toggleProcess.running = true
  }

  function toggle() {
    setNightlight(!root.enabled)
  }

  Process {
    id: statusProcess
    command: ["bash", "-lc", 'exec "$@"', "bash", "tam-toggle-nightlight", "--status"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.ingestStatus(text)
    }
  }

  Process {
    id: toggleProcess
    command: ["bash", "-lc", 'exec "$@"', "bash", "tam-toggle-nightlight"]
    onExited: function(exitCode) {
      if (exitCode !== 0) root.note("toggle-failed " + exitCode)
      var next = root.pending
      root.pending = null
      root.refresh()
      if (next !== null && next !== root.enabled) Qt.callLater(function() { root.setNightlight(next) })
    }
  }

  Component.onCompleted: refresh()

  IpcHandler {
    target: "nightlight"

    function status(): string {
      return JSON.stringify({ enabled: root.enabled, temperature: root.temperature })
    }

    function refresh(): void {
      root.refresh()
    }

    function enable(): string {
      root.setNightlight(true)
      return "enabled"
    }

    function disable(): string {
      root.setNightlight(false)
      return "disabled"
    }

    function toggle(): string {
      var enabling = !root.enabled
      root.setNightlight(enabling)
      return enabling ? "enabled" : "disabled"
    }
  }
}
