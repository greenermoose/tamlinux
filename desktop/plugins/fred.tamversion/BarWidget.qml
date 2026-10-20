import QtQuick
import Quickshell
import Tam.Ui

BarWidget {
  id: root
  moduleName: "fred.tamversion"
  readonly property string pluginVersion: "0.1.1"

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

  implicitWidth: label.implicitWidth
  implicitHeight: label.implicitHeight

  WidgetButton {
    id: label
    anchors.fill: parent
    bar: root.bar
    text: root.displayText
    pressable: false
    horizontalMargin: 8.75
  }
}
