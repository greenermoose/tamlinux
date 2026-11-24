# GNOME, Fedora Workstation, and Ubuntu Desktop

*Reference notes from documented GNOME Human Interface Guidelines (GNOME 45–48),
Fedora Workstation (upstream GNOME), and Ubuntu Desktop (24.04/26.04) defaults.*

## What it is

- **Scope:** GNOME is the flagship desktop environment of Fedora Workstation
  and Ubuntu Desktop (the two most widely deployed Linux desktop
  distributions). Fedora ships near-vanilla upstream GNOME; Ubuntu extends
  it with dock, terminal, and Windows-familiar shortcuts.
- **Why it matters:** Represents the mainstream Linux desktop baseline that
  most Linux users encounter first.

## Modifier semantics and chord grammar

| Modifier | GNOME / Fedora (upstream) | Ubuntu Desktop additions / differences |
| --- | --- | --- |
| `Super` (`Meta`) alone | Activities overview + instant type-to-search | Same |
| `Super` + key | Desktop shell and window tiling: `Super+Left/Right` half-tile, `Super+Up/Down` maximize/unmaximize, `Super+L` lock, `Super+V` notifications, `Super+PageUp/Down` workspaces, `Super+Tab` switch apps, ``Super+` `` switch windows of same app | Adds `Super+1..9` launch/focus dock apps, `Super+D` show desktop, `Super+A` app grid, `Super+S` workspaces |
| `Ctrl` + letter | Standard CUA inside GTK/libadwaita apps (`Ctrl+X/C/V/Z/S/F/W/Q`, `Ctrl+,` preferences, `Ctrl+?` shortcuts window) | Same |
| `Ctrl+Shift` + letter | Terminal emulator workaround (`Ctrl+Shift+C/V` copy/paste, `Ctrl+Shift+T` new tab, `Ctrl+Shift+F` find in GNOME Terminal / Ptyxis) | Same |
| `Ctrl+Alt` + key | Legacy/global desktop actions (`Ctrl+Alt+Left/Right` workspaces, `Ctrl+Alt+Del` power off) | Adds `Ctrl+Alt+T` open terminal |
| `Alt` + key | Legacy window actions (`Alt+Tab` switch windows, `Alt+F4` close, `Alt+F2` run command) and GTK mnemonics | Same |

## Ideas worth taking

- **Built-in per-app Shortcuts Window (`Ctrl+?` in GTK/libadwaita) — `adopt`.**
  Every modern GNOME app ships a structured, searchable cheat sheet of its
  own keybindings. Tamlinux's `Ctrl+G` (`guidance`) generalizes this idea
  to both graphical and terminal programs.
- **`Super`/`Meta` tap for overview/search — `consider`.**
  Making the primary desktop layer immediately searchable lowers the need
  to memorize dozens of app-launch chords.
- **Consistent `Ctrl+,` for Preferences and `Ctrl+Q` / `Ctrl+W` for quit/close — `consider`.**
  Adopted from macOS HIG onto `Ctrl` in GTK apps; clean and mnemonic.

## Things to avoid

- **The `Ctrl+Shift+C/V` terminal split.**
  Copying text takes `Ctrl+C` in every GUI app on Ubuntu/Fedora, but
  `Ctrl+Shift+C` in the terminal. Worse, `Ctrl+Shift+<letter>` cannot be
  distinguished from `Ctrl+<letter>` on `TERM=linux` or legacy xterm
  encoding. Tamlinux must not normalize this split.
- **Splitting compositor actions across `Super`, `Alt`, and `Ctrl+Alt`.**
  Having `Super+Left`, `Alt+F4`, and `Ctrl+Alt+T` all owned by the desktop
  means three different modifier tiers steal keys from applications.
- **Using `Super+V` for notifications instead of clipboard.**
  Conflicts with universal clipboard muscle memory (`V` = paste/clipboard).

## Where to look

- GNOME Developer Documentation, *Human Interface Guidelines: Keyboard
  Interaction* and `gsettings` schemas (`org.gnome.desktop.wm.keybindings`,
  `org.gnome.shell.keybindings`).
- Ubuntu Desktop Guide, *Useful keyboard shortcuts*.
