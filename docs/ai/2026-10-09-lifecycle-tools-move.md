# Lifecycle tools move into Tamlinux

- **CLI Tool**: Claude Code (`claude`) `2.1.295`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Authorship**: Claude moved the two commands, made two private defaults
  configurable, added four tests and wrote this record. Fred set the rule and
  the order.
- **Prompts**:
  > We want all scripts and commands that start with tam-\*, including tam-shell-deploy and tam-plugin, to be developed under the public tamlinux repo, not under a private repo.

  > 1 sure, fred-\* for personal commands that only apply to me; tam-\* for public tam commands that should work on any tamlinux system.
  > 2 The rule should be "developed in a public Tamlinux repo: tamlinux by default, tamlinux-tools for standalone utilities"
  > 3 the order should be: lifecycle tools first, then the 0.4.1 package.

  > yes, start the move

## Change and decisions

`tam-*` commands are public Tamlinux commands that should work on any
Tamlinux system, developed in this repository or, for standalone utilities,
in `tamlinux-tools`. The two lifecycle tools move first, because the next
step reworks them to deploy packages and that work belongs here.

- **`commands/tam-shell-deploy/`** and **`commands/tam-plugin/`** are
  self-contained components like `commands/tam-work/`, each with `make check`
  and `make install` (`PREFIX`, `DESTDIR`) and its existing tests.
- **The source is the copy that runs.** `tam-plugin` is the Tamlinux 2.0.0
  tool from the workstation configuration, not the Omarchy-era 1.2.0 left in
  the frozen `plugin-fred-tamlinux` repository.
- **Behaviour is unchanged on the author's workstation.** Two private
  defaults became configurable: the Home Manager configuration name, now
  `TAMLINUX_HOME_CONFIGURATION` or the current user name, and
  `tam-shell-deploy`'s configuration checkout, now `TAMLINUX_CONFIG_REPO` or
  the single checkout under `~/Code/tamlinux/` holding
  `config/tamlinux/plugins`, the rule `tam-plugin` already used.
- **Not yet deployed from here.** The workstation keeps running its existing
  copies until the reworked tools are packaged, tested and run.

## Verification

- `tam-shell-deploy`: 14 tests passed, including four new ones for
  configuration discovery and the Home Manager configuration name.
- `tam-plugin`: the lifecycle-seams suite passed (dev safety, restore, Home
  Manager preflight, exact snapshots, payload digests, verify and run).
