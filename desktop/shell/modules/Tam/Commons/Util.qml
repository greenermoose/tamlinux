pragma Singleton
import QtQuick

QtObject {
  function clamp(value, min, max) {
    var n = Number(value)
    if (!isFinite(n)) return min
    return Math.max(min, Math.min(max, n))
  }

  function clampAlpha(value) {
    return clamp(value, 0, 1)
  }

  function alpha(c, opacity) {
    var a = clampAlpha(opacity)
    if (!c) return Qt.rgba(0, 0, 0, a)
    if (typeof c === "string") c = Qt.color(c)
    return Qt.rgba(c.r, c.g, c.b, a)
  }

  // One conventional wheel notch is 120 units. A direction change drops the
  // leftover from the previous direction. Large deltas are clamped to one notch.
  function wheelSteps(accumulator, delta) {
    var acc = Number(accumulator)
    var change = Number(delta)
    if (!isFinite(acc)) acc = 0
    if (!isFinite(change)) change = 0
    if (change > 120) change = 120
    if (change < -120) change = -120
    if (acc * change < 0) acc = 0
    var total = acc + change
    var steps = total < 0 ? Math.ceil(total / 120) : Math.floor(total / 120)
    return { steps: steps, remainder: total - steps * 120 }
  }

  // One shell word, single-quoted.
  function shellQuote(value) {
    return "'" + String(value || "").replace(/'/g, "'\\''") + "'"
  }
}
