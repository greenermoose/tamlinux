.pragma library

// Identifies the attached physical keyboard, for the bar tooltip and for
// layout resolution.
//
// Reads only descriptive metadata: device names, USB vendor/product ids, bus
// type and the active keymap. It never opens /dev/input and never sees a
// keystroke. Parsing is pure so it can be unit tested in Node.

// Bus types from linux/input.h, as they appear in `I: Bus=NNNN`.
var BUS = {
  "0001": "PCI",
  "0003": "USB",
  "0005": "Bluetooth",
  "0010": "ISA",
  "0011": "PS/2",
  "0018": "I2C",
  "0019": "Host"
}

// Devices that are not a keyboard someone types on.
function isNoiseName(name) {
  var n = String(name || "").toLowerCase()
  return n.indexOf("virtual") >= 0 ||       // hl-virtual-keyboard-fcitx5
         n.indexOf("fcitx") >= 0 ||
         n.indexOf("power button") >= 0 ||
         n.indexOf("video bus") >= 0 ||
         n.indexOf("sleep button") >= 0 ||
         n.indexOf("at raw set") >= 0 ||    // PS/2 stub, present with nothing attached
         n.indexOf("consumer control") >= 0 ||
         n.indexOf("system control") >= 0
}

// Parse /proc/bus/input/devices into keyboard records.
// Returns [{ name, vendor, product, bus, busLabel, handlers, keyCount }]
function parseProcDevices(text) {
  var out = []
  var blocks = String(text || "").split(/\n\s*\n/)

  for (var i = 0; i < blocks.length; i++) {
    var b = blocks[i]
    if (!b || b.indexOf("N: Name=") < 0) continue

    var nameM = b.match(/N: Name="([^"]*)"/)
    var idM = b.match(/I: Bus=([0-9a-fA-F]+)\s+Vendor=([0-9a-fA-F]+)\s+Product=([0-9a-fA-F]+)/)
    var hM = b.match(/H: Handlers=([^\n]*)/)
    var keyM = b.match(/B: KEY=([0-9a-f ]+)/)
    if (!nameM || !idM) continue

    var handlers = hM ? hM[1].trim() : ""
    // A real keyboard exposes the kbd handler and declares key bits.
    if (handlers.indexOf("kbd") < 0 || !keyM) continue

    out.push({
      name: nameM[1],
      bus: idM[1].toLowerCase(),
      busLabel: BUS[idM[1].toLowerCase()] || ("bus " + idM[1]),
      vendor: idM[2].toLowerCase(),
      product: idM[3].toLowerCase(),
      handlers: handlers,
      keyCount: countKeyBits(keyM[1])
    })
  }
  return out
}

// Number of keys the device declares. Note this is what the HID descriptor
// advertises, which is generally MORE than the board physically has.
//
// Counted per hex digit on purpose: a KEY= bitmap word is 16 hex digits (64
// bits), which exceeds JavaScript's 53-bit safe integer range, so parseInt
// followed by bitwise arithmetic silently loses bits.
var BITS_PER_NIBBLE = {
  "0": 0, "1": 1, "2": 1, "3": 2, "4": 1, "5": 2, "6": 2, "7": 3,
  "8": 1, "9": 2, "a": 2, "b": 3, "c": 2, "d": 3, "e": 3, "f": 4
}

function countKeyBits(bitmap) {
  var s = String(bitmap || "").toLowerCase()
  var n = 0
  for (var i = 0; i < s.length; i++) {
    var b = BITS_PER_NIBBLE[s.charAt(i)]
    if (b !== undefined) n += b
  }
  return n
}

// Pick the keyboard the user is most likely typing on: a real, non-noise
// device, preferring the one declaring the most keys (the main board rather
// than its System/Consumer Control siblings).
//
// Caveat: with two physical keyboards attached this cannot tell which one is
// under the user's hands. The compositor does not report which device emitted
// a keystroke, and only per-device /dev/input reads could answer it, which
// this plugin deliberately does not do.
function primaryKeyboard(devices) {
  var real = (devices || []).filter(function (d) { return !isNoiseName(d.name) })
  if (real.length === 0) return null
  real.sort(function (a, b) { return b.keyCount - a.keyCount })
  return real[0]
}

// Active keymap from `hyprctl -j devices`, e.g. "English (US)".
function activeKeymap(hyprctlJson) {
  try {
    var data = typeof hyprctlJson === "string" ? JSON.parse(hyprctlJson) : hyprctlJson
    var kbs = (data && data.keyboards) || []
    for (var i = 0; i < kbs.length; i++)
      if (kbs[i].main && kbs[i].active_keymap) return kbs[i].active_keymap
    for (var j = 0; j < kbs.length; j++)
      if (kbs[j].active_keymap) return kbs[j].active_keymap
  } catch (e) { /* fall through */ }
  return ""
}

// --- Keyboard LED state ------------------------------------------------
//
// Caps Lock and Num Lock state comes from sysfs, which reports the real
// hardware LED the keyboard itself is showing. This needs no privileges, no
// /dev/input access and no keystroke observation: it is the lamp, not the key.
//
// The LED nodes are named `input<N>::capslock`, where N is the kernel's input
// device index. The device's own `H: Handlers=... event<N>` line carries the
// matching number, so the path is derived from the device rather than guessed.
// Verified on this machine: input5::capslock resolves to the Calliope, whose
// sysfs path carries 0003:17EF:608C.

function inputIndexFor(device) {
  if (!device) return -1
  var m = String(device.handlers || "").match(/\bevent(\d+)\b/)
  return m ? parseInt(m[1], 10) : -1
}

// Returns { caps, num } absolute sysfs brightness paths, or null when the
// device does not expose LEDs (its handlers omit `leds`).
function ledPaths(device) {
  var idx = inputIndexFor(device)
  if (idx < 0) return null
  if (String(device.handlers || "").indexOf("leds") < 0) return null
  var base = "/sys/class/leds/input" + idx + "::"
  return { caps: base + "capslock/brightness", num: base + "numlock/brightness" }
}

// sysfs brightness is "0" or a positive integer; anything else is unknown.
function ledOn(text) {
  var n = parseInt(String(text || "").trim(), 10)
  return isFinite(n) ? n > 0 : false
}

// Trim vendor boilerplate so the tooltip reads like a product name.
function shortName(name) {
  return String(name || "")
    .replace(/\bUSB\b/gi, "")
    .replace(/\bKeyboard\b/gi, "")
    .replace(/\bLiteOn\b/gi, "")
    .replace(/\s+/g, " ")
    .trim()
}

// One-line summary for the bar tooltip, e.g.
//   "Lenovo Calliope - English (US) - USB"
function summary(device, keymap) {
  if (!device) return "No keyboard detected"
  var parts = []
  var n = shortName(device.name)
  parts.push(n !== "" ? n : device.name)
  if (keymap) parts.push(keymap)
  if (device.busLabel) parts.push(device.busLabel)
  return parts.join(" - ")
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    BUS: BUS,
    isNoiseName: isNoiseName,
    parseProcDevices: parseProcDevices,
    countKeyBits: countKeyBits,
    BITS_PER_NIBBLE: BITS_PER_NIBBLE,
    primaryKeyboard: primaryKeyboard,
    activeKeymap: activeKeymap,
    inputIndexFor: inputIndexFor,
    ledPaths: ledPaths,
    ledOn: ledOn,
    shortName: shortName,
    summary: summary
  }
}
