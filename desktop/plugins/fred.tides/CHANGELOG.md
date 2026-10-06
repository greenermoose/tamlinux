# Changelog

## [2.0.0] - Unreleased

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.
- Notifications use Tamlinux's `tam-notification-send`, found through `TAMLINUX_BIN` (default `~/.local/bin`). `OMARCHY_PATH` is no longer read or passed on.
- The panel's layer is `tamlinux-tides-panel`.
- `tests/test_no_omarchy.py` fails on any `omarchy-*` command or layer name, `/usr/share/omarchy` path, or `OMARCHY_*` variable outside comments, documentation, and tests.

## [1.0.4] - 2026-09-22

### Fixed

- Right-click notification text now passes as a literal process argument, including shell metacharacters and newlines.
- Notification helper runs with a closed environment and a ten-second watchdog.
