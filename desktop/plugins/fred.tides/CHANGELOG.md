# Changelog

## [2.0.0] - Unreleased

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.

## [1.0.4] - 2026-09-22

### Fixed

- Right-click notification text now passes as a literal process argument, including shell metacharacters and newlines.
- Notification helper runs with a closed environment and a ten-second watchdog.
