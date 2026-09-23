import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons
import qs.Ui
import "Model.js" as Model
import "Network.js" as Network
import "TidesStore.js" as TidesStore

Panel {
  id: root
  moduleName: "fred.tides"
  ipcTarget: "fred.tides"
  manageIpc: false

  property var anchorItem: null
  property bool openedFromHotkey: false
  property string pluginVersion: "1.0.4"
  readonly property color foreground: Color.popups.text
  readonly property string fontFamily: root.bar ? root.bar.fontFamily : Style.font.family
  property string numberFontFamily: (root.settings && root.settings.numberFontFamily)
    ? root.settings.numberFontFamily
    : "Liberation Sans"

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
    if (screenName) TidesStore.register(screenName, root)
  }

  onOpenedChanged: {
    if (opened) {
      cacheFile.reload()
      weatherLocationFile.reload()
      tidesLocationFile.reload()
      weatherCacheFile.reload()
      Qt.callLater(function() {
        if (tideCurve) tideCurve.requestPaint()
      })
    }
  }

  function open() {
    openedFromHotkey = false
    setCenterHoverRevealSuppressed(false)
    root.controller.show()
    weatherLocationFile.reload()
    tidesLocationFile.reload()
    cacheFile.reload()
    root.refresh()
  }

  function openFromHotkey() {
    openedFromHotkey = true
    root.controller.show()
    weatherLocationFile.reload()
    tidesLocationFile.reload()
    cacheFile.reload()
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
    if (root.bar && typeof root.bar.setCenterHoverRevealSuppressed === "function") {
      root.bar.setCenterHoverRevealSuppressed(value)
    } else if (root.bar && "centerHoverRevealSuppressed" in root.bar) {
      try {
        root.bar.centerHoverRevealSuppressed = value
      } catch (e) {}
    }
  }

  IpcHandler {
    target: "fred.tides"

    function open(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.open("", cur, Hyprland.monitors)
    }
    function close(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.close("", cur, Hyprland.monitors)
    }
    function show(): void { open() }
    function hide(): void { close() }
    function toggle(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.toggle("", cur, Hyprland.monitors)
    }
    function openMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.open(monitor, cur, Hyprland.monitors)
    }
    function closeMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.close(monitor, cur, Hyprland.monitors)
    }
    function toggleMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.toggle(monitor, cur, Hyprland.monitors)
    }
    function refresh(): void { TidesStore.refreshAll(root) }
  }

  IpcHandler {
    target: "io.github.woogy7.tides"

    function open(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.open("", cur, Hyprland.monitors)
    }
    function close(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.close("", cur, Hyprland.monitors)
    }
    function toggle(): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.toggle("", cur, Hyprland.monitors)
    }
    function openMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.open(monitor, cur, Hyprland.monitors)
    }
    function closeMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.close(monitor, cur, Hyprland.monitors)
    }
    function toggleMonitor(monitor: string): void {
      var cur = Hyprland.focusedMonitor ? String(Hyprland.focusedMonitor.name || "") : ""
      TidesStore.toggle(monitor, cur, Hyprland.monitors)
    }
    function refresh(): void { TidesStore.refreshAll(root) }
  }

  // --- Reports & Time Tracking ---------------------------------------------
  property var marineReport: null
  property int marineRetries: 0
  property var now: new Date()

  Timer {
    interval: 30 * 1000
    running: true
    repeat: true
    onTriggered: root.now = new Date()
  }

  // --- Location Management -------------------------------------------------
  readonly property string tidesLocationPath: Quickshell.env("HOME") + "/.local/state/omarchy/settings/tides.json"
  readonly property string cacheFilePath: Quickshell.env("HOME") + "/.cache/fred.tides/cache.json"

  property var weatherLocationState: ({ name: "", latitude: null, longitude: null, unit: "m" })
  property var tidesLocationState: ({ name: "", latitude: null, longitude: null, unit: "m" })

  readonly property bool hasOwnLocation: tidesLocationState.latitude !== null && tidesLocationState.longitude !== null
  readonly property var configuredLocationState: hasOwnLocation ? tidesLocationState : weatherLocationState
  readonly property bool hasCoordinates: configuredLocationState.latitude !== null && configuredLocationState.longitude !== null
  readonly property string activeUnit: configuredLocationState.unit || "m"
  readonly property string locationKey: hasCoordinates ? configuredLocationState.latitude + "," + configuredLocationState.longitude : ""

  onLocationKeyChanged: {
    marineRetries = 0
    marineProc.running = false
    Qt.callLater(refresh)
  }

  property FileView weatherLocationFile: FileView {
    path: Quickshell.env("HOME") + "/.local/state/omarchy/settings/weather.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.weatherLocationState = Model.parseLocationFile(text())
    onLoadFailed: root.weatherLocationState = Model.parseLocationFile("")
  }

  property FileView tidesLocationFile: FileView {
    path: root.tidesLocationPath
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.tidesLocationState = Model.parseLocationFile(text())
    onLoadFailed: root.tidesLocationState = Model.parseLocationFile("")
  }

  property FileView cacheFile: FileView {
    path: root.cacheFilePath
    watchChanges: false
    printErrors: false
    onLoaded: {
      var cached = Model.parseCache(text())
      if (cached && cached.report) {
        root.marineReport = cached.report
      }
    }
  }

  property string weatherRegion: ""

  property FileView weatherCacheFile: FileView {
    path: Quickshell.env("HOME") + "/.cache/fred.weather/weather-cache.json"
    watchChanges: false
    printErrors: false
    onLoaded: {
      try {
        var parsed = JSON.parse(text())
        var area = parsed && parsed.report && parsed.report.data && parsed.report.data.nearest_area && parsed.report.data.nearest_area[0]
        if (area && area.region && area.region[0] && area.region[0].value) {
          root.weatherRegion = String(area.region[0].value).trim()
        }
      } catch (e) {}
    }
  }

  Timer {
    interval: 1500
    running: true
    onTriggered: {
      weatherLocationFile.reload()
      tidesLocationFile.reload()
      cacheFile.reload()
      weatherCacheFile.reload()
    }
  }

  // --- Location Search & Geocoding -----------------------------------------
  property bool editingLocation: false
  property bool savingLocation: false
  property var locationSuggestions: []
  property int suggestionIndex: 0
  property string geocodePendingQuery: ""
  property string geocodeActiveQuery: ""

  function startEditingLocation() {
    editingLocation = true
    savingLocation = false
    locationSuggestions = []
    suggestionIndex = 0
    Qt.callLater(function() {
      locationField.text = root.configuredLocationState.name
      locationField.selectAll()
      locationField.forceActiveFocus()
    })
  }

  function cancelEditingLocation() {
    editingLocation = false
    savingLocation = false
    locationSuggestions = []
    geocodeDebounce.stop()
    Qt.callLater(function() { if (panelKeyCatcher) panelKeyCatcher.forceActiveFocus() })
  }

  function commitLocation() {
    var text = locationField.text.trim()
    if (text === "") {
      clearLocation()
      return
    }
    var choices = locationSuggestions || []
    var index = Math.max(0, Math.min(suggestionIndex, choices.length - 1))
    if (choices[index]) pickSuggestion(choices[index])
  }

  function pickSuggestion(suggestion) {
    if (!suggestion) return
    savingLocation = true
    var reg = suggestion.admin1 || suggestion.country || ""
    persistLocation(suggestion.name, suggestion.latitude, suggestion.longitude, root.activeUnit, reg)
  }

  function clearLocation() {
    locationSaveProc.command = ["rm", "-f", root.tidesLocationPath]
    locationSaveProc.running = true
    cancelEditingLocation()
  }

  function toggleUnit() {
    var nextUnit = root.activeUnit === "m" ? "ft" : "m"
    persistLocation(root.configuredLocationState.name, root.configuredLocationState.latitude, root.configuredLocationState.longitude, nextUnit, root.activeRegion)
  }

  function persistLocation(name, latitude, longitude, unit, region) {
    locationSaveProc.command = ["bash", "-c",
      "mkdir -p \"$(dirname \"$1\")\" && printf '%s' \"$2\" > \"$1\"", "_",
      root.tidesLocationPath, Model.locationFileContents(name, latitude, longitude, unit, region)]
    locationSaveProc.running = true
  }

  Process {
    id: locationSaveProc
    environment: Network.closedEnv
    onExited: function(exitCode) {
      tidesLocationFile.reload()
      if (root.savingLocation) root.cancelEditingLocation()
    }
  }

  function requestGeocode() {
    var query = locationField.text.trim()
    if (query.length < 2) {
      locationSuggestions = []
      return
    }
    geocodePendingQuery = query
    if (!geocodeProc.running) startGeocode()
  }

  function startGeocode() {
    geocodeActiveQuery = geocodePendingQuery
    var url = "https://geocoding-api.open-meteo.com/v1/search?name=" + encodeURIComponent(geocodeActiveQuery) + "&count=5&language=en&format=json"
    geocodeProc.command = Network.curlCommand(url, 5, Network.responseLimits.geocode)
    geocodeProc.running = true
  }

  Process {
    id: geocodeProc
    environment: Network.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var validated = Network.responseText(text, 0, 0, Network.responseLimits.geocode)
          root.locationSuggestions = root.editingLocation ? Model.parseGeocodingResults(validated) : []
        } catch (e) {
          root.locationSuggestions = []
        }
        root.suggestionIndex = 0
        if (root.geocodePendingQuery !== root.geocodeActiveQuery) Qt.callLater(root.startGeocode)
      }
    }
  }

  Timer {
    id: geocodeDebounce
    interval: 300
    onTriggered: root.requestGeocode()
  }

  // --- Derived Tide Calculations -------------------------------------------
  readonly property var events: Model.tideEvents(marineReport)
  readonly property var upcoming: Model.upcomingEvents(events, now, 4)
  readonly property var nextEvent: upcoming.length > 0 ? upcoming[0] : null
  readonly property var dayTides: Model.dayTides(events, now)
  readonly property var currentHeight: Model.heightAt(marineReport, now)
  readonly property string currentHeightFormatted: Model.formatHeight(currentHeight, activeUnit)
  readonly property string currentHeightValueFormatted: Model.formatHeightValue(currentHeight, activeUnit)
  readonly property string currentTrend: nextEvent ? (nextEvent.high ? "Rising" : "Falling") : ""
  readonly property string todayRangeFormatted: Model.todayRange(events, now, activeUnit)

  readonly property string waveIcon: "\udb81\udf8d" // nf-md-waves
  readonly property string label: nextEvent ? waveIcon : ""

  readonly property string activeRegion: hasOwnLocation ? (tidesLocationState.region || "") : weatherRegion
  readonly property string displayLocation: Model.formatLocationDisplay(configuredLocationState.name, activeRegion)
  readonly property string hoverTitle: Model.formatTidesTitle(displayLocation)
  readonly property var fourTides: Model.fourTides(events, now)

  readonly property var hoverLines: {
    var lines = [root.hoverTitle]
    if (currentHeight !== null && currentTrend !== "") {
      lines.push("Sea Level " + currentHeightFormatted + " (" + currentTrend + ")")
    }
    var nextCount = Math.min(2, upcoming.length)
    for (var i = 0; i < nextCount; i++) {
      var ev = upcoming[i]
      var nextType = ev.high ? "Next High Tide" : "Next Low Tide"
      var nextH = Model.formatHeight(ev.height, activeUnit)
      var nextTime = Model.formatTime(ev.time)
      lines.push(nextType + " " + nextH + " at " + nextTime)
    }
    return lines
  }

  readonly property string statusSummary: {
    var parts = [root.hoverTitle]
    if (currentHeightFormatted) parts.push("Sea Level " + currentHeightFormatted + " (" + currentTrend + ")")
    var nextCount = Math.min(2, upcoming.length)
    for (var i = 0; i < nextCount; i++) {
      var ev = upcoming[i]
      var nType = ev.high ? "Next High Tide" : "Next Low Tide"
      var nH = Model.formatHeight(ev.height, activeUnit)
      var nT = Model.formatTime(ev.time)
      parts.push(nType + " " + nH + " at " + nT)
    }
    return parts.join("\n")
  }

  // --- Scrubbing State -----------------------------------------------------
  property var scrubTime: null
  readonly property var cursorTime: scrubTime || now
  readonly property bool scrubbing: scrubTime !== null

  function refresh() {
    if (!hasCoordinates) return
    marineRetries = 0
    startFetch()
  }

  function startFetch() {
    if (marineProc.running || !hasCoordinates) return
    var provider = Model.Providers["open-meteo"]
    var url = provider.buildQueryUrl(configuredLocationState.latitude, configuredLocationState.longitude)
    marineProc.command = Network.curlCommand(url, 10, Network.responseLimits.tides)
    marineProc.running = true
  }

  function scheduleRetry() {
    if (marineRetries >= 3) return
    marineRetries++
    retryTimer.restart()
  }

  Timer {
    id: retryTimer
    interval: 2500
    onTriggered: root.startFetch()
  }

  function saveCache(report) {
    if (!report) return
    var json = Model.serializeCache(report, configuredLocationState, new Date())
    cacheSaveProc.command = ["bash", "-c",
      "mkdir -p \"$(dirname \"$1\")\" && printf '%s' \"$2\" > \"$1\"", "_",
      root.cacheFilePath, json]
    cacheSaveProc.running = true
  }

  Process {
    id: cacheSaveProc
    environment: Network.closedEnv
  }

  Process {
    id: marineProc
    environment: Network.closedEnv
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var validated = Network.responseText(text, 0, 0, Network.responseLimits.tides)
          var parsed = Model.Providers["open-meteo"].parseResponse(validated)
          root.marineReport = parsed
          root.marineRetries = 0
          root.saveCache(parsed)
          TidesStore.broadcastReport(root.screenName, parsed, new Date().toISOString())
        } catch (e) {
          root.scheduleRetry()
        }
      }
    }
  }

  function applyReport(report, updatedAt) {
    if (report && report.hourly) {
      root.marineReport = report
      root.marineRetries = 0
    }
  }

  // Refetch every 3 hours
  Timer {
    interval: 3 * 60 * 60 * 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  // --- Multi-Monitor Focus-Isolated Window ----------------------------------
  TidesPanelWindow {
    id: panel
    anchorItem: root.anchorItem
    bar: root.bar
    owner: root
    open: root.opened
    contentWidth: panel.fittedContentWidth(Style.space(680))
    contentHeight: panel.fittedContentHeight(Math.max(Style.space(260), tidesColumn.implicitHeight), Style.space(480))
    focusTarget: panelKeyCatcher

    PanelKeyCatcher {
      id: panelKeyCatcher
      anchors.fill: parent
      blocked: root.editingLocation
      onCloseRequested: {
        if (root.editingLocation) root.cancelEditingLocation()
        else root.close()
      }
      onReturnRequested: {
        if (!root.editingLocation) root.startEditingLocation()
        else root.commitLocation()
      }
      onTabRequested: function(direction) {
        root.switchPanel(direction)
      }

      Flickable {
        id: tidesScroll
        anchors.fill: parent
        contentWidth: width
        contentHeight: tidesColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height

        Column {
          id: tidesColumn
          width: tidesScroll.width
          spacing: Style.space(12)

          // ---- Header Row ----------------------------------------------------
          Item {
            id: headerRowItem
            width: parent.width
            height: Math.max(Style.space(36), Math.max(heroLeft.implicitHeight, heroRight.implicitHeight))

            Row {
              id: heroLeft
              anchors.left: parent.left
              anchors.leftMargin: Style.space(16)
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(8)

              Text {
                id: waveIconText
                anchors.verticalCenter: parent.verticalCenter
                text: root.waveIcon
                color: root.bar ? root.bar.foreground : Color.popups.text
                font.family: root.fontFamily
                font.pixelSize: Style.space(28)
              }

              // Hidden measure text for accurate, unclipped width calculation
              Text {
                id: locationMeasureText
                visible: false
                text: root.displayLocation || (root.hasCoordinates ? "Coastal Tides" : "Set Location...")
                font.family: root.fontFamily
                font.pixelSize: Style.font.body
                font.bold: true
              }

              // Location Box (Click to edit, styled the same way fred.weather does)
              Rectangle {
                id: locationBox
                anchors.verticalCenter: parent.verticalCenter
                visible: !root.editingLocation
                height: Style.space(30)
                clip: true

                readonly property real maxAvailableWidth: headerRowItem.width
                  - (heroRight.visible ? heroRight.width + Style.space(16) : 0)
                  - Style.space(32)
                  - waveIconText.implicitWidth
                  - heroLeft.spacing * 2

                readonly property real naturalWidth: pinIcon.implicitWidth + locationMeasureText.implicitWidth + locationTextRow.spacing + Style.space(16)
                width: Math.min(maxAvailableWidth, naturalWidth)
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
                  anchors.left: parent.left
                  anchors.leftMargin: Style.space(8)
                  anchors.verticalCenter: parent.verticalCenter
                  spacing: Style.space(6)

                  Text {
                    id: pinIcon
                    text: "\uf041" // map pin icon
                    color: Color.accent
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.bodySmall
                    anchors.verticalCenter: parent.verticalCenter
                  }

                  Text {
                    id: locationText
                    width: Math.min(locationMeasureText.implicitWidth, Math.max(0, locationBox.width - pinIcon.implicitWidth - locationTextRow.spacing - Style.space(16)))
                    text: root.displayLocation || (root.hasCoordinates ? "Coastal Tides" : "Set Location...")
                    color: root.foreground
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.body
                    font.bold: true
                    elide: Text.ElideRight
                    anchors.verticalCenter: parent.verticalCenter
                  }
                }
              }

            // Search textfield
            Row {
              visible: root.editingLocation
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(6)

              TextField {
                id: locationField
                width: Style.space(260)
                enabled: !root.savingLocation
                placeholderText: "Search beach or harbor"
                foreground: root.bar ? root.bar.foreground : Color.popups.text
                font.family: root.fontFamily

                onTextChanged: if (root.editingLocation && !root.savingLocation) geocodeDebounce.restart()

                Keys.onPressed: function(event) {
                  if (event.key === Qt.Key_Escape) {
                    root.cancelEditingLocation()
                    event.accepted = true
                  } else if (event.key === Qt.Key_Down) {
                    if (root.suggestionIndex < root.locationSuggestions.length - 1) root.suggestionIndex++
                    event.accepted = true
                  } else if (event.key === Qt.Key_Up) {
                    if (root.suggestionIndex > 0) root.suggestionIndex--
                    event.accepted = true
                  } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    root.commitLocation()
                    event.accepted = true
                  }
                }
              }

              Rectangle {
                width: Style.space(18)
                height: Style.space(18)
                anchors.verticalCenter: parent.verticalCenter
                radius: Math.min(4, Style.cornerRadius)
                color: !root.savingLocation && clearLocationArea.containsMouse ? Style.hoverFillFor(root.bar ? root.bar.foreground : Color.popups.text, Color.accent) : "transparent"

                Text {
                  anchors.centerIn: parent
                  text: root.savingLocation ? "\udb82\udf96" : "✕"
                  font.family: root.fontFamily
                  color: Qt.darker(root.bar ? root.bar.foreground : Color.popups.text, 1.4)
                  font.pixelSize: Style.font.bodySmall

                  RotationAnimator on rotation {
                    running: root.savingLocation
                    from: 0; to: 360
                    duration: 800
                    loops: Animation.Infinite
                  }
                }

                MouseArea {
                  id: clearLocationArea
                  anchors.fill: parent
                  enabled: !root.savingLocation
                  hoverEnabled: true
                  cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                  onClicked: root.clearLocation()
                }
              }
            }
          }

          Column {
            id: heroRight
            width: tideStats.implicitWidth
            anchors.right: parent.right
            anchors.rightMargin: Style.space(16)
            anchors.verticalCenter: parent.verticalCenter
            spacing: Style.space(12)

            Row {
              id: tideStats
              visible: !!root.nextEvent
              spacing: Style.space(20)

              Column {
                spacing: Style.space(3)
                Text {
                  text: "TIDE"
                  color: Qt.darker(root.bar ? root.bar.foreground : Color.popups.text, 1.5)
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.caption
                  font.letterSpacing: 1
                }
                Text {
                  text: root.currentTrend
                  color: root.bar ? root.bar.foreground : Color.popups.text
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.title
                }
              }

              Column {
                spacing: Style.space(3)
                Text {
                  text: "NOW"
                  color: Qt.darker(root.bar ? root.bar.foreground : Color.popups.text, 1.5)
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.caption
                  font.letterSpacing: 1
                }
                Row {
                  spacing: Style.space(6)

                  Text {
                    id: nowValueText
                    text: root.currentHeightValueFormatted
                    color: root.bar ? root.bar.foreground : Color.popups.text
                    font.family: root.numberFontFamily
                    font.pixelSize: Style.font.title
                    anchors.verticalCenter: parent.verticalCenter
                  }

                  Rectangle {
                    id: unitBox
                    anchors.verticalCenter: parent.verticalCenter
                    implicitWidth: unitBoxText.implicitWidth + Style.space(12)
                    implicitHeight: Style.space(22)
                    radius: Math.min(4, Style.cornerRadius)
                    color: unitBoxHover.hovered ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"
                    border.width: 1
                    border.color: Util.alpha(root.foreground, 0.2)

                    Text {
                      id: unitBoxText
                      anchors.centerIn: parent
                      text: root.activeUnit === "ft" ? "feet" : "meters"
                      font.family: root.fontFamily
                      font.pixelSize: Style.font.caption
                      font.bold: true
                      color: root.foreground
                      opacity: 0.9
                    }

                    TapHandler {
                      onTapped: root.toggleUnit()
                    }

                    HoverHandler {
                      id: unitBoxHover
                      cursorShape: Qt.PointingHandCursor
                    }
                  }
                }
              }
            }
          }
        }

        // ---- Geocoding Suggestions -----------------------------------------
        Column {
          visible: root.editingLocation && !root.savingLocation && root.locationSuggestions.length > 0
          width: parent.width
          spacing: 0

          Repeater {
            model: root.locationSuggestions

            Rectangle {
              required property var modelData
              required property int index
              width: parent.width
              height: suggestionRow.implicitHeight + Style.space(10)
              radius: Style.cornerRadius
              color: index === root.suggestionIndex ? Style.hoverFillFor(root.bar ? root.bar.foreground : Color.popups.text, Color.accent) : "transparent"

              Row {
                id: suggestionRow
                anchors.left: parent.left
                anchors.leftMargin: Style.space(16)
                anchors.verticalCenter: parent.verticalCenter
                spacing: Style.space(8)

                Text {
                  text: modelData.name
                  color: index === root.suggestionIndex ? Style.hoverStateColor(root.bar ? root.bar.foreground : Color.popups.text, Color.accent) : (root.bar ? root.bar.foreground : Color.popups.text)
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.body
                }
                Text {
                  visible: text !== ""
                  text: modelData.description
                  color: Qt.darker(root.bar ? root.bar.foreground : Color.popups.text, 1.5)
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.bodySmall
                  anchors.verticalCenter: parent.verticalCenter
                }
              }

              MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onPositionChanged: root.suggestionIndex = index
                onClicked: root.pickSuggestion(modelData)
              }
            }
          }
        }

        Text {
          visible: !root.nextEvent
          anchors.horizontalCenter: parent.horizontalCenter
          text: root.hasCoordinates ? "Fetching tide forecast…" : "Click the location to set one"
          color: Qt.darker(root.bar ? root.bar.foreground : Color.popups.text, 1.5)
          font.family: root.fontFamily
          font.pixelSize: Style.font.bodySmall
          font.italic: true
        }

        // ---- Interactive 24-Hour Scrubbable Curve --------------------------
        Item {
          visible: !!root.marineReport && !!root.nextEvent
          width: parent.width
          height: Style.space(136)

          Canvas {
            id: tideCurve
            anchors.left: parent.left
            anchors.leftMargin: Style.space(16)
            anchors.right: rangeBarContainer.left
            anchors.rightMargin: Style.space(10)
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            readonly property color fg: root.bar ? root.bar.foreground : Color.popups.text
            onFgChanged: requestPaint()

            readonly property real windowStartMs: root.now.getTime() - 6 * 3600 * 1000
            readonly property real windowMs: 24 * 3600 * 1000

            function timeAtX(px) {
              var frac = Math.max(0, Math.min(1, px / width))
              var tm = windowStartMs + frac * windowMs

              var snapMs = 15 * 60 * 1000
              var best = null
              var targets = [root.now.getTime()]
              for (var i = 0; i < root.events.length; i++) targets.push(root.events[i].time.getTime())
              for (i = 0; i < targets.length; i++) {
                var d = Math.abs(targets[i] - tm)
                if (d <= snapMs && (best === null || d < Math.abs(best - tm))) best = targets[i]
              }
              return new Date(best !== null ? best : tm)
            }

            Connections {
              target: root
              function onMarineReportChanged() { tideCurve.requestPaint() }
              function onNowChanged() { tideCurve.requestPaint() }
              function onScrubTimeChanged() { tideCurve.requestPaint() }
              function onActiveUnitChanged() { tideCurve.requestPaint() }
            }

            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: Qt.SizeHorCursor
              onPositionChanged: function(mouse) { root.scrubTime = tideCurve.timeAtX(mouse.x) }
              onPressed: function(mouse) { root.scrubTime = tideCurve.timeAtX(mouse.x) }
              onExited: root.scrubTime = null
            }

            onPaint: {
              var ctx = getContext("2d")
              ctx.reset()
              if (!root.marineReport) return

              var w = width
              var h = height
              if (w <= 0 || h <= 0) return
              var captionPx = Style.font.caption
              var padTop = captionPx + 8
              var padBottom = captionPx * 2 + 22
              var startMs = windowStartMs
              var endMs = startMs + windowMs

              // Sample the curve every 10 minutes
              var pts = []
              var minH = Infinity
              var maxH = -Infinity
              for (var t = startMs; t <= endMs; t += 10 * 60 * 1000) {
                var v = Model.smoothHeightAt(root.marineReport, t)
                if (v === null) continue
                pts.push({ t: t, v: v })
                if (v < minH) minH = v
                if (v > maxH) maxH = v
              }
              if (pts.length < 2) return
              var span = Math.max(0.5, maxH - minH)
              minH -= span * 0.08
              maxH += span * 0.08
              span = maxH - minH

              function xFor(timeMs) {
                return ((timeMs - startMs) / windowMs) * w
              }
              function yFor(val) {
                return padTop + (1 - (val - minH) / span) * (h - padTop - padBottom)
              }

              // Subtle background area fill
              ctx.beginPath()
              ctx.moveTo(xFor(pts[0].t), h - padBottom)
              for (var i = 0; i < pts.length; i++) ctx.lineTo(xFor(pts[i].t), yFor(pts[i].v))
              ctx.lineTo(xFor(pts[pts.length - 1].t), h - padBottom)
              ctx.closePath()

              var grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom)
              var baseColor = Qt.color(Color.accent || fg)
              grad.addColorStop(0, Qt.rgba(baseColor.r, baseColor.g, baseColor.b, 0.25))
              grad.addColorStop(1, Qt.rgba(baseColor.r, baseColor.g, baseColor.b, 0.02))
              ctx.fillStyle = grad
              ctx.fill()

              // Draw tide curve stroke
              ctx.beginPath()
              for (i = 0; i < pts.length; i++) {
                var px = xFor(pts[i].t)
                var py = yFor(pts[i].v)
                if (i === 0) ctx.moveTo(px, py)
                else ctx.lineTo(px, py)
              }
              ctx.strokeStyle = baseColor
              ctx.lineWidth = 2.0
              ctx.stroke()

              // Grid lines every 6 hours
              var hourStep = 6 * 3600 * 1000
              var firstGrid = Math.ceil(startMs / hourStep) * hourStep
              ctx.strokeStyle = Qt.rgba(fg.r, fg.g, fg.b, 0.12)
              ctx.lineWidth = 1.0
              ctx.fillStyle = Qt.rgba(fg.r, fg.g, fg.b, 0.5)
              ctx.font = captionPx + "px " + root.numberFontFamily
              ctx.textAlign = "center"

              for (var gt = firstGrid; gt <= endMs; gt += hourStep) {
                var gx = xFor(gt)
                ctx.beginPath()
                ctx.moveTo(gx, padTop)
                ctx.lineTo(gx, h - padBottom)
                ctx.stroke()

                var gd = new Date(gt)
                ctx.fillText(Model.formatTime(gd), gx, h - padBottom + captionPx + 4)
              }

              // Cursor indicator
              var cursorMs = root.cursorTime.getTime()
              if (cursorMs >= startMs && cursorMs <= endMs) {
                var cx = xFor(cursorMs)
                var cv = Model.smoothHeightAt(root.marineReport, cursorMs)
                if (cv !== null) {
                  var cy = yFor(cv)

                  // Vertical dashed marker
                  ctx.strokeStyle = root.scrubbing ? baseColor : Qt.rgba(fg.r, fg.g, fg.b, 0.8)
                  ctx.lineWidth = 1.5
                  ctx.beginPath()
                  ctx.moveTo(cx, padTop)
                  ctx.lineTo(cx, h - padBottom)
                  ctx.stroke()

                  // Dot on curve
                  ctx.beginPath()
                  ctx.arc(cx, cy, 4.5, 0, Math.PI * 2)
                  ctx.fillStyle = baseColor
                  ctx.fill()
                  ctx.lineWidth = 2.0
                  ctx.strokeStyle = Color.popups.background
                  ctx.stroke()

                  // Cursor readout text
                  var label = Model.formatTime(root.cursorTime) + "  " + Model.formatHeight(cv, root.activeUnit)
                  if (!root.scrubbing) label = "NOW  " + label
                  ctx.fillStyle = root.scrubbing ? baseColor : fg
                  ctx.font = "bold " + captionPx + "px " + root.numberFontFamily
                  ctx.textAlign = cx > w * 0.75 ? "right" : (cx < w * 0.25 ? "left" : "center")
                  ctx.fillText(label, cx, padTop - 2)
                }
              }
            }
          }

          // ---- Range Bar (Highest High to Lowest Low) -----------------------
          Item {
            id: rangeBarContainer
            anchors.right: parent.right
            anchors.rightMargin: Style.space(16)
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Style.space(46)

            readonly property var extrema: Model.chartExtrema(root.events, root.marineReport, tideCurve.windowStartMs, tideCurve.windowStartMs + tideCurve.windowMs)
            readonly property string highLabel: Model.formatHeight(extrema.high, root.activeUnit)
            readonly property string lowLabel: Model.formatHeight(extrema.low, root.activeUnit)

            readonly property real currentFrac: {
              if (root.currentHeight === null || extrema.high <= extrema.low) return 0.5
              var val = root.scrubbing && root.scrubTime ? (Model.smoothHeightAt(root.marineReport, root.cursorTime.getTime()) || root.currentHeight) : root.currentHeight
              var frac = (val - extrema.low) / (extrema.high - extrema.low)
              return Math.max(0, Math.min(1, frac))
            }

            Column {
              anchors.centerIn: parent
              spacing: Style.space(4)
              width: parent.width

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: rangeBarContainer.highLabel
                color: Color.accent || root.foreground
                font.family: root.numberFontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }

              Item {
                anchors.horizontalCenter: parent.horizontalCenter
                width: Style.space(16)
                height: Style.space(60)

                // Background Track
                Rectangle {
                  anchors.centerIn: parent
                  width: Style.space(5)
                  height: parent.height
                  radius: width / 2
                  color: Util.alpha(root.foreground, 0.15)
                }

                // Range fill gradient
                Rectangle {
                  anchors.centerIn: parent
                  width: Style.space(5)
                  height: parent.height
                  radius: width / 2
                  gradient: Gradient {
                    GradientStop { position: 0.0; color: Color.accent || root.foreground }
                    GradientStop { position: 1.0; color: Qt.darker(Color.accent || root.foreground, 1.8) }
                  }
                }

                // Current / scrubbed water level indicator dot
                Rectangle {
                  anchors.horizontalCenter: parent.horizontalCenter
                  y: (1 - rangeBarContainer.currentFrac) * (parent.height - height)
                  width: Style.space(9)
                  height: Style.space(9)
                  radius: width / 2
                  color: root.foreground
                  border.color: Color.popups.background
                  border.width: 1.5
                }
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: rangeBarContainer.lowLabel
                color: Qt.darker(root.foreground, 1.3)
                font.family: root.numberFontFamily
                font.pixelSize: Style.font.caption
                font.bold: true
              }
            }
          }
        }

        // ---- Chronological Daily Tides Cards (4 Cards) --------------------
        Row {
          id: cardsRow
          visible: !!root.nextEvent && root.fourTides.length > 0
          width: parent.width
          spacing: Style.space(8)

          Item {
            width: Style.space(16)
            height: 1
          }

          Repeater {
            model: root.fourTides

            Rectangle {
              id: tideCard
              required property var modelData
              required property int index
              readonly property int cardCount: Math.max(1, root.fourTides.length)
              width: (parent.width - Style.space(32) - Style.space(8) * (cardCount - 1)) / cardCount
              height: Style.space(52)
              radius: Style.cornerRadius
              color: modelData.time.getTime() > root.now.getTime()
                ? Style.hoverFillFor(root.foreground, Color.accent)
                : "transparent"
              border.color: Qt.darker(root.foreground, 1.8)
              border.width: 1
              opacity: modelData.time.getTime() > root.now.getTime() ? 1.0 : 0.45

              Column {
                anchors.centerIn: parent
                spacing: Style.space(2)

                Row {
                  anchors.horizontalCenter: parent.horizontalCenter
                  spacing: Style.space(4)

                  Text {
                    text: modelData.high ? "HIGH" : "LOW"
                    color: modelData.high ? (Color.accent || root.foreground) : Qt.darker(root.foreground, 1.3)
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.caption
                    font.bold: true
                  }

                  Text {
                    text: Model.formatTime(modelData.time)
                    color: root.foreground
                    font.family: root.numberFontFamily
                    font.pixelSize: Style.font.caption
                  }
                }

                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  text: Model.formatHeight(modelData.height, root.activeUnit)
                  color: root.foreground
                  font.family: root.numberFontFamily
                  font.pixelSize: Style.font.bodySmall
                  font.bold: true
                }
              }
            }
          }
        }

        // ---- Version & Attribution Footer ----------------------------------
        Item {
          width: parent.width
          height: Style.space(18)

          Text {
            anchors.centerIn: parent
            text: "fred.tides v" + root.pluginVersion + " • Open-Meteo Marine"
            font.family: root.fontFamily
            font.pixelSize: Style.font.caption
            color: root.bar ? root.bar.foreground : Color.popups.text
            opacity: 0.4
          }
        }
      }
    }
  }
}
}
