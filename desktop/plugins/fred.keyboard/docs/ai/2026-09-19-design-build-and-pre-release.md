# Session: 2026-09-19 — Design, First Working Build & Pre-Release (v0.1.0)

- **Date**: 2026-09-19 (evening, through ~23:00 EDT)
- **Tool**: `claude` (Claude Code `2.1.278`)
- **Model**: `claude-opus-5` (Claude Opus 5)
- **Prior work**: `agy` (Antigravity CLI `1.2.7`, Gemini 3.8 Flash High), session
  `3eb22acb-1ed1-46e1-a06e-efd56bd84846` — research only, no code, stopped on an
  API quota limit
- **Scope**: `omarchy-fred-keyboard` (new repository), `omarchy-fred-plugin`
  (catalog, README, showcase), `omarchy-fred-config` (deployment, suite plan)
- **Attribution**: verified. Tool and model versions were read live
  (`claude --version`, `agy --version`), not recalled.

## Opening request

Fred had started `fred.keyboard` with `agy` and asked this session to read
those session logs and get up to speed, noting: *"There is a security
implication of this being a key logger. That's an unavoidable side effect of
helping Fred understand exactly what signals his keyboard is sending and which
key presses correspond to which commands."*

## The premise that turned out to be wrong

It is not an unavoidable side effect. Two separate findings:

1. **Panel-scoped capture is not keylogging.** Reading keys through QML
   handlers only while the plugin's own panel holds keyboard focus means the
   compositor routes keystrokes solely to that surface; nothing typed in any
   other window is ever visible. No `/dev/input`, no `input` group, no
   background process. Fred chose this over global capture.

2. **The functionality it seemed to cost is recoverable.** Hyprland matches
   keybinds *before* the focused client sees the key, so a panel-scoped
   listener would never receive `Super+K` — which would have gutted the
   feature for exactly the combinations worth inspecting. The
   `zwp_keyboard_shortcuts_inhibit_manager_v1` protocol suspends that
   matching. Verified end to end rather than assumed:

   | Check | Result |
   | :-- | :-- |
   | Hyprland implements it | `src/protocols/ShortcutsInhibit.cpp`, registered `ProtocolManager.cpp:183` |
   | Keybind matching honours it | `KeybindManager.cpp:643`, `:844` |
   | Works for a layer-shell panel | `isInhibited()` matches `focusState()->surface()` generically |
   | Quickshell exposes it | `Quickshell.Wayland` / `ShortcutInhibitor` |
   | Disabled by config? | No — `binds:disable_keybind_grabbing` is `false` |
   | Binds exempt via `dontInhibit`? | No — 0 of 252 |

   Capture mode (M4b) is the next milestone.

## Prior art

Agy's search missed the field by guessing repository names. A concept search
found eight comparable Omarchy plugins, all MIT. Closest are
`dai199/omarchy-visual-keybindings` (which independently uses the same
`ShortcutInhibitor` API, plus a Hyprland submap as a second mechanism) and
`neilerua973/omarchy-keybindings-editor`. Both hardcode the keyboard;
`neilerua973` documents the compromise in its own source. Fred chose to build
rather than fork, borrowing ideas but no code, so no `UPSTREAM.md` is
required and `README.md` credits the prior work.

## The layout problem

Fred asked whether the model would contain all the keys on his keyboard, and
was right to. **Declared is not present, and present is not always declared:**
his Calliope declares 180 keys across three evdev nodes, including `F13`-`F24`
and Japanese/Korean IME keys it does not have, declares `RIGHTMETA` though it
has no right Super, and omits `FN` entirely because that key is firmware-local
and never reaches the OS. No software reading settles it.

Fred transcribed his keycaps. The board is **not `pc104`**: Insert in the
function row, ScrLk before PrtSc, Home/End on the number row, a double-height
Delete, an Fn key, no right Super. He then asked for the system to generalise,
which produced the two-supply design: the OS XKB geometries plus a
field-observed library in `layouts/*.json`, resolved per device by
`LayoutResolver.js`, which reports whether a match is exact.

## Defects found during the build

Each was caught by a check rather than by reading the code:

1. **The bar icon was wrong.** `"C"` is not the keyboard glyph —
   JavaScript `\u` escapes take exactly four hex digits, so it parsed as
   U+F030 followed by a literal `"C"`. U+F030C needs the literal character.
2. **Key counts were silently wrong** (72 vs. the true 163). A `KEY=` bitmap
   word is 16 hex digits (64 bits), past JavaScript's 53-bit safe integer
   range, so `parseInt` plus bitwise arithmetic lost bits. Now counted per
   hex digit, with a regression test.
3. **The widget rendered at zero width.** Rewriting `BarWidget.qml` from a
   plain `Item` to a `Panel` root dropped `implicitWidth`/`implicitHeight`;
   the base `Panel` has no intrinsic size. It loaded, reported
   `"enabled": true`, logged nothing, and was invisible. Worth noting that
   the agent's *verification* was the real failure here: `listPlugins` and a
   clean log cannot distinguish a working widget from a zero-width one. A bar
   screenshot can, and changes no focus.
4. **A transcription error**, caught by the "main block is 15u on every row"
   invariant: right Shift was 1.75u where a board with a separate arrow
   cluster needs 2.75u.

Also latent, and left alone as out of scope: `fred.monitor` references
`Style.radius` and `Color.accentText`, neither of which exists in this Omarchy
version, and logs warnings on every shell start.

## Lock LEDs

Caps/Num Lock come from `/sys/class/leds/input<N>::capslock/brightness` — the
real hardware lamp, needing no privileges and observing no keystrokes. The
node is derived from the device's own event index, verified by resolving
`input5::capslock/device` to a sysfs path carrying `0003:17EF:608C`. An
`input2::capslock` belonging to the PS/2 stub is exactly what a guess would
have picked up. Polled only while the panel is open, per Fred's stance on
energy use.

## Outcome

Published to `greenermoose/omarchy-fred-keyboard` at **v0.1.0, pre-release**:
public and installable, no tags, no GitHub Release, no Show & Tell post,
nothing sent to the marketplace. Registered in the suite catalog, README and
showcase. Milestones M0-M3b complete; M4b (capture mode) is next.

## Also arising from this session

Fred asked for `system/bom.json` drift to be fixed *and* the mechanism that
allowed it. Three entries had drifted. The cause was four runbooks and a
memory each instructing agents to hand-maintain a file that restates facts the
workstation already knows. Fixed in `omarchy-fred-config` by generating the
derived sections (`bin/omarchy-fred-bom`, run by `omarchy-fred-sync` during
capture) and removing the hand-edit instructions.
