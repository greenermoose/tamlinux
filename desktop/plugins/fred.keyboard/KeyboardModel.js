.pragma library

// Helpers over a keyboard layout. Holds no layout data itself: boards live in
// `layouts/*.json` so they can be shared, reviewed and contributed by others,
// and LayoutResolver.js decides which one applies to the attached device.
//
// Layout shape (see layouts/README for the full contract):
//
//   { schemaVersion, id, name, mainBlockWidth, rows: [[cell, ...], ...],
//     firmwareLocal: [id], declaredButAbsent: [id] }
//
//   cell: { id, label, code, w?, h?, gap?, led? }
//     code  Linux evdev keycode, or null when the key emits nothing to the OS
//           (a firmware-local key such as Fn). At runtime QML reports
//           `KeyEvent.nativeScanCode`, which is this value + 8; that
//           conversion lives in Bindings.js so the code spaces never mix here.
//     w     keycap widths, default 1
//     h     rows spanned, default 1. A cell with h:2 also occupies the row
//           below, which therefore does not re-declare it.
//     gap   blank space in keycap units BEFORE the cell
//     led   indicator name; an LED is drawn, never pressed

function allCells(layout) {
  var out = []
  if (!layout || !layout.rows) return out
  for (var r = 0; r < layout.rows.length; r++)
    for (var c = 0; c < layout.rows[r].length; c++)
      out.push(layout.rows[r][c])
  return out
}

// evdev code -> cell, for highlighting a pressed key. Cells with no code
// (firmware-local) and LED indicators are excluded: they can never light up.
function byCode(layout) {
  var map = {}
  var cells = allCells(layout)
  for (var i = 0; i < cells.length; i++) {
    var c = cells[i]
    if (c.led) continue
    if (c.code === null || c.code === undefined) continue
    map[c.code] = c
    for (var j = 0; j < (c.actions || []).length; j++)
      map[c.actions[j].code] = c.actions[j]
  }
  return map
}

function byId(layout) {
  var map = {}
  var cells = allCells(layout)
  for (var i = 0; i < cells.length; i++) {
    map[cells[i].id] = cells[i]
    for (var j = 0; j < (cells[i].actions || []).length; j++)
      map[cells[i].actions[j].id] = cells[i].actions[j]
  }
  return map
}

// One physical key can emit its F-key code or a firmware action code.
function cellCodes(cell) {
  var codes = cell.code === null || cell.code === undefined ? [] : [cell.code]
  for (var i = 0; i < (cell.actions || []).length; i++) codes.push(cell.actions[i].code)
  return codes
}

// Width of the main alphanumeric block: everything before the nav cluster,
// which is the first cell carrying a gap. Every row should agree, and a
// mis-sized modifier shows up here immediately.
function mainBlockWidth(row) {
  var x = 0, extent = 0
  for (var i = 0; i < row.length; i++) {
    if (row[i].gap) break
    if (row[i].x !== undefined) x = row[i].x
    x += (row[i].w || 1)
    extent = Math.max(extent, x)
  }
  return extent
}

// Total declared width of a row in keycap units.
// Note: a double-height key declared in an earlier row contributes nothing
// here, so a row it spans into measures narrower than it renders.
function rowWidth(row) {
  return placeRow(row, 0, []).width
}

// Lays a row out as absolute positions, resolving gaps into x offsets and
// carrying double-height keys down from the row above. `carry` is the list
// returned as `spans` by the previous row's call; pass [] for the first row.
function placeRow(row, rowIndex, carry) {
  var placed = [], spans = []
  var x = 0, extent = 0, i

  for (i = 0; i < (carry || []).length; i++) {
    // A key spanning into this row occupies its column but is drawn once,
    // by the row that declared it.
    placed.push({ cell: carry[i].cell, x: carry[i].x, w: carry[i].w,
                  continued: true })
  }

  for (i = 0; i < row.length; i++) {
    var cell = row[i]
    x = cell.x === undefined ? x + (cell.gap || 0) : cell.x
    var w = cell.w || 1
    placed.push({ cell: cell, x: x, w: w, continued: false })
    if ((cell.h || 1) > 1) spans.push({ cell: cell, x: x, w: w })
    x += w
    extent = Math.max(extent, x)
  }

  return { row: rowIndex, placed: placed, spans: spans, width: extent }
}

// Full board layout as rows of absolute-positioned cells.
function place(layout) {
  var out = [], carry = []
  if (!layout || !layout.rows) return out
  for (var r = 0; r < layout.rows.length; r++) {
    var res = placeRow(layout.rows[r], r, carry)
    res.height = (layout.rowHeights || [])[r] || 1
    res.gapAfter = (layout.rowGaps || [])[r] || 0
    out.push(res)
    carry = res.spans
  }
  return out
}

function isFirmwareLocal(layout, id) {
  return !!layout && (layout.firmwareLocal || []).indexOf(id) >= 0
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    allCells: allCells,
    byCode: byCode,
    byId: byId,
    cellCodes: cellCodes,
    mainBlockWidth: mainBlockWidth,
    rowWidth: rowWidth,
    placeRow: placeRow,
    place: place,
    isFirmwareLocal: isFirmwareLocal
  }
}
