import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import Tam.Commons as Commons

// Popup lifecycle base. The shell router owns IPC for every panel copy.
Item {
  id: root

  property QtObject bar: null
  property string moduleName: ""
  property var settings: ({})
  property alias controller: panelController
  property bool popoutSwitchClosing: false
  property bool popoutSwitching: false

  readonly property bool opened: panelController.open
  readonly property color barForeground: bar ? bar.barForeground : Commons.Color.foreground

  function open() { panelController.show() }
  function close() { panelController.hide() }
  function closeForPopoutSwitch() {
    popoutSwitchClosing = true
    close()
    Qt.callLater(function() { popoutSwitchClosing = false })
  }
  function toggle() { opened ? close() : open() }
  function switchPanel(direction) {
    if (bar && typeof bar.switchPanelFrom === "function") return bar.switchPanelFrom(root, direction)
    return false
  }

  function setting(name, fallback) {
    var value = settings ? settings[name] : undefined
    return value === undefined || value === null ? fallback : value
  }

  PanelController { id: panelController }

}
