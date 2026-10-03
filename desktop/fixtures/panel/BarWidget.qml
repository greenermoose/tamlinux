import QtQuick
import Tam.Ui

// Second bar widget for the host contract. It is not a fred.* plugin and it
// does not register an IPC target: the shell owns tamlinux-shell, and the
// clock owns the single tamlinux.clock target.
Panel {
  id: root

  moduleName: "tamlinux.fixture"
  ipcTarget: ""
  manageIpc: false
  property string hostKey: ""

  implicitWidth: 16
  implicitHeight: 16

  function publish(state) {
    console.log("TAMLINUX_EVIDENCE fixture host=" + hostKey + " " + state)
  }

  function bindHost() {
    if (bar) bar.registerClickTarget(hit)
    publish("loaded")
  }

  onOpenedChanged: {
    publish("opened=" + (opened ? "true" : "false"))
    if (!bar) return
    if (opened) {
      publish("panel-focus none")
      if (bar.requestPopout) bar.requestPopout(root)
    } else if (bar.releasePopout) {
      bar.releasePopout(root)
    }
  }

  MouseArea {
    id: hit
    anchors.fill: parent
    hoverEnabled: true
    onEntered: if (root.bar && root.bar.showTooltip) root.bar.showTooltip(hit, "fixture")
    onExited: if (root.bar && root.bar.hideTooltip) root.bar.hideTooltip(hit)
  }

  Component.onDestruction: {
    if (bar) bar.unregisterClickTarget(hit)
    publish("destroyed")
  }
}
