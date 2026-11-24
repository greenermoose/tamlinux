# Linux Mint (Cinnamon, MATE, Xfce)

*Reference notes from documented Linux Mint 21/22 Cinnamon, MATE, and Xfce
desktop defaults.*

## What it is

- **Scope:** Linux Mint is one of the largest actively maintained desktop
  Linux distributions, built on Ubuntu/Debian and led by its own Cinnamon
  desktop environment (plus MATE and Xfce editions).
- **Why it matters:** Mint deliberately minimizes friction for users
  arriving from Windows — prioritizing familiar muscle memory, low cognitive
  load, and predictable CUA shortcuts over tiling-WM orthodoxy.

## Modifier semantics and chord grammar

| Modifier | Role in Linux Mint (Cinnamon) |
| --- | --- |
| `Super` (`Meta`) | Windows-familiar shell actions: `Super` Menu, `Super+E` Nemo file manager, `Super+D` show desktop, `Super+L` lock, `Super+Arrows` snap/tile window (including quarter-tile via repeated arrows), `Super+Space` workspace overview (Expo) |
| `Ctrl` + letter | Standard CUA inside applications (`Ctrl+X/C/V/Z/Y/S/F/A/Q/W`) |
| `Ctrl+Alt` + key | Desktop/workspace control (`Ctrl+Alt+Left/Right` switch workspace, `Ctrl+Alt+Up` Expo, `Ctrl+Alt+Down` Scale window overview, `Ctrl+Alt+T` terminal, `Ctrl+Alt+L` lock, `Ctrl+Alt+Del` logout, `Ctrl+Alt+Esc` restart Cinnamon) |
| `Alt` + key | Window actions (`Alt+Tab` switch window, `Alt+F4` close, `Alt+F2` run dialog, `Alt+F10` maximize, `Alt+Space` window menu) |
| `Ctrl+Shift` + letter | Terminal emulator copy/paste (`Ctrl+Shift+C/V`) |

## Ideas worth taking

- **Zero-surprise onboarding for CUA users — `adopt`.**
  Mint succeeds because ordinary editing (`Ctrl+X/C/V/Z/A/S/F`) and
  navigation (`Arrows`, `Home/End`, `Ctrl+Arrows`, `Shift+Arrows`) work
  immediately without a manual. Tamlinux's anchor bindings honor that same
  zero-surprise principle.
- **Simple directional tiling with arrows — `adopt`.**
  Arrow-key spatial navigation and window movement are immediately
  self-explanatory compared to arbitrary letter bindings.

## Things to avoid

- **`Ctrl+Alt+Left/Right` for workspaces.**
  Steals `Ctrl+Alt+Arrows` from applications and remote desktop sessions,
  and splits workspace management away from `Meta`.
- **Three-way modifier sprawl for window management (`Super`, `Alt`, `Ctrl+Alt`).**
  Close is `Alt+F4`, snap is `Super+Arrows`, workspaces are `Ctrl+Alt+Arrows`,
  and terminal is `Ctrl+Alt+T`. There is no single rule for "which modifier
  talks to the desktop."
- **Keeping `Ctrl+Shift+C/V` in the terminal.**
  Inherits GNOME Terminal's copy/paste split.

## Where to look

- Linux Mint User Guide and Cinnamon `org.cinnamon.desktop.keybindings`
  GSettings schemas.
