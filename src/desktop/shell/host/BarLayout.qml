import QtQuick
import Tam.Commons
import "../bar/BarModel.js" as BarModel
import "../bar/widgets" as BarWidgets
import "../panels/audio" as AudioPanel
import "../panels/bluetooth" as BluetoothPanel
import "../panels/network" as NetworkPanel
import "../panels/power" as PowerPanel

// The bar's three sections, drawn from a layout in BarModel.js's shape:
// { left: [entry], center: [entry], right: [entry] }, an entry being an id
// or { id }. An id is either one of the shell's own widgets below or a
// plugin whose entry file pluginEntries names. With centerAnchor set and in
// the center list, that widget sits at the bar's exact center and the rest
// of the center list flows out from it, as on Omarchy's bar. The tray stays
// on the inner edge of its section (pinTrayToInner).
Item {
  id: root

  required property var api
  property var layout: ({ "left": [], "center": [], "right": [] })
  property string centerAnchor: ""
  property var pluginEntries: ({})

  signal adoptRequested(var item, string id)

  // Static imports, not URLs: Quickshell only scans files it reaches by import.
  readonly property var builtins: ({
    "tamlinux.menu": menuWidget,
    "tamlinux.indicators": indicatorsWidget,
    "tamlinux.keyboard-layout": keyboardLayoutWidget,
    "tamlinux.tray": trayWidget,
    "tamlinux.audio": audioPanel,
    "tamlinux.bluetooth": bluetoothPanel,
    "tamlinux.network": networkPanel,
    "tamlinux.power": powerPanel
  })

  Component { id: menuWidget; BarWidgets.Menu {} }
  Component { id: indicatorsWidget; BarWidgets.Indicators {} }
  Component { id: keyboardLayoutWidget; BarWidgets.KeyboardLayout {} }
  Component { id: trayWidget; BarWidgets.Tray {} }
  Component { id: audioPanel; AudioPanel.Panel {} }
  Component { id: bluetoothPanel; BluetoothPanel.Panel {} }
  Component { id: networkPanel; NetworkPanel.Panel {} }
  Component { id: powerPanel; PowerPanel.Panel {} }

  readonly property var leftEntries: BarModel.pinTrayToInner(layout.left, "left")
  readonly property var rightEntries: BarModel.pinTrayToInner(layout.right, "right")
  readonly property var centerEntries: Array.isArray(layout.center) ? layout.center : []
  readonly property bool anchored: centerAnchor !== "" && BarModel.entryIndex(centerEntries, centerAnchor) !== -1
  readonly property real gap: Style.space(4)

  // The indicators show while the pointer is anywhere on the bar, so moving
  // from the clock to the icons it revealed never crosses a spot that hides
  // them. An ancestor of every widget stays hovered over each of them.
  HoverHandler {
    onHoveredChanged: root.api.centerSectionRevealHeld = hovered
  }

  function note(message) {
    console.log("TAMLINUX_EVIDENCE " + message)
  }

  component Slot: Loader {
    id: slot
    required property var modelData
    readonly property string entryId: BarModel.entryId(modelData)

    Component.onCompleted: {
      var builtin = root.builtins[entryId]
      if (builtin) {
        sourceComponent = builtin
        return
      }
      var entry = root.pluginEntries[entryId]
      if (entry) {
        source = entry
        return
      }
      root.note("bar-entry-unknown " + entryId)
    }
    onLoaded: root.adoptRequested(item, entryId)
    onStatusChanged: if (status === Loader.Error) root.note("bar-entry-failed " + entryId)
  }

  Row {
    id: leftRow
    anchors.left: parent.left
    anchors.leftMargin: root.gap
    anchors.verticalCenter: parent.verticalCenter
    spacing: root.gap
    Repeater { model: root.leftEntries; delegate: Slot {} }
  }

  Row {
    id: rightRow
    anchors.right: parent.right
    anchors.rightMargin: root.gap
    anchors.verticalCenter: parent.verticalCenter
    spacing: root.gap
    Repeater { model: root.rightEntries; delegate: Slot {} }
  }

  Item {
    id: center
    anchors.fill: parent

    // Without an anchor: the whole center list, centered.
    Row {
      visible: !root.anchored
      anchors.centerIn: parent
      spacing: root.gap
      Repeater { model: root.anchored ? [] : root.centerEntries; delegate: Slot {} }
    }

    // With one: the anchor centered, its neighbours flowing out from it.
    Row {
      id: anchorRow
      visible: root.anchored
      anchors.centerIn: parent
      Repeater { model: root.anchored ? [root.centerAnchor] : []; delegate: Slot {} }
    }

    Row {
      visible: root.anchored
      anchors.right: anchorRow.left
      anchors.rightMargin: root.gap
      anchors.verticalCenter: parent.verticalCenter
      spacing: root.gap
      Repeater { model: root.anchored ? BarModel.entriesBefore(root.centerEntries, root.centerAnchor) : []; delegate: Slot {} }
    }

    Row {
      visible: root.anchored
      anchors.left: anchorRow.right
      anchors.leftMargin: root.gap
      anchors.verticalCenter: parent.verticalCenter
      spacing: root.gap
      Repeater { model: root.anchored ? BarModel.entriesAfter(root.centerEntries, root.centerAnchor) : []; delegate: Slot {} }
    }
  }
}
