# Changelog

All notable changes to `fred.monitor` in `tamlinux/desktop/plugins/fred.monitor` are documented here.

The 2.x line ships with Tamlinux. Headings identify the containing product release or candidate; inclusion dates do not imply standalone plugin releases. The 1.x entries below are historical Omarchy releases.

## [2.0.5] - Tamlinux 0.4.2-c candidate

- Restore accepted Tamlinux settings, state and cache paths in the packaged plugin.

## [2.0.4] - Tamlinux 0.4.2-a/b candidate

- Shared host hover version styling and a reusable panel version footer. The displayed version is corrected to match the manifest.

## [2.0.3] - Included in Tamlinux 0.4.1 - 2026-10-09

- Fix empty display panels when another component has created the shared Tamlinux runtime directory with mode 0755. Accept a user-owned parent without group/world write permission, while retaining mode 0700 for monitor cache and preview/rollback state.
- Open and validate runtime directories without following symlinks. Unavailable brightness cache no longer prevents reading displays; unsafe layout transaction storage still fails closed.

## [2.0.2] - Included in Tamlinux 0.4.1 - 2026-10-09

- Move non-theme storage to XDG Tamlinux paths and remove legacy helper fallbacks.

## [2.0.1] - Included in Tamlinux 0.4.1 - 2026-10-09

### Fixed
- Reset/retrain works again. `fred-monitor-reset` ran the Tamlinux backend as `python3 -I hyprland_backend.py`. Isolated mode leaves the script's directory off `sys.path`, so the backend's `import compositor_commands` failed. The helper discarded that error, read no monitors, and reported the display as not connected. It now puts only the backend directory on the path and calls the backend's `main`.
- A failed monitor read now reports `cannot read monitors from the compositor` instead of `not connected`.

### Added
- `tests/test_reset.py` runs the helper against a stand-in backend that imports a sibling module, as the real one does.

## [2.0.0] - Included in Tamlinux 0.4.1 - 2026-10-09

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.
- Text Size runs `tam-display-text-size`, and brightness runs `tam-brightness-display`, both through `TAMLINUX_BIN` (default `~/.local/bin`). Helpers run with `PATH=$TAMLINUX_BIN:/usr/bin` instead of Omarchy's command directory.
- The Text Size slider and its px label show the size `tam-display-text-size` reports, read when the panel opens and after each change. They used to show the shell's own font size, which stays at 12 px until the shell follows Text Size.
- `tests/test_no_omarchy.py` fails on any `omarchy-*` command or layer name, `/usr/share/omarchy` path, or `OMARCHY_*` variable outside comments, documentation, and tests.

## [1.2.3] - 2026-09-23

### Fixed

- The keyboard-help sheet no longer blocks the panel shortcut dispatcher or
  takes keyboard focus. Home now remains a visual, mouse-modal cheat sheet:
  Identify and every other existing shortcut work while it is visible and
  immediately after it is dismissed.

## [1.2.2] - Unreleased

### Added

- A `Home for help` control and Home-key help modal documenting panel keyboard
  navigation, activation, Identify, DPMS, Reset, staged moves, Apply, and
  close shortcuts.

### Changed

- Identify is now a true toggle: its button remains active and its click-through
  monitor labels remain visible until Fred toggles Identify off again.
- Each card header now reads connector, physical diagonal, and monitor model
  before its physical position; compact Move left/Move right controls follow
  the position, and Reset/retrain is at the far right of that header.
- Resolution and Orientation are paired pull-downs; Scale now precedes
  Brightness so the two sliders remain together.
- DPMS is a labelled On/Off toggle reflecting the current state. The repeated
  DPMS fact is removed from the card summary.

## [1.2.1] - Unreleased

### Added

- A first-use Default saved layout, guaranteeing that at least one restorable
  layout is always available.
- An explicit disabled brightness control and explanatory message for monitors
  that genuinely do not expose DDC/CI brightness.

### Changed

- The panel header now names the active monitor count, keeps Identify and the
  alignment pull-down beside the title, and puts `Esc to close` plus an X at
  the upper right.
- Saved-layout deletion is available only while another restorable layout
  remains. Discard is labelled as discarding staged changes and explains that
  it reloads the live arrangement.

### Fixed

- DDC brightness probes are serialized across panel instances, successful
  results are cached longer, and transient read failures retain last-known-good
  support. This prevents the timing-sensitive HP 22cwa from losing its slider.
- Rapid slider movement is coalesced into one guarded hardware write and the
  successful value updates the shared brightness cache.

## [1.2.0] - Unreleased

### Added

- Named saved layouts with secure persistent storage and staged restore.
- Automatic Previous layout and Last saved layout recovery entries after Keep.
- Explanations distinguishing global Text Size from per-monitor Scale.

### Changed

- Cards divide the available panel width evenly and the full panel scrolls
  vertically, keeping every monitor and control reachable.
- Resolution uses a compact pull-down and Scale uses a per-monitor slider.
- Global Text Size now appears once below the monitor cards.
- Card summaries no longer repeat resolution, refresh rate, or scale.

### Removed

- Display enable/disable controls, pending a workspace-safe implementation.

## [1.1.0] - 2026-09-20

### Added

- Monitor-aware hover details for the bar instance under the pointer, with a
  version footnote for at-a-glance build identification.
- Physical left-to-right monitor columns with all controls visible.
- Three-second Identify overlays on every connected display.
- Draft layout editing with top, center, or bottom alignment.
- A 15-second Apply / Keep / Revert safety transaction.
- Persistent layout updates in the managed `monitors.lua` block.

### Changed

- The panel remains open when another monitor receives pointer or keyboard
  input, while same-monitor outside clicks still dismiss it.
- Display state cache files now use a private runtime directory and guarded
  file operations.

## [1.0.0] - 2026-09-14

- Initial deployed display panel with per-monitor details, brightness, scale,
  refresh-rate, DPMS, and display-link reset controls.
