// Layout resolution: field-observed library first, OS geometries second.
//   node tests/resolver.test.js

var R = require("./load.js").loadQmlJs("LayoutResolver.js")
var fs = require("fs")
var path = require("path")

var registry = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "..", "layouts", "index.json"), "utf8"))

var failures = []
function check(name, cond, detail) {
  if (!cond) failures.push(name + (detail ? ": " + detail : ""))
}

var allOsPresent = function () { return true }
var noOsPresent = function () { return false }

// 1. Fred's Calliope resolves to the transcribed layout by USB id.
var calliope = R.resolve({ name: "LiteOn Lenovo Calliope USB Keyboard",
                           vendor: "17ef", product: "608c" }, registry, allOsPresent)
check("Calliope resolves to field-observed", calliope.kind === "field-observed", calliope.kind)
check("Calliope layout id", calliope.layoutId === "lenovo-calliope", calliope.layoutId)
check("Calliope matched by USB id", calliope.match === R.MATCH_USB_ID, calliope.match)
check("Calliope is confident", calliope.confident === true)
check("Calliope is exact", R.isExact(calliope) === true)
check("Calliope carries a file", calliope.file === "lenovo-calliope.json", calliope.file)

// 2. USB id wins even when the name would match something else.
var oddName = R.resolve({ name: "Generic Keyboard", vendor: "17ef", product: "608c" },
                        registry, allOsPresent)
check("USB id matches regardless of name", oddName.layoutId === "lenovo-calliope", oddName.layoutId)

// 3. Name pattern matches when the USB id is unknown.
var byName = R.resolve({ name: "Lenovo Calliope Clone", vendor: "ffff", product: "0000" },
                       registry, allOsPresent)
check("name pattern matches", byName.match === R.MATCH_NAME, byName.match)
check("name match is field-observed", byName.kind === "field-observed")

// 4. An unknown ordinary keyboard falls back to an OS geometry, not to a
//    field-observed layout that does not describe it.
var unknown = R.resolve({ name: "Generic USB Keyboard", vendor: "046d", product: "c31c" },
                        registry, allOsPresent)
check("unknown board uses OS geometry", unknown.kind === "os-geometry", unknown.kind)
check("unknown board picks pc104", unknown.layoutId === "pc104", unknown.layoutId)
check("unknown board is not confident", unknown.confident === false)
check("unknown board is not exact", R.isExact(unknown) === false)

// 5. A vendor-named board prefers that vendor's OS geometry over generic pc104.
var tp = R.resolve({ name: "ThinkPad Compact USB Keyboard", vendor: "17ef", product: "6047" },
                   registry, allOsPresent)
check("vendor geometry chosen", tp.layoutId === "thinkpad", tp.layoutId)
check("vendor match kind", tp.match === R.MATCH_OS_VENDOR, tp.match)

// 6. A vendor geometry that the OS does not actually ship is skipped.
var onlyPc104 = function (g) { return g === "pc104" }
var tpMissing = R.resolve({ name: "ThinkPad Compact USB Keyboard", vendor: "17ef", product: "6047" },
                          registry, onlyPc104)
check("missing vendor geometry skipped", tpMissing.layoutId === "pc104", tpMissing.layoutId)

// 7. With no OS geometries at all, the declared fallback is named honestly.
var bare = R.resolve({ name: "Mystery Board", vendor: "0000", product: "0000" },
                     registry, noOsPresent)
check("fallback used", bare.match === R.MATCH_FALLBACK, bare.match)
check("fallback names pc104", bare.layoutId === "pc104", bare.layoutId)

// 8. Missing/garbage input must not throw.
var empty
try { empty = R.resolve(null, registry, allOsPresent) } catch (e) { empty = { err: e.message } }
check("null device does not throw", !empty.err, empty.err)
try { R.resolve({}, null, null) } catch (e2) { check("null registry does not throw", false, e2.message) }

// 9. Every registry entry points at a file that exists.
;(registry.layouts || []).forEach(function (l) {
  var p = path.resolve(__dirname, "..", "layouts", l.file)
  check("layout file exists for " + l.id, fs.existsSync(p), l.file)
  if (fs.existsSync(p)) {
    var data = JSON.parse(fs.readFileSync(p, "utf8"))
    check("layout " + l.id + " id matches registry", data.id === l.id, data.id)
    check("layout " + l.id + " has rows", Array.isArray(data.rows) && data.rows.length > 0)
  }
})

// 10. An OS-geometry resolution has no layout file, so the registry must name a
// bundled stand-in board or the panel draws nothing (0.5.12, slowhp).
check("registry names a stand-in board", typeof registry.standIn === "string" && registry.standIn !== "")
var standInPath = path.resolve(__dirname, "..", "layouts", registry.standIn || "missing")
check("stand-in board file exists", fs.existsSync(standInPath), registry.standIn)
if (fs.existsSync(standInPath)) {
  var standIn = JSON.parse(fs.readFileSync(standInPath, "utf8"))
  var cells = []
  ;(standIn.rows || []).forEach(function (row) { row.forEach(function (c) { cells.push(c) }) })
  var codes = cells.filter(function (c) { return c.code !== undefined }).map(function (c) { return c.code })
  check("stand-in has 104 keys", codes.length === 104, String(codes.length))
  check("stand-in key codes are unique", new Set(codes).size === codes.length)
  var ids = cells.map(function (c) { return c.id })
  check("stand-in ids are unique", new Set(ids).size === ids.length)
  ;["ESC", "ENTER", "SPACE", "LEFTMETA", "K", "KPENTER"].forEach(function (id) {
    check("stand-in has " + id, ids.indexOf(id) >= 0)
  })
  check("stand-in keeps the lock LEDs", ids.indexOf("LED_CAPS") >= 0 && ids.indexOf("LED_NUM") >= 0)
}
var unknownBoard = R.resolve({ name: "AT Translated Set 2 keyboard", vendor: "0001", product: "0001" },
                             registry, allOsPresent)
check("unknown board resolves with no file but a stand-in exists",
      unknownBoard.file === null && !!registry.standIn)

if (failures.length) {
  console.error("FAIL (" + failures.length + ")")
  failures.forEach(function (f) { console.error("  - " + f) })
  process.exit(1)
}
console.log("ok - resolver: " + (registry.layouts || []).length +
            " field-observed layout(s), OS fallback " + registry.fallback)
