# Desktop decoupling toward antiX Core

**Status:** Dependency inventory prepared 2026-10-03; implementation has not
started. Fred approved committing and publishing this plan on 2026-10-03.
Product remains 0.0.1.
**First implementation:** a standalone Quickshell host running `fred.clock`
with Tamlinux-owned shared modules and isolated data.

## Goal and evidence

Keep the working desktop usable while replacing its Omarchy dependencies with
components that can run on antiX Core. The first deliverable is a real plugin
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

Categories: **A** native antiX host/compatible apt pool; **B** pinned Nix package
or user configuration; **C** third-party replacement; **D** Tamlinux rewrite or
integration. These are proposed owners. Exact ISO presence, versions and
dependency closure must be proved on the chosen pilot.

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

The antiX + seatd + standalone Nix direction is retained. Since 2026-10-03 the
compositor is open: the target is a tiling Wayland window system inspired by
the UI Omarchy provides, able to run on circa-2006 graphics hardware, and River
is one candidate. Two details need explicit evidence before implementation
relies on them:

1. **Compositor, and for River its family and window manager.** Current
   [River](https://github.com/riverwm/river) separates the compositor from the
   window manager. [river-classic](https://github.com/riverwm/river-classic)
   retains the older tag/riverctl design assumed in earlier plans. Pin the
   family/version and, if needed, a window manager. The independent shell
   milestone can proceed without choosing that backend.
2. **Non-systemd package and service boundary.** Verify dependencies using
   the chosen antiX repositories. Debian package availability is not sufficient:
   for example, [Debian dbus](https://packages.debian.org/trixie/dbus) lists
   libsystemd0. [seatd](https://packages.debian.org/trixie/seatd) is a package
   candidate, not proof of the complete desktop/session closure.

The [Nix manual](https://nix.dev/manual/nix/2.34/installation/installing-binary)
documents single-user installation on non-systemd Linux. Our chosen installation
and any daemon supervisor must be proved on the pilot. Home Manager package and
configuration generations do not replace host-service management or roll back
the host kernel, apt state, mutable data or live-linked source files.

## Ordered milestones

| Step | Deliverable | Depends on | Exit evidence |
| --- | --- | --- | --- |
| 0 | Current dependency inventory and source baseline | Completed reconnaissance | Classified matrix, source revisions, recorded unknowns. Prepared 2026-10-03. |
| 1 | Independent shell + clock proof | 0 | Clock and read-only calendar load through owned modules, isolated data and no Omarchy runtime imports. |
| 2 | Host contract and incremental shared UI | 1 | Settings, manifests, multi-output lifecycle, tooltips, panel focus and IPC tests; other plugins' API needs recorded. |
| 3 | Compositor contract and Hyprland adapter | 2 | Existing behavior preserved behind interfaces; no shell UI reads raw Hyprland state directly. |
| 4 | Host-safe profiles and non-systemd session/service design | 0; prototype experience from 1–3 | Host-specific state external, service ownership explicit, tested recovery design and target inputs selected. |
| 5 | antiX hardware pilot with chosen compositor/WM, Nix and session | 4; hardware/disk selection | Unprivileged desktop, driver boundary, network/audio/session bus, native sleep/logging and generation rollback proved; Chrome, VS Code and terminal workflows exercised on floor-representative hardware. |
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

Implement **Step 1 only** from this approved plan. Return a reviewable source
diff, reproducible launch instructions and evidence against its acceptance
checks. Steps 2–7 define the subsequent project order; they are not claimed
complete by the first shell prototype.
