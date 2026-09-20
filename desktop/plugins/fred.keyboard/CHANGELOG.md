# Changelog

All notable changes to `fred.keyboard` are documented here.
Format follows Keep a Changelog; this project uses SemVer.

## [0.2.2] - Unreleased

### Changed
- The panel stays open while you use an app on another monitor. The stock
  panel window closes on a click anywhere on any output; `ExplorerPanel.qml`
  is a clone of it (Omarchy 4.0.4-1, MIT, see `UPSTREAM.md`) without the
  click-catchers on other outputs. A click on the panel's own output outside
  the card still closes it. While another window has keyboard focus the
  panel is visible but inert; click the card to bring it back.
- Binds this keyboard cannot send moved to the bottom of the panel as a
  collapsible section (`OrphanBinds.qml`): one summary line that expands into
  aligned "chord - what it does" rows, sorted, scrolling if long. It was a
  single elided line under the readout, unreadable and in the way.

## [0.2.1] - Unreleased

### Added
- Capture mode records mouse actions too: clicks (left, right, middle, back,
  forward) and wheel steps, with the modifiers held, so "Super + Right Click"
  reads out and resolves to its binds ("Resize window; Quick Launch menu").
  Hyprland's inhibitor already covers mouse binds (`onMouseEvent` and
  `onAxisEvent` go through the same inhibited path as keys), so no second
  mechanism was needed.

### Changed
- While capture mode is on, a surface covers the whole card so every click
  inside the panel is recorded rather than acted on, the toggle included.
  Escape is therefore the way out, and the banner now says: press Esc to exit
  capture mode; click anywhere outside the panel to exit the plugin.

## [0.2.0] - Unreleased

### Added
- Binding overlay (M5). The panel reads `hyprctl binds` when it opens, joins
  every bind to the resolved layout, tints the keys that have binds, and
  under "Pressed:" says what the chord runs ("Runs: Keybindings") or that it
  is not bound. Binds whose key this keyboard cannot send (inherited laptop
  keys, F13-F24) are listed as orphans rather than dropped.
- `Bindings.js` grows the Hyprland side of the bridge: modmask bits, keysym
  names to layout cells (including shifted symbols, so a bind on `less` lands
  on the comma key), `code:N` binds to evdev, a bounded parser for the text
  and JSON forms, index, lookup and labels. All unit-tested.
- Spoken names for keypad keys ("Num 1") so they cannot be confused with the
  number row, and names for common unplaced evdev codes ("F23", "Volume Up").

### Changed
- The bind list is read in its text form. On Hyprland 0.56.2 `hyprctl -j
  binds` reports an empty key for every `code:N` bind, which is how the whole
  digit row is bound here; the text form keeps them.

## [0.1.2] - Unreleased

### Fixed
- The chord readout names the space bar "Space Bar" instead of ending in a
  blank, since that keycap carries no legend (`Bindings.cellName`).
- Escape pressed to leave capture mode is now recorded in the readout ("Esc",
  or "Super + Esc") and lights on the board before the mode turns off. With
  capture mode off, Escape still closes the panel.

## [0.1.1] - Unreleased

### Added
- Capture mode (`CaptureMode.qml`): a toggle in the panel, off by default,
  that suspends Hyprland's keybind matching for the panel window through the
  `keyboard-shortcuts-inhibit` protocol while the panel is focused. Bound
  combinations such as Super+K then reach the board instead of running. Escape
  turns it off (a second Escape closes the panel), closing the panel turns it
  off, and a compositor cancel is honoured. An accent banner shows while it is
  in force.
- "Pressed:" readout naming the current chord in Hyprland's modifier order
  ("Super + Shift + K"); a key the layout does not place is shown as `#code`.
- `Bindings.js`: the keycode-space bridge (native scan code to evdev, modifier
  set, chord labels), pure and unit-tested. Plan section 4a.

### Changed
- The native-to-evdev conversion moved out of the key handler into
  `Bindings.js`, as `KeyboardModel.js` always said it should.
- Auto-repeat no longer rewrites the chord readout.

## [0.1.0] - Unreleased

### Added
- Initial plugin scaffold: manifest, GPL-3.0 license, bar widget entry point.
- Bar widget renders the nf-md-keyboard glyph (U+F030C) with a hover tooltip
  placeholder, positioned left of `fred.monitor`.

- Keyboard layout library with two supplies: OS-provided XKB geometries and a
  field-observed library in `layouts/`, resolved per device by
  `LayoutResolver.js` (USB id, then name, then vendor geometry, then generic).
- First field-observed layout: `lenovo-calliope.json`, transcribed from the
  keycaps. Not pc104 - Insert in the function row, double-height Delete, an Fn
  key that emits nothing, no right Super.
- `layouts/README.md` contribution guide for sharing non-standard boards.
- Unit tests for the layout model, double-height key placement, and resolution.

- Device detection (`Device.js`): names the attached physical keyboard, its
  bus and active keymap, filtering the PS/2 stub and fcitx5 virtual keyboard.
- Panel renders the resolved layout with panel-scoped key highlighting.
- Closed-execution process runner (`Launch.qml`) with an env allowlist and
  watchdog; no shell is ever spawned.

- Live Caps Lock / Num Lock indicators read from `/sys/class/leds`, the real
  hardware lamp state. The LED node is derived from the device's own event
  index rather than guessed, and polled only while the panel is open.

### Planned
- Rendering the resolved layout in the panel, with an extras region for keys
  the layout does not place and self-discovery of unknown keys.
- Reverse lookup: command to key combination.
