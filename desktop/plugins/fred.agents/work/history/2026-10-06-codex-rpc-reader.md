# Codex usage reader and last-known limits (2.0.1)

- **Date**: 2026-10-06, finished 2026-10-07
- **CLI Tools**: Codex CLI (`codex`) `0.160.1`, then Claude Code (`claude`) `2.1.292`, both read from the local session metadata and `claude --version`.
- **Models**: GPT-6.1 Sol (`gpt-6.1-sol`), then Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: Fred reported that Codex usage was often unavailable and asked for a fix and a 2.0.1 bump. Codex diagnosed the cause and wrote the fix and tests. The Codex session ended uncommitted when the machine hibernated, and Fred asked Claude to finish it. Claude fixed one test, checked live reads, and committed it.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Why is the account/read error happening? Sometimes I can tell how much codex usage I have left, but often I cannot. Why not?

> Make it so

> Make sure to bump the version of fred.agents to 2.0.1 after you fix the bug.

> that codex session is gone. Release those claims and finish up that work for codex

## Cause

`rpc_request` mixed buffered `readline` on a text pipe with `select` on
the same pipe. When Codex sent several replies together, Python had
already buffered the `account/read` reply, `select` saw an empty pipe,
and the reader waited four seconds before raising a false timeout. The
collector then skipped `account/rateLimits/read` and replaced the shown
limits with an empty record.

## Work and decisions

- `RpcReader` owns a byte buffer read with `os.read`, consumes complete
  lines before polling, keeps partial lines across requests, and reports
  connection closure, RPC errors and malformed results explicitly. Replies
  are capped at 1 MiB.
- A failed refresh keeps the last successful limits from
  `codex.json`, marked `limitsStale` with their original
  `limitsUpdatedAt`. Windows whose reset time has passed drop out. A
  different `CODEX_HOME` or account, or a non-ChatGPT sign-in, clears the
  fallback. Transient failures set `retryAdvised`.
- The panel and bar hover label retained limits "last known" with the
  reading time.
- Claude's change: the hover test extracts QML functions into Node, where
  `bindingWindow`'s unqualified call to `limitWindows` did not resolve.
  The test now exposes the extracted functions globally, as QML scope
  does. No plugin code changed.

## Verification

- `python3 -m unittest discover -s tests`: 19 tests OK.
- Three consecutive live runs of `bin/tam-agent-usage-codex` returned two
  limit windows each, with no status error.
