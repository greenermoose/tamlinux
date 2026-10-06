// Load a validated palette into the shared tokens, once at startup and on
// explicit theme changes. No polling, compositor calls, or shell restart.
import QtQuick
import Quickshell.Io
import Tam.Commons

Item {
  id: root
  property bool reloadPending: false
  property bool busy: false
  property bool streamDone: false
  property bool processDone: false
  property int processExitCode: -1
  property string output: ""

  function reloadTheme() {
    if (root.busy) {
      root.reloadPending = true
      return
    }
    root.busy = true
    root.streamDone = false
    root.processDone = false
    root.processExitCode = -1
    root.output = ""
    reader.running = true
  }

  function finishRead() {
    // A helper can close stdout before exiting. Neither an incomplete read
    // nor output from a failed/timed-out process may change the palette.
    if (!root.busy || !root.streamDone || !root.processDone) return
    if (root.processExitCode === 0) {
      try {
        var payload = JSON.parse(root.output)
        if (Color.applyPayload(payload)) {
          Style.applyThemeStyle(payload.style)
          console.log("TAMLINUX_EVIDENCE theme-loaded " + Color.background)
        } else console.warn("Tamlinux theme payload is invalid")
      } catch (error) {
        console.warn("Tamlinux theme payload could not be read")
      }
    } else console.warn("Tamlinux theme reader failed: " + root.processExitCode)
    root.busy = false
    root.output = ""
    if (root.reloadPending) {
      root.reloadPending = false
      Qt.callLater(root.reloadTheme)
    }
  }

  Process {
    id: reader
    command: ["/usr/bin/timeout", "--kill-after=1s", "3s", "tam-theme-payload"]
    stdout: StdioCollector {
      onStreamFinished: {
        root.output = text
        root.streamDone = true
        root.finishRead()
      }
    }
    onExited: function(exitCode, exitStatus) {
      root.processExitCode = exitCode
      root.processDone = true
      root.finishRead()
    }
  }

  IpcHandler {
    target: "theme"
    function reload(): void { root.reloadTheme() }
    function current(): string {
      return JSON.stringify({foreground: String(Color.foreground), background: String(Color.background),
        accent: String(Color.accent), muted: String(Color.muted), fontFamily: Style.font.family,
        fontBaseSize: Style.font.baseSize})
    }
  }

  Component.onCompleted: reloadTheme()
}
