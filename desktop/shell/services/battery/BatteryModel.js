// Pure helpers for the battery service: the charge level, whether the
// battery is draining, and when to warn that it is low.
//
// Vendored from omarchy 4.0.4 shell/plugins/services/battery/BatteryModel.js
// (MIT, Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy).
// Changes: powerSource() names the profile key ("battery" or "ac") for the
// power-source change, and statusOf() builds the IPC status.

function batteryPercentage(device) {
  if (!device || !device.isPresent) return -1
  return Math.round(Number(device.percentage || 0) * 100)
}

function isDischarging(device, onBattery, dischargingState) {
  return !!(device && device.isPresent && onBattery && device.state === dischargingState)
}

function shouldWarnLowBattery(device, onBattery, dischargingState, threshold, alreadyNotified) {
  var level = batteryPercentage(device)
  if (level < 0) return { level: level, notify: false, notifiedLowBattery: false }

  var low = isDischarging(device, onBattery, dischargingState) && level <= threshold
  return {
    level: level,
    notify: low && !alreadyNotified,
    notifiedLowBattery: low
  }
}

function powerSource(onBattery) {
  return onBattery ? "battery" : "ac"
}

function statusOf(device, onBattery, dischargingState, threshold, notified) {
  var level = batteryPercentage(device)
  return {
    present: level >= 0,
    level: level,
    onBattery: !!onBattery,
    discharging: isDischarging(device, onBattery, dischargingState),
    threshold: threshold,
    warned: !!notified
  }
}

if (typeof module !== "undefined") {
  module.exports = {
    batteryPercentage: batteryPercentage,
    isDischarging: isDischarging,
    shouldWarnLowBattery: shouldWarnLowBattery,
    powerSource: powerSource,
    statusOf: statusOf
  }
}
