// Start is a view of existing menu rows, never a second copy of user actions.
function defaultsFor(defaults, userItems) {
  if (!userItems.some(function(entry) { return entry.id === "quicklaunch" })) return defaults
  return defaults.filter(function(entry) { return entry.id.indexOf("quicklaunch.") !== 0 })
}

function rows(model, items, order, when, checked, query) {
  var result = [], groups = [[], []]
  var settings = ["style.theme", "style.text-size", "style.background", "style.bar.position"]
  var labels = ["Color Palette…", "Text Size…", "Background…", "Bar Position"]
  for (var i = 0; i < order.length; i++) {
    var entry = items[order[i]]
    if (!entry || entry.parent !== "quicklaunch") continue
    if (!model.isVisible(items, order, when, entry)) continue
    if (query && !model.matchesQuery(entry, query, true)) continue
    groups[0].push(model.displayRow(items, order, checked, entry, "", 0, "Quick Launch"))
  }
  for (var s = 0; s < settings.length; s++) {
    var source = items[settings[s]]
    if (!source || !model.isVisible(items, order, when, source)) continue
    var display = Object.assign({}, source, {label: labels[s]})
    if (query && !model.matchesQuery(display, query, true)) continue
    var row = model.displayRow(items, order, checked, display, "", 0, "Settings")
    groups[1].push(row)
  }
  for (var g = 0; g < groups.length; g++) {
    var previousPower = false
    for (var n = 0; n < groups[g].length; n++) {
      var next = groups[g][n]
      var power = /^quicklaunch\.(suspend|hibernate|logout|reboot|shutdown|lock)$/.test(next.itemId)
      next.separatorBefore = g === 0 && n > 0 && power && !previousPower
      previousPower = power
      result.push(next)
    }
  }
  return result
}

function screenAt(screens, x, y) {
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null
  for (var i = 0; i < screens.length; i++) {
    var s = screens[i]
    if (x >= s.x && y >= s.y && x < s.x + s.width && y < s.y + s.height) return s
  }
  return null
}

function placement(width, height, cardWidth, cardHeight, anchor, gap) {
  var x = anchor ? anchor.x : (width - cardWidth) / 2
  var y = anchor ? anchor.y : (height - cardHeight) / 2
  if (anchor && anchor.edge === "bottom") y -= cardHeight
  else if (anchor && y + cardHeight > height - gap) y -= cardHeight
  return {x: Math.max(gap, Math.min(x, width - cardWidth - gap)),
    y: Math.max(gap, Math.min(y, height - cardHeight - gap))}
}

if (typeof module !== "undefined") module.exports = {defaultsFor: defaultsFor, rows: rows, screenAt: screenAt, placement: placement}
