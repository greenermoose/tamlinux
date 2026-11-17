# Bug 0002 — Installing a new version replaces the chosen background

- **Status:** Confirmed.
- **Severity:** Medium; every upgrade replaces the background the person
  chose, and they must pick it again.
- **Affected:** `desktop/theme/engine.py` and `commands/tam-deploy` in
  Tamlinux 0.6.27 and 0.6.28 (bundle deliveries). Earlier versions had no
  portable background selection.
- **Fixed:** None yet. Proposed for 0.6.29.
- **Next:** Make the live background link the authority during offline
  restore, refresh the portable selection from it before the settings
  capture, and add the regression checks below.

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

Proposed, all in this repository:

1. `desktop/theme/engine.py`, `sync_state()`: when `current/background`
   resolves to a supported image, keep it and write the selection that
   `set_theme()` derived from it. Read and resolve the portable selection
   only when the link is missing or dangling (fresh account or restored
   portable state), which is the case 3cf8fb8 meant to cover.
2. `resolve_background_selection()`: a `theme` selection whose file is
   missing falls back to the first image in `current/theme/backgrounds`,
   then to personal images, not to the alphabetically first full path.
3. `commands/tam-deploy`, `ensure_portable_desktop_state()`: whenever the
   live link is valid, rewrite the selection from it (atomic, only when it
   differs), so the capture and the restore agree with the screen. Print one
   line when an existing selection disagreed with the link.
4. Regression tests in `desktop/tests/test_theme_ownership.py`: the stale
   selection reproduction above keeps the live image, the missing-link
   restore still uses the portable selection (the 0.6.25 case), and the
   deploy refresh rewrites a disagreeing selection.

Acceptance: install 0.6.29 over a desktop with a non-default background and
confirm the same image after `tam-desktop`.

## Resolution

Open.
