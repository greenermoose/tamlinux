import QtQuick
import Quickshell.Io

// Typed host actions. The proof leaves TAMLINUX_HOST_ACTIONS unset, so this
// object is not asked to start anything. A daily bar sets that variable.
QtObject {
  id: root

  signal refused()
  signal started(string path)

  function launch(argv, deadline, env) {
    if (!argv || argv.length < 1) return false
    if (String(argv[0]).indexOf("/") !== 0) return false
    if (actionProc.running) {
      refused()
      return false
    }
    actionProc.command = argv
    actionProc.environment = env
    actionProc.deadlineMs = deadline
    actionProc.running = true
    started(String(argv[0]))
    return true
  }

  readonly property Process actionProc: Process {
    clearEnvironment: true
    property int deadlineMs: 15000
    onStarted: actionWatch.restart()
    onExited: {
      actionWatch.stop()
      actionKill.stop()
    }
    readonly property Timer actionWatch: Timer {
      interval: actionProc.deadlineMs
      onTriggered: {
        actionProc.signal(15)
        actionKill.restart()
      }
    }
    readonly property Timer actionKill: Timer {
      interval: 3000
      onTriggered: actionProc.signal(9)
    }
  }
}
