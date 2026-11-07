# tam-meter

Status: implemented on `develop` (awaiting packaged assembly delivery).
Command name is `tam-meter`. Implements the unprivileged energy meter decided
in D191 beside C + `libtam` (D160), replacing the stopgap `fred-energy-reading`
for D170/D190 candidate test records.

`tam-meter` is an unprivileged native C command that samples APU package power,
temperatures, context switches/interrupts, and busy processes without root,
background daemons, or polling loops.

## Behaviour

```text
tam-meter reading [--settle S] [--minutes N] [--interval S] [--json]
tam-meter now [--json]
tam-meter top [--interval S]
tam-meter --version
tam-meter --help
```

- `reading`: Default 360 s settle, 10 min sampling at 2 s intervals. Formats
  the exact Markdown block required for candidate Test records (D170, D190).
  With `--json`, outputs structured JSON data.
- `now`: Single 1-second sample printing current power, temperature, and wakeups.
- `top`: Interactive full-screen terminal monitor (termios cbreak, row-diff redraw,
  no ncurses, `q` or `Esc` exits). Shows live power, sparkline, wakeups, and
  top CPU-consuming processes.

Exit codes: `0` success; `1` CLI usage error; `2` power sensor unavailable.

## Data Sources

- Power: `/sys/class/hwmon/hwmon*/power1_input` where `name` is `amdgpu` (PPT).
- Thermals: `/sys/class/hwmon/hwmon*/temp1_input` where `name` is `k10temp` (Tctl).
- Displays: `/sys/class/drm/card*-*/{status,dpms}` for connected displays.
- System wakeups & busy time: `/proc/stat`.
- Process CPU ticks: `/proc/[0-9]*/stat`.
- Memory & swap: `/proc/meminfo`.

No root access is required. RAPL package energy (`energy_uj`), which is root-only,
is reported as unavailable. Wall power metering (D192) remains out of scope.

## Delivery

Lives in `commands/tam-meter/`. Discovered automatically by `tamlinux-packages`
when its Makefile exists. Links `libtam` and libc only. Tests use sysfs and procfs
fixtures (`TAM_METER_SYSFS_ROOT`, `TAM_METER_PROC_ROOT`).
