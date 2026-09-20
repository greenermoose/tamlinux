# Session: 2026-09-20 — Capture Mode (v0.1.1 - v0.1.2, in development)

- **Date**: 2026-09-20 (morning)
- **Tool**: `claude` (Claude Code `2.1.278`)
- **Model**: `claude-opus-5` (Claude Opus 5)
- **Scope**: the deployed copy in `omarchy-fred-config` (SOP 2); this repo's
  `tests/` harness
- **Transcript**: `~/.claude/projects/-home-fred/a18febdb-55c9-42f4-87f7-2ae104759b15.jsonl`
- **Attribution**: verified. Tool and model versions were read live.

## Opening request

> Develop version 0.10.1 of fred.keyboard, continuing from where we left off
> developing this plugin yesterday.

Both manifests read `0.1.0`, so the version was queried before anything was
stamped; Fred chose `0.1.1`. The work was milestone M4b from the plan.

## What was built

- **`CaptureMode.qml`** — Quickshell's `ShortcutInhibitor` tied to the panel
  window, behind a stock `Toggle` row that is off by default, with an accent
  banner while the compositor has granted the inhibit. While it is on, every
  Hyprland bind reaches the panel instead of running (verified feasible on
  2026-09-19; not exercised by the agent, see below).
- **`Bindings.js`** — the keycode-space bridge the plan's section 4a reserved:
  `evdevFromNative`, the modifier set, and `comboLabel` producing
  "Super + Shift + K" in Hyprland's modifier order, with unplaced keys shown
  as `#code`. Pure; `tests/bindings.test.js` covers it.
- **`BarWidget.qml`** — Escape leaves capture mode first and closes the panel
  second; closing always resets the mode; a "Pressed:" readout; auto-repeat
  no longer rewrites it.

## Decisions worth knowing

1. **The inhibitor's `enabled` is set imperatively, never bound.** Quickshell
   0.3.1 writes `enabled = false` from C++ when the compositor cancels an
   inhibitor (`src/wayland/shortcuts_inhibit/inhibitor.cpp:170`). A QML
   binding would be silently replaced by that write. The wrapper keeps its own
   `wanted` flag as the source of truth.
2. **No Hyprland submap** as a second mechanism. The inhibitor covers all 252
   binds (0 exempt via `dontInhibit`), and a submap would cost a `hyprctl`
   spawn per toggle and can stick if the shell dies mid-capture.
3. **Ergonomics are agent's calls** recorded in the plan (section 6.2) for
   Fred to overturn after he tries it.
4. **Tests moved beside the deployed source.** This repo had been the only
   home of `tests/`, unlike every other tested plugin in the suite, which is
   why the deployed copy could not be tested during SOP 2 without an env-var
   detour. The tests now live in the deployed copy and Publish syncs them
   here with the code, so this repo's `tests/` will next change at Publish.

## Verification

Four suites green against the deployed tree; manifest validates; shell
restarted and the bar glyph confirmed by `grim` screenshot; no plugin messages
in the journal. **Capture mode itself was not exercised:** the panel takes
per-seat keyboard focus and the mode disables the shortcuts Fred would use to
recover, so it is his to test.

## Fred's test and 0.1.2

Fred: *"Capture mode works."* Two readout notes followed, shipped as 0.1.2:
the space bar reads "Space Bar" instead of a blank (`Bindings.cellName`), and
the Escape that ends capture mode is recorded ("Esc") and lit on the board
before the mode turns off. With the mode off, Escape still closes the panel.
