// Stay Awake and optional idle locking. See ../LICENSE-omarchy for attribution.

import QtQuick
import Quickshell
import Tam.Commons
import Quickshell.Io
import Quickshell.Wayland
import "IdleModel.js" as IdleModel

Item {
  id: root

  readonly property string home: Quickshell.env("HOME")
  readonly property string stayAwakeStatePath: {
    var configured = String(Quickshell.env("TAMLINUX_STAY_AWAKE_FILE") || "")
    if (configured.charAt(0) === "/" && configured.length > 1 && configured.charAt(configured.length - 1) !== "/") return configured
    return (Quickshell.env("XDG_STATE_HOME") || root.home + "/.local/state") + "/tamlinux/stay-awake"
  }
  readonly property string stayAwakeStateDir: stayAwakeStatePath.substring(0, stayAwakeStatePath.lastIndexOf("/")) || "/"
  readonly property int lockTimeoutSeconds: IdleModel.secondsFromConfig(Quickshell.env("TAMLINUX_IDLE_LOCK"))
  readonly property var plan: IdleModel.cyclePlan(lockTimeoutSeconds)
  readonly property int lockDelaySeconds: plan.lockDelay
  readonly property bool idleEnabled: stayAwakeStateLoaded && !stayAwake

  property bool stayAwake: false
  property bool stayAwakeStateLoaded: false
  property bool hasPendingStayAwakePersist: false
  property bool pendingStayAwakePersist: false
  property bool idledThisCycle: false
  property string lastEvent: "starting"
  property string lastEventAt: ""

  function nowIso() {
    return new Date().toISOString()
  }

  function logEvent(event, details) {
    var suffix = details === undefined || details === null || details === "" ? "" : ": " + String(details)
    root.lastEventAt = nowIso()
    root.lastEvent = event + suffix
    console.log("tamlinux idle " + root.lastEventAt + " " + root.lastEvent)
  }

  function runProcess(process, label, command) {
    if (process.running) {
      logEvent("process-skip", label + " already running")
      return false
    }
    logEvent("process-start", label + " " + command)
    process.command = ["bash", "-lc", 'exec "$@"', "bash", command]
    process.running = true
    return true
  }

  function lockSystem(reason) {
    logEvent("lock-system", reason || "requested")
    lockTimer.stop()
    root.idledThisCycle = false
    runProcess(lockProcess, "lock", "tam-system-lock")
  }

  function startIdleCycle() {
    if (root.idledThisCycle) {
      logEvent("idle-cycle-already-running")
      return
    }

    logEvent("idle-cycle-start", "lock=" + root.lockTimeoutSeconds)
    root.idledThisCycle = true

    if (root.lockDelaySeconds === 0) lockSystem("lock-timeout-immediate")
    else if (root.lockDelaySeconds > 0) lockTimer.restart()
  }

  function cancelIdleCycle(reason) {
    logEvent("idle-cycle-cancel", reason || "requested")
    lockTimer.stop()

    if (root.idledThisCycle) runProcess(wakeProcess, "wake", "tam-system-wake")

    root.idledThisCycle = false
  }

  function handleActiveSignal() {
    if (root.idledThisCycle) cancelIdleCycle("activity")
  }

  function handleIdleChanged() {
    logEvent("idle-monitor", idleMonitor.isIdle ? "idle" : "active")
    if (!root.idleEnabled || !root.plan.enabled) return

    if (idleMonitor.isIdle) startIdleCycle()
    else handleActiveSignal()
  }

  function statusJson() {
    return JSON.stringify({
      enabled: root.idleEnabled,
      stayAwake: root.stayAwake,
      stayAwakeStateLoaded: root.stayAwakeStateLoaded,
      stayAwakeStatePath: root.stayAwakeStatePath,
      cycle: root.plan.enabled,
      idle: idleMonitor.isIdle,
      inIdleCycle: root.idledThisCycle,
      lock: root.lockTimeoutSeconds,
      lockDelay: root.lockDelaySeconds,
      timers: {
        lock: lockTimer.running
      },
      processes: {
        lock: lockProcess.running,
        wake: wakeProcess.running
      },
      lastEvent: root.lastEvent,
      lastEventAt: root.lastEventAt
    })
  }

  function persistStayAwake(value) {
    if (stayAwakeStateWriter.running) {
      root.pendingStayAwakePersist = !!value
      root.hasPendingStayAwakePersist = true
      return
    }

    stayAwakeStateWriter.command = ["env", "TAMLINUX_STAY_AWAKE_FILE=" + root.stayAwakeStatePath,
      "tam-toggle-idle", value ? "stay-awake" : "allow-idle"]
    stayAwakeStateWriter.running = true
  }

  function refreshStayAwakeState() {
    if (!stayAwakeStateProbe.running) stayAwakeStateProbe.running = true
  }

  function applyStayAwake(value, persist, reason) {
    var enabled = !!value
    var changed = !root.stayAwakeStateLoaded || root.stayAwake !== enabled

    if (persist) persistStayAwake(enabled)

    root.stayAwake = enabled
    root.stayAwakeStateLoaded = true

    if (!changed) return enabled ? "disabled" : "enabled"

    logEvent("stay-awake", (enabled ? "enabled" : "disabled") + (reason ? " " + reason : ""))
    if (enabled) cancelIdleCycle("stay-awake")
    else Qt.callLater(root.handleIdleChanged)

    return enabled ? "disabled" : "enabled"
  }

  function setIdleEnabled(value) {
    return applyStayAwake(!value, true, "ipc")
  }

  IdleMonitor {
    id: idleMonitor
    enabled: root.idleEnabled && root.plan.enabled
    timeout: Math.max(1, root.plan.first)
    respectInhibitors: true
    onIsIdleChanged: root.handleIdleChanged()
  }

  Timer {
    id: lockTimer
    interval: Math.max(0, root.lockDelaySeconds) * 1000
    repeat: false
    onTriggered: if (root.idleEnabled && root.idledThisCycle) root.lockSystem("lock-timeout")
  }

  Process {
    environment: Util.hostEnvironment()
    id: lockProcess
    onExited: function(exitCode, exitStatus) { root.logEvent("process-exit", "lock exitCode=" + exitCode + " status=" + exitStatus) }
  }
  Process {
    environment: Util.hostEnvironment()
    id: wakeProcess
    onExited: function(exitCode, exitStatus) { root.logEvent("process-exit", "wake exitCode=" + exitCode + " status=" + exitStatus) }
  }

  Process {
    environment: Util.hostEnvironment()
    id: stayAwakeStateProbe
    command: ["bash", "-c", 'mkdir -p -- "$1"; if [[ -f $2 ]]; then echo yes; else echo no; fi', "bash", root.stayAwakeStateDir, root.stayAwakeStatePath]
    stdout: SplitParser {
      onRead: function(line) { root.applyStayAwake(String(line).trim() === "yes", false, "state-file") }
    }
    onExited: function() { stayAwakeStateDirWatcher.reload() }
  }

  Process {
    environment: Util.hostEnvironment()
    id: stayAwakeStateWriter
    onExited: function() {
      if (root.hasPendingStayAwakePersist) {
        var pending = root.pendingStayAwakePersist
        root.hasPendingStayAwakePersist = false
        root.persistStayAwake(pending)
        return
      }

      root.refreshStayAwakeState()
    }
  }

  FileView {
    id: stayAwakeStateDirWatcher
    path: root.stayAwakeStateDir
    watchChanges: true
    printErrors: false
    onFileChanged: root.refreshStayAwakeState()
  }

  Component.onCompleted: {
    logEvent("service-ready", root.plan.enabled ? "cycle lock=" + root.lockTimeoutSeconds : "cycle off")
    refreshStayAwakeState()
  }

  IpcHandler {
    target: "idle"

    function status(): string {
      return root.statusJson()
    }

    function debug(): string {
      return root.statusJson()
    }

    function enable(): string {
      return root.setIdleEnabled(true)
    }

    function disable(): string {
      return root.setIdleEnabled(false)
    }

    function toggle(): string {
      return root.setIdleEnabled(!root.idleEnabled)
    }

    function ping(): string {
      return "pong"
    }
  }
}
