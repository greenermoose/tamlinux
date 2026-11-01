# Finish text macros and Meta naming

**Status:** Completion plan requested on 2026-10-31. Basic macro insertion is
confirmed in the development trial; desktop-wide compatibility, complete
Meta+Alt reservation, product-wide naming and packaged acceptance remain open.
This plan extends [input usability](input-usability.md) and supersedes the
Meta+Alt system assignments in the earlier [keybinding plan](keybinding-usability.md).

## Outcome

1. Tamlinux calls the key **Meta** throughout its interface, help and current
   documentation. Users can enter Meta in Tamlinux-owned shortcut notation.
2. Any usable primary keyboard key can be assigned as **Meta + Alt + key**
   to a text macro, including Backspace and slash. Assigned macros insert the
   exact text once into the intended focused text input without also invoking
   a system action, leaking modifiers or leaving keys pressed.
3. The editor, runner, defaults, user migration and runtime dependencies reach
   users together through a recorded package assembly.

Do not narrow the second outcome to ordinary application windows merely to
close the task. Include shell panels and identify any target that cannot be
supported. Explain the actual limitation to the user and obtain a scope
resolution before calling the goal complete. A non-editable surface cannot
accept text; locked/session-inhibited surfaces must retain their protections.

## Preserve the working baseline

The relevant source trail is:

| Commit | Contribution |
| --- | --- |
| `a7952c9c8e3e6c8758c3f822058a6be84667f1d7` | Existing editor, native paste dispatch, punctuation mapping and conflict badge. |
| `1a1030cdcc2320390c0dcc2248cdfba7a11fe06e` | XKB validation, atomic saves, key recording, binding cleanup and modifier-release waiting. |
| `139b060a717573fb2740c0f5e3b5deb599a6aeff` | Carries the triggering window into the runner; cleans partially installed bindings during rollback. |
| `b933299a59e52d06e59b1881e9ac82279f9a2a74` | Records the successful physical trial. |

The [session record](../ai/2026-10-31-macro-reliability.md) records 20 macro,
49 explorer and five session-default tests passing. An invisible Wayland
editor saved Backspace through the real backend into temporary configuration.
During physical observation, Backspace was released 656 ms before the
modifiers. The slash macro emitted one Ctrl+V down/up pair after both modifiers
were released. The user then confirmed, “Text insertion works”. The tested
application was not recorded: this is not an all-applications result.

In a later physical trial with the clipboard-history search focused and a
scratch editor behind it, Fred pressed Meta+Alt+Backspace. No text appeared
in either surface; after dismissing the picker, Ctrl+V pasted the Backspace
macro text into the editor. The clipboard's previous contents were not
recorded, so this does not establish whether that particular press replaced
it. It does establish that panel insertion was not observed. The trial used
the existing `139b060a717573fb2740c0f5e3b5deb599a6aeff` explorer build and Hyprland 0.56.2. Do not infer safe
targeting or general layer-shell support from this observation.

Already implemented: punctuation/name normalization through libxkbcommon;
Lua and shell escaping; stale-editor detection; atomic file replacement;
reload/configuration-error checking and attempted rollback; removal of prior
macro bindings; inhibited key recording; focus checks; serialized native
paste dispatch; matched key release. Preserve these behaviors with regression
coverage rather than replacing the working engine without evidence.

## Source ownership

| Location | Responsibility |
| --- | --- |
| `commands/tam-macro/` | Validation, persistence, generated Lua, delivery and backend tests. |
| `desktop/shell/services/keybindings/` | Editor, model, recording, conflict display and development trial. |
| `desktop/tests/test_keybindings.py` | Model and explorer contracts. |
| `desktop/tests/test_keybinding_defaults.py` | Actual generated default bindings and catalog coverage. |
| `desktop/tests/test_session_defaults.py`, `desktop/session/entry.lua` | Packaged session loading, including user macros after overrides. |
| `desktop/session/hypr/tamlinux/bindings/` | Product default map. |
| `desktop/shell/services/keybindings/BindingCatalog.js` | Explanation metadata, updated with every changed assignment. |
| `tamlinux-packages/nix/packages/default.nix` in the delivery repo | Runtime tools, libraries, wrapping and package assembly. |
| `tam` repository | Its own command/help/corpus naming, subject to that repository's instructions. |

Claim paths in each owning repository before editing. Personal settings have
separate ownership; inspect their effective loading path before proposing a
preserving migration. Do not copy product defaults into user configuration.

## Work 1 — Complete reliable delivery

Start with reproducible application trials, then repair the demonstrated gaps.

- **Focused surfaces:** the generated handler calls `hl.get_active_window()`;
  the runner checks an application window address and explicitly targets it.
  This does not establish correct delivery to a focused layer-shell text
  field. Determine the actual keyboard-focused surface and how it can be
  tracked safely through asynchronous clipboard work. Never paste into an
  underlying window because a panel has focus. Use supported compositor APIs;
  record a genuine API limitation rather than claiming success from window tests.
- **Paste behavior:** current routing is Ctrl+V for GUI windows and Shift+Insert
  for tagged/recognized terminals. Verify browser, Electron, GTK, Qt, XWayland
  and terminal-editor behavior. Add bounded per-application handling only where
  needed. Direct typing is a separately tested option, not an automatic retry
  after a potentially successful paste.
- **Exactly once:** current serialization rejects simultaneous requests and
  sleeps 200 ms after dispatch. That delay is not proof that a slow application
  consumed the clipboard. Investigate delivery/selection ownership evidence;
  either preserve an accepted request through a bounded, target-specific
  sequence or report that it was rejected. Do not silently lose rapid presses,
  paste another macro's text or retry ambiguous delivery.
- **Held keys:** Lua currently checks modifier state every 20 ms up to roughly
  two seconds; cancellation now requests a notification. Package and verify
  its notification tool, and test every release order,
  long holds, auto-repeat and left/right modifiers. Keep all blocking subprocess
  and clipboard work out of Hyprland's event loop.
- **Failure reporting:** editor save errors are shown, but runner stderr and
  Lua early returns may be invisible when launched by a shortcut. Make missing
  tools, busy requests, focus cancellation, dispatch failure and failed rollback
  understandable without showing macro contents in logs/notifications. Attempt
  key cleanup even if delivery fails. Do not hide an unsuccessful recovery.
  Save recovery now reports restore failures and attempts both files; a failed
  key release is reported. Shortcut-launched runner errors still need a visible
  path.
- **Clipboard:** current policy leaves the macro text on the clipboard. Keep
  that explicit; do not add an arbitrary restoration timer. Exercise clipboard
  managers and external clipboard changes. If preservation is added, verify
  selection consumption/ownership before restoring anything. Automatic
  clipboard restoration is deferred: it is not needed for the stated policy,
  and an unverified restoration can race a paste.

**Exit:** exact-once insertion in the tested application classes; no wrong-target
paste, stuck keys or hidden failure. Document unresolved cases individually.

## Work 2 — Reserve Meta+Alt and finish key coverage

Inventory the effective compositor bindings as well as source defaults,
personal overrides, optional apps, submaps and physical-code aliases. Assigning
a macro currently unbinds its chord; it does not reserve the entire prefix.

1. Move remaining **keyboard** system actions off Meta+Alt. Preserve all useful
   actions and explain their replacements. Mouse resize is a separate binding;
   do not move it solely because the keyboard prefix is reserved.
2. Audit the recent migration's Ctrl+Slash, Ctrl+Shift+arrows and Ctrl+Shift+Tab
   assignments: they can intercept ordinary application editing/navigation.
   Prefer suitable Meta combinations, preserve the existing three-physical-key
   constraint, and resolve collisions across the whole map before activation.
   Product defaults now move these actions to Meta+Ctrl: arrows move windows
   into groups, Backslash selects the next group window, and Slash lowers
   scaling. Meta+Ctrl+Page Up/Down changes the grouped window. The effective
   personal map still needs a preserving migration and physical verification.
3. Normalize symbols, named keys, physical codes, aliases and layout differences
   consistently across validation, availability, conflict reporting and lookup.
   Test Backspace, slash, other punctuation, navigation, function, keypad,
   media and non-US keys; NumLock, CapsLock and AltGr need explicit cases.
4. Keep recording non-executing until the captured key is released. Clearly
   display physical-code assignments for shifted/keypad keys. “Available” must
   reflect the effective map, not merely whether another macro uses the name.
5. Verify create/edit/rename/delete and reload. Do not resurrect retired macro
   actions or allow stale cleanup entries to remove an unrelated newer binding.
   Preserve custom user assignments and require a deliberate resolution for
   conflicts instead of silently replacing unrelated customizations.

**Exit:** every usable primary key can be assigned, no system keyboard action
shares the reserved prefix, displaced actions remain accessible, and common
application shortcuts retain their behavior.

## Work 3 — Use Meta consistently

Audit product UI strings, keyboard diagrams/layout labels, plugins, menus,
notifications, CLI help, current guides and the `tam` knowledge corpus.
The explorer has already changed; the rest of Tamlinux has not.

Use a shared display/normalization policy: **Meta** is the user-facing name;
accept existing Super spellings as compatibility input. If Tamlinux-owned Lua
notation becomes Meta, translate at the binding adapter and update the scanner,
unbinding and tests together. Preserve physical meaning/modifier mask.

Do not blindly replace required upstream identifiers such as `Qt.Key_Super_L`,
XKB `Super_L`, protocol constants or compositor syntax. These remain internal
API details, with an explicit small exception list for naming checks. Historical
records and literal upstream quotations are not current interface wording.
Vendor code needs a targeted interface change, not an indiscriminate rewrite.

**Exit:** no unexplained Super label in current Tamlinux user-facing surfaces;
Meta and legacy input aliases resolve identically without changing shortcuts.

## Work 4 — Package and hand over the trial

- Supply the runner, generated-config loader, editor, metadata, map migration,
  Python, libxkbcommon, clipboard tools and compositor interfaces coherently.
  `TAMLINUX_XKBCOMMON` is available for an explicit packaged library path.
  Verify dependency resolution with the package's restricted environment.
- Audit executable identity: generated Lua currently embeds
  `Path(__file__).resolve()`. With Nix wrappers this can bypass the wrapper's
  environment; after a trial uninstall or store collection it can reference
  a removed executable. Choose a maintained entry point or regenerate bindings
  as part of every install/upgrade/rollback and prove the wrapper is retained.
- The trial now refuses to uninstall while generated macro bindings exist;
  this prevents loss but is not a handover. Previously it removed its executable/build without first
  regenerating packaged macro bindings. Fix this before handover. The current
  selected package may not include `tam-macro`; handle that explicitly. Preserve
  earlier overrides and the user's macro JSON. Do not delete the only working
  runner while bindings still refer to it.
- Verify the generated file is loaded once effectively after defaults and
  personal overrides, including fresh login and reload. Test absent, malformed
  and newer user data, interrupted saves, failed reload and rollback failure.
- Prepare an exact recorded assembly after the user authorizes candidate
  preparation. Move Test, Run and Release only on the user's exact-candidate
  stage instruction. A development trial is not packaged acceptance.

**Exit:** the normal packaged explorer owns the behavior after trial removal;
macro assignments survive upgrade, fresh session and rollback as specified.

## Acceptance matrix

Record application/version, native Wayland or XWayland, layout, exact build,
trigger, expected text and result. Keep short results, not broad logs.

| Area | Required observations |
| --- | --- |
| Targets | Browser field, GUI editor, terminal editor, GTK, Qt, Electron, XWayland, Tamlinux panel input. |
| Keys | Backspace, slash, punctuation, Space/Tab/Return/Escape, arrows/navigation, F keys, keypad, media keys that reach the compositor. |
| Layout | Active user layouts, physical vs symbol binding, left/right modifiers, locks and AltGr. |
| Timing | Ordinary tap, last key first, modifiers first, staggered releases, long hold, auto-repeat, rapid consecutive/different macros. |
| Text | Unicode/emoji, quotes/backslashes, multiline/tabbed text, trailing newline, leading/trailing spaces, maximum supported length. |
| Focus | Stable target, change while modifiers held, change during process startup/copy, target closing, panel focus, no target. |
| State | Add, overwrite, alias, rename, delete, duplicate rejection, concurrent/stale edits, invalid JSON, failed save/reload. |
| Clipboard | Manager active, clipboard replaced externally, slow target, successive requests, documented ownership policy. |
| Delivery | Correct packaged dependencies, fresh session, trial removal, upgrade/rollback and no stale executable paths. |
| Naming | UI/help/docs use Meta; API exceptions are deliberate; old configuration still loads. |

Use scratch editor documents for live trials. Fred supplies physical keypresses;
do not inject text automatically into an arbitrary focused application. Test
multiline content in an editor, not a command prompt. Distinguish hardware
keys that never reach the compositor from software binding defects.

## Next actions

1. Establish safe focused-surface delivery and visible runner failures; test
   the resulting trial with Fred before claiming broad compatibility.
2. Complete prefix reservation, preserving user migration and the Meta naming
   audit; validate both the proposed and effective maps.
3. Fix package/trial lifecycle, prepare the authorized candidate, and collect
   packaged acceptance on the user's stage instruction.
