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

    // 2. Match on registered panel screen properties
    for (var pKey in panels) {
      var p = panels[pKey]
      if (p) {
        var win = p.anchorItem && p.anchorItem.QsWindow ? p.anchorItem.QsWindow.window : null
        var scr = (win && win.screen) ? win.screen : (p.bar && p.bar.screen ? p.bar.screen : null)
        if (scr) {
          var sModel = String(scr.model || "").toLowerCase()
          var sName = String(scr.name || "").toLowerCase()
          var sMake = String(scr.manufacturer || "").toLowerCase()
          if (sModel.indexOf(mon) !== -1 || sName.indexOf(mon) !== -1 || sMake.indexOf(mon) !== -1) {
            return p
          }
        }
      }
    }

    // 3. Match by Hyprland monitor description/model
    if (hyprlandMonitors) {
      var list = Array.isArray(hyprlandMonitors) ? hyprlandMonitors : (hyprlandMonitors.values || [])
      var count = list.length || (typeof hyprlandMonitors.count === "number" ? hyprlandMonitors.count : 0)
      for (var i = 0; i < count; i++) {
        var hm = list[i] || (typeof hyprlandMonitors.get === "function" ? hyprlandMonitors.get(i) : null)
        if (!hm) continue
        var name = String(hm.name || "").toLowerCase()
        var desc = String(hm.description || "").toLowerCase()
        var model = String(hm.model || "").toLowerCase()
        var mfr = String(hm.manufacturer || "").toLowerCase()
        if (name.indexOf(mon) !== -1 || desc.indexOf(mon) !== -1 || model.indexOf(mon) !== -1 || mfr.indexOf(mon) !== -1) {
          for (var pk in panels) {
            if (pk.toLowerCase() === name) return panels[pk]
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

function refreshAll(sourcePanel) {
  var called = 0
  for (var key in panels) {
    var p = panels[key]
    if (p && typeof p.refresh === "function") {
      p.refresh()
      called++
    }
  }
  if (called === 0 && sourcePanel && typeof sourcePanel.refresh === "function") {
    sourcePanel.refresh()
    called++
  }
  return called
}

function broadcastReport(sourceScreen, payload, updatedAt) {
  var count = 0
  for (var key in panels) {
    if (key !== sourceScreen && panels[key] && typeof panels[key].applyReport === "function") {
      panels[key].applyReport(payload, updatedAt)
      count++
    }
  }
  return count
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
    close: close,
    refreshAll: refreshAll,
    broadcastReport: broadcastReport
  }
}
