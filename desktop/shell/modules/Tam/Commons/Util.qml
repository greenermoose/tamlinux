pragma Singleton
import QtQuick
import Quickshell

QtObject {
  // Delivery injects these only into Quickshell. Null in a Process environment
  // removes a variable; an empty string restores an explicitly empty caller value.
  readonly property var graphicsProviderKeys: ["__EGL_VENDOR_LIBRARY_FILENAMES", "LIBGL_DRIVERS_PATH"]
  readonly property var providerEnvironment: String(Quickshell.env("TAMLINUX_GRAPHICS_PROVIDER_ENV") || "")
    .split(" ").filter(function (name) { return graphicsProviderKeys.indexOf(name) !== -1 })

  function hostEnvironment(overrides) {
    var result = {}
    for (var key in (overrides || {})) result[key] = overrides[key]
    result.TAMLINUX_GRAPHICS_PROVIDER_ENV = null
    for (var i = 0; i < graphicsProviderKeys.length; i++) {
      var name = graphicsProviderKeys[i]
      result["TAMLINUX_HOST_" + name] = null
      if (providerEnvironment.indexOf(name) !== -1)
        result[name] = Quickshell.env("TAMLINUX_HOST_" + name)
    }
    return result
  }

  // Detached calls in Quickshell 0.3.1 accept argv, not an environment object.
  // GNU env removes provider settings before restoring the original caller.
  function hostArgv(argv) {
    var changes = hostEnvironment()
    var prefix = ["/usr/bin/env"]
    var restore = []
    for (var name in changes) {
      prefix.push("-u", name)
      if (changes[name] !== null && changes[name] !== undefined)
        restore.push(name + "=" + changes[name])
    }
    return prefix.concat(["--"], restore, argv)
  }

  function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
  }

  // A module command's output: the last line as JSON, else the whole text.
  function parseModuleJson(raw) {
    var text = String(raw || "").trim()
    if (!text) return {}
    var lines = text.split("\n")
    try {
      return JSON.parse(lines[lines.length - 1])
    } catch (e) {
      return { text: text }
    }
  }

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
