# tam-fleet

Register and reconcile a small fleet using explicit host profiles and Git.
Requires Python 3.11+, Git, and (for capture) Arch's pacman. No service runs
in the background. Private values stay in the consumer's private checkouts.

Set `TAMLINUX_CONFIG_REPO` to the Home Manager checkout and
`TAMLINUX_FLEET_REGISTRY` to its companion `systems` directory, or pass
`--config PATH --registry PATH` before the subcommand.

```sh
tam-fleet register laptop --username user --role laptop \
  --hardware-profile hardware/laptop.md --capability desktop-common
tam-fleet status
tam-fleet index
tam-fleet check
tam-fleet root-files laptop
tam-fleet capture laptop
tam-fleet reconcile laptop
tam-fleet reconcile laptop --commit
```

Registration creates a planned dossier, `hosts/<hostname>/host.json`, an empty
host module and an empty root manifest. It never copies another machine's
files. The hardware page and selected capability modules must already exist.
The consumer flake exposes only explicit `user@hostname` outputs. Its activation
must check the hostname before writes; this tool never activates Home Manager.

`check` validates identity, capabilities, hardware/local links, root sources and
index freshness. `check --live HOST` additionally checks the running hostname,
account, installed host metadata, root-file contents/modes and `tam-deploy status`.
Source validation alone says nothing about boot, login or physical hardware.

`root-files` previews the union of shared and local manifests, including selected
`hosts/<host>/system/capabilities/<capability>/MANIFEST` fragments. It refuses
duplicate targets and escaping sources. It never installs files as root.

Capture writes only `hosts/<local-hostname>/state/`: package lists, BOM,
local recipe hashes and root-file hashes. It does not heal symlinks, execute
package recipes, copy root contents, or write to a public registry. A different
hostname or dirty destination stops it before writes. Writers share one lock;
symlinked destination paths are refused. Checkouts are trusted local inputs.

Reconciliation runs all checks before and after capture. Only success updates
`last_reconciled`, creates a success receipt and refreshes the index. The
default leaves a diff to review. `--commit` makes one exact-path commit in
each owning repository; Git cannot commit two repositories atomically, so a
failure in the second is reported and leaves the first commit visible. A
staged change or merge conflict stops it. It never pushes or resolves conflicts.

Review and commit observations before another reconciliation. Each machine has
its own GitHub SSH key; never put keys, tokens, serials, IP or MAC addresses in
the registry. Reconcile before retiring a machine and revoke its key separately.
