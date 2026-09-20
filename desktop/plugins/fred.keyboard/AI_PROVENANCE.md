# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the
AI tools, models, prompts, and architectural decisions that shaped
`fred.keyboard`.

---

## 1. Fred's Multi-Agent AI Toolchain

CLI versions below were captured live on 2026-09-19 and re-checked 2026-09-20 (`<tool> --version`) for
the tools that touched this repository.

| Tool & Interface | CLI Version | Backing Models | Primary Role in the Ecosystem |
| :-- | :-- | :-- | :-- |
| **Claude Code** (`claude`) | `2.1.278` | Claude Opus 5 (`claude-opus-5`) | **Architecture & System Planning**: research, feasibility verification, plan authoring, scaffolding. |
| **Antigravity CLI** (`agy`) | `1.2.7` | Gemini 3.8 Flash (High) (`gemini-3.8-flash-high`) | **Research**: initial reconnaissance of Omarchy internals and prior art. |

---

## 2. Key Architectural Milestones & AI Role

| Milestone | Version | Primary AI Partner | Key Decisions & Achievements |
| :-- | :-- | :-- | :-- |
| **Reconnaissance** | pre-`0.1.0` | Antigravity (Gemini 3.8 Flash High) | Surveyed stock Omarchy keyboard components, `hyprctl binds` (252 binds), `bindings.lua`, `omarchy-menu-keybindings`, and the plugin marketplace registry. Identified `/dev/input` global capture as the approach used by an existing minimap plugin. Session ended on an API quota limit before any code was written. |
| **Design & feasibility** | `0.1.0` | Claude Code (Claude Opus 5) | Established that key capture need not be global: panel-scoped capture makes the plugin a non-keylogger. Found and resolved the blocking risk that Hyprland matches keybinds before the focused client sees them, by verifying `zwp_keyboard_shortcuts_inhibit_manager_v1` end to end (Hyprland `ShortcutsInhibit.cpp`, `KeybindManager.cpp:643`/`:844`, layer-shell support via `focusState()->surface()`, Quickshell's `ShortcutInhibitor`, `binds:disable_keybind_grabbing=false`, 0/252 binds exempt). Documented the evdev/xkb/Qt keycode reconciliation hazard. (An initial proposal to drive the model from XKB `pc104` geometry was superseded once Fred transcribed his keycaps: his board is not pc104.) Surveyed eight prior-art plugins. |
| **Scaffold** | `0.1.0` | Claude Code (Claude Opus 5) | Repository skeleton: manifest, GPL-3.0 license, changelog, bar widget entry point with the nf-md-keyboard glyph. |
| **Layout system** | `0.1.0` | Claude Code (Claude Opus 5) | Two supplies of layouts (OS XKB geometries plus a field-observed library), `LayoutResolver.js` with per-device resolution and exactness reporting, the Calliope transcribed from its keycaps, and a contribution guide. |
| **First working build** | `0.1.0` | Claude Code (Claude Opus 5) | Bar widget, panel rendering the resolved layout, panel-scoped key highlighting, device detection, and Caps/Num Lock indicators read from sysfs. Fixed three real defects found during the build: a `\uF030C` escape that silently parsed as U+F030 plus a literal "C", 64-bit `KEY=` bitmap words losing precision through `parseInt`, and a missing `implicitWidth` that made the widget load correctly but render at zero width. |
| **Pre-release publish** | `0.1.0` | Claude Code (Claude Opus 5) | Published to public GitHub `main` as a pre-release: no tags, no GitHub Release, no marketplace submission. Registered in the suite catalog and showcase. |
| **Capture mode** | `0.1.1` | Claude Code (Claude Opus 5) | `CaptureMode.qml` wraps Quickshell's `ShortcutInhibitor` behind an off-by-default toggle with an accent banner; Escape leaves the mode before it closes the panel, and closing resets it. `Bindings.js` takes over the keycode bridge (native to evdev, modifiers, chord labels) with unit tests, and the panel gains a "Pressed: Super + K" readout. The inhibitor is driven imperatively because Quickshell clears `enabled` itself on a compositor cancel. Fred tested it interactively and confirmed it works. |
| **Readout fixes** | `0.1.2` | Claude Code (Claude Opus 5) | From Fred's test: the space bar reads "Space Bar" instead of a blank (`Bindings.cellName`), and the Escape that ends capture mode is recorded in the readout before the mode turns off. |
| **Binding overlay** | `0.2.0` | Claude Code (Claude Opus 5) | `Bindings.js` gains the Hyprland side of the keycode bridge: modmask bits, keysym-to-cell mapping with shifted symbols, `code:N` to evdev, a bounded parser for `hyprctl binds`, index, exact-modmask lookup and labels, all unit-tested. Found that Hyprland 0.56.2's JSON output drops `code:N` binds (77 of 252 here), so the text form is read. Panel tints bound keys, says what a chord runs, and lists orphan binds. |
| **Mouse capture** | `0.2.1` | Claude Code (Claude Opus 5) | Fred's addition: capture mode records clicks and wheel steps with held modifiers and resolves them against Hyprland's mouse binds. Verified in the local Hyprland source that the inhibitor covers `onMouseEvent`/`onAxisEvent`, so no second mechanism. The card is covered while the mode is on; the banner names Esc as the exit, in Fred's words. |
| **Panel ergonomics** | `0.2.2` | Claude Code (Claude Opus 5) | Fred's requests after a look: the panel stays open while apps on other monitors are used (`ExplorerPanel.qml`, a clone of the stock `Ui/KeyboardPanel.qml` without its other-output click-catchers; first upstream code in the repo, recorded in `UPSTREAM.md`), and the orphan-bind list becomes a collapsible, aligned section at the bottom (`OrphanBinds.qml`). |

---

## 3. Provenance Notes

- The design plan lives at `~/docs/plans/fred-keyboard-plan.md` in
  `omarchy-fred-config` and records every decision with its date and rationale.
- Agy's reconnaissance session transcript:
  `~/.gemini/antigravity-cli/brain/3eb22acb-1ed1-46e1-a06e-efd56bd84846/`.
- No third-party code is vendored into this repository. The prior-art plugins
  listed in `README.md` informed the design only; had any code been copied,
  `UPSTREAM.md` and MIT attribution would be mandatory.
- Human direction throughout: Fred set the concept, chose panel-scoped capture
  over global capture, and decided the layout, binding scope, capture-mode and
  build-versus-fork questions.
