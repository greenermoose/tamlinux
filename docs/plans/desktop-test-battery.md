# Physical Desktop Test Battery (`tam-desktop-test`)

**Status:** Plan approved by Fred on 2026-11-02; implementation in Develop for candidate 0.6.2.

## Context & Motivation

Manual testing of candidate desktop builds requires the user to execute a repetitive script of UI/UX verification steps: sweeping across bar widgets, opening/closing tooltips and panels, testing Start menu hot corners and mouse gap triggers, exercising multi-monitor workspace sync, dragging/resizing windows, checking PuTTY-style terminal clipboard interoperability, verifying live Micro autoreload, testing keybinding exploration and shortcut capture, and confirming safe window close controls.

`desktop/check-live` verified only internal Quickshell QML states via IPC (`qs ipc`) without emitting real physical Wayland input events or exercising compositor focus, window tiling, terminal paste, or mouse navigation.

`tam-desktop-test` (`desktop/test-battery`) replaces manual questionnaire testing with an automated, watchable physical test battery that:
1. Synthesizes authentic Wayland keyboard, modifier, pointer, click, drag, and scroll events via `zwp_virtual_keyboard_v1` and `zwlr_virtual_pointer_v1`.
2. Compiles and uploads the exact active system XKB keymap (via `libxkbcommon.so.0`), ensuring evdev keycodes, `code:N` bindings, keypad aliases, and modifier masks match physical hardware input.
3. Provides watchable execution at two distinct speeds:
   - **`~0.1s` per intra-workspace step** with smooth 60 ms cursor glides and OSD notifications.
   - **`~0.5s` per multi-monitor workspace transition** to allow multi-display views to settle visually.
4. Protects the user with a **Dual Emergency Stop**:
   - Reserved global keybinding: `Meta + Shift + Escape` (`tam-desktop-test --stop`).
   - Physical mouse grab detection: moving the physical mouse during a run aborts immediately, releases all held buttons and keys, closes test windows, and restores desktop state.
5. Logs all machine-observable assertions to `events.jsonl`, diffs `journalctl` (filtered against benign messages), and produces `summary.md` with a dedicated section for human visual observations.

## Scope & Components

- `tamlinux/desktop/virtual_input.py`: Pure Python/ctypes Wayland virtual keyboard and pointer synthesis library.
- `tamlinux/desktop/test-battery`: 6-phase test choreography runner, safety monitor, and telemetry recorder.
- `tamlinux/commands/tam-desktop-test/`: CLI wrapper with `--stop`, `--speed`, `--phases`, `--workspace`, and `--dry-run` options.
- `tamlinux/desktop/session/hypr/tamlinux/bindings/utilities.lua`: Adds reserved `META + SHIFT + ESCAPE` -> `tam-desktop-test --stop`.
- `tamlinux/desktop/shell/services/keybindings/BindingCatalog.js`: Adds mnemonic explanation for the emergency stop binding.
- `tamlinux/desktop/tests/test_virtual_input.py`: Unit tests for evdev keycode mapping, chords, interpolation, and modifiers.
- `tamlinux/desktop/tests/test_desktop_battery.py`: Unit tests for runner pacing, dry-run execution, and telemetry logging.

## Execution Sequence (The 6 Phases)

1. **Phase 0: Preflight Baseline Snapshot**: Records active workspace, window address, cursor coordinates, clipboard (`CLIPBOARD` and `PRIMARY`), and journal cursor.
2. **Phase 1: Top Bar & Shell Overlays**: Smooth cursor sweep across top bar widgets on awake displays; right-click on unused bar gap to open Start menu; desktop `Meta + RMB` Start trigger; cycling of overlay toggles (emojis, clipboard, reminders).
3. **Phase 2: Multi-Monitor Workspaces (0.5s pace)**: Cycles workspaces `1 -> 2 -> 3 -> 1` and switches to isolated staging Workspace 10.
4. **Phase 3: Keybinding Explorer & Capture Inhibitor**: Opens Explorer (`Meta + K`), types search filter, focuses Shortcut Capture box, verifies capture inhibitor absorbs destructive chords without executing, and dismisses cleanly with `Escape`.
5. **Phase 4: Foot, Micro, TUI Clipboard & Text Macros**: Launches Foot terminal, types text, LMB-drags to copy to PRIMARY, RMB-clicks to paste (`K24`); launches Micro (`Meta + E`), tests live file autoreload (`V11`); tests `Meta + Alt + <key>` macro expansion and universal copy/paste (`Meta + C / Meta + V`).
6. **Phase 5: Tiling, Mouse-Follow & Safe Close Controls**: Spawns second Foot window; tests focus-follows-mouse (`V12`); executes directional swap, punctuation resize chords, appearance toggles (`Meta + U`); tests floating drag; verifies `Meta + W` does not close (`K22`), closes via `Meta + Q` and `Meta + Backspace`.
7. **Phase 6: Restore & Postflight Audit**: Returns to initial workspace at 0.5s pace, restores window focus, cursor coordinates, and clipboard contents; diffs user journal against benign messages; writes `events.jsonl`, `journal.log`, and `summary.md`.
