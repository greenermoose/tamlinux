## Session: 2026-10-14/15 — Protocol-state crash fix and native system defaults (0.4.3 Develop)

- **CLI Tool**: Claude Code (`claude`) `2.1.300`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Commits**: `354eae8` (protocol state), `f43e7c8` (native defaults)
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > I've got codex started on a new session for Tamlinux 0.4.3. See what you can do to help. Keep out of its way, but do things that will help us get to a 0.4.3 that works well.

  > 1

  > Codex has release claims. Please proceed with what you can do.

  "1" selected the recommended option: fix `ProtocolState.qml` rather than
  disable the protocol shadow trial.

- **Key Decisions & Implementation Notes**:
  - Two shell crashes on the development workstation were a use-after-free in
    `Qt::endPropertyUpdateGroup` while Quickshell committed an ext-workspace
    batch during a display hotplug. The freed observer memory held the
    `"$" + outputName` keys that `protocol_model.js` builds, so the
    `ProtocolState.snapshot` binding was re-capturing its observers inside the
    group's notification pass. The shell only loads that path in protocol
    shadow/proof mode.
  - `ProtocolState` now polls the models every 250 ms with plain reads and
    publishes a snapshot only when its JSON changes. No QML binding observes
    the protocol bindables. A guard test forbids reintroducing one. The shadow
    ID hashes this file, so the shadow-period count restarts at deployment.
  - Native defaults: 23 entries under `desktop/native/defaults/root`, vendor
    locations only (`/usr/lib`, `/usr/share`), Tamlinux names, values
    unchanged from the previous owner's package (MIT, recorded in
    `origins.json`). Names collide with no installed package, so the files
    coexist with the previous owner until Cutover.
  - `tam-fcitx5` and `tam-bt-agent` (D145) ship enabled for graphical
    sessions. The pairing agent was renamed from `bt-agent.service` after the
    built package showed that name was already owned; it now starts after and
    skips while any `bt-agent.service` is active, so two agents never run.
  - Settings that live in a single file owned by another package (faillock,
    nsswitch, CUPS, skel, dirmngr, Docker `daemon.json`, MIME and terminal
    lists) and their paired settings are deliberately absent; they need a
    preserving adapter with recovery. The inotify limit needs nothing: Arch's
    `filesystem` package already sets it.
- **Verification**:
  - Protocol and shadow tests (14) and Sway tests (11) pass; the new guard
    fails on the previous file; a windowless live read returned a ready
    snapshot of three outputs and four workspaces.
  - Native defaults tests (8) pass, including real fontconfig resolution of
    `sans-serif`, `system-ui` and `-apple-system` to Liberation Sans.
    `systemd-analyze verify` passes for both user units, logind's merged
    configuration shows `HandlePowerKey=ignore`, and zram-generator against
    the tree creates `/dev/zram0` sized to RAM at priority 100.
  - Full desktop suite: 544 run, one existing skip.

### Addendum: per-user bash defaults and keyserver list

- **Commit**: `7ab8820`
- **Prompts** (after Claude compared per-user and system delivery):
  > Go with your recommendations for both
- **Key Decisions & Implementation Notes**:
  - `desktop/user-defaults/bash` is the bash default set with the inherited
    environment variable, configuration-path handling and command completion
    removed; `env` keeps only the user tool paths.
  - A fresh Arch account already has the skeleton `~/.bashrc`, so "write only
    when missing" would never fire. `apply` instead adds a marked env block at
    the top (before the skeleton's non-interactive return) and an rc block at
    the end (after its `ls` alias), once, keeping the original. A linked
    `~/.bashrc` belongs to another manager and is left alone.
  - `~/.gnupg/dirmngr.conf` is written only when missing and not recreated
    after deletion. GnuPG 2.4.9 reads it when present, the system file otherwise.
  - `--remove` takes out exactly those changes and keeps later edits.
- **Verification**: 8 new tests run real interactive and non-interactive bash
  against the Arch skeleton; full desktop suite 552 run, one existing skip.
