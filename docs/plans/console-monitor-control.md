# Monitor control from a Linux text console

Status: first implementation accepted and implemented in Develop, 2026-10-23.
Source and package dependency definition are ready; candidate pinning and real
console acceptance remain separate. No installation or activation occurred.

The accepted first scope is console blank/wake/idle, monitor information and
supported hardware brightness. Independent output modesetting remains future
work, with the recovery proof below required before it can be exposed.

## Goal

Provide `tam-monitor`, a keyboard-driven TUI that works from a real Linux
virtual console, including when Hyprland and Quickshell are stopped. Explain
which controls belong to the console, the monitor hardware or the desktop.
Do not require the user to start a desktop to blank a screen.

## Why the existing controls differ

The graphical monitor panel delegates power and layout changes to Hyprland.
The existing `tam-brightness-display off` command likewise calls `hyprctl`;
its `--monitor` option does not make that power operation per-monitor.
These are compositor clients, rather than standalone console controllers.

A text console uses the kernel framebuffer console. Its idle blanking timer
is independent of the graphical idle policy. `consoleblank=0` disables its
automatic blanking. The `setterm` console interface can blank and unblank the
console, but does not select individual DRM connectors or set desktop layouts.
Blanking and monitor power saving must be distinguished and physically checked.

Switching VTs also changes which session owns display access. Discovering a
Hyprland socket does not give an inactive compositor control of the foreground
console. Without Hyprland running there is no compositor socket to call.

DDC/CI brightness and supported monitor settings can work independently of
Hyprland. Availability depends on hardware, driver and device permissions.
Reading a power feature does not establish that software can wake the monitor
after turning it off.

## Recommended first implementation

Develop under `commands/tam-monitor/` in this repository. Package it through
the ordinary commands assembly. Use Python's curses support and existing
native console/DDC tools; keep the UI unprivileged.

The initial command provides:

- A monitor list with connector, identity, connection state and independently
  detected capabilities. Read kernel connector information without requiring
  compositor environment variables. Distinguish unavailable data from off.
- Brightness read/write through existing DDC helpers for external displays
  and backlight controls for supported internal panels. Bound hardware calls;
  keep the UI responsive and report failed writes.
- Blank the active text console and restore it on a keypress. Immediate
  forced blanking requires a surviving timed wake guard, since `setterm
  --blank=force` can remain blank despite ordinary keyboard input. Recover
  on normal exit/signals; the guard also covers UI death. Verify foreground
  VT ownership before acting and after a VT switch.
- An explicit console idle interval in minutes, including off. Explain that
  it concerns the console, not the graphical idle policy. Start with runtime
  changes only; do not edit boot arguments or login configuration.
- A visible capability explanation for individual monitor power. Offer DDC
  standby only after that model's off-and-wake path is physically verified;
  keep an independent timed recovery route. Never use hardware power-off
  merely because feature D6 is readable.
- Noninteractive `list`, `brightness`, `blank`, `wake` and `idle` operations
  backed by the same implementation. Console operations must act on an owned
  foreground Linux VT, never an arbitrary device path supplied by the caller.

This first implementation supplies useful console control, but does not
claim full parity with the graphical panel. It must label unsupported
controls clearly instead of returning success for a desktop-only request.

## Full per-monitor control

Independent output power, mode, refresh, rotation and link retraining need
a separate native DRM/KMS backend when no compositor is running. A curses
frontend alone cannot supply them. Desktop workspace placement and graphical
scaling have no direct equivalent in the kernel's text console.

Before adding native modesetting, prove a recoverable prototype on a spare
VT: acquire display access for the active local session, preserve the console
framebuffer and modes, handle VT pause/resume, and restore the console on
failure or process death. Never fight an active compositor for DRM ownership.
Do not expose modesetting until recovery is demonstrated. Any required native
helper and permissions need their own package contract; do not run the whole
TUI as root or broadly change device permissions.

If full independent output control is required in the first delivered command,
this backend and its hardware proof are part of completion, rather than a
claim that the console/DDC implementation already meets the goal.

## Verification and acceptance

Automated checks cover routing with no graphical environment, actual VT
identification, device mapping and hotplug, unsupported capabilities, bounded
hardware failures, write verification, wake guard recovery, interrupted UI,
VT switching, CLI errors and restoration of terminal settings. Run curses
interaction tests through a pseudo-terminal; substitute hardware interfaces.

Physical acceptance requires a recorded package and an actual Linux console
with Hyprland and Quickshell stopped: list connected monitors, adjust each
supported brightness control, blank and restore the console, test idle wake,
interrupt the UI, kill it during a bounded blank, switch VTs and confirm the
console remains usable. Verify whether blanking actually puts each monitor
into low power. Test DDC off/wake separately before enabling it by default.
Do not change or stop the user's session during investigation.

## Evidence and references

Source: `commands/tam-brightness-display/tam-brightness-display`,
`commands/tam-brightness-display-ddc/tam-brightness-display-ddc`,
`desktop/plugins/fred.monitor/Panel.qml` and
`desktop/shell/host/compositor_commands.py`.

- [setterm interface, including blank force/poke](https://man7.org/linux/man-pages/man1/setterm.1.html)
- [DRM ownership and modesetting](https://docs.kernel.org/gpu/drm-uapi.html#primary-nodes-drm-master-and-authentication)
- [logind device access and pause/resume](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html)
- [DDC requirements and limitations](https://www.ddcutil.com/faq/)

## Next actions

1. Include the source and dependency declaration when preparing the next
   user-requested candidate; do not change the existing candidate's pins.
2. On the user's Test instruction, verify the actual no-desktop console path,
   physical low-power behavior and wake recovery before claiming acceptance.
3. Plan and prove native per-output modesetting separately if it is requested.

## Development result

`commands/tam-monitor/` provides the TUI and matching CLI, direct connector/EDID
reads, verified DDC/backlight brightness, foreground text-VT validation,
bounded helper process trees, a separate-process wake guard and runtime console
idle controls with kernel readback. It never contacts a compositor or writes
DDC power features. It repaints only on content/size changes so the TUI does
not keep resetting the console idle timer.

25 focused tests cover hardware failure, readback, mapping/hotplug, forbidden
VTs/background callers, bounded helper descendants, timeout/key/interrupt
wake, caller SIGKILL/SIGSTOP, VT switching and real curses interaction through
a pseudo-terminal. Console and monitor writes are substituted in these tests;
physical acceptance is still pending. See the
[development record](../ai/2026-10-23-console-monitor-control.md).
