import QtQuick
import Quickshell
import "protocol_model.js" as Model

// Observation only. This object has no facade, dispatcher, or Process.
QtObject {
  id: shadow
  property var protocolSnapshot: null
  property var ipcSnapshot: null
  property bool enabled: false
  property string identity: Quickshell.env("TAMLINUX_PROTOCOL_SHADOW_ID") || "development"
  property string revision: Quickshell.env("TAMLINUX_SHELL_REVISION") || "development"
  property int settleMs: 750
  property int heartbeatMs: 60000
  property int sequence: 0
  property int comparisons: 0
  property string lastStatus: ""
  property string observedKey: ""
  readonly property string factsKey: JSON.stringify({
    protocol: protocolSnapshot ? Model.comparable(protocolSnapshot) : null,
    ready: protocolSnapshot ? protocolSnapshot.ready : false,
    problems: protocolSnapshot ? protocolSnapshot.problems : [],
    ipc: ipcSnapshot ? Model.comparable(ipcSnapshot) : null
  })

  function changed() {
    if (!enabled || factsKey === observedKey) return
    observedKey = factsKey
    settle.restart()
  }

  function sample(heartbeat) {
    if (!enabled) return
    var comparison = Model.compare(protocolSnapshot, ipcSnapshot)
    var status = settle.running ? "settling"
      : comparison.equal ? "equal"
      : comparison.differences[0] === "not-ready" ? "unready" : "different"
    if (status !== "settling") comparisons++
    var problems = protocolSnapshot && protocolSnapshot.problems ? protocolSnapshot.problems : []
    // Reasons are closed, short identifiers; never log window/user content.
    var bounded = problems.slice(0, 8).map(function(reason) {
      return /^[a-z-]{1,40}$/.test(String(reason)) ? String(reason) : "invalid-reason"
    })
    var key = JSON.stringify([status, comparison.differences, bounded])
    // Settling limits comparisons to at most one per 750 ms; unchanged
    // states produce only the once-a-minute health record.
    if (!heartbeat && key === lastStatus) return
    lastStatus = key
    sequence++
    console.log("TAMLINUX_EVIDENCE protocol-shadow " + JSON.stringify({
      schema: 1,
      identity: /^[0-9a-f]{64}$/.test(identity) ? identity : "development",
      revision: /^[0-9a-f]{40}$/.test(revision) ? revision : "development",
      sequence: sequence, comparisons: comparisons, status: status,
      differences: status === "settling" ? [] : comparison.differences,
      problems: bounded,
      outputs: protocolSnapshot ? Math.min(64, protocolSnapshot.outputs.length) : 0,
      workspaces: protocolSnapshot ? Math.min(64, protocolSnapshot.workspaces.length) : 0
    }))
  }

  onFactsKeyChanged: changed()
  onEnabledChanged: { if (enabled) { observedKey = ""; changed() } }
  readonly property Timer settle: Timer {
    interval: shadow.settleMs
    onTriggered: shadow.sample(false)
  }
  readonly property Timer heartbeat: Timer {
    interval: shadow.heartbeatMs
    running: shadow.enabled
    repeat: true
    onTriggered: shadow.sample(true)
  }
  Component.onCompleted: changed()
}
