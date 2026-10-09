# Menu ownership and reload behavior

Step 0.4.2 owns the menu without changing its retained applications, routes,
navigation or power policy. This candidate is developed and tested in isolation;
workstation acceptance remains a separate transition.

**Package transition, 2026-10-09:** the menu implementation is retained on
`develop` after the packaged 0.4.1 release was merged back. The product version
is `0.4.2-a`. Delivery selects an exact source revision in a committed
`tamlinux-packages` assembly; the consumer restores the owned menu extension
with that assembly. Test and Run use the same package outputs and installed
paths. The earlier independent shell/plugin snapshots are historical evidence,
not the deployment mechanism for this candidate.

The source candidate passed nine parser/reader/headless-service checks and
18 existing service regressions after the merge. Consumer comparison confirms
all 196 effective menu rows are unchanged. Before activation, verify the
built package paths, version, plugin payloads, menu files, service environment,
protocol-shadow identity and rollback artifact. Promotion to `test` and
physical workstation checks require the user's Test instruction.

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
