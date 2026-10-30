import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Ui

BarWidget {
  id: root
  moduleName: "fred.tamversion"
  readonly property string pluginVersion: "0.1.3"

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

  readonly property bool hasCultivarEnv: !!Quickshell.env("TAMLINUX_CULTIVAR")
  property string cultivarName: hasCultivarEnv ? Quickshell.env("TAMLINUX_CULTIVAR") : ""

  readonly property bool hasGenerationEnv: !!Quickshell.env("TAMLINUX_GENERATION")
  property string generationNumber: hasGenerationEnv ? Quickshell.env("TAMLINUX_GENERATION") : ""

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
    id: generationFile
    path: root.configDir + "/tamlinux/generation"
    printErrors: false
    watchChanges: true
    blockLoading: true
    onLoaded: if (!root.hasGenerationEnv) root.generationNumber = text().trim()
    onLoadFailed: if (!root.hasGenerationEnv) root.generationNumber = ""
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
    var genLine = root.generationNumber !== ""
      ? ("Home Manager Generation " + root.generationNumber)
      : "Home Manager generation unavailable"
    var kernelPart = root.kernelRelease !== ""
      ? ("Linux " + (root.kernelRelease.indexOf("-") !== -1 ? root.kernelRelease.split("-")[0] : root.kernelRelease))
      : ""
    var hostParts = [root.osName]
    if (kernelPart !== "") hostParts.push(kernelPart)
    if (root.compositorName !== "") hostParts.push(root.compositorName + (root.compositorVersion !== "" ? " " + root.compositorVersion : ""))
    var hostLine = hostParts.join(" · ")
    return [title, genLine, hostLine, "", "fred.tamversion v" + root.pluginVersion].join("\n")
  }

  readonly property string tooltipText: formatHover()

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
    pressable: false
    horizontalMargin: 8.75
  }
}
