import QtQuick
import Quickshell
import "host" as Host

ShellRoot {
  id: test
  property int step: 0
  property var protocol: null
  property var ipc: null
  property var logger: Host.ProtocolShadow {
    enabled: false
    protocolSnapshot: test.protocol
    ipcSnapshot: test.ipc
    settleMs: 35
    heartbeatMs: 120
    identity: "a".repeat(64)
    revision: "b".repeat(40)
  }
  function state(owner, ready) {
    return { ready: ready, problems: [],
      outputs: [{ name: "DP-1", x: 0, y: 0, activeWorkspaceId: 1 }],
      workspaces: [{ id: 1, output: owner }] }
  }
  function check(ok, message) {
    if (!ok) throw new Error("SHADOW_FIXTURE_FAILED " + message)
  }
  Timer {
    interval: 70; running: true; repeat: true
    onTriggered: {
      try {
        if (test.step === 0) {
          check(test.logger.sequence === 0, "disabled logger is silent")
          test.protocol = test.state("DP-1", true)
          test.ipc = test.state("DP-1", true)
          test.logger.enabled = true
          check(test.logger.sequence === 0, "changes wait for settling")
        } else if (test.step === 1) {
          check(test.logger.sequence === 1 && test.logger.lastStatus.indexOf("equal") >= 0, "first settled equality")
          // A burst changes both sources, then ends in agreement before settle.
          test.protocol = test.state("DP-2", true)
          test.ipc = test.state("DP-2", true)
          test.protocol = test.state("DP-1", true)
          test.ipc = test.state("DP-1", true)
        } else if (test.step === 2) {
          check(test.logger.lastStatus.indexOf("equal") >= 0, "burst has no false difference")
          test.protocol = test.state("DP-2", true)
        } else if (test.step === 3) {
          check(test.logger.lastStatus.indexOf("different") >= 0, "persistent mismatch is recorded")
          test.ipc = test.state("DP-2", true)
        } else if (test.step === 4) {
          check(test.logger.lastStatus.indexOf("equal") >= 0, "recovery is recorded")
          test.protocol = test.state("DP-2", false)
        } else if (test.step === 5) {
          check(test.logger.lastStatus.indexOf("unready") >= 0, "loss of readiness is recorded")
          test.logger.enabled = false
          test.step = test.logger.sequence + 100
          return
        } else {
          check(test.logger.sequence === test.step - 100, "disable stops heartbeats")
          console.log("SHADOW_FIXTURE_OK")
          Qt.quit()
        }
        test.step++
      } catch (error) { console.log(String(error)); Qt.quit() }
    }
  }
}
