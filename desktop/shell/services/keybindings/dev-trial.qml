// Development trial of the keybinding explorer (D198): the explorer as its own
// Quickshell instance. It reads the binds and the command table itself, never
// talks to the installed shell, and quits when the explorer closes. Neither a
// selected row nor a captured shortcut is run.

import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import "KeybindingsModel.js" as Model
import "BindingCatalog.js" as Catalog

ShellRoot {
  id: root

  readonly property int bindsLimit: 262144
  property string bindsText: ""
  property string commandsText: ""
  property int pending: 3
  property var customCatalog: []
  property var rows: []

  function loaded() {
    pending -= 1
    if (pending > 0) return
    rows = Model.explorerRecords(bindsText, commandsText, false, customCatalog.concat(Catalog.entries))
    explorer.visible = true
  }

  Process {
    environment: Util.hostEnvironment()
    running: true
    command: ["/usr/bin/hyprctl", "binds"]
    stdout: StdioCollector {
      onStreamFinished: { root.bindsText = text.length > root.bindsLimit ? "" : text; root.loaded() }
    }
  }

  Process {
    environment: Util.hostEnvironment()
    running: true
    command: [Quickshell.env("TAMLINUX_KEYBINDINGS_SCAN") || "tam-menu-keybindings", "--scan"]
    stdout: StdioCollector {
      onStreamFinished: { root.commandsText = text; root.loaded() }
    }
  }

  FileView {
    path: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/tamlinux/keybindings-metadata.json"
    printErrors: false
    onLoaded: { root.customCatalog = Model.parseCatalog(text()); root.loaded() }
    onLoadFailed: { root.customCatalog = []; root.loaded() }
  }

  Explorer {
    id: explorer
    visible: false
    rows: root.rows
    bindingsAvailable: Model.parseBinds(root.bindsText).length > 0
    onDismissRequested: Qt.quit()
  }
}
