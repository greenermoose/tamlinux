# Tamlinux shell proof

Develop-stage host for `fred.clock` 2.0.0 and the other seven `fred.*` 2.0.0
plugins. The proof still uses an isolated home and a read-only calendar.
It runs outside the Omarchy shell and does not replace the running desktop.
Stopping the proof process and deleting its isolated state is the recovery path.

Clock source is the `develop/2.0.0` working tree. The 1.3.3 pin
`ed5140ccefc83c0a2fdd5f899bbd290acc35d88a` remains the baseline the adapter
patch is generated from.
Development closure checked here: Quickshell 0.3.1, Qt 6.11.2.

## Host contract

Each output gets its own bar object from `desktop/shell/host/BarApi.qml`.
The shell answers calls that have to see every output. Call sites below are
the pinned revisions in the source baseline of
[desktop-decoupling.md](../docs/plans/desktop-decoupling.md). Plugin source
is not copied into this directory.

| Call | Who uses it | Host behavior |
| --- | --- | --- |
| `foreground`, `fontFamily`, `position`, `urgent`, `barSize` | all eight plugins | Bottom bar, horizontal, owned palette and type scale. |
| `bar.screen.name` | weather, tides | The output this bar was built for. |
| `setting()` / `updateEntryInline` | clock | Scalar writes for a registered id. Unknown ids are refused. |
| `moduleWidgets` | workspaces | Every live instance of that id, across outputs. |
| `requestPopout` / `releasePopout` | keyboard, monitor, sysinfo, weather, tides, clock | One open popup per output. Opening another on that output closes the current one. |
| `switchPanelFrom` | clock, weather, tides | Opens the next widget on that output that has `open` and `close`. |
| `targetBelongsToWindow` | keyboard, monitor, sysinfo, weather, tides | True only when the click target belongs to that window. |
| `setCenterHoverRevealSuppressed` | weather, tides | Stored on that bar. |
| `showTooltip` / `hideTooltip` | sysinfo, monitor, and the shared buttons | Separate overlay. Size follows `TAMLINUX_UI_SCALE`. |
| `shell.summon` / `hide` / `toggle` | monitor calls `summon` | Opens or closes the first registered panel widget. `omarchy.osd` is refused. |
| `bar.run` | none of the 2.0.0 plugins | Logged and not executed. The string is not interpreted. |
| `pickAgent()` | agents | Recorded. Starts `/usr/bin/omarchy-agent --pick` only when `TAMLINUX_HOST_ACTIONS=1`. |
| `openTerminal(program)` | sysinfo | Records `btop` only. Any other program is refused. The `btop` launch uses the same actions flag. |
| `notify(text)` | weather | Records the length of a plain notice up to 512 characters. Shell characters are refused. A plain notice is sent only when the actions flag is set. |
| `openTimezoneMenu()` | clock | Recorded. Opens the timezone program only when the actions flag is set. |

`Tam.Commons` and `Tam.Ui` include the shared types the eight plugins construct:
`Border`, `BarIconButton`, `BorderSurface`, `CursorSurface`, `Dropdown`,
`PanelHero`, `PanelSectionHeader`, `PanelSlider`, and `ToggleSwitch`, plus the
type and spacing tokens those plugins read. `Border.surfaceSpec` and
`Border.controlSpec` use the fallback color and a uniform width. They do not
read a theme file. `Util.wheelSteps` accumulates wheel notches. There is no
`execDetached`. The eight `develop/2.0.0` plugins load from their own trees
and import `Tam.Commons` and `Tam.Ui`.

## Compositor contract

Shell UI and fixtures read `desktop/shell/host/Compositor.qml`.
`HyprlandAdapter.qml` is the only shell file that imports
`Quickshell.Hyprland` or starts `/usr/bin/hyprctl`. There is no generic
`hyprctl` argument list. `desktop/shell/host/compositor_commands.py` builds
the argv and does not run it. `hyprland_backend.py` is the only Python that
starts `/usr/bin/hyprctl`, and only for a named operation.
`SwayAdapter.qml` is the only shell file that imports `Quickshell.WindowManager`
or `Quickshell.I3`. It loads only when `TAMLINUX_COMPOSITOR=sway`. Workspaces
prefer ext-workspace window sets, then i3 IPC. Bindings come from a generated
`bindsym` fragment. `sway_commands.py` and `sway_snapshot.py` do not run
commands, and this slice does not start `swaymsg`.

The facade exposes plain data:

- outputs: name, focused flag, active workspace id, `dpmsOn`, a description
  capped at 128 characters, integer `x` and `y`, and whether a special
  workspace is showing
- `focusedOutputName` and `outputForScreen(screen)`
- workspaces: id, output name, occupied, bounded window summaries
- `focusedWorkspaceId`, `bindingsText`, `activeKeymap`
- a revision counter that changes when the snapshot changes

Named actions are `focusWorkspace(id)`, `focusOutput(name)`, and
`setDpms(name, on)`. They record the request unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. The proof launcher removes that
variable, so a selftest cannot blank a display or move focus. Output names
must match `^[A-Za-z0-9._-]{1,64}$`. Public workspace ids are 1 through 10.
Helper dispatch ids, used by windows-mode sets, are 1 through 160. Reads
are the fixed commands `binds`, `-j devices`, `-j monitors`,
`monitors all -j`, `activeworkspace -j`, `configerrors`, and `rollinglog`,
each with `PATH=/usr/bin`, the Wayland runtime directory, the Hyprland
instance signature, and a short deadline. Bindings text, the keymap, and
window summaries are capped. Mutations are focus, move, DPMS, a bounded
batch, one validated monitor rule, and `reload`. DPMS uses `dispatch` with
`on` or `off`, then a fixed fallback. The layout helper does not write
`monitors.lua` unless the live flag is set.

`desktop/fixtures/compositor/` is `tamlinux.compositor`. It reads the facade
and logs names, counts, the keymap, and whether the screen matches an output.
It does not import Hyprland. Plugin QML reads this facade. The develop
helpers load the backend from `TAMLINUX_COMPOSITOR_COMMANDS`, which the
proof exports as the host directory. Brightness still calls the Omarchy
display helper.

IPC stays on the shell target `tamlinux-shell` and the one `tamlinux.clock`
handler inside the single clock instance. The fixture sets `manageIpc` false
and does not register a target, because a widget instantiated once per output
would otherwise register the same target more than once. The proof does not
register `omarchy.clock` or `fred.clock`.

`TAMLINUX_CLOCK_OFFLINE=1` makes `runFetch()` return before starting
`fetch-events.py`, and it leaves the 15-minute refresh timer stopped. The
launcher also writes a local-only calendar config and a synthetic `events.json`
under the isolated home. Event add/delete stays in the QML tree but the
offline profile hides those controls and refuses both the UI path and the
`createEvent` / `deleteEvent` IPC.

## Session services

`shell/host/Services.qml` loads the session services named in
`TAMLINUX_SERVICES` (comma-separated; unknown names are ignored). Each is
imported statically, because Quickshell only scans files it reaches by import.
`TAMLINUX_BAR=0` runs the services without a bar, beside another shell's bar;
the host then reports its bar position as `top` so popups clear that bar.

| Service | Source | Behavior |
| --- | --- | --- |
| `notifications` | `shell/services/notifications/`, vendored with its MIT notice (`shell/services/LICENSE-omarchy`) | Owns `org.freedesktop.Notifications`. Popups top-right on every output, do-not-disturb with bypass rules, ten-entry history and replay, popups that survive a restart, argv and `default` actions. Clicking a card without an action calls the facade's `focusApp(name)`. State is under `~/.local/state/tamlinux/notifications/`. IPC target `notifications`: `ping`, `dndState`, `toggleDnd`, `setDnd`, `isDnd`, `showHistory`, `clear`, `dismissAll`, `dismissOne`, `invokeLast`, `dismiss`. |
| `osd` | `shell/services/osd/`, vendored with the same notice | Volume, brightness, and status overlays, bottom-centre on the focused output, on the `tamlinux-osd` overlay layer. It takes no pointer or keyboard input. A card shows a glyph with a progress bar and percentage, or a glyph with a short message, and hides after its duration (default 1200 ms; 0 keeps it open). IPC target `osd`: `show(payloadJson)` with `icon`, `message`, `value`, `max`, `progressText`, and `duration`; `close`, `state`, `ping`. |

`focusApp(name)` takes `^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$`. On Hyprland it
matches the window class case-insensitively and dispatches a focus by window
address; on Sway it dispatches `[app_id="(?i)…"] focus` with `.` and `+` as
character classes. Like the other mutations it is recorded unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`.

If another notification server already owns the name, Quickshell logs that
and claims the name when the other server releases it.

## Layout

```text
desktop/
  launch-clock-proof          # stage, launch, and --selftest
  shell/shell.qml             # named config root
  shell/host/                 # bar, settings writes, manifest checks
  shell/host/Compositor.qml   # facade the shell and fixtures read
  shell/host/HyprlandAdapter.qml
  shell/host/SwayAdapter.qml      # loaded only when TAMLINUX_COMPOSITOR=sway
  shell/host/compositor_commands.py
  shell/host/sway_commands.py     # swaymsg argv; does not run it
  shell/host/sway_snapshot.py     # fixture snapshot; does not run commands
  shell/host/hyprland_backend.py  # the only Python that starts hyprctl
  shell/host/ui_contract.py   # border and wheel numbers; does not launch anything
  shell/modules/Tam/          # Commons and Ui
  adapters/clock-step1.patch  # imports, identity, offline gate, disabled edits
  adapters/build_patch.py     # regenerates that patch from the pinned revision
  fixtures/panel/             # tamlinux.fixture, not a fred.* plugin
  fixtures/compositor/        # tamlinux.compositor, reads the facade only
  fixtures/sway/              # ext-workspace, i3 IPC, inputs, bindsym fragment
  fixtures/ui/                # tamlinux.ui, constructs the shared controls
  tests/test_host.py
  tests/test_compositor.py
  tests/test_sway.py
  tests/test_ui.py
```

The launcher exports the pinned clock with `git archive`, applies the patch,
and checks the manifest before Quickshell starts. Entry points must be real
files inside the plugin root: duplicate ids, malformed manifests, missing
files, `..`, and symlinks are rejected.

## Launch

From this repository, with a sibling checkout of `clock-fred-tamlinux` (or
`TAMLINUX_CLOCK_SOURCE` pointing at one):

```sh
python3 desktop/launch-clock-proof --timeout 120
python3 desktop/launch-clock-proof --selftest --scale 1
python3 desktop/launch-clock-proof --selftest --scale 1.25
python3 desktop/launch-clock-proof --selftest --compositor sway --scale 1
```

The interactive bar sits on the bottom edge of the first screen and does not
reserve exclusive space, so the production layout is not reflowed. Choose a
connector with `--output NAME`, or `--output all`.

Isolated state is `$XDG_RUNTIME_DIR/tamlinux-clock-proof/`. The launcher
refuses to run without `XDG_RUNTIME_DIR`. The next launch replaces that state.
The proof environment unsets `OMARCHY_PATH` and sets `PATH` to `/usr/bin`.
`QML_IMPORT_PATH` is only `desktop/shell/modules`.

Stop an interactive proof with Ctrl-C. `--selftest` stops its own processes.

## Checks recorded 2026-10-03

Automated, on the development Wayland session:

- Host registry and settings tests passed, including duplicate ids, a malformed
  manifest, a missing entry, parent-path and symlink escapes, and a shared
  directory refused for settings.
- The adapter patch matches `build_patch.py` and the added lines do not import
  `qs.Commons` or keep the Omarchy menu and IPC targets.
- `--selftest --scale 1` and `--scale 1.25` each loaded the real clock, opened
  and closed the calendar through `tamlinux.clock` IPC, cycled the format from
  `dddd HH:mm` to `dddd h:mm AP`, wrote that format, and read it back on a
  second launch. `fetch-events.py` stayed suppressed. `createEvent` was
  refused. Dropping the selected output destroyed the bar and the popup.
  No proof helper process remained.
- Tooltip probe, not a pointer hover: scale 1 drew a 132×42 window at 11px;
  scale 1.25 drew a 168×54 window at 14px.
- The proof log did not mention the Omarchy shell tree, and the shell reported
  `OMARCHY_PATH` unset.
- Unchanged clock helper tests: `tests/test_fetch.py` and `tests/test_manage.py`
  passed. `tests/test_limits.py` had one failure (`test_oversized_remote_feed`,
  0 events instead of 1) in this environment. The proof does not modify those
  helpers.

Fred started this bar on 2026-10-03, said it looked fine, and then said
everything works. Local event creation is disabled in this slice on purpose.
The output check above removes the screen from the host model. That is a
simulated disappearance, not an unplugged monitor.

## Checks recorded 2026-10-03, host contract

Automated, on the development Wayland session, after the clock checks above:

- Registry acceptance of two plugin ids, rejection of a repeated id, settings
  writes for each registered id, and refusal of an unknown id.
- The fixture source does not register an IPC handler. The shell registers
  `tamlinux-shell` once.
- `--selftest --scale 1` and `--scale 1.25` kept the clock results: calendar
  open and close, format `dddd h:mm AP` across restart, refused event edit,
  fetch suppressed, and tooltip sizes 132×42 at 11px and 168×54 at 14px.
- The same runs loaded one clock and two fixture instances. Panel switch
  opened the fixture. The calendar took on-demand keyboard focus. The fixture
  recorded that it does not take focus. Opening the calendar closed the
  fixture on that host and left the other host's fixture open. A click target
  belonged to its own window and not the other. `summon("omarchy.osd")` was
  refused. Hide, toggle, and a fixture settings write succeeded.
- Dropping one of the two host copies destroyed that copy and left the other.
  Those two copies share one physical output, so that half of the check is
  simulated.
- With `--output all`, the shell saw three outputs. Dropping `HDMI-A-1`
  destroyed that bar and left the `DP-2` and `DP-1` bars in place.

## Checks recorded 2026-10-03, compositor contract

Automated, on the development Wayland session, after the host-contract checks:

- `desktop/tests/test_compositor.py` passed (9 tests). It builds argv for
  focus, DPMS, binds, and devices, and rejects bad output names and workspace
  ids, without running `hyprctl`. The adapter source matches those command
  templates. Other shell QML does not import `Quickshell.Hyprland` or mention
  `hyprctl`.
- `desktop/tests/test_host.py` still passed (11 tests).
- `--selftest --scale 1` and `--scale 1.25` kept the clock and host-contract
  results: calendar open and close, format `dddd h:mm AP` across restart,
  refused event edit, fetch suppressed, and tooltip sizes 132×42 at 11px and
  168×54 at 14px.
- The same runs compared adapter output names, the focused output, and active
  workspace ids with one `hyprctl -j monitors` snapshot. Bindings text and the
  keymap were non-empty and within their caps. Recorded focus and DPMS lines
  appeared. Live action lines did not. The proof log mentioned `hyprctl` only
  on the adapter's binds, devices, and monitors read lines.

## Checks recorded 2026-10-03, shared UI

Automated, on the development Wayland session, after the compositor checks:

- `desktop/tests/test_ui.py` passed (8 tests). Border specs use the fallback
  color and a uniform width, including when the section name is not a theme
  token. Wheel notches match `1,0 0,60 1,0 0,-20`. The action source does not
  start a process, and `Util` has `wheelSteps` without `execDetached`.
- `desktop/tests/test_host.py` still passed (11 tests).
  `desktop/tests/test_compositor.py` still passed (9 tests).
- `--selftest --scale 1` and `--scale 1.25` kept the clock, host, and
  compositor results, including tooltip sizes 132×42 at 11px and 168×54 at 14px.
- The same runs built every shared control on both host copies. Border evidence
  was `flat-top=2 surface-top=1 control-top=1 focus-accent=true
  normal-foreground=true overlay=false`. At scale 1 the tokens were display 24,
  large 28, subtitle 13, base 12, control 28, and status slot 21.
- `pickAgent`, `openTerminal("btop")`, `notify("status")`, and
  `openTimezoneMenu` were recorded. `openTerminal("sh")`, a shell-like notice,
  an over-long notice, and `bar.run("omarchy-agent --pick")` were refused.
  No new `omarchy-agent`, terminal, notification, timezone, or `btop` process
  appeared.

## Checks recorded 2026-10-03, plugin 2.0.0

Automated, on the development Wayland session:

- `desktop/tests/test_host.py`, `test_compositor.py`, and `test_ui.py` passed
  (28 tests).
- `--selftest --scale 1` and `--scale 1.25` kept the clock, host, compositor,
  and shared-UI results. The tooltip read `fred.clock v2.0.0`, at 132×42 / 11px
  and 168×54 / 14px.
- The same runs registered `fred.agents`, `fred.sysinfo`, `fred.weather`,
  `fred.tides`, `fred.keyboard`, `fred.monitor`, and `fred.workspaces` from
  their `develop/2.0.0` trees. No plugin-load failure and no `qs.Commons` or
  `qs.Ui` import in that log.
- Clock helper tests `test_fetch.py` and `test_manage.py` passed.
  `test_limits.py` still has the known `test_oversized_remote_feed` failure
  (0 events instead of 1). `fred.sysinfo`, `fred.monitor`, and
  `fred.workspaces` Python tests passed.
- On 2026-10-03 the helper command move was checked: compositor tests
  passed (17), host tests passed (11), UI tests passed (8), workspace
  desktop-mode tests passed (42), monitor layout tests passed (10), and
  monitor state tests passed (3). `--plugins --selftest` at scale 1 and
  1.25 registered all eight plugins and rejected any live compositor action.

## Checks recorded 2026-10-04, Sway adapter

Automated, on the development Wayland session:

- `desktop/tests/test_sway.py` passed (11). The ext-workspace fixture wins
  over a different i3 workspace list. `exec`, `include`, and other bind
  commands are dropped. The modules do not start a process.
- `desktop/tests/test_compositor.py` still passed (17).
- `--selftest --compositor sway` at scale 1 and 1.25 published the fixture
  output names, workspace ids, keymap, and binding bytes. Focus and DPMS were
  recorded. The log did not contain `hyprctl` or `swaymsg`, and no `swaymsg`
  process was running.
- `--selftest` at scale 1 and 1.25 still loaded the Hyprland adapter, checked
  the physical outputs, and registered all eight plugins. The Sway adapter was
  not loaded.

## Limits

This is a Develop candidate. It does not install a package, switch the
production shell, or prove a Void target session. The eight plugins load in
the isolated host. They are not the running bar. Typed actions record the
request during the proof. They start the existing programs only when
`TAMLINUX_HOST_ACTIONS=1`, which `launch-daily-bar --replace` sets and the
proof unsets. Plugin QML does not import Hyprland or start `hyprctl`.
The develop workspace and monitor helpers call the named Hyprland backend
instead of building Hyprland commands. The shell's Hyprland adapter remains
the only Hyprland import in `desktop/`. The Sway adapter fills the same
facade from fixtures and does not start `swaymsg`. Those helpers do not have
a Sway backend yet. Live compositor actions stay off unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`, and the proof never sets that flag.
Replacing the running bar is `desktop/launch-daily-bar --replace` after this
candidate is accepted. That acceptance is Tamlinux 0.1.
