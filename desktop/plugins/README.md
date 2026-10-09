# Tamlinux plugins

The `fred.*` plugin suite lives here, one directory per plugin, beside the
shell that hosts it. Tamlinux owns its desktop and its plugins together:
`desktop/shell/` owns the shell, the plugin host, and the shared API, and
`desktop/plugins/fred.<name>/` owns each plugin and its specific helpers.
Shared desktop helpers live alongside the shell rather than inside a plugin.
Utilities useful beyond the desktop live in `tamlinux-tools`.

Shell and plugin changes land together in one repository, reviewed in one
integration, with one recorded source revision. Individual plugin versions
stay in the manifests and namespaced tags for diagnostics; independent
release schedules are no longer necessary.

## Layout

```text
desktop/
  shell/                 # the shell, plugin host, and shared API (registry,
                         # settings, popouts, IPC, compositor facade)
  plugins/
    fred.clock/          # one directory per plugin: manifest, QML, helpers,
    fred.workspaces/     # tests, docs, and provenance records
    fred.agents/
    fred.keyboard/
    fred.monitor/
    fred.sysinfo/
    fred.tides/
    fred.weather/
```

Each plugin keeps its own `manifest.json`, entry points, settings, tests,
and optional activation. Runtime IDs stay `fred.<name>`, so existing
settings and shell references keep working.

## Frozen Omarchy-era repositories

The eight plugins were previously published as independent public
repositories (`greenermoose/*-fred-tamlinux`). On 2026-10-09 their current
work (the 2.0.0 rewrites on the Tamlinux shell API) was moved here with
their full history. In `git`:

- branch `fred.<name>/main`          — the plugin's `main` history
- branch `fred.<name>/develop/2.0.0` — its development line
- tags `fred.<name>/<tag>`           — its releases, namespaced to avoid
  collisions between plugins (for example `fred.clock/v1.3.3`)

The old repositories are frozen and then archived: their released 1.x
versions target Omarchy, and their history, tags, releases, and branches
remain there as the historical Omarchy suite. They are read-only reference,
not active source.