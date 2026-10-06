import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import "host"
import "bar/BarModel.js" as BarModel

ShellRoot {
  id: proof

  property string clockEntry: Quickshell.env("TAMLINUX_CLOCK_ENTRY") || ""
  property string fixtureEntry: Quickshell.env("TAMLINUX_PANEL_ENTRY") || ""
  property string compositorEntry: Quickshell.env("TAMLINUX_COMPOSITOR_ENTRY") || ""
  property string uiEntry: Quickshell.env("TAMLINUX_UI_ENTRY") || ""
  property var extraEntries: []
  property alias compositor: compositorFacade
  property string pluginIds: Quickshell.env("TAMLINUX_PLUGIN_IDS") || "fred.clock"
  property bool outputDropped: false
  // TAMLINUX_BAR=0 runs only the services, beside another shell's bar.
  readonly property bool barEnabled: Quickshell.env("TAMLINUX_BAR") !== "0"
  // The bar's edge, from the layout document's "position": "top" (the
  // default) or "bottom". Services-only mode sits beside Omarchy's top bar.
  readonly property string barPosition: barEnabled && barLayout ? barPositionSetting : "top"
  property string barPositionSetting: "top"
  property bool barTransparent: false
  // Hidden is the flag file ~/.local/state/tamlinux/toggles/bar-off, as
  // Omarchy keeps its own, so it survives a restart. The shell writes it
  // (toggleBar); a flag set from outside is read at the next start.
  property bool barHidden: false
  property bool barFlagReady: false
  property bool barFlagWritten: false
  readonly property string barFlagPath: (Quickshell.env("HOME") || "") + "/.local/state/tamlinux/toggles/bar-off"
  // The layout document as read, kept to write position and transparency
  // back without dropping keys this shell does not know.
  property var barLayoutDoc: null
  property string outputName: Quickshell.env("TAMLINUX_OUTPUT") || ""
  property string droppedHosts: ""
  property var settingsDoc: ({ "version": 1, "entries": {} })
  property bool settingsReady: false
  property var hosts: []
  // TAMLINUX_BAR_LAYOUT names a layout file; with it the bar draws that
  // layout (host/BarLayout.qml) instead of the proof's row of entries.
  // TAMLINUX_PLUGIN_ENTRIES is a JSON object, plugin id to entry file.
  readonly property string barLayoutPath: Quickshell.env("TAMLINUX_BAR_LAYOUT") || ""
  property var barLayout: null
  property bool barLayoutReady: barLayoutPath === ""
  property var pluginEntries: ({})
  // The shell's own bar widgets, whose settings it also stores.
  readonly property var builtinWidgetIds: [
    "tamlinux.menu", "tamlinux.indicators", "tamlinux.keyboard-layout", "tamlinux.tray",
    "tamlinux.audio", "tamlinux.bluetooth", "tamlinux.network", "tamlinux.power"
  ]
  property var liveWidgets: []

  readonly property int hostCopies: {
    var n = Number(Quickshell.env("TAMLINUX_HOST_COPIES") || "1")
    if (!isFinite(n) || n < 1) return 1
    if (n > 4) return 4
    return Math.round(n)
  }

  readonly property string settingsPath: (Quickshell.env("HOME") || "") + "/.config/tamlinux-shell/settings.json"

  function evidence(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function allowedId(id) {
    if (builtinWidgetIds.indexOf(id) !== -1) return true
    if (typeof id === "string" && pluginEntries[id] !== undefined) return true
    var parts = pluginIds.split(",")
    for (var i = 0; i < parts.length; i++) {
      if (parts[i] === id) return true
    }
    return false
  }

  function entrySettings(id) {
    var entries = settingsDoc && settingsDoc.entries ? settingsDoc.entries : {}
    var entry = entries[id]
    return entry ? entry : { "id": id }
  }

  function ingestSettings(raw) {
    try {
      var parsed = JSON.parse(raw || "")
      if (!parsed || parsed.version !== 1 || !parsed.entries) throw new Error("shape")
      settingsDoc = parsed
    } catch (e) {
      evidence("settings-unreadable")
      settingsDoc = { "version": 1, "entries": { "fred.clock": { "id": "fred.clock" } } }
    }
  }

  // { centerAnchor, layout: { left, center, right } }, Omarchy's bar shape;
  // anything else draws an empty bar and says so.
  function ingestBarLayout(raw) {
    var parsed = null
    try {
      parsed = JSON.parse(raw || "")
    } catch (e) {
      parsed = null
    }
    var layout = parsed && parsed.layout && typeof parsed.layout === "object" ? parsed.layout : null
    if (!layout) evidence("bar-layout-unreadable")
    var sections = ["left", "center", "right"]
    var clean = {}
    for (var i = 0; i < sections.length; i++) {
      var list = layout && Array.isArray(layout[sections[i]]) ? layout[sections[i]] : []
      clean[sections[i]] = list.slice(0, 32)
    }
    var anchor = parsed && typeof parsed.centerAnchor === "string" ? parsed.centerAnchor : ""
    var position = readPosition(parsed ? parsed.position : undefined)
    barLayoutDoc = layout ? parsed : null
    barPositionSetting = position
    barTransparent = !!parsed && parsed.transparent === true
    barLayout = { "centerAnchor": anchor, "layout": clean }
    evidence("bar-layout left=" + clean.left.length + " center=" + clean.center.length + " right=" + clean.right.length
      + " position=" + position + " transparent=" + barTransparent)
  }

  // No vertical bar (D89): left, right, and anything else read as top.
  function readPosition(value) {
    if (value === undefined || value === null || value === "top") return "top"
    if (value === "bottom") return "bottom"
    evidence("bar-position-unsupported " + JSON.stringify(value).slice(0, 40))
    return "top"
  }

  // Position and transparency live in the layout document beside the
  // layout. An unreadable document is never overwritten.
  function saveBarLayout() {
    if (!barLayoutDoc || barLayoutPath === "") {
      evidence("bar-layout-not-saved")
      return false
    }
    var doc = {}
    for (var key in barLayoutDoc) doc[key] = barLayoutDoc[key]
    doc.position = barPositionSetting
    doc.transparent = barTransparent
    barLayoutDoc = doc
    barLayoutFile.setText(JSON.stringify(doc, null, 2) + "\n")
    evidence("bar-layout-saved position=" + barPositionSetting + " transparent=" + barTransparent)
    return true
  }

  function setBarPosition(value) {
    var next = String(value || "")
    if (next !== "top" && next !== "bottom") {
      evidence("bar-position-unsupported " + JSON.stringify(next.slice(0, 40)))
      return "unknown"
    }
    barPositionSetting = next
    saveBarLayout()
    return next
  }

  function toggleBarTransparency() {
    barTransparent = !barTransparent
    saveBarLayout()
    return barTransparent ? "transparent" : "opaque"
  }

  // on shows the bar, off hides it, toggle flips it.
  function toggleBar(mode) {
    var wanted = String(mode || "toggle")
    if (wanted !== "on" && wanted !== "off" && wanted !== "toggle") {
      evidence("bar-toggle-unsupported " + JSON.stringify(wanted.slice(0, 16)))
      return "unknown"
    }
    barHidden = wanted === "toggle" ? !barHidden : wanted === "off"
    writeBarFlag()
    evidence("bar-hidden " + barHidden)
    return barHidden ? "hidden" : "shown"
  }

  function writeBarFlag() {
    if (barFlagProc.running) return
    barFlagWritten = barHidden
    barFlagProc.command = barHidden
      ? ["/usr/bin/install", "-D", "-m", "600", "/dev/null", barFlagPath]
      : ["/usr/bin/rm", "-f", barFlagPath]
    barFlagProc.running = true
  }

  // Every screen's indicators, not the one copy the per-widget target
  // reaches (G8). Returns how many copies refreshed.
  function refreshIndicators() {
    var items = moduleWidgets("tamlinux.indicators")
    for (var i = 0; i < items.length; i++) {
      if (typeof items[i].refresh === "function") items[i].refresh()
    }
    evidence("indicators-refreshed " + items.length)
    return items.length
  }

  function ingestPluginEntries(raw) {
    var parsed = {}
    try {
      parsed = JSON.parse(raw || "{}")
    } catch (e) {
      evidence("plugin-entries-unreadable")
      parsed = {}
    }
    var clean = {}
    for (var id in parsed) {
      if (typeof parsed[id] === "string" && parsed[id].indexOf("/") === 0) clean[id] = parsed[id]
    }
    pluginEntries = clean
  }

  function updateEntryInline(moduleName, settings) {
    if (!allowedId(moduleName)) {
      evidence("settings-rejected " + moduleName)
      return false
    }
    var entry = { "id": moduleName }
    for (var key in settings) {
      if (key === "id") continue
      var value = settings[key]
      var kind = typeof value
      if (kind !== "string" && kind !== "number" && kind !== "boolean") {
        evidence("settings-rejected-type " + key)
        return false
      }
      if (kind === "number" && !isFinite(value)) {
        evidence("settings-rejected-type " + key)
        return false
      }
      if (kind === "string" && value.length > 512) {
        evidence("settings-rejected-length " + key)
        return false
      }
      entry[key] = value
    }
    var doc = { "version": 1, "entries": {} }
    var existing = settingsDoc && settingsDoc.entries ? settingsDoc.entries : {}
    for (var name in existing) doc.entries[name] = existing[name]
    doc.entries[moduleName] = entry
    settingsDoc = doc
    settingsFile.setText(JSON.stringify(doc, null, 2) + "\n")
    if (moduleName === "fred.clock")
      evidence("settings-wrote " + String(entry.format || ""))
    else
      evidence("settings-wrote " + moduleName + " marker=" + String(entry.marker || ""))
    return true
  }

  // The session services a bar widget may ask for by name. Null when that
  // service is not in TAMLINUX_SERVICES (the proof runs none).
  function firstPartyServiceFor(id) {
    if (id === "tamlinux.notifications") return sessionServices.notifications
    if (id === "tamlinux.nightlight") return sessionServices.nightlight
    if (id === "tamlinux.idle") return sessionServices.idle
    if (id === "tamlinux.media") return sessionServices.media
    return null
  }

  function selectedScreens() {
    var listed = Quickshell.screens
    if (outputDropped || !listed || listed.length === 0) return []
    if (outputName === "" || outputName === "first") return [listed[0]]
    if (outputName === "all") {
      var every = []
      for (var i = 0; i < listed.length; i++) every.push(listed[i])
      return every
    }
    for (var j = 0; j < listed.length; j++) {
      if (listed[j].name === outputName) return [listed[j]]
    }
    return []
  }

  readonly property var hostKeys: {
    var screens = selectedScreens()
    var dropped = {}
    var parts = droppedHosts.split(",")
    for (var d = 0; d < parts.length; d++) {
      if (parts[d] !== "") dropped[parts[d]] = true
    }
    var keys = []
    for (var s = 0; s < screens.length; s++) {
      var name = screens[s].name || "screen"
      for (var c = 0; c < hostCopies; c++) {
        var key = name + "#" + c
        if (!dropped[key]) keys.push(key)
      }
    }
    return keys
  }

  function screenFor(key) {
    var name = String(key || "").split("#")[0]
    var listed = Quickshell.screens
    if (!listed) return null
    for (var i = 0; i < listed.length; i++) {
      if (listed[i].name === name) return listed[i]
    }
    return null
  }

  function loadsClock(key) {
    if (Quickshell.env("TAMLINUX_CLOCK_ON_ALL") === "1")
      return hostKeys.indexOf(key) !== -1
    return hostKeys.length > 0 && hostKeys[0] === key
  }

  function attachHost(bar) {
    var next = hosts.filter(function(item) { return item !== bar })
    next.push(bar)
    hosts = next
    evidence("hosts-live " + hosts.length)
  }

  function detachHost(bar) {
    hosts = hosts.filter(function(item) { return item !== bar })
    evidence("hosts-live " + hosts.length)
  }

  function registerWidget(key, widget) {
    if (!widget) return
    for (var i = 0; i < liveWidgets.length; i++) {
      if (liveWidgets[i].widget === widget) return
    }
    var next = liveWidgets.slice()
    next.push({ key: key, id: String(widget.moduleName || ""), widget: widget })
    liveWidgets = next
    evidence("widget-registered " + String(widget.moduleName || "") + " host=" + key)
  }

  function unregisterHost(key) {
    liveWidgets = liveWidgets.filter(function(row) { return row.key !== key })
    evidence("host-cleared " + key)
  }

  function moduleWidgets(id) {
    var found = []
    var wanted = String(id || "")
    for (var i = 0; i < liveWidgets.length; i++) {
      if (liveWidgets[i].id === wanted && liveWidgets[i].widget)
        found.push(liveWidgets[i].widget)
    }
    return found
  }

  function firstWidget(id) {
    var items = moduleWidgets(id)
    return items.length > 0 ? items[0] : null
  }

  // ------------------------------------------------------------ panel routes
  //
  // Every screen's bar holds its own copy of each panel, and each copy
  // registers the same per-panel IPC target, which reaches only one of them.
  // Keys go through these routes instead, as on Omarchy (findPanelWidget):
  // an open copy wins, then the copy on the focused output (pickPanelSlot).
  // The overlays (Wi-Fi QR, both speed tests) and the OSD are single
  // windows in the services; the routes reach those too.

  readonly property var overlayIds: ["tamlinux.wifiqr", "tamlinux.speedtest", "tamlinux.disk-speedtest"]

  // The proof sets routeFocus (setRouteFocus) to check each screen's route
  // without moving the session's real focus; empty means the compositor's.
  property string routeFocus: ""

  function focusedScreenName() {
    if (routeFocus !== "") return routeFocus
    return compositor ? String(compositor.focusedOutputName || "") : ""
  }

  function isPanel(item) {
    return !!item && typeof item.open === "function" && typeof item.close === "function"
      && item.opened !== undefined
  }

  // The copy a key acts on; null when no bar draws that panel.
  function findPanelWidget(id) {
    var wanted = String(id || "")
    var candidates = []
    for (var i = 0; i < liveWidgets.length; i++) {
      var row = liveWidgets[i]
      if (row.id !== wanted || !isPanel(row.widget)) continue
      candidates.push({
        slot: row.widget,
        screenName: String(row.key).split("#")[0],
        opened: row.widget.opened === true
      })
    }
    return BarModel.pickPanelSlot(candidates, focusedScreenName())
  }

  function overlay(id) {
    if (overlayIds.indexOf(String(id || "")) === -1) return null
    var host = sessionServices.panels
    return host && host.panel ? host.panel(id) : null
  }

  function knownRoute(id) {
    return allowedId(id) || overlayIds.indexOf(id) !== -1 || id === "tamlinux.osd"
  }

  // Bar panels take no payload; the overlays and the OSD do (the network
  // panel passes the Wi-Fi QR its interface, the audio panel the OSD its
  // level). Panels call this as bar.shell.summon.
  function summon(id, payloadJson) {
    var payload = payloadJson === undefined || payloadJson === null ? "{}" : String(payloadJson)
    if (!knownRoute(id)) {
      evidence("unsupported summon " + id)
      return false
    }
    if (id === "tamlinux.osd") {
      var osd = sessionServices.osd
      if (!osd) return false
      osd.open(payload)
      return true
    }
    var item = findPanelWidget(id)
    if (item) {
      item.open()
      evidence("summoned " + id + " screen=" + panelScreen(item))
      return true
    }
    if (overlay(id)) {
      sessionServices.panels.summon(id, payload)
      evidence("summoned " + id + " overlay")
      return true
    }
    item = firstWidget(id)
    if (item && typeof item.open === "function") {
      item.open()
      evidence("summoned " + id)
      return true
    }
    evidence("summon-missing " + id)
    return false
  }

  function hidePlugin(id) {
    if (!knownRoute(id)) {
      evidence("unsupported hide " + id)
      return false
    }
    var item = findPanelWidget(id) || overlay(id) || firstWidget(id)
    if (!item || typeof item.close !== "function") {
      evidence("hide-missing " + id)
      return false
    }
    item.close()
    evidence("hidden " + id)
    return true
  }

  function togglePlugin(id) {
    if (!knownRoute(id)) {
      evidence("unsupported toggle " + id)
      return false
    }
    var item = findPanelWidget(id) || overlay(id)
    if (item) {
      if (item.opened === true) hidePlugin(id)
      else summon(id, "{}")
      evidence("toggled " + id)
      return true
    }
    // A widget that is not a panel but toggles something of its own.
    item = firstWidget(id)
    if (!item || typeof item.toggle !== "function") {
      evidence("toggle-missing " + id)
      return false
    }
    item.toggle()
    evidence("toggled " + id)
    return true
  }

  // One method on the copy a key would reach, such as the network panel's
  // showQr. Returns what it returned, "ok" for nothing, "unknown" when there
  // is no such panel or method, "error" when it threw.
  function callPanel(id, method) {
    var name = String(method || "")
    if (!knownRoute(id) || !/^[a-z][A-Za-z0-9]{0,63}$/.test(name)) {
      evidence("unsupported call " + id + " " + name.slice(0, 64))
      return "unknown"
    }
    var item = findPanelWidget(id) || overlay(id) || firstWidget(id)
    if (!item || typeof item[name] !== "function") {
      evidence("call-missing " + id + " " + name)
      return "unknown"
    }
    try {
      var result = item[name]()
      evidence("called " + id + " " + name)
      return result === undefined || result === null ? "ok" : String(result)
    } catch (e) {
      evidence("call-failed " + id + " " + name)
      return "error"
    }
  }

  // The bar that counts for togglePanelAt: the focused output's, or the
  // first. Every bar is laid out from one layout, so any one would do; the
  // focused one also answers which copies are drawn there.
  function countingHostKey() {
    var focused = focusedScreenName()
    var first = ""
    for (var i = 0; i < liveWidgets.length; i++) {
      var key = String(liveWidgets[i].key)
      if (key.split("#")[0] === focused) return key
      if (first === "") first = key
    }
    return first
  }

  // The ids of the panels in one bar section, in layout order, counting only
  // panels drawn on the counting bar: the tray, plain widgets, and a widget
  // hiding itself are passed over, as on Omarchy.
  function panelIdsIn(section) {
    var name = String(section || "")
    if (!barLayout || ["left", "center", "right"].indexOf(name) === -1) return []
    var entries = barLayout.layout[name]
    var key = countingHostKey()
    var ids = []
    for (var i = 0; i < entries.length; i++) {
      var id = BarModel.entryId(entries[i])
      for (var j = 0; j < liveWidgets.length; j++) {
        var row = liveWidgets[j]
        if (row.key !== key || row.id !== id) continue
        var item = row.widget
        if (!isPanel(item) || !BarModel.isDrawnSlot(item)) continue
        ids.push(id)
        break
      }
    }
    return ids
  }

  // The Nth panel of a section (one-based, for SUPER + CTRL + 1-9), toggled
  // on the focused screen. Returns the id it acted on, or "unknown".
  function togglePanelAt(section, index) {
    var ids = panelIdsIn(section)
    var n = Math.round(Number(index))
    var id = isFinite(n) && n >= 1 && n <= ids.length ? ids[n - 1] : ""
    if (id === "") {
      evidence("panel-at-missing " + String(section).slice(0, 16) + " " + String(index).slice(0, 8))
      return "unknown"
    }
    evidence("panel-at " + section + " " + n + " " + id)
    togglePlugin(id)
    return id
  }

  function panelScreen(item) {
    for (var i = 0; i < liveWidgets.length; i++) {
      if (liveWidgets[i].widget === item) return String(liveWidgets[i].key).split("#")[0]
    }
    return ""
  }

  function probePanels(section) {
    evidence("panels " + section + " " + panelIdsIn(section).join(","))
  }

  function openOn(key, id) {
    for (var i = 0; i < liveWidgets.length; i++) {
      var row = liveWidgets[i]
      if (row.key === key && row.id === id && row.widget && typeof row.widget.open === "function") {
        row.widget.open()
        evidence("opened " + id + " host=" + key)
        return true
      }
    }
    evidence("open-missing " + id + " host=" + key)
    return false
  }

  function dropHost(key) {
    var name = String(key || "")
    if (name === "" || droppedHosts.split(",").indexOf(name) !== -1) return
    droppedHosts = droppedHosts === "" ? name : droppedHosts + "," + name
    evidence("host-dropped " + name)
  }

  function probeWidgets() {
    evidence("widgets fred.clock=" + moduleWidgets("fred.clock").length
      + " tamlinux.fixture=" + moduleWidgets("tamlinux.fixture").length)
  }

  function clockHost() {
    for (var i = 0; i < hosts.length; i++) {
      if (hosts[i].loadsClock) return hosts[i]
    }
    return hosts.length > 0 ? hosts[0] : null
  }

  function probeSwitch() {
    var bar = clockHost()
    if (!bar || !bar.surface) {
      evidence("switch-result false")
      return
    }
    var panels = bar.surface.panelWidgets()
    evidence("switch-panels " + panels.length + " widgets " + bar.surface.widgets.length)
    if (panels.length < 2) {
      evidence("switch-result false")
      return
    }
    var owner = panels[0]
    for (var n = 0; n < panels.length; n++) {
      if (panels[n].moduleName === "fred.clock") owner = panels[n]
    }
    var ok = bar.surface.switchPanelFrom(owner, 1)
    evidence("switch-result " + (ok ? "true" : "false"))
  }

  function probeActions() {
    var bar = clockHost()
    if (!bar || !bar.surface) {
      evidence("actions-missing")
      return
    }
    var api = bar.surface
    api.pickAgent()
    api.openTerminal("btop")
    api.openTerminal("sh")
    api.notify("status")
    api.notify("$(bad)")
    var longText = ""
    for (var i = 0; i < 513; i++) longText += "a"
    api.notify(longText)
    api.openTimezoneMenu()
    api.run("tam-agent --pick")
    evidence("actions-probed")
  }

  function probeClick() {
    if (hosts.length < 2) {
      evidence("click-same false click-other false")
      return
    }
    var first = clockHost()
    var second = null
    for (var i = 0; i < hosts.length; i++) {
      if (hosts[i] !== first) {
        second = hosts[i]
        break
      }
    }
    if (!first || !second) {
      evidence("click-same false click-other false")
      return
    }
    var target = first.firstClickTarget ? first.firstClickTarget() : null
    var same = first.surface && first.surface.targetBelongsToWindow(target, first)
    var other = second.surface && second.surface.targetBelongsToWindow(target, second)
    evidence("click-same " + (same ? "true" : "false") + " click-other " + (other ? "true" : "false"))
  }

  FileView {
    id: settingsFile
    path: proof.settingsPath
    watchChanges: true
    printErrors: false
    onLoaded: {
      proof.ingestSettings(text())
      proof.settingsReady = true
    }
    onLoadFailed: {
      proof.ingestSettings("")
      proof.settingsReady = true
      proof.evidence("settings-missing")
    }
  }

  FileView {
    id: barLayoutFile
    path: proof.barLayoutPath
    printErrors: false
    onLoaded: {
      // Read once; later loads follow the shell's own writes.
      if (proof.barLayoutPath === "" || proof.barLayoutReady) return
      proof.ingestBarLayout(text())
      proof.barLayoutReady = true
    }
    onLoadFailed: {
      if (proof.barLayoutPath === "") return
      proof.ingestBarLayout("")
      proof.barLayoutReady = true
    }
  }

  FileView {
    path: proof.barFlagPath
    printErrors: false
    onLoaded: {
      proof.evidence("bar-flag hidden")
      proof.barHidden = true
      proof.barFlagWritten = true
      proof.barFlagReady = true
    }
    onLoadFailed: proof.barFlagReady = true
  }

  Process {
    id: barFlagProc
    clearEnvironment: true
    // A toggle that landed while the flag was being written is written next.
    onExited: if (proof.barFlagWritten !== proof.barHidden) proof.writeBarFlag()
  }

  IpcHandler {
    target: "tamlinux-shell"
    function ping(): void { proof.evidence("ping") }
    function tooltipProbe(): void {
      var bar = proof.clockHost()
      if (bar && bar.probeTooltip) bar.probeTooltip()
      else proof.evidence("tooltip-no-bar")
    }
    // Hover text on the named widget, as a plugin would show it, to check
    // where the tooltip lands. Logs the same tooltip evidence line.
    function tooltipProbeFor(id: string): void {
      var item = proof.firstWidget(id)
      var bar = item && item.bar ? item.bar : null
      if (!bar) {
        proof.evidence("tooltip-no-widget " + id)
        return
      }
      bar.showTooltip(item, "probe " + id + ": a long line of hover text that would run off the edge")
    }
    function dropOutput(): void {
      proof.outputDropped = true
      proof.evidence("output-dropped")
    }
    function dropHost(key: string): void { proof.dropHost(key) }
    function openOn(key: string, id: string): void { proof.openOn(key, id) }
    // The routes keys use: each reaches the copy on the focused screen.
    function summon(id: string): string { return proof.summon(id, "{}") ? "ok" : "unknown" }
    function hide(id: string): string { return proof.hidePlugin(id) ? "ok" : "unknown" }
    function toggle(id: string): string { return proof.togglePlugin(id) ? "ok" : "unknown" }
    function call(id: string, method: string): string { return proof.callPanel(id, method) }
    function togglePanelAt(section: string, index: string): string { return proof.togglePanelAt(section, index) }
    function probePanels(section: string): void { proof.probePanels(section) }
    // The bar itself: on, off, or toggle; top or bottom; transparency.
    // IPC arguments are not optional: toggleBar flips the bar (the key),
    // setBar on|off sets it.
    function toggleBar(): string { return proof.toggleBar("toggle") }
    function setBar(mode: string): string { return proof.toggleBar(mode) }
    function setBarPosition(position: string): string { return proof.setBarPosition(position) }
    function toggleBarTransparency(): string { return proof.toggleBarTransparency() }
    function refreshIndicators(): string { return String(proof.refreshIndicators()) }
    function setRouteFocus(name: string): void {
      proof.routeFocus = String(name || "").slice(0, 64)
      proof.evidence("route-focus " + proof.routeFocus)
    }
    function probeWidgets(): void { proof.probeWidgets() }
    function probeSwitch(): void { proof.probeSwitch() }
    function probeClick(): void { proof.probeClick() }
    function writeFixture(): void {
      proof.updateEntryInline("tamlinux.fixture", { "marker": "step2" })
    }
    function rejectSettings(): void {
      proof.updateEntryInline("omarchy.osd", { "marker": "no" })
    }
    function compositorFocusWorkspace(id: string): void {
      if (proof.compositor) proof.compositor.focusWorkspace(id)
    }
    function compositorFocusOutput(name: string): void {
      if (proof.compositor) proof.compositor.focusOutput(name)
    }
    function compositorSetDpms(name: string, on: string): void {
      if (proof.compositor) proof.compositor.setDpms(name, on)
    }
    function probeActions(): void { proof.probeActions() }
  }

  Compositor {
    id: compositorFacade
  }

  Services {
    id: sessionServices
    shell: proof
  }

  Component.onCompleted: {
    evidence("shell-id tamlinux-clock-proof")
    evidence("ipc-owner tamlinux-shell")
    evidence("scale " + Style.uiScale)
    evidence("omarchy " + (Quickshell.env("OMARCHY_PATH") ? "set" : "unset"))
    var panelPath = String(Quickshell.env("TAMLINUX_PANEL_ENTRY") || "")
    var compositorPath = String(Quickshell.env("TAMLINUX_COMPOSITOR_ENTRY") || "")
    var uiPath = String(Quickshell.env("TAMLINUX_UI_ENTRY") || "")
    if (panelPath !== "") fixtureEntry = panelPath
    if (compositorPath !== "") compositorEntry = compositorPath
    if (uiPath !== "") uiEntry = uiPath
    var rawEntries = String(Quickshell.env("TAMLINUX_EXTRA_ENTRIES") || "")
    var parsedEntries = []
    if (rawEntries !== "") {
      var entryParts = rawEntries.split("|")
      for (var n = 0; n < entryParts.length; n++) {
        if (entryParts[n] !== "") parsedEntries.push(entryParts[n])
      }
    }
    extraEntries = parsedEntries
    ingestPluginEntries(String(Quickshell.env("TAMLINUX_PLUGIN_ENTRIES") || "{}"))
    evidence("clock-entry " + clockEntry)
    evidence("extra-entries " + extraEntries.length)
    evidence("host-copies " + hostCopies)
    evidence("screens " + (Quickshell.screens ? Quickshell.screens.length : 0))
    evidence("bar " + (barEnabled ? "on" : "off"))
  }

  Variants {
    model: proof.settingsReady && proof.barLayoutReady && proof.barFlagReady && proof.barEnabled ? proof.hostKeys : []
    delegate: BarWindow {
      id: barWindow
      required property var modelData
      shell: proof
      hostKey: modelData
      screenRef: proof.screenFor(modelData)
      loadsClock: proof.loadsClock(modelData)
    }
  }

  Timer {
    interval: 1500
    running: proof.settingsReady && proof.barEnabled
    repeat: false
    onTriggered: {
      if (!proof.hostKeys || proof.hostKeys.length === 0)
        proof.evidence("output-missing name=" + proof.outputName)
    }
  }
}
