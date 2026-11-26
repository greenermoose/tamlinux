import QtQuick
import Quickshell
import "host" as Host
import "services/keybindings/KeybindingsModel.js" as KeybindingsModel

ShellRoot {
  id: root

  property var comp: Host.Compositor {}
  property var lastPointer: null
  property int pointerTokenSeen: -1
  property bool sawInitial: false
  property bool sawEventUpdate: false
  property bool sawActionsSent: false
  property bool sawReconnect: false
  property int ticks: 0

  readonly property string mode: Quickshell.env("TAMLINUX_ADAPTER_TEST_MODE") || "mock"

  function fail(msg) {
    console.log("TAMPANE_ADAPTER_FAILED " + msg)
    Qt.quit()
  }

  function findOutput(name) {
    var list = comp.outputs || []
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].name === name) return list[i]
    }
    return null
  }

  function findWorkspace(output, id) {
    var list = comp.workspaces || []
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].output === output && list[i].id === id) return list[i]
    }
    return null
  }

  Connections {
    target: root.comp
    function onPointerPositionReady(token, point) {
      root.pointerTokenSeen = token
      root.lastPointer = point
    }
  }

  Timer {
    interval: 50
    running: true
    repeat: true
    onTriggered: {
      root.ticks++
      if (root.ticks > 160) root.fail("timeout state=" + JSON.stringify({
        backend: root.comp.backendName,
        sawInitial: root.sawInitial,
        sawEventUpdate: root.sawEventUpdate,
        sawActionsSent: root.sawActionsSent,
        sawReconnect: root.sawReconnect,
        focusedOutput: root.comp.focusedOutputName,
        outputs: root.comp.outputs,
        keyboards: root.comp.keyboards,
        activeKeymap: root.comp.activeKeymap,
        pointer: root.lastPointer
      }))

      if (root.comp.backendName !== "tam-pane") root.fail("wrong backend " + root.comp.backendName)
      if (!root.comp.backend) return

      if (root.mode === "mock") {
        // Inject two-output ProtocolState fixtures so combine() is exercised too.
        if (root.ticks === 1 && root.comp.backend.protocolState) {
          var s1 = { name: "DP-1", x: 0, y: 0, width: 1920, height: 1080, model: "Primary" }
          var s2 = { name: "HDMI-A-1", x: 1920, y: 0, width: 1920, height: 1080, model: "Secondary" }
          var g1 = { screens: [s1] }
          var g2 = { screens: [s2] }
          var sets = []
          for (var t = 1; t <= 9; t++) {
            sets.push({ name: String(t), active: t === 1 || t === 3, urgent: false, canActivate: true, canDeactivate: true, projection: g1 })
            sets.push({ name: String(t), active: t === 2, urgent: false, canActivate: true, canDeactivate: true, projection: g2 })
          }
          root.comp.backend.protocolState.screens = [s1, s2]
          root.comp.backend.protocolState.windowsets = sets
          root.comp.backend.protocolState.refresh()
        }

        if (!root.sawInitial) {
          var dp1 = root.findOutput("DP-1")
          var hdmi = root.findOutput("HDMI-A-1")
          var ws1 = root.findWorkspace("DP-1", 1)
          var ws3 = root.findWorkspace("DP-1", 3)
          var binds = KeybindingsModel.parseBinds(root.comp.bindingsText)
          if (dp1 && hdmi && ws1 && ws3 && binds.length >= 2 && root.comp.keyboards.length === 1
              && root.comp.focusedOutputName === "DP-1"
              && dp1.activeWorkspaceIds && dp1.activeWorkspaceIds.length === 2
              && dp1.activeWorkspaceIds[0] === 1 && dp1.activeWorkspaceIds[1] === 3
              && ws1.occupied && ws3.occupied
              && ws1.windows.length === 1 && ws3.windows.length === 1
              && ws1.windows[0].className === "tam-last"
              && ws3.windows[0].className === "tam-last"
              && root.comp.activeKeymap === "English (US)") {
            root.sawInitial = true
            console.log("TAMPANE_STAGE_INITIAL_OK")
            // Trigger actions and pointer query.
            root.comp.requestPointerPosition(42)
            root.comp.toggleWorkspace(4, "DP-1")
            root.comp.focusOutput("HDMI-A-1")
            root.comp.setDpms("HDMI-A-1", false)
            root.comp.focusApp("tam-last")
            root.comp.switchKeyboardLayout("main-kbd")
          }
          return
        }

        if (!root.sawActionsSent) {
          if (root.pointerTokenSeen === 42 && root.lastPointer && root.lastPointer.x === 450 && root.lastPointer.y === 220) {
            root.sawActionsSent = true
            console.log("TAMPANE_STAGE_ACTIONS_OK")
          }
          return
        }

        if (!root.sawEventUpdate) {
          var hdmi2 = root.findOutput("HDMI-A-1")
          if (hdmi2 && hdmi2.focused && hdmi2.dpmsOn === false
              && root.comp.focusedOutputName === "HDMI-A-1"
              && root.comp.activeKeymap === "German"
              && root.comp.typedKeyboardName === "main-kbd") {
            // Update ProtocolState to reflect new active tags after reconnect test.
            root.sawEventUpdate = true
            console.log("TAMPANE_STAGE_EVENTS_OK")
          }
          return
        }

        if (!root.sawReconnect) {
          var dp1r = root.findOutput("DP-1")
          var hdmir = root.findOutput("HDMI-A-1")
          if (dp1r && hdmir && hdmir.dpmsOn === true && root.comp.focusedOutputName === "DP-1"
              && root.comp.activeKeymap === "French") {
            root.sawReconnect = true
            console.log("TAMPANE_ADAPTER_OK mock initial, multi-tag, actions, events, and reconnect")
            Qt.quit()
          }
          return
        }
      } else if (root.mode === "headless") {
        if (!root.sawInitial) {
          var h1 = root.findOutput("HEADLESS-1")
          var h2 = root.findOutput("HEADLESS-2")
          var bindsH = KeybindingsModel.parseBinds(root.comp.bindingsText)
          if (h1 && h2 && bindsH.length > 0 && root.comp.focusedOutputName !== "") {
            root.sawInitial = true
            root.comp.requestPointerPosition(7)
            root.comp.toggleWorkspace(2, "HEADLESS-1")
            root.comp.focusOutput("HEADLESS-2")
            root.comp.setDpms("HEADLESS-2", false)
          }
          return
        }
        var h1now = root.findOutput("HEADLESS-1")
        var h2now = root.findOutput("HEADLESS-2")
        if (root.pointerTokenSeen === 7 && root.lastPointer !== null
            && h1now && h1now.activeWorkspaceIds && h1now.activeWorkspaceIds.indexOf(1) !== -1
            && h1now.activeWorkspaceIds.indexOf(2) !== -1
            && h2now && h2now.focused && h2now.dpmsOn === false) {
          console.log("TAMPANE_ADAPTER_HEADLESS_OK two outputs, multi-tag, focus, dpms, cursor, binds")
          Qt.quit()
        }
      }
    }
  }
}
