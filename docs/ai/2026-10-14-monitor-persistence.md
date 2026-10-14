# 2026-10-14 — Preserve saved monitor geometry during workspace reconciliation

- **CLI Tool**: Codex CLI `0.162.1`, dynamically checked.
- **Model**: `gpt-6.1-sol`, verified from runtime metadata.
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Resume from the Tamlinux 0.4.3 handoff.

An isolated compositor trace identifies `tam-desktop-mode`, launched by the
workspace widget, as the writer replacing a saved center display position with
0x0. Its layout reader used the prior configuration path. When that path had
no layout, connector names from retained workspace state became invented
1920-pixel geometry and were then applied as monitor rules.

The helper now reads `tamlinux/hypr/monitors.lua`, matching the session and Display
panel. Workspace topology names retain slot identity without claiming physical
coordinates. Geometry reconciliation requires explicit saved positions and
supports signed coordinates; automatic or computed positions stay with the
compositor.

Verification: the original helper fails the new stale-layout and invented-position
regressions. All 57 workspace helper tests pass after correction, including signed
coordinate restoration. Installed-output transition checks are recorded separately.

Paired committed-output verification: 512 desktop checks pass with one existing
skip; the fresh-session contract builds and 76 isolated installed-output probes
pass. Three VM trials preserve saved positions after VT transitions and output
reconnection. The physical preview retains its previous generation and GTK/settings
checkpoint with unchanged saved layout bytes. The user reports, “Order and mouse
path stay correct,” after two returns to the preview desktop.

Recovery preparation adds explicit custom Claude/T3 Code and Obsidian vault roots
to the finite checkpoint, including the vault registry. The CLI binds restoration
to the captured roots; personal vault notes remain outside the selected theme
tree. Twenty-one settings recovery checks pass, including actual GTK values.

Native DNS gains an explicit read-only checkpoint and restoring operation. The
fixed native executor captures both DNS files, original permission modes and
absences, four fields per Ethernet/Wi-Fi profile and service states. It archives
later values, validates original digests/destinations, refuses concurrent changes
and supports retry after partial restoration. Eight regressions pass against real
files and a bounded daemon fixture; installed native verification follows.

The user also confirms physical lock/unlock with the preview account password
returns to the same display arrangement. Installed recovery executes in the
isolated Arch VM: original custom application/vault themes, GTK explicit/unset
values, live configuration and monitor layout restore; later writes are archived
and vault notes remain intact. The native DNS checkpoint restores original
file bytes/modes/absences and profile fields, archives later settings and passes
a repeated restoration. Fixture connections are removed and initial native
services and routing restored. Paired commands output is bound to product
`8c36863` and delivery `e8b641d`; package checks pass after correcting the
native-systemctl fixture. This is preparation, with complete recovery and the
normal-account Test kit still open.

Speaker-tuning recovery now includes its six fixed files and enablement link.
Optional audio capture binds connected sink/source channel volumes, mutes and
default names plus the owned tuning unit active/enabled state. Restoration
archives later values before stopping the owned client, restores files and
verified audio values, refuses missing devices/channels and supports interrupted
retry. Delivery supplies the systemd and Pulse clients explicitly. The complete
desktop suite runs 529 checks with one existing skip; installed PipeWire proof
follows. Persistent WirePlumber routes and legacy tuning conversion remain open.

Installed audio recovery passes against native PipeWire in the isolated VM,
using temporary null sinks and a harmless user service fixture. Original file
bytes/modes/links, default input/output, individual channel volumes and mutes,
and service active/enabled state restore; later files/audio values archive and
a repeated restoration passes. Fixture files/services/devices are removed and
initial defaults restored. This proves the recovery interfaces, with physical
DSP/device behavior and persistent WirePlumber routes remaining outside scope.
A fresh physical preview login has zero runtime collector findings: both the
compositor and shell environments are clean. The user reports a missing keypad
shortcut; the preview had not received the reference account personal workspace
overrides. Those overrides are retained separately as consumer preferences.

Read-only normal-account inventory finds native `asdcontrol` already installed,
while the other new integration endpoints are absent. The development native
bundle previously claimed that same binary path. It now owns
`/usr/lib/tamlinux/asdcontrol`; the fixed brightness caller, Polkit action and
collector agree on that endpoint. Existing native packages can remain installed
through Desktop Test. The native development recipe advances to release 0.2;
source staging checks pass, with archive/build validation following.

The fresh preview keypad callbacks still could not switch desktops after the
personal overrides were copied. Their standalone helper endpoint was absent,
and the raw plugin script depends on backend/live-action variables supplied
only by the shell. A new `tam-desktop-mode` command installs the same engine
with paired immutable backend modules and an explicit live-action environment.
Existing direct consumer links to the raw plugin need removal from the eventual
Test consumer. The current normal-account session remains unchanged.
