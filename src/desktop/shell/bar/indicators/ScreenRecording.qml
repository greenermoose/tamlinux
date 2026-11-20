// Ported from omarchy 4.0.4 shell/plugins/bar/indicators/ScreenRecording.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).
// Changes: owned module, id, and command names.

import QtQuick
import Quickshell.Io
import Tam.Commons
import Tam.Ui

BarIndicator {
  id: root

  property bool recording: false

  active: recording
  activeText: "󰻂"
  inactiveText: "󰻂"
  activeTooltipText: "Stop recording"
  inactiveTooltipText: "Screen Recording"

  function refresh() {
    if (!root.bar || statusProc.running) return
    statusProc.command = ["tam-capture-screenrecording", "--status"]
    statusProc.running = true
  }

  onBarChanged: refresh()
  Component.onCompleted: refresh()

  Connections {
    target: root.indicatorHost
    ignoreUnknownSignals: true
    function onRefreshRequested() { root.refresh() }
  }

  Process {
    environment: Util.hostEnvironment()
    id: statusProc
    onExited: function(exitCode) {
      root.recording = exitCode === 0
    }
  }

  onPressed: function() {
    if (root.bar) {
      root.bar.screenRecording(root.recording ? "stop" : "menu")
    }
  }
}
