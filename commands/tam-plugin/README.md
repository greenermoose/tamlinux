# tam-plugin

## What it does

`tam-plugin` lists, inspects and moves `fred.*` shell plugins through the
lifecycle stages on a workstation: `dev` points the running plugin at a
checkout, `test` loads an exact snapshot with a recorded payload digest, `run`
activates the accepted candidate through Home Manager and records it, `verify`
compares the published and deployed payloads, and `restore` recovers from a
stuck override. `tam-plugin help` lists every command.

## Install

```bash
make check
make install   # honours PREFIX and DESTDIR
```

## Configuration

| Variable | Default |
| --- | --- |
| `FRED_CONFIG_REPO` | The one checkout under `~/Code/tamlinux/` that contains `config/tamlinux/plugins` |
| `TAMLINUX_HOME_CONFIGURATION` | The current user name (`home-manager switch --flake <repo>#<name>`) |
| `FRED_PUBLISHED_ROOT` | `~/Code/tamlinux` |
| `TAMLINUX_REGISTRY` | `~/.local/share/tamlinux/shell/host/registry.py` |

## Status

This is the Tamlinux 2.0.0 tool, moved here from a private workstation
configuration on 2026-10-09 with its behaviour unchanged. The Omarchy-era
1.x tool stays in the frozen `plugin-fred-tamlinux` repository. Its next
change makes Test and Run deploy package outputs built by
[`tamlinux-packages`](https://github.com/greenermoose/tamlinux-packages) and
resolves published plugins from `desktop/plugins/` in this repository.
