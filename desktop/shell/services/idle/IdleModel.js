// Pure helpers for the idle service: timeout parsing, the idle-cycle plan,
// and the screensaver window count.
//
// Ported from omarchy 4.0.4 shell/plugins/services/idle/IdleModel.js (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changes:
// a timeout of 0, a negative or non-numeric value, or no value means off
// (the source fell back to a default, and read 0 as at once), and a timeout
// is capped where a QML Timer interval would overflow; cyclePlan() works out
// the stages from the two timeouts; and the screensaver windows are counted
// from Wayland toplevel app ids in place of compositor window events.

// QML Timer.interval is a signed 32-bit count of milliseconds.
var maxTimeoutSeconds = 2147483

function secondsFromConfig(value) {
  if (value === undefined || value === null || String(value).trim() === "") return 0
  var n = Number(value)
  if (!isFinite(n) || n <= 0) return 0
  return Math.min(Math.floor(n), maxTimeoutSeconds)
}

// Stages run from the moment the session goes idle. The idle monitor fires at
// the earlier enabled timeout; each stage's delay is counted from then. A
// delay of -1 means that stage is off. Both off: no idle cycle at all.
function cyclePlan(screensaverSeconds, lockSeconds) {
  var screensaver = secondsFromConfig(screensaverSeconds)
  var lock = secondsFromConfig(lockSeconds)
  if (screensaver === 0 && lock === 0)
    return { enabled: false, first: 0, screensaverDelay: -1, lockDelay: -1 }
  var first = screensaver === 0 ? lock : (lock === 0 ? screensaver : Math.min(screensaver, lock))
  return {
    enabled: true,
    first: first,
    screensaverDelay: screensaver === 0 ? -1 : screensaver - first,
    lockDelay: lock === 0 ? -1 : lock - first
  }
}

function screensaverWindowCount(appIds, appId) {
  var wanted = String(appId || "")
  if (wanted === "") return 0
  var count = 0
  for (var i = 0; i < (appIds || []).length; i++) {
    if (String(appIds[i] || "") === wanted) count++
  }
  return count
}

if (typeof module !== "undefined") {
  module.exports = {
    maxTimeoutSeconds: maxTimeoutSeconds,
    secondsFromConfig: secondsFromConfig,
    cyclePlan: cyclePlan,
    screensaverWindowCount: screensaverWindowCount
  }
}
