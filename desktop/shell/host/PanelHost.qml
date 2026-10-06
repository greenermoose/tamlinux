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

    // Panel settings live with the bar; until it moves (0.3) changes last
    // only until the shell restarts.
    function updateEntryInline(id, values) {
      host.note("panel-setting-not-saved " + id)
      return false
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
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded audio") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed audio")
  }

  Loader {
    active: host.enabled.indexOf("bluetooth") !== -1
    sourceComponent: Component { BluetoothPanel.Panel { bar: panelBar } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded bluetooth") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed bluetooth")
  }

  Loader {
    active: host.enabled.indexOf("network") !== -1
    sourceComponent: Component { NetworkPanel.Panel { bar: panelBar } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded network") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed network")
  }

  Loader {
    active: host.enabled.indexOf("wifiqr") !== -1
    sourceComponent: Component { WifiQrPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.wifiqr" }) } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded wifiqr") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed wifiqr")
  }

  Loader {
    active: host.enabled.indexOf("power") !== -1
    sourceComponent: Component { PowerPanel.Panel { bar: panelBar } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded power") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed power")
  }

  Loader {
    active: host.enabled.indexOf("speedtest") !== -1
    sourceComponent: Component { SpeedTestPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.speedtest" }) } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded speedtest") }
    onStatusChanged: if (status === Loader.Error) host.note("panel-failed speedtest")
  }

  Loader {
    active: host.enabled.indexOf("disk-speedtest") !== -1
    sourceComponent: Component { DiskSpeedTestPanel.Panel { shell: panelShell; manifest: ({ id: "tamlinux.disk-speedtest" }) } }
    onLoaded: { panelBar.registerWidget(item); host.note("panel-loaded disk-speedtest") }
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
