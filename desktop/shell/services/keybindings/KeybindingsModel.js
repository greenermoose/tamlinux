
// Keybinding viewer rows for the Tamlinux shell. Pure functions over the
// compositor facade's bindingsText (Hyprland `hyprctl binds` text, or the
// Sway adapter's JSON array) and the command table tam-menu-keybindings
// scans from the Lua config. No I/O; Node loads this file for the tests.
//
// The modifier names, key renames, and the two web-app rows are ported from
// omarchy 4.0.4 bin/omarchy-menu-keybindings (MIT, Copyright (c) David
// Heinemeier Hansson; see ../LICENSE-omarchy). The parsing and the order
// are new.

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

// Viewer rows: [{ display, dispatcher, arg }], alphabetical by what the
// binding does, then by its keys. A row whose command the scan could not find keeps an empty
// dispatcher: the viewer shows it but Enter does nothing.
function records(bindingsText, commandsText) {
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
    rows.push({ display: display, dispatcher: b.dispatcher, arg: b.arg,
                does: text, combo: comboText(b.modmask, b.key) })
  }

  for (var i = 0; i < binds.length; i++) {
    var b = binds[i]
    if (b.key === "" && b.description !== "")
      b.key = commands.keyFor[b.modmask + "," + b.description] || ""
    if (b.dispatcher === "__lua") {
      if (b.description === "") continue
      var found = commands.byKey[b.modmask + "," + b.description + "," + b.key]
      b.dispatcher = found ? found.dispatcher : ""
      b.arg = found ? found.arg : ""
    }
    if (b.key === "code:201") continue  // the Copilot key repeats another binding
    add(b)
  }
  for (var s = 0; s < STATIC_ROWS.length; s++) add(STATIC_ROWS[s])

  rows.sort(function (a, b) {
    return naturalCompare(a.does, b.does) || naturalCompare(a.combo, b.combo) ||
           (a.display < b.display ? -1 : a.display > b.display ? 1 : 0)
  })
  return rows.map(function (r) { return { display: r.display, dispatcher: r.dispatcher, arg: r.arg } })
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
    actionText: actionText,
    naturalCompare: naturalCompare,
    records: records,
    formatRecords: formatRecords,
    KEYCODE_NAMES: KEYCODE_NAMES
  }
}
