// Reminder card for the Tamlinux host: type the minutes, Enter, then an
// optional message, Enter. reminder.sh beside this file sets the timer.
//
// Ported from omarchy 4.0.4 shell/plugins/reminders/ReminderFlow.qml (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changes:
// Tam.Commons and Tam.Ui; the reminder helper lives beside this file; the
// IPC target reminders; and the tamlinux-reminders layer namespace.

import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import Tam.Commons
import Tam.Ui
import "ReminderFlowModel.js" as ReminderFlowModel

Item {
  id: root

  readonly property string serviceDir: Quickshell.shellDir + "/services/reminders"
  property string reminderScript: root.serviceDir + "/reminder.sh"

  property bool opened: false
  property string step: "minutes"
  property string minutes: ""
  property string filterText: ""
  property string fontFamily: Style.font.family

  property color background: Color.menu.background
  property color foreground: Color.menu.text
  property color border: Color.menu.border
  property var borderSpec: Border.flat(border, Math.max(1, Style.space(2)))
  property color scrim: Color.menu.scrim
  readonly property int cornerRadius: Style.cornerRadius
  property int contentMargin: Style.space(18)
  property int headingSize: Style.fontPx(16 / 12)
  property int headerHeight: Math.max(Style.space(34), Style.font.title + Style.spacing.controlPaddingY * 2)
  property int cardWidth: Math.min(Style.space(300), panel.width - Style.gapsOut * 2)
  property int cardHeight: Math.min(contentMargin * 2 + headerHeight, panel.height - Style.gapsOut * 2)
  readonly property string promptText: root.step === "message" ? "Reminder message" : "Remind in minutes"

  function open(payloadJson) {
    root.opened = true
    root.step = "minutes"
    root.minutes = ""
    root.filterText = ""

    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function close() {
    root.opened = false
  }

  function toggle() {
    if (root.opened) root.close()
    else root.open("{}")
  }

  // Backspace, Ctrl+Backspace, and Ctrl+U edit a non-empty entry.
  function editsFilter(event, text) {
    if (!text) return false
    if (event.modifiers & (Qt.AltModifier | Qt.MetaModifier)) return false
    if (event.key === Qt.Key_U)
      return event.modifiers === Qt.ControlModifier
    return event.key === Qt.Key_Backspace
  }

  function editedFilter(event, text) {
    if (event.key === Qt.Key_U) return ""
    if (event.modifiers & Qt.ControlModifier)
      return text.replace(/\s+$/, "").replace(/\S+$/, "")
    return text.slice(0, -1)
  }

  function setFilter(nextFilter) {
    root.filterText = nextFilter
  }

  function submit() {
    var selection = root.filterText

    if (root.step === "minutes") {
      var nextMinutes = ReminderFlowModel.validMinutes(selection)

      if (!selection.trim()) {
        root.close()
        return
      }

      if (!nextMinutes) {
        Quickshell.execDetached([root.reminderScript, "toast", "Invalid reminder", "Enter the number of minutes"])
        return
      }

      root.minutes = nextMinutes
      root.step = "message"
      root.filterText = ""
      Qt.callLater(function() { keyCatcher.forceActiveFocus() })
      return
    }

    if (root.step === "message") {
      var args = [root.reminderScript].concat(ReminderFlowModel.reminderArgs(root.minutes, selection))
      root.close()
      Quickshell.execDetached(args)
    }
  }

  IpcHandler {
    target: "reminders"
    function toggle(): void { root.toggle() }
    function open(): void { root.open("{}") }
    function close(): void { root.close() }
    function ping(): string { return "pong" }
  }

  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "tamlinux-reminders"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore

    Rectangle {
      anchors.fill: parent
      color: root.scrim
    }

    MouseArea {
      anchors.fill: parent
      onClicked: root.close()
    }

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      radius: root.cornerRadius
      anchors.centerIn: parent
      color: root.background
      borderSpec: root.borderSpec
      padding: root.contentMargin

      MouseArea { anchors.fill: parent; onClicked: {} }

      Item {
        id: keyCatcher
        anchors.fill: parent
        focus: true

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) {
            if (root.filterText) root.setFilter("")
            else root.close()
            event.accepted = true
          } else if (root.editsFilter(event, root.filterText)) {
            root.setFilter(root.editedFilter(event, root.filterText))
            event.accepted = true
          } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.submit()
            event.accepted = true
          } else if (event.text && event.text.length === 1 && event.text.charCodeAt(0) >= 32 && event.text.charCodeAt(0) !== 127) {
            root.setFilter(root.filterText + event.text)
            event.accepted = true
          }
        }
      }

      Item {
        anchors.fill: parent
        anchors.topMargin: card.contentTopInset
        anchors.rightMargin: card.contentRightInset
        anchors.bottomMargin: card.contentBottomInset
        anchors.leftMargin: card.contentLeftInset

        Text {
          textFormat: Text.PlainText
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          text: root.filterText || (root.promptText + "...")
          color: root.foreground
          opacity: root.filterText ? 1 : 0.58
          font.family: root.fontFamily
          font.pixelSize: root.headingSize
          elide: Text.ElideRight
        }
      }
    }
  }
}
