// Battery service for the Tamlinux host: warns once when the battery runs
// low while draining, and switches the power profile when the machine moves
// between battery and mains power. Without a battery it does nothing.
//
// Vendored from omarchy 4.0.4 shell/plugins/services/battery/Service.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy).
// Changes:
// - The warning runs tam-battery-low <level> and the profile switch runs
//   tam-powerprofiles-set <battery|ac>.
// - IPC target battery (new): status (JSON) and ping. Nothing over IPC can
//   send a warning or change the profile.

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import "BatteryModel.js" as BatteryModel

Item {
  id: root

  readonly property int batteryThreshold: 10
  property string pendingPowerSource: ""

  PersistentProperties {
    id: persisted
    reloadableId: "tamlinux-battery"
    property bool notifiedLowBattery: false
  }

  function checkBattery() {
    var state = BatteryModel.shouldWarnLowBattery(UPower.displayDevice, UPower.onBattery, UPowerDeviceState.Discharging, batteryThreshold, persisted.notifiedLowBattery)
    persisted.notifiedLowBattery = state.notifiedLowBattery
    if (state.notify) sendLowBatteryWarning(state.level)
  }

  function sendLowBatteryWarning(level) {
    if (warningProcess.running) return
    warningProcess.command = ["tam-battery-low", String(level)]
    warningProcess.running = true
  }

  function applyPowerProfile() {
    pendingPowerSource = BatteryModel.powerSource(UPower.onBattery)
    if (!powerProfileProcess.running) runPendingPowerProfile()
  }

  function runPendingPowerProfile() {
    powerProfileProcess.command = ["tam-powerprofiles-set", pendingPowerSource]
    pendingPowerSource = ""
    powerProfileProcess.running = true
  }

  function statusJson() {
    return JSON.stringify(BatteryModel.statusOf(UPower.displayDevice, UPower.onBattery, UPowerDeviceState.Discharging, batteryThreshold, persisted.notifiedLowBattery))
  }

  Process { id: warningProcess }

  Process {
    id: powerProfileProcess
    onExited: if (root.pendingPowerSource !== "") root.runPendingPowerProfile()
  }

  Timer {
    interval: 30000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.checkBattery()
  }

  Connections {
    target: UPower
    function onOnBatteryChanged() {
      root.checkBattery()
      root.applyPowerProfile()
    }
  }

  IpcHandler {
    target: "battery"

    function status(): string {
      return root.statusJson()
    }

    function ping(): string {
      return "pong"
    }
  }
}
