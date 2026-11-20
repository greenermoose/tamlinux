import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Ui

BarWidget {
  id: root
  moduleName: "fred.tamversion"
  readonly property string pluginVersion: "0.1.6"

  readonly property string installedVersion: Quickshell.env("TAMLINUX_VERSION") || "unknown"
  // A completed milestone can have a shorter label without changing package
  // identity. The override expires when the installed version series changes.
  readonly property string milestoneVersion: String(setting("milestoneVersion", ""))
  readonly property bool showMilestone: /^\d+\.\d+\.\d+$/.test(milestoneVersion)
    && installedVersion.replace(/-[a-z]+$/, "") === milestoneVersion
  // VERSION uses SemVer (0.4.4-a); otherwise retain the familiar 0.4.4a spelling.
  readonly property string displayVersion: showMilestone ? milestoneVersion
    : installedVersion.replace(/^(\d+\.\d+\.\d+)-([a-z]+)$/, "$1$2")
  readonly property string displayText: "Tamlinux " + displayVersion

  readonly property string configDir: Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")
  readonly property string versionNotesPath: Quickshell.env("TAMLINUX_VERSION_NOTES")
    || "/usr/lib/tamlinux/current/share/tamlinux/version-notes.txt"
  property string rawVersionNotes: ""

  readonly property bool hasCultivarEnv: !!Quickshell.env("TAMLINUX_CULTIVAR")
  property string cultivarName: hasCultivarEnv ? Quickshell.env("TAMLINUX_CULTIVAR") : ""

  readonly property bool hasKernelEnv: !!Quickshell.env("TAMLINUX_KERNEL_RELEASE")
  property string kernelRelease: hasKernelEnv ? Quickshell.env("TAMLINUX_KERNEL_RELEASE") : ""

  readonly property bool hasOsNameEnv: !!Quickshell.env("TAMLINUX_OS_NAME")
  property string osName: hasOsNameEnv ? Quickshell.env("TAMLINUX_OS_NAME") : "Arch Linux"

  readonly property string compositorName: Quickshell.env("TAMLINUX_COMPOSITOR")
    || Quickshell.env("XDG_CURRENT_DESKTOP")
    || Quickshell.env("DESKTOP_SESSION")
    || "Hyprland"

  readonly property string compositorVersion: Quickshell.env("TAMLINUX_HYPRLAND_VERSION") || ""

  FileView {
    id: versionNotesFile
    path: root.versionNotesPath
    printErrors: false
    watchChanges: true
    blockLoading: true
    onLoaded: root.rawVersionNotes = text().trim()
    onLoadFailed: root.rawVersionNotes = ""
    onFileChanged: reload()
  }

  FileView {
    id: cultivarFile
    path: root.configDir + "/tamlinux/cultivar"
    printErrors: false
    watchChanges: true
    blockLoading: true
    onLoaded: if (!root.hasCultivarEnv) root.cultivarName = text().trim()
    onLoadFailed: if (!root.hasCultivarEnv) root.cultivarName = ""
    onFileChanged: reload()
  }

  FileView {
    id: osreleaseWatcher
    path: "/proc/sys/kernel/osrelease"
    printErrors: false
    blockLoading: true
    onLoaded: if (!root.hasKernelEnv) root.kernelRelease = text().trim()
    onLoadFailed: if (!root.hasKernelEnv) root.kernelRelease = ""
  }

  FileView {
    id: osReleaseFile
    path: "/etc/os-release"
    printErrors: false
    blockLoading: true
    onLoaded: {
      if (!root.hasOsNameEnv) {
        var match = text().match(/^PRETTY_NAME="?([^"\n]+)"?/m) || text().match(/^NAME="?([^"\n]+)"?/m)
        if (match && match[1]) root.osName = match[1]
      }
    }
    onLoadFailed: if (!root.hasOsNameEnv) root.osName = "Arch Linux"
  }

  function formatHover() {
    var title = root.cultivarName !== ""
      ? ("Tamlinux cultivar " + root.cultivarName + " " + root.displayVersion)
      : root.displayText
    var kernelPart = root.kernelRelease !== ""
      ? ("Linux " + (root.kernelRelease.indexOf("-") !== -1 ? root.kernelRelease.split("-")[0] : root.kernelRelease))
      : ""
    var hostParts = [root.osName]
    if (kernelPart !== "") hostParts.push(kernelPart)
    if (root.compositorName !== "") hostParts.push(root.compositorName + (root.compositorVersion !== "" ? " " + root.compositorVersion : ""))
    var hostLine = hostParts.join(" · ")
    return [title, hostLine, "", "fred.tamversion v" + root.pluginVersion].join("\n")
  }

  readonly property string tooltipText: formatHover()

  function wrapLine(line, width) {
    var trimmed = line.replace(/\s+$/, "")
    if (trimmed.length <= width) return trimmed
    var indentMatch = trimmed.match(/^(\s*-\s+|\s+)/)
    var indent = indentMatch ? (indentMatch[1].indexOf("-") !== -1 ? "  " : indentMatch[1]) : ""
    var words = trimmed.split(/\s+/)
    var lines = []
    var current = words[0]
    for (var i = 1; i < words.length; i++) {
      if (current.length + 1 + words[i].length <= width) {
        current += " " + words[i]
      } else {
        lines.push(current)
        current = indent + words[i]
      }
    }
    lines.push(current)
    return lines.join("\n")
  }

  function wrapNotes(text, width) {
    var lines = text.split(/\r?\n/)
    var out = []
    for (var i = 0; i < lines.length; i++) out.push(wrapLine(lines[i], width))
    return out.join("\n")
  }

  function formatVersionNotes() {
    var fallback = "Tamlinux " + root.displayVersion + " version notes\n\nNo version notes recorded for this version."
    var raw = root.rawVersionNotes
    if (!raw || root.installedVersion === "unknown") return fallback
    var firstLine = raw.split(/\r?\n/, 1)[0].trim()
    var displayHeader = "Tamlinux " + root.displayVersion + " version notes"
    var installedHeader = "Tamlinux " + root.installedVersion + " version notes"
    if (firstLine.indexOf(displayHeader) !== 0 && firstLine.indexOf(installedHeader) !== 0) {
      return fallback
    }
    return wrapNotes(raw, 72)
  }

  readonly property string versionNotes: formatVersionNotes()

  function showVersionNotes() {
    if (root.bar && root.bar.showTooltip) root.bar.showTooltip(label, root.versionNotes)
  }

  onVersionNotesChanged: {}

  onTooltipTextChanged: {
    if (label.tooltipHovered && root.bar && root.bar.showTooltip) {
      root.bar.showTooltip(label, root.tooltipText)
    }
  }

  implicitWidth: label.implicitWidth
  implicitHeight: label.implicitHeight

  WidgetButton {
    id: label
    anchors.fill: parent
    bar: root.bar
    text: root.displayText
    tooltipText: root.tooltipText
    pressable: true
    onPressed: function(button) { if (button === Qt.LeftButton) root.showVersionNotes() }
    horizontalMargin: 8.75
  }
}
