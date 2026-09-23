# Display & Monitor Manager (`fred.monitor`)

Display information, per-display control, saved layouts, and guarded link reset plugin for [Tamlinux](https://github.com/greenermoose/tamlinux) (Hyprland + Quickshell). Current release: **v1.2.3**.

![fred.monitor Screenshot](assets/screenshot.png)

---

## Overview

`fred.monitor` replaces the stock Omarchy Display panel (`omarchy.monitor`) with an enhanced clone designed for multi-monitor setups. It adds per-display link retraining and reset, fixes stock multi-monitor scaling and toggle syntax issues, and provides clear visibility and control over connected displays.

| Item | Details |
| :--- | :--- |
| **Plugin ID** | `fred.monitor` |
| **Upstream Target** | `omarchy.monitor` |
| **License** | GPL-3.0-or-later |
| **Author** | Fred (@greenermoose) |
| **Repository** | `https://github.com/greenermoose/monitor-fred-tamlinux` |

---

## Features

- **Per-Display Cards**: Side-by-side cards show connector, monitor identity, physical size, position, and live hardware facts.
- **Per-Display Controls**:
  - Individual DDC brightness sliders with guarded writes and explicit unavailable state.
  - Resolution, orientation, scale, and position controls staged before Apply.
  - DPMS On/Off toggle and per-display Identify overlays.
- **Saved Layouts**: Named layouts, a first-use Default, and automatic Previous and Last saved recovery entries.
- **Safe Apply**: A detached 15-second rollback guard; Keep persists the verified layout and Revert restores the prior one.
- **Link Reset / Retrain**: Per-display link retraining (`fred-monitor-reset`) to recover from DP/HDMI jitter or panel sync faults.
- **Stock Defect Fixes**:
  - Uses native Hyprland Lua syntax for display toggling (`hl.monitor({ output = ..., disabled = true/false })`).
  - Applies monitor scaling without clobbering existing physical offsets and monitor positions.
- **Unified Keyboard Navigation**: Home opens a help sheet; shortcuts cover cards, controls, Identify, Reset, Apply, and close.
- **Running Version Visibility**: Running version displayed on bar icon hover tooltip and in the popup panel footer.
- **Hardened Process Execution**:
  - All process execution goes through a supervised `Launch.qml` component.
  - Closed environment with strict allowlists (`clearEnvironment: true`).
  - Watchdog timers enforcing strict process deadlines (SIGTERM followed by SIGKILL).
  - Strict input validation (`^[A-Za-z0-9._-]+$`) on monitor connector names.
  - Direct execution without ambient shell string interpolation.

---

## Installation

Install and enable the plugin via Omarchy:

```bash
omarchy plugin add https://github.com/greenermoose/monitor-fred-tamlinux.git --enable
```

Because `fred.monitor` declares `clonedFrom: "omarchy.monitor"`, Omarchy automatically replaces the stock Display widget in place on the bar.

To persist an applied layout, `~/.config/hypr/monitors.lua` must contain one
`fred.monitor` managed block. Put the monitor rules you want this plugin to
manage between these markers, keeping any unrelated configuration outside:

```lua
-- BEGIN fred.monitor managed displays
-- Your current hl.monitor({ ... }) rules go here.
-- END fred.monitor managed displays
```

Apply previews a layout temporarily; Keep only saves it when that block is
present and writable. The helper refuses to replace an unmarked file.

---

## License & Attribution

- Licensed under **GNU General Public License v3.0 or later** ([`LICENSE`](LICENSE)).
- Cloned from stock Omarchy [`omarchy.monitor`](/usr/share/omarchy/shell/plugins/panels/monitor/) (MIT License). See [`UPSTREAM.md`](UPSTREAM.md) for provenance details and diff recipe.
