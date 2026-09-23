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

function monitorCountLabel(count) {
  var n = Math.max(0, Math.round(Number(count) || 0))
  var words = ["No", "One", "Two", "Three"]
  var amount = n < words.length ? words[n] : String(n)
  return amount + " Monitor" + (n === 1 ? "" : "s")
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
  parts.push("VRR " + (display.vrr ? "on" : "off"))
  if (display.workspace) {
    parts.push("workspace " + display.workspace)
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

function sortDisplays(displays) {
  if (!Array.isArray(displays)) return []
  return displays.slice().sort(function(a, b) {
    if (!!a.enabled !== !!b.enabled) return a.enabled ? -1 : 1
    var ax = Number(a.x)
    var bx = Number(b.x)
    if (!isFinite(ax)) ax = 0
    if (!isFinite(bx)) bx = 0
    if (ax !== bx) return ax - bx
    return String(a.name || "").localeCompare(String(b.name || ""))
  })
}

function diagonalInches(display) {
  if (!display) return ""
  var pw = Number(display.physicalWidth)
  var ph = Number(display.physicalHeight)
  if (isFinite(pw) && isFinite(ph) && pw > 0 && ph > 0) {
    return (Math.round(Math.sqrt(pw * pw + ph * ph) / 25.4 * 10) / 10) + "\u2033"
  }
  var match = String(display.sizeInches || "").match(/\(([0-9.]+)\" diag\)/)
  return match ? match[1] + "\u2033" : ""
}

function displayIdentity(display) {
  if (!display) return "Unknown display"
  var make = String(display.make || "").trim()
  var model = String(display.model || "").trim()
  if (make && model && model.toLowerCase().indexOf(make.toLowerCase()) === 0) return model
  return [make, model].filter(function(part) { return part !== "" }).join(" ") || String(display.description || "Display")
}

function cardIdentity(display) {
  if (!display) return "Unknown display"
  var diagonal = diagonalInches(display)
  var identity = String(display.model || "").trim() || displayIdentity(display)
  return [diagonal, identity].filter(function(part) { return part !== "" }).join(" ")
}

function formatHover(display, displays, version) {
  var versionFootnote = "fred.monitor" + (version ? " v" + version : "")
  if (!display) return "Display\n\n" + versionFootnote
  var position = positionLabel(display.name, displays)
  var title = position ? position + " Monitor" : "Monitor"
  var parts = [String(display.name || "Display"), displayIdentity(display)]
  var diagonal = diagonalInches(display)
  if (diagonal) parts.push(diagonal)
  if (display.width && display.height) parts.push(display.width + " \u00d7 " + display.height)
  if (display.refreshRate) parts.push(Number(display.refreshRate).toFixed(2) + " Hz")
  if (display.scale) parts.push(normalizeScale(display.scale) + "\u00d7")
  return title + "\n" + parts.join(" \u00b7 ") + "\n\n" + versionFootnote
}

function logicalHeight(display) {
  var scale = Number(display.scale) || 1
  var rotated = Math.abs(Number(display.transform || 0)) % 2 === 1
  return Math.round(Number(rotated ? display.width : display.height) / scale)
}

function logicalWidth(display) {
  var scale = Number(display.scale) || 1
  var rotated = Math.abs(Number(display.transform || 0)) % 2 === 1
  return Math.round(Number(rotated ? display.height : display.width) / scale)
}

function alignDisplays(displays, alignment) {
  var sorted = sortDisplays(displays).map(function(display) {
    var copy = {}
    for (var key in display) copy[key] = display[key]
    return copy
  })
  var enabled = sorted.filter(function(display) { return display.enabled })
  var maxHeight = 0
  for (var i = 0; i < enabled.length; i++) maxHeight = Math.max(maxHeight, logicalHeight(enabled[i]))
  var x = 0
  for (var j = 0; j < enabled.length; j++) {
    var height = logicalHeight(enabled[j])
    enabled[j].x = x
    enabled[j].y = alignment === "top" ? 0 : (alignment === "center" ? Math.round((maxHeight - height) / 2) : maxHeight - height)
    enabled[j].logicalWidth = logicalWidth(enabled[j])
    enabled[j].logicalHeight = height
    x += logicalWidth(enabled[j])
  }
  return sorted
}

function moveDisplay(displays, name, delta, alignment) {
  var sorted = sortDisplays(displays)
  var index = -1
  for (var i = 0; i < sorted.length; i++) if (sorted[i].name === name) index = i
  var target = index + Number(delta)
  if (index < 0 || target < 0 || target >= sorted.length || !sorted[target].enabled) return alignDisplays(sorted, alignment)
  var item = sorted[index]
  sorted[index] = sorted[target]
  sorted[target] = item
  // Preserve the requested order while alignment recalculates positions.
  for (var j = 0, x = 0; j < sorted.length; j++) {
    if (!sorted[j].enabled) continue
    sorted[j].x = x
    x += logicalWidth(sorted[j])
  }
  return alignDisplays(sorted, alignment)
}

function layoutSignature(displays) {
  return sortDisplays(displays).map(function(display) {
    return [display.name, !!display.enabled, Number(display.width), Number(display.height), Number(display.refreshRate).toFixed(3), Number(display.x), Number(display.y), normalizeScale(display.scale), Number(display.transform || 0)].join("|")
  }).join(";")
}

if (typeof module !== "undefined") {
  module.exports = {
    clampBrightness: clampBrightness,
    normalizeScale: normalizeScale,
    cleanScale: cleanScale,
    matchingScaleIndex: matchingScaleIndex,
    availableScales: availableScales,
    brightnessName: brightnessName,
    monitorCountLabel: monitorCountLabel,
    parseDisplays: parseDisplays,
    parseState: parseState,
    formatFacts: formatFacts,
    isValidOutputName: isValidOutputName,
    pickEnv: pickEnv,
    helperPath: helperPath,
    positionLabel: positionLabel,
    sortDisplays: sortDisplays,
    diagonalInches: diagonalInches,
    displayIdentity: displayIdentity,
    cardIdentity: cardIdentity,
    formatHover: formatHover,
    logicalWidth: logicalWidth,
    logicalHeight: logicalHeight,
    alignDisplays: alignDisplays,
    moveDisplay: moveDisplay,
    layoutSignature: layoutSignature
  }
}
