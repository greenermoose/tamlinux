import QtQuick

// Compositor-neutral state for one shell. Widgets read this object.
// Hyprland stays in HyprlandAdapter.qml.
QtObject {
  id: facade

  property var outputs: []
  property string focusedOutputName: ""
  property var workspaces: []
  property int focusedWorkspaceId: 0
  property string bindingsText: ""
  property string activeKeymap: ""
  property int revision: 0

  function outputForScreen(screen) {
    if (!screen || !screen.name) return ""
    var name = String(screen.name)
    for (var i = 0; i < outputs.length; i++) {
      if (outputs[i] && outputs[i].name === name) return name
    }
    return ""
  }

  function focusWorkspace(id) { backend.focusWorkspace(id) }
  function focusOutput(name) { backend.focusOutput(name) }
  function setDpms(name, on) { backend.setDpms(name, on) }

  readonly property HyprlandAdapter backend: HyprlandAdapter {
    host: facade
  }

  function applySnapshot(snapshot) {
    outputs = snapshot.outputs
    focusedOutputName = snapshot.focusedOutputName
    workspaces = snapshot.workspaces
    focusedWorkspaceId = snapshot.focusedWorkspaceId
    bindingsText = snapshot.bindingsText
    activeKeymap = snapshot.activeKeymap
    revision = revision + 1
  }
}
