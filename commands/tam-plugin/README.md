# tam-plugin

## What it does

`tam-plugin` lists and inspects `fred.*` shell plugins and helps develop them.
`dev` points a running plugin at its source in a Tamlinux checkout for fast
iteration and `dev off` restores the installed package; `diff` and `verify`
compare the installed plugin with its source; `restore` recovers from a
stuck override. `new` creates a bar-widget plugin in the checkout (manifest,
`BarWidget.qml`, README, changelog), validates it, and places it in the
default bar layout; `desktop/widget-proof <id>` then renders it offscreen.
The catalog is read from the plugin manifests, so a new plugin needs no
entry here. `tam-plugin help` lists every command.

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
| `TAMLINUX_PLUGIN_CATALOG` | unset; the package sets it to its plugin output |

## Status

Moved here from a private workstation configuration on 2026-10-09. Version
3.0.0 reads plugin sources from this repository and leaves Test and Run to
`tam-deploy`. The Omarchy-era 1.x tool stays in the frozen
`plugin-fred-tamlinux` repository.

Since 3.1.0 (Tamlinux 0.4.4) the catalog is every manifest naming the
Tamlinux repository, read from the packaged plugin root
(`TAMLINUX_PLUGIN_CATALOG`, set by the package), the installed plugin links,
and a checkout; catalog links point to `tamlinux/desktop/plugins/`. `list`, `info` and
`search` perform no marketplace requests, read no old registry cache and fetch
no repository. `list --refresh` remains accepted; catalog updates arrive with
the package. Local source inspection remains available with a Tamlinux checkout.
`upstream-diff` now reports its retirement and points to `verify <id>`; it no
longer requires an inherited distribution installation. Historical ancestry
stays in each plugin's source records.

The product also owns its reload dependencies: `tam-qmlcache-purge` removes
only compiled QML/JS cache entries corresponding to the selected plugin tree,
and `tam-restart-shell` uses the managed user service's `try-restart` operation.
It leaves an inactive service inactive. Nix delivery supplies their required
standard tools and resolves both commands from the same product command output.
