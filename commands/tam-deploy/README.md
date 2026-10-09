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
| `run` | Require a deployed Test of the pinned assembly whose installation still verifies. Fast-forward `main` of each component, then of `tamlinux-packages`, to the tested revisions. Nothing is rebuilt. |
| `back` | Activate the previous generation and restore its pin. |

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
