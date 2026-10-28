import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import Tam.Commons
import "KeybindingsModel.js" as Model

PanelWindow {
  id: panel
  property var rows: []
  property string modifier: "all"
  property string group: "All groups"
  property var selected: null
  property bool capturing: false
  property string captureResult: ""
  property var lastCaptured: null
  property string commandPath: ""
  readonly property string appVersion: Model.APP_VERSION || "0.1.0"
  readonly property string buildRevision: Quickshell.env("TAMLINUX_KEYBINDINGS_REV") || ""
  readonly property string cultivarVersion: Quickshell.env("TAMLINUX_VERSION") || ""
  signal closed()

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
      color: btn.checked ? Color.accentText : (btn.isAccent ? Color.accentText : Color.foreground)
      horizontalAlignment: Text.AlignHCenter
      verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
      radius: Style.cornerRadius
      color: btn.checked ? Util.alpha(Color.accent, 0.25)
           : (btn.isAccent ? (btn.hovered ? Util.alpha(Color.accent, 0.30) : Util.alpha(Color.accent, 0.18))
           : (btn.down ? Util.alpha(Color.foreground, 0.14)
           : (btn.hovered ? Util.alpha(Color.foreground, 0.09) : Util.alpha(Color.foreground, 0.04))))
      border.color: btn.checked ? Color.accent
                  : (btn.isAccent ? Color.accent
                  : (btn.hovered ? Util.alpha(Color.foreground, 0.35) : Util.alpha(Color.foreground, 0.18)))
      border.width: 1
    }
  }
  readonly property var filtered: Model.filterExplorer(rows, modifier, search.text).filter(function(row) { return panel.group === "All groups" || row.group === panel.group })
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
  WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
  exclusionMode: ExclusionMode.Ignore
  onVisibleChanged: {
    if (visible) { search.text = ""; modifier = "all"; group = "All groups"; groupSelect.currentIndex = 0; selected = null; lastCaptured = null; Qt.callLater(function() { search.forceActiveFocus() }) }
    else { capturing = false; inhibitor.enabled = false }
  }
  function closeExplorer() { capturing = false; inhibitor.enabled = false; closed() }
  function beginCapture() { lastCaptured = null; captureResult = ""; capturing = true; inhibitor.enabled = true; captureFocus.forceActiveFocus() }
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
    var match = /^([A-Za-z0-9_./+-]+)(?:\s|$)/.exec(selected.arg)
    if (match && !pathLookup.running) {
      pathLookup.target = selected.arg
      pathLookup.command = ["sh", "-c", 'command -v -- "$1"', "sh", match[1]]
      pathLookup.running = true
    }
  }
  Process {
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
  Rectangle { anchors.fill: parent; color: Color.menu.scrim }
  MouseArea { anchors.fill: parent; onClicked: panel.closeExplorer() }
  Rectangle {
    id: card
    anchors.centerIn: parent
    width: Math.min(panel.width - 32, 1040)
    height: Math.min(panel.height - 32, 720)
    radius: Style.cornerRadius
    color: Color.menu.background
    border.color: Color.menu.border
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
            color: Color.menu.text
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
            color: panel.buildRevision !== "" ? Util.alpha(Color.accent, 0.16) : Util.alpha(Color.menu.text, 0.08)
            border.color: panel.buildRevision !== "" ? Util.alpha(Color.accent, 0.45) : Util.alpha(Color.menu.border, 0.8)
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
                color: Color.accent
                anchors.verticalCenter: parent.verticalCenter
              }
              Text {
                text: "v" + panel.appVersion + (panel.buildRevision !== "" ? " • " + panel.buildRevision : "")
                color: panel.buildRevision !== "" ? Color.accentText : Color.menu.text
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
          color: Color.foreground
          placeholderTextColor: Util.alpha(Color.foreground, 0.45)
          selectedTextColor: Color.accentText
          selectionColor: Util.alpha(Color.accent, 0.4)
          font.pixelSize: 13
          leftPadding: 14
          rightPadding: 14
          verticalAlignment: Text.AlignVCenter
          background: Rectangle {
            radius: Style.cornerRadius
            color: "#0c0f12"
            border.color: search.activeFocus ? Color.accent : Util.alpha(Color.foreground, 0.22)
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
          Repeater {
            model: [
              {label:"All", value:"all"},
              {label:"Super", value:"super"},
              {label:"Super + Alt", value:"alt"},
              {label:"Super + Ctrl", value:"ctrl"},
              {label:"Super + Shift", value:"shift"}
            ]
            DarkButton {
              required property var modelData
              text: modelData.label
              checkable: true
              checked: panel.modifier === modelData.value
              onClicked: { panel.modifier = modelData.value }
            }
          }
          Rectangle {
            width: 1; height: 20
            color: Util.alpha(Color.foreground, 0.16)
            anchors.verticalCenter: parent.verticalCenter
          }
          ComboBox {
            id: groupSelect
            model: ["All groups", "Workspaces", "Windows", "Media and display", "Applications", "Other"]
            onCurrentTextChanged: panel.group = currentText
            contentItem: Text {
              leftPadding: 10
              rightPadding: 24
              text: groupSelect.displayText
              font.pixelSize: 12
              color: Color.foreground
              verticalAlignment: Text.AlignVCenter
              elide: Text.ElideRight
            }
            background: Rectangle {
              implicitWidth: 150
              implicitHeight: 34
              radius: Style.cornerRadius
              color: groupSelect.hovered ? Util.alpha(Color.foreground, 0.08) : Util.alpha(Color.foreground, 0.04)
              border.color: groupSelect.visualFocus ? Color.accent : Util.alpha(Color.foreground, 0.22)
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
                border.color: Util.alpha(Color.accent, 0.45)
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
                color: highlighted ? Color.accentText : Color.foreground
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
              }
              background: Rectangle {
                radius: 4
                color: highlighted ? Util.alpha(Color.accent, 0.25) : "transparent"
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
        }
        Row {
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: 8
          DarkButton {
            visible: panel.modifier !== "all" || panel.group !== "All groups" || search.text !== ""
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
            height: 24
            width: countText.implicitWidth + 16
            radius: 12
            color: Util.alpha(Color.foreground, 0.04)
            border.color: Util.alpha(Color.foreground, 0.16)
            border.width: 1
            anchors.verticalCenter: parent.verticalCenter
            Text {
              id: countText
              anchors.centerIn: parent
              text: panel.filtered.length + (panel.filtered.length === 1 ? " shortcut" : " shortcuts")
              color: Color.foreground
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
            color: isSelected ? Util.alpha(Color.accent, 0.22) : (hover.containsMouse ? Util.alpha(Color.foreground, 0.06) : "transparent")
            border.color: isSelected ? Color.accent : (hover.containsMouse ? Util.alpha(Color.foreground, 0.15) : "transparent")
            border.width: 1

            // Active indicator bar on left edge
            Rectangle {
              anchors.left: parent.left
              anchors.leftMargin: 3
              anchors.verticalCenter: parent.verticalCenter
              width: 3
              height: 22
              radius: 1.5
              color: Color.accent
              visible: rowDelegate.isSelected
            }

            Text {
              anchors.left: parent.left; anchors.leftMargin: rowDelegate.isSelected ? 14 : 12
              anchors.right: chordRow.left; anchors.rightMargin: 12
              anchors.verticalCenter: parent.verticalCenter
              text: modelData.does
              color: rowDelegate.isSelected ? Color.accentText : Color.menu.text
              font.bold: true
              font.pixelSize: 13
              elide: Text.ElideRight
            }

            Row {
              id: chordRow
              anchors.right: parent.right; anchors.rightMargin: 12
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
                    color: rowDelegate.isSelected ? Color.accentText : Color.menu.text
                    opacity: rowDelegate.isSelected ? 0.7 : 0.4
                    font.pixelSize: 11
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                  }
                  Rectangle {
                    height: 22
                    width: Math.max(22, keyLabel.implicitWidth + 12)
                    radius: 4
                    color: rowDelegate.isSelected ? Util.alpha(Color.accent, 0.28) : Util.alpha(Color.foreground, 0.08)
                    border.color: rowDelegate.isSelected ? Color.accent : Util.alpha(Color.foreground, 0.18)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                      id: keyLabel
                      anchors.centerIn: parent
                      text: modelData
                      color: rowDelegate.isSelected ? Color.accentText : Color.menu.text
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
          Text { anchors.centerIn: parent; visible: list.count === 0; text: panel.rows.length ? "No shortcuts found" : "No bindings available from the compositor"; color: Color.menu.text; opacity: 0.7 }
        }
        Rectangle {
          width: parent.width - list.width - 18; height: parent.height; radius: 8
          color: Util.alpha(Color.foreground, 0.03)
          border.color: Util.alpha(Color.foreground, 0.12)
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
              color: Color.menu.text
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "Use arrow keys or click a row to inspect its details"
              color: Color.menu.text
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
                    color: Util.alpha(Color.foreground, 0.08)
                    border.color: Util.alpha(Color.foreground, 0.2)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: catLabel
                      anchors.centerIn: parent
                      text: panel.selected ? panel.selected.group : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Color.menu.text
                    }
                  }
                  Rectangle {
                    height: 22
                    width: dispLabel.implicitWidth + 14
                    radius: 11
                    color: Util.alpha(Color.accent, 0.15)
                    border.color: Util.alpha(Color.accent, 0.4)
                    border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                      id: dispLabel
                      anchors.centerIn: parent
                      text: panel.selected ? (panel.selected.dispatcher || "internal") : ""
                      font.pixelSize: 11
                      font.bold: true
                      color: Color.menu.selectedText
                    }
                  }
                }

                Text {
                  width: parent.width
                  text: panel.selected ? panel.selected.does : ""
                  color: Color.accentText
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
                      color: Color.menu.text
                      opacity: 0.5
                      font.pixelSize: 12
                      font.bold: true
                      anchors.verticalCenter: parent.verticalCenter
                    }
                    Rectangle {
                      height: 26
                      width: Math.max(26, detailKeyLabel.implicitWidth + 14)
                      radius: 4
                      color: Util.alpha(Color.accent, 0.22)
                      border.color: Color.accent
                      border.width: 1
                      anchors.verticalCenter: parent.verticalCenter

                      Text {
                        id: detailKeyLabel
                        anchors.centerIn: parent
                        text: modelData
                        color: Color.accentText
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
                color: Util.alpha(Color.foreground, 0.04)
                border.color: Util.alpha(Color.foreground, 0.12)
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
                    color: Color.accent
                  }
                  Text {
                    width: parent.width
                    wrapMode: Text.Wrap
                    color: Color.foreground
                    font.pixelSize: 13
                    lineHeight: 1.25
                    text: panel.selected && panel.selected.explanation ? panel.selected.explanation : "No additional explanation is available for this action."
                  }
                }
              }

              // Command & Dispatcher Card
              Column {
                width: parent.width
                spacing: 6

                Text {
                  text: "Command & Arguments"
                  font.pixelSize: 11
                  font.bold: true
                  color: Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: cmdText.implicitHeight + 16
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Color.foreground, 0.18)
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
                    color: Color.accent
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
                  color: Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: 34
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Color.foreground, 0.18)
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
                      color: panel.commandPath ? "#68b087" : (panel.selected && panel.selected.dispatcher === "exec" ? "#c46b6b" : Color.accent)
                    }

                    Text {
                      width: parent.width - 16
                      text: panel.commandPath ? panel.commandPath : (panel.selected && panel.selected.dispatcher === "exec" ? "Executable not found on PATH" : "Built-in compositor dispatcher")
                      font.family: Style.fontFamily
                      font.pixelSize: 11
                      color: panel.commandPath ? Color.menu.text : (panel.selected && panel.selected.dispatcher === "exec" ? Color.urgent : Color.muted)
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
      anchors.fill: parent; visible: panel.capturing; radius: card.radius; color: Color.menu.background
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
          var found = Model.capturedBindings(panel.rows, mask, key, event.nativeScanCode)
          if (found.length > 0) {
            panel.lastCaptured = found[0]
            panel.captureResult = found.map(function(r) { return r.combo + "  →  " + r.does }).join("\n")
            panel.selected = found[0]
          } else {
            panel.lastCaptured = null
            var chordLabel = Model.comboText(mask, key)
            panel.captureResult = (chordLabel ? chordLabel + "  →  " : "") + "No matching shortcut found"
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
              color: Color.menu.text
              font.pixelSize: 24
              font.bold: true
              anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
              height: 24
              width: captureStatusRow.implicitWidth + 16
              radius: 12
              color: inhibitor.active ? Util.alpha(Color.accent, 0.16) : Util.alpha(Color.menu.text, 0.08)
              border.color: inhibitor.active ? Util.alpha(Color.accent, 0.45) : Util.alpha(Color.menu.border, 0.8)
              border.width: 1
              anchors.verticalCenter: parent.verticalCenter
              Row {
                id: captureStatusRow
                anchors.centerIn: parent
                spacing: 6
                Rectangle {
                  width: 6; height: 6; radius: 3
                  color: inhibitor.active ? Color.accent : "#c46b6b"
                  anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                  text: inhibitor.active ? "Capture Active — Safe to test" : "Waiting for compositor capture"
                  color: inhibitor.active ? Color.accentText : Color.menu.text
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
          color: Color.foreground
          opacity: 0.75
          font.pixelSize: 13
          text: inhibitor.active
            ? (panel.lastCaptured ? "Found matching shortcut! Press any other combination to test again, or Esc to return to the list." : "Press any key combination on your keyboard. Shortcuts are intercepted and will not run the command.")
            : "Waiting for the compositor to grant shortcut capture. Press Esc to exit."
        }

        Item {
          width: parent.width
          height: parent.height - y - 10

          Rectangle {
            anchors.fill: parent
            visible: !panel.lastCaptured && !panel.captureResult
            radius: 8
            color: Util.alpha(Color.foreground, 0.02)
            border.color: Util.alpha(Color.foreground, 0.14)
            border.width: 1

            Column {
              anchors.centerIn: parent
              spacing: 16
              width: Math.min(parent.width - 80, 560)

              Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 64; height: 64; radius: 32
                color: Util.alpha(Color.accent, 0.15)
                border.color: Util.alpha(Color.accent, 0.4)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "⌨"
                  font.pixelSize: 28
                  color: Color.accent
                }
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Press any key combination"
                color: Color.foreground
                font.pixelSize: 18
                font.bold: true
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                color: Color.foreground
                opacity: 0.7
                font.pixelSize: 13
                lineHeight: 1.3
                text: "Press shortcuts like SUPER + RETURN, SUPER + K, ALT + TAB, or SUPER + BACKSPACE. The full details card will appear here instantly without executing the command."
              }
            }
          }

          Rectangle {
            anchors.fill: parent
            visible: !panel.lastCaptured && !!panel.captureResult
            radius: 8
            color: Util.alpha(Color.foreground, 0.02)
            border.color: Util.alpha(Color.urgent, 0.35)
            border.width: 1

            Column {
              anchors.centerIn: parent
              spacing: 16
              width: Math.min(parent.width - 80, 560)

              Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 64; height: 64; radius: 32
                color: Util.alpha(Color.urgent, 0.15)
                border.color: Util.alpha(Color.urgent, 0.4)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "✕"
                  font.pixelSize: 26
                  font.bold: true
                  color: Color.urgent
                }
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: panel.captureResult
                color: Color.foreground
                font.pixelSize: 17
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
              }

              Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                color: Color.foreground
                opacity: 0.7
                font.pixelSize: 13
                text: "This combination is not registered in your compositor configuration. Try another combination or press Esc to return to the list."
              }

              DarkButton {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Back to list  (Esc)"
                onClicked: panel.finishCapture()
              }
            }
          }

          Rectangle {
            anchors.fill: parent
            visible: !!panel.lastCaptured
            radius: 8
            color: Util.alpha(Color.foreground, 0.02)
            border.color: Util.alpha(Color.accent, 0.45)
            border.width: 1

            Column {
              anchors.fill: parent
              anchors.margins: 24
              spacing: 16

              Row {
                width: parent.width
                spacing: 10

                Rectangle {
                  height: 24
                  width: captureCatLabel.implicitWidth + 14
                  radius: 12
                  color: Util.alpha(Color.foreground, 0.08)
                  border.color: Util.alpha(Color.foreground, 0.22)
                  border.width: 1
                  anchors.verticalCenter: parent.verticalCenter
                  Text {
                    id: captureCatLabel
                    anchors.centerIn: parent
                    text: panel.lastCaptured ? (panel.lastCaptured.group || "Other") : ""
                    font.pixelSize: 11
                    font.bold: true
                    color: Color.foreground
                  }
                }

                Rectangle {
                  height: 24
                  width: captureDispLabel.implicitWidth + 14
                  radius: 12
                  color: Util.alpha(Color.accent, 0.15)
                  border.color: Util.alpha(Color.accent, 0.45)
                  border.width: 1
                  anchors.verticalCenter: parent.verticalCenter
                  Text {
                    id: captureDispLabel
                    anchors.centerIn: parent
                    text: panel.lastCaptured ? (panel.lastCaptured.dispatcher || "command") : ""
                    font.pixelSize: 11
                    font.bold: true
                    color: Color.accentText
                  }
                }

                Item {
                  width: Math.max(0, parent.width - captureCatLabel.implicitWidth - captureDispLabel.implicitWidth - captureChordsRow.implicitWidth - 70)
                  height: 1
                }

                Row {
                  id: captureChordsRow
                  spacing: 4
                  anchors.verticalCenter: parent.verticalCenter
                  Repeater {
                    model: panel.lastCaptured ? (panel.lastCaptured.chord || (panel.lastCaptured.combo ? panel.lastCaptured.combo.split(" + ") : [])) : []
                    Row {
                      spacing: 4
                      anchors.verticalCenter: parent.verticalCenter
                      Text {
                        visible: index > 0
                        text: "+"
                        color: Color.accentText
                        opacity: 0.7
                        font.pixelSize: 13
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                      }
                      Rectangle {
                        height: 28
                        width: Math.max(28, captureChordLabel.implicitWidth + 14)
                        radius: 4
                        color: Util.alpha(Color.accent, 0.25)
                        border.color: Color.accent
                        border.width: 1
                        anchors.verticalCenter: parent.verticalCenter
                        Text {
                          id: captureChordLabel
                          anchors.centerIn: parent
                          text: modelData
                          color: Color.accentText
                          font.pixelSize: 13
                          font.bold: true
                          font.family: Style.fontFamily
                        }
                      }
                    }
                  }
                }
              }

              Text {
                width: parent.width
                text: panel.lastCaptured ? panel.lastCaptured.does : ""
                color: Color.accentText
                font.bold: true
                font.pixelSize: 22
                wrapMode: Text.Wrap
              }

              Rectangle {
                width: parent.width
                height: captureExplCol.implicitHeight + 20
                radius: 6
                color: Util.alpha(Color.foreground, 0.04)
                border.color: Util.alpha(Color.foreground, 0.12)
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
                    color: Color.accent
                  }
                  Text {
                    width: parent.width
                    wrapMode: Text.Wrap
                    color: Color.foreground
                    font.pixelSize: 13
                    lineHeight: 1.25
                    text: panel.lastCaptured && panel.lastCaptured.explanation ? panel.lastCaptured.explanation : "No additional explanation is available for this action."
                  }
                }
              }

              Column {
                width: parent.width
                spacing: 6

                Text {
                  text: "Command & Arguments"
                  font.pixelSize: 11
                  font.bold: true
                  color: Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: captureCmdText.implicitHeight + 16
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Color.foreground, 0.18)
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
                    color: Color.accent
                    wrapMode: Text.WrapAnywhere
                  }
                }
              }

              Column {
                width: parent.width
                spacing: 6

                Text {
                  text: "Executable Path"
                  font.pixelSize: 11
                  font.bold: true
                  color: Color.accent
                }

                Rectangle {
                  width: parent.width
                  height: 34
                  radius: 6
                  color: "#0a0c0e"
                  border.color: Util.alpha(Color.foreground, 0.18)
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
                      color: panel.commandPath ? "#68b087" : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? "#c46b6b" : Color.accent)
                    }

                    Text {
                      width: parent.width - 20
                      text: panel.commandPath ? panel.commandPath : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? "Executable not found on PATH" : "Built-in compositor dispatcher")
                      font.family: Style.fontFamily
                      font.pixelSize: 11
                      color: panel.commandPath ? Color.foreground : (panel.lastCaptured && panel.lastCaptured.dispatcher === "exec" ? Color.urgent : Color.muted)
                      elide: Text.ElideMiddle
                      anchors.verticalCenter: parent.verticalCenter
                    }
                  }
                }
              }

              Item {
                width: parent.width
                height: 36
                anchors.topMargin: 4

                Row {
                  anchors.left: parent.left
                  anchors.verticalCenter: parent.verticalCenter
                  spacing: 6
                  Text {
                    text: "Try another key combination anytime, or press Esc to return to the list."
                    color: Color.foreground
                    opacity: 0.65
                    font.pixelSize: 12
                    anchors.verticalCenter: parent.verticalCenter
                  }
                }

                Row {
                  anchors.right: parent.right
                  anchors.verticalCenter: parent.verticalCenter
                  spacing: 10
                  DarkButton {
                    isAccent: true
                    text: "Inspect in list  (Enter)"
                    onClicked: panel.finishCapture()
                  }
                  DarkButton {
                    text: "Back to list  (Esc)"
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
}
