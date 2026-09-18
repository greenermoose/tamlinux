.pragma library

var panels = ({})

function register(screenName, panel) {
  if (screenName && panel) {
    panels[screenName] = panel
  }
}

function unregister(screenName, panel) {
  if (screenName && panels[screenName] === panel) {
    delete panels[screenName]
  }
}

function getPanel(screenName) {
  if (screenName && panels[screenName]) return panels[screenName]
  return null
}

function resolveTargetPanel(monitorName, fallbackScreenName, hyprlandMonitors) {
  var mon = String(monitorName || "").trim().toLowerCase()
  if (mon) {
    // 1. Direct match on screenName (e.g. "hdmi-a-1", "dp-1", "dp-2")
    for (var key in panels) {
      if (key.toLowerCase() === mon || key.toLowerCase().indexOf(mon) !== -1) {
        return panels[key]
      }
    }

    // 2. Match by Hyprland monitor description/model (e.g. "hp", "dell", "msi")
    if (hyprlandMonitors) {
      var count = hyprlandMonitors.length || (typeof hyprlandMonitors.count === "number" ? hyprlandMonitors.count : 0)
      for (var i = 0; i < count; i++) {
        var hm = hyprlandMonitors[i] || (typeof hyprlandMonitors.get === "function" ? hyprlandMonitors.get(i) : null)
        if (!hm) continue
        var name = String(hm.name || "").toLowerCase()
        var desc = String(hm.description || "").toLowerCase()
        var model = String(hm.model || "").toLowerCase()
        if (name.indexOf(mon) !== -1 || desc.indexOf(mon) !== -1 || model.indexOf(mon) !== -1) {
          for (var pKey in panels) {
            if (pKey.toLowerCase() === name) return panels[pKey]
          }
        }
      }
    }
  }

  // If a panel is already open, target that one
  for (var k in panels) {
    if (panels[k] && panels[k].opened) return panels[k]
  }

  // Otherwise target fallback/focused monitor
  var fallback = String(fallbackScreenName || "").trim()
  if (fallback && panels[fallback]) return panels[fallback]

  // Fallback to any registered panel
  var keys = Object.keys(panels)
  if (keys.length > 0) return panels[keys[0]]

  return null
}

function toggle(monitorName, fallbackScreenName, hyprlandMonitors) {
  var p = resolveTargetPanel(monitorName, fallbackScreenName, hyprlandMonitors)
  if (p && typeof p.toggle === "function") p.toggle()
}

function open(monitorName, fallbackScreenName, hyprlandMonitors) {
  var p = resolveTargetPanel(monitorName, fallbackScreenName, hyprlandMonitors)
  if (p && typeof p.open === "function") p.open()
}

function close(monitorName, fallbackScreenName, hyprlandMonitors) {
  var p = resolveTargetPanel(monitorName, fallbackScreenName, hyprlandMonitors)
  if (p && typeof p.close === "function") p.close()
}

if (typeof module !== "undefined") {
  module.exports = {
    panels: panels,
    register: register,
    unregister: unregister,
    getPanel: getPanel,
    resolveTargetPanel: resolveTargetPanel,
    toggle: toggle,
    open: open,
    close: close
  }
}
