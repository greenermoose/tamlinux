import QtQuick
import Quickshell
import Quickshell.Io
import "../panels/audio" as AudioPanel
import "../panels/bluetooth" as BluetoothPanel
import "../panels/network" as NetworkPanel
import "../panels/wifiqr" as WifiQrPanel
import "../panels/power" as PowerPanel
import "../panels/speedtest" as SpeedTestPanel
import "../panels/diskspeedtest" as DiskSpeedTestPanel

// The ported panels without the Tamlinux bar (plan 18 0.2.4-0.2.6). Every
// panel shares one stand-in bar at the top of the focused output, offset by
// TAMLINUX_PANEL_TOP_OFFSET pixels so cards clear a bar drawn by another
// shell. Keys open a panel through its own IPC target, for example
// `tam-shell tamlinux.audio toggle`; an overlay without a target of its own
// opens through `tam-shell tamlinux.panels summon <id>`. TAMLINUX_PANELS
// names the panels to load, comma-separated; unknown names are ignored.
Item {
  id: host

  property var shell: null
  property var osd: null
  property var media: null

  readonly property var known: ["audio", "bluetooth", "network", "wifiqr", "power", "speedtest", "disk-speedtest"]
  readonly property var enabled: {
    var wanted = String(Quickshell.env("TAMLINUX_PANELS") || "").split(",")
    var picked = []
    for (var i = 0; i < wanted.length; i++) {
      var name = wanted[i].trim()
      if (known.indexOf(name) !== -1 && picked.indexOf(name) === -1) picked.push(name)
    }
    return picked
  }

  readonly property var focusedScreen: {
    var name = shell && shell.compositor ? String(shell.compositor.focusedOutputName || "") : ""
    var listed = Quickshell.screens
    if (!listed || listed.length === 0) return null
    for (var i = 0; i < listed.length; i++) {
      if (listed[i].name === name) return listed[i]
    }
    return listed[0]
  }

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function settingsFor(item) {
    var id = item && item.moduleName ? String(item.moduleName) : ""
    if (id === "" || !shell || !shell.entrySettings || !("settings" in item)) return
    item.settings = shell.entrySettings(id)
  }

  function adopt(item, name) {
    settingsFor(item)
    panelBar.registerWidget(item)
    note("panel-loaded " + name)
  }

  // The settings document loads after the panels may have.
  Connections {
    target: host.shell
    ignoreUnknownSignals: true
    function onSettingsDocChanged() {
      var items = panelBar.widgets
      for (var i = 0; i < items.length; i++) host.settingsFor(items[i])
    }
  }

  // Bar panels name themselves with moduleName; overlays (Wi-Fi QR, speed
  // tests) with manifest.id.
  function panel(id) {
    var wanted = String(id || "")
    var items = panelBar.widgets
    for (var i = 0; i < items.length; i++) {
      var item = items[i]
      if (!item) continue
      if (item.moduleName === wanted || (item.manifest && item.manifest.id === wanted)) return item
    }
    return null
  }

  // What the panels call as bar.shell. Only the calls the ported panels make.
  QtObject {
    id: panelShell

    readonly property var compositor: host.shell ? host.shell.compositor : null

    function summon(id, payloadJson) {
      if (id === "tamlinux.osd") {
        if (host.osd) host.osd.open(payloadJson)
        return !!host.osd
      }
      var item = host.panel(id)
      if (!item) {
        host.note("panel-missing " + id)
        return false
      }
      item.open(payloadJson)
      return true
    }

    function hide(id) {
      var item = host.panel(id)
      if (item) item.close()
      return !!item
    }

    function firstPartyServiceFor(id) {
      if (id === "tamlinux.media") return host.media
      if (id === "tamlinux.osd") return host.osd
      return null
    }

    // Panel settings (the tray's pins, the battery percentage) are saved in
    // the shell's settings document, beside the plugins'.
    function updateEntryInline(id, values) {
      if (!host.shell || !host.shell.updateEntryInline) {
        host.note("panel-setting-not-saved " + id)
        return false
      }
      return host.shell.updateEntryInline(id, values)
    }
  }

  BarApi {
    id: panelBar
    shell: panelShell
    hostKey: "panels"
    position: "top"
    barSize: Math.max(0, Number(Quickshell.env("TAMLINUX_PANEL_TOP_OFFSET") || 0))
    screen: host.focusedScreen
  }

  // Static imports, not URLs: Quickshell only scans files it reaches by import.
  Loader {
    active: host.enabled.indexOf("audio") !== -1
    sourceComponent: Component { AudioPanel.Panel { bar: panelBar } }
    onLoaded: host.adopt(item, "audio")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed audio")
  }

  Loader {
    active: host.enabled.indexOf("bluetooth") !== -1
    sourceComponent: Component { BluetoothPanel.Panel { bar: panelBar } }
    onLoaded: host.adopt(item, "bluetooth")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed bluetooth")
  }

  Loader {
    active: host.enabled.indexOf("network") !== -1
    sourceComponent: Component { NetworkPanel.Panel { bar: panelBar } }
    onLoaded: host.adopt(item, "network")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed network")
  }

  Loader {
    active: host.enabled.indexOf("wifiqr") !== -1
    sourceComponent: Component { WifiQrPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.wifiqr" }) } }
    onLoaded: host.adopt(item, "wifiqr")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed wifiqr")
  }

  Loader {
    active: host.enabled.indexOf("power") !== -1
    sourceComponent: Component { PowerPanel.Panel { bar: panelBar } }
    onLoaded: host.adopt(item, "power")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed power")
  }

  Loader {
    active: host.enabled.indexOf("speedtest") !== -1
    sourceComponent: Component { SpeedTestPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.speedtest" }) } }
    onLoaded: host.adopt(item, "speedtest")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed speedtest")
  }

  Loader {
    active: host.enabled.indexOf("disk-speedtest") !== -1
    sourceComponent: Component { DiskSpeedTestPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.disk-speedtest" }) } }
    onLoaded: host.adopt(item, "disk-speedtest")
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed disk-speedtest")
  }

  // Omarchy's menu opened overlays through its shell's generic summon; this is
  // the same route for the panels this host loads (0.2.6).
  IpcHandler {
    target: "tamlinux.panels"

    function summon(id: string): bool { return panelShell.summon(id, "{}") }
    function hide(id: string): bool { return panelShell.hide(id) }
  }

  Component.onCompleted: note("panels " + (enabled.length > 0 ? enabled.join(",") : "none"))
}
