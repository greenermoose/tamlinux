# tam-deploy

## What it does

`tam-deploy` installs a Tamlinux package assembly on a workstation through
Home Manager. Test and Run use the same package and the same installed
locations; only the evidence and the branch differ. An assembly is a
[`tamlinux-packages`](https://github.com/greenermoose/tamlinux-packages)
revision whose lock file pins every component.

| Command | Effect |
| --- | --- |
| `status` | Show the pinned assembly, its component revisions, the installed shell revision, the stage and the generation; compare required endpoints with the exact selected package outputs, rejecting missing/broken links and mixed assemblies. |
| `init [revision] [--test]` | First installation on a registered local host without an existing generation. Require all components on `main` (or `test` with `--test`), build the exact consumer generation, activate and verify its package endpoints. Works from a text session without a Home Manager CLI. Records no previous generation; never promotes branches or enables graphical login. |
| `test [revision]` | Require the assembly and each pinned component to be on `test`. Pin the revision (default: the head of `test`) in the configuration lock, switch Home Manager, restart the shell if active, verify the installed paths and commit the pin. Activation or verification failure attempts to restore the lock and previous generation. |
| `run [revision] [--untested]` | Make an assembly the daily one and move it onto `main`. Without a revision: promote the installed Test to `main` without rebuilding, or report that a `main` commit is already running. With a revision (any `tamlinux-packages` commit, full or abbreviated): install it if needed, then fast-forward `main`; a `main` commit (including an older one) moves no branch. A commit, or a component it pins, that is only on `develop` or another branch is untested and needs `--untested`; it then moves `test` too. A revision `main` cannot fast-forward to is refused. |
| `back` | Activate the previous generation and restore its pin. |

The rollback pin identifies the assembly actually running, using the deployment
record for the active generation. A prepared but inactive consumer lock is not
the rollback assembly. Without a matching record, the current lock must match
the installed source revision; otherwise deployment stops before activation.
Back identifies its return pin from the active deployment record too, so a staged consumer lock cannot pair the old generation with a newer assembly. It records the restored generation and components for subsequent deployments.

Promote a candidate from `develop` to `test` (a fast-forward push) before
`tam-deploy test`; `tam-deploy` never resolves a moving branch at build time.

## Install

```bash
make check
make install   # honours PREFIX and DESTDIR
```

## Configuration

| Variable | Default |
| --- | --- |
| `TAMLINUX_CONFIG_REPO` | The one checkout under `~/Code/tamlinux/` whose `flake.lock` has a `tamlinux-packages` input |
| `TAMLINUX_HOME_CONFIGURATION` | The registered local `user@hostname`; a different host's output is refused. Legacy configurations without `hosts/` retain the current user name. |
| `TAMLINUX_WORKSPACE` | `~/Code/tamlinux`, holding clones of `tamlinux-packages` and each component |
| `TAMLINUX_PACKAGES_INPUT` | `tamlinux-packages`, the configuration's flake input |
| `TAMLINUX_GITHUB_OWNER` | `greenermoose` |

The configuration's `tamlinux-packages` input must name the repository
without a revision (for example `github:greenermoose/tamlinux-packages`); the
lock file holds the exact revision.

`test` and `run` refuse while the configuration has uncommitted or untracked
changes, so every generation has an identifiable configuration commit. Two
kinds of path are exempt: the deployment records (`system/bom.json`,
`system/plugin-runs`) and the files listed in `system/live-paths`, one
repository-relative path per line (`#` comments allowed). List only files the
running session writes through a Home Manager live (out-of-store) link, such as
the shell's `settings.json`: their content is not part of a generation. Their
SHA-256 at deployment is recorded as `livePaths` in the deployment state.

## Exact endpoint verification

The command evaluates `packages.<system>` at the committed assembly revision
through its local Git history and compares resolved endpoints with those exact
store outputs. It checks the shell, every selected plugin, every product
command, tam, tam-file-select, and the menu/tam-man endpoints when the assembly
provides them. Missing files, broken links, unexpected plugins and old packages
fail verification. The installed `deployment-selection.json` records intentional
plugin subsets; its IDs and product revision must agree with the assembly.
Older assemblies without that record are checked against their full plugin set.
Nix evaluation must succeed; no name-pattern fallback declares a match.

## First installation from a console

Register the machine in the consumer configuration before installing. Keep a
verified native-base recovery snapshot and boot medium: there is no previous
Home Manager generation. Review conflicting account files before activation.
The command can be entered through the exact assembly's command package:

```sh
nix shell github:greenermoose/tamlinux-packages/<assembly-revision>#tamlinux-commands \
  --command tam-deploy init <assembly-revision>
```

Only an assembly whose components are already on `main` is accepted by default.
An explicitly authorized Test installation uses `--test`; it requires the
assembly and components on `test` and never promotes them. `init` installs
the package and records endpoints; physical console and graphical acceptance
remain separate. It never starts a display manager or compositor.

Build failure restores the previous lock before any account activation. An
activation/verification failure retains `first-install.json` beside the local
deployment record with the attempted assembly, generation and previous lock.
It refuses an automatic retry rather than claiming recovery without a prior
generation. Inspect partial links and restore from the native-base recovery
point before retrying. Ordinary upgrades continue to require a known rollback
generation. From a text login with no active graphical session, activation and
rollback do not start the desktop or require shell IPC. If a graphical session
is active, the shell is restarted and checked. An unavailable user service
manager or ambiguous session state stops the operation.

If recovery fails after an installation error, or recording fails after an
activation, the generation, consumer lock and deployment record may disagree.
The same is true if rollback fails after activation is attempted. Inspect
`tam-deploy status`, the active generation and the consumer lock before
retrying; the error does not claim that the prior state was restored.
