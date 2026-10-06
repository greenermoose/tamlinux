# 2026-10-06 — The proof launcher addresses its own instance

- **CLI Tool**: Claude Code `2.1.291`.
- **Model**: `claude-opus-5-5`.
- **Role**: implementation, while checking the 2.0.0 plugins for Tamlinux 0.3.0.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > I had to recover from a KIQ error. That interrupted opencode as it was working on T15. I believe you're done with 0.2.6 of the tamlinux project. What's next for you? Anything for agy to work on? opencode is very slow this morning, but I've prompted it to "Read AGENTS.md and your inbox. Check to see how far you got. Continue from where you left off." We'll see what it does. So far it has only read AGENTS.md after several minutes.

  > Go ahead

## Work and decisions

`desktop/launch-clock-proof --selftest` failed with "calendar did not open"
before any plugin change. Since stage 0.1 the session runs its own Tamlinux
shell from the same `desktop/shell` directory, and `quickshell ipc -p
desktop/shell` reached that instance, not the isolated proof. The launcher
now records the PID of the instance it spawned and calls `quickshell ipc
--pid`. It refuses to send IPC when it has not spawned one.

This was also a safety gap. Later selftest calls (DPMS off, dropping hosts,
writing fixtures) would have gone to the session shell. Each failing run
stopped at its first check, after one `tamlinux.clock open` call.

## Verification

- `--selftest --scale 1` and `--scale 1.25` print `selftest ok`, with all
  eight `fred.*` 2.0.0 plugins registered from their `develop/2.0.0`
  working trees.
