// Unit tests for Bindings.js: the keycode-space bridge (plan section 4a).
// Run: node tests/bindings.test.js
var assert = require("assert")
var load = require("./load.js")
var B = load.loadQmlJs("Bindings.js")

// native -> evdev is a fixed offset of 8; junk never becomes a code.
assert.strictEqual(B.evdevFromNative(45), 37)          // K
assert.strictEqual(B.evdevFromNative(133), 125)        // left Super
assert.strictEqual(B.evdevFromNative(8), 0)
assert.strictEqual(B.evdevFromNative(7), null)
assert.strictEqual(B.evdevFromNative(undefined), null)
assert.strictEqual(B.evdevFromNative("abc"), null)

// Both sides of every modifier pair count, nothing else does.
;[29, 97, 42, 54, 56, 100, 125, 126].forEach(function (c) { assert.ok(B.isModifier(c), c) })
;[1, 37, 28, 57, 105].forEach(function (c) { assert.ok(!B.isModifier(c), c) })

var byCode = { 37: { id: "K", label: "K" }, 28: { id: "ENTER", label: "Enter" },
               16: { id: "Q" },                        // a cell with no label
               57: { id: "SPACE", label: "" },         // a blank keycap
               1: { id: "ESC", label: "Esc" } }

// Modifiers lead in Hyprland's order regardless of the key order given.
assert.strictEqual(B.comboLabel({ 37: true, 42: true, 125: true }, byCode), "Super + Shift + K")
assert.strictEqual(B.comboLabel({ 56: true, 29: true, 125: true, 54: true }, byCode),
                   "Super + Ctrl + Alt + Shift")

// Left and right of the same modifier collapse to one name.
assert.strictEqual(B.comboLabel({ 42: true, 54: true, 37: true }, byCode), "Shift + K")

// Entries set to false are not held; a label falls back to the cell id.
assert.strictEqual(B.comboLabel({ 37: false, 16: true }, byCode), "Q")

// A blank keycap gets its spoken name; the readout never ends in "+ ".
assert.strictEqual(B.cellName(byCode[57]), "Space Bar")
assert.strictEqual(B.comboLabel({ 125: true, 57: true }, byCode), "Super + Space Bar")
assert.strictEqual(B.cellName({ id: "NOLEGEND", label: "" }), "NOLEGEND")

// Escape reads as its keycap, alone or in a chord.
assert.strictEqual(B.comboLabel({ 1: true }, byCode), "Esc")
assert.strictEqual(B.comboLabel({ 125: true, 1: true }, byCode), "Super + Esc")

// A code the layout does not place is shown, not dropped.
assert.strictEqual(B.comboLabel({ 125: true, 999: true }, byCode), "Super + #999")
assert.strictEqual(B.comboLabel({ 37: true }, null), "#37")

// Multiple plain keys sort by code so the label is stable.
assert.strictEqual(B.comboLabel({ 28: true, 37: true }, byCode), "Enter + K")

assert.strictEqual(B.comboLabel({}, byCode), "")

console.log("ok - bindings: native offset, modifier set, combo labels")

// --- Hyprland binds ---------------------------------------------------------
//
// Values come out of a vm sandbox with its own Array/Object prototypes, so
// structural comparison uses deepEqual, never deepStrictEqual.

var fs = require("fs"), path = require("path")
var KM = load.loadQmlJs("KeyboardModel.js")
var layout = JSON.parse(fs.readFileSync(path.resolve(__dirname, "..",
                                                     "layouts", "lenovo-calliope.json"), "utf8"))
var byId = KM.byId(layout), layoutByCode = KM.byCode(layout)

// Modifier masks round-trip: Hyprland's bits are Shift 1, Ctrl 4, Alt 8, Super 64.
assert.strictEqual(B.modmaskFromPressed({ 125: true, 42: true }), 65)
assert.strictEqual(B.modmaskFromPressed({ 29: true, 100: true, 37: true }), 12)
assert.deepEqual(B.modmaskNames(73), ["Super", "Alt", "Shift"])
assert.deepEqual(B.modmaskNames(2), [])          // Caps Lock bit is not held

// Keysym spellings the config uses, case-insensitively, land on the right cap.
assert.strictEqual(B.keysymToCellId("K"), "K")
assert.strictEqual(B.keysymToCellId("k"), "K")
assert.strictEqual(B.keysymToCellId("RETURN"), "ENTER")
assert.strictEqual(B.keysymToCellId("Delete"), "DELETE")
assert.strictEqual(B.keysymToCellId("comma"), "COMMA")
assert.strictEqual(B.keysymToCellId("less"), "COMMA")   // shifted symbol, same cap
assert.strictEqual(B.keysymToCellId("F12"), "F12")
assert.strictEqual(B.keysymToCellId("KP_7"), "KP7")
assert.strictEqual(B.keysymToCellId("XF86AudioMute"), null)
assert.strictEqual(B.keysymToCellId(""), null)

// Kinds: only keys and keycodes belong on a board.
assert.strictEqual(B.bindKind("K"), "key")
assert.strictEqual(B.bindKind("code:10"), "keycode")
assert.strictEqual(B.bindKind("mouse:272"), "mouse")
assert.strictEqual(B.bindKind("mouse_down"), "mouse")
assert.strictEqual(B.bindKind("switch:on:Lid Switch"), "switch")
assert.strictEqual(B.bindKind(""), "none")

// The text form carries modifiers inside a keycode bind's key string.
assert.strictEqual(B.keyTerm("SUPER + ALT + code:10"), "code:10")
assert.strictEqual(B.keyTerm("K"), "K")
assert.strictEqual(B.keycodeToEvdev("code:10"), 2)      // X11 10 -> evdev 2 -> "1"
assert.strictEqual(B.keycodeToEvdev("K"), null)

// A synthetic slice of `hyprctl binds`, both forms.
var text = [
  "bindd", "\tmodmask: 64", "\tsubmap: ", "\tkey: K", "\tkeycode: 0", "\tcatchall: false",
  "\tdescription: Keybindings", "\tdispatcher: __lua", "\targ: 74",
  "bindd", "\tmodmask: 72", "\tsubmap: ", "\tkey: SUPER + ALT + code:10", "\tkeycode: 0",
  "\tcatchall: false", "\tdescription: Switch to group window 1", "\tdispatcher: __lua", "\targ: 225",
  "bindld", "\tmodmask: 0", "\tsubmap: ", "\tkey: XF86AudioMute", "\tkeycode: 0", "\tcatchall: false",
  "\tdescription: Mute", "\tdispatcher: __lua", "\targ: 8",
  "bindd", "\tmodmask: 64", "\tsubmap: ", "\tkey: mouse:272", "\tkeycode: 0", "\tcatchall: false",
  "\tdescription: Move window", "\tdispatcher: movewindow", "\targ: ",
  "bindd", "\tmodmask: 65", "\tsubmap: ", "\tkey: code:201", "\tkeycode: 0", "\tcatchall: false",
  "\tdescription: Omarchy menu", "\tdispatcher: __lua", "\targ: 53",
  "bind", "\tmodmask: 64", "\tsubmap: ", "\tkey: space", "\tkeycode: 0", "\tcatchall: false",
  "\tdescription: ", "\tdispatcher: exec", "\targ: omarchy-menu", ""
].join("\n")

var binds = B.parseBinds(text)
assert.strictEqual(binds.length, 6)
assert.deepEqual(binds.map(function (b) { return b.kind }),
                       ["key", "keycode", "key", "mouse", "keycode", "key"])
assert.strictEqual(binds[1].code, 2)
assert.strictEqual(binds[1].modmask, 72)
assert.strictEqual(B.describe(binds[0]), "Keybindings")
assert.strictEqual(B.describe(binds[5]), "exec omarchy-menu")   // no description: dispatcher

// JSON input is accepted too, and yields the same records.
var json = JSON.stringify([{ modmask: 64, key: "K", description: "Keybindings",
                             dispatcher: "__lua", arg: "74" }])
assert.deepEqual(B.parseBinds(json)[0], binds[0])

// Garbage never throws and never yields records.
assert.deepEqual(B.parseBinds(""), [])
assert.deepEqual(B.parseBinds("[not json"), [])
assert.deepEqual(B.parseBinds("{\"a\":1}"), [])
assert.deepEqual(B.parseBinds("nonsense\nwithout records"), [])

// Index against the Calliope: K and "1" are placed, F23 and the media key are
// orphans, the mouse bind is indexed by its Hyprland name.
var idx = B.indexBinds(binds, byId)
assert.strictEqual(idx.byCode[37].length, 1)
assert.strictEqual(idx.byCode[2].length, 1)
assert.strictEqual(idx.byCode[57].length, 1)
assert.strictEqual(idx.orphans.length, 2)
assert.strictEqual(idx.other, 0)
assert.strictEqual(idx.byMouse["mouse:272"].length, 1)
assert.deepEqual(B.boundCounts(idx), { 2: 1, 37: 1, 57: 1 })

// Lookup needs exactly one non-modifier key and an exact modifier match.
assert.deepEqual(B.lookup(idx, { 125: true, 37: true }).map(B.describe), ["Keybindings"])
assert.deepEqual(B.lookup(idx, { 125: true, 42: true, 37: true }), [])   // Super+Shift+K unbound
assert.deepEqual(B.lookup(idx, { 125: true, 56: true, 2: true }).map(B.describe),
                       ["Switch to group window 1"])
assert.deepEqual(B.lookup(idx, { 125: true }), [])                       // modifiers only
assert.deepEqual(B.lookup(idx, { 125: true, 37: true, 2: true }), [])    // two keys

// Labels for binds, including keycode binds and orphans.
assert.strictEqual(B.bindLabel(binds[0], byId, layoutByCode), "Super + K")
assert.strictEqual(B.bindLabel(binds[1], byId, layoutByCode), "Super + Alt + 1")
assert.strictEqual(B.bindLabel(binds[2], byId, layoutByCode), "XF86AudioMute")
assert.strictEqual(B.bindLabel(binds[4], byId, layoutByCode), "Super + Shift + F23")
assert.strictEqual(B.bindLabel(binds[5], byId, layoutByCode), "Super + Space Bar")

// Mouse: Qt buttons and wheel steps map to Hyprland's names, and a click with
// modifiers held resolves like a chord.
assert.strictEqual(B.mouseButtonKey(2), "mouse:273")        // Qt.RightButton
assert.strictEqual(B.mouseButtonKey(16), "mouse:276")       // Qt.ForwardButton
assert.strictEqual(B.mouseButtonKey(32), null)
assert.strictEqual(B.wheelKey(0, -120), "mouse_down")
assert.strictEqual(B.wheelKey(0, 120), "mouse_up")
assert.strictEqual(B.wheelKey(120, 0), "mouse_left")
assert.strictEqual(B.wheelKey(0, 0), null)
assert.strictEqual(B.mouseName("mouse:273"), "Right Click")
assert.strictEqual(B.mouseName("MOUSE_DOWN"), "Scroll Down")
assert.strictEqual(B.mouseLabel({ 125: true, 42: true }, "mouse:273"), "Super + Shift + Right Click")
assert.strictEqual(B.mouseLabel({}, "mouse_up"), "Scroll Up")
assert.deepEqual(B.lookupMouse(idx, { 125: true }, "mouse:272").map(B.describe), ["Move window"])
assert.deepEqual(B.lookupMouse(idx, { 125: true, 42: true }, "mouse:272"), [])   // wrong mods
assert.deepEqual(B.lookupMouse(idx, { 125: true, 37: true }, "mouse:272"), [])   // a key is down
assert.deepEqual(B.lookupMouse(idx, {}, "mouse:273"), [])
assert.strictEqual(B.bindLabel(binds[3], byId, layoutByCode), "Super + Left Click")

// Keypad keys are named so they cannot be confused with the number row.
assert.strictEqual(B.cellName(byId.KP1), "Num 1")
assert.strictEqual(B.codeName(115), "Volume Up")
assert.strictEqual(B.codeName(999), "#999")

console.log("ok - bindings: hyprctl parse (text + json), index, lookup, labels")
