# Tamlinux desktop shell

Product shell, host contract, and session services for Hyprland/Quickshell.
Plugin payloads live under [`plugins/`](plugins/README.md).

Historical 2026-10-03 shell-proof check dumps and Omarchy-era proof narrative
were removed from this file in the 2026-10-31 docs prune; retrieve the full
pre-prune text with `git show 020c8dc:desktop/README.md` (see
[FILING-CARD.md](FILING-CARD.md)).

## Start menu (0.5.10)

Right-click unused bar space, or press SUPER and right-click anywhere, to
open Start near the pointer. It exposes Quick Launch and Settings in one
searchable list. Occupied bar widgets retain their own right-click behavior.
SUPER + ALT + right-drag resizes windows.

Settings offers Color Palette, Text Size, Background and Bar Position.
`tam-menu toggle start` opens the combined view; `tam-menu toggle quicklaunch`
remains available. See the [approved plan](../docs/plans/start-menu.md).

## Console-first startup

Tamlinux boots through visible text progress to a text login. The optional
desktop starts when the signed-in user runs `tam-desktop` on a local
foreground console. There is no graphical login manager. See
[console-first-startup.md](../docs/plans/console-first-startup.md).

## Names

*The Tamlinux shell* is one Quickshell configuration that draws the bar and
panels and runs session services. *Host* in this directory means the plugin
host contract in `shell/host/` (registry, settings, popouts, IPC, compositor
facade). Elsewhere, *host* means the distribution the workstation package is
installed on.

*Ported* code was copied from Omarchy (MIT, notice kept), adapted to
Tamlinux, and is maintained here; headers say `Ported from omarchy …`.

## Host contract

Each output gets its own bar object from `desktop/shell/host/BarApi.qml`.
Plugin source is not copied into this directory.

| Call | Who uses it | Host behavior |
| --- | --- | --- |
| `foreground`, `fontFamily`, `position`, `urgent`, `barSize` | all plugins | Top or bottom bar, horizontal, owned palette and type scale. |
| `bar.screen.name` | weather, tides | The output this bar was built for. |
| `setting()` / `updateEntryInline` | clock | Scalar writes for a registered id. |
| `moduleWidgets` | workspaces | Every live instance of that id, across outputs. |
| `requestPopout` / `releasePopout` | keyboard, monitor, sysinfo, weather, tides, clock | One open popup per output. |
| `switchPanelFrom` | clock, weather, tides | Opens the next widget on that output with `open`/`close`. |
| `showTooltip` / `hideTooltip` | sysinfo, monitor, shared buttons | Separate overlay; size follows `TAMLINUX_UI_SCALE`. |
| `shell.summon` / `hide` / `toggle` | monitor | Registered panel on the focused output. |
| `compositor.*` keyboard helpers | keyboard layout widget | From the Hyprland adapter. |
| `pickAgent()` | agents | `$TAMLINUX_BIN/tam-agent --pick` when actions are enabled. |
| `openTerminal(program)` | sysinfo, menu | Bounded program names only. |
| `notify(text)` | weather | Plain notice up to 512 characters when actions are enabled. |

`Tam.Commons` and `Tam.Ui` supply shared types and tokens. There is no
`execDetached`. Plugins import `Tam.Commons` and `Tam.Ui` from their own trees.

## Compositor contract

Shell UI reads `desktop/shell/host/Compositor.qml`.
`HyprlandAdapter.qml` is the only shell file that imports
`Quickshell.Hyprland` or starts `/usr/bin/hyprctl`.
`SwayAdapter.qml` loads only when `TAMLINUX_COMPOSITOR=sway`.

Named actions (`focusWorkspace`, `focusOutput`, `setDpms`) record the request
unless `TAMLINUX_COMPOSITOR_LIVE_ACTIONS=1`. Protocol proof:

```sh
python3 desktop/launch-protocol-proof
```

## Session services

`shell/host/Services.qml` loads services named in `TAMLINUX_SERVICES`
(comma-separated). `TAMLINUX_BAR=0` runs services without a bar.

| Service | Role |
| --- | --- |
| `notifications` | Freedesktop notifications, DND, history |
| `osd` | Volume/brightness/status overlays |
| `clipboard` | Clipboard history picker |
| `emojis` | Emoji picker |
| `imagepicker` | Image carousel for pickers |
| `reminders` | Timed reminder cards |
| `menu` | Command menu / Start |
| `background` | Desktop background layer |
| `polkit` | Session polkit agent |
| `media` | MPRIS media keys |
| `battery` | Low-battery warning and power profiles |
| `idle` | Stay Awake / idle lock |
| `theme` | Palette apply without restarting the shell |

## Layout

```text
desktop/
  shell/shell.qml
  shell/host/          # bar API, compositor facade, adapters
  shell/services/      # session services
  shell/modules/Tam/   # Commons and Ui
  plugins/             # fred.* payloads
  tests/
```

## Theme

`tam-shell theme reload` applies validated colors to `Tam.Commons`.
Import `Tam.Commons as Commons` (unqualified `Color` can mean QtQuick's type).
Headless checks: `python3 desktop/check-theme --quickshell /path/to/quickshell`.
Full Tamarack design is a separate milestone ([theme-system.md](../docs/plans/theme-system.md)).

The daily session starter is `shell/host/session_start.py`. It builds plugin
entries from `~/.config/tamlinux/plugins/` and reads
`~/.config/tamlinux/shell/{layout,settings}.json`.
