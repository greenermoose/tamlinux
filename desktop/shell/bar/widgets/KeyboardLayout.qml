// Ported from omarchy 4.0.4 shell/plugins/bar/widgets/KeyboardLayout.qml
// (MIT, Copyright (c) David Heinemeier Hansson; see ../../services/LICENSE-omarchy).
// Changes: owned module, id, and command names; the keyboards, the layout
// switch, and its events come from the compositor facade (bar.compositor)
// instead of Hyprland directly.

import QtQuick
import Quickshell
import Quickshell.Io
import Tam.Ui
import Tam.Commons
import "KeyboardLayoutModel.js" as KeyboardLayoutModel

BarWidget {
  id: root
  moduleName: "tamlinux.keyboard-layout"


  property string layoutFull: ""
  // The keyboard the last reading spoke for, which is the one a click switches,
  // and separately the one activelayout named as being typed on. A reading
  // confirms the first is really there, so the click has a keyboard to reach
  // from the first reading onwards rather than only after a switch, and stops
  // naming one that has been unplugged.
  property string keyboardName: ""
  property string typedKeyboardName: ""
  // Keyboards on the seat, buttons and virtual ones excluded, and whether the
  // last reading left that shape in doubt.
  property int keyboardCount: 0
  property bool keyboardUnresolved: false
  // Nothing to read or switch on the single-layout install most people run, so
  // the widget ships on the bar and stays out of the way until there are two.
  // An older Hyprland that doesn't report the list keeps showing the label.
  property bool multipleLayouts: true
  // Short language code per layout description ("English (US)": "en"), read from
  // xkb's own table rather than maintained by hand.
  property var layoutBriefs: ({})
  readonly property string layoutLabel: KeyboardLayoutModel.shortLabel(layoutFull, layoutBriefs)

  readonly property var compositor: root.bar ? root.bar.compositor : null

  function refresh() {
    if (root.compositor) root.compositor.refreshKeyboards()
  }

  // Keyboards someone can actually type on, which is not everything the
  // compositor calls a keyboard.
  function typedKeyboards(keyboards) {
    return keyboards.filter(k => KeyboardLayoutModel.isTypedKeyboard(k.name))
  }

  // The main flag names no keyboard for long: fcitx5 takes it with the virtual
  // keyboard it binds to inject, which leaves no typed keyboard holding it and
  // nothing to read at all, and once that unbinds it lands on whichever device
  // the compositor saw last, a power button included. Go by layout progress
  // instead, and by the keyboard the last switch named.
  function selectKeyboard(typed) {
    return KeyboardLayoutModel.selectKeyboard(typed, root.compositor ? root.compositor.typedKeyboardName : "")
  }

  // The facade's records in the shape KeyboardLayoutModel reads.
  function modelKeyboards(list) {
    return (list || []).map(function(k) {
      return { name: k.name, layout: k.layout === null ? undefined : k.layout, active_keymap: k.activeKeymap, active_layout_index: k.activeLayoutIndex }
    })
  }

  // Each facade reading replaces the last. An empty one is either a seat with
  // no keyboards or a read that failed; both leave the shape in doubt.
  function ingest() {
    var listed = root.compositor ? root.modelKeyboards(root.compositor.keyboards) : []
    var typed = root.typedKeyboards(listed)
    var kb = root.selectKeyboard(typed)
    if (!kb || !kb.active_keymap) {
      root.keyboardUnresolved = true
      if (typed.length === 0) {
        root.layoutFull = ""
        root.keyboardName = ""
      }
      return
    }

    root.keyboardUnresolved = false
    root.keyboardCount = typed.length
    root.keyboardName = String(kb.name || "")
    root.multipleLayouts = kb.layout === undefined || String(kb.layout).indexOf(",") !== -1
    root.layoutFull = kb.active_keymap
  }

  // It switches the keyboard the last reading spoke for, so a click always
  // advances the device the label is describing. Switching the seat together
  // would reach the typed keyboard without having to name it, but it would also
  // carry the buttons along, and the whole read depends on those staying where
  // they started: once a button has been advanced too, a toggle that wraps the
  // keyboard back to the first layout leaves the button reading as the furthest
  // along, and the label follows the button.
  function cycleLayout() {
    if (!root.keyboardName || !root.compositor) return
    root.compositor.switchKeyboardLayout(root.keyboardName)
    refreshTimer.restart()
  }

  Component.onCompleted: {
    briefsProc.running = true
    ingest()
  }

  // The compositor adapter reads the devices again on every layout switch and
  // reload, and when asked; each reading lands here.
  Connections {
    target: root.compositor
    function onKeyboardsChanged() { root.ingest() }
    function onTypedKeyboardNameChanged() { root.ingest() }
  }

  // The table only changes when xkb data is upgraded, so read it at startup and
  // leave it alone. The bar is built per monitor, so this runs once per widget.
  // The exotic rulesets cover layouts like trans (IPA) that ship in the same xkb
  // package and set just as well, so load them or those labels lose their code.
  Process {
    id: briefsProc
    command: ["xkbcli", "list", "--load-exotic"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.layoutBriefs = KeyboardLayoutModel.layoutBriefs(text)
    }
  }

  Timer {
    id: refreshTimer
    interval: 600
    onTriggered: root.refresh()
  }

  // Which keyboard on a crowded seat the label is describing can change without
  // the compositor announcing it, since a device arriving or leaving raises no event
  // of its own, and that can only be learned by asking. Poll while there is that
  // ambiguity, until a first reading lands so a query that failed at login still
  // recovers, and while a reading has left the seat's shape in doubt. The
  // one-keyboard install has none of those, and is left alone rather than
  // asking forever for an answer that cannot change.
  Timer {
    interval: 10000
    running: !root.keyboardName || root.keyboardUnresolved || root.keyboardCount > 1
    repeat: true
    onTriggered: root.refresh()
  }

  visible: layoutLabel !== "" && multipleLayouts
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.layoutLabel
    fontSize: Style.font.caption
    horizontalMargin: 6
    tooltipText: root.layoutFull
    onPressed: function() { root.cycleLayout() }
  }
}
