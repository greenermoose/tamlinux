import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import Tam.Ui
import "."

BarWidget {
  id: root
  moduleName: "fred.tides"

  readonly property string pluginVersion: "2.0.2"
  // Tamlinux's own commands, by absolute path: TAMLINUX_BIN, else ~/.local/bin.
  readonly property string notificationHelper:
    (Quickshell.env("TAMLINUX_BIN") || (Quickshell.env("HOME") + "/.local/bin")) + "/tam-notification-send"

  Process {
    id: notificationProc
    clearEnvironment: true
    environment: ({
      "PATH": "/usr/bin:/bin",
      "HOME": Quickshell.env("HOME") || "",
      "XDG_RUNTIME_DIR": Quickshell.env("XDG_RUNTIME_DIR") || "",
      "WAYLAND_DISPLAY": Quickshell.env("WAYLAND_DISPLAY") || "",
      "DBUS_SESSION_BUS_ADDRESS": Quickshell.env("DBUS_SESSION_BUS_ADDRESS") || ""
    })
    readonly property Timer watchdog: Timer {
      interval: 10000
      onTriggered: notificationProc.signal(9)
    }
    onStarted: watchdog.restart()
    onExited: watchdog.stop()
  }

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
    if ("pluginVersion" in target) target.pluginVersion = root.pluginVersion
  }

  function refresh() {
    if (panelLoader.item && panelLoader.item.refresh) panelLoader.item.refresh()
  }

  function togglePanel() {
    if (panelLoader.item && panelLoader.item.toggle) panelLoader.item.toggle()
  }

  function toggle() {
    togglePanel()
  }

  // Shape contract for shell.summon/hide/toggle routing
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false

  function open() {
    if (panelLoader.item && panelLoader.item.openFromHotkey) panelLoader.item.openFromHotkey()
  }

  function close() {
    if (panelLoader.item && panelLoader.item.close) panelLoader.item.close()
  }

  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function closeForPopoutSwitch() {
    if (panelLoader.item) panelLoader.item.closeForPopoutSwitch()
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: panelLoader.item && panelLoader.item.label ? panelLoader.item.label : "\udb81\udf8d"
    slotSize: Style.bar.statusSlot
    tooltipText: {
      var lines = (panelLoader.item && panelLoader.item.hoverLines) ? panelLoader.item.hoverLines.slice() : ["Tides"]
      lines.push("", "fred.tides v" + root.pluginVersion)
      return lines.join("\n")
    }

    onPressed: function(b) {
      if (!root.bar) return
      if (b === Qt.RightButton) {
        if (panelLoader.item && panelLoader.item.statusSummary && root.notificationHelper !== "" && !notificationProc.running) {
          notificationProc.command = [root.notificationHelper, "Tides", String(panelLoader.item.statusSummary).slice(0, 4096)]
          notificationProc.running = true
        }
      } else if (b === Qt.MiddleButton) {
        root.refresh()
      } else {
        root.togglePanel()
      }
    }
  }
}
