# tam-deploy and tam-plugin 3.0.0: deploy packaged assemblies

- **CLI Tool**: Claude Code (`claude`) `2.1.295`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Authorship**: Claude rewrote the deploy command, reworked `tam-plugin`,
  wrote their tests and this record. Fred approved the deployment contract
  and chose the command behaviour below.
- **Prompts**:
  > I have approved it and yes, start 2b

  Fred then chose, among proposed options: name the deploy command
  `tam-deploy`; record a Test by pinning and committing the assembly revision
  in the consumer lock; make Run a promotion to `main` without reinstalling;
  remove the snapshot `test` and `run` commands from `tam-plugin`.

## Change and decisions

Test and Run now install the same package through the same Home Manager
endpoint. A deployment is a `tamlinux-packages` revision whose lock pins every
component.

- **`tam-deploy` replaces `tam-shell-deploy`.** `test [revision]` requires the
  assembly and each pinned component to be on `test`, pins the revision
  (default: the head of `test`) in the configuration lock, switches Home
  Manager, restarts the shell, verifies that the shell, plugins and commands
  resolve into the assembly's packages and commits the pin. A failure restores
  the lock and the previous generation.
- **Run promotes without rebuilding.** Test already installed the exact bytes,
  so `run` re-verifies the installation and fast-forwards `main` of each
  component, then of `tamlinux-packages`. Components go first so the
  assembly's `main` never pins a component revision missing from that
  component's `main`. Pushes are fast-forward only.
- **`back`** activates the previous generation and restores its pin.
- **`tam-plugin` 3.0.0** reads plugin sources from `desktop/plugins/` in a
  Tamlinux checkout; `diff` and `verify` compare the installed plugin with
  that source. The snapshot `test` and `run` commands are removed and point to
  `tam-deploy`. `dev off` restores the installed package link without a Home
  Manager switch. Legacy snapshot state still blocks `dev` until `restore`.

## Verification

- `tam-deploy`: 20 tests, using real repositories with bare origins for the
  branch checks and fast-forward pushes, plus failure recovery, verification
  of installed paths, and pin handling.
- `tam-plugin`: the rewritten lifecycle suite (dev, restore, legacy state,
  verify, moved commands) uses the product's own registry and a temporary
  home and fails if Home Manager would run.
- Both suites, and `tam-work`'s 38 tests, pass inside the `tamlinux-packages`
  build of this branch, which runs every command's `make check` in the Nix
  sandbox. On the author's workstation `tam-plugin verify fred.clock` reports
  the installed digest recorded at the 0.4.1 acceptance.

## Addendum: run modes

- **Prompts**:
  > Add the argument to tam-deploy run. But I want to be able to run any commit I see in the git graph for tamlinux-packages. Maybe you could warn if I'm attempting to run a commit that hasn't been tested yet. [...] the default tam-reploy run should be to run whatever test I'm currently on. I shouldn't have to remember or look up a commit hash. If I'm already running a main branch commit, then tam-deploy run could return a message to that effect.

  > Require --untested, then implement it

`run` takes an optional revision. Without one it promotes the installed Test or
reports an installed `main` commit. With one it installs the revision if
needed and fast-forwards `main`; a revision already on `main`, including an
older one, moves no branch. A revision, or a component it pins, found only on
`develop` or another branch is untested: `run` refuses it unless
`--untested` is given, and then also moves `test` so `main` stays within
`test`. A revision `main` cannot fast-forward to is refused. Test and Run share
one install step. 25 tests cover each mode with real repositories.
