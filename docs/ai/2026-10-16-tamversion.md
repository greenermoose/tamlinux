# Tamlinux version in the bar

- **CLI Tool**: Codex CLI (`codex`) `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > We are working on Tamlinux 0.4.4a. I just ran tam-restart-shell and all seems well. To help me know which version of Tamlinux we're running, please add Tamlinux x.y.z to the center of the top bar just to the left of fred.clock. This can be a plugin called fred.tamversion. Or propose another way to do that if you think a plugin is not the best. The stay awake stuff that appears when mouse is in top bar should be to the left of tamversion. Ask if you have questions about this. After doing tamversion, then continue on with the rest of the 0.4.4 development work.

  > In which repo will you file the code for fred.tamversion?

  > Do you understand why I want fred.tamversion showing as soon as possible?

  > Make 0.4.4b just a+tamversion, bump VERSION in both repos, and hand it to me for Test before any login work.

## Implementation

Original GPL-3.0-or-later plugin in `desktop/plugins/fred.tamversion`.
The resolved shell launcher reads its own packaged `version` file and passes
`TAMLINUX_VERSION` to QML, replacing an inherited stale value. A source launch
uses the checkout's VERSION; absent metadata is explicitly unknown. The label
formats SemVer letter `0.4.4-a` as `0.4.4a`. Package plugin discovery is automatic;
the CLI catalog, proof launcher, live checker and default layout include the
new plugin. The clock remains the center anchor, with indicators to the left
of the version label.

The next proposed candidate is 0.4.4-b, limited to this feature. Existing
0.4.4-a is unchanged. Candidate preparation grants no Test or Run promotion.
Existing custom layouts require inserting the plugin before the clock when
that candidate is installed.

## Verification

- Host/registry/default-layout tests: 31 pass, one historical adapter check skipped.
- Offscreen execution using the installed paired Quickshell provider renders
  `Tamlinux 0.4.4a` at positive width and height (125.3125 by 26).
- Full desktop suite: 590 tests pass, one historical adapter check skipped.
- Offscreen development, release and missing-version labels all render successfully.
- Package build results are recorded by the delivery candidate.
