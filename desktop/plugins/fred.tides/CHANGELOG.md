# Changelog

All notable changes to `fred.tides` in `tamlinux/desktop/plugins/fred.tides` are documented here.

The 2.x line ships with Tamlinux. Headings identify the containing product release or candidate; inclusion dates do not imply standalone plugin releases. The 1.x entries below are historical Omarchy releases.

## [2.0.2] - Tamlinux 0.4.2-a/b candidate

- Use the shared host hover surface and reusable panel version footer.

## [2.0.1] - Included in Tamlinux 0.4.1 - 2026-10-09

- Move non-theme storage to XDG Tamlinux paths and remove legacy helper fallbacks.

## [2.0.0] - Included in Tamlinux 0.4.1 - 2026-10-09

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
