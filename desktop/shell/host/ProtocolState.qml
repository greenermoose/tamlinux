import QtQuick
import Quickshell
import Quickshell.WindowManager
import "protocol_model.js" as Model

// Poll the protocol models; never bind to them. Quickshell commits an
// ext-workspace batch inside one Qt property update group. A QML binding over
// those bindable fields re-captures its observers during the group's
// notification pass, and Qt can then call a freed observer (2026-10-14 TTY1
// crashes). Plain reads in a timer handler register no observers.
QtObject {
  id: state
  // Fixtures assign lists here; null reads the live compositor models.
  property var windowsets: null
  property var screens: null
  property int pollInterval: 250
  property var snapshot: Model.snapshot([], [])
  property string snapshotKey: ""

  function currentSets() { return windowsets !== null ? windowsets : WindowManager.windowsets }
  function currentScreens() { return screens !== null ? screens : Quickshell.screens }

  // Publish only real changes so snapshotChanged keeps meaning "facts moved".
  function refresh() {
    var next = Model.snapshot(currentSets(), currentScreens())
    var key = JSON.stringify(next)
    if (key === snapshotKey) return
    snapshotKey = key
    snapshot = next
  }

  function activate(number) {
    var id = Model.workspaceNumber(number)
    if (!id) return false
    var sets = currentSets() || []
    for (var i = 0; i < sets.length && i < Model.listLimit; i++) {
      var set = sets[i]
      if (!set || Model.workspaceNumber(set.name) !== id) continue
      // Active workspaces commonly cannot activate; that is already success.
      if (set.active) return true
      if (!set.canActivate) return false
      set.activate()
      return true
    }
    return false
  }

  function assign(number, outputName) {
    var id = Model.workspaceNumber(number)
    if (!id || !Model.validName(outputName)) return false
    var outputs = currentScreens() || []
    var screen = null
    for (var s = 0; s < outputs.length && s < Model.listLimit; s++) {
      if (outputs[s] && outputs[s].name === outputName) screen = outputs[s]
    }
    if (!screen) return false
    var sets = currentSets() || []
    for (var i = 0; i < sets.length && i < Model.listLimit; i++) {
      var set = sets[i]
      if (!set || Model.workspaceNumber(set.name) !== id) continue
      if (!set.canSetProjection) return false
      var projection = WindowManager.screenProjection(screen)
      if (!projection) return false
      set.setProjection(projection)
      return true
    }
    return false
  }

  readonly property Timer poll: Timer {
    interval: state.pollInterval
    running: true
    repeat: true
    onTriggered: state.refresh()
  }
  Component.onCompleted: refresh()
}
