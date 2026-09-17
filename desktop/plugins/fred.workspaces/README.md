# Workspaces with Desktop Mode (`fred.workspaces`)

Fred's Omarchy workspaces plugin: a shell bar widget with dynamic all-monitor desktop sets, endpoint-based independent switching, rich window tooltips, and automatic display geometry detection.

![Workspaces with Desktop Mode](assets/screenshot.png)

---

## Overview

`fred.workspaces` replaces the stock `omarchy.workspaces` bar widget in-place using Omarchy's `clonedFrom` routing, adding a desktop mode switcher tailored for multi-monitor and single-monitor workflows:

| Mode | Indicator | Description |
| :--- | :---: | :--- |
| **Mac Desktop Mode** | `M` | Workspaces switch independently between the left and right endpoints. Odd workspaces use the left endpoint and even workspaces use the right endpoint. |
| **Windows Desktop Mode** | `W` | Every active monitor switches as one set. The set size automatically follows the number of active displays while preserving the original two-monitor behavior. |
| **Omarchy Stock Mode** | `O` | Traditional Omarchy presentation showing workspaces `1–5` on both bars. |

---

## Features

- **Quick Mode Toggle**: Click the mode letter (`M` / `W` / `O`) directly on the bar or press `SUPER + CTRL + M` to cycle modes.
- **Five Ready-to-Use Sets**: Windows mode always begins with desktop choices `1`–`5`; sets `6`–`10` appear when active or occupied.
- **Rich Set Tooltips**: Hover over a desktop button to see windows from every member workspace, labeled Left/Center/Right for three displays.
- **Dynamic Geometry Detection**: Queries `hyprctl monitors -j`, excludes disabled and mirrored outputs, and orders the remaining displays by `(x, y, name)`.
- **Single-to-Many Monitor Support**: One formula handles laptops, the original two-monitor pair, three-monitor desks, and larger arrangements.
- **Optional Endpoint Overrides**: `OMARCHY_DESKTOP_LEFT_MONITOR` and `OMARCHY_DESKTOP_RIGHT_MONITOR` customize Mac-mode endpoints without excluding displays from Windows mode.
- **Self-Contained Execution**: Bundles the standard-library-only `omarchy-desktop-mode` helper and launches it descriptor-relatively from the bar.

### Windows-mode mapping

For desktop `D`, set size `S`, and zero-based monitor position `P`:

```text
workspace = (D - 1) * S + P + 1
```

| Active monitors | Desktop 1 | Desktop 2 | Desktop 5 |
| :-- | :-- | :-- | :-- |
| 1 | `1` | `2` | `5` |
| 2 | `1, 2` | `3, 4` | `9, 10` |
| 3 | `1, 2, 3` | `4, 5, 6` | `13, 14, 15` |

---

## Requirements

- Omarchy Linux (or Arch Linux with Hyprland and Quickshell)
- Python 3 (`python3`, standard library only — executed with `python3 -I` isolated mode)

---

## Installation

Install directly with Omarchy's plugin manager:

```bash
omarchy plugin add https://github.com/greenermoose/omarchy-fred-workspaces.git --enable --yes
```

Because this plugin declares `clonedFrom: "omarchy.workspaces"`, enabling it replaces the stock Omarchy workspace widget in-place in your bar layout.

---

## Hyprland Keybindings

To enable synchronized desktop switching with your keyboard shortcuts, add the following to `~/.config/hypr/bindings.lua` (or reference the bundled script in `hyprland.conf`):

```lua
-- Desktop mode toggle
o.bind("SUPER + CTRL + M", "Toggle Mac/Windows desktop mode", "omarchy-desktop-mode toggle")

-- XKB keycodes (evdev + 8); keypad bindings ignore Num Lock.
local keypad_codes = {
  [1] = 87, [2] = 88, [3] = 89, [4] = 83, [5] = 84,
  [6] = 85, [7] = 79, [8] = 80, [9] = 81, [10] = 90,
}

for desktop = 1, 10 do
  local top_row = "code:" .. tostring(desktop + 9)
  local keypad = "code:" .. tostring(keypad_codes[desktop])

  hl.unbind("SUPER + " .. top_row)
  hl.unbind("SUPER + SHIFT + " .. top_row)
  hl.unbind("SUPER + SHIFT + ALT + " .. top_row)

  o.bind("SUPER + " .. top_row, "Switch desktop " .. desktop, "omarchy-desktop-mode switch " .. desktop)
  o.bind("SUPER + SHIFT + " .. top_row, "Move window to desktop " .. desktop, "omarchy-desktop-mode move " .. desktop)
  o.bind("SUPER + SHIFT + ALT + " .. top_row, "Move window silently to desktop " .. desktop, "omarchy-desktop-mode move-silent " .. desktop)

  o.bind("SUPER + " .. keypad, "Switch desktop " .. desktop, "omarchy-desktop-mode switch " .. desktop)
  o.bind("SUPER + SHIFT + " .. keypad, "Move window to desktop " .. desktop, "omarchy-desktop-mode move " .. desktop)
  o.bind("SUPER + SHIFT + ALT + " .. keypad, "Move window silently to desktop " .. desktop, "omarchy-desktop-mode move-silent " .. desktop)
end
```

> **Note**: If `omarchy-desktop-mode` is not in your `PATH`, you can symlink it into `~/.local/bin/`:
> ```bash
> ln -sf ~/.config/omarchy/plugins/fred.workspaces/omarchy-desktop-mode ~/.local/bin/omarchy-desktop-mode
> ```

---

## CLI Usage

The bundled `omarchy-desktop-mode` command provides scriptable desktop management:

```bash
omarchy-desktop-mode status            # Print current mode (mac, windows, omarchy)
omarchy-desktop-mode indicator         # Print single-letter indicator (M, W, O)
omarchy-desktop-mode toggle            # Cycle mode (omarchy -> mac -> windows)
omarchy-desktop-mode switch <NUMBER>   # Switch to desktop / workspace NUMBER
omarchy-desktop-mode move <NUMBER>     # Move active window to desktop NUMBER and follow
omarchy-desktop-mode move-silent <NUM> # Move active window without switching
omarchy-desktop-mode realign <MON> <N> # Bring one monitor back to desktop N, leaving the rest of the set
omarchy-desktop-mode monitors          # Print the ordered monitor set and endpoints
```

---

## Configuration & Overrides

To override the left/right endpoints used by Mac mode, create `~/.config/omarchy/desktop-mode.conf`:

```bash
# Explicit monitor names from `hyprctl monitors`
OMARCHY_DESKTOP_LEFT_MONITOR="DP-2"
OMARCHY_DESKTOP_RIGHT_MONITOR="HDMI-A-1"
```

> **Security & Format Notes**:
> - Parsed strictly as a **data-only** configuration file without shell execution (`source` is not used).
> - Values may optionally be enclosed in single or double quotes.
> - Monitor names must be alphanumeric identifiers matching `^[A-Za-z0-9._-]{1,64}$`.
> - Inline comments after values (e.g. `KEY=VAL # comment`) are rejected to avoid parsing ambiguities.
> - Windows mode always uses every active, non-mirrored monitor. Endpoint overrides do not remove monitors from its set.

### Split monitor sets (Windows mode)

Anything that focuses a window on a hidden workspace — an app that opens on a stale workspace, a window switcher, a single-monitor Hyprland dispatch — makes Hyprland move just that monitor. The `splitSet` widget setting decides whether that is allowed to split the set. It only applies to Windows mode; Omarchy and Mac modes treat each monitor individually.

```bash
omarchy bar set fred.workspaces splitSet true    # default
omarchy bar set fred.workspaces splitSet false
```

- `true`: the set splits, shown per monitor. The monitor that left the set's desktop shows a hollow marker on its own desktop and **F** (it followed a window focus) as its mode letter; hover **F** to see where it is versus the set, click **F** to bring just that monitor back. Monitors still on the set's desktop keep the solid marker and **W**. Clicking any desktop, or `SUPER + number` (top row or keypad), moves the whole set.
- `false`: the set never splits — every monitor follows to the focused monitor's desktop automatically.

### Upgrading from v1.2.1

Windows mode now interprets workspace IDs using the active set size. On three displays, workspace `3` belongs to desktop 1 instead of desktop 2. Existing windows are not moved or renumbered automatically; selecting a desktop applies the new contiguous mapping.

## Tests

The helper's monitor discovery, mapping, dispatch verification, and window-move behavior use only Python's standard library:

```bash
python -m unittest discover -s tests -v
python -m py_compile omarchy-desktop-mode tests/test_desktop_mode.py
omarchy plugin validate .
```

---

## Uninstallation
 
To remove the plugin and automatically restore the stock Omarchy workspace widget:
 
```bash
omarchy plugin remove fred.workspaces
```

## Acknowledgments

Developed with the assistance of [Antigravity](https://antigravity.google) (Google DeepMind), which contributed to the original multi-monitor modes and plugin architecture. The v1.3.0 monitor-set plan and implementation were produced with Codex CLI `0.154.0` using `gpt-5.6-sol`; see [AI provenance](AI_PROVENANCE.md) and the [public implementation plan](docs/plans/monitor-set-windows-mode.md).

---

## License

GNU General Public License v3.0 (GPL-3.0-or-later). See [LICENSE](LICENSE) for details.
