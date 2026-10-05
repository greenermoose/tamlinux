// Desktop background for the Tamlinux host: the image the background link
// points at, drawn on every output, with a slanted reveal when it changes.
// A double-click on the bare desktop opens the menu's background (left) or
// theme (right) route.
//
// Vendored from omarchy 4.0.4 shell/plugins/background/Background.qml (MIT,
// Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changes:
// the link is TAMLINUX_BACKGROUND_LINK and is watched, so any command that
// repoints it changes the background; the double-clicks run menu routes
// instead of Omarchy's switchers; themeTransition keeps its arguments but
// does not reload colours (the host palette is Tam.Commons); and the
// tamlinux-background layer namespace.

import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import "components"

Item {
  id: root

  // The host's menu service, if it runs; the double-clicks open its routes.
  property var menu: null

  readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")
  readonly property string currentBackgroundLink: Quickshell.env("TAMLINUX_BACKGROUND_LINK") || (root.stateHome + "/tamlinux/background")
  readonly property string linkDir: root.currentBackgroundLink.replace(/\/[^\/]*$/, "") || "/"
  readonly property string linkName: root.currentBackgroundLink.replace(/^.*\//, "")

  property string currentBackground: ""
  property string displayedBackground: ""
  property string incomingBackground: ""
  property string oldBackground: ""
  property bool finishingTransition: false
  property int backgroundVersion: 0
  property int revealStartedVersion: -1
  property real revealProgress: 1

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
    fromPath = String(fromPath || "").trim()
    if (!path || (!force && finalPath === currentBackground)) return
    currentBackground = finalPath
    backgroundVersion += 1
    revealStartedVersion = -1

    revealAnimation.stop()
    finishingTransition = false

    if (instant || !displayedBackground) {
      oldBackground = ""
      incomingBackground = ""
      displayedBackground = path
      revealProgress = 1
      return
    }

    oldBackground = fromPath || displayedBackground
    incomingBackground = path
    revealProgress = 0
  }

  function startReveal(panel) {
    if (!incomingBackground) return
    panel.maskReady = true
    if (revealStartedVersion === backgroundVersion) return
    revealStartedVersion = backgroundVersion
    revealAnimation.restart()
  }

  function openRoute(route) {
    if (root.menu) root.menu.openRoute(route)
  }

  Process {
    id: readlinkProc
    command: ["readlink", "-f", root.currentBackgroundLink]
    stdout: StdioCollector {
      onStreamFinished: root.setBackground(String(text || "").trim(), false)
    }
  }

  // Commands that set the background repoint the link (ln -nsf renames a new
  // link over it), so a change shows without each one calling this service.
  Process {
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

  NumberAnimation {
    id: revealAnimation
    target: root
    property: "revealProgress"
    from: 0
    to: 1
    duration: 420
    easing.type: Easing.InOutCubic
    onFinished: {
      if (root.incomingBackground) {
        root.displayedBackground = root.currentBackground || root.incomingBackground
        root.finishingTransition = true
      }
      root.revealProgress = 1
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

      property bool maskReady: false

      function maybeStartReveal() {
        if (!root.incomingBackground || root.revealProgress !== 0 || maskReady) return
        if (incomingFrame.status !== Image.Ready) return
        Qt.callLater(function() {
          if (!root.incomingBackground || root.revealProgress !== 0 || maskReady) return
          if (incomingFrame.status !== Image.Ready) return
          root.startReveal(panel)
        })
      }

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
        onStatusChanged: {
          if (status === Image.Ready && root.finishingTransition) {
            root.incomingBackground = ""
            root.oldBackground = ""
            root.finishingTransition = false
          }
        }
      }

      Image {
        id: oldFrame
        anchors.fill: parent
        source: root.imageUrl(root.oldBackground)
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: false
        smooth: true
        mipmap: true
        visible: root.oldBackground !== "" && root.revealProgress < 1
        onStatusChanged: panel.maybeStartReveal()
      }

      Item {
        id: incomingLayer
        anchors.fill: parent
        visible: root.incomingBackground !== "" && incomingFrame.status === Image.Ready && (root.revealProgress >= 1 || panel.maskReady)
        layer.enabled: root.incomingBackground !== "" && root.revealProgress < 1
        layer.smooth: true
        layer.effect: MultiEffect {
          maskEnabled: true
          maskSource: revealMask
          maskThresholdMin: 0.5
          maskSpreadAtMin: 0.02
        }

        Image {
          id: incomingFrame
          anchors.fill: parent
          source: root.imageUrl(root.incomingBackground)
          fillMode: Image.PreserveAspectCrop
          asynchronous: true
          cache: false
          smooth: true
          mipmap: true
          onStatusChanged: panel.maybeStartReveal()
        }
      }

      Item {
        id: revealMask
        anchors.fill: parent
        visible: false
        layer.enabled: true

        readonly property real slant: -0.18
        readonly property real centerTop: width / 2 - slant * height / 2
        readonly property real centerBottom: width / 2 + slant * height / 2
        readonly property real reach: width / 2 + Math.abs(slant) * height / 2 + 4
        readonly property real spread: reach * root.revealProgress

        Shape {
          anchors.fill: parent
          antialiasing: true
          preferredRendererType: Shape.CurveRenderer
          ShapePath {
            fillColor: "white"
            strokeColor: "transparent"
            startX: revealMask.centerTop - revealMask.spread; startY: 0
            PathLine { x: revealMask.centerTop + revealMask.spread; y: 0 }
            PathLine { x: revealMask.centerBottom + revealMask.spread; y: revealMask.height }
            PathLine { x: revealMask.centerBottom - revealMask.spread; y: revealMask.height }
            PathLine { x: revealMask.centerTop - revealMask.spread; y: 0 }
          }
        }
      }

      Connections {
        target: root
        function onIncomingBackgroundChanged() {
          panel.maskReady = false
          panel.maybeStartReveal()
        }
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
