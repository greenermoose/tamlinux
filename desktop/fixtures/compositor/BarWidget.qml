import QtQuick

// Reads the shell compositor facade. This is not a fred.* plugin and it does
// not import a compositor module.
Item {
  id: root

  property var bar: null
  property var settings: null
  property string hostKey: ""
  property var screenRef: null
  property string moduleName: "tamlinux.compositor"

  implicitWidth: 8
  implicitHeight: 8

  function publish(line) {
    console.log("TAMLINUX_EVIDENCE " + line)
  }

  function uniqueSorted(values) {
    var found = []
    for (var i = 0; i < values.length; i++) {
      if (found.indexOf(values[i]) === -1) found.push(values[i])
    }
    found.sort(function(a, b) { return a - b })
    return found
  }

  function publishSnapshot() {
    var compositor = root.bar ? root.bar.compositor : null
    if (!compositor) {
      publish("compositor-fixture missing")
      return
    }
    var names = []
    var active = []
    var outputs = compositor.outputs || []
    for (var i = 0; i < outputs.length; i++) {
      if (!outputs[i]) continue
      names.push(String(outputs[i].name))
      if (outputs[i].activeWorkspaceId > 0) active.push(outputs[i].activeWorkspaceId)
    }
    var windows = 0
    var spaces = compositor.workspaces || []
    for (var w = 0; w < spaces.length; w++) {
      var listed = spaces[w] && spaces[w].windows ? spaces[w].windows.length : 0
      windows += listed
    }
    var screenName = root.screenRef ? String(root.screenRef.name || "") : ""
    var matched = compositor.outputForScreen(root.screenRef)
    publish("compositor-outputs " + names.join(","))
    publish("compositor-focused-output " + String(compositor.focusedOutputName || ""))
    publish("compositor-active-workspaces " + uniqueSorted(active).join(","))
    publish("compositor-bindings-bytes " + String((compositor.bindingsText || "").length))
    publish("compositor-keymap " + String(compositor.activeKeymap || ""))
    publish("compositor-windows " + windows)
    publish("compositor-screen-match " + (matched !== "" && matched === screenName ? "true" : "false"))
    publish("compositor-revision " + compositor.revision)
  }

  function bindHost() {
    publish("compositor-fixture loaded host=" + hostKey)
    publishSnapshot()
  }

  Connections {
    target: root.bar && root.bar.compositor ? root.bar.compositor : null
    function onRevisionChanged() { root.publishSnapshot() }
  }
}
