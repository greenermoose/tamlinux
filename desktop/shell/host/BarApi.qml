import QtQuick
import Quickshell
import Tam.Commons

// Per-output facade plugins treat as `bar`. One instance owns one bar window:
// its popout, its click targets, and its panel order. Lists that span outputs
// are answered by the shell.
QtObject {
  id: api

  property var host: null
  property var widget: null
  property var widgets: []
  property string hostKey: ""
  property var screen: null
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
  readonly property var compositor: shell ? shell.compositor : null

  function setCenterHoverRevealSuppressed(value) {
    centerHoverRevealSuppressed = !!value
  }

  function registerWidget(item) {
    if (!item || widgets.indexOf(item) !== -1) return
    var next = widgets.slice()
    next.push(item)
    widgets = next
    if (shell && shell.registerWidget) shell.registerWidget(hostKey, item)
  }

  function moduleWidgets(id) {
    if (shell && shell.moduleWidgets) return shell.moduleWidgets(id)
    var found = []
    for (var i = 0; i < widgets.length; i++) {
      if (widgets[i] && widgets[i].moduleName === id) found.push(widgets[i])
    }
    return found
  }

  function panelWidgets() {
    var found = []
    for (var i = 0; i < widgets.length; i++) {
      var item = widgets[i]
      if (item && item.open && item.close)
        found.push(item)
    }
    return found
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
    if (activePopout && activePopout !== owner && activePopout.close) {
      console.log("TAMLINUX_EVIDENCE popout-closed-previous host=" + hostKey)
      activePopout.close()
    }
    activePopout = owner
    console.log("TAMLINUX_EVIDENCE popout-owned host=" + hostKey)
  }

  function releasePopout(owner) {
    if (activePopout === owner) {
      activePopout = null
      console.log("TAMLINUX_EVIDENCE popout-released host=" + hostKey)
    }
  }

  function switchPanelFrom(owner, direction) {
    var panels = panelWidgets()
    if (!owner || panels.length < 2) return false
    var index = panels.indexOf(owner)
    if (index < 0) return false
    var step = direction < 0 ? -1 : 1
    var next = panels[(index + step + panels.length) % panels.length]
    if (!next || next === owner || typeof next.open !== "function") return false
    next.open()
    console.log("TAMLINUX_EVIDENCE panel-switched host=" + hostKey)
    return true
  }

  function targetWindow(target) {
    return target && target.QsWindow ? target.QsWindow.window : null
  }

  function targetBelongsToWindow(target, window) {
    return !!target && !!window && targetWindow(target) === window
  }

  function showTooltip(target, text) {
    if (host && host.showTooltip) host.showTooltip(target, text)
  }

  function hideTooltip(target) {
    if (host && host.hideTooltip) host.hideTooltip(target)
  }

  function clearSurface() {
    var count = clickTargets.length
    clickTargets = []
    if (activePopout) {
      activePopout = null
      console.log("TAMLINUX_EVIDENCE popout-cleared host=" + hostKey)
    }
    console.log("TAMLINUX_EVIDENCE targets-cleared host=" + hostKey + " count=" + count)
  }

  function run(command) {
    reportUnsupported(String(command || "run"))
  }

  function pickAgent() {
    recordAction("pick-agent")
  }

  function openTerminal(program) {
    if (String(program || "") === "btop") {
      recordAction("open-terminal btop")
      return true
    }
    reportUnsupported("open-terminal")
    return false
  }

  function notify(text) {
    var body = String(text === undefined || text === null ? "" : text)
    if (!plainNotice(body)) {
      reportUnsupported("notify")
      return false
    }
    recordAction("notify " + body.length)
    return true
  }

  function openTimezoneMenu() {
    recordAction("timezone-menu")
  }

  function plainNotice(body) {
    if (body.length < 1 || body.length > 512) return false
    for (var i = 0; i < body.length; i++) {
      var code = body.charCodeAt(i)
      if (code < 32 || code === 36 || code === 38 || code === 59 || code === 92 || code === 96 || code === 124)
        return false
    }
    return true
  }

  function recordAction(name) {
    console.log("TAMLINUX_EVIDENCE action-recorded " + name)
  }

  function reportUnsupported(action) {
    console.log("TAMLINUX_EVIDENCE unsupported " + String(action || "action"))
  }
}
