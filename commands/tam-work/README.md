# tam-work

## What it does

`tam-work` provides advisory, path-scoped claims so several sessions (people or AI agents) can work in the same Git checkouts. Overlapping paths are refused. It never switches branches, stashes or resets files.

## Install

Run `make install` (honours `PREFIX`, `DESTDIR`) and `make check`:

```bash
make check
make install
```

## Usage

Claim specific repository-relative paths:

```bash
tam-work begin --scope desktop/shell --note "refactor status bar"
```

Claim exclusive access to the whole checkout:

```bash
tam-work begin --exclusive --note "branch switch and rebase"
```

Release a claim:

```bash
tam-work finish --note "finished status bar work"
```

Check claim status, include history, output JSON, or filter by repository:

```bash
tam-work status
tam-work status --all
tam-work status --json
tam-work status --repo tamlinux
```

List coordination messages in the inbox:

```bash
tam-work inbox
tam-work inbox --all
```

The older `claim` and `release` pair:

```bash
tam-work claim task-12 --owner dev --scope desktop/shell --worktree /tmp/worktrees/dev --note "investigate layout"
tam-work release task-12 --owner dev --note "finished investigation"
```

## Identity

Session ownership uses `TAM_WORK_OWNER` and `TAM_WORK_SESSION`, or flags `--owner` and `--session`. If `TAM_WORK_SESSION` is not set, `identity()` reads session variables in the following order:

1. `CODEX_THREAD_ID` (infers owner `codex`)
2. `CODEX_SESSION_ID` (infers owner `codex`)
3. `CLAUDE_SESSION_ID` (infers owner `claude`)

## Locations

- **Workspace**: Root holding canonical checkouts. Defaults to `~/Code/tamlinux`. Overridden by the `TAM_WORK_WORKSPACE` environment variable or `--workspace` flag.
- **Registry**: Claim storage (one JSON file per claim plus `.lock`). Defaults to `<workspace>/worktrees/coordination`. Overridden by the `TAM_WORK_REGISTRY` environment variable or `--registry` flag.
- **Inbox**: Incoming coordination briefs located at `<workspace>/worktrees/<owner>/inbox/*.md`.

Flags win, then environment variables, then defaults under home, as `resolve_paths` resolves them.

## Sharing a checkout

When multiple sessions share a checkout:

- Commit only your own paths: `git commit -m ... -- <paths>`.
- Never `git add -A` or `git commit -a`.
- Use `--exclusive` for branch switches, rebase/reset/stash/pull/amend and whole-tree builds or deploys.

## License

GPL-3.0-or-later
