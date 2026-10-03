# Desktop decoupling toward Void Linux

**Status:** Step 2 candidate is in `desktop/` as of 2026-10-03. The clock
proof remains, and the host contract checks passed the same day. Product
remains 0.0.1. Not promoted past Develop. Step 3 has not started.
**First implementation:** a standalone Quickshell host running `fred.clock`
with Tamlinux-owned shared modules and isolated data. The candidate lives in
`desktop/`; see that README for the launch command and the 2026-10-03 check
record.

## Goal and evidence

Keep the working desktop usable while replacing its Omarchy dependencies with
components that can run on Void Linux, with antiX Core as the fallback if
Void has a showstopper. The first deliverable is a real plugin
running in an independent shell configuration. Later milestones establish the
compositor, session and host-service contracts, prove them on secondary hardware,
and feed the [installation framework](installation-framework.md).

The current dependency inventory was measured from plugin source, inherited
desktop configuration, helper scripts, package metadata and service definitions.
Machine-specific evidence is retained privately. Its important findings:

- All eight plugins import Omarchy's `qs.Commons` and `qs.Ui`. The shared
  modules, manifest registry, widget host and panel lifecycle must be replaced.
- Workspaces, sysinfo, weather and tides import `Quickshell.Hyprland` in seven
  QML files. Keyboard and monitor also depend on `hyprctl` subprocesses.
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

Categories: **A** native Void host/XBPS package; **B** reproducible desktop
package or user configuration (native XBPS candidate, Nix optional);
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
[compositor survey](../../upstream/2026-10-03-compositor.md). Evaluate native
XBPS/xbps-src delivery; Nix is an option, not a prerequisite for the pilot.

1. **Sway and plugin backends.** Measure supported renderer paths on old graphics.
   Use compositor-neutral interfaces (`ext-workspace-v1` first, `Quickshell.I3`
   second where supported). Binding discovery reads generated configuration.
   The independent shell milestone does not depend on the final backend.
2. **Native package and service boundary.** Prove Void's actual package closure,
   seatd, session bus, runtime directory, PAM, login, and runit supervision.
   Compare musl and glibc including required application compatibility costs.
   If antiX is needed, validate its own APT/service closure separately.
3. **Coordinated recovery.** Pair a Btrfs system/package-database checkpoint with
   kernel/modules, firmware, initramfs, and boot selection. Test rescue restoration
   while preserving user documents. If Nix is used, include its state consistently;
   a profile generation alone does not restore native packages or the host kernel.

## Ordered milestones

| Step | Deliverable | Depends on | Exit evidence |
| --- | --- | --- | --- |
| 0 | Current dependency inventory and source baseline | Completed reconnaissance | Classified matrix, source revisions, recorded unknowns. Prepared 2026-10-03. |
| 1 | Independent shell + clock proof | 0 | Candidate in `desktop/`. Automated checks passed and Fred accepted the visible bar on 2026-10-03. Develop only. |
| 2 | Host contract and incremental shared UI | 1 | Candidate in `desktop/`. Settings, manifests, per-output popout and cleanup, tooltips, panel focus, and IPC checks passed on 2026-10-03. Other plugins' API needs are recorded. Develop only; Step 3 has not started. |
| 3 | Compositor contract and Hyprland adapter | 2 | Existing behavior preserved behind interfaces; no shell UI reads raw Hyprland state directly. |
| 4 | Host-safe profiles and non-systemd session/service design | 0; prototype experience from 1–3 | Host-specific state external, service ownership explicit, tested recovery design and target inputs selected. |
| 5 | Void hardware pilot with Sway, runit, Btrfs and libc comparison | 4; hardware/disk selection | Unprivileged desktop, driver boundary, network/audio/session bus, native sleep/logging and coordinated system recovery proved; Chrome, VS Code and terminal workflows exercised on floor-representative hardware. |
| 6 | Selected compositor/WM backend and remaining plugin/workflow ports | 3 + 5 | All eight plugins and required desktop workflows pass parity checks. |
| 7 | One-command workstation layer | 5 + 6 | Fresh-host inspect/plan/apply/verify, repeatable application and demonstrated recovery on pilot. |

The pilot machine can be selected in parallel with Steps 1–3. No primary-machine
OS migration follows merely from a successful prototype.

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
- Shared UI not built in this slice: `Border`, `BarIconButton`,
  `BorderSurface`, `CursorSurface`, `Dropdown`, `PanelHero`,
  `PanelSectionHeader`, `PanelSlider`, and `ToggleSwitch`.
- Hyprland imports and `hyprctl` remain Step 3. Keyboard already disables its
  per-instance IPC handler because one target cannot be registered on every
  output. This host keeps IPC on `tamlinux-shell` and one clock instance.

One popout is owned per output. `targetBelongsToWindow` follows the target's
window. `moduleWidgets` returns every live instance of an id. Settings writes
succeed only for a registered id. Output removal clears that output's widgets,
click targets, popout, and tooltip.

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

## Next handoff

The Step 2 candidate is in `desktop/`. Review that README, including the
manual checks it does not claim. Promotion to Test is a separate decision.
Steps 3–7 define the subsequent project order; they are not claimed complete
by this prototype.
