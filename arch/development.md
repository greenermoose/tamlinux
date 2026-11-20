# Develop a component, then package it

## Build a native product tree

The top-level `make` builds the six native C commands against installed
libtam. `make install PREFIX=/usr/lib/tamlinux/current DESTDIR=/tmp/stage`
installs all commands, the shell, plugins, assets, menus and user units
under that prefix. It does not activate a service or write user settings.
`make check-install` checks the shared product data and its reproducibility.

Build dependencies include a C compiler, make, pkg-config, libtam with its
display/session libraries, libcpuid, libsystemd, libmagic, and Python with
FontTools for the owned icon font. Other fonts and runtime programs are
native dependencies, rather than copied into the product. Version notes
come from the packaging recipe; source identity is recorded in `BUNDLE`.
Native adapters own system-wide integration. Product units are installed
under `share/systemd/user` with stable paths in the selected prefix.

## Try one component

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

## Run the whole test suite

`desktop/check-all` runs every test file in `desktop/tests`, `make check` in every command, and the headless `check-panels` and `check-theme`, each alone with a time limit. It works from a clean clone with session variables removed, so uncommitted edits are not tested and results do not depend on being in a desktop session. It reports failures, skip reasons and core dumps the run left, and exits non-zero if any unit failed or a test left a core dump. Commands that link `libtam` need a current development `libtam`, including its display libraries.

`--rev REVISION` tests another revision. `--proofs` also enables the opt-in proofs, which start real programs under private headless compositors; warn whoever is at the machine first. `desktop/check-live` is separate because it drives the real screens.

A candidate must pass this suite at its frozen revision before Test.
