# tam-monitor

`tam-monitor` provides monitor information, hardware brightness, and targeted Linux
text-console display control without Hyprland or Quickshell. It is implemented in C99
using `libtam-display` and `libtam-display-session` (API >= 0.4.0).

Run without arguments on a terminal to open the keyboard TUI.

## Commands

```sh
# List monitors and hardware capabilities
tam-monitor list [--json] [--no-probe]

# Hardware brightness (DDC/CI or internal backlight)
tam-monitor brightness MONITOR [1..100]

# Keep a single monitor active for an interactive console shell
tam-monitor keep CONNECTOR --shell [--card N] [--json]

# Bounded trial keeping one monitor active
tam-monitor keep CONNECTOR --seconds 1..60 [--card N] [--json]

# Blank all monitors or targeted monitors
tam-monitor blank [--monitor CONNECTOR ...] [--seconds 1..60] [--card N] [--json]

# Wake all monitors or a targeted monitor
tam-monitor wake [--monitor CONNECTOR | --all] [--json]

# Kernel console blanking idle interval (0 = off)
tam-monitor idle 0..60

# Bounded feasibility inspection
tam-monitor preview --card N --keep CONNECTOR --seconds 1..60 [--json]
tam-monitor inspect --fd FD [--keep CONNECTOR] [--json]
```

## Interactive TUI

Running `tam-monitor` on a terminal launches the interactive console TUI (implemented
directly with standard termios and VT102 escape sequences without an `ncurses` dependency):

- `j`/`k` or Up/Down arrows: select a monitor
- `+`/`-`: adjust brightness by 5% with readback verification
- `r`: refresh hardware detection and brightness
- `o`: keep selected monitor active (15s bounded trial or session switch)
- `x`: toggle blank/wake on the selected monitor
- `w`: wake all monitors
- `s`: spawn an interactive subshell keeping only the selected monitor active
- `b`: blank the console (at most 15 seconds; keypress wakes and is consumed)
- `i`: cycle console idle interval (0, 1, 5, 10, 15, 30, 60 minutes)
- `q` or `ESC`: quit TUI (cleans up and restores terminal)

The TUI repaints only when screen content or terminal size changes (with `SIGWINCH`
handling), preserving terminal state across resize.

## Lifetime, Safety and Recovery

Targeted console display control (`keep`, targeted `blank`, targeted `wake`) requires:
1. An owned foreground Linux text VT (`/dev/ttyN`, major 4).
2. A matching active local login session.
3. Access to the backing DRM card device (`/dev/dri/cardN`).

A separate recovery process owns VT handoff (`VT_PROCESS`), captures the initial
KMS configuration, verifies the bound console framebuffer geometry (`GETFB2` stride and
dimensions vs `/sys/class/graphics/fb*`), and listens on a peer-credential-verified UNIX domain socket
(`SO_PEERCRED`).

The recovery owner guarantees clean restoration on:
- Interactive shell exit or command completion
- Bounded trial timeout
- Client death or `SIGKILL`
- Signals (`SIGINT`, `SIGTERM`, `SIGHUP`)
- Hotplug disconnection of retained outputs
- VT switch away from the active console

## Build and Tests

```sh
# Build C binary
make

# Run unit and fixture test suites
make check

# Install
make install PREFIX=/your/prefix
```

Static and dynamic resource footprint:
- Unstripped binary: ~390 KiB (including ~255 KiB debug info and ~79 KiB `.text`)
- Dynamic ELF dependencies: `libsystemd.so.0`, `libm.so.6`, `libc.so.6`
- Startup latency: ~2.6 ms (`--help`), ~2.9 ms (`list --json --no-probe`)
- Peak RSS: ~10.1 MiB
- Live owner + recovery guard combined memory: ~400 KiB PSS (~4.25 MiB RSS) during an active `keep --shell` session
