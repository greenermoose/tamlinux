# Bug 0002 — Installing a new version replaces the chosen background

- **Status:** Fix available.
- **Severity:** Medium; every upgrade replaces the background the person
  chose, and they must pick it again.
- **Affected:** `desktop/theme/engine.py` and `commands/tam-deploy` in
  Tamlinux 0.6.27 and 0.6.28 (bundle deliveries). Earlier versions had no
  portable background selection.
- **Fixed:** In source on `develop`; planned for 0.6.29, not yet installed.
- **Next:** Install 0.6.29 over a desktop with a non-default background and
  confirm the same image after `tam-desktop`.

## Reproduce

Synthetic home, Tokyo Night theme, using the installed engine with
`TAMLINUX_THEME_OFFLINE=1` and `HOME`/`XDG_*` pointed at a scratch folder:

1. `engine.py initialize` (creates `current/theme`, five theme images).
2. Copy any `.jpg` into `~/.config/tamlinux/backgrounds/tokyo-night/`.
3. `engine.py bg-set <current/theme/backgrounds/3-sunset-lake.png>`. The link
   and `background.selection` agree (`tokyo-night`, `3-sunset-lake.png`).
4. Make the selection stale: write
   `{"file": "tamarack.png", "format": 1, "kind": "theme", "theme": "tamarack-light"}`
   to `current/background.selection`.
5. `engine.py initialize --sync`, the step `tam-deploy` runs during a bundle
   install (`sync_active_desktop_state`).

The background is now the personal image from step 2, not `3-sunset-lake.png`.
If step 4 is skipped, the chosen image survives two syncs.

## Expected and actual

Expected: the image on screen before the install is the image after it.

Actual: `sync_state()` reads `background.selection` before rebuilding the
theme and then applies it over the live link. `set_theme()` has already
written a correct selection derived from the live link, and `sync_state()`
then discards it. This ordering came from 3cf8fb8 (0.6.25), which targeted
restores where derived state was missing, but it also runs when the link is
present and valid.

When the stale selection names a file that does not exist,
`resolve_background_selection()` falls back to `images(...)[0]`. `images()`
sorts by full path across both directories, so `~/.config/...` comes before
`~/.local/state/...`. The first personal image therefore wins over the
theme's own first image, which is why the same image appears every time.

`tam-deploy`'s `ensure_portable_desktop_state()` writes the selection only
when it is absent, so a stale selection survives into the switch-time
capture and the restore.

Unknown: the writer that left the selection stale between installs has not
been identified. Every journaled engine write (`bg-set`, `bg-next`, theme set)
writes the link and selection together. The fix below makes the live link win
either way.

## Workaround

Pick the background again after each install.

## Fix and verification

The live link is not always right: after a rollback, the restored selection
is the deliberate choice. So the fix keeps the selection as the authority and
removes the two ways it went wrong:

1. `desktop/theme/engine.py`: `resolve_background_selection()` no longer
   substitutes another image for a missing one. In `sync_state()`, a selection
   that cannot be resolved falls back to the image that was showing, which
   `set_theme()` records before rebuilding. Only when nothing is showing does
   it choose, and then it takes the theme's first image before personal ones.
2. `commands/tam-deploy`: `ensure_portable_desktop_state()` rewrites the
   selection from the image on screen before every bundle install, so the
   switch-time capture and the restore agree with the desktop. When the link
   is dangling and a selection exists, the selection is left for the restore
   to resolve.

Regression checks:

- `desktop/tests/test_theme_ownership.py`: three new tests cover a stale
  selection (keeps the shown image), a restored valid selection (wins over the
  shown image, the rollback case), and nothing showing (the theme's first
  image). The two bug tests fail on the previous engine with the personal
  image; the full file passes (48 tests).
- `commands/tam-deploy/tests/bundle_integration.py`:
  `test_install_keeps_the_shown_background_over_a_stale_selection` runs a
  bundle activation with a stale selection. It fails on the previous code and
  passes now. The `tam-deploy` unit suites pass (133 tests). Of the 19
  integration tests, 18 pass. The other,
  `test_bundle_native_recovery_prefers_host_record_and_falls_back_to_system`,
  fails the same way without this change.

Remaining: installed acceptance in 0.6.29.

## Resolution

Open.
