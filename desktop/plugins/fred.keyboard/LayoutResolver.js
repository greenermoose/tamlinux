.pragma library

// Chooses a keyboard layout for an attached device.
//
// Two supplies of layouts, consulted in order:
//
//   1. The field-observed library in `layouts/` - boards we have physically
//      transcribed because no stock geometry describes them correctly. Fred's
//      Lenovo Calliope is the first; others arrive from his own hardware or
//      from users who send in their keycap arrangement.
//   2. The OS supply - XKB geometries under /usr/share/X11/xkb/geometry,
//      covering pc101/pc104/pc105 and a set of vendor boards. Correct for
//      ordinary keyboards and free to use, so we prefer them over guessing.
//
// A field-observed layout always wins over a stock geometry for the same
// device: it exists precisely because the stock one was wrong.
//
// This module is pure. It does no file or process I/O so it can be unit
// tested in Node; callers supply the registry, the device facts, and a
// predicate reporting which OS geometries actually exist on this machine.

// Match strength, highest first. Returned so callers can explain the choice
// to the user rather than presenting a layout as if it were certain.
var MATCH_USB_ID = "usb-id"          // vendor:product - unambiguous
var MATCH_NAME = "name-pattern"      // device name matched a library entry
var MATCH_OS_VENDOR = "os-vendor"    // an OS vendor geometry named the device
var MATCH_OS_DEFAULT = "os-default"  // generic OS geometry, e.g. pc104
var MATCH_FALLBACK = "fallback"      // nothing matched; last resort

function norm(s) {
  return (s === null || s === undefined) ? "" : String(s).toLowerCase()
}

// device: { name, vendor, product }  - vendor/product are hex strings as they
//         appear in /proc/bus/input/devices, e.g. "17ef", "608c".
// registry: the parsed layouts/index.json.
// osHas: function(geometryName) -> bool, true if the OS provides it.
//
// Returns { layoutId, file, kind, match, confident, why } where `file` is set
// only for field-observed layouts and `layoutId` names an XKB geometry
// otherwise.
function resolve(device, registry, osHas) {
  device = device || {}
  registry = registry || {}
  osHas = osHas || function () { return false }

  var entries = registry.layouts || []
  var vendor = norm(device.vendor)
  var product = norm(device.product)
  var name = norm(device.name)

  // 1. Field-observed, matched by USB vendor:product. Strongest signal.
  for (var i = 0; i < entries.length; i++) {
    var m = entries[i].match || {}
    if (m.vendor && m.product &&
        norm(m.vendor) === vendor && norm(m.product) === product) {
      return result(entries[i], MATCH_USB_ID, true,
                    "USB id " + vendor + ":" + product + " is a transcribed board")
    }
  }

  // 2. Field-observed, matched on the device name.
  for (var j = 0; j < entries.length; j++) {
    var mm = entries[j].match || {}
    if (mm.namePattern && name.indexOf(norm(mm.namePattern)) >= 0) {
      return result(entries[j], MATCH_NAME, true,
                    "device name contains \"" + mm.namePattern + "\"")
    }
  }

  var os = registry.osGeometries || {}

  // 3. An OS vendor geometry whose name appears in the device name, e.g. a
  //    ThinkPad board matching the `thinkpad` geometry file.
  var vendorFiles = os.vendorFiles || []
  for (var k = 0; k < vendorFiles.length; k++) {
    if (name.indexOf(norm(vendorFiles[k])) >= 0 && osHas(vendorFiles[k])) {
      return {
        layoutId: vendorFiles[k], file: null, kind: "os-geometry",
        match: MATCH_OS_VENDOR, confident: false,
        why: "device name suggests the OS \"" + vendorFiles[k] + "\" geometry"
      }
    }
  }

  // 4. First preferred generic OS geometry that exists.
  var preferred = os.preferred || []
  for (var n = 0; n < preferred.length; n++) {
    if (osHas(preferred[n])) {
      return {
        layoutId: preferred[n], file: null, kind: "os-geometry",
        match: MATCH_OS_DEFAULT, confident: false,
        why: "no specific layout known; using the OS \"" + preferred[n] + "\" geometry"
      }
    }
  }

  // 5. Nothing available. Name the fallback so the panel can say so plainly.
  return {
    layoutId: registry.fallback || "pc104", file: null, kind: "os-geometry",
    match: MATCH_FALLBACK, confident: false,
    why: "no layout matched and no OS geometry was found"
  }
}

function result(entry, match, confident, why) {
  return {
    layoutId: entry.id,
    file: entry.file,
    kind: "field-observed",
    match: match,
    confident: confident,
    why: why
  }
}

// True when the resolved layout is known to describe this exact board, as
// opposed to a plausible stand-in. The panel uses this to decide whether to
// invite the user to correct the layout.
function isExact(res) {
  return !!res && res.kind === "field-observed"
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    resolve: resolve,
    isExact: isExact,
    MATCH_USB_ID: MATCH_USB_ID,
    MATCH_NAME: MATCH_NAME,
    MATCH_OS_VENDOR: MATCH_OS_VENDOR,
    MATCH_OS_DEFAULT: MATCH_OS_DEFAULT,
    MATCH_FALLBACK: MATCH_FALLBACK
  }
}
