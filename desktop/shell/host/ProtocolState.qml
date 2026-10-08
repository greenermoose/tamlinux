import QtQuick
import Quickshell
import Quickshell.WindowManager
import "protocol_model.js" as Model

// Bind the lazy models and all nested fields used by snapshot(). The binding
// tracks active/urgent/projection and screen geometry changes, not only lists.
QtObject {
  id: state
  property var windowsets: WindowManager.windowsets
  property var screens: Quickshell.screens
  readonly property var snapshot: Model.snapshot(windowsets, screens)

  function activate(number) {
    var id = Model.workspaceNumber(number)
    if (!id) return false
    for (var i = 0; i < windowsets.length && i < Model.listLimit; i++) {
      var set = windowsets[i]
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
    var screen = null
    for (var s = 0; s < screens.length && s < Model.listLimit; s++) {
      if (screens[s] && screens[s].name === outputName) screen = screens[s]
    }
    if (!screen) return false
    for (var i = 0; i < windowsets.length && i < Model.listLimit; i++) {
      var set = windowsets[i]
      if (!set || Model.workspaceNumber(set.name) !== id) continue
      if (!set.canSetProjection) return false
      var projection = WindowManager.screenProjection(screen)
      if (!projection) return false
      set.setProjection(projection)
      return true
    }
    return false
  }
}
