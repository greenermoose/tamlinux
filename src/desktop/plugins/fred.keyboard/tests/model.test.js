// Structural checks on KeyboardModel.js. Plain Node, no framework:
//   node tests/model.test.js
//
// The cross-check against the live device bitmap is a separate script
// (tests/check-against-hardware.sh) because it only works on Fred's machine.

var M = require("./load.js").loadQmlJs("KeyboardModel.js")
var fs = require("fs"), path = require("path")
var L = JSON.parse(fs.readFileSync(
  path.resolve(__dirname, "..", "layouts", "lenovo-calliope.json"), "utf8"))

var failures = []
function check(name, cond, detail) {
  if (cond) return
  failures.push(name + (detail ? ": " + detail : ""))
}

// 1. No duplicate evdev codes. A duplicate would make two keys light at once.
var seen = {}
var dupes = []
M.allCells(L).forEach(function (c) {
  if (c.code === null || c.code === undefined) return
  if (seen[c.code]) dupes.push(c.id + " and " + seen[c.code] + " share code " + c.code)
  seen[c.code] = c.id
})
check("no duplicate evdev codes", dupes.length === 0, dupes.join("; "))

// 2. No duplicate ids.
var ids = {}, dupIds = []
M.allCells(L).forEach(function (c) {
  if (ids[c.id]) dupIds.push(c.id)
  ids[c.id] = true
})
check("no duplicate ids", dupIds.length === 0, dupIds.join(", "))

// 3. Six rows, as Fred described.
check("six rows", L.rows.length === 6, "got " + L.rows.length)

// 4. Fn is present but emits nothing.
var fn = M.allCells(L).filter(function (c) { return c.id === "FN" })[0]
check("Fn is modelled", !!fn)
check("Fn emits no code", fn && fn.code === null, fn ? String(fn.code) : "missing")
check("Fn listed as firmware-local", L.firmwareLocal.indexOf("FN") >= 0)

// 5. The double-height keys span two rows.
var tall = M.allCells(L).filter(function (c) { return c.h === 2 }).map(function (c) { return c.id })
check("Delete is double-height", tall.indexOf("DELETE") >= 0, tall.join(","))
check("numpad + is double-height", tall.indexOf("KPPLUS") >= 0, tall.join(","))
check("numpad Enter is double-height", tall.indexOf("KPENTER") >= 0, tall.join(","))
check("exactly three tall keys", tall.length === 3, tall.join(","))

// 6. A tall key must not be re-declared in the row it spans into.
var r3 = L.rows[2].map(function (c) { return c.id })
var r4 = L.rows[3].map(function (c) { return c.id })
check("Delete not repeated in row 4", r4.indexOf("DELETE") < 0)
check("KPPLUS not repeated in row 4", r4.indexOf("KPPLUS") < 0)
var r6 = L.rows[5].map(function (c) { return c.id })
check("KPENTER not repeated in row 6", r6.indexOf("KPENTER") < 0)

// 7. This board has no right Super key.
check("no RIGHTMETA keycap", !ids["RIGHTMETA"])
check("RIGHTMETA recorded as declared-but-absent", L.declaredButAbsent.indexOf("RIGHTMETA") >= 0)

// 8. Byte-for-byte sanity on a few codes that are easy to transpose.
var byCode = M.byCode(L)
check("code 1 is Esc", byCode[1] && byCode[1].id === "ESC")
check("code 111 is Delete", byCode[111] && byCode[111].id === "DELETE")
check("code 110 is Insert", byCode[110] && byCode[110].id === "INSERT")
check("code 70 is ScrLk", byCode[70] && byCode[70].id === "SCROLLLOCK")
check("code 99 is PrtSc", byCode[99] && byCode[99].id === "SYSRQ")
check("code 96 is numpad Enter", byCode[96] && byCode[96].id === "KPENTER")
check("code 28 is Enter", byCode[28] && byCode[28].id === "ENTER")

// 9. The main alphanumeric block must be exactly 15u on every row. This is
// the real invariant: a mis-sized modifier shows up here immediately.
// (Whole-row width is NOT comparable, because a double-height key declared
// in an earlier row contributes no width to the row it spans into.)
var mains = L.rows.map(M.mainBlockWidth)
mains.forEach(function (w, i) {
  check("row " + (i + 1) + " main block is 15u", Math.abs(w - 15) < 0.001, w.toFixed(2) + "u")
})

// 10. Placement: double-height keys carry into the row below exactly once,
// are drawn by the row that declares them, and keep their column.
var board = M.place(L)
check("placed six rows", board.length === 6, String(board.length))

function findPlaced(rowIdx, id) {
  return board[rowIdx].placed.filter(function (p) { return p.cell.id === id })[0]
}

var delR3 = findPlaced(2, "DELETE"), delR4 = findPlaced(3, "DELETE")
check("Delete placed in row 3", !!delR3)
check("Delete carried into row 4", !!delR4)
check("Delete drawn once (row 3 owns it)", delR3 && delR3.continued === false)
check("Delete marked continued in row 4", delR4 && delR4.continued === true)
check("Delete keeps its column", delR3 && delR4 && delR3.x === delR4.x,
      delR3 && delR4 ? delR3.x + " vs " + delR4.x : "missing")

var plusR3 = findPlaced(2, "KPPLUS"), plusR4 = findPlaced(3, "KPPLUS")
check("numpad + carried into row 4", !!plusR4 && plusR4.continued === true)
check("numpad + keeps its column", plusR3 && plusR4 && plusR3.x === plusR4.x)

var entR5 = findPlaced(4, "KPENTER"), entR6 = findPlaced(5, "KPENTER")
check("numpad Enter carried into row 6", !!entR6 && entR6.continued === true)
check("numpad Enter keeps its column", entR5 && entR6 && entR5.x === entR6.x)

// A span must not leak further than one row.
check("Delete does not reach row 5", !findPlaced(4, "DELETE"))
check("numpad Enter does not exist in row 4", !findPlaced(3, "KPENTER"))

// Nav cluster and numpad must occupy consistent columns across rows 2-6.
// The nav cluster is a 3u region; not every row fills all three columns
// (PgDn sits beside the double-height Delete, Up is the centre of the
// inverted-T), so we assert the region, not a single start column.
var navIds = ["HOME", "END", "DELETE", "PAGEUP", "PAGEDOWN", "UP", "LEFT", "DOWN", "RIGHT"]
var navPos = []
for (var r = 1; r < 6; r++)
  board[r].placed.forEach(function (p) {
    if (navIds.indexOf(p.cell.id) >= 0 && !p.continued) navPos.push([p.cell.id, p.x])
  })
var NAV_START = 16, NAV_WIDTH = 3
check("nav cluster inside its 3u region",
      navPos.every(function (n) { return n[1] >= NAV_START && n[1] < NAV_START + NAV_WIDTH }),
      navPos.map(function (n) { return n[0] + "@" + n[1] }).join(" "))
check("nav cells sit on column boundaries",
      navPos.every(function (n) { return Math.abs(n[1] - Math.round(n[1])) < 0.001 }),
      navPos.map(function (n) { return n[0] + "@" + n[1] }).join(" "))

// The numpad must start at the same column on every row that has one.
var padPos = []
for (var r2 = 1; r2 < 6; r2++) {
  var first = board[r2].placed.filter(function (p) {
    return p.cell.id.indexOf("KP") === 0 || p.cell.id === "NUMLOCK"
  }).sort(function (a, b) { return a.x - b.x })[0]
  if (first) padPos.push(first.x)
}
check("numpad starts at one column",
      padPos.every(function (x) { return x === padPos[0] }), padPos.join(","))

if (failures.length) {
  console.error("FAIL (" + failures.length + ")")
  failures.forEach(function (f) { console.error("  - " + f) })
  process.exit(1)
}
console.log("ok - " + M.allCells(L).length + " cells, " + L.rows.length +
            " rows, main block " + mains[0].toFixed(2) + "u on all rows")
