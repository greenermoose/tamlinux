# Tamlinux shell proof

Develop-stage host for one real plugin: pinned `fred.clock` 1.3.3, with a
read-only calendar, running outside the Omarchy shell. This does not replace
the running desktop. Stopping the proof process and deleting its isolated
state is the recovery path.

Pinned clock revision: `ed5140ccefc83c0a2fdd5f899bbd290acc35d88a`.
Development closure checked here: Quickshell 0.3.1, Qt 6.11.2.

## Host contract

The clock still expects a bar object. This host supplies that object from
`desktop/shell/host/BarApi.qml`.

| Clock use | Host behavior |
| --- | --- |
| `bar.foreground`, `fontFamily`, `vertical`, `position`, `barSize` | Bottom bar, horizontal, owned palette and type scale. |
| `setting()` / `settings` | Inline entry `fred.clock` in the proof settings file. |
| `bar.shell.updateEntryInline` | Validates scalar values and writes that entry. Unknown ids are refused. |
| `bar.moduleWidgets` | Returns the live clock instance for `fred.clock`. |
| `requestPopout` / `releasePopout` | One open popup. Opening another closes the current one. |
| `registerClickTarget` / `unregisterClickTarget` | Bar clicks are forwarded while the calendar overlay is open. |
| `showTooltip` / `hideTooltip` | Separate overlay window. Size follows `TAMLINUX_UI_SCALE`. |
| `bar.run` / timezone / event edit | Logged as unsupported and not executed. |
| Panel open, close, Escape wiring, outside click | Owned `KeyboardPanel`. Escape is handled by `PanelKeyCatcher`. |

Shared modules are `Tam.Commons` and `Tam.Ui`. They cover the types the clock
actually constructs, including `TextField`, and they do not read an Omarchy
theme directory. IPC targets in this proof are `tamlinux-shell` and
`tamlinux.clock`. The proof does not register `omarchy.clock` or `fred.clock`.

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
  shell/modules/Tam/          # Commons and Ui
  adapters/clock-step1.patch  # imports, identity, offline gate, disabled edits
  adapters/build_patch.py     # regenerates that patch from the pinned revision
  tests/test_host.py
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

## Limits

This is a Develop candidate. It does not install a package, switch the
production shell, or prove an antiX session. Compositor backends, the other
seven plugins, and the one-command install are later steps.
