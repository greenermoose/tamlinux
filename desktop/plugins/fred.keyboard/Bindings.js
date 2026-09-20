.pragma library

// Keycode-space bridge (plan section 4a). Three code spaces have to line up,
// and they meet here and nowhere else:
//
//   evdev   Linux input-event-codes - what layouts/*.json carry as `code`
//   native  KeyEvent.nativeScanCode as QML reports it: evdev + 8 (the X11
//           convention, which Qt keeps on Wayland)
//   keysym  the names `hyprctl -j binds` uses ("K", "XF86AudioRaiseVolume");
//           parsing those is the next milestone and belongs in this file too
//
// Everything here is pure so it can be unit-tested from Node.

var NATIVE_OFFSET = 8

function evdevFromNative(nativeScanCode) {
  var n = Number(nativeScanCode)
  if (!isFinite(n) || n < NATIVE_OFFSET) return null
  return n - NATIVE_OFFSET
}

// Modifier keys by evdev code, named the way Hyprland spells them in a bind.
var MODIFIERS = {
  125: "Super", 126: "Super",
  29: "Ctrl",   97: "Ctrl",
  56: "Alt",    100: "Alt",
  42: "Shift",  54: "Shift"
}

var MODIFIER_ORDER = ["Super", "Ctrl", "Alt", "Shift"]

// Names for keys whose keycap legend does not work in a sentence, keyed by
// layout cell id: a blank space bar, and keypad keys whose caps repeat the
// number row's legends.
var SPOKEN_NAMES = {
  SPACE: "Space Bar",
  KP0: "Num 0", KP1: "Num 1", KP2: "Num 2", KP3: "Num 3", KP4: "Num 4",
  KP5: "Num 5", KP6: "Num 6", KP7: "Num 7", KP8: "Num 8", KP9: "Num 9",
  KPDOT: "Num .", KPENTER: "Num Enter", KPPLUS: "Num +", KPMINUS: "Num -",
  KPASTERISK: "Num *", KPSLASH: "Num /"
}

// Names for evdev codes a bind may target that the board does not place, so
// an orphan bind reads as "F23" rather than "code:201".
var EVDEV_NAMES = {
  113: "Mute", 114: "Volume Down", 115: "Volume Up", 163: "Next Track",
  164: "Play/Pause", 165: "Previous Track", 166: "Stop", 224: "Brightness Down",
  225: "Brightness Up"
}
for (var fn = 13; fn <= 24; fn++) EVDEV_NAMES[170 + fn] = "F" + fn   // KEY_F13 = 183

// What to call a layout cell in the chord readout: a spoken name where the
// keycap legend misleads, else the legend, else the cell id.
function cellName(cell) {
  if (!cell) return ""
  if (Object.prototype.hasOwnProperty.call(SPOKEN_NAMES, cell.id)) return SPOKEN_NAMES[cell.id]
  if (cell.label !== undefined && cell.label !== "") return cell.label
  return cell.id
}

// What to call an evdev code with no cell: a known name, else "#<code>".
function codeName(code) {
  if (Object.prototype.hasOwnProperty.call(EVDEV_NAMES, code)) return EVDEV_NAMES[code]
  return "#" + code
}

function isModifier(code) {
  return Object.prototype.hasOwnProperty.call(MODIFIERS, code)
}

// Human-readable label for a set of held keys: modifiers first in Hyprland's
// customary order, then the other keys by their keycap label.
//
//   pressed  object used as a set of evdev codes ({ 125: true, 37: true })
//   byCode   evdev code -> layout cell, from KeyboardModel.byCode(layout)
//
// A code with no cell on the resolved layout is shown as "#<code>" so a key
// the layout does not know about is visible rather than silently dropped -
// that is how a layout file gets corrected.
function comboLabel(pressed, byCode) {
  var mods = [], keys = []
  var seen = {}
  for (var k in pressed) {
    if (!Object.prototype.hasOwnProperty.call(pressed, k) || !pressed[k]) continue
    var code = Number(k)
    if (isModifier(code)) {
      var name = MODIFIERS[code]
      if (!seen[name]) { seen[name] = true; mods.push(name) }
    } else {
      var cell = byCode ? byCode[code] : undefined
      keys.push({ code: code, label: cell ? cellName(cell) : codeName(code) })
    }
  }
  mods.sort(function (a, b) { return MODIFIER_ORDER.indexOf(a) - MODIFIER_ORDER.indexOf(b) })
  keys.sort(function (a, b) { return a.code - b.code })
  return mods.concat(keys.map(function (x) { return x.label })).join(" + ")
}

// --- Hyprland binds ---------------------------------------------------------
//
// `hyprctl binds` reports each bind with a modifier bitmask and the key as an
// xkb keysym name spelled however the config spelled it ("Delete", "DELETE",
// "comma"). Hyprland compares keysyms case-insensitively; so do we.
//
// The plain-text form is read, not `-j`: on Hyprland 0.56.2 the JSON drops
// the key of every `code:N` bind (key "", keycode 0), and Fred's digit-row
// binds are all `code:N`. The text form keeps them as "SUPER + code:10". A
// JSON array is still accepted for callers that have one.

var MODMASK = { Shift: 1, Caps: 2, Ctrl: 4, Alt: 8, Mod2: 16, Mod3: 32, Super: 64, Mod5: 128 }

// Bitmask of the modifiers held in a pressed set.
function modmaskFromPressed(pressed) {
  var mask = 0
  for (var k in pressed) {
    if (!Object.prototype.hasOwnProperty.call(pressed, k) || !pressed[k]) continue
    var name = MODIFIERS[Number(k)]
    if (name) mask |= MODMASK[name]
  }
  return mask
}

// Modifier names for a mask, in the same order comboLabel uses. Lock bits
// (Caps, Mod2 = Num Lock) are not modifiers a user holds and are ignored.
function modmaskNames(mask) {
  var out = []
  for (var i = 0; i < MODIFIER_ORDER.length; i++)
    if (mask & MODMASK[MODIFIER_ORDER[i]]) out.push(MODIFIER_ORDER[i])
  return out
}

// xkb keysym name (lower-cased) -> layout cell id, for the US keymap. Letters
// and digits map to themselves. Shifted symbols map to the cap that carries
// them, because a bind on "less" is pressed on the comma key.
var KEYSYM_CELLS = {
  "return": "ENTER", "escape": "ESC", "space": "SPACE", "tab": "TAB",
  "backspace": "BACKSPACE", "delete": "DELETE", "insert": "INSERT",
  "home": "HOME", "end": "END", "prior": "PAGEUP", "page_up": "PAGEUP",
  "next": "PAGEDOWN", "page_down": "PAGEDOWN",
  "up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT",
  "print": "SYSRQ", "sys_req": "SYSRQ", "scroll_lock": "SCROLLLOCK",
  "pause": "PAUSE", "break": "PAUSE", "menu": "COMPOSE",
  "caps_lock": "CAPSLOCK", "num_lock": "NUMLOCK",
  "grave": "GRAVE", "asciitilde": "GRAVE",
  "minus": "MINUS", "underscore": "MINUS", "equal": "EQUAL", "plus": "EQUAL",
  "bracketleft": "BRACKETLEFT", "braceleft": "BRACKETLEFT",
  "bracketright": "BRACKETRIGHT", "braceright": "BRACKETRIGHT",
  "backslash": "BACKSLASH", "bar": "BACKSLASH",
  "semicolon": "SEMICOLON", "colon": "SEMICOLON",
  "apostrophe": "APOSTROPHE", "quotedbl": "APOSTROPHE",
  "comma": "COMMA", "less": "COMMA", "period": "PERIOD", "greater": "PERIOD",
  "slash": "SLASH", "question": "SLASH",
  "exclam": "1", "at": "2", "numbersign": "3", "dollar": "4", "percent": "5",
  "asciicircum": "6", "ampersand": "7", "asterisk": "8",
  "parenleft": "9", "parenright": "0",
  "kp_enter": "KPENTER", "kp_add": "KPPLUS", "kp_subtract": "KPMINUS",
  "kp_multiply": "KPASTERISK", "kp_divide": "KPSLASH", "kp_decimal": "KPDOT",
  "kp_delete": "KPDOT", "kp_insert": "KP0", "kp_end": "KP1", "kp_down": "KP2",
  "kp_next": "KP3", "kp_left": "KP4", "kp_begin": "KP5", "kp_right": "KP6",
  "kp_home": "KP7", "kp_up": "KP8", "kp_prior": "KP9",
  "super_l": "LEFTMETA", "super_r": "RIGHTMETA", "shift_l": "LEFTSHIFT",
  "shift_r": "RIGHTSHIFT", "control_l": "LEFTCTRL", "control_r": "RIGHTCTRL",
  "alt_l": "LEFTALT", "alt_r": "RIGHTALT"
}

function keysymToCellId(keysym) {
  var k = String(keysym || "").toLowerCase()
  if (k === "") return null
  if (/^[a-z0-9]$/.test(k)) return k.toUpperCase()
  if (/^f([1-9]|1[0-9]|2[0-4])$/.test(k)) return k.toUpperCase()
  if (/^kp_[0-9]$/.test(k)) return "KP" + k.charAt(3)
  if (Object.prototype.hasOwnProperty.call(KEYSYM_CELLS, k)) return KEYSYM_CELLS[k]
  return null
}

// What kind of input a bind's `key` names. "key" and "keycode" binds belong
// on a keyboard model; the rest are neither placed nor orphaned.
function bindKind(key) {
  var k = String(key || "")
  if (k === "") return "none"
  if (/^mouse[:_]/.test(k)) return "mouse"
  if (/^switch:/.test(k)) return "switch"
  if (/^code:\d+$/.test(k)) return "keycode"
  return "key"
}

// The text form writes a keycode bind's key as "SUPER + ALT + code:10": the
// modifiers ride along in the string. The key proper is the last term.
function keyTerm(key) {
  var parts = String(key || "").split("+")
  return parts[parts.length - 1].trim()
}

// X11 keycode named by a `code:N` key, as evdev; null for anything else.
function keycodeToEvdev(key) {
  var m = /^code:(\d+)$/.exec(String(key || ""))
  return m ? evdevFromNative(Number(m[1])) : null
}

// --- Mouse ------------------------------------------------------------------
//
// Hyprland names pointer input the way its binds spell it: "mouse:<BTN code>"
// for buttons (Linux input-event-codes: BTN_LEFT 272 ...), and mouse_up /
// mouse_down / mouse_left / mouse_right for the wheel. The inhibitor covers
// these too (KeybindManager::onMouseEvent and onAxisEvent both go through
// handleKeybinds), so in capture mode they reach the panel like keys do.

// Qt.MouseButton value -> Hyprland key name.
var MOUSE_BUTTONS = {
  1: "mouse:272",    // Qt.LeftButton      BTN_LEFT
  2: "mouse:273",    // Qt.RightButton     BTN_RIGHT
  4: "mouse:274",    // Qt.MiddleButton    BTN_MIDDLE
  8: "mouse:275",    // Qt.BackButton      BTN_SIDE
  16: "mouse:276"    // Qt.ForwardButton   BTN_EXTRA
}

var MOUSE_NAMES = {
  "mouse:272": "Left Click", "mouse:273": "Right Click", "mouse:274": "Middle Click",
  "mouse:275": "Back Click", "mouse:276": "Forward Click",
  "mouse_down": "Scroll Down", "mouse_up": "Scroll Up",
  "mouse_left": "Scroll Left", "mouse_right": "Scroll Right"
}

function mouseButtonKey(qtButton) {
  var b = Number(qtButton)
  return Object.prototype.hasOwnProperty.call(MOUSE_BUTTONS, b) ? MOUSE_BUTTONS[b] : null
}

// Wheel step -> Hyprland key name. Qt's angleDelta is positive when the wheel
// rolls away from the user (up) or to the left; Hyprland's onAxisEvent calls
// a positive Wayland delta "mouse_down", which is the same gesture.
function wheelKey(dx, dy) {
  if (dy) return dy < 0 ? "mouse_down" : "mouse_up"
  if (dx) return dx > 0 ? "mouse_left" : "mouse_right"
  return null
}

function mouseName(key) {
  var k = String(key || "").toLowerCase()
  return Object.prototype.hasOwnProperty.call(MOUSE_NAMES, k) ? MOUSE_NAMES[k] : key
}

// Label for held modifiers plus a mouse action: "Super + Right Click".
function mouseLabel(pressed, mouseKey) {
  return modmaskNames(modmaskFromPressed(pressed)).concat([mouseName(mouseKey)]).join(" + ")
}

// Bounds on what we accept from hyprctl. A bind list is a few tens of KB;
// anything past these is not a bind list.
var MAX_BINDS_TEXT = 4 * 1024 * 1024
var MAX_BINDS = 4096
var MAX_FIELD = 512

function clip(v) {
  var s = v === undefined || v === null ? "" : String(v)
  return s.length > MAX_FIELD ? s.substring(0, MAX_FIELD) : s
}

// One bind record from raw fields, whichever form they came in.
function makeBind(f) {
  var key = keyTerm(clip(f.key))
  var kind = bindKind(key)
  return {
    modmask: (Number(f.modmask) || 0) & 0xff,
    key: key,
    kind: kind,
    cellId: kind === "key" ? keysymToCellId(key) : null,
    code: kind === "keycode" ? keycodeToEvdev(key) : null,
    description: clip(f.description),
    dispatcher: clip(f.dispatcher),
    arg: clip(f.arg),
    submap: clip(f.submap)
  }
}

// Text records look like:
//
//   bindd
//   \tmodmask: 64
//   \tsubmap:
//   \tkey: K
//   \tkeycode: 0
//   \tcatchall: false
//   \tdescription: Keybindings
//   \tdispatcher: __lua
//   \targ: 74
//
// A line without a leading tab starts a new record.
function parseBindsText(s) {
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
    var m = /^\t([a-z_]+):\s?(.*)$/.exec(line)
    if (m) cur[m[1]] = m[2]
  }
  if (cur && out.length < MAX_BINDS) out.push(makeBind(cur))
  return out
}

function parseBindsJson(s) {
  var raw
  try { raw = JSON.parse(s) } catch (e) { return [] }
  if (!Array.isArray(raw)) return []
  var out = []
  for (var i = 0; i < raw.length && out.length < MAX_BINDS; i++)
    if (raw[i] && typeof raw[i] === "object") out.push(makeBind(raw[i]))
  return out
}

// Parse `hyprctl binds` output (text, or a JSON array) into plain records.
// Never throws: bad or oversized input yields an empty list.
function parseBinds(text) {
  var s = String(text || "")
  if (s.length === 0 || s.length > MAX_BINDS_TEXT) return []
  return s.charAt(0) === "[" ? parseBindsJson(s) : parseBindsText(s)
}

// What a bind does, in words: its description, or the raw dispatcher when
// the config gave none.
function describe(bind) {
  if (!bind) return ""
  if (bind.description) return bind.description
  return (bind.dispatcher + " " + bind.arg).trim()
}

// Join binds to a layout. Returns:
//   byCode   evdev code -> [bind, ...] for keys the layout places
//   byMouse  Hyprland mouse key name -> [bind, ...]
//   orphans  keyboard binds whose key has no cell on this layout
//   other    count of switch / empty binds
function indexBinds(binds, byId) {
  var byCode = {}, byMouse = {}, orphans = [], other = 0
  var placedCodes = {}
  for (var id in byId)
    if (Object.prototype.hasOwnProperty.call(byId, id) && byId[id].code !== null &&
        byId[id].code !== undefined && !byId[id].led)
      placedCodes[byId[id].code] = byId[id]
  for (var i = 0; i < binds.length; i++) {
    var b = binds[i]
    var code = null
    if (b.kind === "key") {
      var cell = b.cellId && byId ? byId[b.cellId] : undefined
      if (cell && cell.code !== null && cell.code !== undefined) code = cell.code
    } else if (b.kind === "keycode") {
      if (b.code !== null && placedCodes[b.code]) code = b.code
    } else if (b.kind === "mouse") {
      var mk = b.key.toLowerCase()
      if (!byMouse[mk]) byMouse[mk] = []
      byMouse[mk].push(b)
      continue
    } else { other++; continue }
    if (code === null) { orphans.push(b); continue }
    if (!byCode[code]) byCode[code] = []
    byCode[code].push(b)
  }
  return { byCode: byCode, byMouse: byMouse, orphans: orphans, other: other }
}

// evdev code -> number of binds on that key with any modifiers. What the
// board tints.
function boundCounts(index) {
  var out = {}
  for (var code in index.byCode)
    if (Object.prototype.hasOwnProperty.call(index.byCode, code)) out[code] = index.byCode[code].length
  return out
}

// The binds a pressed set would fire: exactly one non-modifier key held,
// and its modmask equal to the held modifiers. Returns [] otherwise.
function lookup(index, pressed) {
  var keys = []
  for (var k in pressed) {
    if (!Object.prototype.hasOwnProperty.call(pressed, k) || !pressed[k]) continue
    var code = Number(k)
    if (!isModifier(code)) keys.push(code)
  }
  if (keys.length !== 1) return []
  var mask = modmaskFromPressed(pressed)
  var cands = index && index.byCode ? index.byCode[keys[0]] || [] : []
  var out = []
  for (var i = 0; i < cands.length; i++) if (cands[i].modmask === mask) out.push(cands[i])
  return out
}

// The binds a mouse action would fire with the given keys held: no
// non-modifier key down, and the modmask equal to the held modifiers.
function lookupMouse(index, pressed, mouseKey) {
  for (var k in pressed)
    if (Object.prototype.hasOwnProperty.call(pressed, k) && pressed[k] && !isModifier(Number(k)))
      return []
  var mask = modmaskFromPressed(pressed)
  var cands = index && index.byMouse ? index.byMouse[String(mouseKey || "").toLowerCase()] || [] : []
  var out = []
  for (var i = 0; i < cands.length; i++) if (cands[i].modmask === mask) out.push(cands[i])
  return out
}

// Label for a bind as a chord, e.g. "Super + Shift + K".
function bindLabel(bind, byId, byCode) {
  var cell
  if (bind.kind === "keycode") cell = byCode && bind.code !== null ? byCode[bind.code] : undefined
  else cell = bind.cellId && byId ? byId[bind.cellId] : undefined
  var name = cell ? cellName(cell)
                  : bind.kind === "keycode" && bind.code !== null ? codeName(bind.code)
                  : bind.kind === "mouse" ? mouseName(bind.key)
                  : bind.key
  return modmaskNames(bind.modmask).concat([name]).join(" + ")
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    NATIVE_OFFSET: NATIVE_OFFSET,
    MODIFIERS: MODIFIERS,
    evdevFromNative: evdevFromNative,
    isModifier: isModifier,
    cellName: cellName,
    codeName: codeName,
    comboLabel: comboLabel,
    MODMASK: MODMASK,
    modmaskFromPressed: modmaskFromPressed,
    modmaskNames: modmaskNames,
    keysymToCellId: keysymToCellId,
    bindKind: bindKind,
    keyTerm: keyTerm,
    keycodeToEvdev: keycodeToEvdev,
    parseBinds: parseBinds,
    describe: describe,
    indexBinds: indexBinds,
    boundCounts: boundCounts,
    lookup: lookup,
    mouseButtonKey: mouseButtonKey,
    wheelKey: wheelKey,
    mouseName: mouseName,
    mouseLabel: mouseLabel,
    lookupMouse: lookupMouse,
    bindLabel: bindLabel
  }
}
