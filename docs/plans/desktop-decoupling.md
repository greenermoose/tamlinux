# Desktop decoupling toward Void Linux

**Status:** Tamlinux 0.3.0. The Tamlinux shell's session services (notifications,
on-screen display, clipboard, pickers, reminders, menu, background, polkit,
media, idle, battery, and lock) and the inherited desktop's panels (audio,
Bluetooth, network, Wi-Fi QR, power, and speed tests) run in daily use beside
the existing bar, and every key binding and menu entry runs Tamlinux's own
commands (stage 0.2, complete). Stage 0.3 replaces the daily bar with the
Tamlinux shell and the eight rewritten plugins, which are Develop candidates
and, since 0.3.0, depend only on Tamlinux. Plugin QML
reads the compositor facade; the shell loads `SwayAdapter.qml` only when
`TAMLINUX_COMPOSITOR=sway`, and the Hyprland proof stays the default.
`tam-desktop-mode` and the monitor helpers still call the named Hyprland
backend (stage 0.4). On 2026-10-05 the milestones were re-keyed by version:
each accepted step is a patch release (see "Ordered milestones").
**First implementation:** a standalone Tamlinux shell running `fred.clock`
with Tamlinux-owned shared modules and isolated data. The candidate lives in
`desktop/`; see that README for the launch command and the 2026-10-03 check
record.

## Goal and evidence

Keep the working desktop usable while replacing its Omarchy dependencies with
components packaged as one workstation package. That package installs first on
existing distributions, starting with Fred's Arch workstation, and later on
Void Linux, with antiX Core as the fallback if Void has a showstopper. The first
deliverable is a real plugin running in an independent shell configuration.
Later milestones rewrite the plugins, establish the compositor and host-service
contracts, package the result, remove Omarchy from the development workstation,
and then prove the package on another distribution and on Void through the
[installation framework](installation-framework.md). Version numbers for each
milestone are in [VERSIONING.md](../../VERSIONING.md).

The current dependency inventory was measured from plugin source, inherited
desktop configuration, helper scripts, package metadata and service definitions.
Machine-specific evidence is retained privately. Its important findings:

- All eight plugins import Omarchy's `qs.Commons` and `qs.Ui`. The shared
  modules, manifest registry, widget host and panel lifecycle must be replaced.
- Workspaces, sysinfo, weather and tides imported `Quickshell.Hyprland`.
  Keyboard and monitor also started `hyprctl`. Plugin QML now reads the
  compositor facade. The workspace and monitor helpers still use Hyprland
  commands.
- Python/shell implementation does not itself imply portability: the workspace
  and monitor helpers use Hyprland commands and Omarchy paths.
- Stock menu, indicators, keyboard-layout, update, tray, Bluetooth, network
  and audio widgets are part of existing desktop functionality, alongside the
  eight `fred.*` plugins.
- Sleep/recovery hooks, session startup, user services and the current Nix
  configuration depend on systemd/logind and require separate target adapters.

## Source baseline

These are the measured local heads of the public component checkouts, not a
fresh reconciliation of remote tags or marketplace state. Retain these versions
for the first development snapshot; do not silently substitute moving `main`.

| Component | Manifest version | Source revision |
| --- | --- | --- |
| fred.agents | 1.2.0 | [b506739](https://github.com/greenermoose/agents-fred-tamlinux/tree/b506739c9b3825b54069b4539108cf1969addf30) |
| fred.clock | 1.3.3 | [ed5140c](https://github.com/greenermoose/clock-fred-tamlinux/tree/ed5140ccefc83c0a2fdd5f899bbd290acc35d88a) |
| fred.keyboard | 1.0.0 | [6fa043e](https://github.com/greenermoose/keyboard-fred-tamlinux/tree/6fa043ebab6485a0a5a072fa4b6346b06d7d569b) |
| fred.monitor | 1.2.3 | [a39abb5](https://github.com/greenermoose/monitor-fred-tamlinux/tree/a39abb54bf25ffddfe3a0c9743477cf73156ec05) |
| fred.sysinfo | 1.1.2 | [1dbddd6](https://github.com/greenermoose/sysinfo-fred-tamlinux/tree/1dbddd6b37e5292bca34ac5d75e8faf54d286b64) |
| fred.tides | 1.0.4 | [0b61bb8](https://github.com/greenermoose/tides-fred-tamlinux/tree/0b61bb850e8ee8948b7eb62982ece613a04bbb57) |
| fred.weather | 1.0.4 | [d149ec2](https://github.com/greenermoose/weather-fred-tamlinux/tree/d149ec24673c08ab6e850c72ad14eb1eb644aa51) |
| fred.workspaces | 1.5.2 | [4ddac79](https://github.com/greenermoose/workspaces-fred-tamlinux/tree/4ddac791fcb6f4cbd9f857255bc950e73b901e7f) |

Current snapshot uses Quickshell 0.3.1. Choose and lock the prototype's compatible
Qt/Quickshell closure explicitly; a working distro binary is useful during
development but is not yet a reproducible install manifest.

## Target ownership matrix

Categories: **A** native host package (the existing distribution's packages,
or XBPS on Void); **B** the workstation package or user configuration (Nix
flake on existing distributions, native `xbps-src` on Void);
**C** third-party replacement; **D** Tamlinux rewrite/integration. Exact package
versions and dependency closure must be proved on the pilot. The
[base plan](base-operating-system.md) defines Void first, antiX Core fallback,
Btrfs recovery, and musl/glibc evaluation.

| Dependency group | Class | Work needed |
| --- | --- | --- |
| Kernel, firmware, networking, filesystems, boot and resume device | A | Select ISO/init and host profile; verify hardware and recovery. |
| Qt/Quickshell, fonts, Python and user tools | B | Pin closure; separate native graphics/session interfaces from user packages. |
| qs.Commons/qs.Ui, theme and scale tokens | D | Own shared modules and component contracts. |
| Plugin manifest/registry, bar loading and settings | D | Validate local plugins and instantiate per output; preserve IDs and source provenance. |
| Popout coordination, tooltip surfaces, focus/dismissal and IPC | D | Define explicit host API and cleanup rules. |
| Clock calendar logic and launch integration | B+D | Reuse models/helpers; inject executable/data paths and replace Omarchy actions. |
| Agent usage, launcher and provider state | B+D | Retain bounded helpers; own launcher; keep private provider data external. |
| Workspaces, keyboard, monitor, panel target/focused output | B+C+D | Retain pure models; extract backend interfaces; implement selected compositor/WM. |
| Weather/tides locations, cache, notification and monitor routing | B+D | Replace helper/path/focus coupling while preserving bounded network work. |
| Declarative bindings, input, output layouts and window policy | C+D | Generate validated config for a pinned compositor/WM family. |
| seatd/libseat, session bus, runtime directory, auth and supervision | A+C+D | Prove each responsibility; seat access alone does not supply a full session. |
| Menus, app launch, terminal/browser selection and power actions | B+D | Own argv-based actions and desktop-file integration. |
| Tray and notification service | B+C/D | Choose one owner per D-Bus service; port shell surfaces. |
| Audio/media, Bluetooth and network controls | A/B+C+D | Choose compatible service stacks and target-native startup; own wrappers/UI. |
| Clipboard, capture, portals, screen share, removable media and secrets | A/B+C+D | Select providers for the target compositor and session; verify real workflows. |
| Idle/DPMS, inhibitors, Stay Awake and locker | B+C+D | Preserve policy and event-driven behavior; test replacement locker separately. |
| Suspend-to-hibernate, RTC, resume logging and fault detection | A+C+D | Own host lifecycle adapters; preserve bounded recovery and failure reporting. |
| Home Manager services and Nix daemon/session setup | B+C/D | Separate packages/config from init-dependent supervision and activation. |
| Plugin lifecycle CLI, drift/BOM/version metadata and installation | B+D | Separate base/shell adapters; record actual components and recovery paths. |
| Pacman patch hooks, PKGBUILDs and plugin ABI checks | A/B+D | Retire dropped-stack patches; repackage only applicable fixes. |
| Optional AI/editor/capture tools and other applications | B or declared tool-manager seam | Declare required workflows and actual versions; avoid installing the entire source workstation's package list. |

## Decisions needed before target integration

The target is **Void + runit + Btrfs**, with antiX Core + runit if Void has a
showstopper. **Sway** remains selected after the
[compositor survey](../../upstream/2026-10-03-compositor.md). The workstation
package is delivered as a Nix flake with a native host adapter on existing
distributions and as native `xbps-src` packages on Void.

1. **Sway and plugin backends.** Measure supported renderer paths on old graphics.
   Use compositor-neutral interfaces (`ext-workspace-v1` first, `Quickshell.I3`
   second where supported). Binding discovery reads generated configuration.
   The independent shell milestone does not depend on the final backend.
2. **Native package and service boundary.** On existing distributions, prove
   the host adapter: session entry, locker PAM, groups and udev rules, and the
   graphics-driver bridge for Nix-built Sway. On Void, prove the actual package closure,
   seatd, session bus, runtime directory, PAM, login, and runit supervision.
   Compare musl and glibc including required application compatibility costs.
   If antiX is needed, validate its own APT/service closure separately.
3. **Coordinated recovery.** Pair a Btrfs system/package-database checkpoint with
   kernel/modules, firmware, initramfs, and boot selection. Test rescue restoration
   while preserving user documents. If Nix is used, include its state consistently;
   a profile generation alone does not restore native packages or the host kernel.

## Ordered milestones

Since 2026-10-05 each milestone is a Tamlinux version: the minor version is a
stage and each accepted step within it is a patch
([VERSIONING.md](../../VERSIONING.md)). The proof work below this table keeps
its original names (Step 1–5), which were Develop candidates feeding stages
0.3 and 0.4.

| Stage | Deliverable | Depends on | Exit evidence |
| --- | --- | --- | --- |
| Proof (Steps 0–3) | Dependency inventory; independent shell + clock; host contract and shared UI; compositor contract with the Hyprland adapter | — | Classified matrix and source baseline; candidates in `desktop/` checked 2026-10-03. Develop only. |
| 0.0 | The foundation owned: package mirror and kernel, Hyprland configuration, shell environment, session entry, login screen | — | 0.0.1 and 0.0.2, 2026-09-22 and 2026-10-04. |
| 0.1 | Session services in the Tamlinux shell beside the existing bar; the desktop's commands owned | Proof | 0.1.0–0.1.23 accepted 2026-10-04 and 2026-10-05: notifications, OSD, clipboard, pickers, reminders, menu, background, screenshots, polkit, capture, media, idle, battery, browser extensions, monitor watch, lock, and the menus' and keys' remaining commands. |
| 0.2 | Every key binding and menu entry on owned commands; the inherited desktop's panels (audio, Bluetooth, network, power, Wi-Fi QR, speed tests) in the Tamlinux shell | 0.1 | 0.2.0–0.2.6 accepted 2026-10-05. Each key and entry checked by Fred; only the bar's own panel keys left for 0.3. |
| 0.3 | The Tamlinux shell with the eight `fred.<id>` 2.0.0 plugins and its own tray, indicators, and status widgets as the daily bar | 0.2 | 0.3.0 accepted 2026-10-06: the plugins load in the isolated shell and call only Tamlinux commands. Next the shell's own widgets (0.3.1); then the daily bar is replaced and the inherited shell stops (0.3.2). |
| 0.4 | Plugin backends and helpers on the compositor contract; Sway adapter | 0.3 | Sway adapter slice, 2026-10-04: ext-workspace workspaces first, i3 IPC second, bindings from a generated fragment; fixture proof passed. Still needed: Sway backends for the monitor and desktop-mode helpers, night light, and capture through the contract; daily use of the Hyprland adapter. |
| 0.5 | Tamlinux's own look and name | 0.3 | One theme source generates every application's colours; owned fonts; the name on the login screen, menus, and About. |
| 0.6 | The inherited desktop removed; Hyprland stays | 0.2–0.5 | Its system files, session environment, and every package it built are owned; its packages, package mirror, repository, and kernel are removed. |
| 0.7 | Workstation package beside the Hyprland session | 0.4 + 0.6 | Nix flake and Arch host adapter install a Sway session; `install verify` passes. |
| 0.8 | Sway session as the daily driver | 0.7 | Daily use; parity checks for all eight plugins and the required workflows, one step per milestone. |
| 1.0 | Hyprland removed from the development workstation | 0.8 | Removed after a backup and recorded rollback route; carried patches for dropped components retired. |
| 1.1 | Second distribution | 1.0 | Same package installed and verified on a different distribution with systemd; host-adapter differences recorded. |
| 1.2 | Void hardware pilot with Sway, runit, Btrfs and libc comparison | 1.0; hardware/disk selection | Native `xbps-src` packages from the same sources; unprivileged desktop, driver boundary, network/audio/session bus, native sleep/logging and coordinated system recovery proved; Chrome, VS Code and terminal workflows exercised on floor-representative hardware. |
| 1.3 | Repeatable installation | 1.2 | Live-media base install, single-command activation, terminal-only profile, and demonstrated recovery on more than one machine. |

The pilot machine can be selected in parallel with stages 0.2–0.8. The
development workstation keeps Arch as its base through 1.0; moving its base is
a separate later decision.

## Step 1 implementation specification

### Proposed source layout

Develop the initial independent shell in this repository, rather than creating
a new repository as a prerequisite:

```text
desktop/
  shell/shell.qml
  shell/modules/Tam/Commons/qmldir
  shell/modules/Tam/Ui/qmldir
  shell/host/                 # bar, settings, registry, panel lifecycle
  adapters/                  # deterministic patches against pinned plugin sources
  fixtures/                  # synthetic local calendar/settings
  tests/                     # meaningful contract and integration checks
  README.md                  # launch, evidence, cleanup and limits
```

Plugin sources retain their own repositories. Stage a pinned clean source copy
in a disposable development directory, apply a small recorded adapter patch,
and load that result. The final package should compose pinned inputs rather
than maintain a second permanent copy of the plugins here. Preserve licenses
and identify changed files. This shape is proposed for the first slice; record
any implementation adjustment and its reason in this plan.

The 2026-10-03 candidate kept that layout and adjusted three loading details.
The proof bar is on the bottom edge and does not take an exclusive zone, so it
does not reflow the production desktop. Sibling `Launch.qml` is listed in a
generated `qmldir` and imported with `import "."`, because a file-URL load does
not otherwise see it. `Tam.Ui` includes a `TextField` because the calendar
constructs one. Tooltip scale and output removal in the automated run are host
probes, not a physical hover or unplug.

### Build in this order

1. Record the source revision, intended host properties/methods, and all
   shared types transitively reached by the clock/calendar. Include
   `bar.shell.updateEntryInline`, `moduleWidgets`, popout coordination,
   click-target cleanup and setting persistence where the real code uses them.
2. Implement a small host, a local explicit registry, and the minimal
   `Tam.Commons`/`Tam.Ui` closure. Use owned namespaces; do not rely on global
   `qs.*` imports finding the installed Omarchy shell.
3. Adapt the real clock entry point and read-only calendar to the new imports
   and injected helper/action/data paths. Keep `Model.js`, calendar algorithms
   and bounded `Launch.qml` execution behavior where applicable.
4. Provide synthetic local ICS/settings and isolated HOME/XDG state. Disable
   remote calendar feeds in this profile. The current clock starts fetching at
   component initialization and has a refresh timer: account for those paths
   explicitly instead of assuming an offline fixture prevents all work.
5. Run the named independent configuration with a known Qt/Quickshell closure.
   [Quickshell's distribution guide](https://quickshell.org/docs/v0.3.0/guide/distribution/)
   documents named configs. Use a unique test identity and bounded lifetime;
   avoid claiming the existing bar or shell IPC identity.
6. Verify the checks below, record results and unresolved features, and present
   the candidate for the next lifecycle stage. Leave existing plugin deployment
   and the normal shell running throughout.

### Behavior required for Step 1

- A bar contains the **real adapted** `fred.clock` at the pinned source revision.
- Date/time and the configured format display correctly; right-click format
  change persists in test settings across prototype restart.
- Left-click opens the calendar; month navigation, Escape and outside-click
  dismissal work; synthetic local events are visible.
- The host tooltip is legible and positioned correctly at 1x and 1.25x scale.
- Explicit output selection works; output disappearance closes/destroys its
  surfaces and handlers without leaking processes or capturing focus.
- Launch failures, missing optional helpers and unsupported actions are clear.
  Keep event editing, remote feeds and timezone changes out of the first test
  surface unless their adapters are already implemented and verified.
- Existing process deadlines, closed environments and input limits survive;
  there is no broad `sh -c` replacement for typed actions. Disabling an action
  must also cover its IPC route.
- The harness exits cleanly and leaves no ongoing sampler or production-data
  change. Essential clock updates are allowed; unrelated background refresh
  work is disabled in this offline proof.

### Evidence required before Step 1 is complete

Record the exact source and Qt/Quickshell versions; launch command; temp data
location/cleanup; automated checks and manual UI observations; logs for popup,
output removal and process cleanup; and any skipped features. Check imports,
resolved helper paths, environment and runtime logs with `OMARCHY_PATH` unset
and no Omarchy directory in the prototype import path/PATH.

Existing pure clock tests should still pass. Add meaningful registry tests for
duplicate IDs, malformed manifests, nonexistent/outside entry points and
settings writes, plus integration checks for popup lifecycle and process
cleanup. Do not claim the shell proved independent merely because an import
search passed; exercise the real component.

## Step 2 host contract

The clock remains the only real plugin. `desktop/fixtures/panel/` is a second
widget, `tamlinux.fixture`, used to exercise two widgets and two host
instances without loading Hyprland. The full call matrix is in
[desktop/README.md](../../desktop/README.md).

Recorded needs, from the pinned revisions in the source baseline:

- Bar: `switchPanelFrom` (clock, weather, tides), `targetBelongsToWindow`
  (keyboard, monitor, sysinfo, weather, tides), `moduleWidgets` (workspaces),
  `screen.name` (weather, tides), `showTooltip` (sysinfo, monitor), and
  `setCenterHoverRevealSuppressed` (weather, tides).
- Shell: `updateEntryInline` (clock) and `summon` (monitor, currently aimed
  at `omarchy.osd`, which this host refuses).
- `bar.run` stays refused. The commands are `omarchy-agent --pick`,
  `omarchy-launch-terminal btop`, `omarchy-notification-send`, and
  `omarchy-menu-timezone`.
- Shared UI not built in the Step 2 slice: `Border`, `BarIconButton`,
  `BorderSurface`, `CursorSurface`, `Dropdown`, `PanelHero`,
  `PanelSectionHeader`, `PanelSlider`, and `ToggleSwitch`. Those types are
  in the Step 4 slice.
- Hyprland imports and `hyprctl` in this tree now live only in
  `HyprlandAdapter.qml` (Step 3). Plugin QML reads that facade (Step 5).
  Keyboard already disables its
  per-instance IPC handler because one target cannot be registered on every
  output. This host keeps IPC on `tamlinux-shell` and one clock instance.

One popout is owned per output. `targetBelongsToWindow` follows the target's
window. `moduleWidgets` returns every live instance of an id. Settings writes
succeed only for a registered id. Output removal clears that output's widgets,
click targets, popout, and tooltip.

## Step 3 compositor contract

`desktop/shell/host/Compositor.qml` is the facade shell UI and fixtures read.
`HyprlandAdapter.qml` is the only shell file that imports `Quickshell.Hyprland`
or starts `/usr/bin/hyprctl`. `desktop/fixtures/compositor/`
(`tamlinux.compositor`) reads the facade. The contract is in
[desktop/README.md](../../desktop/README.md).

The facade carries output names, focus, active workspace ids, DPMS state,
workspace and bounded window summaries, bindings text, the active keymap, and
a revision counter. `focusWorkspace`, `focusOutput`, and `setDpms` record the
request unless `TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. The proof launcher removes
that variable. Output names match `^[A-Za-z0-9._-]{1,64}$`. Workspace ids are
1 through 10. Reads are the fixed argv for `binds`, `-j devices`, and
`-j monitors`, with a closed environment and a short deadline. There is no
generic `hyprctl` argument list.

Checked on 2026-10-03. Argv and rejection tests do not run `hyprctl`.
`--selftest` at scale 1 and 1.25 compares output names, the focused output,
and active workspace ids with one `hyprctl -j monitors` snapshot, and the
clock checks still pass. Live focus and DPMS lines are absent from the proof
log. Layout rewrite, `hyprctl reload`, and monitor reset stay with the later
plugin backends. A Sway backend is Step 5.

## Step 4 shared UI, first slice

`Tam.Commons` and `Tam.Ui` now include the controls and tokens the eight
plugins construct. `Border.flat`, `surfaceSpec`, and `controlSpec` return a
uniform width from the caller's fallback color. Section names are ignored.
`desktop/shell/host/ui_contract.py` holds the same numbers for tests and does
not launch anything.

`BarApi` adds `pickAgent`, `openTerminal`, `notify`, and `openTimezoneMenu`.
`openTerminal` accepts only `btop`. `notify` accepts a plain string of at most
512 characters and records its length. `bar.run` still logs the string and
does not execute it. `Util.wheelSteps` is the pure notch helper. There is no
`execDetached`.

`desktop/fixtures/ui/` is `tamlinux.ui`. It constructs the new controls and is
not a `fred.*` plugin. The eight `fred.*` plugins on `develop/2.0.0` import
`Tam.Commons` and `Tam.Ui` instead of the Omarchy shell modules. `bar.run` is
gone. `pickAgent`, `openTerminal`, `notify`, and `openTimezoneMenu` record the
request in the proof. They start the existing programs only when
`TAM LINUX_HOST_ACTIONS=1`, which the proof unsets. Plugin QML reads the
compositor facade; the remaining Hyprland commands are in `tam-desktop-mode`
and the monitor helpers. Replacing the running bar is
`desktop/launch-daily-bar --replace` after that bar is accepted, at step
0.3.2.

## Boundaries and recovery

This task is Develop-stage work. Do not restart or replace the production shell,
switch Home Manager, edit the active desktop configuration, change sleep trials,
tag releases, submit marketplace items or migrate an OS as a side effect.
Stopping the prototype and discarding its isolated test state is its recovery
path. Any later Test/Run/Publish/Release promotion follows the project lifecycle.

The target compositor's security boundary is root-owned installed plumbing
plus validated user data; it is not achieved simply by moving an arbitrary
user-executable init script into another directory. Prove what the launcher
actually executes and how invalid config falls back before treating it as
hardened.

## Step 5 facade reads, first slice

Plugin QML on `develop/2.0.0` reads `bar.compositor`. Weather, tides, and
sysinfo target panels from `focusedOutputName` and `outputs`, including the
bounded monitor description. Keyboard reads `bindingsText` and
`activeKeymap`. Monitor DPMS calls `setDpms`. Workspaces QML reads outputs,
workspaces, focus, and `dpmsOn`, and reacts to `revision`.

`tam-desktop-mode`, `fred-monitor-layout`, `fred-monitor-state`, and
`fred-monitor-reset` on `develop/2.0.0` call named operations in
`hyprland_backend.py`. That file is the only Python that starts `hyprctl`.
Command text stays in `compositor_commands.py`. Reads run. Mutations,
including the `monitors.lua` write, record unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. Brightness still uses the Omarchy
helper. Replacing the running bar remains step 0.3.2.

## Step 5 Sway adapter

`SwayAdapter.qml` is the only shell file that imports `Quickshell.WindowManager`
or `Quickshell.I3`. `Compositor.qml` loads it only when
`TAMLINUX_COMPOSITOR=sway`. The default remains `HyprlandAdapter.qml`.
Quickshell 0.3.1 on this machine includes both modules.

Workspace lists and workspace focus prefer `WindowManager.windowsets`
(`ext-workspace-v1`). Outputs, focus, position, and DPMS come from
`Quickshell.I3`. `I3.dispatch` receives one fixed request: `workspace number N`,
`focus output NAME`, or `output NAME power on|off`. Mutations are recorded
unless `TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. `sway_commands.py` holds the
matching `/usr/bin/swaymsg` argv and does not run it. This slice does not
start `swaymsg`.

Bindings come from a generated `bindsym` fragment, not from a Sway query.
Only workspace-number and focus-output commands are kept. `exec`, `include`,
and any other command are dropped. The result is the JSON array
`Bindings.parseBinds` already accepts. The keymap comes from a bounded
`get_inputs` fixture (`xkb_active_layout_name`).

`launch-clock-proof` sets `TAMLINUX_COMPOSITOR=hyprland` unless
`--compositor sway` is passed. That mode reads `desktop/fixtures/sway/` and
does not start `hyprctl` or `swaymsg`. Checked on 2026-10-04 at scale 1 and
1.25. The Hyprland `--selftest` at those scales still registered all eight
plugins.

## Next handoff

Point `tam-desktop-mode`, `fred-monitor-layout`, `fred-monitor-state`, and
`fred-monitor-reset` at a Sway backend with the same named operations. Layout
must stop writing `monitors.lua`. A live Sway session is still required before
those mutations can be more than recorded commands. Replacing the running bar
is step 0.3.2, not a side effect of this develop candidate. Promotion
to Test is a separate decision. Stages 0.4 and later are not claimed complete
by this prototype.
