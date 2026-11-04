# Develop a component, then package it

Use the checkout's `commands/tam-dev/tam-dev` before it is delivered as `tam-dev`.

```sh
tam-dev try command:tam-hardware
tam-dev try app:keybindings
tam-dev try app:keyboard
tam-dev try plugin:fred.keyboard
tam-dev try shell
tam-dev try shell --live
tam-dev status
tam-dev stop shell
```

Other native components are `tam`, `libtam`, and `tamlinux-tools`. `build` prepares the local output; `check` runs its focused checks; `try` checks and starts the trial. Dirty working trees are supported. No operation invokes Nix, commits source, changes assembly pins or allocates a candidate version.

Commands are exposed through the user development prefix. Clear your terminal's command cache with `hash -r` when switching. Session bindings can have a different PATH; use the reported absolute launcher for a deliberate command trial. Preview apps have their own Quickshell configuration paths. Shell/plugin previews use isolated settings and do not claim desktop services. Plugins that create a `PanelWindow` while loading need a real output; their offscreen `widget-proof` check may fail, so use `tam-dev try plugin:NAME --live` for integration (it skips that offscreen proof). Live trials require the paired `tam-shell` routing capability delivered with this workflow. Older installations use separate previews. Use `--live` when actual desktop integration is needed: it deliberately stops the packaged shell; a recorded IPC selection routes commands to it, and its supervisor restores the packaged service when the trial exits. Package links and service definitions remain unchanged. `stop` also restores the service. Never start a second live shell trial.

Status identifies the source content, revision, dirty state, output and whether the source changed since building. Keep a trial current before selecting it for a candidate. Native build dependencies must already be available; a missing dependency is an explicit build error, not an implicit package installation.

Builds retain the four most recent completed entries per component plus any active or referenced fallback. Build/check subprocesses have a five-minute limit. Builds and trial records live under `$XDG_STATE_HOME/tamlinux/development`. Trials are development feedback. Packaged Test observations must refer to the selected assembly and actual installed endpoints. Stop superseded trials during handover, preserving newer overrides. The candidate integration manages this handover for registered trials.
