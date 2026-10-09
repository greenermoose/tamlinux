# Plugin suite consolidation into Tamlinux

- **CLI Tool**: OpenCode `1.18.35` / Antigravity CLI (`agy`) `1.2.16`
- **Model**: `big-pickle` / `gemini-3.8-flash-high`
- **Transcript**: Retained privately by the author.
- **Authorship**: Started by OpenCode from Fred's brief; completed, debugged, and verified by Antigravity.
- **Prompts**:
  > Freeze the eight plugin repos (clock-fred-tamlinux, keyboard-fred-tamlinux, etc.) and move them to the tamlinux repo, specifically tamlinux/desktop/plugins. Each should have the name desktop/plugins/fred.<name>/. Here is more background on this task:
  > The eight plugins belong in tamlinux/desktop/plugins/. Your clarification removes the main reason to maintain independent repos: they serve one desktop, share its API, and evolve with it.
  > ...

## Change and decisions

The eight `fred.*` desktop plugins (`fred.agents`, `fred.clock`, `fred.keyboard`,
`fred.monitor`, `fred.sysinfo`, `fred.tides`, `fred.weather`, `fred.workspaces`)
have been imported with full git history into `desktop/plugins/fred.<name>/` in the
unified Tamlinux repository.

1. **Git history & tags**:
   Each plugin's development history was rewritten into `desktop/plugins/fred.<name>`
   and fetched into namespaced branches (`fred.<name>/main`, `fred.<name>/develop/2.0.0`)
   and namespaced tags (`fred.<name>/<tag>`). The eight `develop/2.0.0` branches were
   merged into `main`.
2. **Manifests**:
   Updated all 8 `manifest.json` files to reference repository
   `https://github.com/greenermoose/tamlinux.git` and homepage
   `https://github.com/greenermoose/tamlinux`.
3. **Shell and Proof Integration**:
   `desktop/launch-clock-proof` and `desktop/adapters/build_patch.py` were updated
   to read the plugins directly from `desktop/plugins/`.
4. **Tooling & Test Boundaries**:
   `test_layout.py` in `fred.monitor` was made robust to its in-repo location.
   `desktop/tests/test_compositor.py` boundaries were updated to isolate shell
   facade checks from in-repo plugin UI strings.
5. **Freeze Status**:
   The eight independent `*-fred-tamlinux` repositories are marked frozen as
   retained historical Omarchy 1.x archives.

## Verification

- `python3 -m unittest discover desktop/tests`: all 409 tests passed (1 skipped).
- `python3 desktop/launch-clock-proof --selftest`: passed cleanly, registering all 8 plugins.
- `tam-plugin list` and `tam-plugin diff fred.clock`: verified with in-repo paths.
