# Keyboard Shortcut Visualizer (fred.keyboard)

Part of Fred's `fred.*` plugin suite for [Tamlinux](https://github.com/greenermoose/tamlinux) (Fred's personal Linux workstation environment): a shell bar widget that shows your shortcuts on an interactive keyboard display. Press a combination to see what it runs, or search for a command to see which keys run it.

![The panel: your keyboard drawn from a field-observed layout, bound keys tinted](assets/screenshot.png)

Built for the Tamlinux personal Linux workstation environment (Hyprland +
Quickshell). Version 2.0.5.

## Overview

- **Hover** the bar icon: the attached keyboard's name, bus and active keymap
  ("Lenovo Calliope - English (US) - USB").

  ![Bar tooltip](assets/bar-tooltip.png)
- **Click** it: a panel draws the board. Keys light as you press them; Caps
  and Num Lock show the real hardware LED state. Keys that have Hyprland
  binds are tinted; hover any key for its evdev code and every bind on it.

  ![Hovering the 1 key: evdev 2 and its five binds](assets/hover.png)

- **Press a chord** and the panel reads it back ("Pressed: Meta + K") and
  says what it runs ("Runs: Keybindings"), or that it is not bound.
- **Capture mode** (a switch in the panel, off by default) suspends
  Hyprland's own keybind handling for the panel while it is focused, so bound
  combinations - `Meta+K`, `Super`+right-click, `Super`+wheel - reach the
  board instead of firing. Press Esc to leave it.

  ![Capture mode on: Meta+K read back as "Runs: Keybindings" instead of opening the menu](assets/capture-mode.png)
- **Search** a command ("volume", "workspace", or a chord such as
  "meta + k") and the matching binds are listed with their keys marked on
  the board.

  ![Searching "workspace": ten binds in two columns, their keys outlined on the board](assets/search.png)
- **Binds your keyboard cannot send** - laptop media keys inherited in a
  desktop config, F13-F24 - are listed in a collapsible section rather than
  silently dropped.
- The panel **stays open while you use apps on another monitor**, so you can
  read a bind, try it there, and come back.

## Keyboard layouts

The bundled library includes the physically transcribed Lenovo Calliope
and a reference transcription for the HP 15-f233wm US laptop. The latter
matches its exact system SKU and built-in PS/2 device, and draws the compact
function row, integrated number pad and stacked half-height arrows. Media
actions highlight the corresponding F-key; Fn itself stays firmware-local.
An unknown board uses a generic 104-key diagram. The panel names the source
and distinguishes a reference from a physically confirmed layout. OS XKB
geometry names are discovered but their geometry files are not rendered.
To add a board, see
[`layouts/README.md`](layouts/README.md).

## Key Event Capture

Key capture is panel-scoped: the plugin reads key events only while its own
panel holds keyboard focus, through QML key handlers. The Wayland compositor
routes keystrokes solely to the focused surface, so nothing typed in any other
window is ever visible to this plugin. It does not read `/dev/input`, does not
require `input` group membership, and runs no background process.

Capture mode is an explicit, off-by-default toggle. While it is on, the panel
holds a `zwp_keyboard_shortcuts_inhibit_manager_v1` request for its own
window, which Hyprland honours only while that window is focused. Every key
combination and mouse action then reaches the board instead of running. While
capturing, clicks inside the panel are recorded too, the switch included, so
Esc is the way out; a click anywhere outside the panel closes it. The
inhibitor releases whenever the panel loses focus, and closing the panel
always resets the mode to off.

Everything else the plugin runs goes through one closed-environment launcher
(`Launch.qml`): an absolute executable, an allowlisted environment, a
deadline, and never a shell. It reads `hyprctl devices` and `hyprctl binds`,
lists the XKB geometry directory, and opens one fixed URL (this repository)
with `xdg-open` when the version footer is clicked. Nothing is written to
disk.

## Requirements

Everything the plugin needs is part of a stock Tamlinux installation; there is
nothing to install first.

- **The Tamlinux shell** from the matching package assembly. The bundled 2.x
  widget uses `Tam.Commons` and `Tam.Ui`; the standalone Omarchy 1.x line is frozen.
- **Hyprland** (tested on 0.56.2), for `hyprctl devices` and `hyprctl binds`,
  and for capture mode, which relies on the compositor implementing
  `keyboard-shortcuts-inhibit-unstable-v1`. Hyprland does; capture mode is
  the only feature that would not work on a compositor that does not.
- **Quickshell 0.3.1 or newer** with its Wayland module, as shipped with
  Tamlinux, for the `ShortcutInhibitor` type.
- **`xdg-utils`** (`xdg-open`) for the footer link to this repository, and
  **`xkeyboard-config`** for the OS-supplied keyboard geometries used as
  stand-in layouts. Both are already present on Tamlinux.
- A physical keyboard listed in `/proc/bus/input/devices`. A USB board is
  identified by vendor and product id; without one the panel falls back to
  a generic layout and says so.

Node.js is needed only to run the tests.

## Installation

The 2.x plugin is included in the pinned [Tamlinux package assembly](https://github.com/greenermoose/tamlinux-packages). Its installed payload is at `~/.config/tamlinux/plugins/fred.keyboard/`; install and update it with the assembly through Home Manager. The standalone repository contains the frozen Omarchy 1.x line.

Place `{ "id": "fred.keyboard" }` in a `left`, `center`, or `right` list under `layout` in `~/.config/tamlinux/shell/layout.json`. The document uses `schemaVersion: 1`. Widget settings are the `fred.keyboard` entry under `entries` in `~/.config/tamlinux/shell/settings.json`, whose top-level `version` is `1`.

See [plugin ownership](../README.md) and the [deployment contract](https://github.com/greenermoose/tamlinux-packages/blob/main/docs/deployment.md). Home and XDG paths below use their default locations; the helpers honor the corresponding `XDG_*_HOME` overrides.

## Upstream code

`ExplorerPanel.qml` is cloned from Omarchy's stock `Ui/KeyboardPanel.qml`
(MIT) with the other-monitor click-catchers removed, so the panel can stay
open while you work elsewhere. `UPSTREAM.md` records the version, the diff
recipe and the license notice. Nothing else is copied.

## Prior art

Eight Omarchy plugins explore adjacent ground, and this one was designed
after studying them. Credit where due, all MIT licensed:

- [`dai199/omarchy-visual-keybindings`](https://github.com/dai199/omarchy-visual-keybindings) - interactive keybinding explorer and editor; independently uses the same shortcut-inhibit mechanism
- [`neilerua973/omarchy-keybindings-editor`](https://github.com/neilerua973/omarchy-keybindings-editor) - on-screen keyboard binding editor
- [`felixzsh/omarchy-key-visualizer`](https://github.com/felixzsh/omarchy-key-visualizer) - on-screen key display for screencasts
- [`seth-wood/keyarchy`](https://github.com/seth-wood/keyarchy) - tracks which shortcuts you actually use
- [`fze-fze/omarchy-shortcut-sheet`](https://github.com/fze-fze/omarchy-shortcut-sheet) - tap-Meta shortcut overlay
- [`YonatanBaum/omarchy-app-shortcuts`](https://github.com/YonatanBaum/omarchy-app-shortcuts) - per-application cheat sheet
- [`balazsorban44/omarchy-keyboard-minimap`](https://github.com/balazsorban44/omarchy-keyboard-minimap) - keyboard minimap with global capture via `/dev/input`, the approach this plugin deliberately does not take
- [`balazsorban44/omarchy-keybinding-coach`](https://github.com/balazsorban44/omarchy-keybinding-coach) - one binding at a time in the bar

No code from these projects is used here; `UPSTREAM.md` records what each
one contributed to the design. `fred.keyboard` differs mainly in drawing the
real board from layout data rather than a hardcoded grid, covering the full
key set including keys the board does not have, reporting the keyboard's
identity, and treating capture mode as a deliberate, visible toggle.

## Development

### Independent keyboard trial

To try this widget without rebuilding or activating the desktop, install its
standalone development app from an exact committed revision:

```bash
python3 desktop/plugins/fred.keyboard/dev-trial install HEAD
```

Open **Keyboard (Development)** in the application launcher, or run
`~/.local/dev/bin/tam-keyboard`. It runs the same widget in its own Quickshell
instance, reads the current keyboard and desktop shortcuts, and exits when
its panel closes. The packaged bar widget stays as it is. Capture mode starts
off and is scoped to the trial's focused window. An unknown keyboard uses the
bundled generic board; its exact key positions are not inferred.

The installer archives the selected commit and checks actual key rendering,
press/release highlighting, device detection and shortcut loading before
installing the launcher. Builds live under `~/.local/dev/share/tamlinux/dev-trials/keyboard/`;
the record is `~/.local/state/tamlinux/dev-trials/keyboard.json`. Inspect it
with `python3 desktop/plugins/fred.keyboard/dev-trial status`. After closing
the trial, remove it with:

```bash
~/.local/dev/bin/tam-keyboard --uninstall
```

Removal restores any launcher or desktop entry displaced by the first
installation. The standalone trial is for development feedback; it does not
advance the Tamlinux package's stage.

Tests run with Node and need nothing else:

```bash
for t in tests/*.test.js; do node "$t"; done
```

AI-assisted engineering is disclosed in [`AI_PROVENANCE.md`](AI_PROVENANCE.md)
and the per-session records under `docs/ai/`.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
