import QtQuick
import Tam.Commons

// Facade the clock treats as `bar`: presentation, popout ownership, click
// targets, tooltip hooks, and settings writes. Unsupported commands are
// reported and not executed.
QtObject {
  id: api

  property var host: null
  property var widget: null
  property string position: "bottom"
  property bool vertical: false
  property int barSize: Style.bar.sizeHorizontal
  property color foreground: Color.foreground
  property color barForeground: Color.foreground
  property color background: Color.background
  property color urgent: Color.urgent
  property string fontFamily: Style.font.family
  property bool foregroundAnimationEnabled: false
  property bool centerHoverRevealSuppressed: false
  property var activePopout: null
  property var clickTargets: []
  property var shell: null

  function setCenterHoverRevealSuppressed(value) {
    centerHoverRevealSuppressed = !!value
  }

  function moduleWidgets(id) {
    if (!widget) return []
    if (id === widget.moduleName || id === "fred.clock") return [widget]
    return []
  }

  function registerClickTarget(target) {
    if (!target || clickTargets.indexOf(target) !== -1) return
    var next = clickTargets.slice()
    next.push(target)
    clickTargets = next
  }

  function unregisterClickTarget(target) {
    clickTargets = clickTargets.filter(function(item) { return item !== target })
  }

  function requestPopout(owner) {
    if (activePopout && activePopout !== owner && activePopout.close)
      activePopout.close()
    activePopout = owner
    console.log("TAMLINUX_EVIDENCE popout-owned")
  }

  function releasePopout(owner) {
    if (activePopout === owner) {
      activePopout = null
      console.log("TAMLINUX_EVIDENCE popout-released")
    }
  }

  function switchPanelFrom(owner, direction) {
    return false
  }

  function targetBelongsToWindow(target, window) {
    return true
  }

  function showTooltip(target, text) {
    if (host && host.showTooltip) host.showTooltip(target, text)
  }

  function hideTooltip(target) {
    if (host && host.hideTooltip) host.hideTooltip(target)
  }

  function run(command) {
    reportUnsupported(String(command || "run"))
  }

  function reportUnsupported(action) {
    console.log("TAMLINUX_EVIDENCE unsupported " + String(action || "action"))
  }
}
