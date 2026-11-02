// Run the actual keyboard widget as an independent development application.
// The small bar facade supplies read-only compositor state and local popup
// coordination; this instance never calls or replaces the installed shell.
import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import Tam.Commons as Commons
import "Device.js" as Device
import "."

ShellRoot {
  id: app
  readonly property bool checking: Quickshell.env("TAMLINUX_KEYBOARD_CHECK") === "1"
  property int pending: 2
  property bool started: false
  readonly property var keyboard: widgetLoader.item
  readonly property var processEnv: ["HOME", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY",
                                     "HYPRLAND_INSTANCE_SIGNATURE"]

  property QtObject compositor: QtObject {
    property string activeKeymap: ""
    property string bindingsText: ""
    property int revision: 0
  }

  property QtObject standaloneBar: QtObject {
    property var compositor: app.compositor
    property string position: "top"
    property bool vertical: false
    property int barSize: 0
    property string fontFamily: Style.font.family
    property color barForeground: Commons.Color.foreground
    property color foreground: Commons.Color.foreground
    property var activePopout: null
    property var clickTargets: []
    function requestPopout(owner) { activePopout = owner }
    function releasePopout(owner) { if (activePopout === owner) activePopout = null }
  }

  function loaded() {
    pending -= 1
    compositor.revision += 1
  }

  Launch {
    exe: "/usr/bin/hyprctl"
    args: ["binds"]
    envKeys: app.processEnv
    deadlineMs: 4000
    Component.onCompleted: launch()
    stdout: StdioCollector {
      onStreamFinished: {
        app.compositor.bindingsText = text.length <= 262144 ? text : ""
      }
    }
    onExited: app.loaded()
  }

  Launch {
    exe: "/usr/bin/hyprctl"
    args: ["-j", "devices"]
    envKeys: app.processEnv
    deadlineMs: 4000
    Component.onCompleted: launch()
    stdout: StdioCollector {
      onStreamFinished: {
        if (text.length <= 262144) app.compositor.activeKeymap = Device.activeKeymap(text)
      }
    }
    onExited: app.loaded()
  }

  Loader {
    id: widgetLoader
    source: "BarWidget.qml"
    onLoaded: item.bar = app.standaloneBar
  }

  Connections {
    target: app.keyboard
    function onOpenedChanged() {
      if (app.started && !app.keyboard.opened) quitTimer.start()
    }
  }

  Timer {
    interval: 50
    repeat: true
    running: !app.started
    property int attempts: 0
    onTriggered: {
      attempts += 1
      if (attempts < 120 && (app.pending > 0 || !app.keyboard || !app.keyboard.layout)) return
      app.started = true
      if (app.checking) {
        console.log("KEYBOARD_APP_CHECK " + JSON.stringify({
          layout: keyboard.layout ? keyboard.layout.id : null,
          rows: keyboard.layout ? keyboard.layout.rows.length : 0,
          bindings: keyboard.binds.length,
          device: keyboard.device ? keyboard.device.name : null,
          keymap: keyboard.keymap,
          error: keyboard.loadError
        }))
        Qt.quit()
      } else {
        keyboard.open()
      }
    }
  }

  Timer { id: quitTimer; interval: 180; onTriggered: Qt.quit() }
}
