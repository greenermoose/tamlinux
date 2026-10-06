import QtQuick
import Quickshell

// Compositor-neutral state for one shell. Widgets read this object.
// Hyprland stays in HyprlandAdapter.qml. Sway stays in SwayAdapter.qml.
// The unselected file is not loaded.
QtObject {
  id: facade

  property var outputs: []
  property string focusedOutputName: ""
  property var workspaces: []
  property int focusedWorkspaceId: 0
  property string bindingsText: ""
  property string activeKeymap: ""
  // Keyboards on the seat, { name, layout, activeKeymap, activeLayoutIndex,
  // main }, and the one the last layout switch named as typed on.
  property var keyboards: []
  property string typedKeyboardName: ""
  property int revision: 0
  property var backend: null
  // A component the bar's popups instantiate to close on an outside click,
  // or null when the compositor has no focus grab (Sway).
  readonly property var focusGrab: backend && backend.focusGrab ? backend.focusGrab : null

  readonly property string backendName: {
    var name = String(Quickshell.env("TAMLINUX_COMPOSITOR") || "hyprland")
    return name === "sway" ? "sway" : "hyprland"
  }

  function outputForScreen(screen) {
    if (!screen || !screen.name) return ""
    var name = String(screen.name)
    for (var i = 0; i < outputs.length; i++) {
      if (outputs[i] && outputs[i].name === name) return name
    }
    return ""
  }

  function focusWorkspace(id) {
    if (backend) backend.focusWorkspace(id)
  }

  function focusOutput(name) {
    if (backend) backend.focusOutput(name)
  }

  function setDpms(name, on) {
    if (backend) backend.setDpms(name, on)
  }

  function focusApp(name) {
    if (backend) backend.focusApp(name)
  }

  function refreshKeyboards() {
    if (backend && backend.refreshKeyboards) backend.refreshKeyboards()
  }

  // Advance the named keyboard to its next layout.
  function switchKeyboardLayout(name) {
    if (backend && backend.switchKeyboardLayout) backend.switchKeyboardLayout(name)
  }

  function applyKeyboards(list, typedName) {
    keyboards = list
    typedKeyboardName = typedName
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

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function finishBackend(component) {
    var object = component.createObject(null, { host: facade })
    if (!object) {
      note("compositor-backend failed")
      return
    }
    backend = object
    note("compositor-backend " + backendName)
  }

  function loadBackend() {
    var file = backendName === "sway" ? "SwayAdapter.qml" : "HyprlandAdapter.qml"
    var component = Qt.createComponent(Qt.resolvedUrl(file))
    if (component.status === Component.Ready) {
      finishBackend(component)
      return
    }
    if (component.status === Component.Loading) {
      component.statusChanged.connect(function() {
        if (component.status === Component.Ready) finishBackend(component)
        else if (component.status === Component.Error) note("compositor-backend failed")
      })
      return
    }
    note("compositor-backend failed")
  }

  Component.onCompleted: loadBackend()
  Component.onDestruction: {
    if (backend) backend.destroy()
  }
}
