## Session: 2026-11-06 — Include calculator in Quick Launch and Start menu

- **CLI Tool**: `agy` `1.5.2`
- **Model**: Gemini 3.8 Flash (`gemini-3.8-flash`)
- **Authorship**: AI-assisted, directed by Fred.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > For Tamlinux 0.6.15 include a way to run a calculator easily. I don't see Calculator from Start or Quick Launch. If there is a great graphical calculator app that we should have, make sure it is installed. I want to be able to quick math but also complex things like mortgage rates, IRR, etc. I need easy access to both scientific and financial math functions without having to dig around. Needs to available from the menu that shows with Meta + RMC.

### Work

- Installed `qalculate-gtk` (and `libqalculate`), an open-source graphical GTK calculator supporting quick arithmetic, complete scientific functions, built-in financial formulas (`pmt`, `pv`, `rate`, `nper`), and equation solving for IRR.
- Configured `qalculate-gtk` with keypad, completion, and as-you-type calculation enabled.
- Added `quicklaunch.calculator` (`uwsm-app -- qalculate-gtk`) to `desktop/menu/default.jsonc` and personal menu extension.
- Updated `desktop/session/hypr/tamlinux/bindings/utilities.lua` to route `XF86Calculator` to `uwsm-app -- qalculate-gtk` instead of removed `omacalc`.
- Updated `desktop/shell/services/keybindings/BindingCatalog.js` to match the new `XF86Calculator` binding.
- Added window rules in `desktop/session/hypr/tamlinux/apps/system.lua` to float and center `qalculate-gtk` windows.
- Recorded `tamlinux` candidate inclusion for Tamlinux 0.6.15 via `fred-stage include 0.6.15 tamlinux`.

### Verification

- Verified `qalculate-gtk` and `qalc` installation and evaluated sample mortgage (`pmt(6.5%/12, 360, 300000)`) and IRR equation solving (`solve(..., x)`).
- Ran `tamlinux/desktop/tests/test_start_menu.py`, `test_menu_jsonc.py`, `test_keybinding_defaults.py`, and `test_keybindings.py`: all 69 tests passed.
- Ran `tam-dev check shell`: passed.
