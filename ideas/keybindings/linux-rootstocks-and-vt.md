# General-Purpose Linux Distributions and the Linux Console (VT)

*Reference notes from actively maintained rootstock/general-purpose Linux
distributions (Debian, Arch Linux, Void Linux, NixOS, Alpine Linux, Gentoo,
openSUSE) and the Linux kernel virtual terminal (`drivers/tty/vt/keyboard.c`,
`TERM=linux`).*

## What it is

- **Scope:** The major actively maintained general-purpose and minimal
  Linux distributions — **Debian**, **Arch Linux**, **Void Linux** (Tamlinux's
  planned 1.2 rootstock), **NixOS**, **Alpine Linux**, **Gentoo**, and
  **openSUSE** — do not invent a distro-wide keybinding standard of their
  own. Instead, they ship:
  1. The **Linux kernel virtual terminal (VT / console)** keymap
     (`loadkeys` / `kbd`) at boot and in text sessions.
  2. Upstream defaults of whichever desktop environment (GNOME, KDE,
     XFCE, Sway, Hyprland) or console tool (`bash`, `ash`/`busybox`, `zsh`,
     `nano`, `vi`, `less`, `tmux`) the user installs.
- **Why it matters:** Because Tamlinux runs on top of Arch today and Void
  tomorrow — and supports text VT sessions (`TERM=linux`) as a first-class
  surface — the Linux kernel VT defines the **hard floor** of what keys
  can ever reach a text application.

## Modifier semantics and hardware/kernel constraints on `TERM=linux`

| Key combination | What the Linux kernel VT actually does |
| --- | --- |
| `Alt+F1`..`Alt+F12` and `Ctrl+Alt+F1`..`F12` | **Captured by kernel:** switches virtual consoles (tty1–tty12). Never reaches applications! |
| `Alt+Left` / `Alt+Right` | **Captured by kernel:** switches to previous/next virtual console. Never reaches applications! |
| `Alt+SysRq+<key>` (`R E I S U B`) | **Captured by kernel:** Magic SysRq emergency recovery (when `kernel.sysrq` enabled). |
| `Ctrl+Alt+Del` | **Captured by kernel:** triggers reboot / `ctrl-alt-del.target`. |
| `Meta` (`Super`) | **Not sent** to console applications by default keymaps. |
| `Shift+Arrows`, `Ctrl+Arrows`, `Ctrl+Shift+<letter>` | **Indistinguishable** from unmodified arrows or `Ctrl+<letter>` in default `TERM=linux` encoding. |
| `Ctrl+H`, `Ctrl+I`, `Ctrl+J`/`Ctrl+M`, `Ctrl+[` | **Legacy ASCII collisions:** identical bytes to `Backspace` (`0x08`), `Tab` (`0x09`), `Enter` (`0x0A`/`0x0D`), and `Escape` (`0x1B`). |
| `Ctrl+<22 clean letters>` | **Reliable everywhere:** `A B C D E F G K L N O P Q R S T U V W X Y Z`. |
| `Alt+<letter/punct/Enter/Backspace>` | **Reliable everywhere:** sent as `ESC <char>`. |
| Plain special keys (`Arrows`, `Home`, `End`, `PgUp`, `PgDn`, `Ins`, `Del`, `Tab`, `Enter`, `Backspace`, `Esc`, `F1`–`F12`) | **Reliable everywhere.** |

## Ideas worth taking

- **Design from the `TERM=linux` intersection up — `adopt`.**
  Every essential Tamlinux command must be reachable using the reliable
  intersection (`Ctrl+<22 clean letters>`, `Alt+<char>`, plain navigation
  and function keys), while graphical terminals (`tam-last` + Kitty
  keyboard protocol) can offer richer ergonomics like `Shift+Arrows`
  selection and `Ctrl+Arrows` word jumps without breaking text VT users.
- **Never bind `Alt+Left/Right` or `Alt+F1..F12` in the default map — `adopt`.**
  Keeping those completely off-limits guarantees zero conflict with Linux
  VT switching.
- **Keep `loadkeys` / standard kernel recovery (`Ctrl+Alt+F*`, `Alt+SysRq`) untouched — `adopt`.**
  Emergency recovery and VT switching must always work identically on
  Arch, Void, Debian, or any future rootstock.

## Things to avoid

- **Assuming graphical-only modifiers exist everywhere.**
  A keybinding system that depends on `Ctrl+Shift+letter` or `Super` for
  core editing fails completely on a bare rootstock console or over SSH.
- **Assuming `Shift+PgUp` scrolls the Linux console.**
  The kernel removed software VGA/fbcon scrollback in Linux 5.9 (2020) for
  security/maintenance reasons; console users rely on pagers (`tam-view`,
  `less`) or multiplexers.

## Where to look

- Linux kernel `drivers/tty/vt/keyboard.c` and `defkeymap.map`.
- `kbd` package (`loadkeys(1)`, `keymaps(5)`, `showkey(1)`).
- Tamlinux `tam-last/arch/key-path.md` and `arch/keybindings.md`.
