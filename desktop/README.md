# Tamlinux shell proof

Develop-stage host for pinned `fred.clock` 1.3.3, with a read-only calendar,
plus a small fixture widget that is not a `fred.*` plugin. It runs outside
the Omarchy shell and does not replace the running desktop. Stopping the
proof process and deleting its isolated state is the recovery path.

Pinned clock revision: `ed5140ccefc83c0a2fdd5f899bbd290acc35d88a`.
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
| `bar.run` | agents, sysinfo, weather, clock | Logged and not executed. The call sites are `omarchy-agent --pick`, `omarchy-launch-terminal btop`, `omarchy-notification-send`, and `omarchy-menu-timezone`. |

`Tam.Commons` and `Tam.Ui` still cover only the types the clock constructs.
These shared types are used by the other plugins and are not built yet:
`Border`, `BarIconButton`, `BorderSurface`, `CursorSurface`, `Dropdown`,
`PanelHero`, `PanelSectionHeader`, `PanelSlider`, and `ToggleSwitch`.

## Compositor contract

Shell UI and fixtures read `desktop/shell/host/Compositor.qml`.
`HyprlandAdapter.qml` is the only shell file that imports
`Quickshell.Hyprland` or starts `/usr/bin/hyprctl`. There is no generic
`hyprctl` argument list. `desktop/shell/host/compositor_commands.py` builds
the same argv for tests and does not run it.

The facade exposes plain data:

- outputs: name, focused flag, active workspace id, `dpmsOn`
- `focusedOutputName` and `outputForScreen(screen)`
- workspaces: id, output name, occupied, bounded window summaries
- `focusedWorkspaceId`, `bindingsText`, `activeKeymap`
- a revision counter that changes when the snapshot changes

Named actions are `focusWorkspace(id)`, `focusOutput(name)`, and
`setDpms(name, on)`. They record the request unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. The proof launcher removes that
variable, so a selftest cannot blank a display or move focus. Output names
must match `^[A-Za-z0-9._-]{1,64}$`. Workspace ids are 1 through 10. Reads
are the fixed commands `binds`, `-j devices`, and `-j monitors`, each with
`PATH=/usr/bin`, the Wayland runtime directory, the Hyprland instance
signature, and a four-second deadline. Bindings text, the keymap, and window
summaries are capped. Layout rewrite, `hyprctl reload`, and monitor reset
stay out of this slice.

`desktop/fixtures/compositor/` is `tamlinux.compositor`. It reads the facade
and logs names, counts, the keymap, and whether the screen matches an output.
It does not import Hyprland. The seven plugins are unchanged and still talk
to Hyprland themselves.

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

## Layout

```text
desktop/
  launch-clock-proof          # stage, launch, and --selftest
  shell/shell.qml             # named config root
  shell/host/                 # bar, settings writes, manifest checks
  shell/host/Compositor.qml   # facade the shell and fixtures read
  shell/host/HyprlandAdapter.qml
  shell/host/compositor_commands.py
  shell/modules/Tam/          # Commons and Ui
  adapters/clock-step1.patch  # imports, identity, offline gate, disabled edits
  adapters/build_patch.py     # regenerates that patch from the pinned revision
  fixtures/panel/             # tamlinux.fixture, not a fred.* plugin
  fixtures/compositor/        # tamlinux.compositor, reads the facade only
  tests/test_host.py
  tests/test_compositor.py
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

## Limits

This is a Develop candidate. It does not install a package, switch the
production shell, or prove a Void target session. The other seven plugins are
not loaded and are not pointed at the facade yet. The Hyprland adapter is the
only new Hyprland import in this tree. A Sway backend and the one-command
install are later steps. Live compositor actions stay off unless
`TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`, and the proof never sets that flag.
