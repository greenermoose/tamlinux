// Tide mathematics and provider modeling for fred.tides

var M_TO_FT = 3.280839895

// Parse location JSON (compatible with omarchy weather.json & tides.json)
function parseLocationFile(raw) {
  var unset = { name: "", latitude: null, longitude: null, unit: "m" }
  try {
    var data = JSON.parse(String(raw || ""))
    if (!data || typeof data !== "object") return unset

    var latitude = parseFloat(data.latitude)
    var longitude = parseFloat(data.longitude)
    var hasCoordinates = !isNaN(latitude) && !isNaN(longitude)
    var unit = (data.unit === "ft" || data.unit === "feet" || data.unit === "imperial") ? "ft" : "m"

    return {
      name: typeof data.name === "string" ? data.name.replace(/^\s+|\s+$/g, "") : "",
      latitude: hasCoordinates ? latitude : null,
      longitude: hasCoordinates ? longitude : null,
      unit: unit
    }
  } catch (e) {
    return unset
  }
}

function formatLocationDisplay(name, region) {
  var n = String(name || "").trim()
  if (!n) return "Brunswick, Maine"
  if (n.indexOf(",") !== -1) return n
  if (region && String(region).trim()) return n + ", " + String(region).trim()
  if (n.toLowerCase() === "brunswick") return "Brunswick, Maine"
  return n
}

function formatTidesTitle(locationDisplay) {
  var loc = String(locationDisplay || "").trim()
  return loc ? "Tides for " + loc : "Tides"
}

function locationFileContents(name, latitude, longitude, unit) {
  var u = unit === "ft" ? "ft" : "m"
  return JSON.stringify({
    name: name || "",
    latitude: latitude,
    longitude: longitude,
    unit: u
  }, null, 2) + "\n"
}

// Convert height from meters (base internal unit) to user-configured unit
function convertHeight(meters, unit) {
  if (meters === null || meters === undefined || isNaN(meters)) return null
  return unit === "ft" ? meters * M_TO_FT : meters
}

function formatHeight(meters, unit) {
  if (meters === null || meters === undefined || isNaN(meters)) return ""
  var u = unit === "ft" ? "ft" : "m"
  var val = convertHeight(meters, unit)
  var sign = val >= 0 ? "+" : ""
  return sign + val.toFixed(1) + u
}

function formatRange(meters, unit) {
  if (meters === null || meters === undefined || isNaN(meters)) return ""
  var u = unit === "ft" ? "ft" : "m"
  var val = convertHeight(meters, unit)
  return val.toFixed(1) + u
}

function pad2(n) {
  return (n < 10 ? "0" : "") + n
}

function formatTime(date) {
  if (!date || isNaN(date.getTime())) return ""
  return pad2(date.getHours()) + ":" + pad2(date.getMinutes())
}

function untilText(from, to) {
  if (!from || !to) return ""
  var mins = Math.max(0, Math.round((to.getTime() - from.getTime()) / 60000))
  var h = Math.floor(mins / 60)
  var m = mins % 60
  if (h === 0) return m + "m"
  return h + "h " + pad2(m) + "m"
}

function dayLabel(date, now) {
  if (!date || !now) return ""
  if (date.toDateString() === now.toDateString()) return "TODAY"
  return ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"][date.getDay()]
}

// Local extrema of the hourly sea-level series.
// Refines each peak/trough with a parabolic fit through neighbors for minute-level accuracy.
function tideEvents(report) {
  if (!report || !report.hourly || !report.hourly.time) return []
  var times = report.hourly.time
  var heights = report.hourly.sea_level_height_msl
  if (!heights || !Array.isArray(heights) || heights.length < 3) return []

  var out = []
  for (var i = 1; i < heights.length - 1; i++) {
    var a = heights[i - 1], b = heights[i], c = heights[i + 1]
    if (a === null || b === null || c === null || a === undefined || b === undefined || c === undefined) continue
    var isMax = b > a && b >= c
    var isMin = b < a && b <= c
    if (!isMax && !isMin) continue

    var denom = a - 2 * b + c
    var shift = denom === 0 ? 0 : (a - c) / (2 * denom)
    if (shift > 1) shift = 1
    if (shift < -1) shift = -1

    var t = new Date(times[i])
    if (isNaN(t.getTime())) continue
    out.push({
      time: new Date(t.getTime() + shift * 3600 * 1000),
      high: isMax,
      height: b - (a - c) * shift / 4 // height in meters
    })
  }
  return out
}

function upcomingEvents(events, now, count) {
  if (!Array.isArray(events) || !now) return []
  var out = []
  var targetCount = typeof count === "number" ? count : 4
  var nowMs = now.getTime()
  for (var i = 0; i < events.length && out.length < targetCount; i++) {
    if (events[i].time.getTime() > nowMs) out.push(events[i])
  }
  return out
}

// Sea level right now, linearly interpolated between the hourly samples.
function heightAt(report, now) {
  if (!report || !report.hourly || !report.hourly.time || !now) return null
  var times = report.hourly.time
  var heights = report.hourly.sea_level_height_msl
  if (!heights || times.length < 2) return null

  var start = new Date(times[0])
  if (isNaN(start.getTime())) return null
  var pos = (now.getTime() - start.getTime()) / 3600000
  var i = Math.floor(pos)
  if (i < 0 || i >= heights.length - 1) return null
  var a = heights[i], b = heights[i + 1]
  if (a === null || b === null || a === undefined || b === undefined) return null
  return a + (b - a) * (pos - i)
}

// Sea level at arbitrary instant via Catmull-Rom cubic spline through hourly samples.
function smoothHeightAt(report, timeMs) {
  if (!report || !report.hourly || !report.hourly.time) return null
  var heights = report.hourly.sea_level_height_msl
  if (!heights || heights.length < 2) return null
  var start = new Date(report.hourly.time[0])
  if (isNaN(start.getTime())) return null

  var n = heights.length
  var pos = (timeMs - start.getTime()) / 3600000
  if (pos < 0 || pos > n - 1) return null
  var i = Math.floor(pos)
  if (i >= n - 1) i = n - 2
  var f = pos - i

  var p1 = heights[i], p2 = heights[i + 1]
  var p0 = i > 0 ? heights[i - 1] : p1
  var p3 = i + 2 < n ? heights[i + 2] : p2
  if (p0 === null || p1 === null || p2 === null || p3 === null
    || p0 === undefined || p1 === undefined || p2 === undefined || p3 === undefined) return null

  return 0.5 * ((2 * p1) + (-p0 + p2) * f
    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
    + (-p0 + 3 * p1 - 3 * p2 + p3) * f * f * f)
}

// Today's tidal swing in meters
function todayRangeMeters(events, now) {
  if (!Array.isArray(events) || !now) return null
  var highs = [], lows = []
  var todayStr = now.toDateString()
  for (var i = 0; i < events.length; i++) {
    if (events[i].time.toDateString() !== todayStr) continue
    if (events[i].high) highs.push(events[i].height)
    else lows.push(events[i].height)
  }
  if (highs.length === 0 || lows.length === 0) return null
  return Math.max.apply(null, highs) - Math.min.apply(null, lows)
}

function todayRange(events, now, unit) {
  var rangeM = todayRangeMeters(events, now)
  if (rangeM === null) return ""
  return formatRange(rangeM, unit)
}

// Events for the active day with tomorrow rollover
function dayTides(events, now) {
  if (!Array.isArray(events) || !now) return { label: "TODAY", events: [] }
  var today = [], tomorrow = []
  var tomorrowDate = new Date(now.getTime() + 24 * 3600 * 1000)
  var todayStr = now.toDateString()
  var tomStr = tomorrowDate.toDateString()

  for (var i = 0; i < events.length; i++) {
    var d = events[i].time.toDateString()
    if (d === todayStr) today.push(events[i])
    else if (d === tomStr) tomorrow.push(events[i])
  }
  var nowMs = now.getTime()
  var todayRemaining = today.filter(function(e) { return e.time.getTime() > nowMs })
  if (todayRemaining.length === 0 && tomorrow.length > 0) return { label: "TOMORROW", events: tomorrow }
  return { label: "TODAY", events: today }
}

function parseGeocodingResults(raw) {
  try {
    var data = JSON.parse(String(raw || "{}"))
    var results = data.results
    if (!results || !results.length) return []

    var out = []
    for (var i = 0; i < results.length; i++) {
      var r = results[i]
      if (!r || !r.name || r.latitude === undefined || r.longitude === undefined) continue
      var region = [r.admin1, r.country].filter(function(part) { return !!part }).join(", ")
      out.push({
        name: String(r.name),
        description: region,
        latitude: r.latitude,
        longitude: r.longitude
      })
    }
    return out
  } catch (e) {
    return []
  }
}

// ============================================================================
// Data Provider Abstraction
// ============================================================================
var Providers = {
  "open-meteo": {
    id: "open-meteo",
    displayName: "Open-Meteo Marine",
    buildQueryUrl: function(latitude, longitude) {
      return "https://marine-api.open-meteo.com/v1/marine"
        + "?latitude=" + encodeURIComponent(String(latitude))
        + "&longitude=" + encodeURIComponent(String(longitude))
        + "&hourly=sea_level_height_msl"
        + "&forecast_days=3"
        + "&timezone=auto"
    },
    parseResponse: function(raw) {
      var parsed = JSON.parse(String(raw || ""))
      if (!parsed || !parsed.hourly || !Array.isArray(parsed.hourly.time) || !Array.isArray(parsed.hourly.sea_level_height_msl)) {
        throw new Error("Invalid Open-Meteo marine payload")
      }
      return parsed
    }
  },

  // Stubs for Version 1.1 Expansion
  "noaa": {
    id: "noaa",
    displayName: "NOAA CO-OPS (v1.1 Planned)",
    buildQueryUrl: function(stationId) {
      return "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        + "?product=predictions&datum=MLLW&time_zone=lst_ldt&units=metric&format=json"
        + "&station=" + encodeURIComponent(String(stationId))
    },
    parseResponse: function(raw) {
      throw new Error("NOAA provider is scheduled for Version 1.1")
    }
  },

  "harmonics": {
    id: "harmonics",
    displayName: "Local Harmonics Math (v1.1 Planned)",
    buildQueryUrl: function() { return null },
    parseResponse: function() {
      throw new Error("Harmonics provider is scheduled for Version 1.1")
    }
  }
}

// Cache serialisation & parsing
function serializeCache(report, location, updatedAt) {
  return JSON.stringify({
    version: "1.0.0",
    updatedAt: (updatedAt || new Date()).toISOString(),
    location: location || null,
    report: report || null
  }, null, 2) + "\n"
}

function parseCache(raw) {
  try {
    var data = JSON.parse(String(raw || ""))
    if (!data || typeof data !== "object" || !data.report) return null
    return data
  } catch (e) {
    return null
  }
}

if (typeof module !== "undefined") {
  module.exports = {
    M_TO_FT: M_TO_FT,
    parseLocationFile: parseLocationFile,
    formatLocationDisplay: formatLocationDisplay,
    formatTidesTitle: formatTidesTitle,
    locationFileContents: locationFileContents,
    convertHeight: convertHeight,
    formatHeight: formatHeight,
    formatRange: formatRange,
    pad2: pad2,
    formatTime: formatTime,
    untilText: untilText,
    dayLabel: dayLabel,
    tideEvents: tideEvents,
    upcomingEvents: upcomingEvents,
    heightAt: heightAt,
    smoothHeightAt: smoothHeightAt,
    todayRangeMeters: todayRangeMeters,
    todayRange: todayRange,
    dayTides: dayTides,
    parseGeocodingResults: parseGeocodingResults,
    Providers: Providers,
    serializeCache: serializeCache,
    parseCache: parseCache
  }
}
