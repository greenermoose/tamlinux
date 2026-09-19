function clampBrightness(value) {
  var n = Number(value)
  if (!isFinite(n)) return 1
  return Math.max(1, Math.min(100, Math.round(n)))
}

function normalizeScale(scale) {
  var n = parseFloat(String(scale || ""))
  if (!isFinite(n)) return ""
  return String(Math.round(n * 100) / 100)
}

function gcd(a, b) {
  while (b) {
    var remainder = a % b
    a = b
    b = remainder
  }
  return a
}

function cleanScale(scale, width, height) {
  var requested = Number(scale)
  var modeWidth = Number(width)
  var modeHeight = Number(height)
  if (!isFinite(requested) || !isFinite(modeWidth) || !isFinite(modeHeight)
      || requested <= 0 || modeWidth <= 0 || modeHeight <= 0) return ""

  var divisor = gcd(Math.round(modeWidth * 120), Math.round(modeHeight * 120))
  var scaleUnits = Math.round(requested * 120)
  if (scaleUnits > divisor) scaleUnits = divisor
  while (divisor % scaleUnits !== 0) scaleUnits++
  return normalizeScale(scaleUnits / 120)
}

function matchingScaleIndex(scales, currentScale, width, height) {
  var current = Number(currentScale)
  if (!Array.isArray(scales) || !isFinite(current)) return -1

  var bestIndex = -1
  var bestDistance = Infinity
  var normalizedCurrent = normalizeScale(current)
  for (var i = 0; i < scales.length; i++) {
    if (cleanScale(scales[i], width, height) !== normalizedCurrent) continue

    var distance = Math.abs(Number(scales[i]) - current)
    if (distance < bestDistance) {
      bestIndex = i
      bestDistance = distance
    }
  }
  return bestIndex
}

function availableScales(scales, width, height) {
  if (!Array.isArray(scales) || Number(width) <= 0 || Number(height) <= 0) return scales || []

  var byEffectiveScale = {}
  for (var i = 0; i < scales.length; i++) {
    var requested = Number(scales[i])
    var effective = Number(cleanScale(requested, width, height))

    if (!isFinite(requested) || !isFinite(effective)) continue

    var key = normalizeScale(effective)
    var existing = byEffectiveScale[key]
    if (!existing || Math.abs(requested - effective) < existing.distance) {
      byEffectiveScale[key] = {
        value: String(scales[i]),
        index: i,
        distance: Math.abs(requested - effective)
      }
    }
  }

  return Object.keys(byEffectiveScale)
    .map(function(key) { return byEffectiveScale[key] })
    .sort(function(a, b) { return a.index - b.index })
    .map(function(candidate) { return candidate.value })
}

function brightnessName(percent) {
  var p = Math.round(percent)
  if (p >= 95) return "Sun blast"
  if (p >= 80) return "Solar flare"
  if (p >= 65) return "Golden hour"
  if (p >= 45) return "Even day"
  if (p >= 30) return "Soft glow"
  if (p >= 20) return "Lamp light"
  if (p >= 10) return "Candlelit"
  return "Night owl"
}

function parseState(raw) {
  var data = null
  try {
    data = raw ? JSON.parse(String(raw)) : null
  } catch (e) {
    data = null
  }
  if (!data || typeof data !== "object") {
    return { focusedMonitor: "", displays: [], enabledDisplayCount: 0 }
  }
  var displays = Array.isArray(data.displays) ? data.displays : (Array.isArray(data) ? data : [])
  var count = 0
  for (var i = 0; i < displays.length; i++) {
    if (displays[i] && displays[i].enabled) count++
  }
  return {
    focusedMonitor: data.focusedMonitor || "",
    displays: displays,
    enabledDisplayCount: count
  }
}

function parseDisplays(raw) {
  return parseState(raw)
}

function formatFacts(display) {
  if (!display) return ""
  var parts = []
  if (display.width && display.height) {
    var rate = display.refreshRate ? Number(display.refreshRate).toFixed(2) : "60.00"
    parts.push(display.width + "×" + display.height + " @ " + rate + " Hz")
  }
  if (display.scale) {
    var lw = display.logicalWidth || Math.round(display.width / display.scale)
    var lh = display.logicalHeight || Math.round(display.height / display.scale)
    parts.push("scale " + display.scale + " → " + lw + "×" + lh + " logical")
  }
  parts.push("transform " + (display.transform !== undefined ? display.transform : 0))
  parts.push("DPMS " + (display.dpmsStatus ? "on" : "off"))
  parts.push("VRR " + (display.vrr ? "on" : "off"))
  if (display.workspace) {
    parts.push("workspace " + display.workspace)
  }
  if (display.sizeInches) {
    parts.push(display.sizeInches)
  }
  return parts.join("  ·  ")
}

function isValidOutputName(name) {
  return typeof name === "string" && /^[A-Za-z0-9._-]+$/.test(name)
}

function pickEnv(keys, extra, lookup) {
  var env = {}
  if (extra) {
    for (var k in extra) {
      if (Object.prototype.hasOwnProperty.call(extra, k) && extra[k] !== undefined && extra[k] !== null && extra[k] !== "") {
        env[k] = String(extra[k])
      }
    }
  }
  if (keys && typeof lookup === "function") {
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i]
      var val = lookup(key)
      if (val !== undefined && val !== null && val !== "") {
        env[key] = String(val)
      }
    }
  }
  return env
}

function helperPath(name) {
  if (typeof Qt === "undefined" || !Qt.resolvedUrl) return name
  var url = String(Qt.resolvedUrl(name))
  if (url.indexOf("file://") === 0) {
    url = url.substring(7)
  }
  return decodeURIComponent(url)
}

function positionLabel(displayName, displays) {
  if (!Array.isArray(displays)) return ""
  var enabled = []
  for (var i = 0; i < displays.length; i++) {
    if (displays[i] && displays[i].enabled) enabled.push(displays[i])
  }
  if (enabled.length <= 1) return ""
  enabled.sort(function(a, b) { return (a.x || 0) - (b.x || 0) })
  var idx = -1
  for (var j = 0; j < enabled.length; j++) {
    if (enabled[j].name === displayName) { idx = j; break }
  }
  if (idx < 0) return ""
  if (enabled.length === 2) return idx === 0 ? "Left" : "Right"
  if (enabled.length === 3) {
    if (idx === 0) return "Left"
    if (idx === 1) return "Center"
    return "Right"
  }
  return "L" + (idx + 1)
}

if (typeof module !== "undefined") {
  module.exports = {
    clampBrightness: clampBrightness,
    normalizeScale: normalizeScale,
    cleanScale: cleanScale,
    matchingScaleIndex: matchingScaleIndex,
    availableScales: availableScales,
    brightnessName: brightnessName,
    parseDisplays: parseDisplays,
    parseState: parseState,
    formatFacts: formatFacts,
    isValidOutputName: isValidOutputName,
    pickEnv: pickEnv,
    helperPath: helperPath,
    positionLabel: positionLabel
  }
}
