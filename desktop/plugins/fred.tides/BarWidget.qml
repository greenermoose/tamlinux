import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "fred.tides"

  readonly property string pluginVersion: "1.0.3"
  property string fontFamily: (root.settings && root.settings.fontFamily)
    ? root.settings.fontFamily
    : "Liberation Mono"
  property bool hoverOpen: false

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
    if ("pluginVersion" in target) target.pluginVersion = root.pluginVersion
    if ("fontFamily" in target) target.fontFamily = root.fontFamily
  }

  function refresh() {
    if (panelLoader.item && panelLoader.item.refresh) panelLoader.item.refresh()
  }

  function togglePanel() {
    if (panelLoader.item && panelLoader.item.toggle) panelLoader.item.toggle()
  }

  function toggle() {
    togglePanel()
  }

  // Shape contract for shell.summon/hide/toggle routing
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false

  function open() {
    if (panelLoader.item && panelLoader.item.openFromHotkey) panelLoader.item.openFromHotkey()
  }

  function close() {
    if (panelLoader.item && panelLoader.item.close) panelLoader.item.close()
  }

  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function closeForPopoutSwitch() {
    if (panelLoader.item) panelLoader.item.closeForPopoutSwitch()
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: panelLoader.item && panelLoader.item.label ? panelLoader.item.label : "\udb81\udf8d"
    slotSize: Style.bar.statusSlot
    tooltipText: ""

    HoverHandler {
      id: buttonHover
      onHoveredChanged: {
        if (hovered) {
          if (!root.opened) root.hoverOpen = true
        } else {
          root.hoverOpen = false
        }
      }
    }

    onPressed: function(b) {
      root.hoverOpen = false
      if (!root.bar) return
      if (b === Qt.RightButton) {
        if (panelLoader.item && panelLoader.item.statusSummary) {
          root.bar.run("omarchy-notification-send \"Tides\" \"" + panelLoader.item.statusSummary.replace(/"/g, "\\\"") + "\"")
        }
      } else if (b === Qt.MiddleButton) {
        root.refresh()
      } else {
        root.togglePanel()
      }
    }
  }

  PopupWindow {
    id: hoverPopup
    visible: root.hoverOpen && !root.opened
    color: "transparent"
    implicitWidth: Math.ceil(tooltipBubble.implicitWidth)
    implicitHeight: Math.ceil(tooltipBubble.implicitHeight)

    anchor {
      id: hoverAnchor
      window: button.QsWindow.window
      adjustment: PopupAdjustment.Slide
      edges: Edges.Top | Edges.Left
      gravity: Edges.Bottom | Edges.Right
      rect.width: 1
      rect.height: 1

      onAnchoring: {
        var barWin = button.QsWindow.window
        if (!barWin) return
        var popupWidth = hoverPopup.implicitWidth
        var popupHeight = hoverPopup.implicitHeight
        var localX = button.width / 2 - popupWidth / 2
        var localY = button.height + 6
        if (root.bar && root.bar.position === "bottom") {
          localY = -popupHeight - 6
        }
        var point = barWin.contentItem.mapFromItem(button, localX, localY)
        hoverAnchor.rect.x = Math.round(point.x)
        hoverAnchor.rect.y = Math.round(point.y)
      }
    }

    BorderSurface {
      id: tooltipBubble
      implicitWidth: tooltipCol.implicitWidth + Style.space(24)
      implicitHeight: tooltipCol.implicitHeight + Style.space(16)
      color: Color.tooltip.background
      borderSpec: Border.surfaceSpec("tooltip", "border", Color.tooltip.border, 1)
      radius: Style.cornerRadius

      Column {
        id: tooltipCol
        anchors.centerIn: parent
        spacing: Style.space(3)

        Repeater {
          model: (panelLoader.item && panelLoader.item.hoverLines) ? panelLoader.item.hoverLines : ["Tides"]
          Text {
            anchors.horizontalCenter: parent.horizontalCenter
            textFormat: Text.PlainText
            text: modelData
            color: Color.tooltip.text
            font.family: root.fontFamily
            font.pixelSize: Style.font.body
            horizontalAlignment: Text.AlignHCenter
          }
        }

        Item {
          width: 1
          height: Style.space(6)
        }

        Text {
          anchors.horizontalCenter: parent.horizontalCenter
          textFormat: Text.PlainText
          text: "fred.tides v" + root.pluginVersion
          color: Color.tooltip.text
          opacity: 0.45
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
          horizontalAlignment: Text.AlignHCenter
        }
      }
    }
  }
}
