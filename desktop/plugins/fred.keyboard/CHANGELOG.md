# Changelog

All notable changes to `fred.keyboard` are documented here.
Format follows Keep a Changelog; this project uses SemVer.

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
- Capture mode via `zwp_keyboard_shortcuts_inhibit_manager_v1`, letting all
  252 Hyprland binds reach the panel instead of firing.
- Bidirectional lookup: key combination to command, and command to key
  combination.
