# tam-plugin

## What it does

`tam-plugin` lists and inspects `fred.*` shell plugins and helps develop them.
`dev` points a running plugin at its source in a Tamlinux checkout for fast
iteration and `dev off` restores the installed package; `diff` and `verify`
compare the installed plugin with its source; `restore` recovers from a
stuck override. `tam-plugin help` lists every command.

`dev` is not a deployment. Plugins are tested and run as part of the
Tamlinux package with [`tam-deploy`](../tam-deploy/README.md); the `test` and
`run` commands of tam-plugin 2.x were removed in 3.0.0.

## Install

```bash
make check
make install   # honours PREFIX and DESTDIR
```

## Configuration

| Variable | Default |
| --- | --- |
| `TAMLINUX_SOURCE_REPO` | `~/Code/tamlinux/tamlinux`; plugin sources are in its `desktop/plugins/` |
| `FRED_PUBLISHED_ROOT` | `~/Code/tamlinux` |
| `FRED_LIVE_DIR` | `~/.config/tamlinux/plugins` |
| `TAMLINUX_REGISTRY` | `~/.local/share/tamlinux/shell/host/registry.py` |

## Status

Moved here from a private workstation configuration on 2026-10-09. Version
3.0.0 reads plugin sources from this repository and leaves Test and Run to
`tam-deploy`. The Omarchy-era 1.x tool stays in the frozen
`plugin-fred-tamlinux` repository.
