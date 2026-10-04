# Changelog

## [2.0.0] - Unreleased

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.

## [1.0.4] - 2026-09-23

### Fixed

- Use the weather location's calendar date for the 10-day forecast, so late
  evening in western timezones does not label tomorrow as Today.
- Filter past daily entries when a cache spans midnight and align current
  high, low, and rain probability with the correct local day.

### Included since the last GitHub Release (v1.0.2)

- Broadcast weather updates across monitor bars, retry daily forecast loading
  after early-wake network errors, and refresh after resume (v1.0.3).
