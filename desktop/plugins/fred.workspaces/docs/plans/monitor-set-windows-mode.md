# Implementation Plan: Dynamic Windows Monitor Sets (v1.3.0)

## Outcome

Windows Desktop mode treats every active, enabled, non-mirrored monitor as a
single ordered set. The set size follows the live monitor count, so one
implementation supports laptops, the original two-monitor arrangement, and
three or more monitors.

This plan and the v1.3.0 implementation were produced with Codex CLI
`0.154.0` using model `gpt-5.6-sol`.

## Mapping contract

Let `D` be the desktop number, `S` the active monitor count, and `P` the
zero-based left-to-right monitor position:

```text
workspace(D, S, P) = (D - 1) * S + P + 1
```

| Active monitors | Desktop 1 | Desktop 2 | Desktop 5 |
| :-- | :-- | :-- | :-- |
| 1 | `1` | `2` | `5` |
| 2 | `1, 2` | `3, 4` | `9, 10` |
| 3 | `1, 2, 3` | `4, 5, 6` | `13, 14, 15` |
| 4 | `1, 2, 3, 4` | `5, 6, 7, 8` | `17, 18, 19, 20` |

The two-monitor behavior is therefore unchanged. The bar always presents
desktops 1–5 initially and may reveal active/occupied desktops through 10.
Clicking a bar number, pressing the same top-row number, or pressing its
numeric-keypad equivalent invokes the same helper command.

## Design

### Ordered monitor discovery

`omarchy-desktop-mode` reads `hyprctl monitors -j`, validates output names,
excludes disabled and mirrored outputs, caps the set at 16 monitors, and
sorts by `(x, y, name)`. If discovery fails, it switches only one workspace
and never applies a stale multi-monitor arrangement.

The helper publishes a bounded version-2 state document:

```json
{
  "version": 2,
  "monitors": ["DP-2", "DP-1", "HDMI-A-1"],
  "left": "DP-2",
  "right": "HDMI-A-1",
  "count": 3
}
```

`monitors` is authoritative in Windows mode. The endpoint fields preserve
Mac-mode configuration compatibility.

### Switching and moving

One bounded Hyprland batch first places every member workspace, then
activates the expected workspace on each monitor and restores the initiating
monitor's focus. A read-back of `hyprctl monitors -j` must match the complete
mapping before `desktop-current` advances.

In Windows mode, moving a window to desktop `D` selects the target workspace
using the focused monitor's position in the ordered set. A normal move then
activates the destination set; a silent move leaves the visible set alone.

### Bar state

`Workspaces.qml` uses the same set-size formula to:

- map live workspace IDs back to bar desktop numbers;
- mark a set focused only when every monitor has the expected workspace;
- mark a set occupied when any member workspace has a window;
- aggregate bounded window summaries from all members;
- label two-monitor tooltips Left/Right and three-monitor tooltips
  Left/Center/Right.

### Local migration

Static odd/even Hyprland workspace pins are incompatible with a runtime set
size and were removed from Fred's local configuration. The helper is the sole
placement authority for desktop-mode actions. Physical monitor arrangement
rules were not changed.

## Completed work

- [x] Replace the left/right-pair data model with an ordered monitor set.
- [x] Generalize switch, move, mode-entry, state, diagnostics, and help text.
- [x] Generalize bar buttons, focus, occupancy, and tooltips.
- [x] Preserve top-row and numeric-keypad routes to the common helper.
- [x] Add standard-library unit tests for 1/2/3/4-monitor behavior and faults.
- [x] Validate the real three-monitor mappings `1/2/3`, `4/5/6`, and
  `13/14/15` on Fred's desk.
- [x] Preserve the v1.2.1 security controls: isolated Python, closed process
  environment, strict input/output bounds, deadlines, and atomic state.

## Release verification

```bash
python -m unittest discover -s tests -v
python -m py_compile omarchy-desktop-mode tests/test_desktop_mode.py
omarchy plugin validate .
```

Live three-monitor acceptance matrix:

| Action | Left (`DP-2`) | Center (`DP-1`) | Right (`HDMI-A-1`) |
| :-- | :--: | :--: | :--: |
| Desktop 1 | 1 | 2 | 3 |
| Desktop 2 | 4 | 5 | 6 |
| Desktop 5 | 13 | 14 | 15 |

Rollback is available through public tag `v1.2.1`; it restores pair
semantics but does not move or delete existing windows.
