import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons
import "Model.js" as Model
import "Device.js" as Device
import "LayoutResolver.js" as Resolver

// fred.keyboard - keyboard shortcut explorer.
//
// Bar icon (nf-md-keyboard) with a tooltip naming the attached keyboard;
// clicking opens a panel that draws the board.
//
// Key capture is panel-scoped: keys are read through QML handlers only while
// this panel holds keyboard focus. Nothing typed in any other window is
// visible here, and no /dev/input node is ever opened. Capture mode - which
// suspends Hyprland's keybind matching so bound combinations can be inspected
// rather than executed - is a later milestone, so for now bound combinations
// still run their command instead of reaching this panel.
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

  readonly property string pluginVersion: "0.1.0"

  // Closed environment: only these names reach a child process.
  readonly property var keyboardEnv: ["HOME", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY",
                                      "HYPRLAND_INSTANCE_SIGNATURE"]

  property var device: null           // primary physical keyboard
  property string keymap: ""          // e.g. "English (US)"
  property var layout: null           // resolved layout object
  property var resolution: null       // how that layout was chosen
  property var registry: null         // layouts/index.json
  property var pressed: ({})          // evdev codes currently down
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

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: captureArea
    contentWidth: panel.fittedContentWidth(Style.space(1000))
    contentHeight: panel.fittedContentHeight(panelColumn.implicitHeight, Style.space(560))

    // Panel-scoped capture. A plain focused Item rather than PanelKeyCatcher:
    // that component takes keys before its descendants for menu navigation,
    // which is the opposite of what a key inspector needs.
    Item {
      id: captureArea
      anchors.fill: parent
      focus: true

      Keys.onPressed: function (event) {
        if (event.key === Qt.Key_Escape) { root.close(); event.accepted = true; return }
        var next = Object.assign({}, root.pressed)
        next[event.nativeScanCode - 8] = true   // X11 keycode -> evdev
        root.pressed = next
        event.accepted = true
      }

      Keys.onReleased: function (event) {
        var next = Object.assign({}, root.pressed)
        delete next[event.nativeScanCode - 8]
        root.pressed = next
        root.refreshLeds()   // a Caps/Num press changes the lamp on release
        event.accepted = true
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
          ledState: root.ledState
          unit: Math.max(Style.space(20),
                         Math.min(Style.space(38),
                                  (panelColumn.width - Style.space(6)) /
                                  Math.max(1, board.boardUnits)))
        }

        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          font.family: Style.font.family
          font.pixelSize: Style.font.caption
          color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.55)
          text: "Press a key to light it up. Bound combinations such as Super+K are " +
                "still claimed by Hyprland and will not reach this panel yet - capture " +
                "mode, which suspends that, is the next milestone. A key marked with a " +
                "small circle (Fn) never reaches the OS at all. Escape closes."
        }
      }
    }
  }

  onOpenedChanged: {
    if (opened) {
      procDevices.reload()
      hyprctlProc.launch()
    } else {
      root.pressed = ({})
    }
  }
}
