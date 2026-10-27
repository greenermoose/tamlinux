# tam-monitor C migration, console framebuffer mapping, and resource measurements

Date: 2026-10-26
Tool: Google Antigravity
Model: Gemini 3.8 Flash

## Summary

Completed the C migration of `tam-monitor`, actual console framebuffer mapping, individual
wake, targeted blanking, interactive `keep --shell`, terminal TUI without `ncurses`, and
comparative resource measurements for Tamlinux 0.5.5:

1. **Console framebuffer mapping and verification**:
   - Discovers bound fbcon device from `/sys/class/vtconsole`, resolves fb device via `FBIOGET_CON2FBMAP` or single bound fbcon, and traces device symlinks to the primary backing DRM card (`cardN`).
   - Verifies fbcon dimensions and stride against active DRM framebuffer references via `tam_display_state_verify_console_fb`.

2. **Full C CLI/TUI migration**:
   - Replaced legacy Python `tam-monitor` script (`commands/tam-monitor/tam-monitor` retired).
   - Reimplemented CLI dispatcher in `native.c`, hardware discovery / backlight / DDC in `native-hw.c`, preview / keep / blank / wake / guard in `native-preview.c`, terminal TUI in `native-tui.c`, and uevent hotplug monitor in `native-events.c`.
   - Built with standard ANSI / VT102 escape sequences with `SIGWINCH` resize handling and no `ncurses` runtime dependency.
   - Introduced `SO_PEERCRED`-verified UNIX domain socket for in-session `WAKE`, `BLANK`, `KEEP`, `RESTORE`, and `STOP` commands.

3. **Resource measurements vs Python baseline**:
   - Unstripped binary: 390.6 KiB (includes ~255 KiB debug sections and 78.9 KiB `.text`).
   - Startup latency: `--help` runs in 2.58 ms (32.3x faster than Python 83.36 ms), `list --json --no-probe` runs in 2.87 ms (28.8x faster than Python 82.56 ms).
   - Peak RSS: 10.12 MiB (2.1x lower than Python 21.33 MiB).
   - Active owner + recovery guard combined memory during live `keep --shell` session: combined PSS is 400 KiB (3.61 MiB headroom under the 4.00 MiB review budget).

4. **Test verification**:
   - All 24 tests in `test_monitor.py` passing against compiled C binary.
   - All 21 tests in `native_preview.py` passing including recovery, deadlines, signals, hotplug, `keep --shell`, targeted blank, and individual wake.
   - All 9 tests in `native_cli.py` and `test-native-events` passing.
   - All `libtam` ASan/UBSan unit test suites passing.
