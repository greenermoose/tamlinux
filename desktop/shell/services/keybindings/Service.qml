// Keybinding viewer rows for tam-menu-keybindings. The rows come from the
// compositor facade's bindings; the caller passes the command table it
// scanned from the Lua config, since the facade does not know what a Lua
// bind runs. The menu shows the rows and the caller runs the chosen one.

import QtQuick
import Quickshell
import Quickshell.Io
import "KeybindingsModel.js" as Model

Item {
  id: root

  property var shell: null

  function bindingsText() {
    return root.shell && root.shell.compositor ? String(root.shell.compositor.bindingsText || "") : ""
  }

  IpcHandler {
    target: "keybindings"
    function records(commands: string): string {
      return Model.formatRecords(Model.records(root.bindingsText(), commands))
    }
    function ping(): string { return "ok" }
  }
}
