# tam-shell-deploy

## What it does

`tam-shell-deploy` moves the Tamlinux shell between lifecycle stages on a
workstation whose Home Manager configuration pins this repository as its
`tamlinux` flake input.

| Command | Effect |
| --- | --- |
| `status` | Show the deployed, locked and `main` revisions and the active generation. |
| `test <commit>` | Deploy a committed ancestor of `main` with `--override-input`, leaving the lock file unchanged. |
| `run` | Pin the tested revision (or `main`), switch Home Manager, record the revision and commit the pin. |
| `back` | Activate the previous Home Manager generation and restart the shell services. |

## Install

```bash
make check
make install   # honours PREFIX and DESTDIR
```

## Configuration

| Variable | Default |
| --- | --- |
| `TAMLINUX_CONFIG_REPO` | The one checkout under `~/Code/tamlinux/` that contains `config/tamlinux/plugins` |
| `TAMLINUX_HOME_CONFIGURATION` | The current user name (`home-manager switch --flake <repo>#<name>`) |
| `TAMLINUX_SOURCE_REPO` | `~/Code/tamlinux/tamlinux` |

## Status

Moved here from a private workstation configuration on 2026-10-09 with its
behaviour unchanged. It still deploys source revisions directly. Its next
change makes Test and Run deploy package outputs built by
[`tamlinux-packages`](https://github.com/greenermoose/tamlinux-packages), and
take Test candidates from the `test` branch.
