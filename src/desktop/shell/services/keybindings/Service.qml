// The explorer combines the compositor's live bindings with the command
// table scanned by tam-menu-keybindings. Selecting a row never dispatches it.

import QtQuick
import Quickshell
import Quickshell.Io
import "KeybindingsModel.js" as Model
import "BindingCatalog.js" as Catalog

Item {
  id: root

  property var shell: null
  property bool opened: false
  property var rows: []
  property bool bindingsAvailable: false
  property var customCatalog: []

  function open(commands) {
    var text = bindingsText()
    bindingsAvailable = Model.parseBinds(text).length > 0
    rows = Model.explorerRecords(text, commands, false, root.customCatalog.concat(Catalog.entries))
    opened = true
  }

  FileView {
    path: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/tamlinux/keybindings-metadata.json"
    printErrors: false
    watchChanges: true
    onLoaded: root.customCatalog = Model.parseCatalog(text())
    onLoadFailed: root.customCatalog = []
    onFileChanged: reload()
  }

  Explorer {
    visible: root.opened
    rows: root.rows
    bindingsAvailable: root.bindingsAvailable
    onDismissRequested: root.opened = false
  }

  function bindingsText() {
    return root.shell && root.shell.compositor ? String(root.shell.compositor.bindingsText || "") : ""
  }

  IpcHandler {
    target: "keybindings"
    function open(commands: string): string { root.open(commands); return "ok" }
    function records(commands: string): string {
      return Model.formatRecords(Model.records(root.bindingsText(), commands))
    }
    function ping(): string { return "ok" }
  }
}
