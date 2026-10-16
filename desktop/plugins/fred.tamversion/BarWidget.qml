import QtQuick
import Quickshell
import Tam.Ui

BarWidget {
  id: root
  moduleName: "fred.tamversion"
  readonly property string pluginVersion: "0.1.0"

  readonly property string installedVersion: Quickshell.env("TAMLINUX_VERSION") || "unknown"
  // VERSION uses SemVer (0.4.4-a); the bar uses the familiar 0.4.4a spelling.
  readonly property string displayVersion: installedVersion.replace(/^(\d+\.\d+\.\d+)-([a-z]+)$/, "$1$2")
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
