# Plugin scaffold and offscreen widget check

- **CLI Tool**: Claude Code (`claude`) `2.1.301`
- **Model**: `claude-opus-5-5`
- **Commit**: `24bcba1`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Yes, please start on those. Are you able to claim all the paths you need? Can you coordinate with codex and agy?

  > Tamlinux 0.4.4c's source is settled. Codex has released all claims. I'm finishing up work before proceeding with testing automatic login. Please finish up everything you've been working on. And let me know what product-source is. Do we need to keep that?

  "Those" are the agent's proposals to add a plugin scaffold and a committed
  offscreen widget check, after reviewing how `fred.tamversion` was built.

## Implementation

- `tam-plugin new fred.<id> --description TEXT` writes `manifest.json`,
  `BarWidget.qml` (a `displayText` label whose `pluginVersion` matches the
  manifest), `README.md` and `CHANGELOG.md`, validates the directory with the
  registry, and inserts one entry into `default-layout.json` (end of the right
  section, or `--section`/`--before`/`--after`; `--no-layout` skips it). The
  layout keeps its one-entry-per-line form, so the diff is one line. Refusals
  (existing or invalid ID, missing description, unknown anchor) create nothing.
  `tam-plugin` is 3.1.0.
- `desktop/widget-proof <id|dir>` loads one bar widget in a disposable
  Quickshell config with the offscreen platform, a private runtime directory
  and no display, session bus or desktop Qt/GTK settings, so it needs no
  session access. It prints the widget's text property and implicit size as
  JSON and fails on no load, no size, or a text other than `--expect`.
  Widgets that create a `PanelWindow` while loading cannot load offscreen and
  are reported as such.
- Committed on a feature branch while 0.4.4-c's source selection was open,
  then fast-forwarded onto `develop` after it settled.

## Verification

- `tam-plugin`: 12 unit tests and the lifecycle seams pass, including a
  rendered check of a freshly generated plugin.
- `widget-proof`: 7 tests pass. `fred.tamversion` renders `Tamlinux 0.4.4b`
  (125.3 by 26) in about 0.13 s; `fred.clock`, `fred.weather` and `fred.tides`
  render; `fred.keyboard` and `fred.monitor` report the `PanelWindow` limit.
  It also passes inside a workspace-write agent sandbox.
- Live render tests skip when no Quickshell is available, so package check
  phases are unaffected.
