import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons
import qs.Ui
import "Model.js" as Model
import "Network.js" as Network
import "WeatherStore.js" as WeatherStore

Panel {
  id: root
  moduleName: "fred.weather"
  ipcTarget: "omarchy.weather"
  manageIpc: false

  property var anchorItem: null
  property bool openedFromHotkey: false
  property string pluginVersion: "1.0.3"
  readonly property color foreground: Color.popups.text
  readonly property string fontFamily: root.bar ? root.bar.fontFamily : Style.font.family

  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root

  readonly property string screenName: {
    if (panel && panel.screen && panel.screen.name) return String(panel.screen.name)
    if (anchorItem && anchorItem.QsWindow && anchorItem.QsWindow.window && anchorItem.QsWindow.window.screen)
      return String(anchorItem.QsWindow.window.screen.name || "")
    if (root.bar && root.bar.screen && root.bar.screen.name) return String(root.bar.screen.name)
    return ""
  }

  onScreenNameChanged: {
    if (screenName) WeatherStore.register(screenName, root)
  }

  function showHover() {
    if (hostWidget && "hoverOpen" in hostWidget) hostWidget.hoverOpen = true
  }

  function hideHover() {
    if (hostWidget && "hoverOpen" in hostWidget) hostWidget.hoverOpen = false
  }

  IpcHandler {
    target: "fred.weather"

    function open(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.open("", cur, Hyprland.monitors)
    }
    function close(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.close("", cur, Hyprland.monitors)
    }
    function show(): void { open() }
    function hide(): void { close() }
    function toggle(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.toggle("", cur, Hyprland.monitors)
    }
    function openMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.open(monitor, cur, Hyprland.monitors)
    }
    function closeMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.close(monitor, cur, Hyprland.monitors)
    }
    function toggleMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.toggle(monitor, cur, Hyprland.monitors)
    }
    function showHover(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.showHover(monitor, cur, Hyprland.monitors)
    }
    function hideHover(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.hideHover(monitor, cur, Hyprland.monitors)
    }
    function refresh(): void { WeatherStore.refreshAll(root) }
    function edit(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      var p = WeatherStore.resolveTargetPanel("", cur, Hyprland.monitors)
      if (p) {
        p.open()
        p.startEditingLocation()
      }
    }
  }

  IpcHandler {
    target: "omarchy.weather"

    function open(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.open("", cur, Hyprland.monitors)
    }
    function close(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.close("", cur, Hyprland.monitors)
    }
    function show(): void { open() }
    function hide(): void { close() }
    function toggle(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.toggle("", cur, Hyprland.monitors)
    }
    function openMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.open(monitor, cur, Hyprland.monitors)
    }
    function closeMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.close(monitor, cur, Hyprland.monitors)
    }
    function toggleMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.toggle(monitor, cur, Hyprland.monitors)
    }
    function showHover(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.showHover(monitor, cur, Hyprland.monitors)
    }
    function hideHover(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      WeatherStore.hideHover(monitor, cur, Hyprland.monitors)
    }
    function refresh(): void { WeatherStore.refreshAll(root) }
    function edit(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      var p = WeatherStore.resolveTargetPanel("", cur, Hyprland.monitors)
      if (p) {
        p.open()
        p.startEditingLocation()
      }
    }
  }

  function open() {
    openedFromHotkey = false
    setCenterHoverRevealSuppressed(false)
    root.controller.show()
    locationFile.reload()
    root.refresh()
  }

  function openFromHotkey() {
    openedFromHotkey = true
    root.controller.show()
    locationFile.reload()
    root.refresh()
    Qt.callLater(function() {
      if (root.opened) setCenterHoverRevealSuppressed(true)
    })
  }

  function close() {
    setCenterHoverRevealSuppressed(false)
    if (root.editingLocation) root.cancelEditingLocation()
    root.controller.hide()
  }

  function toggle() {
    if (root.opened) root.close()
    else root.openFromHotkey()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  function setCenterHoverRevealSuppressed(value) {
    if (root.bar && typeof root.bar.setCenterHoverRevealSuppressed === "function")
      root.bar.setCenterHoverRevealSuppressed(value)
    else if (root.bar && "centerHoverRevealSuppressed" in root.bar)
      root.bar.centerHoverRevealSuppressed = value
  }

  // --- Weather Data State --------------------------------------------------

  property var report: null
  property double reportUpdatedAt: 0
  property string reportLocationQuery: ""
  property bool reportIsLive: false

  property var dailyForecastReport: null
  property double forecastClock: Date.now()
  property double hourlyUpdatedAt: 0
  property string hourlyLocationQuery: ""
  property bool hourlyFetchFailed: false

  readonly property var hourlyEntries: hourlyLocationQuery === locationQuery
    ? Model.hourlyForecast(dailyForecastReport, forecastClock, 48) : []
  readonly property string hourlyStatus: hourlyFetchFailed && hourlyEntries.length > 0
    ? "Update failed \u00b7 Showing last forecast"
    : ((hourlyUpdatedAt > 0 && forecastClock - hourlyUpdatedAt > root.refreshMinutes * 120000)
      || (currentUpdatedAt > 0 && forecastClock - currentUpdatedAt > root.refreshMinutes * 120000)
      ? "Forecast may be outdated \u00b7 Middle-click weather to retry" : "")

  property string wttrLocation: ""
  property bool locationReady: false
  property bool cacheReady: false
  property bool weatherReady: false
  property var weatherCache: null
  property bool cacheWritePending: false
  property bool cacheWriteInFlight: false

  readonly property string weatherCacheDir: (Quickshell.env("XDG_CACHE_HOME")
    || Quickshell.env("HOME") + "/.cache") + "/fred.weather"
  readonly property string weatherCachePath: weatherCacheDir + "/weather-cache.json"

  function initializeWeather() {
    if (weatherReady || !locationReady || !cacheReady) return
    if (weatherCache && weatherCache.locationQuery === locationQuery) {
      if (weatherCache.report) {
        report = weatherCache.report.data
        reportUpdatedAt = weatherCache.report.updatedAt
        reportLocationQuery = weatherCache.locationQuery
      }
      if (weatherCache.dailyForecast) {
        dailyForecastReport = weatherCache.dailyForecast.data
        hourlyUpdatedAt = weatherCache.dailyForecast.updatedAt
        hourlyLocationQuery = weatherCache.locationQuery
      }
      label = Model.currentIcon(openMeteoCurrent, "\uf185")
    }
    weatherReady = true
    Qt.callLater(root.refresh)
  }

  function scheduleCacheWrite() {
    if (!weatherReady) return
    cacheWritePending = true
    if (!cacheWriteInFlight) writeWeatherCache()
  }

  function writeWeatherCache() {
    if (cacheWriteInFlight || !cacheWritePending) return
    cacheWritePending = false
    cacheWriteInFlight = true
    try {
      weatherCacheFile.setText(JSON.stringify(root.weatherCache, null, 2))
    } catch (e) {
      cacheWriteInFlight = false
      console.warn("Failed to write weather cache: " + e)
    }
  }

  // --- Location & Settings -------------------------------------------------

  property var configuredLocationState: ({ name: "", latitude: null, longitude: null })
  readonly property string configuredLocation: configuredLocationState.name
  readonly property string locationQuery: Model.wttrLocationQuery(configuredLocationState.name, configuredLocationState.latitude, configuredLocationState.longitude)

  onLocationQueryChanged: {
    reportIsLive = false
    if (!weatherReady) return
    if (savingLocation) savingLocationQueryStarted = true
    forecastRetries = 0
    dailyForecastRetries = 0
    forecastRetryTimer.stop()
    dailyForecastRetryTimer.stop()
    refresh()
  }

  readonly property bool hasConfiguredCoordinates: !isNaN(parseFloat(String(configuredLocationState.latitude))) && !isNaN(parseFloat(String(configuredLocationState.longitude)))
  readonly property var openMeteoCurrent: Model.openMeteoCurrentCondition(dailyForecastReport)
  readonly property var current: (hasConfiguredCoordinates && openMeteoCurrent) ? openMeteoCurrent : ((report && report.current_condition && report.current_condition[0]) ? report.current_condition[0] : openMeteoCurrent)
  readonly property double currentUpdatedAt: current === openMeteoCurrent ? hourlyUpdatedAt : reportUpdatedAt
  readonly property var areaInfo: report && report.nearest_area && report.nearest_area[0] ? report.nearest_area[0] : null

  readonly property string todayString: new Date().toISOString().slice(0, 10)
  readonly property var forecastDays: Model.openMeteoForecastDays(dailyForecastReport, todayString, 10)

  readonly property string reportCountry: areaInfo && areaInfo.country && areaInfo.country[0] ? areaInfo.country[0].value : ""
  readonly property bool useImperial: Model.shouldUseImperial(setting("unit", ""), Qt.locale().name, reportCountry)
  readonly property int refreshMinutes: Math.max(1, parseInt(setting("refreshMinutes", 15), 10) || 15)

  readonly property string reportLocation: Model.formatLocationDisplay(configuredLocation, areaInfo, wttrLocation)
  readonly property string reportTempNum: current ? String(useImperial ? current.temp_F : current.temp_C) : ""
  readonly property string tempUnit: "°" + (useImperial ? "F" : "C")
  readonly property string reportFeels: current ? (useImperial ? current.FeelsLikeF + tempUnit : current.FeelsLikeC + tempUnit) : ""
  readonly property string reportWind: current ? (useImperial ? (current.windspeedMiles + " mph" + (current.windDirectionCardinal ? " " + current.windDirectionCardinal : "")) : (current.windspeedKmph + " km/h" + (current.windDirectionCardinal ? " " + current.windDirectionCardinal : ""))) : ""
  readonly property string reportHumidity: current ? (current.humidity + "%") : ""

  property string label: "\uf185"

  readonly property var hoverLines: Model.buildBarHoverLines(
    root.current,
    root.forecastDays,
    root.useImperial,
    root.reportLocation
  )

  readonly property string barHoverTooltip: Model.buildBarHoverTooltip(
    root.pluginVersion,
    root.current,
    root.forecastDays,
    root.useImperial,
    root.reportLocation
  )

  function refresh() {
    if (!weatherReady) return
    forecastClock = Date.now()
    forecastRetries = 0
    dailyForecastRetries = 0
    refreshForecast()
    if (root.locationQuery === "" && !locationProc.running) locationProc.running = true
    refreshDailyForecast(null)
  }

  function applyDailyForecast(payload, updatedAt, query) {
    if (!payload || query !== root.locationQuery) return
    root.dailyForecastReport = payload
    root.hourlyUpdatedAt = updatedAt
    root.hourlyLocationQuery = query
    root.hourlyFetchFailed = false
    root.forecastClock = updatedAt
    root.dailyForecastRetries = 0
    root.label = Model.currentIcon(root.openMeteoCurrent, "\uf185")
    root.weatherCache = Model.updatedWeatherCache(root.weatherCache, root.locationQuery, "dailyForecast", payload, root.hourlyUpdatedAt)
  }

  function applyReport(payload, updatedAt, query) {
    if (!payload || query !== root.locationQuery) return
    root.report = payload
    root.reportUpdatedAt = updatedAt
    root.reportLocationQuery = query
    root.reportIsLive = true
    root.forecastRetries = 0
    root.label = Model.currentIcon(root.openMeteoCurrent, Model.currentIcon(root.current, "\uf185"))
    root.weatherCache = Model.updatedWeatherCache(root.weatherCache, root.locationQuery, "report", payload, root.reportUpdatedAt)
  }

  function refreshForecast() {
    if (forecastProc.running) return
    forecastProc.requestQuery = locationQuery
    forecastProc.running = true
  }

  function forecastCoordinates(sourceReport) {
    var lat = parseFloat(String(root.configuredLocationState.latitude))
    var lon = parseFloat(String(root.configuredLocationState.longitude))
    if (isNaN(lat) || isNaN(lon)) {
      var canReuseArea = reportLocationQuery === locationQuery && (locationQuery !== "" || reportIsLive)
      var area = sourceReport && sourceReport.nearest_area && sourceReport.nearest_area[0]
        ? sourceReport.nearest_area[0] : (canReuseArea ? root.areaInfo : null)
      if (!area) return null
      lat = parseFloat(String(area.latitude))
      lon = parseFloat(String(area.longitude))
    }
    return Model.validCoordinates(lat, lon) ? [lat, lon] : null
  }

  function refreshDailyForecast(sourceReport) {
    if (dailyForecastProc.running) return
    var coordinates = forecastCoordinates(sourceReport)
    if (!coordinates) return

    var url = "https://api.open-meteo.com/v1/forecast"
      + "?latitude=" + encodeURIComponent(String(coordinates[0]))
      + "&longitude=" + encodeURIComponent(String(coordinates[1]))
      + "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,sunrise,sunset"
      + "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,is_day"
      + "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code,is_day"
      + "&forecast_days=10"
      + "&timezone=auto"

    dailyForecastProc.command = Network.curlCommand(url, 5, Network.responseLimits.dailyForecast)
    dailyForecastProc.requestQuery = locationQuery
    dailyForecastProc.requestCoordinates = coordinates
    dailyForecastProc.running = true
  }

  // --- Location Editing State ----------------------------------------------

  property bool editingLocation: false
  property bool savingLocation: false
  property bool savingLocationQueryStarted: false
  property var locationSuggestions: []
  property string locationError: ""
  property int suggestionIndex: 0

  function startEditingLocation() {
    editingLocation = true
    savingLocation = false
    savingLocationQueryStarted = false
    locationSuggestions = []
    locationError = ""
    suggestionIndex = 0
    Qt.callLater(function() {
      locationField.text = root.configuredLocation
      locationField.selectAll()
      locationField.forceActiveFocus()
    })
  }

  function cancelEditingLocation() {
    editingLocation = false
    savingLocation = false
    savingLocationQueryStarted = false
    locationError = ""
    locationSearchDebounce.stop()
    locationSearchProc.running = false
    panelKeyCatcher.forceActiveFocus()
  }

  function commitLocationChoice(choice) {
    if (!choice || (!choice.name && choice.latitude === null)) {
      clearLocationPreference()
      return
    }
    saveLocationPreference(choice.name, choice.latitude, choice.longitude)
  }

  function saveLocationPreference(name, latitude, longitude) {
    savingLocation = true
    savingLocationQueryStarted = false
    locationError = ""
    var cmd = ["omarchy-weather-location", "--set", name]
    if (latitude !== null && longitude !== null && !isNaN(Number(latitude)) && !isNaN(Number(longitude))) {
      cmd.push(String(latitude) + "," + String(longitude))
    }
    locationSaveProc.command = cmd
    locationSaveProc.running = true
  }

  function clearLocationPreference() {
    savingLocation = true
    savingLocationQueryStarted = false
    locationError = ""
    locationClearProc.command = ["omarchy-weather-location", "--clear"]
    locationClearProc.running = true
  }

  function openCurrentPinMap() {
    var lat = parseFloat(String(configuredLocationState.latitude))
    var lon = parseFloat(String(configuredLocationState.longitude))
    if (isNaN(lat) || isNaN(lon)) return
    var mapUrl = Model.locationMapUrl(lat, lon)
    if (mapUrl) openMapProc.command = ["xdg-open", mapUrl]
    openMapProc.running = true
  }

  Process {
    id: openMapProc
    environment: Network.closedEnv
  }

  // --- Files & Timers ------------------------------------------------------

  Timer {
    interval: 60000
    running: root.opened
    repeat: true
    onTriggered: root.forecastClock = Date.now()
  }

  Timer {
    id: autoRefreshTimer
    interval: root.refreshMinutes * 60000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  property int forecastRetries: 0
  Timer {
    id: forecastRetryTimer
    interval: Math.min(60000, 5000 * Math.pow(2, forecastRetries))
    repeat: false
    onTriggered: root.refreshForecast()
  }

  property int dailyForecastRetries: 0
  Timer {
    id: dailyForecastRetryTimer
    interval: Math.min(60000, 5000 * Math.pow(2, dailyForecastRetries))
    repeat: false
    onTriggered: root.refreshDailyForecast(null)
  }

  function scheduleDailyForecastRetry() {
    root.hourlyFetchFailed = true
    if (root.dailyForecastRetries < 3) {
      dailyForecastRetryTimer.start()
      root.dailyForecastRetries++
    }
  }

  FileView {
    id: locationFile
    path: Quickshell.env("HOME") + "/.local/state/omarchy/settings/weather.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      var parsed = Model.parseLocationFile(text())
      root.configuredLocationState = parsed
      if (!root.locationReady) {
        root.locationReady = true
        Qt.callLater(root.initializeWeather)
      }
    }
    onLoadFailed: {
      root.configuredLocationState = { name: "", latitude: null, longitude: null }
      if (!root.locationReady) {
        root.locationReady = true
        Qt.callLater(root.initializeWeather)
      }
    }
  }

  Timer {
    interval: 1500
    running: true
    onTriggered: locationFile.reload()
  }

  FileView {
    id: weatherCacheFile
    path: root.weatherCachePath
    blockLoading: false
    blockWrites: false
    atomicWrites: true
    printErrors: false
    onLoaded: {
      if (root.cacheReady) return
      try {
        var raw = String(text() || "").trim()
        if (raw.length > 0)
          root.weatherCache = Model.parseWeatherCache(Network.responseText(raw, 512 * 1024))
      } catch (e) {
        console.warn("Weather cache load failed: " + e)
      }
      root.cacheReady = true
      Qt.callLater(root.initializeWeather)
    }
    onLoadFailed: function(error) {
      root.cacheReady = true
      Qt.callLater(root.initializeWeather)
    }
    onSaved: {
      root.cacheWriteInFlight = false
      if (root.cacheWritePending) Qt.callLater(root.writeWeatherCache)
    }
    onSaveFailed: function(error) {
      root.cacheWriteInFlight = false
      if (root.cacheWritePending) Qt.callLater(root.writeWeatherCache)
    }
  }

  // --- Network Processes ---------------------------------------------------

  Process {
    id: ensureCacheDir
    command: ["mkdir", "-p", root.weatherCacheDir]
    environment: Network.closedEnv
  }

  Process {
    id: dailyForecastProc
    property string requestQuery: ""
    property var requestCoordinates: null
    environment: Network.closedEnv
    stdout: StdioCollector {
      id: dailyForecastStdout
      waitForEnd: true
      onStreamFinished: {
        dailyForecastProc.running = false
        var raw = String(dailyForecastStdout.text || "").trim()
        if (!raw) {
          root.scheduleDailyForecastRetry()
          return
        }
        if (dailyForecastProc.requestQuery !== root.locationQuery) return
        try {
          var payload = JSON.parse(Network.responseText(raw, Network.responseLimits.dailyForecast))
          if (payload.error) throw new Error(payload.reason || "Open-Meteo returned an error")
          root.dailyForecastReport = payload
          root.hourlyUpdatedAt = Date.now()
          root.hourlyLocationQuery = dailyForecastProc.requestQuery
          root.hourlyFetchFailed = false
          root.forecastClock = root.hourlyUpdatedAt
          root.dailyForecastRetries = 0
          root.label = Model.currentIcon(root.openMeteoCurrent, "\uf185")
          root.weatherCache = Model.updatedWeatherCache(root.weatherCache, root.locationQuery, "dailyForecast", payload, root.hourlyUpdatedAt)
          root.scheduleCacheWrite()
          WeatherStore.broadcastDailyForecast(root.screenName, payload, root.hourlyUpdatedAt, dailyForecastProc.requestQuery)
          if (root.savingLocation && Model.weatherResponseCompletesSave(root.hasConfiguredCoordinates, "open-meteo"))
            root.editingLocation = false
        } catch (e) {
          root.scheduleDailyForecastRetry()
        }
      }
    }
  }

  Process {
    id: forecastProc
    property string requestQuery: ""
    command: Network.curlCommand("https://wttr.in/" + root.locationQuery + "?format=j1", 10, Network.responseLimits.forecast)
    environment: Network.closedEnv
    stdout: StdioCollector {
      id: forecastStdout
      waitForEnd: true
      onStreamFinished: {
        forecastProc.running = false
        var raw = String(forecastStdout.text || "").trim()
        if (!raw) {
          if (root.forecastRetries < 3) {
            forecastRetryTimer.start()
            root.forecastRetries++
          }
          return
        }
        if (forecastProc.requestQuery !== root.locationQuery) return
        try {
          var payload = JSON.parse(Network.responseText(raw, Network.responseLimits.forecast))
          root.report = payload
          root.reportUpdatedAt = Date.now()
          root.reportLocationQuery = forecastProc.requestQuery
          root.reportIsLive = true
          root.forecastRetries = 0
          root.label = Model.currentIcon(root.openMeteoCurrent, Model.currentIcon(root.current, "\uf185"))
          root.weatherCache = Model.updatedWeatherCache(root.weatherCache, root.locationQuery, "report", payload, root.reportUpdatedAt)
          root.scheduleCacheWrite()
          WeatherStore.broadcastReport(root.screenName, payload, root.reportUpdatedAt, forecastProc.requestQuery)
          if (!root.hasConfiguredCoordinates && !dailyForecastProc.running)
            root.refreshDailyForecast(payload)
          if (root.savingLocation && Model.weatherResponseCompletesSave(root.hasConfiguredCoordinates, "wttr"))
            root.editingLocation = false
        } catch (e) {
          if (root.forecastRetries < 3) {
            forecastRetryTimer.start()
            root.forecastRetries++
          }
        }
      }
    }
  }

  Process {
    id: locationProc
    command: ["omarchy-weather-location"]
    environment: Network.closedEnv
    stdout: StdioCollector {
      id: locationStdout
      waitForEnd: true
      onStreamFinished: {
        locationProc.running = false
        var raw = String(locationStdout.text || "").trim()
        if (locationProc.exitCode === 0 && raw.length > 0)
          root.wttrLocation = raw
      }
    }
  }

  Timer {
    id: locationSearchDebounce
    interval: 300
    repeat: false
    onTriggered: {
      var query = locationField.text.trim()
      if (query.length < 2) {
        root.locationSuggestions = []
        return
      }
      var coordLoc = Model.coordinateLocation(query)
      if (coordLoc) {
        root.locationSuggestions = [coordLoc]
        return
      }
      var url = Model.locationSearchUrl(query)
      locationSearchProc.command = Network.curlCommand(url, 5, Network.responseLimits.geocode)
      locationSearchProc.query = query
      locationSearchProc.running = true
    }
  }

  Process {
    id: locationSearchProc
    property string query: ""
    environment: Network.closedEnv
    stdout: StdioCollector {
      id: locationSearchStdout
      waitForEnd: true
      onStreamFinished: {
        locationSearchProc.running = false
        var raw = String(locationSearchStdout.text || "").trim()
        if (!raw) return
        try {
          root.locationSuggestions = Model.parseLocationSearch(raw, locationSearchProc.query)
          root.suggestionIndex = 0
        } catch (e) {
          root.locationSuggestions = []
        }
      }
    }
  }

  Process {
    id: locationSaveProc
    environment: Network.closedEnv
    onExited: function(code) {
      if (code === 0) locationFile.reload()
      else {
        root.savingLocation = false
        root.locationError = "Failed to save location"
      }
    }
  }

  Process {
    id: locationClearProc
    environment: Network.closedEnv
    onExited: function(code) {
      if (code === 0) locationFile.reload()
      else {
        root.savingLocation = false
        root.locationError = "Failed to clear location"
      }
    }
  }

  // --- Multi-Monitor Focus-Isolated Panel Window ---------------------------

  WeatherPanelWindow {
    id: panel
    anchorItem: root.anchorItem
    bar: root.bar
    owner: root
    open: root.opened
    contentWidth: panel.fittedContentWidth(Style.space(640))
    contentHeight: panel.fittedContentHeight(mainColumn.implicitHeight, Style.space(780))
    focusTarget: panelKeyCatcher

    PanelKeyCatcher {
      id: panelKeyCatcher
      focus: true

      Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Escape) {
          if (root.editingLocation) root.cancelEditingLocation()
          else root.close()
          event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
          if (!root.editingLocation) root.startEditingLocation()
          else if (root.locationSuggestions.length > 0) {
            root.commitLocationChoice(root.locationSuggestions[root.suggestionIndex])
          } else {
            root.commitLocationChoice({ name: locationField.text.trim(), latitude: null, longitude: null })
          }
          event.accepted = true
        } else if (event.key === Qt.Key_Tab) {
          root.switchPanel(event.modifiers & Qt.ShiftModifier ? -1 : 1)
          event.accepted = true
        }
      }
    }

    Flickable {
      anchors.fill: parent
      contentWidth: width
      contentHeight: mainColumn.implicitHeight
      clip: true
      boundsBehavior: Flickable.StopAtBounds

      Column {
        id: mainColumn
        width: parent.width
        spacing: Style.space(14)

        // 1. Header Bar: Location, Status, and Controls
        Row {
          width: parent.width
          spacing: Style.space(8)

          // Location Pill (Click to edit)
          Rectangle {
            height: Style.space(30)
            width: Math.min(parent.width - controlsRow.width - parent.spacing, locationTextRow.implicitWidth + Style.space(16))
            radius: Style.cornerRadius
            color: locMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"
            border.width: 1
            border.color: Util.alpha(root.foreground, 0.15)

            MouseArea {
              id: locMouse
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.PointingHandCursor
              onClicked: root.startEditingLocation()
            }

            Row {
              id: locationTextRow
              anchors.centerIn: parent
              spacing: Style.space(6)

              Text {
                text: "\uf041" // map pin icon
                color: Color.accent
                font.family: root.fontFamily
                font.pixelSize: Style.font.bodySmall
                anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                text: root.reportLocation || "Detecting Location..."
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
                font.bold: true
                elide: Text.ElideRight
                anchors.verticalCenter: parent.verticalCenter
              }
            }
          }

          Item {
            // Spacer
            width: parent.width - locationTextRow.parent.width - controlsRow.width - parent.spacing
            height: 1
          }

          // Controls Row (Map Pin, Refresh, Close)
          Row {
            id: controlsRow
            spacing: Style.space(6)
            anchors.verticalCenter: parent.verticalCenter

            // View Pin on Map (if coordinates configured)
            Rectangle {
              visible: root.hasConfiguredCoordinates
              width: Style.space(30)
              height: Style.space(30)
              radius: Style.cornerRadius
              color: mapMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"

              Text {
                anchors.centerIn: parent
                text: "\uf279" // map icon
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
              }

              MouseArea {
                id: mapMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.openCurrentPinMap()
              }
            }

            // Refresh Button
            Rectangle {
              width: Style.space(30)
              height: Style.space(30)
              radius: Style.cornerRadius
              color: refMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"

              Text {
                anchors.centerIn: parent
                text: "\uf021" // sync/refresh icon
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
              }

              MouseArea {
                id: refMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.refresh()
              }
            }

            // Close Button
            Rectangle {
              width: Style.space(30)
              height: Style.space(30)
              radius: Style.cornerRadius
              color: closeMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.urgent) : "transparent"

              Text {
                anchors.centerIn: parent
                text: "\u2715" // close cross
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
              }

              MouseArea {
                id: closeMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.close()
              }
            }
          }
        }

        // 2. Location Search Bar (Visible when editingLocation)
        Column {
          visible: root.editingLocation
          width: parent.width
          spacing: Style.space(6)

          Row {
            width: parent.width
            spacing: Style.space(8)

            TextField {
              id: locationField
              width: parent.width - btnCancelLoc.width - btnClearLoc.width - parent.spacing * 2
              placeholderText: "Search city, US ZIP, or lat, lon..."
              font.family: root.fontFamily
              onTextChanged: locationSearchDebounce.restart()
              Keys.onPressed: function(e) {
                if (e.key === Qt.Key_Down && root.locationSuggestions.length > 0) {
                  root.suggestionIndex = Math.min(root.locationSuggestions.length - 1, root.suggestionIndex + 1)
                  e.accepted = true
                } else if (e.key === Qt.Key_Up && root.locationSuggestions.length > 0) {
                  root.suggestionIndex = Math.max(0, root.suggestionIndex - 1)
                  e.accepted = true
                } else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) {
                  if (root.locationSuggestions.length > 0)
                    root.commitLocationChoice(root.locationSuggestions[root.suggestionIndex])
                  else
                    root.commitLocationChoice({ name: locationField.text.trim(), latitude: null, longitude: null })
                  e.accepted = true
                } else if (e.key === Qt.Key_Escape) {
                  root.cancelEditingLocation()
                  e.accepted = true
                }
              }
            }

            Rectangle {
              id: btnClearLoc
              width: Style.space(64)
              height: Style.space(28)
              radius: Style.cornerRadius
              color: clearLocMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"
              border.width: 1
              border.color: Util.alpha(root.foreground, 0.2)
              Text {
                anchors.centerIn: parent
                text: "IP Auto"
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.bodySmall
              }
              MouseArea {
                id: clearLocMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.clearLocationPreference()
              }
            }

            Rectangle {
              id: btnCancelLoc
              width: Style.space(64)
              height: Style.space(28)
              radius: Style.cornerRadius
              color: cancelLocMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.urgent) : "transparent"
              border.width: 1
              border.color: Util.alpha(root.foreground, 0.2)
              Text {
                anchors.centerIn: parent
                text: "Cancel"
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.bodySmall
              }
              MouseArea {
                id: cancelLocMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.cancelEditingLocation()
              }
            }
          }

          // Search Suggestions Dropdown
          Column {
            width: parent.width
            spacing: Style.space(2)
            visible: root.locationSuggestions.length > 0

            Repeater {
              model: root.locationSuggestions
              Rectangle {
                required property var modelData
                required property int index
                width: parent.width
                height: Style.space(28)
                radius: Style.cornerRadius
                color: (index === root.suggestionIndex || sugMouse.containsMouse)
                  ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"

                Text {
                  anchors.fill: parent
                  anchors.leftMargin: Style.space(8)
                  verticalAlignment: Text.AlignVCenter
                  text: (modelData.name || "") + (modelData.description ? " \u2014 " + modelData.description : "")
                  color: root.foreground
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.bodySmall
                  elide: Text.ElideRight
                }

                MouseArea {
                  id: sugMouse
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.commitLocationChoice(parent.modelData)
                }
              }
            }
          }
        }

        // 3. Hero Section: Current Conditions
        Rectangle {
          width: parent.width
          height: Style.space(110)
          radius: Style.cornerRadius
          color: Util.alpha(root.foreground, 0.04)
          border.width: 1
          border.color: Util.alpha(root.foreground, 0.12)

          Row {
            anchors.fill: parent
            anchors.margins: Style.space(12)
            spacing: Style.space(16)

            // Giant Icon
            Text {
              width: Style.space(70)
              height: Style.space(70)
              anchors.verticalCenter: parent.verticalCenter
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
              text: Model.currentIcon(root.openMeteoCurrent, "\uf185")
              color: Color.accent
              font.family: root.fontFamily
              font.pixelSize: Style.font.displayLarge * 1.6
            }

            // Temp + Condition Description
            Column {
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(2)
              width: Style.space(160)

              Row {
                spacing: Style.space(2)
                Text {
                  text: root.reportTempNum || "—"
                  color: root.foreground
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.displayLarge
                  font.bold: true
                }
                Text {
                  text: root.tempUnit
                  color: root.foreground
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.title
                  anchors.top: parent.top
                  anchors.topMargin: Style.space(4)
                }
              }

              Text {
                text: (root.current && root.current.description) ? root.current.description : "Current Conditions"
                color: root.foreground
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
                elide: Text.ElideRight
              }

              Text {
                text: (root.current && root.current.todayMaxF && root.current.todayMinF)
                  ? ("H: " + (root.useImperial ? root.current.todayMaxF : root.current.todayMaxC) + "° / L: " + (root.useImperial ? root.current.todayMinF : root.current.todayMinC) + "°")
                  : ""
                color: root.foreground
                opacity: 0.6
                font.family: root.fontFamily
                font.pixelSize: Style.font.caption
              }
            }

            Item {
              // Spacer
              width: parent.width - 70 - 160 - telemetryGrid.width - (parent.spacing * 3)
              height: 1
            }

            // Telemetry Grid: Feels Like, Humidity, Wind, Sunrise/Sunset
            Grid {
              id: telemetryGrid
              anchors.verticalCenter: parent.verticalCenter
              columns: 2
              columnSpacing: Style.space(20)
              rowSpacing: Style.space(6)

              // Feels Like
              Row {
                spacing: Style.space(6)
                Text { text: "\uf2c9"; color: Color.accent; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
                Text { text: "Feels: " + (root.reportFeels || "—"); color: root.foreground; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
              }

              // Wind
              Row {
                spacing: Style.space(6)
                Text { text: "\uf72e"; color: Color.accent; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
                Text { text: "Wind: " + (root.reportWind || "—"); color: root.foreground; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
              }

              // Humidity
              Row {
                spacing: Style.space(6)
                Text { text: "\uf043"; color: Color.accent; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
                Text { text: "Humidity: " + (root.reportHumidity || "—"); color: root.foreground; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
              }

              // Rain Chance
              Row {
                spacing: Style.space(6)
                Text { text: "\uf73d"; color: Color.accent; font.family: root.fontFamily; font.pixelSize: Style.font.bodySmall }
                Text {
                  text: "Rain: " + ((root.current && root.current.todayPrecipProbability !== null) ? (root.current.todayPrecipProbability + "%") : "—")
                  color: root.foreground
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.bodySmall
                }
              }
            }
          }
        }

        // 4. Section: 48-Hour Hourly Timeline
        HourlyForecast {
          entries: root.hourlyEntries
          foreground: root.foreground
          fontFamily: root.fontFamily
          useImperial: root.useImperial
          status: root.hourlyStatus
        }

        // Horizontal Separator
        Rectangle {
          width: parent.width
          height: 1
          color: Util.alpha(root.foreground, 0.12)
        }

        // 5. Section: 10-Day Daily Outlook
        DailyForecast {
          days: root.forecastDays
          foreground: root.foreground
          fontFamily: root.fontFamily
          useImperial: root.useImperial
        }

        // 6. Section: Centered Version Footer
        Item {
          width: parent.width
          height: Style.space(24)

          Text {
            anchors.centerIn: parent
            textFormat: Text.PlainText
            text: "fred.weather v" + root.pluginVersion
            color: root.foreground
            opacity: 0.45
            font.family: root.fontFamily
            font.pixelSize: Style.font.caption
          }
        }
      }
    }
  }

  Component.onCompleted: {
    ensureCacheDir.running = true
    Qt.callLater(function() {
      if (root.screenName) WeatherStore.register(root.screenName, root)
    })
  }

  Component.onDestruction: {
    if (root.screenName) WeatherStore.unregister(root.screenName, root)
  }
}
