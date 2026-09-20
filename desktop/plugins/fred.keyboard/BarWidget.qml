import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons
import "Model.js" as Model
import "Device.js" as Device
import "LayoutResolver.js" as Resolver
import "KeyboardModel.js" as KM
import "Bindings.js" as Bindings

// fred.keyboard - keyboard shortcut explorer.
//
// Bar icon (nf-md-keyboard) with a tooltip naming the attached keyboard;
// clicking opens a panel that draws the board.
//
// Key capture is panel-scoped: keys are read through QML handlers only while
// this panel holds keyboard focus. Nothing typed in any other window is
// visible here, and no /dev/input node is ever opened. Capture mode
// (CaptureMode.qml) additionally suspends Hyprland's keybind matching for
// this window while it is focused, so bound combinations can be inspected
// rather than executed. It is off by default and switched on in the panel.
Panel {
  id: root
  moduleName: "fred.keyboard"

  // The bar widget is instantiated once per screen, so the base Panel's
  // automatic IpcHandler would register the same target several times and
  // only one would win. Per-monitor IPC (openMonitor/closeMonitor/
  // toggleMonitor, per the develop-new-plugin SOP) needs a single owner and
  // is deferred to a later milestone. Agents must not open this panel
  // programmatically in any case: it takes keyboard focus, which is per-seat
  // rather than per-monitor, so it would seize Fred's keyboard.
  ipcTarget: ""
  manageIpc: false

  // The bar sizes a widget from its implicit size. The base Panel is a plain
  // Item with none, so without this the widget loads, reports enabled, and
  // renders at zero width - present in listPlugins but invisible in the bar.
  // BarIconButton derives its own implicit size from Style.bar.iconSlot, so
  // taking it here is not circular despite the button filling this item.
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  readonly property string pluginVersion: "0.2.2"

  // Closed environment: only these names reach a child process.
  readonly property var keyboardEnv: ["HOME", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY",
                                      "HYPRLAND_INSTANCE_SIGNATURE"]

  property var device: null           // primary physical keyboard
  property string keymap: ""          // e.g. "English (US)"
  property var layout: null           // resolved layout object
  property var resolution: null       // how that layout was chosen
  property var registry: null         // layouts/index.json
  property var pressed: ({})          // evdev codes currently down
  property var lastPressed: ({})      // the set at the most recent key press
  property string lastMouse: ""       // Hyprland mouse key of the most recent click, or ""
  readonly property var byCode: KM.byCode(root.layout)
  readonly property var byId: KM.byId(root.layout)
  readonly property string lastCombo: root.lastMouse !== ""
    ? Bindings.mouseLabel(root.lastPressed, root.lastMouse)
    : Bindings.comboLabel(root.lastPressed, root.byCode)

  // Hyprland binds, joined to the resolved layout.
  property var binds: []
  readonly property var bindIndex: Bindings.indexBinds(root.binds, root.byId)
  readonly property var boundCounts: Bindings.boundCounts(root.bindIndex)
  readonly property var lastBinds: root.lastMouse !== ""
    ? Bindings.lookupMouse(root.bindIndex, root.lastPressed, root.lastMouse)
    : Bindings.lookup(root.bindIndex, root.lastPressed)
  readonly property bool lastHasKey: {
    if (root.lastMouse !== "") return true
    for (var k in root.lastPressed)
      if (root.lastPressed[k] && !Bindings.isModifier(Number(k))) return true
    return false
  }
  // Binds whose key this keyboard cannot send, as "chord - what it does"
  // rows sorted by chord. Inherited laptop keys, mostly.
  readonly property var orphanRows: {
    var o = root.bindIndex.orphans || []
    var rows = []
    for (var i = 0; i < o.length; i++)
      rows.push({ chord: Bindings.bindLabel(o[i], root.byId, root.byCode),
                  does: Bindings.describe(o[i]) })
    rows.sort(function (a, b) { return a.chord < b.chord ? -1 : a.chord > b.chord ? 1 : 0 })
    return rows
  }
  property bool orphansExpanded: false
  property bool capsOn: false         // real hardware LED state
  property bool numOn: false
  readonly property var ledState: ({ capslock: root.capsOn, numlock: root.numOn })
  readonly property var ledPaths: Device.ledPaths(root.device)
  property var osGeometryFiles: []    // filenames in the XKB geometry dir
  property string loadError: ""

  readonly property string deviceSummary:
    loadError !== "" ? loadError : Device.summary(device, keymap)

  // --- Layout resolution -------------------------------------------------

  // Generic pc101/pc104/jp106 style names are variants *inside* the single
  // `pc` geometry file; vendor boards are standalone files. Both count as
  // available, but they are discovered differently.
  readonly property var pcVariants: {
    if (!registry || !registry.osGeometries) return []
    var g = registry.osGeometries
    return (g.preferred || []).concat(g.regional || [])
  }

  function osHas(name) {
    if (osGeometryFiles.indexOf(name) >= 0) return true
    return pcVariants.indexOf(name) >= 0 && osGeometryFiles.indexOf("pc") >= 0
  }

  function resolveLayout() {
    if (!registry || !device) return
    root.resolution = Resolver.resolve(device, registry, root.osHas)
    if (root.resolution.file)
      layoutFile.path = Model.helperPath("layouts/" + root.resolution.file)
  }

  // --- Files -------------------------------------------------------------

  property FileView registryFile: FileView {
    path: Model.helperPath("layouts/index.json")
    printErrors: false
    onLoaded: {
      try {
        root.registry = JSON.parse(text())
        root.resolveLayout()
      } catch (e) { root.loadError = "Layout registry unreadable" }
    }
    onLoadFailed: root.loadError = "Layout registry missing"
  }

  property FileView layoutFile: FileView {
    printErrors: false
    onLoaded: {
      try {
        root.layout = JSON.parse(text())
        root.loadError = ""
      } catch (e) { root.loadError = "Layout file unreadable" }
    }
    onLoadFailed: root.loadError = "Layout file missing"
  }

  property FileView procDevices: FileView {
    path: "/proc/bus/input/devices"
    printErrors: false
    onLoaded: {
      root.device = Device.primaryKeyboard(Device.parseProcDevices(text()))
      root.resolveLayout()
    }
    onLoadFailed: root.loadError = "Cannot read input devices"
  }

  // Caps/Num Lock come from sysfs, which reports the actual lamp on the
  // keyboard. No privileges, no /dev/input, no keystroke observation.
  property FileView capsLed: FileView {
    path: root.ledPaths ? root.ledPaths.caps : ""
    printErrors: false
    onLoaded: root.capsOn = Device.ledOn(text())
    onLoadFailed: root.capsOn = false
  }

  property FileView numLed: FileView {
    path: root.ledPaths ? root.ledPaths.num : ""
    printErrors: false
    onLoaded: root.numOn = Device.ledOn(text())
    onLoadFailed: root.numOn = false
  }

  function refreshLeds() {
    if (!root.ledPaths) return
    capsLed.reload()
    numLed.reload()
  }

  // sysfs attributes do not reliably emit inotify events, so the LEDs are
  // polled rather than watched - but only while the panel is open, so a
  // closed panel costs nothing.
  Timer {
    running: root.opened && root.ledPaths !== null
    interval: 500
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refreshLeds()
  }

  // --- Processes ---------------------------------------------------------

  Launch {
    id: hyprctlProc
    exe: "/usr/bin/hyprctl"
    args: ["-j", "devices"]
    envKeys: root.keyboardEnv
    deadlineMs: 4000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.keymap = Device.activeKeymap(String(text || ""))
    }
  }

  // Plain `ls` with arguments, never a shell: a login shell would source the
  // user's profile and defeat the closed environment above.
  // The text form, not -j: on Hyprland 0.56.2 the JSON drops the key of every
  // `code:N` bind. Bindings.parseBinds bounds and validates the input.
  Launch {
    id: bindsProc
    exe: "/usr/bin/hyprctl"
    args: ["binds"]
    envKeys: root.keyboardEnv
    deadlineMs: 4000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.binds = Bindings.parseBinds(String(text || ""))
    }
  }

  Launch {
    id: geometryProc
    exe: "/usr/bin/ls"
    args: ["/usr/share/X11/xkb/geometry"]
    envKeys: root.keyboardEnv
    deadlineMs: 4000
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.osGeometryFiles = String(text || "").split("\n")
          .map(function (s) { return s.trim() })
          .filter(function (s) { return s !== "" })
        root.resolveLayout()
      }
    }
  }

  Component.onCompleted: {
    hyprctlProc.launch()
    geometryProc.launch()
  }

  // --- Bar icon ----------------------------------------------------------

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "󰌌"
    tooltipText: "Keyboard\n" + root.deviceSummary +
                 "\n\nfred.keyboard v" + root.pluginVersion
    onPressed: function (b) { root.toggle() }
  }

  // --- Panel -------------------------------------------------------------

  // A clone of the stock KeyboardPanel that does not close when another
  // monitor is clicked (UPSTREAM.md).
  ExplorerPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: captureArea
    contentWidth: panel.fittedContentWidth(Style.space(1000))
    contentHeight: panel.fittedContentHeight(panelColumn.implicitHeight, Style.space(800))

    // Panel-scoped capture. A plain focused Item rather than PanelKeyCatcher:
    // that component takes keys before its descendants for menu navigation,
    // which is the opposite of what a key inspector needs.
    Item {
      id: captureArea
      anchors.fill: parent
      focus: true

      // Escape is the way out of capture mode first, and out of the panel
      // second: one press restores the system's shortcuts, the next closes.
      // While capture is on, Escape is also recorded like any other key, so
      // the readout shows what ended the mode; with it off the panel is
      // closing, and there is nothing left to show it on.
      Keys.onPressed: function (event) {
        event.accepted = true
        var escape = event.key === Qt.Key_Escape
        if (escape && !capture.wanted) { root.close(); return }
        var code = Bindings.evdevFromNative(event.nativeScanCode)
        if (code !== null) {
          var next = Object.assign({}, root.pressed)
          next[code] = true
          root.pressed = next
          if (!event.isAutoRepeat) { root.lastPressed = next; root.lastMouse = "" }
        }
        if (escape) capture.wanted = false
      }

      Keys.onReleased: function (event) {
        var code = Bindings.evdevFromNative(event.nativeScanCode)
        var next = Object.assign({}, root.pressed)
        if (code !== null) delete next[code]
        root.pressed = next
        root.refreshLeds()   // a Caps/Num press changes the lamp on release
        event.accepted = true
      }

      // Records a mouse action the way the key handler records a chord.
      function recordMouse(key) {
        if (!key) return
        root.lastPressed = Object.assign({}, root.pressed)
        root.lastMouse = key
      }

      Column {
        id: panelColumn
        width: parent.width
        spacing: Style.spacing.sm

        PanelSectionHeader {
          width: parent.width
          text: root.device ? Device.summary(root.device, root.keymap) : "Keyboard"
        }

        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.65)
          text: {
            if (root.loadError !== "") return root.loadError
            if (!root.resolution) return "Resolving layout..."
            if (root.resolution.kind === "field-observed")
              return "Layout: " + root.resolution.layoutId + " - transcribed for this board"
            return "Layout: " + root.resolution.layoutId + " - stand-in, " + root.resolution.why
          }
        }

        KeyboardView {
          id: board
          layout: root.layout
          pressed: root.pressed
          bindings: root.boundCounts
          ledState: root.ledState
          unit: Math.max(Style.space(20),
                         Math.min(Style.space(38),
                                  (panelColumn.width - Style.space(6)) /
                                  Math.max(1, board.boardUnits)))
        }

        Text {
          width: parent.width
          elide: Text.ElideRight
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          color: Color.foreground
          text: root.lastCombo === "" ? "Press a key or combination."
                                      : "Pressed: " + root.lastCombo
        }

        // What the chord does. Only a chord with a non-modifier key can be
        // bound; modifiers alone say nothing rather than "not bound".
        Text {
          width: parent.width
          visible: root.lastHasKey
          wrapMode: Text.WordWrap
          font.family: Style.font.family
          font.pixelSize: Style.font.body
          color: root.lastBinds.length > 0 ? Color.accent
                 : Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.65)
          text: {
            if (root.binds.length === 0) return "Binds not loaded."
            if (root.lastBinds.length === 0) return "Not bound in Hyprland."
            var parts = []
            for (var i = 0; i < root.lastBinds.length; i++)
              parts.push(Bindings.describe(root.lastBinds[i]))
            return "Runs: " + parts.join("; ")
          }
        }

        CaptureMode {
          id: capture
          width: parent.width
          window: panel
          // The toggle row is clicked with the pointer; keep the keys with
          // the capture area either way so the very next chord is seen.
          onWantedChanged: captureArea.forceActiveFocus()
        }

        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.55)
          text: "Keys light up on the board while this panel has focus; tinted keys " +
                "have Hyprland binds. With capture mode off, bound combinations run " +
                "their command and never arrive here; with it on, keys and mouse " +
                "actions arrive here and do not run. A key marked with a small " +
                "circle (Fn) never reaches the OS at all. Escape closes."
        }

        // Binds this keyboard cannot send. Collapsed to one line; the list is
        // for the occasional audit, not the everyday glance.
        OrphanBinds {
          width: parent.width
          rows: root.orphanRows
          total: root.binds.length
          expanded: root.orphansExpanded
          onToggled: root.orphansExpanded = !root.orphansExpanded
        }
      }

      // Mouse capture. While the mode is on this surface covers the whole
      // card, so every click and wheel step inside the panel is recorded
      // rather than acted on - including on the toggle, which is why Escape
      // is the way out. Hyprland's inhibitor already keeps the compositor
      // from claiming Super+click first (KeybindManager::onMouseEvent goes
      // through the same inhibited path as keys). Off, the surface is
      // disabled and invisible to the pointer, and the controls work.
      MouseArea {
        anchors.fill: parent
        enabled: capture.wanted
        visible: capture.wanted
        acceptedButtons: Qt.AllButtons
        preventStealing: true
        onPressed: function (mouse) {
          captureArea.recordMouse(Bindings.mouseButtonKey(mouse.button))
          mouse.accepted = true
        }
        onWheel: function (wheel) {
          captureArea.recordMouse(Bindings.wheelKey(wheel.angleDelta.x, wheel.angleDelta.y))
          wheel.accepted = true
        }
      }
    }
  }

  onOpenedChanged: {
    if (opened) {
      procDevices.reload()
      hyprctlProc.launch()
      bindsProc.launch()   // binds change with the config; re-read per open
    } else {
      // Closing must never leave the inhibitor wanted: the next open would
      // otherwise silently pause the system's shortcuts again.
      capture.wanted = false
      root.pressed = ({})
      root.lastPressed = ({})
      root.lastMouse = ""
      root.orphansExpanded = false
    }
  }
}
