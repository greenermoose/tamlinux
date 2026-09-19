// weather.json holds {"name": ..., "latitude": ..., "longitude": ...} (see
// omarchy-weather-location, which owns the format). Missing, blank, or
// unparseable means the location is auto-detected from the IP address.
function parseLocationFile(raw) {
  var unset = { name: "", latitude: null, longitude: null }
  try {
    var data = JSON.parse(String(raw || ""))
    if (!data || typeof data !== "object") return unset

    var latitude = parseFloat(data.latitude)
    var longitude = parseFloat(data.longitude)
    var hasCoordinates = !isNaN(latitude) && !isNaN(longitude)
    return {
      name: typeof data.name === "string" ? data.name.replace(/^\s+|\s+$/g, "") : "",
      latitude: hasCoordinates ? latitude : null,
      longitude: hasCoordinates ? longitude : null
    }
  } catch (e) {
    return unset
  }
}

// wttr.in path segment for a configured location: exact coordinates when
// both are present, the URL-encoded name as a fallback (hand-edited
// weather.loc files may only carry a name), empty for IP auto-detect.
function wttrLocationQuery(location, latitude, longitude) {
  var lat = parseFloat(String(latitude))
  var lon = parseFloat(String(longitude))
  if (!isNaN(lat) && !isNaN(lon)) return lat + "," + lon

  var name = String(location || "").replace(/^\s+|\s+$/g, "")
  return name === "" ? "" : encodeURIComponent(name)
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
        name: String(r.name) + (r.admin1 ? ", " + r.admin1 : ""),
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

function locationCommit(text, suggestions, selectedIndex) {
  var name = String(text || "").replace(/^\s+|\s+$/g, "")
  if (name === "") return { name: "", latitude: null, longitude: null }

  var choices = suggestions || []
  var index = Math.max(0, Math.min(parseInt(selectedIndex, 10) || 0, choices.length - 1))
  var suggestion = choices[index]
  if (suggestion) return suggestion

  return { name: name, latitude: null, longitude: null }
}

function validCoordinates(latitude, longitude) {
  return typeof latitude === "number" && isFinite(latitude) && Math.abs(latitude) <= 90
    && typeof longitude === "number" && isFinite(longitude) && Math.abs(longitude) <= 180
}

function coordinateLocation(text) {
  var match = String(text || "").trim().match(/^([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)$/)
  if (!match) return null
  var latitude = Number(match[1])
  var longitude = Number(match[2])
  if (!validCoordinates(latitude, longitude)) return null
  return { name: "Pinned location", description: latitude + ", " + longitude,
    latitude: latitude, longitude: longitude }
}

function locationSearchUrl(query) {
  query = String(query || "").trim()
  if (/^\d{5}(?:-\d{4})?$/.test(query))
    return "https://api.zippopotam.us/us/" + query.slice(0, 5)
  return "https://geocoding-api.open-meteo.com/v1/search?name=" + encodeURIComponent(query)
    + "&count=5&language=en&format=json"
}

function parseLocationSearch(raw, query) {
  if (!/^\d{5}(?:-\d{4})?$/.test(query)) return parseGeocodingResults(raw)
  var data = JSON.parse(raw)
  if (!Array.isArray(data.places)) throw new Error("ZIP lookup returned no places")
  return data.places.map(function(place) {
    var latitude = Number(place.latitude)
    var longitude = Number(place.longitude)
    if (!validCoordinates(latitude, longitude)) throw new Error("ZIP lookup returned invalid coordinates")
    return {
      name: place["place name"] + ", " + place["state abbreviation"] + " " + data["post code"],
      description: "ZIP area center (approximate), " + place.state,
      latitude: latitude,
      longitude: longitude
    }
  })
}

function locationMapUrl(latitude, longitude) {
  if (!validCoordinates(latitude, longitude)) return ""
  return "https://www.openstreetmap.org/?mlat=" + latitude + "&mlon=" + longitude
    + "#map=15/" + latitude + "/" + longitude
}

function formatLocationDisplay(configuredLocation, areaInfo, wttrLocation) {
  var config = String(configuredLocation || "").trim().replace(/\s+\d{5}(?:-\d{4})?$/, "")
  var area = areaInfo && areaInfo.areaName && areaInfo.areaName[0] ? String(areaInfo.areaName[0].value || "").trim() : ""
  var region = areaInfo && areaInfo.region && areaInfo.region[0] ? String(areaInfo.region[0].value || "").trim() : ""
  var wttr = String(wttrLocation || "").trim()

  if (config.indexOf(",") !== -1) return config
  var baseCity = config || area || wttr
  if (baseCity && region && region.toLowerCase() !== baseCity.toLowerCase()) {
    return baseCity + ", " + region
  }
  return baseCity
}

function isFutureForecastDate(dateString, todayString) {
  if (!dateString) return false
  return String(dateString).slice(0, 10) > String(todayString || "")
}

function roundedTemp(value) {
  if (value === undefined || value === null || value === "") return ""
  var n = parseFloat(String(value))
  return isNaN(n) ? "" : String(Math.round(n))
}

function celsiusToFahrenheit(value) {
  if (value === undefined || value === null || value === "") return ""
  var n = parseFloat(String(value))
  return isNaN(n) ? "" : (n * 9 / 5) + 32
}

function formatTemp(value, useImperial) {
  if (value === undefined || value === null || value === "") return ""
  return value + "°" + (useImperial ? "F" : "C")
}

function normalizedUnit(value) {
  return String(value || "").replace(/^\s+|\s+$/g, "").toLowerCase()
}

function localeUsesImperial(localeName) {
  var name = String(localeName || "").replace(".", "_")
  return /^en[_-]US($|[_.-])/.test(name) || /^en[_-]LR($|[_.-])/.test(name) || /^my($|[_.-])/.test(name)
}

function countryUsesImperial(countryName) {
  var country = String(countryName || "")
    .replace(/^\s+|\s+$/g, "")
    .replace(/[._-]+/g, " ")
    .toLowerCase()
  if (!country) return null
  if (country === "us" || country === "usa" || country === "united states" || country === "united states of america") return true
  if (country === "liberia" || country === "myanmar" || country === "burma") return true
  return false
}

function shouldUseImperial(unitOverride, localeName, countryName) {
  var unit = normalizedUnit(unitOverride)
  if (unit === "imperial") return true
  if (unit === "metric") return false

  var countryPreference = countryUsesImperial(countryName)
  if (countryPreference !== null) return countryPreference

  return localeUsesImperial(localeName)
}

function degreesToCardinal(deg) {
  if (deg === undefined || deg === null || isNaN(deg)) return ""
  var val = Math.floor((deg / 22.5) + 0.5)
  var arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
  return arr[(val % 16)] || ""
}

function dayName(dateString, formatter) {
  if (!dateString) return ""
  var d = new Date(dateString + "T12:00:00")
  if (isNaN(d.getTime())) return ""
  if (formatter) return formatter(d)
  return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][d.getDay()]
}

function shortDayName(dateString, todayString) {
  if (!dateString) return ""
  if (todayString && dateString.slice(0, 10) === todayString.slice(0, 10)) return "Today"
  var d = new Date(dateString + "T12:00:00")
  if (isNaN(d.getTime())) return ""
  var days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
  var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  return days[d.getDay()] + " " + months[d.getMonth()] + " " + d.getDate()
}

function weatherDescription(code) {
  var c = parseInt(String(code || "0"), 10)
  switch (c) {
    case 0: return "Clear Sky"
    case 1: return "Mainly Clear"
    case 2: return "Partly Cloudy"
    case 3: return "Overcast"
    case 45: return "Fog"
    case 48: return "Freezing Fog"
    case 51: return "Light Drizzle"
    case 53: return "Moderate Drizzle"
    case 55: return "Dense Drizzle"
    case 56: return "Light Freezing Drizzle"
    case 57: return "Dense Freezing Drizzle"
    case 61: return "Slight Rain"
    case 63: return "Moderate Rain"
    case 65: return "Heavy Rain"
    case 66: return "Light Freezing Rain"
    case 67: return "Heavy Freezing Rain"
    case 71: return "Slight Snow"
    case 73: return "Moderate Snow"
    case 75: return "Heavy Snow"
    case 77: return "Snow Grains"
    case 80: return "Slight Showers"
    case 81: return "Moderate Showers"
    case 82: return "Violent Showers"
    case 85: return "Slight Snow Showers"
    case 86: return "Heavy Snow Showers"
    case 95: return "Thunderstorm"
    case 96: return "Thunderstorm w/ Hail"
    case 99: return "Severe Thunderstorm"
    default: return "Cloudy"
  }
}

// Parses up to 10 forecast days from Open-Meteo
function openMeteoForecastDays(dailyForecastReport, todayString, maxDays) {
  var daily = dailyForecastReport && dailyForecastReport.daily ? dailyForecastReport.daily : null
  if (!daily || !daily.time) return []

  var limit = maxDays || 10
  var result = []
  for (var i = 0; i < daily.time.length && result.length < limit; ++i) {
    var date = daily.time[i]
    var maxC = daily.temperature_2m_max ? daily.temperature_2m_max[i] : ""
    var minC = daily.temperature_2m_min ? daily.temperature_2m_min[i] : ""
    var code = daily.weather_code ? daily.weather_code[i] : null
    var prob = daily.precipitation_probability_max ? daily.precipitation_probability_max[i] : null
    var precipSum = daily.precipitation_sum ? daily.precipitation_sum[i] : null

    result.push({
      date: date,
      isToday: todayString ? date.slice(0, 10) === todayString.slice(0, 10) : i === 0,
      dayLabel: shortDayName(date, todayString),
      dayName: dayName(date),
      maxtempC: roundedTemp(maxC),
      mintempC: roundedTemp(minC),
      maxtempF: roundedTemp(celsiusToFahrenheit(maxC)),
      mintempF: roundedTemp(celsiusToFahrenheit(minC)),
      openMeteoWeatherCode: code,
      description: weatherDescription(code),
      precipitationProbability: typeof prob === "number" && isFinite(prob) ? Math.round(prob) : null,
      precipitationSumMm: precipSum !== null && isFinite(precipSum) ? Number(precipSum) : null,
      precipitationSumIn: precipSum !== null && isFinite(precipSum) ? Number((precipSum * 0.0393701).toFixed(2)) : null,
      sunrise: daily.sunrise ? daily.sunrise[i] : null,
      sunset: daily.sunset ? daily.sunset[i] : null
    })
  }
  return result
}

function openMeteoCurrentCondition(dailyForecastReport) {
  var current = dailyForecastReport && dailyForecastReport.current ? dailyForecastReport.current : null
  if (!current || current.temperature_2m === undefined || current.temperature_2m === null) return null

  var daily = dailyForecastReport.daily || {}
  var todayMaxC = daily.temperature_2m_max && daily.temperature_2m_max[0] !== undefined ? daily.temperature_2m_max[0] : null
  var todayMinC = daily.temperature_2m_min && daily.temperature_2m_min[0] !== undefined ? daily.temperature_2m_min[0] : null
  var todayPrecipProb = daily.precipitation_probability_max && daily.precipitation_probability_max[0] !== undefined ? daily.precipitation_probability_max[0] : null

  var windDeg = current.wind_direction_10m !== undefined ? current.wind_direction_10m : null

  return {
    temp_C: roundedTemp(current.temperature_2m),
    temp_F: roundedTemp(celsiusToFahrenheit(current.temperature_2m)),
    FeelsLikeC: roundedTemp(current.apparent_temperature),
    FeelsLikeF: roundedTemp(celsiusToFahrenheit(current.apparent_temperature)),
    windspeedKmph: roundedTemp(current.wind_speed_10m),
    windspeedMiles: roundedTemp(current.wind_speed_10m * 0.621371),
    windDirectionDeg: windDeg,
    windDirectionCardinal: degreesToCardinal(windDeg),
    humidity: roundedTemp(current.relative_humidity_2m),
    openMeteoWeatherCode: current.weather_code,
    description: weatherDescription(current.weather_code),
    isDay: current.is_day,
    todayMaxC: roundedTemp(todayMaxC),
    todayMinC: roundedTemp(todayMinC),
    todayMaxF: roundedTemp(celsiusToFahrenheit(todayMaxC)),
    todayMinF: roundedTemp(celsiusToFahrenheit(todayMinC)),
    todayPrecipProbability: todayPrecipProb !== null && isFinite(todayPrecipProb) ? Math.round(todayPrecipProb) : null,
    sunrise: daily.sunrise ? daily.sunrise[0] : null,
    sunset: daily.sunset ? daily.sunset[0] : null
  }
}

function currentIcon(current, fallback) {
  if (!current) return fallback || ""
  if (current.openMeteoWeatherCode !== undefined && current.openMeteoWeatherCode !== null)
    return iconForOpenMeteoCode(current.openMeteoWeatherCode, Number(current.isDay) === 0)
  if (current.weatherCode !== undefined && current.weatherCode !== null)
    return iconForCode(current.weatherCode, false)
  return fallback || ""
}

function provisionalCurrentIcon(current, resolvedIcon) {
  return resolvedIcon || currentIcon(current, "")
}

function weatherResponseCompletesSave(hasConfiguredCoordinates, source) {
  return hasConfiguredCoordinates ? source === "open-meteo" : source === "wttr"
}

function validWeatherReport(report) {
  return !!report && Array.isArray(report.current_condition)
    && !!report.current_condition[0] && typeof report.current_condition[0] === "object"
    && !Array.isArray(report.current_condition[0])
}

function parseWeatherCache(raw) {
  var cache = JSON.parse(raw)
  if (!cache || cache.version !== 1 || typeof cache.locationQuery !== "string"
      || (!cache.report && !cache.dailyForecast))
    throw new Error("Invalid weather cache format")

  ;["report", "dailyForecast"].forEach(function(source) {
    var entry = cache[source]
    if (entry === null || entry === undefined) return
    if (!entry || typeof entry.updatedAt !== "number" || !isFinite(entry.updatedAt)
        || entry.updatedAt <= 0 || !entry.data)
      throw new Error("Invalid cached weather timestamp or payload")
    if (source === "report" ? !validWeatherReport(entry.data)
        : entry.data.error || hourlyForecast(entry.data, entry.updatedAt, 48).length === 0)
      throw new Error("Invalid cached " + source)
  })
  return cache
}

function updatedWeatherCache(previous, locationQuery, source, data, updatedAt) {
  if (source !== "report" && source !== "dailyForecast")
    throw new Error("Unknown weather cache source")
  var matching = previous && previous.locationQuery === locationQuery
  if (matching && locationQuery === "" && source === "report") {
    var oldReport = previous.report && previous.report.data
    var oldArea = oldReport && oldReport.nearest_area && oldReport.nearest_area[0]
    var newArea = data && data.nearest_area && data.nearest_area[0]
    matching = oldArea && newArea
      && parseFloat(oldArea.latitude) === parseFloat(newArea.latitude)
      && parseFloat(oldArea.longitude) === parseFloat(newArea.longitude)
  }
  var cache = {
    version: 1,
    locationQuery: locationQuery,
    report: matching ? previous.report : null,
    dailyForecast: matching ? previous.dailyForecast : null
  }
  cache[source] = { updatedAt: updatedAt, data: data }
  return cache
}

function wttrNextForecastDays(report, todayString) {
  var days = report && report.weather ? report.weather : []
  var result = []
  for (var i = 0; i < days.length && result.length < 10; ++i) {
    if (isFutureForecastDate(days[i].date, todayString)) result.push(days[i])
  }
  return result
}

function buildForecastDays(report, dailyForecastReport, todayString) {
  var days = openMeteoForecastDays(dailyForecastReport, todayString, 10)
  return days.length > 0 ? days : wttrNextForecastDays(report, todayString)
}

function bareTempForDay(day, kind, useImperial) {
  if (!day) return ""
  var v = useImperial
    ? (kind === "max" ? day.maxtempF : day.mintempF)
    : (kind === "max" ? day.maxtempC : day.mintempC)
  if (v === undefined || v === null || v === "") return ""
  return v + "°"
}

function dayIcon(day) {
  if (!day) return ""
  if (day.openMeteoWeatherCode !== undefined && day.openMeteoWeatherCode !== null)
    return iconForOpenMeteoCode(day.openMeteoWeatherCode, false)
  if (!day.hourly || day.hourly.length === 0) return ""

  var best = day.hourly[0]
  var bestDist = 9999
  for (var i = 0; i < day.hourly.length; ++i) {
    var t = parseInt(String(day.hourly[i].time || "0"), 10)
    var dist = Math.abs(t - 1200)
    if (dist < bestDist) {
      bestDist = dist
      best = day.hourly[i]
    }
  }
  return iconForCode(best.weatherCode, false)
}

function iconForOpenMeteoCode(code, night) {
  var c = parseInt(String(code || "0"), 10)
  if (c === 0) return iconForCode(113, night)
  if (c === 1 || c === 2) return iconForCode(116, night)
  if (c === 3) return iconForCode(119, night)
  if (c === 45 || c === 48) return iconForCode(143, night)
  if (c === 51 || c === 53 || c === 55 || c === 56 || c === 57 || c === 61) return iconForCode(266, night)
  if (c === 63 || c === 65 || c === 66 || c === 67 || c === 80 || c === 81 || c === 82) return iconForCode(308, night)
  if (c === 71 || c === 73 || c === 75 || c === 77 || c === 85 || c === 86) return iconForCode(338, night)
  if (c === 95 || c === 96 || c === 99) return iconForCode(389, night)
  return iconForCode(119, night)
}

// Icon mapping using Font Awesome sun "\uf185" () for clear sky daylight!
function iconForCode(code, night) {
  var c = parseInt(String(code || "0"), 10)
  switch (c) {
    case 113: return night ? "\ue32b" : "\uf185"  // Clear / Sunny (Font Awesome )
    case 116: return night ? "\ue379" : "\ue302"  // Partly cloudy
    case 119: case 122: return "\ue312"          // Overcast / Cloudy
    case 143: case 248: case 260: return night ? "\ue346" : "\ue313"  // Fog
    case 176: case 263: case 353: return night ? "\ue334" : "\ue308"  // Patchy rain
    case 179: case 227: case 230: case 323: case 326: case 368: return night ? "\ue327" : "\ue30a"  // Snow
    case 182: case 185: case 281: case 284: case 311: case 314:
    case 317: case 320: case 350: case 362: case 365: case 374: case 377: return "\ue3ad"  // Sleet / hail
    case 200: case 386: case 389: case 392: case 395: return "\ue31d"  // Thunderstorm
    case 266: case 293: case 296: case 299: case 302: case 305: case 308: case 356: case 359: return "\ue318"  // Rain
    case 329: case 332: case 335: case 338: case 371: return "\ue31a"  // Heavy snow
    default: return "\ue312"
  }
}

// Forecast timestamps are location-local wall times, not the computer's timezone.
function forecastWallTime(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) return NaN
  return Date.parse(value + "Z")
}

function hourlyForecast(report, nowMs, hours) {
  var hourly = report && report.hourly
  if (!hourly || !Array.isArray(hourly.time) || !Array.isArray(hourly.temperature_2m)) return []
  var offset = Number(report.utc_offset_seconds)
  if (!isFinite(offset)) return []
  var now = nowMs + offset * 1000
  var start = Math.floor(now / 3600000) * 3600000
  var end = start + hours * 3600000
  var entries = []
  for (var i = 0; i < hourly.time.length; i++) {
    var time = forecastWallTime(hourly.time[i])
    if (!isFinite(time) || time < start || time >= end) continue
    var probability = hourly.precipitation_probability ? hourly.precipitation_probability[i] : null
    entries.push({
      kind: "hour",
      time: time,
      date: hourly.time[i].slice(0, 10),
      label: hourLabel(hourly.time[i], false),
      temperature: hourly.temperature_2m[i],
      probability: typeof probability === "number" && isFinite(probability) && probability >= 0 && probability <= 100
        ? probability : null,
      precipitation: hourly.precipitation ? hourly.precipitation[i] : null,
      icon: hourly.weather_code && hourly.weather_code[i] !== null
        ? iconForOpenMeteoCode(hourly.weather_code[i], hourly.is_day && hourly.is_day[i] === 0) : ""
    })
  }
  if (!entries.length) return []
  var daily = report.daily || {}
  ;["sunrise", "sunset"].forEach(function(kind) {
    var times = daily[kind] || []
    for (var j = 0; j < times.length; j++) {
      var time = forecastWallTime(times[j])
      if (!isFinite(time) || time < start || time >= end) continue
      entries.push({
        kind: kind,
        time: time,
        date: times[j].slice(0, 10),
        label: hourLabel(times[j], true),
        icon: kind === "sunrise" ? "\ue30c" : "\ue32b"
      })
    }
  })
  entries.sort(function(a, b) { return a.time - b.time })
  return entries
}

function hourLabel(isoTime, isSolar) {
  var parts = isoTime.slice(11, 16).split(":")
  var hour = parseInt(parts[0], 10)
  var minute = parts[1]
  var ampm = hour >= 12 ? "PM" : "AM"
  var h12 = hour % 12 || 12
  if (isSolar) return h12 + ":" + minute + " " + ampm
  return h12 + " " + ampm
}

function hourlyTemperature(celsius, useImperial) {
  if (celsius === null || celsius === undefined || !isFinite(Number(celsius))) return ""
  var c = Number(celsius)
  var value = useImperial ? Math.round((c * 9 / 5) + 32) : Math.round(c)
  return value + "°"
}

function hourlyPrecipitation(mm, useImperial) {
  if (mm === null || mm === undefined || !isFinite(Number(mm))) return "—"
  var n = Number(mm)
  if (n <= 0) return "0"
  if (useImperial) {
    var inches = n * 0.0393701
    return (inches < 0.01 ? "<0.01" : inches.toFixed(2)) + " in"
  }
  return (n < 0.1 ? "<0.1" : n.toFixed(1)) + " mm"
}

// Returns array of lines for the hover tooltip (excluding the trailing version line)
function buildBarHoverLines(currentCondition, dailyForecastDays, useImperial, locationName) {
  var loc = locationName && locationName.trim() ? locationName.trim() : ""
  var title = loc ? ("Weather report for " + loc) : "Weather report"
  if (!currentCondition) return [title]

  var temp = useImperial ? currentCondition.temp_F : currentCondition.temp_C
  var unit = useImperial ? "°F" : "°C"
  var desc = currentCondition.description || "Current Conditions"

  var hi = useImperial ? currentCondition.todayMaxF : currentCondition.todayMaxC
  var lo = useImperial ? currentCondition.todayMinF : currentCondition.todayMinC
  var feels = useImperial ? currentCondition.FeelsLikeF : currentCondition.FeelsLikeC
  var wind = (useImperial ? currentCondition.windspeedMiles + " mph" : currentCondition.windspeedKmph + " km/h")
  if (currentCondition.windDirectionCardinal) wind += " " + currentCondition.windDirectionCardinal

  var lines = [title]

  var line2 = desc + " · " + temp + unit
  if (hi && lo) line2 += " (H: " + hi + "° / L: " + lo + "°)"
  lines.push(line2)

  var line3 = "Feels like: " + feels + unit + " · Humidity: " + currentCondition.humidity + "% · Wind: " + wind
  lines.push(line3)

  if (currentCondition.todayPrecipProbability !== null && currentCondition.todayPrecipProbability !== undefined) {
    lines.push("Precipitation chance today: " + currentCondition.todayPrecipProbability + "%")
  }

  // Next upcoming day snapshot
  if (dailyForecastDays && dailyForecastDays.length > 1) {
    var tomorrow = dailyForecastDays[1]
    var tHi = useImperial ? tomorrow.maxtempF : tomorrow.maxtempC
    var tLo = useImperial ? tomorrow.mintempF : tomorrow.mintempC
    var tDesc = tomorrow.description || ""
    lines.push("Tomorrow: " + tDesc + " · " + tHi + "° / " + tLo + "°" +
      (tomorrow.precipitationProbability !== null ? " (" + tomorrow.precipitationProbability + "% rain)" : ""))
  }

  return lines
}

// Generates the rich multi-line bar hover tooltip
function buildBarHoverTooltip(pluginVersion, currentCondition, dailyForecastDays, useImperial, locationName) {
  var lines = buildBarHoverLines(currentCondition, dailyForecastDays, useImperial, locationName)
  var versionLine = "fred.weather v" + (pluginVersion || "1.0.2")

  // Blank line separator above the bottom version line
  lines.push("")
  lines.push(versionLine)

  return lines.join("\n")
}

if (typeof module !== "undefined") {
  module.exports = {
    parseLocationFile: parseLocationFile,
    wttrLocationQuery: wttrLocationQuery,
    parseGeocodingResults: parseGeocodingResults,
    locationCommit: locationCommit,
    validCoordinates: validCoordinates,
    coordinateLocation: coordinateLocation,
    formatLocationDisplay: formatLocationDisplay,
    locationSearchUrl: locationSearchUrl,
    parseLocationSearch: parseLocationSearch,
    locationMapUrl: locationMapUrl,
    isFutureForecastDate: isFutureForecastDate,
    roundedTemp: roundedTemp,
    celsiusToFahrenheit: celsiusToFahrenheit,
    formatTemp: formatTemp,
    normalizedUnit: normalizedUnit,
    localeUsesImperial: localeUsesImperial,
    countryUsesImperial: countryUsesImperial,
    shouldUseImperial: shouldUseImperial,
    degreesToCardinal: degreesToCardinal,
    dayName: dayName,
    shortDayName: shortDayName,
    weatherDescription: weatherDescription,
    openMeteoForecastDays: openMeteoForecastDays,
    openMeteoCurrentCondition: openMeteoCurrentCondition,
    currentIcon: currentIcon,
    provisionalCurrentIcon: provisionalCurrentIcon,
    weatherResponseCompletesSave: weatherResponseCompletesSave,
    parseWeatherCache: parseWeatherCache,
    updatedWeatherCache: updatedWeatherCache,
    wttrNextForecastDays: wttrNextForecastDays,
    buildForecastDays: buildForecastDays,
    bareTempForDay: bareTempForDay,
    dayIcon: dayIcon,
    iconForOpenMeteoCode: iconForOpenMeteoCode,
    iconForCode: iconForCode,
    forecastWallTime: forecastWallTime,
    hourlyForecast: hourlyForecast,
    hourLabel: hourLabel,
    hourlyTemperature: hourlyTemperature,
    hourlyPrecipitation: hourlyPrecipitation,
    buildBarHoverLines: buildBarHoverLines,
    buildBarHoverTooltip: buildBarHoverTooltip
  }
}
