# Plugin set derived from the plugin directories

- **CLI Tool**: Claude Code (`claude`) `2.1.301`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Is there anything we can do to speed up how quickly agents can build and deploy plugins for Tamlinux? Take a look at what codex did to create fred.tamversion and how long it took. Was there any wasted effort or are there any deterministic scripts or tools or skills or guides or runbooks or memories we can make that will speed things up?

  > Please go ahead and build 1, 2, and 6. Then let's touch base again.

  Item 2 of the agent's proposal: derive every plugin list from
  `desktop/plugins/fred.*/manifest.json` so adding a plugin touches only its
  own directory and the default layout.

## Implementation

Adding `fred.tamversion` had required editing seven hand-kept copies of the
plugin set, and one historical-fixture test broke on the new default widget.
Each copy now derives the set:

- `tam-plugin` builds its catalog from manifests whose `repository` is the
  Tamlinux repository, read from the installed plugin package (resolved
  through the live links) and from a source checkout. Repository URLs follow
  from the ID; descriptions come from each manifest. Discovery stays offline.
- `check-live` expects the plugins the active deployment records in
  `deployment-selection.json`, falling back to the installed links, so a
  checkout ahead of the installed version no longer reports a false failure.
- `launch-clock-proof` loads every bundled plugin except the clock.
- Desktop tests compare the default layout with the plugin directories and
  compare the historical Omarchy import with the default restricted to the
  widgets the fixture names, plus an entry-count check against the fixture.
- `desktop/plugins/README.md` describes the directory as the plugin list.

## Verification

- `tam-plugin`: lifecycle seams pass; 6 unit tests pass, including new checks
  that every packaged plugin is searchable with its manifest description and
  that a plugin naming another repository is not catalogued. Its `list --all`
  output is identical to the installed `tam-plugin`'s on the workstation.
- `test_host.py` (31, one skipped) and `test_omarchy_shell_import.py` pass.
- Full desktop suite: 592 tests pass, one skipped. Another session's
  uncommitted login files were present in the checkout during that run.
- `check-live --stages passive` on the running 0.4.4-b desktop reports
  "all bundled plugins loaded"; its one failure is an unrelated core dump from
  the previous day.
