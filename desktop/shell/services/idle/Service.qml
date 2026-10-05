// Idle service for the Tamlinux host: the Stay Awake switch, and an optional
// idle cycle that starts the screensaver and then the lock when the session
// has been idle long enough.
//
// Ported from omarchy 4.0.4 shell/plugins/services/idle/Service.qml (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changes:
// - The timeouts come from TAMLINUX_IDLE_SCREENSAVER and TAMLINUX_IDLE_LOCK
//   (seconds). Unset or 0 turns that stage off, and with both off there is no
//   idle cycle (the source read 0 as at once and had default timeouts).
// - Stay Awake is the file TAMLINUX_STAY_AWAKE_FILE (an absolute path;
//   default ~/.local/state/tamlinux/stay-awake). Anything that suspends on
//   idle should skip suspending while it exists. It is written by argument,
//   never as shell text.
// - Screensaver windows are counted from Wayland toplevels (app id
//   org.tamlinux.screensaver), so no compositor event stream is read.
// - The stages run tam-launch-screensaver, tam-system-lock, and
//   tam-system-wake. The original's locked-session check before the
//   screensaver is left to the lock command, which ends the screensaver.
// - IPC target idle adds ping.

import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "IdleModel.js" as IdleModel

Item {
  id: root

  readonly property string home: Quickshell.env("HOME")
  readonly property string stayAwakeStatePath: {
    var configured = String(Quickshell.env("TAMLINUX_STAY_AWAKE_FILE") || "")
    if (configured.charAt(0) === "/" && configured.length > 1 && configured.charAt(configured.length - 1) !== "/") return configured
    return root.home + "/.local/state/tamlinux/stay-awake"
  }
  readonly property string stayAwakeStateDir: stayAwakeStatePath.substring(0, stayAwakeStatePath.lastIndexOf("/")) || "/"
  readonly property int screensaverTimeoutSeconds: IdleModel.secondsFromConfig(Quickshell.env("TAMLINUX_IDLE_SCREENSAVER"))
  readonly property int lockTimeoutSeconds: IdleModel.secondsFromConfig(Quickshell.env("TAMLINUX_IDLE_LOCK"))
  readonly property var plan: IdleModel.cyclePlan(screensaverTimeoutSeconds, lockTimeoutSeconds)
  readonly property int screensaverDelaySeconds: plan.screensaverDelay
  readonly property int lockDelaySeconds: plan.lockDelay
  readonly property bool idleEnabled: stayAwakeStateLoaded && !stayAwake
  readonly property string screensaverClass: "org.tamlinux.screensaver"

  property bool stayAwake: false
  property bool stayAwakeStateLoaded: false
  property bool hasPendingStayAwakePersist: false
  property bool pendingStayAwakePersist: false
  property bool idledThisCycle: false
  property bool screensaverStartedThisCycle: false
  property string lastEvent: "starting"
  property string lastEventAt: ""
  property int screensaverWindowCount: 0

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

  function launchScreensaver() {
    root.screensaverStartedThisCycle = true
    screensaverLaunchGraceTimer.restart()
    runProcess(screensaverProcess, "screensaver", "tam-launch-screensaver")
  }

  function lockSystem(reason) {
    logEvent("lock-system", reason || "requested")
    screensaverTimer.stop()
    lockTimer.stop()
    screensaverLaunchGraceTimer.stop()
    root.idledThisCycle = false
    root.screensaverStartedThisCycle = false
    runProcess(lockProcess, "lock", "tam-system-lock")
  }

  function startIdleCycle() {
    if (root.idledThisCycle) {
      logEvent("idle-cycle-already-running")
      return
    }

    logEvent("idle-cycle-start", "screensaver=" + root.screensaverTimeoutSeconds + " lock=" + root.lockTimeoutSeconds)
    root.idledThisCycle = true
    root.screensaverStartedThisCycle = false

    if (root.screensaverDelaySeconds === 0) launchScreensaver()
    else if (root.screensaverDelaySeconds > 0) screensaverTimer.restart()

    if (root.lockDelaySeconds === 0) lockSystem("lock-timeout-immediate")
    else if (root.lockDelaySeconds > 0) lockTimer.restart()
  }

  function cancelIdleCycle(reason) {
    logEvent("idle-cycle-cancel", reason || "requested")
    screensaverTimer.stop()
    lockTimer.stop()
    screensaverLaunchGraceTimer.stop()

    if (root.idledThisCycle) runProcess(wakeProcess, "wake", "tam-system-wake")

    root.idledThisCycle = false
    root.screensaverStartedThisCycle = false
  }

  function refreshScreensaverWindows() {
    var appIds = []
    var toplevels = ToplevelManager.toplevels ? ToplevelManager.toplevels.values : []
    for (var i = 0; i < toplevels.length; i++) appIds.push(toplevels[i] ? toplevels[i].appId : "")
    var before = root.screensaverWindowCount
    root.screensaverWindowCount = IdleModel.screensaverWindowCount(appIds, root.screensaverClass)
    if (root.screensaverWindowCount > before) handleScreensaverWindowOpened()
    else if (root.screensaverWindowCount < before) handleScreensaverWindowClosed()
  }

  function handleScreensaverWindowOpened() {
    screensaverLaunchGraceTimer.stop()
  }

  function handleScreensaverWindowClosed() {
    if (!root.idleEnabled || !root.idledThisCycle || !root.screensaverStartedThisCycle) return
    if (root.screensaverWindowCount > 0) return

    // The user dismissed the screensaver before the lock deadline. Treat that
    // as activity and cancel the pending lock; the lock timer is only allowed
    // to fire while the screensaver remains up.
    root.cancelIdleCycle("screensaver-dismissed")
  }

  function handleActiveSignal() {
    if (!root.idledThisCycle) return

    // Starting the screensaver can make the compositor report activity. Keep
    // the lock timer running once the screensaver exists (or during its short
    // launch grace); its window closing cancels the cycle if it exits before
    // the normal lock deadline.
    if (root.screensaverStartedThisCycle && (root.screensaverWindowCount > 0 || screensaverLaunchGraceTimer.running)) {
      logEvent("idle-monitor-active", "screensaver cycle remains armed")
      return
    }

    cancelIdleCycle("activity")
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
      screensaverStarted: root.screensaverStartedThisCycle,
      screensaver: root.screensaverTimeoutSeconds,
      lock: root.lockTimeoutSeconds,
      screensaverDelay: root.screensaverDelaySeconds,
      lockDelay: root.lockDelaySeconds,
      screensaverWindows: root.screensaverWindowCount,
      timers: {
        screensaver: screensaverTimer.running,
        lock: lockTimer.running,
        screensaverLaunchGrace: screensaverLaunchGraceTimer.running
      },
      processes: {
        screensaver: screensaverProcess.running,
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

    stayAwakeStateWriter.command = value
      ? ["bash", "-c", 'mkdir -p -- "$1" && touch -- "$2"', "bash", root.stayAwakeStateDir, root.stayAwakeStatePath]
      : ["rm", "-f", "--", root.stayAwakeStatePath]
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
    id: screensaverTimer
    interval: Math.max(0, root.screensaverDelaySeconds) * 1000
    repeat: false
    onTriggered: root.launchScreensaver()
  }

  Timer {
    id: lockTimer
    interval: Math.max(0, root.lockDelaySeconds) * 1000
    repeat: false
    onTriggered: if (root.idleEnabled && root.idledThisCycle) root.lockSystem("lock-timeout")
  }

  Timer {
    id: screensaverLaunchGraceTimer
    interval: 3000
    repeat: false
    onTriggered: {
      if (root.idleEnabled && root.idledThisCycle && root.screensaverStartedThisCycle && root.screensaverWindowCount === 0 && !idleMonitor.isIdle) {
        root.cancelIdleCycle("screensaver-not-running")
      }
    }
  }

  Connections {
    target: ToplevelManager.toplevels
    function onValuesChanged() { root.refreshScreensaverWindows() }
  }

  Process {
    id: screensaverProcess
    onExited: function(exitCode, exitStatus) { root.logEvent("process-exit", "screensaver exitCode=" + exitCode + " status=" + exitStatus) }
  }
  Process {
    id: lockProcess
    onExited: function(exitCode, exitStatus) { root.logEvent("process-exit", "lock exitCode=" + exitCode + " status=" + exitStatus) }
  }
  Process {
    id: wakeProcess
    onExited: function(exitCode, exitStatus) { root.logEvent("process-exit", "wake exitCode=" + exitCode + " status=" + exitStatus) }
  }

  Process {
    id: stayAwakeStateProbe
    command: ["bash", "-c", 'mkdir -p -- "$1"; if [[ -f $2 ]]; then echo yes; else echo no; fi', "bash", root.stayAwakeStateDir, root.stayAwakeStatePath]
    stdout: SplitParser {
      onRead: function(line) { root.applyStayAwake(String(line).trim() === "yes", false, "state-file") }
    }
    onExited: function() { stayAwakeStateDirWatcher.reload() }
  }

  Process {
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
    logEvent("service-ready", root.plan.enabled ? "cycle screensaver=" + root.screensaverTimeoutSeconds + " lock=" + root.lockTimeoutSeconds : "cycle off")
    refreshScreensaverWindows()
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
