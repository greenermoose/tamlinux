
// Keybinding viewer rows for the Tamlinux shell. Pure functions over the
// compositor facade's bindingsText (Hyprland `hyprctl binds` text, or the
// Sway adapter's JSON array) and the command table tam-menu-keybindings
// scans from the Lua config. No I/O; Node loads this file for the tests.
//
// The modifier names, key renames, and the two web-app rows are ported from
// omarchy 4.0.4 bin/omarchy-menu-keybindings (MIT, Copyright (c) David
// Heinemeier Hansson; see ../LICENSE-omarchy). The parsing and the order
// are new.

var APP_VERSION = "0.4.4"
var MAX_TEXT = 4 * 1024 * 1024
var MAX_BINDS = 4096
var MAX_FIELD = 1024

function clip(value) {
  var s = value === undefined || value === null ? "" : String(value)
  return s.length > MAX_FIELD ? s.substring(0, MAX_FIELD) : s
}

// Lua binds report the whole chord ("SUPER + code:20") as the key; the
// modifiers are already in modmask, so keep only the last part.
function bindKey(rawKey, keycode) {
  var key = clip(rawKey)
  var cut = key.lastIndexOf(" + ")
  if (cut >= 0) key = key.substring(cut + 3)
  if (key === "" && String(keycode || "0") !== "0") key = "code:" + String(keycode)
  return key
}

function makeBind(f) {
  return {
    modmask: (Number(f.modmask) || 0) & 0xff,
    key: bindKey(f.key, f.keycode),
    description: clip(f.description),
    dispatcher: clip(f.dispatcher),
    arg: clip(f.arg)
  }
}

function parseText(s) {
  var out = [], cur = null
  var lines = s.split("\n")
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i]
    if (line.charAt(0) !== "\t") {
      if (cur && out.length < MAX_BINDS) out.push(makeBind(cur))
      cur = /^bind/.test(line) ? {} : null
      continue
    }
    if (!cur) continue
    var m = /^\t([a-z_]+): ?(.*)$/.exec(line)
    if (m) cur[m[1]] = m[2]
  }
  if (cur && out.length < MAX_BINDS) out.push(makeBind(cur))
  return out
}

function parseJson(s) {
  var raw
  try { raw = JSON.parse(s) } catch (e) { return [] }
  if (!Array.isArray(raw)) return []
  var out = []
  for (var i = 0; i < raw.length && out.length < MAX_BINDS; i++)
    if (raw[i] && typeof raw[i] === "object") out.push(makeBind(raw[i]))
  return out
}

// The facade's bindings as plain records. Never throws; empty or oversized
// input gives [].
function parseBinds(text) {
  var s = String(text || "")
  if (s.length === 0 || s.length > MAX_TEXT) return []
  return s.charAt(0) === "[" ? parseJson(s) : parseText(s)
}

// The scan's lines are "modmask<TAB>description<TAB>key<TAB>kind<TAB>arg".
// byKey: "modmask,description,key" -> { dispatcher, arg }
// keyFor: "modmask,description" -> key (for binds reported without one)
function parseCommands(text) {
  var byKey = {}, keyFor = {}
  var s = String(text || "")
  if (s.length > MAX_TEXT) s = ""
  var lines = s.split("\n")
  for (var i = 0; i < lines.length; i++) {
    var f = lines[i].split("\t")
    if (f.length < 3 || f[0] === "" || f[1] === "" || f[2] === "") continue
    keyFor[f[0] + "," + f[1]] = f[2]
    byKey[f[0] + "," + f[1] + "," + f[2]] = {
      dispatcher: clip(f[3] || ""),
      arg: clip(f.slice(4).join("\t"))
    }
  }
  return { byKey: byKey, keyFor: keyFor }
}

var MODS_TEXT = {
  0: "", 1: "SHIFT", 4: "CTRL", 5: "SHIFT CTRL", 8: "ALT", 9: "SHIFT ALT",
  12: "CTRL ALT", 13: "SHIFT CTRL ALT", 64: "SUPER", 65: "SUPER SHIFT",
  68: "SUPER CTRL", 69: "SUPER SHIFT CTRL", 72: "SUPER ALT",
  73: "SUPER SHIFT ALT", 76: "SUPER CTRL ALT", 77: "SUPER SHIFT CTRL ALT"
}

function modsText(modmask) {
  var t = MODS_TEXT[modmask]
  return t === undefined ? String(modmask) : t
}

// XKB keycodes on the US layout, as `xkbcli compile-keymap` names their
// first symbol.
var KEYCODE_NAMES = {
  10: "1", 11: "2", 12: "3", 13: "4", 14: "5", 15: "6", 16: "7", 17: "8",
  18: "9", 19: "0", 20: "MINUS", 21: "EQUAL", 34: "BRACKETLEFT",
  35: "BRACKETRIGHT", 59: "COMMA", 60: "PERIOD", 61: "SLASH",
  79: "KP_HOME", 80: "KP_UP", 81: "KP_PRIOR", 83: "KP_LEFT", 84: "KP_BEGIN",
  85: "KP_RIGHT", 87: "KP_END", 88: "KP_DOWN", 89: "KP_NEXT",
  90: "KP_INSERT", 91: "KP_DELETE"
}

var MOUSE_NAMES = {
  272: "LEFT MOUSE BUTTON", 273: "RIGHT MOUSE BUTTON", 274: "MIDDLE MOUSE BUTTON"
}

var KEY_RENAMES = { comma: "COMMA", period: "PERIOD", minus: "MINUS", equal: "EQUAL", slash: "SLASH" }

function keyLabel(key) {
  if (KEY_RENAMES[key]) return KEY_RENAMES[key]
  var m = /^code:([0-9]+)$/.exec(key)
  if (m) return KEYCODE_NAMES[m[1]] || key
  m = /^mouse:([0-9]+)$/.exec(key)
  if (m) return MOUSE_NAMES[m[1]] || key
  return key
}

function comboText(modmask, key) {
  var mods = modsText(modmask)
  var label = keyLabel(key)
  return mods === "" ? label : mods + " + " + label
}

// Individual keys for pill/badge rendering: ["SUPER", "SHIFT", "W"]
function chordKeys(modmask, key) {
  var mods = modsText(modmask)
  var label = keyLabel(key)
  var parts = []
  if (mods !== "") {
    var modParts = mods.split(" ")
    for (var i = 0; i < modParts.length; i++) {
      if (modParts[i] !== "") parts.push(modParts[i])
    }
  }
  if (label !== "") parts.push(label)
  return parts
}

// What a bind without a description does, from its dispatcher and argument.
function actionText(dispatcher, arg) {
  var action = (dispatcher + " " + arg).replace(/^\s+|\s+$/g, "")
  action = action.replace(/^exec\s+/, "")
  action = action.replace(/(^|\s)uwsm(-app| app)\s+--\s+/, "$1")
  return action.replace(/^\s+|\s+$/g, "")
}

function pad(text, width) {
  var s = text
  while (s.length < width) s += " "
  return s
}

// Rows the config cannot show: shortcuts the web-app extensions handle.
var STATIC_ROWS = [
  { modmask: 9, key: "L", description: "Copy URL from Web App", dispatcher: "sendshortcut", arg: "SHIFT ALT,L," },
  { modmask: 9, key: "D", description: "Download Video from Web App", dispatcher: "sendshortcut", arg: "SHIFT ALT,D," }
]

// Curated metadata is keyed by the complete action, so a user override is
// never given a description for a different command.
var EXPLANATIONS = {
  "tam-hyprland-window-single-square-aspect-toggle": "Toggle a square aspect ratio for the only window on the current workspace.",
  "tam-hyprland-window-gaps-toggle": "Toggle outer and inner window gaps on the active workspace.",
  "tam-hyprland-window-opacity-toggle": "Toggle window opacity between translucent and solid.",
  "tam-hyprland-window-close-all": "Close all open windows on the current workspace.",
  "tam-hyprland-window-tiled-fullscreen-toggle": "Toggle full screen within the tiled boundary without obscuring the bar.",
  "tam-hyprland-window-pop": "Pop active window out of tiling layout into a floating and pinned window.",
  "tam-hyprland-workspace-layout-toggle": "Toggle between master/stack and dwindle workspace tiling layouts.",
  "tam-shell clipboard toggle": "Open the clipboard history manager to search and paste recent clips.",
  "tam-shell media playPause": "Toggle media playback between play and pause.",
  "tam-shell media next": "Skip forward to the next media track.",
  "tam-shell media previous": "Return to the previous media track.",
  "tam-audio-output-volume raise": "Increase master audio output volume.",
  "tam-audio-output-volume lower": "Decrease master audio output volume.",
  "tam-audio-output-volume mute-toggle": "Mute or unmute master audio output.",
  "tam-audio-input-mute": "Mute or unmute microphone audio input.",
  "tam-audio-output-switch": "Switch active audio output sink (headphones, speakers, HDMI).",
  "tam-audio-source-switch": "Switch active media player audio source.",
  "tam-brightness-display +5%": "Increase primary display backlight brightness by 5%.",
  "tam-brightness-display 5%-": "Decrease primary display backlight brightness by 5%.",
  "tam-brightness-display 100%": "Set display brightness to maximum.",
  "tam-brightness-display 1%": "Set display brightness to minimum.",
  "tam-brightness-keyboard up": "Increase keyboard backlight brightness.",
  "tam-brightness-keyboard down": "Decrease keyboard backlight brightness.",
  "tam-brightness-keyboard cycle": "Cycle keyboard backlight brightness through presets.",
  "tam-toggle-input-device touchpad": "Toggle touchpad input device on or off.",
  "foot": "Launch Foot, the fast Wayland terminal emulator.",
  "micro": "Launch Micro, the terminal text editor.",
  "tam-menu": "Open the Tamlinux application menu.",
  "tam-menu-keybindings": "Open the interactive keybinding explorer.",
  "hl.dsp.window.close()": "Safely close the focused persistent window.",
  "hl.dsp.layout(\"togglesplit\")": "Toggle the tiling split orientation between horizontal and vertical.",
  "hl.dsp.window.float({ action = \"toggle\" })": "Toggle the active window between floating and tiled mode.",
  "hl.dsp.window.fullscreen({ mode = \"fullscreen\" })": "Toggle true full screen display for the focused window.",
  "hl.dsp.window.fullscreen({ mode = \"maximized\" })": "Maximize window to the full display area while retaining the top bar."
}

function findExplanation(dispatcher, arg) {
  if (!arg && !dispatcher) return ""
  if (arg && EXPLANATIONS[arg]) return EXPLANATIONS[arg]
  var full = (dispatcher + " " + arg).trim()
  if (EXPLANATIONS[full]) return EXPLANATIONS[full]
  var clean = actionText(dispatcher, arg)
  if (clean && EXPLANATIONS[clean]) return EXPLANATIONS[clean]
  return ""
}

function actionGroup(text) {
  var s = String(text).toLowerCase()
  if (/workspace|desktop [0-9]/.test(s)) return "Workspaces"
  if (/window|focus|tile|floating|fullscreen/.test(s)) return "Windows"
  if (/audio|volume|mute|media|brightness/.test(s)) return "Media and display"
  if (/terminal|browser|application|apps menu/.test(s)) return "Applications"
  return "Other"
}

// Case-insensitive, with runs of digits compared as numbers, so
// "Switch desktop 2" sorts before "Switch desktop 10".
function naturalCompare(a, b) {
  var x = String(a).toLowerCase().match(/\d+|\D+/g) || []
  var y = String(b).toLowerCase().match(/\d+|\D+/g) || []
  for (var i = 0; i < x.length && i < y.length; i++) {
    if (x[i] === y[i]) continue
    var nx = /^\d/.test(x[i]), ny = /^\d/.test(y[i])
    if (nx && ny) {
      var d = Number(x[i]) - Number(y[i])
      if (d !== 0) return d < 0 ? -1 : 1
      continue
    }
    return x[i] < y[i] ? -1 : 1
  }
  return x.length - y.length < 0 ? -1 : x.length > y.length ? 1 : 0
}

function parseCatalog(text) {
  var input = String(text || "")
  if (!input || input.length > MAX_TEXT) return []
  try { var value = JSON.parse(input); return Array.isArray(value) ? value.slice(0, MAX_BINDS) : [] }
  catch (e) { return [] }
}

// Attach only catalog entries that match the live chord and exact action.
function bindingMetadata(catalog, bind) {
  if (!Array.isArray(catalog) || !bind.dispatcher || !bind.arg) return null
  var key = String(bind.key || "").toUpperCase()
  for (var i = 0; i < catalog.length; i++) {
    var item = catalog[i]
    if (item && item.mask === bind.modmask && String(item.key || "").toUpperCase() === key &&
        item.dispatcher === bind.dispatcher && item.arg === bind.arg &&
        typeof item.action === "string" && typeof item.why === "string" && typeof item.mnemonic === "string") return item
  }
  return null
}

// Viewer rows: [{ display, dispatcher, arg }], alphabetical by what the
// binding does, then by its keys. A row whose command the scan could not find keeps an empty
// dispatcher: the viewer shows it but Enter does nothing.
function explorerRecords(bindingsText, commandsText, includeStatic, catalog) {
  var commands = parseCommands(commandsText)
  var binds = parseBinds(bindingsText)
  var seen = {}, rows = []

  function add(b) {
    var description = b.description
    var text = description !== "" ? description : actionText(b.dispatcher, b.arg)
    if (text === "") return
    var display = pad(comboText(b.modmask, b.key), 35) + " → " + text
    var id = [display, b.dispatcher, b.arg].join("\t")
    if (seen[id]) return
    seen[id] = true
    var meta = bindingMetadata(catalog, b)
    rows.push({ display: display, dispatcher: b.dispatcher, arg: b.arg,
                does: text, combo: comboText(b.modmask, b.key),
                chord: chordKeys(b.modmask, b.key),
                modmask: b.modmask, key: b.key, group: actionGroup(text),
                explanation: meta ? meta.action : findExplanation(b.dispatcher, b.arg),
                rationale: meta ? meta.why : "", mnemonic: meta ? meta.mnemonic : "",
                unlabeled: !!b.unlabeled })
  }

  for (var i = 0; i < binds.length; i++) {
    var b = binds[i]
    if (b.key === "" && b.description !== "")
      b.key = commands.keyFor[b.modmask + "," + b.description] || ""
    if (b.dispatcher === "__lua") {
      if (b.description === "") { b.description = "Unlabeled compositor binding"; b.unlabeled = true; b.dispatcher = ""; b.arg = ""; add(b); continue }
      var found = commands.byKey[b.modmask + "," + b.description + "," + b.key]
      b.dispatcher = found ? found.dispatcher : ""
      b.arg = found ? found.arg : ""
    }
    if (b.key === "code:201") continue  // the Copilot key repeats another binding
    add(b)
  }
  if (includeStatic) for (var s = 0; s < STATIC_ROWS.length; s++) add(STATIC_ROWS[s])

  rows.sort(function (a, b) {
    return naturalCompare(a.does, b.does) || naturalCompare(a.combo, b.combo) ||
           (a.display < b.display ? -1 : a.display > b.display ? 1 : 0)
  })
  return rows
}

function records(bindingsText, commandsText) {
  return explorerRecords(bindingsText, commandsText, true).filter(function (r) { return !r.unlabeled }).map(function (r) {
    return { display: r.display, dispatcher: r.dispatcher, arg: r.arg }
  })
}

// Filters combine with search. A multi-modifier chord appears in each
// applicable modifier filter; plain Super means Super alone.
function filterExplorer(rows, modifier, query) {
  var words = String(query || "").toLowerCase().trim().split(/\s+/).filter(Boolean)
  return rows.filter(function (row) {
    var mask = row.modmask
    if (modifier === "super" && mask !== 64) return false
    if (modifier === "alt" && (mask & 72) !== 72) return false
    if (modifier === "ctrl" && (mask & 68) !== 68) return false
    if (modifier === "shift" && (mask & 65) !== 65) return false
    var haystack = [row.combo, row.does, row.dispatcher, row.arg, row.group, row.explanation, row.rationale, row.mnemonic].join(" ").toLowerCase()
    return words.every(function (word) { return haystack.indexOf(word) !== -1 })
  })
}

function sortExplorer(rows, order) {
  return rows.slice().sort(function(a, b) {
    if (order === "key") return naturalCompare(keyLabel(a.key), keyLabel(b.key)) ||
      a.modmask - b.modmask || naturalCompare(a.does, b.does)
    return naturalCompare(a.does, b.does) || naturalCompare(a.combo, b.combo)
  })
}

// A quick scan of the common Super chords, plus every other reported chord.
// Keys use the same US-layout labels as the rest of the explorer.
function availabilityKeyLabel(key) {
  var symbols = { BRACKETLEFT: "[", BRACKETRIGHT: "]", BACKSLASH: "\\", SLASH: "/",
                  MINUS: "-", EQUAL: "=", GRAVE: "`", PRINT: "PrtSc" }
  return symbols[key] || key
}

function availability(rows) {
  var keys = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").concat(
    ["GRAVE", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
     "MINUS", "EQUAL", "BRACKETLEFT", "BRACKETRIGHT", "BACKSLASH",
     "COMMA", "PERIOD", "SLASH", "SPACE", "RETURN", "BACKSPACE",
     "HOME", "END", "DELETE", "PAGE_UP", "PAGE_DOWN", "UP", "LEFT", "DOWN", "RIGHT"])
  var aliases = { PRIOR: "PAGE_UP", NEXT: "PAGE_DOWN", PAGEUP: "PAGE_UP", PAGEDOWN: "PAGE_DOWN",
                  GRAVE: "GRAVE", LESS: "COMMA", GREATER: "PERIOD" }
  var masks = [64, 72, 68, 65], cells = {}, other = []
  rows.forEach(function(row) {
    var key = String(keyLabel(row.key)).toUpperCase()
    key = aliases[key] || key
    if (masks.indexOf(row.modmask) < 0 || !key) { other.push(row); return }
    if (keys.indexOf(key) < 0) keys.push(key)
    var id = row.modmask + ":" + key
    if (!cells[id]) cells[id] = []
    if (cells[id].indexOf(row.does) < 0) cells[id].push(row.does)
  })
  return { rows: keys.map(function(key) {
    return { key: key, label: availabilityKeyLabel(key), cells: masks.map(function(mask) { return (cells[mask + ":" + key] || []).join("; ") }) }
  }), other: other }
}

// The native scan code follows XKB's evdev+8 convention. Compare both the
// key symbol and code form so configured physical-key bindings still match.
function capturedBindings(rows, modmask, key, nativeScanCode) {
  var symbol = String(key || "").toUpperCase()
  var code = "code:" + String(Number(nativeScanCode) || 0)
  return rows.filter(function (row) {
    return row.modmask === modmask &&
      (String(row.key).toUpperCase() === symbol || String(row.key).toLowerCase() === code)
  })
}

// One "display<TAB>dispatcher<TAB>arg" line per row, each ending in "\n".
function formatRecords(rows) {
  var out = ""
  for (var i = 0; i < rows.length; i++)
    out += rows[i].display + "\t" + rows[i].dispatcher + "\t" + rows[i].arg + "\n"
  return out
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    parseBinds: parseBinds,
    parseCommands: parseCommands,
    modsText: modsText,
    keyLabel: keyLabel,
    comboText: comboText,
    chordKeys: chordKeys,
    actionText: actionText,
    naturalCompare: naturalCompare,
    records: records,
    explorerRecords: explorerRecords,
    bindingMetadata: bindingMetadata,
    parseCatalog: parseCatalog,
    filterExplorer: filterExplorer,
    sortExplorer: sortExplorer,
    capturedBindings: capturedBindings,
    availability: availability,
    availabilityKeyLabel: availabilityKeyLabel,
    formatRecords: formatRecords,
    KEYCODE_NAMES: KEYCODE_NAMES,
    APP_VERSION: APP_VERSION,
    version: APP_VERSION
  }
}
