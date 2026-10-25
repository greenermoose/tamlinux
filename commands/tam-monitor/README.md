# tam-monitor

The [approved native monitor plan](../../docs/plans/console-monitor-control.md)
is being implemented. The installed Python command below remains in place
while ownership and recovery feasibility are established.

An optional C inspection prototype builds as `build/tam-monitor`:

```sh
# First install libtam's display development files into a scratch prefix.
make native LIBTAM_PREFIX=/your/development/prefix
make check-native LIBTAM_PREFIX=/your/development/prefix
# Or use normal pkg-config discovery of libtam-display >= 0.1.0.
make native
```

Its interface is `inspect --fd FD [--keep CONNECTOR] [--json]`. The descriptor
must come from an authorized session/device owner; acquisition is not yet
implemented. `--keep` analyzes connector/CRTC/plane routing only. The tool
does not open DRM cards, acquire master or blank monitors. It enables atomic
property visibility on the supplied file description. Its observation is not
a restorable snapshot or a kernel-validated atomic request. Native tests use
fake data and a non-DRM descriptor; they access no display device.

The prototype is deliberately excluded from `make install` until acquisition,
restore and lifetime are ready for a recorded package Test. Running it from
source against the live session is not the physical Test procedure.

## Installed command

Monitor information, supported brightness and text-console blanking without
Hyprland or Quickshell. Run `tam-monitor` for the keyboard TUI.

```sh
tam-monitor list
tam-monitor list --json --no-probe
tam-monitor brightness card1-DP-1
tam-monitor brightness card1-DP-1 65
tam-monitor blank --seconds 15
tam-monitor wake
tam-monitor idle 5
tam-monitor idle 0
```

In the TUI, arrows select a connector, `+`/`-` change brightness, `r` refreshes,
`b` blanks the console for at most 15 seconds, `i` cycles the console idle
interval and `q` exits. A keypress wakes an immediate blank and is consumed.
The CLI accepts bounded blank durations of 1–60 seconds. The wake guard runs
in a separate process group and restores the screen on timeout or caller
death. After a VT switch it refuses to poke a different console or a desktop.

Blank, wake and idle require the current user's foreground Linux text VT,
such as a login on Ctrl+Alt+F2. They refuse graphical VTs, terminal windows,
tmux, SSH and background jobs. Monitor information and supported hardware
brightness can also be used from a desktop terminal. No command starts or
contacts a compositor, changes device permissions or asks for root.

External brightness uses the packaged `tam-brightness-display-ddc` helper;
internal panels use `tam-hw-display` and `brightnessctl`. Hardware permissions
remain the host's responsibility. Ambiguous connector names across GPUs and
multiple internal panels have no automatic brightness mapping. Changes are
read back from hardware; a failed write or verification returns an error.
An inaccessible monitor has **unknown** brightness, never an invented off
state. Refresh retries detection subject to the existing helper's brief
unavailable cache. Each hardware call, including its children, has a deadline.

`idle` changes the kernel console blanking interval for the running boot,
not the desktop idle policy or boot configuration. The command reads the
current interval from the kernel's `consoleblank` parameter and verifies
changes there when available. Without that readback it labels a change as
requested rather than verified. The interval is shared console policy,
not a separate timer for every monitor. Timer readback is not hardware
power telemetry. The TUI repaints only when its content or terminal size changes,
so it does not continually reset the console inactivity timer.

Console blanking is not a lock and is not proof of monitor low-power mode.
How blanking affects each display must be checked on the actual driver and
hardware. It affects the outputs driven by the console together. Independent
power-off, resolution, rotation, layout, profiles and link retraining are
unavailable in this version. DDC power writes are withheld until a model's
off-and-wake recovery is physically verified. Full independent output
control needs a native DRM/KMS backend with proven console restoration.

Development checks: `make check`. They substitute console/hardware actions;
physical no-desktop acceptance still requires the recorded package and a
real Linux VT. The command is delivered through the Tamlinux package assembly.
