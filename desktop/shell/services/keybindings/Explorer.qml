import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import Tam.Commons
import Tam.Commons as Commons
import "KeybindingsModel.js" as Model

PanelWindow {
  id: panel
  property var rows: []
  property bool bindingsAvailable: false
  property string modifier: "all"
  property string group: "All groups"
  property string sortOrder: "name"
  property var selected: null
  property bool capturing: false
  property bool showingTable: false
  readonly property var availability: Model.availability(rows)
  property string captureResult: ""
  property var lastCaptured: null
  property var lastTriedChord: []
  property string lastTriedCombo: ""
  property string commandPath: ""
  readonly property string appVersion: Model.APP_VERSION || "0.1.0"
  readonly property string buildRevision: Quickshell.env("TAMLINUX_KEYBINDINGS_REV") || ""
  readonly property string cultivarVersion: Quickshell.env("TAMLINUX_VERSION") || ""
  signal dismissRequested()

  component DarkButton: Button {
    id: btn
    property bool isAccent: false
    implicitHeight: 34
    leftPadding: 14
    rightPadding: 14
    contentItem: Text {
      text: btn.text
      font.pixelSize: 12
      font.bold: btn.checked || btn.isAccent
      color: btn.checked ? Commons.Color.accentText : (btn.isAccent ? Commons.Color.accentText : Commons.Color.foreground)
      horizontalAlignment: Text.AlignHCenter
      verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
      radius: Style.cornerRadius
      color: btn.checked ? Util.alpha(Commons.Color.accent, 0.25)
           : (btn.isAccent ? (btn.hovered ? Util.alpha(Commons.Color.accent, 0.30) : Util.alpha(Commons.Color.accent, 0.18))
           : (btn.down ? Util.alpha(Commons.Color.foreground, 0.14)
           : (btn.hovered ? Util.alpha(Commons.Color.foreground, 0.09) : Util.alpha(Commons.Color.foreground, 0.04))))
      border.color: btn.checked ? Commons.Color.accent
                  : (btn.isAccent ? Commons.Color.accent
                  : (btn.hovered ? Util.alpha(Commons.Color.foreground, 0.35) : Util.alpha(Commons.Color.foreground, 0.18)))
      border.width: 1
    }
  }
  component FilterBox: ComboBox {
    id: box
    implicitWidth: 125
    implicitHeight: 34
    contentItem: Text { leftPadding: 10; rightPadding: 22; text: box.displayText; font.pixelSize: 12; color: Commons.Color.foreground; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
    background: Rectangle { radius: Style.cornerRadius; color: box.hovered ? Util.alpha(Commons.Color.foreground, 0.08) : Util.alpha(Commons.Color.foreground, 0.04); border.color: box.visualFocus ? Commons.Color.accent : Util.alpha(Commons.Color.foreground, 0.22); border.width: 1 }
    popup: Popup {
      y: box.height + 4; width: box.width; implicitHeight: Math.min(240, contentItem.implicitHeight + 8); padding: 4
      contentItem: ListView { clip: true; implicitHeight: contentHeight; model: box.popup.visible ? box.delegateModel : null; currentIndex: box.highlightedIndex; ScrollIndicator.vertical: ScrollIndicator {} }
      background: Rectangle { color: "#101418"; border.color: Util.alpha(Commons.Color.accent, 0.45); border.width: 1; radius: Style.cornerRadius }
    }
    delegate: ItemDelegate {
      width: box.width - 8; height: 30; highlighted: box.highlightedIndex === index
      contentItem: Text { text: modelData; color: highlighted ? Commons.Color.accentText : Commons.Color.foreground; font.pixelSize: 12; verticalAlignment: Text.AlignVCenter }
      background: Rectangle { radius: 4; color: highlighted ? Util.alpha(Commons.Color.accent, 0.25) : "transparent" }
    }
  }
  readonly property var filtered: Model.sortExplorer(Model.filterExplorer(rows, modifier, search.text).filter(function(row) { return panel.group === "All groups" || row.group === panel.group }), sortOrder)
  onFilteredChanged: {
    if (filtered.length > 0) {
      var foundIndex = -1
      if (panel.selected) {
        for (var i = 0; i < filtered.length; i++) {
          if (filtered[i].display === panel.selected.display && filtered[i].arg === panel.selected.arg) {
            foundIndex = i
            break
          }
        }
      }
      if (foundIndex >= 0) {
        list.currentIndex = foundIndex
      } else {
        list.currentIndex = 0
      }
      panel.selected = filtered[list.currentIndex]
    } else {
      list.currentIndex = -1
      panel.selected = null
    }
  }
  anchors { top: true; bottom: true; left: true; right: true }
  color: "transparent"
  WlrLayershell.namespace: "tamlinux-keybindings"
  WlrLayershell.layer: WlrLayer.Overlay
  // Let other windows take focus while this reference remains visible.
  WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
  exclusionMode: ExclusionMode.Ignore
  onVisibleChanged: {
    if (visible) { showingTable = false; search.text = ""; modifier = "all"; group = "All groups"; groupSelect.currentIndex = 0; modifierSelect.currentIndex = 0; selected = filtered.length ? filtered[0] : null; lastCaptured = null; Qt.callLater(function() { search.forceActiveFocus() }) }
    else { capturing = false; inhibitor.enabled = false }
  }
  function closeExplorer() { capturing = false; inhibitor.enabled = false; dismissRequested() }
  function beginCapture() { lastCaptured = null; captureResult = ""; lastTriedChord = []; lastTriedCombo = ""; capturing = true; inhibitor.enabled = true; captureFocus.forceActiveFocus() }
  function finishCapture() {
    var target = panel.lastCaptured
    panel.capturing = false
    inhibitor.enabled = false
    if (target) {
      if (panel.modifier !== "all") panel.modifier = "all"
      if (panel.group !== "All groups") panel.group = "All groups"
      if (search.text !== "") search.text = ""
      Qt.callLater(function() {
        var targetIndex = -1
        for (var i = 0; i < panel.filtered.length; i++) {
          if (panel.filtered[i].display === target.display && panel.filtered[i].arg === target.arg) {
            targetIndex = i
            break
          }
        }
        if (targetIndex >= 0) {
          list.currentIndex = targetIndex
          panel.selected = panel.filtered[targetIndex]
          list.positionViewAtIndex(targetIndex, ListView.Center)
          list.forceActiveFocus()
        } else {
          search.forceActiveFocus()
        }
      })
    } else {
      search.forceActiveFocus()
    }
  }
  onSelectedChanged: {
    commandPath = ""
    if (!selected || selected.dispatcher !== "exec") return
    var match = selected.arg.match(/^([A-Za-z0-9_./+-]+)(?:\s|$)/)
    if (match && !pathLookup.running) {
      pathLookup.target = selected.arg
      pathLookup.command = ["sh", "-c", 'command -v -- "$1"', "sh", match[1]]
      pathLookup.running = true
    }
  }
  Process {
    environment: Util.hostEnvironment()
    id: pathLookup
    property string target: ""
    stdout: StdioCollector { onStreamFinished: if (panel.selected && panel.selected.arg === pathLookup.target && text.trim().charAt(0) === "/") panel.commandPath = text.trim() }
  }
  ShortcutInhibitor {
    id: inhibitor
    window: panel
    enabled: false
    onCancelled: { panel.capturing = false; panel.captureResult = "Capture was stopped by the compositor." }
  }
  Rectangle { anchors.fill: parent; color: Commons.Color.menu.scrim }
  MouseArea { anchors.fill: parent; onClicked: panel.closeExplorer() }
  Rectangle {
    id: card
    anchors.centerIn: parent
    width: Math.min(panel.width - 32, 1040)
    height: Math.min(panel.height - 32, 720)
    radius: Style.cornerRadius
    color: Commons.Color.menu.background
    border.color: Commons.Color.menu.border
    border.width: 1
    MouseArea { anchors.fill: parent }
    Column {
      anchors.fill: parent
      anchors.margins: 24
      spacing: 12
      Item {
        width: parent.width; height: 38
        Row {
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          spacing: 12
          Text {
            text: "Keyboard shortcuts"
            color: Commons.Color.menu.text
            font.pixelSize: 24
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
          }
          Rectangle {
            id: versionBadge
            anchors.verticalCenter: parent.verticalCenter
            height: 24
            width: versionBadgeRow.implicitWidth + 16
            radius: 12
            color: panel.buildRevision !== "" ? Util.alpha(Commons.Color.accent, 0.16) : Util.alpha(Commons.Color.menu.text, 0.08)
            border.color: panel.buildRevision !== "" ? Util.alpha(Commons.Color.accent, 0.45) : Util.alpha(Commons.Color.menu.border, 0.8)
            border.width: 1
            ToolTip.visible: badgeMouse.containsMouse
            ToolTip.delay: 300
            ToolTip.text: "Keybinding Explorer v" + panel.appVersion + (panel.buildRevision !== "" ? " • commit " + panel.buildRevision : "") + (panel.cultivarVersion !== "" ? " • Tamlinux " + panel.cultivarVersion : "")
            MouseArea {
              id: badgeMouse
              anchors.fill: parent
              hoverEnabled: true
            }
            Row {
              id: versionBadgeRow
              anchors.centerIn: parent
              spacing: 6
              Rectangle {
                visible: panel.buildRevision !== ""
                width: 6; height: 6; radius: 3
                color: Commons.Color.accent
                anchors.verticalCenter: parent.verticalCenter
              }
              Text {
                text: "v" + panel.appVersion + (panel.buildRevision !== "" ? " • " + panel.buildRevision : "")
                color: panel.buildRevision !== "" ? Commons.Color.accentText : Commons.Color.menu.text
                font.pixelSize: 11
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
              }
            }
          }
        }
        DarkButton {
          id: closeButton
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          text: "Close  Esc"
          onClicked: panel.closeExplorer()
        }
      }
      Row {
        width: parent.width; height: 40; spacing: 10
        TextField {
          id: search
          width: parent.width - 150
          height: parent.height
          color: Commons.Color.foreground
          placeholderTextColor: Util.alpha(Commons.Color.foreground, 0.45)
          selectedTextColor: Commons.Color.accentText
          selectionColor: Util.alpha(Commons.Color.accent, 0.4)
          font.pixelSize: 13
          leftPadding: 14
          rightPadding: 14
          verticalAlignment: Text.AlignVCenter
          background: Rectangle {
            radius: Style.cornerRadius
            color: "#0c0f12"
            border.color: search.activeFocus ? Commons.Color.accent : Util.alpha(Commons.Color.foreground, 0.22)
            border.width: 1
          }
          placeholderText: "Search shortcuts, actions, or commands (e.g. terminal, workspace, close)..."
          Keys.onEscapePressed: function(event) {
            if (search.text.length > 0) {
              search.text = ""
              event.accepted = true
            } else {
              panel.closeExplorer()
            }
          }
          Keys.onDownPressed: {
            if (list.count > 0) {
              list.forceActiveFocus()
              if (list.count > 1 && list.currentIndex === 0) {
                list.currentIndex = 1
              } else if (list.currentIndex < 0) {
                list.currentIndex = 0
              }
              list.positionViewAtIndex(list.currentIndex, ListView.Contain)
            }
          }
          Keys.onReturnPressed: {
            if (list.count > 0) {
              list.forceActiveFocus()
            }
          }
        }
        DarkButton {
          width: 140
          height: parent.height
          isAccent: true
          text: "Try a shortcut"
          onClicked: panel.beginCapture()
        }
      }
      Item {
        width: parent.width; height: 34
        Row {
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          spacing: 6
          Text { text: "Modifier keys"; color: Commons.Color.foreground; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
          FilterBox {
            id: modifierSelect
            model: ["All", "Super", "Super + Alt", "Super + Ctrl", "Super + Shift"]
            onCurrentIndexChanged: panel.modifier = ["all", "super", "alt", "ctrl", "shift"][currentIndex] || "all"
            Connections {
              target: panel
              function onModifierChanged() {
                var index = ["all", "super", "alt", "ctrl", "shift"].indexOf(panel.modifier)
                if (index >= 0 && modifierSelect.currentIndex !== index) modifierSelect.currentIndex = index
              }
            }
          }
          Text { text: "Groups"; color: Commons.Color.foreground; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
          ComboBox {
            id: groupSelect
            model: ["All groups", "Workspaces", "Windows", "Media and display", "Applications", "Other"]
            onCurrentTextChanged: panel.group = currentText
            contentItem: Text {
              leftPadding: 10
              rightPadding: 24
              text: groupSelect.displayText
              font.pixelSize: 12
              color: Commons.Color.foreground
              verticalAlignment: Text.AlignVCenter
              elide: Text.ElideRight
            }
            background: Rectangle {
              implicitWidth: 150
              implicitHeight: 34
              radius: Style.cornerRadius
              color: groupSelect.hovered ? Util.alpha(Commons.Color.foreground, 0.08) : Util.alpha(Commons.Color.foreground, 0.04)
              border.color: groupSelect.visualFocus ? Commons.Color.accent : Util.alpha(Commons.Color.foreground, 0.22)
              border.width: 1
            }
            popup: Popup {
              y: groupSelect.height + 4
              width: groupSelect.width
              implicitHeight: Math.min(240, contentItem.implicitHeight + 8)
              padding: 4
              contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: groupSelect.popup.visible ? groupSelect.delegateModel : null
                currentIndex: groupSelect.highlightedIndex
                ScrollIndicator.vertical: ScrollIndicator { }
              }
              background: Rectangle {
                color: "#101418"
                border.color: Util.alpha(Commons.Color.accent, 0.45)
                border.width: 1
                radius: Style.cornerRadius
              }
            }
            delegate: ItemDelegate {
              width: groupSelect.width - 8
              height: 30
              highlighted: groupSelect.highlightedIndex === index
              contentItem: Text {
                text: modelData
                color: highlighted ? Commons.Color.accentText : Commons.Color.foreground
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
              }
              background: Rectangle {
                radius: 4
                color: highlighted ? Util.alpha(Commons.Color.accent, 0.25) : "transparent"
              }
            }
            Connections {
              target: panel
              function onGroupChanged() {
                var idx = groupSelect.find(panel.group)
                if (idx >= 0 && groupSelect.currentIndex !== idx) groupSelect.currentIndex = idx
              }
            }
          }
          Text { text: "Sort by"; color: Commons.Color.foreground; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
          FilterBox {
            id: sortSelect
            model: ["Action name", "Key"]
            onCurrentIndexChanged: panel.sortOrder = currentIndex === 1 ? "key" : "name"
          }
          DarkButton {
            text: panel.showingTable ? "Back to list" : "Availability table"
            onClicked: { panel.showingTable = !panel.showingTable; if (panel.showingTable) tableFocus.forceActiveFocus(); else search.forceActiveFocus() }
          }
        }
        Row {
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: 8
          DarkButton {
            visible: (panel.modifier !== "all" || panel.group !== "All groups" || search.text !== "") && panel.width > 1200
            text: "Reset filters"
            onClicked: {
              panel.modifier = "all"
              panel.group = "All groups"
              groupSelect.currentIndex = 0
              search.text = ""
              search.forceActiveFocus()
            }
          }
          Rectangle {
            visible: panel.width > 1150
            height: 24
            width: countText.implicitWidth + 16
            radius: 12
            color: Util.alpha(Commons.Color.foreground, 0.04)
            border.color: Util.alpha(Commons.Color.foreground, 0.16)
            border.width: 1
            anchors.verticalCenter: parent.verticalCenter
            Text {
              id: countText
              anchors.centerIn: parent
              text: panel.filtered.length + (panel.filtered.length === 1 ? " shortcut" : " shortcuts")
              color: Commons.Color.foreground
              opacity: 0.85
              font.pixelSize: 11
              font.bold: true
            }
          }
        }
      }
      Row {
        width: parent.width
        height: parent.height - y
        spacing: 18
        ListView {
          id: list
          width: Math.floor((parent.width - 18) * 0.57); height: parent.height
          clip: true; spacing: 4; model: panel.filtered
          onCurrentIndexChanged: {
            if (currentIndex >= 0 && currentIndex < panel.filtered.length) {
              panel.selected = panel.filtered[currentIndex]
            }
          }
          Keys.onEscapePressed: function(event) {
            if (search.text.length > 0) {
              search.text = ""
              search.forceActiveFocus()
              event.accepted = true
            } else {
              panel.closeExplorer()
            }
          }
          Keys.onUpPressed: {
            if (currentIndex <= 0) {
              search.forceActiveFocus()
            } else {
              currentIndex = currentIndex - 1
              positionViewAtIndex(currentIndex, ListView.Contain)
            }
          }
          Keys.onDownPressed: {
            if (currentIndex < count - 1) {
              currentIndex = currentIndex + 1
              positionViewAtIndex(currentIndex, ListView.Contain)
            }
          }
          Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Backspace && search.text.length > 0) {
              search.text = search.text.substring(0, search.text.length - 1)
              search.forceActiveFocus()
              event.accepted = true
            } else if (event.text && event.text.length === 1 && event.key !== Qt.Key_Escape && event.key !== Qt.Key_Return && event.key !== Qt.Key_Enter && event.key !== Qt.Key_Tab && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))) {
              search.text += event.text
              search.forceActiveFocus()
              event.accepted = true
            }
          }
          ScrollBar.vertical: ScrollBar { }
          delegate: Rectangle {
            id: rowDelegate
            required property var modelData
            required property int index
            readonly property bool isSelected: list.currentIndex === index
            width: list.width; height: 42; radius: 6
            color: isSelected ? Util.alpha(Commons.Color.accent, 0.22) : (hover.containsMouse ? Util.alpha(Commons.Color.foreground, 0.06) : "transparent")
            border.color: isSelected ? Commons.Color.accent : (hover.containsMouse ? Util.alpha(Commons.Color.foreground, 0.15) : "transparent")
            border.width: 1

            // Active indicator bar on left edge
            Rectangle {
              anchors.left: parent.left
              anchors.leftMargin: 3
              anchors.verticalCenter: parent.verticalCenter
              width: 3
              height: 22
              radius: 1.5
              color: Commons.Color.accent
              visible: rowDelegate.isSelected
            }

            Text {
              anchors.left: panel.sortOrder === "key" ? chordRow.right : parent.left
              anchors.leftMargin: panel.sortOrder === "key" ? 12 : (rowDelegate.isSelected ? 14 : 12)
              anchors.right: panel.sortOrder === "key" ? parent.right : chordRow.left
              anchors.rightMargin: 12
              anchors.verticalCenter: parent.verticalCenter
              text: modelData.does
              color: rowDelegate.isSelected ? Commons.Color.accentText : Commons.Color.menu.text
              font.bold: true
              font.pixelSize: 13
              elide: Text.ElideRight
            }

            Row {
              id: chordRow
              width: panel.sortOrder === "key" ? parent.width * 0.46 : implicitWidth
              anchors.left: panel.sortOrder === "key" ? parent.left : undefined
              anchors.leftMargin: rowDelegate.isSelected ? 14 : 12
              anchors.right: panel.sortOrder === "key" ? undefined : parent.right
              anchors.rightMargin: 12
              anchors.verticalCenter: parent.verticalCenter
              spacing: 4

              Repeater {
                model: modelData.chord || (modelData.combo ? modelData.combo.split(" + ") : [])
                Row {
                  spacing: 4
                  anchors.verticalCenter: parent.verticalCenter
                  Text {
                    visible: index > 0
                    text: "+"
                    color: rowDelegate.isSelected ? Commons.Color.accentText : Commons.Color.menu.text
                    opacity: rowDelegate.isSelected ? 0.7 : 0.4
                    font.pixelSize: 11
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                  }
                  Rectangle {
                    height: 22
                    width: Math.max(22, keyLabel.implicitWidth + 12)
                    radius: 4
                    color: rowDelegate.isSelected ? Util.alpha(Commons.Color.accent, 0.28) : Util.alpha(Commons.Color.foreground, 0.08)
                    border.color: rowDelegate.isSelected ? Commons.Color.accent : Util.alpha(Commons.Color.foreground, 0.18)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                      id: keyLabel
                      anchors.centerIn: parent
                      text: modelData
                      color: rowDelegate.isSelected ? Commons.Color.accentText : Commons.Color.menu.text
                      font.pixelSize: 11
                      font.bold: true
                      font.family: Style.fontFamily
                    }
                  }
                }
              }
            }

            MouseArea {
              id: hover
              anchors.fill: parent
              hoverEnabled: true
              onClicked: {
                list.currentIndex = index
                list.forceActiveFocus()
              }
            }
          }
          Text { anchors.centerIn: parent; visible: list.count === 0; text: panel.rows.length ? "No shortcuts found" : "No bindings available from the compositor"; color: Commons.Color.menu.text; opacity: 0.7 }
        }
        Rectangle {
          width: parent.width - list.width - 18; height: parent.height; radius: 8
          color: Util.alpha(Commons.Color.foreground, 0.03)
          border.color: Util.alpha(Commons.Color.foreground, 0.12)
          border.width: 1

          // Empty state
          Column {
            anchors.centerIn: parent
            spacing: 8
            visible: !panel.selected
            width: parent.width - 32
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "Select a shortcut"
              font.bold: true
              font.pixelSize: 16
              color: Commons.Color.menu.text
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "Use arrow keys or click a row to inspect its details"
              color: Commons.Color.menu.text
              opacity: 0.6
              font.pixelSize: 13
            }
          }

          // Populated inspector details
          Flickable {
            anchors.fill: parent
            anchors.margins: 16
            visible: !!panel.selected
            contentWidth: width
            contentHeight: detailsCol.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            Column {
              id: detailsCol
              width: parent.width
              spacing: 14

              // Title and Category Tag
              Column {
                width: parent.width
                spacing: 8
                Row {
                  width: parent.width
                  spacing: 8
                  Rectangle {
                    height: 22
                    width: catLabel.implicitWidth + 14
                    radius: 11
                    color: Util.alpha(Commons.Color.foreground, 0.08)
                    border.color: Util.alpha(Commons.Color.foreground, 0.2)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: catLabel
                      anchors.centerIn: parent
                      text: panel.selected ? panel.selected.group : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Commons.Color.menu.text
                    }
                  }
                  Rectangle {
                    height: 22
                    width: dispLabel.implicitWidth + 14
                    radius: 11
                    color: Util.alpha(Commons.Color.accent, 0.15)
                    border.color: Util.alpha(Commons.Color.accent, 0.4)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: dispLabel
                      anchors.centerIn: parent
                      text: panel.selected ? (panel.selected.dispatcher || "internal") : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Commons.Color.menu.selectedText
                    }
                  }
                }

                Text {
                  width: parent.width
                  text: panel.selected ? panel.selected.does : ""
                  color: Commons.Color.accentText
                  font.bold: true
                  font.pixelSize: 20
                  wrapMode: Text.Wrap
                }
              }

              // Key Combination Badges
              Row {
                spacing: 4
                Repeater {
                  model: panel.selected ? (panel.selected.chord || (panel.selected.combo ? panel.selected.combo.split(" + ") : [])) : []
                  Row {
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      visible: index > 0
                      text: "+"
                      color: Commons.Color.menu.text
                      opacity: 0.5
                      font.pixelSize: 12
                      font.bold: true
                      anchors.verticalCenter: parent.verticalCenter
                    }
                    Rectangle {
                      height: 26
                      width: Math.max(26, detailKeyLabel.implicitWidth + 14)
                      radius: 4
                      color: Util.alpha(Commons.Color.accent, 0.22)
                      border.color: Commons.Color.accent
                      border.width: 1
                      anchors.verticalCenter: parent.verticalCenter

                      Text {
                        id: detailKeyLabel
                        anchors.centerIn: parent
                        text: modelData
                        color: Commons.Color.accentText
                        font.pixelSize: 12
                        font.bold: true
                        font.family: Style.fontFamily
                      }
                    }
                  }
                }
              }

              // Explanation Card
              Rectangle {
                width: parent.width
                height: explCol.implicitHeight + 20
                radius: 6
                color: Util.alpha(Commons.Color.foreground, 0.04)
                border.color: Util.alpha(Commons.Color.foreground, 0.12)
                border.width: 1

                Column {
                  id: explCol
                  anchors.left: parent.left
                  anchors.right: parent.right
                  anchors.margins: 12
                  anchors.verticalCenter: parent.verticalCenter
                  spacing: 4

                  Text {
                    text: "Action"
                    font.pixelSize: 11
                    font.bold: true
                    color: Commons.Color.accent
                  }
                  Text {
                    width: parent.width
                    wrapMode: Text.Wrap
                    color: Commons.Color.foreground
                    font.pixelSize: 13
                    lineHeight: 1.25
                    text: panel.selected && panel.selected.explanation ? panel.selected.explanation : "No additional explanation is available for this action."
                  }
                }
              }

              Column {
                width: parent.width; spacing: 5
                Text { text: "Why this shortcut (suggested)"; color: Commons.Color.accent; font.pixelSize: 11; font.bold: true }
                Text { width: parent.width; wrapMode: Text.Wrap; color: Commons.Color.foreground; font.pixelSize: 13; text: panel.selected && panel.selected.rationale ? panel.selected.rationale : "No explanation recorded for this binding." }
                Text { text: "Remember it"; color: Commons.Color.accent; font.pixelSize: 11; font.bold: true; topPadding: 6 }
                Text { width: parent.width; wrapMode: Text.Wrap; color: Commons.Color.foreground; font.pixelSize: 13; text: panel.selected && panel.selected.mnemonic ? panel.selected.mnemonic : "No mnemonic recorded for this binding." }
              }

              // Command & Dispatcher Card
              Column {
                width: parent.width
                spacing: 6

                Text {
                  text: "Command & Arguments"
                  font.pixelSize: 11
                  font.bold: true
                  color: Commons.Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: cmdText.implicitHeight + 16
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Commons.Color.foreground, 0.18)
                  border.width: 1

                  Text {
                    id: cmdText
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: panel.selected ? (panel.selected.arg || "(none)") : ""
                    font.family: Style.fontFamily
                    font.pixelSize: 12
                    color: Commons.Color.accent
                    wrapMode: Text.WrapAnywhere
                  }
                }
              }

              // Executable Path Card
              Column {
                width: parent.width
                spacing: 6

                Text {
                  text: "Executable Path"
                  font.pixelSize: 11
                  font.bold: true
                  color: Commons.Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: 34
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Commons.Color.foreground, 0.18)
                  border.width: 1

                  Row {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 10
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8

                    Rectangle {
                      width: 8; height: 8; radius: 4
                      anchors.verticalCenter: parent.verticalCenter
                      color: panel.commandPath ? "#68b087" : (panel.selected && panel.selected.dispatcher === "exec" ? "#c46b6b" : Commons.Color.accent)
                    }

                    Text {
                      width: parent.width - 16
                      text: panel.commandPath ? panel.commandPath : (panel.selected && panel.selected.dispatcher === "exec" ? "Executable not found on PATH" : "Built-in compositor dispatcher")
                      font.family: Style.fontFamily
                      font.pixelSize: 11
                      color: panel.commandPath ? Commons.Color.menu.text : (panel.selected && panel.selected.dispatcher === "exec" ? Commons.Color.urgent : Commons.Color.muted)
                      elide: Text.ElideMiddle
                      anchors.verticalCenter: parent.verticalCenter
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    Rectangle {
      anchors.fill: parent
      anchors.margins: 16
      anchors.topMargin: 170
      visible: panel.showingTable && !panel.capturing
      color: Commons.Color.menu.background
      MouseArea { anchors.fill: parent }
      Item {
        id: tableFocus
        anchors.fill: parent
        focus: panel.showingTable
        Keys.onEscapePressed: { panel.showingTable = false; search.forceActiveFocus() }
        Keys.onDownPressed: tableList.contentY = Math.min(tableList.contentY + 80, Math.max(0, tableList.contentHeight - tableList.height))
        Keys.onUpPressed: tableList.contentY = Math.max(0, tableList.contentY - 80)
        Column {
          anchors.fill: parent
          spacing: 8
          Text {
            width: parent.width
            text: panel.bindingsAvailable ? "Live bindings · * means no reported binding · Super is held in every column" : "No bindings available from the compositor"
            color: Commons.Color.foreground
            font.pixelSize: 12
          }
          Row {
            width: parent.width; height: 28; spacing: 2
            Repeater {
              model: ["Key", "Super", "+ Alt", "+ Ctrl", "+ Shift"]
              Rectangle {
                required property int index
                required property var modelData
                width: index === 0 ? 90 : (tableFocus.width - 98) / 4
                height: 28; color: Util.alpha(Commons.Color.accent, 0.16); radius: 3
                Text { anchors.fill: parent; anchors.margins: 6; text: modelData; color: Commons.Color.accentText; font.bold: true; font.pixelSize: 12; elide: Text.ElideRight }
              }
            }
          }
          ListView {
            id: tableList
            width: parent.width; height: parent.height - y
            clip: true
            model: panel.bindingsAvailable ? panel.availability.rows : []
            ScrollBar.vertical: ScrollBar { }
            delegate: Row {
              required property var modelData
              required property int index
              width: ListView.view.width; spacing: 2
              height: Math.max(32, c0.implicitHeight + 12, c1.implicitHeight + 12, c2.implicitHeight + 12, c3.implicitHeight + 12)
              Rectangle {
                width: 90; height: parent.height; color: Util.alpha(Commons.Color.foreground, 0.06)
                Text { anchors.fill: parent; anchors.margins: 6; text: modelData.key; color: Commons.Color.foreground; font.bold: true; font.pixelSize: 11; wrapMode: Text.WrapAnywhere }
              }
              Repeater {
                model: parent.modelData.cells
                Rectangle {
                  required property var modelData
                  required property int index
                  width: (tableFocus.width - 98) / 4; height: parent.height
                  color: Util.alpha(Commons.Color.foreground, modelData ? 0.06 : 0.025)
                  Text { id: cellText; anchors.fill: parent; anchors.margins: 6; text: modelData || "*"; color: modelData ? Commons.Color.foreground : Commons.Color.muted; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
              }
              // Invisible measurement texts keep multi-action cells fully visible.
              Text { id: c0; visible: false; width: (tableFocus.width - 98) / 4 - 12; text: parent.modelData.cells[0]; font.pixelSize: 11; wrapMode: Text.Wrap }
              Text { id: c1; visible: false; width: c0.width; text: parent.modelData.cells[1]; font.pixelSize: 11; wrapMode: Text.Wrap }
              Text { id: c2; visible: false; width: c0.width; text: parent.modelData.cells[2]; font.pixelSize: 11; wrapMode: Text.Wrap }
              Text { id: c3; visible: false; width: c0.width; text: parent.modelData.cells[3]; font.pixelSize: 11; wrapMode: Text.Wrap }
            }
            footer: Column {
              width: tableList.width; spacing: 4
              Text { visible: panel.bindingsAvailable; width: parent.width; text: "Other modifier combinations and unmodified keys"; color: Commons.Color.accentText; font.bold: true; font.pixelSize: 13; topPadding: 16; bottomPadding: 8 }
              Repeater {
                model: panel.bindingsAvailable ? panel.availability.other : []
                Row {
                  required property var modelData
                  width: parent.width; height: Math.max(otherCombo.implicitHeight, otherAction.implicitHeight) + 12; spacing: 2
                  Text { id: otherCombo; width: parent.width * 0.35; text: modelData.combo; color: Commons.Color.foreground; font.bold: true; font.pixelSize: 11; wrapMode: Text.Wrap }
                  Text { id: otherAction; width: parent.width * 0.64; text: modelData.does; color: Commons.Color.foreground; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
              }
            }
          }
        }
      }
    }
    Rectangle {
      anchors.fill: parent; visible: panel.capturing; radius: card.radius; color: Commons.Color.menu.background
      MouseArea { anchors.fill: parent }
      Item {
        id: captureFocus; anchors.fill: parent; focus: panel.capturing
        Keys.onPressed: function(event) {
          event.accepted = true
          if (event.key === Qt.Key_Escape) {
            panel.finishCapture()
            return
          }
          if (panel.lastCaptured && (event.key === Qt.Key_Return || event.key === Qt.Key_Enter)) {
            panel.finishCapture()
            return
          }
          if (!inhibitor.active) return
          if (event.key === Qt.Key_Shift || event.key === Qt.Key_Control || event.key === Qt.Key_Alt || event.key === Qt.Key_Meta || event.key === Qt.Key_Super_L || event.key === Qt.Key_Super_R) return
          var mask = ((event.modifiers & Qt.MetaModifier) ? 64 : 0) | ((event.modifiers & Qt.ControlModifier) ? 4 : 0) | ((event.modifiers & Qt.AltModifier) ? 8 : 0) | ((event.modifiers & Qt.ShiftModifier) ? 1 : 0)
          var names = {}; names[Qt.Key_Space] = "SPACE"; names[Qt.Key_Backspace] = "BACKSPACE"; names[Qt.Key_Return] = "RETURN"; names[Qt.Key_Tab] = "TAB"; names[Qt.Key_Left] = "LEFT"; names[Qt.Key_Right] = "RIGHT"; names[Qt.Key_Up] = "UP"; names[Qt.Key_Down] = "DOWN"
          var key = names[event.key] || (event.key >= 32 && event.key <= 126 ? String.fromCharCode(event.key).toUpperCase() : "")
          panel.lastTriedChord = Model.chordKeys(mask, key)
          panel.lastTriedCombo = Model.comboText(mask, key) || (key ? key : "Key")
          var found = Model.capturedBindings(panel.rows, mask, key, event.nativeScanCode)
          if (found.length > 0) {
            panel.lastCaptured = found[0]
            panel.captureResult = found.map(function(r) { return r.combo + "  →  " + r.does }).join("\n")
            panel.selected = found[0]
          } else {
            panel.lastCaptured = null
            panel.captureResult = panel.lastTriedCombo + "  →  No matching shortcut found"
          }
        }
      }
      Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 14

        Item {
          width: parent.width; height: 38
          Row {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            spacing: 12
            Text {
              text: "Try a shortcut"
              color: Commons.Color.menu.text
              font.pixelSize: 24
              font.bold: true
              anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
              height: 24
              width: captureStatusRow.implicitWidth + 16
              radius: 12
              color: inhibitor.active ? Util.alpha(Commons.Color.accent, 0.16) : Util.alpha(Commons.Color.menu.text, 0.08)
              border.color: inhibitor.active ? Util.alpha(Commons.Color.accent, 0.45) : Util.alpha(Commons.Color.menu.border, 0.8)
              border.width: 1
              anchors.verticalCenter: parent.verticalCenter
              Row {
                id: captureStatusRow
                anchors.centerIn: parent
                spacing: 6
                Rectangle {
                  width: 6; height: 6; radius: 3
                  color: inhibitor.active ? Commons.Color.accent : "#c46b6b"
                  anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                  text: inhibitor.active ? "Capture Active — Safe to test" : "Waiting for compositor capture"
                  color: inhibitor.active ? Commons.Color.accentText : Commons.Color.menu.text
                  font.pixelSize: 11
                  font.bold: true
                  anchors.verticalCenter: parent.verticalCenter
                }
              }
            }
          }
          DarkButton {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: "Back to list  Esc"
            onClicked: panel.finishCapture()
          }
        }

        Text {
          width: parent.width
          wrapMode: Text.Wrap
          color: Commons.Color.foreground
          opacity: 0.75
          font.pixelSize: 13
          text: inhibitor.active
            ? "Shortcuts are intercepted and will not run the command. Press any key combination to test it, and press another anytime."
            : "Waiting for the compositor to grant shortcut capture. Press Esc to exit."
        }

        Row {
          width: parent.width
          height: parent.height - y - 10
          spacing: 18

          // Left Pane: What you are trying
          Rectangle {
            id: tryPane
            width: Math.floor((parent.width - 18) * 0.44)
            height: parent.height
            radius: 8
            color: Util.alpha(Commons.Color.foreground, 0.02)
            border.color: Util.alpha(Commons.Color.foreground, 0.14)
            border.width: 1

            Column {
              anchors.fill: parent
              anchors.margins: 20
              spacing: 16

              // Header
              Row {
                width: parent.width
                spacing: 8
                Text {
                  text: "What you are trying"
                  font.pixelSize: 15
                  font.bold: true
                  color: Commons.Color.foreground
                  anchors.verticalCenter: parent.verticalCenter
                }
                Rectangle {
                  height: 20
                  width: liveBadgeText.implicitWidth + 12
                  radius: 10
                  color: Util.alpha(Commons.Color.accent, 0.16)
                  border.color: Util.alpha(Commons.Color.accent, 0.4)
                  border.width: 1
                  anchors.verticalCenter: parent.verticalCenter
                  Row {
                    anchors.centerIn: parent
                    spacing: 5
                    Rectangle {
                      width: 6; height: 6; radius: 3
                      color: Commons.Color.accent
                      anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                      id: liveBadgeText
                      text: "Listening"
                      color: Commons.Color.accentText
                      font.pixelSize: 10
                      font.bold: true
                    }
                  }
                }
              }

              // Active Keycap Box
              Rectangle {
                width: parent.width
                height: 110
                radius: 8
                color: panel.lastCaptured ? Util.alpha(Commons.Color.accent, 0.10)
                     : (panel.lastTriedCombo ? Util.alpha(Commons.Color.urgent, 0.08) : "#0c0f12")
                border.color: panel.lastCaptured ? Commons.Color.accent
                            : (panel.lastTriedCombo ? Util.alpha(Commons.Color.urgent, 0.45) : Util.alpha(Commons.Color.foreground, 0.20))
                border.width: 1

                Column {
                  anchors.centerIn: parent
                  spacing: 10

                  // Keycaps
                  Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 6
                    visible: panel.lastTriedChord.length > 0

                    Repeater {
                      model: panel.lastTriedChord
                      Row {
                        spacing: 6
                        anchors.verticalCenter: parent.verticalCenter
                        Text {
                          visible: index > 0
                          text: "+"
                          color: Commons.Color.accentText
                          opacity: 0.7
                          font.pixelSize: 14
                          font.bold: true
                          anchors.verticalCenter: parent.verticalCenter
                        }
                        Rectangle {
                          height: 34
                          width: Math.max(34, keycapLabel.implicitWidth + 18)
                          radius: 5
                          color: panel.lastCaptured ? Util.alpha(Commons.Color.accent, 0.26) : Util.alpha(Commons.Color.foreground, 0.12)
                          border.color: panel.lastCaptured ? Commons.Color.accent : Util.alpha(Commons.Color.foreground, 0.3)
                          border.width: 1
                          anchors.verticalCenter: parent.verticalCenter

                          Text {
                            id: keycapLabel
                            anchors.centerIn: parent
                            text: modelData
                            color: Commons.Color.accentText
                            font.pixelSize: 14
                            font.bold: true
                            font.family: Style.fontFamily
                          }
                        }
                      }
                    }
                  }

                  // Status line under keycaps
                  Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 6
                    visible: panel.lastTriedChord.length > 0

                    Rectangle {
                      width: 6; height: 6; radius: 3
                      color: panel.lastCaptured ? "#68b087" : Commons.Color.urgent
                      anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                      text: panel.lastCaptured ? panel.lastCaptured.does : "Unassigned key combination"
                      color: panel.lastCaptured ? "#68b087" : Commons.Color.urgent
                      font.pixelSize: 13
                      font.bold: true
                      anchors.verticalCenter: parent.verticalCenter
                    }
                  }

                  // Empty prompt when no key tried yet
                  Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: panel.lastTriedChord.length === 0
                    text: "Press any key combination on keyboard..."
                    color: Commons.Color.foreground
                    opacity: 0.6
                    font.pixelSize: 14
                  }
                }
              }

              // "Try another one" callout card
              Rectangle {
                width: parent.width
                height: tryAnotherCol.implicitHeight + 24
                radius: 8
                color: Util.alpha(Commons.Color.foreground, 0.04)
                border.color: Util.alpha(Commons.Color.foreground, 0.12)
                border.width: 1

                Column {
                  id: tryAnotherCol
                  anchors.left: parent.left
                  anchors.right: parent.right
                  anchors.margins: 14
                  anchors.verticalCenter: parent.verticalCenter
                  spacing: 6

                  Row {
                    spacing: 6
                    Text {
                      text: "⚡"
                      font.pixelSize: 13
                      anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                      text: "Try another one anytime"
                      font.pixelSize: 12
                      font.bold: true
                      color: Commons.Color.accent
                      anchors.verticalCenter: parent.verticalCenter
                    }
                  }

                  Text {
                    width: parent.width
                    wrapMode: Text.Wrap
                    color: Commons.Color.foreground
                    opacity: 0.75
                    font.pixelSize: 12
                    lineHeight: 1.3
                    text: "No need to reset or press enter. Simply press any other shortcut on your keyboard right now to test it."
                  }
                }
              }

              // Common shortcuts suggestions
              Column {
                width: parent.width
                spacing: 8

                Text {
                  text: "Popular shortcuts you can test:"
                  font.pixelSize: 11
                  font.bold: true
                  color: Commons.Color.foreground
                  opacity: 0.6
                }

                Flow {
                  width: parent.width
                  spacing: 6

                  Repeater {
                    model: [
                      { combo: "SUPER + RETURN", desc: "Terminal" },
                      { combo: "SUPER + BACKSPACE", desc: "Close" },
                      { combo: "SUPER + K", desc: "Explorer" },
                      { combo: "SUPER + SPACE", desc: "Launcher" },
                      { combo: "ALT + TAB", desc: "Cycle" }
                    ]
                    Rectangle {
                      height: 24
                      width: sampleRow.implicitWidth + 12
                      radius: 4
                      color: Util.alpha(Commons.Color.foreground, 0.05)
                      border.color: Util.alpha(Commons.Color.foreground, 0.15)
                      border.width: 1

                      Row {
                        id: sampleRow
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                          text: modelData.combo
                          color: Commons.Color.accent
                          font.pixelSize: 10
                          font.bold: true
                          font.family: Style.fontFamily
                        }
                        Text {
                          text: "(" + modelData.desc + ")"
                          color: Commons.Color.foreground
                          opacity: 0.6
                          font.pixelSize: 10
                        }
                      }
                    }
                  }
                }
              }

              Item { width: 1; height: 1 }

              DarkButton {
                width: parent.width
                text: "Back to list  (Esc)"
                onClicked: panel.finishCapture()
              }
            }
          }

          // Right Pane: What that does
          Rectangle {
            id: doesPane
            width: parent.width - tryPane.width - 18
            height: parent.height
            radius: 8
            color: Util.alpha(Commons.Color.foreground, 0.02)
            border.color: panel.lastCaptured ? Util.alpha(Commons.Color.accent, 0.4) : Util.alpha(Commons.Color.foreground, 0.14)
            border.width: 1

            // 1. Initial State: Waiting for input
            Column {
              anchors.centerIn: parent
              spacing: 14
              width: Math.min(parent.width - 60, 480)
              visible: panel.lastTriedChord.length === 0

              Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 56; height: 56; radius: 28
                color: Util.alpha(Commons.Color.accent, 0.14)
                border.color: Util.alpha(Commons.Color.accent, 0.35)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "→"
                  font.pixelSize: 24
                  font.bold: true
                  color: Commons.Color.accent
                }
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "What that does"
                color: Commons.Color.foreground
                font.pixelSize: 17
                font.bold: true
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                color: Commons.Color.foreground
                opacity: 0.65
                font.pixelSize: 13
                lineHeight: 1.3
                text: "Press any key combination on the left. The matching command, category, explanation, and executable path will display here."
              }
            }

            // 2. Unmatched State: No binding found
            Column {
              anchors.centerIn: parent
              spacing: 14
              width: Math.min(parent.width - 60, 480)
              visible: panel.lastTriedChord.length > 0 && !panel.lastCaptured

              Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 56; height: 56; radius: 28
                color: Util.alpha(Commons.Color.urgent, 0.12)
                border.color: Util.alpha(Commons.Color.urgent, 0.35)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "✕"
                  font.pixelSize: 22
                  font.bold: true
                  color: Commons.Color.urgent
                }
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "No action assigned"
                color: Commons.Color.foreground
                font.pixelSize: 17
                font.bold: true
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                color: Commons.Color.foreground
                opacity: 0.70
                font.pixelSize: 13
                lineHeight: 1.3
                text: "The combination '" + panel.lastTriedCombo + "' is not bound to any command in your Hyprland configuration. It is available to assign."
              }
            }

            // 3. Matched State: Full details card!
            Flickable {
              anchors.fill: parent
              anchors.margins: 20
              visible: !!panel.lastCaptured
              contentWidth: width
              contentHeight: matchCol.implicitHeight
              clip: true
              boundsBehavior: Flickable.StopAtBounds

              Column {
                id: matchCol
                width: parent.width
                spacing: 14

                // Header: Section label & tags
                Row {
                  width: parent.width
                  spacing: 8

                  Text {
                    text: "What that does"
                    font.pixelSize: 15
                    font.bold: true
                    color: Commons.Color.foreground
                    anchors.verticalCenter: parent.verticalCenter
                  }

                  Rectangle {
                    height: 22
                    width: captureCatLabel.implicitWidth + 14
                    radius: 11
                    color: Util.alpha(Commons.Color.foreground, 0.08)
                    border.color: Util.alpha(Commons.Color.foreground, 0.22)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: captureCatLabel
                      anchors.centerIn: parent
                      text: panel.lastCaptured ? (panel.lastCaptured.group || "Other") : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Commons.Color.foreground
                    }
                  }

                  Rectangle {
                    height: 22
                    width: captureDispLabel.implicitWidth + 14
                    radius: 11
                    color: Util.alpha(Commons.Color.accent, 0.15)
                    border.color: Util.alpha(Commons.Color.accent, 0.45)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: captureDispLabel
                      anchors.centerIn: parent
                      text: panel.lastCaptured ? (panel.lastCaptured.dispatcher || "command") : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Commons.Color.accentText
                    }
                  }
                }

                // Action Name Title
                Text {
                  width: parent.width
                  text: panel.lastCaptured ? panel.lastCaptured.does : ""
                  color: Commons.Color.accentText
                  font.bold: true
                  font.pixelSize: 22
                  wrapMode: Text.Wrap
                }

                // Action Explanation Card
                Rectangle {
                  width: parent.width
                  height: captureExplCol.implicitHeight + 20
                  radius: 6
                  color: Util.alpha(Commons.Color.foreground, 0.04)
                  border.color: Util.alpha(Commons.Color.foreground, 0.12)
                  border.width: 1

                  Column {
                    id: captureExplCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 14
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                      text: "Action"
                      font.pixelSize: 11
                      font.bold: true
                      color: Commons.Color.accent
                    }
                    Text {
                      width: parent.width
                      wrapMode: Text.Wrap
                      color: Commons.Color.foreground
                      font.pixelSize: 13
                      lineHeight: 1.25
                      text: panel.lastCaptured && panel.lastCaptured.explanation ? panel.lastCaptured.explanation : "No additional explanation is available for this action."
                    }
                  }
                }

                Column {
                  width: parent.width; spacing: 5
                  Text { text: "Why this shortcut (suggested)"; color: Commons.Color.accent; font.pixelSize: 11; font.bold: true }
                  Text { width: parent.width; wrapMode: Text.Wrap; color: Commons.Color.foreground; font.pixelSize: 13; text: panel.lastCaptured && panel.lastCaptured.rationale ? panel.lastCaptured.rationale : "No explanation recorded for this binding." }
                  Text { text: "Remember it"; color: Commons.Color.accent; font.pixelSize: 11; font.bold: true; topPadding: 6 }
                  Text { width: parent.width; wrapMode: Text.Wrap; color: Commons.Color.foreground; font.pixelSize: 13; text: panel.lastCaptured && panel.lastCaptured.mnemonic ? panel.lastCaptured.mnemonic : "No mnemonic recorded for this binding." }
                }

                // Command & Arguments Card
                Column {
                  width: parent.width
                  spacing: 6

                  Text {
                    text: "Command & Arguments"
                    font.pixelSize: 11
                    font.bold: true
                    color: Commons.Color.accent
                  }

                  Rectangle {
                    width: parent.width
                    height: captureCmdText.implicitHeight + 16
                    radius: 6
                    color: "#0a0c0e"
                    border.color: Util.alpha(Commons.Color.foreground, 0.18)
                    border.width: 1

                    Text {
                      id: captureCmdText
                      anchors.left: parent.left
                      anchors.right: parent.right
                      anchors.margins: 12
                      anchors.verticalCenter: parent.verticalCenter
                      text: panel.lastCaptured ? (panel.lastCaptured.arg || "(none)") : ""
                      font.family: Style.fontFamily
                      font.pixelSize: 12
                      color: Commons.Color.accent
                      wrapMode: Text.WrapAnywhere
                    }
                  }
                }

                // Executable Path Card
                Column {
                  width: parent.width
                  spacing: 6

                  Text {
                    text: "Executable Path"
                    font.pixelSize: 11
                    font.bold: true
                    color: Commons.Color.accent
                  }

                  Rectangle {
                    width: parent.width
                    height: 34
                    radius: 6
                    color: "#0a0c0e"
                    border.color: Util.alpha(Commons.Color.foreground, 0.18)
                    border.width: 1

                    Row {
                      anchors.left: parent.left
                      anchors.right: parent.right
                      anchors.margins: 12
                      anchors.verticalCenter: parent.verticalCenter
                      spacing: 8

                      Rectangle {
                        width: 8; height: 8; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: panel.commandPath ? "#68b087" : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? "#c46b6b" : Commons.Color.accent)
                      }

                      Text {
                        width: parent.width - 20
                        text: panel.commandPath ? panel.commandPath : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? "Executable not found on PATH" : "Built-in compositor dispatcher")
                        font.family: Style.fontFamily
                        font.pixelSize: 11
                        color: panel.commandPath ? Commons.Color.foreground : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? Commons.Color.urgent : Commons.Color.muted)
                        elide: Text.ElideMiddle
                        anchors.verticalCenter: parent.verticalCenter
                      }
                    }
                  }
                }

                // Inspect button
                DarkButton {
                  isAccent: true
                  text: "Inspect in main list  (Enter)"
                  onClicked: panel.finishCapture()
                }
              }
            }
          }
        }
      }
    }
  }
}
