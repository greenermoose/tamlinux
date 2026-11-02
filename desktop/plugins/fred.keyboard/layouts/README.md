# Keyboard layout library

Layouts describe where the keys physically are on a board, so the panel can
draw your keyboard rather than a generic one.

`fred.keyboard` draws a transcribed layout when its USB vendor:product or
device name matches a library entry. Otherwise it draws the bundled
`pc104-standin.json`: a generic ANSI board with navigation keys and a number
pad, with press and release highlighting for its keys. Its positions may
differ from a laptop's physical arrangement.

`../LayoutResolver.js` also discovers OS XKB geometry names, but the renderer
does not read XKB geometry files. An OS geometry name alone cannot supply a
drawable layout. The registry's `standIn` file supplies the board in this
case, including when no OS geometry exists. Only a matched, transcribed
layout is reported as exact.

## Why a field-observed library is necessary

The obvious approach - read the keyboard's declared capabilities and draw
those - does not work. A USB keyboard's HID descriptor advertises the generic
usage table, not its keycaps. Fred's Lenovo Calliope declares **180 keys**,
including `F13`-`F24`, Japanese and Korean IME keys, and Sun-style editing
keys that are not on the board. It also declares `RIGHTMETA` although the
board has no right Super key, while its `Fn` key is **absent** from the
declared set because it is handled in firmware and never reaches the OS.

So: **declared is not present, and present is not always declared.** Only
someone looking at the keyboard can settle it. That is what this library
records.

## Contributing a layout

1. Copy `lenovo-calliope.json` as a starting point.
2. Identify your board:
   ```bash
   grep -A5 'Name=.*[Kk]eyboard' /proc/bus/input/devices
   ```
   The `Vendor=` and `Product=` hex values go in the registry `match` block.
3. Transcribe the keycaps row by row, left to right, exactly as they are -
   including any gap, double-height key, or extra key. Do not normalise it
   toward a standard layout; the whole point is the deviation.
4. Add an entry to `index.json` with your match rules and a short `notes`
   field describing how the board differs from `pc104`.
5. Run the tests:
   ```bash
   node tests/model.test.js
   node tests/resolver.test.js
   ```

## Layout format

```jsonc
{
  "schemaVersion": 1,
  "id": "lenovo-calliope",              // matches the registry entry
  "name": "Lenovo Calliope (space-saving full-size)",
  "source": "field-observed",
  "contributor": "greenermoose",
  "verified": "2026-09-19",
  "mainBlockWidth": 15,                 // alphanumeric block, keycap units
  "firmwareLocal": ["FN"],              // physically present, emits nothing
  "declaredButAbsent": ["RIGHTMETA"],   // declared by HID, not a keycap
  "rows": [ [ /* cells */ ] ]
}
```

### Cell fields

| Field | Meaning |
| :-- | :-- |
| `id` | Stable identifier, upper case (`ESC`, `KP7`, `LEFTSHIFT`). |
| `label` | What is printed on the keycap. |
| `code` | Linux evdev keycode, or `null` if the key emits nothing to the OS. |
| `w` | Keycap widths, default `1`. Backspace is `2`, left Shift `2.25`. |
| `h` | Rows spanned, default `1`. Use `2` for a double-height key. |
| `gap` | Blank space in keycap units **before** this cell. |
| `led` | Indicator name. An LED is drawn, never pressed. |

### Rules

- A cell with `"h": 2` also occupies the row below. **Do not re-declare it**
  in that row; the renderer carries it down and draws it once.
- `gap` separates clusters. On a full-size board the nav cluster starts 1u
  after the 15u main block, and the numpad 1u after the nav cluster's 3u.
- `code` is the **evdev** keycode, not the X11 one. At runtime QML reports
  `nativeScanCode`, which is evdev + 8; the conversion happens in
  `Bindings.js` so the two never mix inside a layout file.
- `mainBlockWidth` must equal the summed width of every row's alphanumeric
  block. The tests enforce this, and it is the quickest way to catch a
  mis-sized modifier.

### Finding evdev keycodes

```bash
grep -E '#define KEY_' /usr/include/linux/input-event-codes.h
```

To see what a specific key emits, `wev` reports Wayland key events, and
`sudo evtest` reads a device node directly. Neither is needed to contribute a
layout if you use the table above.
