// The explorer combines the compositor's live bindings with the command
// table scanned by tam-menu-keybindings. Selecting a row never dispatches it.

import QtQuick
import Quickshell
import Quickshell.Io
import "KeybindingsModel.js" as Model

Item {
  id: root

  property var shell: null
  property bool opened: false
  property var rows: []

  function open(commands) {
    rows = Model.explorerRecords(bindingsText(), commands)
    opened = true
  }

  Explorer {
    visible: root.opened
    rows: root.rows
    onClosed: root.opened = false
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
