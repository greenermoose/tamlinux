// Desktop background for the Tamlinux host: the image the background link
// points at, drawn on every output, changing immediately.
// A double-click on the bare desktop opens the menu's background (left) or
// theme (right) route.
//
// Ported from omarchy 4.0.4 shell/plugins/background/Background.qml (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changes:
// the link is TAMLINUX_BACKGROUND_LINK and is watched, so any command that
// repoints it changes the background; the double-clicks run menu routes
// instead of Omarchy's switchers; themeTransition keeps its arguments but
// does not reload colours (the host palette is Tam.Commons); and the
// tamlinux-background layer namespace.

import Quickshell
import Tam.Commons
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import "components"

Item {
  id: root

  // The host's menu service, if it runs; the double-clicks open its routes.
  property var menu: null

  readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
  readonly property string currentBackgroundLink: Quickshell.env("TAMLINUX_BACKGROUND_LINK") || (root.stateHome + "/tamlinux/current/background")
  readonly property string linkDir: root.currentBackgroundLink.replace(/\/[^\/]*$/, "") || "/"
  readonly property string linkName: root.currentBackgroundLink.replace(/^.*\//, "")

  property string currentBackground: ""
  property string displayedBackground: ""

  function imageUrl(path) {
    if (!path) return ""
    return "file://" + String(path).split("/").map(encodeURIComponent).join("/")
  }

  function refreshBackground() {
    if (!readlinkProc.running) readlinkProc.running = true
  }

  function setBackground(path, instant) {
    transitionBackground("", path, path, instant, false)
  }

  function transitionBackground(fromPath, path, finalPath, instant, force) {
    path = String(path || "").trim()
    finalPath = String(finalPath || path).trim()
    if (!path || (!force && finalPath === currentBackground)) return
    currentBackground = finalPath
    displayedBackground = finalPath
  }

  function openRoute(route) {
    if (root.menu) root.menu.openRoute(route)
  }

  Process {
    environment: Util.hostEnvironment()
    id: readlinkProc
    command: ["readlink", "-f", root.currentBackgroundLink]
    stdout: StdioCollector {
      onStreamFinished: root.setBackground(String(text || "").trim(), false)
    }
  }

  // Commands that set the background repoint the link (ln -nsf renames a new
  // link over it), so a change shows without each one calling this service.
  Process {
    environment: Util.hostEnvironment()
    id: linkWatchProc
    command: ["setpriv", "--pdeathsig", "TERM", "inotifywait", "-mq", "-e", "create", "-e", "moved_to", "--format", "%f", root.linkDir]
    onExited: watchRestartTimer.restart()
    stdout: SplitParser {
      onRead: function(data) {
        if (String(data) === root.linkName) linkSettleTimer.restart()
      }
    }
  }

  // A burst of renames (a theme switch) settles before one read of the link.
  Timer {
    id: linkSettleTimer
    interval: 100
    repeat: false
    onTriggered: root.refreshBackground()
  }

  // The link's directory may not exist yet; try again, and read the link in
  // case it changed while nothing watched.
  Timer {
    id: watchRestartTimer
    interval: 5000
    repeat: false
    onTriggered: {
      if (!linkWatchProc.running) linkWatchProc.running = true
      root.refreshBackground()
    }
  }

  IpcHandler {
    target: "background"

    function refresh(): void {
      root.refreshBackground()
    }

    function set(path: string): void {
      root.setBackground(path, false)
    }

    function setInstant(path: string): void {
      root.setBackground(path, true)
    }

    function transition(fromPath: string, path: string): void {
      root.transitionBackground(fromPath, path, path, false, false)
    }

    function themeTransition(fromPath: string, path: string, finalPath: string, colorsB64: string, shellB64: string): void {
      root.transitionBackground(fromPath, path, finalPath, false, true)
    }

    function current(): string {
      return root.currentBackground
    }

    function ping(): string {
      return "ok"
    }
  }

  Component.onCompleted: {
    linkWatchProc.running = true
    refreshBackground()
  }

  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: panel
      required property var modelData

      screen: modelData
      visible: !remapGuard.remapping
      anchors { top: true; bottom: true; left: true; right: true }

      ScreenMoveRemap {
        id: remapGuard
        window: panel
      }
      color: "transparent"
      // Keep render updates enabled. The background layer has been observed to
      // lose its committed buffer while parked with updatesEnabled=false,
      // leaving a black desktop until the shell is restarted. The wallpaper
      // itself is static, so this favors correctness over a small render-loop
      // optimization.
      updatesEnabled: true

      WlrLayershell.namespace: "tamlinux-background"
      WlrLayershell.layer: WlrLayer.Background
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
      exclusionMode: ExclusionMode.Ignore

      Image {
        id: base
        anchors.fill: parent
        source: root.imageUrl(root.displayedBackground)
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true

      }

      MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onDoubleClicked: function(mouse) {
          root.openRoute(mouse.button === Qt.RightButton ? "theme" : "background")
          mouse.accepted = true
        }
      }
    }
  }
}
