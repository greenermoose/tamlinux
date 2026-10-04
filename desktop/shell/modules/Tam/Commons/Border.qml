pragma Singleton
import QtQuick

// Uniform border specs from the caller's fallback color and width.
// Section names are ignored. The numbers match shell/host/ui_contract.py.
QtObject {
  function sides(width) {
    var n = Number(width)
    if (!isFinite(n) || n < 0) n = 0
    return { top: n, right: n, bottom: n, left: n }
  }

  function flat(fill, width) {
    return { color: fill || "transparent", widths: sides(width), gradient: null }
  }

  function none() {
    return flat("transparent", 0)
  }

  function surfaceSpec(section, token, fallbackColor, fallbackWidth) {
    return flat(fallbackColor, fallbackWidth)
  }

  function controlSpec(state, foreground, accent) {
    var hot = state === "focus" || state === "hover" || state === "hover-cursor" || state === "hot"
    var fill = (hot && accent) ? accent : (foreground || "transparent")
    return flat(fill, 1)
  }

  function top(spec) { return side(spec, "top") }
  function right(spec) { return side(spec, "right") }
  function bottom(spec) { return side(spec, "bottom") }
  function left(spec) { return side(spec, "left") }

  function side(spec, name) {
    if (!spec || !spec.widths || spec.widths[name] === undefined) return 0
    var n = Number(spec.widths[name])
    return isFinite(n) && n > 0 ? n : 0
  }

  function uniformWidth(spec) { return top(spec) }

  function specColor(spec) {
    return spec && spec.color ? spec.color : "transparent"
  }

  function isNone(spec) { return top(spec) <= 0 }

  function needsOverlay(spec) {
    if (!spec || !spec.widths) return false
    if (spec.gradient) return true
    var first = top(spec)
    return right(spec) !== first || bottom(spec) !== first || left(spec) !== first
  }

  function canUseNative(spec) {
    return !isNone(spec) && !needsOverlay(spec)
  }
}
