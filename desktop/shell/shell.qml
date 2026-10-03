import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Commons
import "host"

ShellRoot {
  id: proof

  property string clockEntry: Quickshell.env("TAMLINUX_CLOCK_ENTRY") || ""
  property bool outputDropped: false
  property string outputName: Quickshell.env("TAMLINUX_OUTPUT") || ""
  property var settingsDoc: ({ "version": 1, "entries": {} })
  property bool settingsReady: false
  property var activeBar: null

  readonly property string settingsPath: (Quickshell.env("HOME") || "") + "/.config/tamlinux-shell/settings.json"

  function evidence(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  function clockEntrySettings() {
    var entries = settingsDoc && settingsDoc.entries ? settingsDoc.entries : {}
    var entry = entries["fred.clock"]
    return entry ? entry : { "id": "fred.clock" }
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

  function updateEntryInline(moduleName, settings) {
    if (moduleName !== "fred.clock") {
      evidence("settings-rejected " + moduleName)
      return false
    }
    var entry = { "id": "fred.clock" }
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
    doc.entries["fred.clock"] = entry
    settingsDoc = doc
    settingsFile.setText(JSON.stringify(doc, null, 2) + "\n")
    evidence("settings-wrote " + String(entry.format || ""))
    return true
  }

  readonly property var screenModel: {
    var listed = Quickshell.screens
    if (outputDropped) return []
    if (!listed || listed.length === 0) return []
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

  IpcHandler {
    target: "tamlinux-shell"
    function ping(): void { proof.evidence("ping") }
    function tooltipProbe(): void {
      if (proof.activeBar) proof.activeBar.probeTooltip()
      else proof.evidence("tooltip-no-bar")
    }
    function dropOutput(): void {
      proof.outputDropped = true
      proof.evidence("output-dropped")
    }
  }

  Component.onCompleted: {
    evidence("shell-id tamlinux-clock-proof")
    evidence("scale " + Style.uiScale)
    evidence("omarchy " + (Quickshell.env("OMARCHY_PATH") ? "set" : "unset"))
    evidence("clock-entry " + clockEntry)
  }

  Variants {
    model: proof.settingsReady ? proof.screenModel : []
    delegate: BarWindow {
      id: barWindow
      required property var modelData
      screenRef: modelData
      shell: proof
      onClockReady: function(widget) {
        proof.activeBar = barWindow
        var text = widget.displayText || ""
        proof.evidence("ready screen=" + (modelData.name || "")
          + " format=" + String(widget.configuredFormat || "")
          + " text=" + JSON.stringify(text))
      }
    }
  }

  Timer {
    interval: 1500
    running: proof.settingsReady
    repeat: false
    onTriggered: {
      if (!proof.screenModel || proof.screenModel.length === 0)
        proof.evidence("output-missing name=" + proof.outputName)
    }
  }
}
