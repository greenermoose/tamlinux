# Short, understandable keyboard shortcuts

**Status:** Approved by Fred on 2026-10-29; implementation in Develop. Physical and package trials remain open. Extends the approved [input-usability plan](input-usability.md) and its K22–K23 acceptance. The current running bindings remain the baseline until an exact candidate is promoted.

## Goal

Every active keyboard chord on the supported keyboard requires no more than two modifier keys plus one primary key, including any Shift needed to type a symbol. Preserve the useful actions and keypad aliases. Group related actions, make keys suggest what they do, and avoid accidental destructive actions. Users can inspect a shortcut to see what it does, when it helps, why the key was chosen and a way to remember it.

This is a product-wide default map with a separate preserving migration for personal overrides. Do not replace user customizations. A per-host live compositor scan establishes the actual map; product defaults alone cannot prove the goal on an upgraded installation.

## Proposed map

The user reviewed an audit of the current map and asked to proceed. The choices below resolve the audit's remaining tradeoffs for implementation review. Names describe actions, not necessarily executable names. Physical layout and collisions must be validated against the active keymap before implementation is considered ready.

| Action | Proposed chord | Reason |
| --- | --- | --- |
| Agent picker | Super + Shift + C | C for coding; Super+A stays available and is near close Q. |
| Private browser | Super + Alt + B | B is browser; Alt distinguishes private from Shift+B. |
| File manager at current directory | Super + Alt + E | E for explore here; preserves the familiar Super+Alt+F full-width action. |
| Music terminal UI | Super + Alt + M | M groups both music launchers. |
| Grok | Super + Alt + A | A for assistant; parallels Shift+A ChatGPT. |
| WhatsApp | Super + Alt + I | I for instant messages. |
| Google Messages | Super + Shift + I | I groups the messaging services. |
| X Post | Super + Alt + X | X groups reading and posting. |
| Calendar | Super + Alt + D | D for date. |
| Time | Super + Alt + T | T for time. |
| Battery | Super + Alt + P | P for power, alongside the power panel. |
| Weather | Super + Alt + W | W for weather. |
| Show reminders | Super + Alt + R | R groups reminder actions. |
| Clear reminders | Super + Shift + R | R family; invoke a confirmation dialog before clearing, while preserving noninteractive command behavior. |
| Reset zoom | Super + Alt + Z | Z groups zoom. |
| Theme menu | Super + Shift + T | T for theme. |
| Notification history | Super + Alt + H | H for history. |
| Toggle display mirroring | Super + Alt + Delete | Paired with Ctrl+Delete internal display. |
| Previous / next monitor | Super + Alt + Page Up / Page Down | A matched pair avoids intercepting Ctrl+Shift+Tab in applications. Replace the old Ctrl+Alt+Tab next-monitor chord too. |
| Previous / next group window | Super + Ctrl + Left / Right | Already present as group-focus aliases; retire the four-key previous binding and retain the existing next-group aliases. |
| Move workspace to directional monitor | Alt + Shift + arrow | Directional family; global application collisions are a material risk. Check common apps and document consequences; redesign if unsuitable. |
| Move window silently to desktop 1–10 | Ctrl + Alt + number and keypad number | Keeps destination number; global application collisions are a material risk. Preserve host desktop-mode behavior; check common apps and redesign if unsuitable. |
| Vertical resize, normal | Super + semicolon / apostrophe | Adjacent unshifted physical keys, left/right for shrink up / expand down. |
| Vertical resize, small | Super + Alt + semicolon / apostrophe | Alt means small increment, same keys as normal. |
| Vertical resize, large | Super + Ctrl + semicolon / apostrophe | Ctrl means large increment, same keys as normal. |
| Horizontal resize, normal / small / large | Super + comma / period; Super + Alt + comma / period; Super + Ctrl + comma / period | Requires resolving notification and Transcode collisions; see below. |

### Collisions and displaced actions

Reserve the six horizontal-resize chords as a coherent family. Move notification dismiss-last to Super+N, invoke-last to Super+Alt+N, silence to Super+Ctrl+N, and dismiss-all to Super+Shift+N; move notification history to Super+Alt+H. These displace Editor on Shift+N and night light on Ctrl+N: move Editor to Super+Shift+E (E for editor; Micro remains Super+E), and night light to Super+Ctrl+J. Move Transcode from Super+Ctrl+period to Super+Ctrl+Y. Test all of these for missing-modifier safety, including closing actions. None of these moves may be applied silently to user-owned customizations.

The personal hardware retrain action can use Super+Shift+H, keeping its host-specific command outside product defaults. Confirm the key's meaning in that host's catalog. Existing host overrides for desktops, resizing and right-click must be migrated carefully: explicitly unbind their old chords, preserve desktop-mode and Quick Launch behavior, and avoid duplicates. Show Fred any changes to user-owned files and coordinate their application with the packaged candidate; a live-linked override can affect a later compositor reload even before deployment.

Alt+Shift+arrows and Ctrl+Alt+numbers are global compositor shortcuts and can override application shortcuts. Verify in browser, editor, terminal and representative remote sessions, including physical left/right modifiers; if conflicts are significant, redesign the full family before claiming success. Treat keypad navigation and NumLock as separate checks. The chosen map is a proposal, not proof of universal ergonomics.

## Explanation and mnemonic database

Provide a packaged, maintainable catalog of binding metadata keyed by stable action identity **and chord**, so aliases and modifier choices can have distinct explanations. An entry contains a concise action explanation (what it does and when useful), a binding rationale and a mnemonic. Mark rationale as a suggested explanation where no recorded design decision exists; do not imply invented history is fact. Include entries or structured templates for numbered desktop, bar panel, direction, resize, media and hardware families; cover every shipped binding, including actions outside the changed map. Unlabeled compositor events must not receive fabricated specific behavior.

Join catalog data to the actual compositor action and chord, rather than trusting description alone. Verify dispatcher/command identity when available. If a user changes the command or adds a custom binding, do not attach a stale product rationale: show the actual command and a clear “No explanation recorded” fallback. Support host- or user-supplied metadata without requiring a global database edit, and prevent one custom entry from impersonating a different action. Handle missing or invalid optional metadata without breaking the explorer. A structured data file or equivalent versioned catalog is acceptable; no background service or database server is required.

Display **What it does**, **Why this shortcut**, and **Remember it** on both the selected-item and captured-item detail cards, with reasonable wrapping and scrolling. The interface must continue to display actual current bindings, allow other windows to receive focus, and never execute a shortcut when selected or captured. Search may include explanations and mnemonics. Package the database in both the normal shell and the standalone development trial. Explain its scope and how to maintain it.

## Delivery and verification

1. Inventory current product defaults, physical keycode mappings, live host overrides, optional webapps, dynamic bindings, aliases and supported compositor variants. Establish exact ownership and recognize that personal bindings and application context differ across machines.
2. Implement the reviewed product defaults, confirmation for reminder clearing, preserving migration/override handoff and catalog. Use path claims; do not edit a live-linked file ahead of the agreed cutover. Do not activate from source. Keep changes in Develop.
3. Add behavioral tests that enumerate real generated defaults and supported aliases, verify preservation of actions, keycode-aware collision detection and the three-physical-key limit, confirm reminder cancellation leaves timers intact, and exercise metadata identity matching, custom overrides, fallbacks, aliases and full shipped-action coverage. Verify the normal and capture detail cards show all three fields and never run the action.
4. Review package and migration diffs, prepare an exact recorded assembly and rollback point. An explorer development trial can validate the UI, but does not activate product bindings or prove the packaged shell. Test the product only on Fred's explicit **Test** instruction for the exact candidate, through the recorded package path. Apply host changes at the reviewed cutover, with a way back.
5. In the candidate, re-read `hyprctl` bindings, reconcile unnamed/keycode records, and check every physical chord and alias. Fred tries each family, reminder confirmation, compositor focus and capture; verify in common applications and on multiple monitors. Update the effective workstation catalog only after the candidate is active. Record conflicts and address them before acceptance.

**Done when:** source and installed effective maps have no keyboard chords over three physical keys on the supported layout, no unintended collisions or lost actions, every shipped action has useful and correctly matched metadata, custom bindings have honest fallback behavior, tests pass, and Fred confirms physical usability. Test, Run and Release remain separate exact-candidate decisions.
