# AI Collaboration & Provenance

This repository practices transparent AI-assisted engineering. We document the
AI tools, models, prompts, and architectural decisions that shaped
`fred.keyboard`.

---

## 1. Fred's Multi-Agent AI Toolchain

CLI versions below were captured live on 2026-09-19 (`<tool> --version`) for
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
| **Design & feasibility** | `0.1.0` | Claude Code (Claude Opus 5) | Established that key capture need not be global: panel-scoped capture makes the plugin a non-keylogger. Found and resolved the blocking risk that Hyprland matches keybinds before the focused client sees them, by verifying `zwp_keyboard_shortcuts_inhibit_manager_v1` end to end (Hyprland `ShortcutsInhibit.cpp`, `KeybindManager.cpp:643`/`:844`, layer-shell support via `focusState()->surface()`, Quickshell's `ShortcutInhibitor`, `binds:disable_keybind_grabbing=false`, 0/252 binds exempt). Established XKB `pc104` geometry as the model source instead of a hardcoded grid, and documented the evdev/xkb/Qt keycode reconciliation hazard. Surveyed eight prior-art plugins. |
| **Scaffold** | `0.1.0` | Claude Code (Claude Opus 5) | Repository skeleton: manifest, GPL-3.0 license, changelog, bar widget entry point with the nf-md-keyboard glyph. |

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
