import QtQuick
import Quickshell.Io
import "MenuModel.js" as MenuModel

Item {
  id: source
  property string path
  property bool optional: false
  property var items: []
  property bool ready: false
  property bool valid: false
  property bool hasFile: false
  property string error: ""
  property bool pending: false
  property string collected: ""
  signal updated()

  function reload() { pending = true; debounce.restart() }
  onPathChanged: reload()
  Component.onCompleted: reload()

  // Watching alone must not read the unbounded file into Quickshell.
  FileView {
    path: source.path
    preload: false
    watchChanges: true
    printErrors: false
    onFileChanged: source.reload()
  }
  Timer {
    id: debounce
    interval: 75
    onTriggered: {
      if (reader.running) return
      source.pending = false
      source.collected = ""
      reader.readPath = source.path
      reader.command = ["timeout", "--signal=KILL", "2", "python3", "-I", decodeURIComponent(Qt.resolvedUrl("read-menu.py").toString().replace(/^file:\/\//, "")), reader.readPath]
      reader.running = true
    }
  }
  Process {
    id: reader
    property string readPath: ""
    stdout: StdioCollector { onStreamFinished: source.collected = text }
    onExited: function(code, status) {
      if (reader.readPath !== source.path) { source.reload(); return }
      var changed = false
      try {
        if (status !== 0 || (code !== 0 && !(code === 3 && source.optional && !source.hasFile)))
          throw new Error("menu read failed (" + code + ")")
        var candidate = MenuModel.parseMenuJsonc(code === 3 ? "{}" : source.collected)
        source.items = candidate
        source.valid = true
        if (code === 0) source.hasFile = true
        source.error = ""
        changed = true
      } catch (e) {
        source.error = String(e)
        console.warn("Tamlinux menu: retaining last valid source; " + source.error)
      }
      var first = !source.ready
      source.ready = true
      if (changed || first) source.updated()
      if (source.pending) debounce.restart()
    }
  }
}
