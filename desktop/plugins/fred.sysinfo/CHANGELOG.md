# Changelog

All notable changes to `fred.sysinfo` in `tamlinux/desktop/plugins/fred.sysinfo` are documented here.

The 2.x line ships with Tamlinux. Headings identify the containing product release or candidate; inclusion dates do not imply standalone plugin releases. The 1.x entries below are historical Omarchy releases.

## [2.0.3] - Tamlinux 0.4.2-c candidate

- Restore accepted Tamlinux settings, state and cache paths in the packaged plugin.

## [2.0.2] - Tamlinux 0.4.2-a/b candidate

- Shared host hover version styling and a reusable panel version footer.

## [2.0.1] - Included in Tamlinux 0.4.1 - 2026-10-09

- Move non-theme storage to XDG Tamlinux paths and remove legacy helper fallbacks.

## [2.0.0] - Included in Tamlinux 0.4.1 - 2026-10-09

### Changed
- The widget loads in the Tamlinux shell through `Tam.Commons` and `Tam.Ui`. It no longer imports the Omarchy shell modules or calls `bar.run`.
- Omarchy shell IPC targets are gone. Hyprland reads that this plugin already had stay in the plugin until the compositor contract.
- The panel's layer is `tamlinux-sysinfo-panel`.
- `tests/test_no_omarchy.py` fails on any `omarchy-*` command or layer name, `/usr/share/omarchy` path, or `OMARCHY_*` variable outside comments, documentation, and tests.

## [1.1.2] - 2026-09-22

### Security

- Move probe caches to a private runtime directory and use descriptor-relative, no-follow atomic writes and checked reads.

### Changed

- The bar hover now shows current CPU usage, available RAM, and free root-disk space.
- Entering the bar icon refreshes telemetry before the hover appears, preventing stale values from the widget's startup probe or previous panel session.
