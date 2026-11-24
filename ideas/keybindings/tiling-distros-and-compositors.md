# Tiling Distributions and Wayland/X11 Compositors

*Reference notes from documented defaults of Regolith Linux, Arch-family
Hyprland desktops (Omarchy, CachyOS, EndeavourOS, Garuda), i3/Sway, Niri,
and Hyprland.*

## What it is

- **Scope:** Actively maintained tiling-first Linux distributions and
  compositors where keyboard navigation is the primary interface:
  - **Regolith Linux** (Ubuntu/Debian-based curated i3/Sway desktop).
  - **Omarchy** (Tamlinux's historical Arch/Hyprland starting lineage) and
    Arch-family desktops (**CachyOS**, **EndeavourOS** i3/Sway, **Garuda**
    Hyprland/Sway).
  - **i3 / Sway**, **Niri** (scrollable-tiling Wayland compositor), and
    **Hyprland**.

## Modifier semantics and chord grammar

| System | Modifier rule & notable patterns |
| --- | --- |
| **i3 / Sway** | Single `Mod` (`Super`/`Meta` or `Alt`): `Mod+Arrows`/`JKL;` focus, `Mod+Shift+Arrows` move, `Mod+1..0` workspaces, `Mod+Shift+1..0` move to workspace, `Mod+Enter` terminal, `Mod+D` launcher, `Mod+Shift+Q` close (Shift protects against accidental close), `Mod+F` fullscreen, `Mod+R` **resize mode** |
| **Regolith** | Standardizes i3/Sway on `Super` with ergonomic refinements: `Super+Space` launcher, `Super+Enter` terminal, `Super+Shift+Q` close, `Super+Shift+?` opens **Remontoire** (live cheat sheet parsed directly from the active config!) |
| **Niri** | Cleanest spatial grammar in modern Wayland: `Mod+Left/Right` focus column, `Mod+Up/Down` focus window in column, `Mod+Ctrl+Arrows` move column/window, `Mod+Shift+Arrows` focus monitor, `Mod+Shift+Ctrl+Arrows` move to monitor, `Mod+PageUp/Down` workspaces, `Mod+R` cycle preset column widths, `Mod+F` maximize column, `Mod+Shift+/` built-in **hotkey overlay** |
| **Hyprland / Omarchy** | `Meta` (`SUPER` upstream) + single modifier (`Shift`, `Ctrl`, `Alt`): `Meta+Q` close, `Meta+Return` terminal, `Meta+Space` menu, `Meta+F` fullscreen, `Meta+1..0` desktops, `Meta+Shift+1..0` move window, `Meta+K` keybindings explorer, `Meta+C/V/X` universal copy/paste/cut |

## Ideas worth taking

- **Live hotkey overlay parsed from actual active config (Regolith Remontoire, Niri `Mod+Shift+/`, Tamlinux `Meta+K`) — `adopt`.**
  Never let docs drift from reality: the help overlay should read the live
  bindings plus explanations/mnemonics (as in Tamlinux P14).
- **Niri's strict modifier-to-scope mapping — `adopt`.**
  In Niri, every modifier has one clear spatial job (`Mod` = focus,
  `Mod+Ctrl` = move, `Mod+Shift` = monitor/bigger scope). Users deduce
  chords instead of memorizing tables.
- **Guarding destructive actions (i3 `Mod+Shift+Q` or confirmation) — `consider`.**
  Putting `Close` or `Clear` where a stray tap won't trigger it prevents
  data loss (already noted in Tamlinux P14 for clearing reminders).
- **Strict 3-physical-key ceiling (Tamlinux P14) — `adopt`.**
  Niri's `Mod+Shift+Ctrl+Arrow` (4 keys) is the warning sign: once a chord
  needs three modifiers plus a key, ergonomics collapse.

## Things to avoid

- **Using `Alt` as the compositor `Mod` key (older i3 default).**
  Collides catastrophically with terminal and editor `Alt` bindings.
  `Meta` must be the compositor modifier.
- **Unstructured proliferation of `Meta+Shift/Ctrl/Alt+<letter>` app launchers.**
  When every web app and utility grabs a global `Meta+<mod>+<letter>`
  chord (as in early Omarchy maps), the map becomes an unmemorable
  alphabet soup. A fast searchable menu (`Meta+Space`) + a small set of
  high-frequency anchors scales far better.
- **Global `Alt+Shift+Arrows` or `Ctrl+Alt+<number>` compositor grabs.**
  Stealing chords that do not contain `Meta` breaks editors, browsers,
  and remote sessions (flagged as a material risk in Tamlinux P14).

## Where to look

- i3 / Sway default config (`/etc/sway/config`).
- Regolith Desktop documentation (`regolith-desktop.com`) and Remontoire.
- Niri default config (`github.com/YaLTeR/niri`, `resources/default-config.kdl`).
- Tamlinux [`plans/P14-keybinding-usability.md`](../../plans/P14-keybinding-usability.md)
  and [`plans/P29-text-macros-and-meta.md`](../../plans/P29-text-macros-and-meta.md).
