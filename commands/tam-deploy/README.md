# tam-deploy

## What it does

`tam-deploy` installs a Tamlinux package assembly on a workstation through
Home Manager. Test and Run use the same package and the same installed
locations; only the evidence and the branch differ. An assembly is a
[`tamlinux-packages`](https://github.com/greenermoose/tamlinux-packages)
revision whose lock file pins every component.

| Command | Effect |
| --- | --- |
| `status` | Show the pinned assembly, its component revisions, the installed shell revision, the stage and the generation; report any installed path outside the assembly's packages. |
| `test [revision]` | Require the assembly and each pinned component to be on `test`. Pin the revision (default: the head of `test`) in the configuration lock, switch Home Manager, restart the shell, verify the installed paths and commit the pin. A failure restores the lock and the previous generation. |
| `run [revision] [--untested]` | Make an assembly the daily one and move it onto `main`. Without a revision: promote the installed Test to `main` without rebuilding, or report that a `main` commit is already running. With a revision (any `tamlinux-packages` commit, full or abbreviated): install it if needed, then fast-forward `main`; a `main` commit (including an older one) moves no branch. A commit, or a component it pins, that is only on `develop` or another branch is untested and needs `--untested`; it then moves `test` too. A revision `main` cannot fast-forward to is refused. |
| `back` | Activate the previous generation and restore its pin. |

The rollback pin identifies the assembly actually running, using the deployment
record for the active generation. A prepared but inactive consumer lock is not
the rollback assembly. Without a matching record, the current lock must match
the installed source revision; otherwise deployment stops before activation.
Back records the restored generation and components for subsequent deployments.

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
| `TAMLINUX_HOME_CONFIGURATION` | The current user name (`home-manager switch --flake <repo>#<name>`) |
| `TAMLINUX_WORKSPACE` | `~/Code/tamlinux`, holding clones of `tamlinux-packages` and each component |
| `TAMLINUX_PACKAGES_INPUT` | `tamlinux-packages`, the configuration's flake input |
| `TAMLINUX_GITHUB_OWNER` | `greenermoose` |

The configuration's `tamlinux-packages` input must name the repository
without a revision (for example `github:greenermoose/tamlinux-packages`); the
lock file holds the exact revision.
