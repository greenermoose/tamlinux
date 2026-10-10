# Menu ownership and reload behavior

Step 0.4.2 owns the menu without changing its retained applications, routes,
navigation or power policy. This candidate is developed and tested in isolation;
workstation acceptance remains a separate transition.

**Candidate status, 2026-10-09:** 0.4.2-b was packaged and installed in
Test. The repaired 0.4.2-c source restores accepted plugin storage contracts
and updates the delivery selection to tam 0.9.1. Menu defaults, parsing and
all 196 effective workstation rows remain unchanged from b. Delivery selects
an exact source commit in a committed `tamlinux-packages` assembly; physical
acceptance applies to that assembly and generation. No Run or Release
acceptance is claimed by source or package checks.

The candidate uses product-owned menu defaults and the optional consumer
extension through the same Nix/Home Manager endpoints for Test and Run.
The earlier independent shell/plugin snapshots are historical evidence,
not the deployment mechanism. Before activation, verify built package paths,
versions, plugin payloads, menu files, service environment, protocol-shadow
identity and the rollback artifact. After activation, verify installed
endpoints and menu readiness, then exercise focused-output routing, navigation,
application launch, refresh/restart and the next natural login.

The product supplies `desktop/menu/default.jsonc`, its upstream MIT notice and
the `tam-menu` entry point. Delivery modules install defaults at
`$XDG_CONFIG_HOME/tamlinux/menu/default.jsonc` and an optional personal extension
at `tamlinux/menu/extension.jsonc`. `TAMLINUX_MENU_DEFAULT` and
`TAMLINUX_MENU_EXTENSION` select the files. Personal application choices belong
in user configuration. The default tree retains named theme/font/branding and
boot dependencies for their later ownership stages.

The menu accepts JSON objects keyed by row ID, optionally wrapped in `items`.
Dotted IDs imply parents. Line/block comments and trailing commas are supported
outside quoted strings; action text is preserved verbatim. Rows use string
fields (`parent`, `icon`, `iconFont`, `label`, `title`, `target`, `description`,
`action`, `provider`, `when`, `checked`) and string or string-array `aliases`.
Invalid types, ambiguous actions, unsafe IDs, missing parents/targets and route
cycles reject the candidate model. Extension rows currently replace normalized
fields, so overrides should supply the full row including retained aliases.

| Limit | Bound |
| --- | --- |
| File read | 256 KiB of strict UTF-8 from a regular file, including normal config/store symlinks |
| Parser input | 262,144 UTF-16 code units; the file reader imposes the byte bound first |
| Rows | 2,048 per source and merged static model, including the synthetic root |
| JSON nesting / route depth | 32 |
| Row ID / alias | 256 code units |
| Aliases per row | 32 |
| String field | 16,384 code units; NUL rejected |
| Reader deadline | 2 seconds |

`MenuSource.qml` coalesces changes for 75 ms and runs one bounded reader per
source. Its FileView is used only to watch: `preload: false` prevents the
[default eager read](https://quickshell.org/docs/v0.2.1/types/Quickshell.Io/FileView/).
The helper validates file type and size before reading, uses a bounded read and
strict UTF-8, and rejects FIFOs without waiting for a writer. Parsing finishes
before source replacement; merge validation finishes before visible model
replacement. Failed reads/parses retain the last valid source. Failed merges
retain the last valid visible model. No invalid candidate runs guards or actions.
An initially absent optional extension means an empty extension; removing a
previously loaded file retains it. Use `{}` to deliberately clear its rows.

`tam-menu refresh` schedules rereading. `tam-menu status` reports readiness,
static row count, configured source paths and the latest reload error. Actions
continue in detached systemd scopes through the existing executor. Power argv
can be verified by recording dispatch in a fixture without performing the action.

Verification: `python3 -B -m unittest discover -s desktop/tests -p test_menu_jsonc.py`.
The full service fixture uses a private headless compositor, temporary HOME and
runtime directory, and recorded actions. Run it where local Unix sockets are
permitted; the test detects sandbox restrictions before launching wlroots.
Physical focused-output routing, keyboard navigation, application launching,
restart/login and recovery still require the exact daily Test candidate.
