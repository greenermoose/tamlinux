# Changelog

## [2.0.0] - Unreleased

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.
- The location is read and set through Tamlinux's `tam-weather-location`, by absolute path through `TAMLINUX_BIN` (default `~/.local/bin`), not `omarchy-weather-location` by name. The location file is unchanged.
- The panel's layer is `tamlinux-weather-panel`.
- `tests/test_no_omarchy.py` fails on any `omarchy-*` command or layer name, `/usr/share/omarchy` path, or `OMARCHY_*` variable outside comments, documentation, and tests.

## [1.0.4] - 2026-09-23

### Fixed

- Use the weather location's calendar date for the 10-day forecast, so late
  evening in western timezones does not label tomorrow as Today.
- Filter past daily entries when a cache spans midnight and align current
  high, low, and rain probability with the correct local day.

### Included since the last GitHub Release (v1.0.2)

- Broadcast weather updates across monitor bars, retry daily forecast loading
  after early-wake network errors, and refresh after resume (v1.0.3).
