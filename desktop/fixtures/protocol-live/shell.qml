import QtQuick
import Quickshell
import "host" as Host
import "host/protocol_model.js" as Model

// No surfaces or mutations. The host receives the unchanged IPC snapshot.
ShellRoot {
  id: proof
  property var facade: QtObject {
    property var snapshot: null
    function applySnapshot(value) { snapshot = value }
    function applyKeyboards(list, typedName) {}
  }
  property var adapter: Host.HyprlandAdapter { host: proof.facade }
  property int attempts: 0
  Timer {
    interval: 1000; running: true; repeat: true
    onTriggered: {
      proof.attempts++
      var state = proof.adapter.protocolProof.item
      var facts = state ? state.snapshot : null
      var comparison = Model.compare(facts, proof.facade.snapshot)
      if (comparison.equal && proof.attempts >= 3) {
        console.log("PROTOCOL_LIVE_OK " + JSON.stringify(Model.comparable(facts)))
        Qt.quit()
      } else if (proof.attempts >= 10) {
        console.log("PROTOCOL_LIVE_FAILED " + JSON.stringify({ comparison: comparison,
          protocol: facts ? Model.comparable(facts) : null,
          problems: facts ? facts.problems : [],
          ipc: proof.facade.snapshot ? Model.comparable(proof.facade.snapshot) : null }))
        Qt.quit()
      }
    }
  }
}
