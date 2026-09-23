# Changelog

All notable changes to `fred.monitor` are documented here.

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
