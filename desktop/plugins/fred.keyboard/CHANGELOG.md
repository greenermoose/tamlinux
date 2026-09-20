# Changelog

All notable changes to `fred.keyboard` are documented here.
Format follows Keep a Changelog; this project uses SemVer.

## [1.0.0] - 2026-09-20

First release. Everything below was built and tested on Fred's workstation
between 2026-09-19 and 2026-09-20 as the 0.x pre-releases listed after this
section; 1.0.0 is 0.3.6 with the README and screenshots brought up to date.

### Added
- A model of the attached keyboard, drawn from a field-observed layout when
  one exists for the board (Lenovo Calliope ships) and from the OS XKB
  geometries otherwise, with the resolution reported honestly as exact or
  stand-in. Keys light as they are pressed; Caps and Num Lock come from the
  real hardware LEDs in sysfs.
- Capture mode: a `keyboard-shortcuts-inhibit` request tied to the panel
  window, off by default. While on, every Hyprland bind - keys, mouse
  buttons and wheel - reaches the panel instead of running, so any
  combination can be inspected. Esc ends it; closing the panel resets it.
- Binding overlay from `hyprctl binds`: bound keys tinted, a hover on any key
  listing its evdev code and every bind on it, and a "Pressed: ... / Runs:
  ..." readout for the chord or click just made. Modifier keys report how
  many binds they are held in.
- Reverse lookup: search a command and see the chords that run it, marked on
  the board.
- Orphan binds - keys this keyboard cannot send - listed in a collapsible
  section rather than dropped.
- The panel stays open while apps on other monitors are used
  (`ExplorerPanel.qml`, cloned from the stock panel window, see
  `UPSTREAM.md`).
- Bar tooltip naming the keyboard, its bus and keymap; a clickable version
  footer.

### Security
- Panel-scoped capture only: keys are read through QML handlers while the
  panel holds keyboard focus. No `/dev/input`, no `input` group, no
  background process, nothing typed elsewhere is visible.
- Every child process runs through one closed-environment launcher with a
  deadline; no shell is ever spawned. `hyprctl` output is bounded before it
  is parsed. The only URL opened is a fixed constant via `xdg-open`.

## [0.3.6] - Unreleased

### Fixed
- The expanded orphan-bind list pushed the panel's content past the card's
  bottom edge. The list now gets exactly the room left after everything else
  in the panel, so the column never exceeds the card; the card itself may use
  whatever height the screen allows.

## [0.3.5] - Unreleased

### Changed
- Search results and the orphan-bind list are laid out in two columns
  (`BindList.qml`, shared by both), so far fewer entries need scrolling.
- When a list does overflow, a scroll indicator appears at its right edge and
  the caption says "Scroll the list with the mouse wheel."

## [0.3.4] - Unreleased

### Changed
- Capture mode is one box: title with its state ("Capture mode - ON"),
  description, the switch, and - while the mode is live - the notice inside
  the same box. The box takes the accent border and fill while live, the
  switch dims, and the notice says that clicking the switch is recorded too:
  press Esc to exit capture mode, click outside the panel to exit the plugin.
- An Esc hint at the top right of the panel: "Press Esc to close", becoming
  "Esc to exit capture mode" while the mode is on. The old "Escape closes."
  at the bottom is gone.

## [0.3.3] - Unreleased

### Changed
- Modifier keys (Super, Ctrl, Alt, Shift) no longer hover as "No Hyprland
  binds": a modifier never carries a bind of its own but is held in other
  keys' binds, and the hover now says how many. Non-modifier keys with no
  binds still say so.
- The Fn sentence moved from the Layout line to the capture-mode hint at the
  bottom, keeping the Layout line to the board and its tint.

## [0.3.2] - Unreleased

### Changed
- The version footer is centred, matching the rest of the suite, and clicking
  it opens the plugin's public repository in the browser (`xdg-open` through
  the closed-environment `Launch`, the URL a fixed constant).

## [0.3.1] - Unreleased

### Added
- Hover any key for its name, evdev code and every Hyprland bind on it, one
  "chord - what it does" line per bind (`Bindings.keyTooltip`, stock
  `PanelToolTip`). Unbound keys say "No Hyprland binds"; Fn says why it can
  never have any.
- A version footer at the bottom of the panel.

### Changed
- The tint legend ("tinted keys have Hyprland binds", the Fn ring) moved up
  to the Layout line, where the board it describes is, out of the capture
  mode hint at the bottom.

## [0.3.0] - Unreleased

### Added
- Reverse lookup (M6, `SearchView.qml`): type part of a command ("volume",
  "workspace", or a chord such as "super + k") and the matching binds are
  listed as chord and description, with their keys and modifiers marked on
  the board. Orphan binds are findable but shown muted. Escape clears the
  query, then returns focus to the live board. `Bindings.searchBinds` and
  `markedCodes` are pure and unit-tested.

### Changed
- Search and capture mode are modes, not neighbours: switching capture on
  takes focus from the field, and while capture is on the field cannot be
  clicked, since every click in the panel is recorded instead.

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
- An extras region for keys the layout does not place, and self-discovery of
  unknown keys in capture mode.
