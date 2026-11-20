// Idle timeout parsing. Ported from omarchy (MIT; see ../LICENSE-omarchy).

// QML Timer.interval is a signed 32-bit count of milliseconds.
var maxTimeoutSeconds = 2147483

function secondsFromConfig(value) {
  if (value === undefined || value === null || String(value).trim() === "") return 0
  var n = Number(value)
  if (!isFinite(n) || n <= 0) return 0
  return Math.min(Math.floor(n), maxTimeoutSeconds)
}

// The monitor fires at the configured lock deadline; zero disables it.
function cyclePlan(lockSeconds) {
  var lock = secondsFromConfig(lockSeconds)
  return { enabled: lock > 0, first: lock, lockDelay: lock > 0 ? 0 : -1 }
}

if (typeof module !== "undefined") {
  module.exports = { maxTimeoutSeconds: maxTimeoutSeconds, secondsFromConfig: secondsFromConfig, cyclePlan: cyclePlan }
}
