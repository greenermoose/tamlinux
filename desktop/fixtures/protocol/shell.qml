import QtQuick
import Quickshell
import "host" as Host
import "host/protocol_model.js" as Model

ShellRoot {
  id: test
  property int step: 0
  property int calls: 0
  property var one: QtObject {
    property string name: "DP-1"
    property int x: 0
    property int y: 0
    property int width: 1920
    property int height: 1080
    property string model: "First"
  }
  property var two: QtObject {
    property string name: "HDMI-A-1"
    property int x: 1920
    property int y: 0
    property int width: 1920
    property int height: 1080
    property string model: "Second"
  }
  property var group: QtObject { property var screens: [test.one] }
  property var otherGroup: QtObject { property var screens: [test.two] }
  property var first: QtObject {
    property string id: "opaque-identifier"
    property string name: "1"
    property bool active: true
    property bool urgent: false
    property bool canActivate: false
    property bool canSetProjection: false
    property var projection: test.group
    function activate() { test.calls++ }
  }
  property var second: QtObject {
    property string id: "another-opaque-identifier"
    property string name: "2"
    property bool active: false
    property bool urgent: false
    property bool canActivate: true
    property bool canSetProjection: false
    property var projection: test.group
    function activate() { test.calls++ }
  }
  property var third: QtObject {
    property string id: "opaque-three"
    property string name: "3"
    property bool active: true
    property bool urgent: false
    property bool canActivate: false
    property bool canSetProjection: false
    property var projection: test.otherGroup
    function activate() { test.calls++ }
  }
  property var protocol: Host.ProtocolState { windowsets: []; screens: [] }

  function check(ok, message) {
    if (!ok) throw new Error("PROTOCOL_FIXTURE_FAILED " + message)
  }
  function runStep() {
    var facts = protocol.snapshot
    if (step === 0) {
      check(!facts.ready && facts.workspaces.length === 0, "initially empty")
      protocol.screens = [one, two]
      protocol.windowsets = [first, second, third]
    } else if (step === 1) {
      check(facts.ready && facts.workspaces.length === 3, "late population")
      check(facts.workspaces[0].id === 1 && facts.workspaces[1].output === "DP-1", "opaque id and group")
      check(facts.outputs[0].activeWorkspaceId === 1 && facts.outputs[1].activeWorkspaceId === 3, "per-output active")
      check(protocol.activate(1) && calls === 0, "already active without capability")
      check(protocol.activate(2) && calls === 1, "inactive with capability")
      check(!protocol.activate(11) && !protocol.activate("x"), "invalid activation")
      check(!protocol.assign(2, "DP-1") && !protocol.assign(2, "bad name"), "assignment capability")
      second.urgent = true
      second.canActivate = false
      one.x = -1920
    } else if (step === 2) {
      check(facts.workspaces[1].urgent && !facts.workspaces[1].canActivate, "nested urgency/capability update")
      check(!protocol.activate(2) && calls === 1, "no unadvertised activation")
      check(facts.outputs[0].x === -1920, "geometry update")
      second.projection = otherGroup
    } else if (step === 3) {
      check(facts.workspaces[1].output === "HDMI-A-1", "workspace move between groups")
      group.screens = [two]
      third.active = false
    } else if (step === 4) {
      check(facts.ready && facts.workspaces[0].output === "HDMI-A-1", "nested projection screens update")
      check(facts.outputs[0].activeWorkspaceId === 0 && facts.outputs[1].activeWorkspaceId === 1, "active changes")
      protocol.screens = [one]
    } else if (step === 5) {
      check(!facts.ready && facts.outputs.length === 1 && facts.workspaces[0].output === "", "hotplug removal")
      protocol.screens = [one, two]
    } else if (step === 6) {
      check(facts.ready && facts.workspaces[0].output === "HDMI-A-1", "hotplug return")
      var ipc = { outputs: [{ name: "HDMI-A-1", x: 1920, y: 0, activeWorkspaceId: 1, dpmsOn: false },
        { name: "DP-1", x: -1920, y: 0, activeWorkspaceId: 0 }],
        workspaces: [{ id: 3, output: "HDMI-A-1" }, { id: 2, output: "HDMI-A-1", occupied: true,
          windows: [{ title: "Window" }] }, { id: 1, output: "HDMI-A-1" }],
        focusedOutputName: "HDMI-A-1", focusedWorkspaceId: 1, bindingsText: "bindings", activeKeymap: "English" }
      check(Model.compare(facts, ipc).equal, "normalized equality")
      var combined = Model.combine(facts, ipc)
      check(combined.focusedWorkspaceId === 1 && combined.outputs[1].dpmsOn === false, "IPC-only gaps")
      check(combined.workspaces[1].occupied && combined.workspaces[1].windows.length === 1, "window gap")
      ipc.workspaces[0].output = "DP-1"
      check(!Model.compare(facts, ipc).equal, "difference detected")
      check(Model.combine({ ready: false }, ipc) === ipc, "initial fallback")
      check(Model.workspaceNumber(true) === 0 && Model.workspaceNumber("01") === 0, "invalid number")
      check(!Model.validName("DP-1\n") && !Model.validName("a".repeat(65)), "output bounds")
      check(Model.position(Infinity) === 0 && Model.position(200000) === 100000, "geometry bounds")
      var duplicate = Model.snapshot([first, first], [one, two])
      check(!duplicate.ready && duplicate.problems.indexOf("duplicate-workspace") >= 0, "duplicate names")
      var many = []; for (var i = 0; i < 65; i++) many.push(first)
      check(!Model.snapshot(many, [one, two]).ready, "list cap")
      group.screens = [one, two]
    } else if (step === 7) {
      check(!facts.ready && facts.workspaces[0].output === "", "ambiguous projection rejected")
      group.screens = [two]
      first.active = false
      second.active = true
    } else if (step === 8) {
      check(facts.ready && facts.outputs[1].activeWorkspaceId === 2, "active workspace changed")
      console.log("PROTOCOL_FIXTURE_OK reactive snapshots, capabilities, merge, comparison and bounds")
      Qt.quit()
    }
    step++
  }
  Timer {
    interval: 30; running: true; repeat: true
    onTriggered: {
      try { test.runStep() }
      catch (error) { console.log(String(error)); Qt.quit() }
    }
  }
}
