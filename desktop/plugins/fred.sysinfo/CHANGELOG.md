# Changelog

## [2.0.0] - Unreleased

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
