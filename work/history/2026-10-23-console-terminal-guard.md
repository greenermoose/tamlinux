# Hold the text shell during explicit desktop use

- **CLI Tool**: Codex CLI `0.164.0`.
- **Model**: `gpt-6.1-sol`.
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation, directed by Fred.

## Guiding prompt

> Keep working on Tamlinux 0.5. I'm hoping to be able to try a boot-to-text-terminal soon. Currently when I boot I get dumped directly into a graphical shell. I want to boot to a text shell and then be able to start a graphical shell if I want, or just start using my computer if I don't need a graphical shell.

## Changes and verification

Keep the text login shell while the explicit desktop command runs, but hold
its foreground terminal until the graphical session and compositor stop.
Disable terminal signal keys and echo, ignore job-control suspension, and
discard queued input before restoring terminal settings. Disconnect the
session starter's standard input from the console. External termination
requests UWSM shutdown; unknown cleanup keeps the console held and points to
another text console for recovery. Ordinary desktop use blocks on the child
without polling. This addresses keyboard escape to the underlying shell;
deliberate process termination by an authenticated process is outside it.

Eleven console-launcher tests pass, including a real pseudo-terminal trial
of Ctrl-Z/Ctrl-C, direct suspension, queued complete/incomplete text, failed
cleanup, terminal restoration and failed execution. An additional ten session
defaults/launcher tests pass. The external-termination test checks shutdown
before releasing the console. Physical text boot, VT switching, locking,
desktop lifecycle and credential-service acceptance remain pending. No stage
promotion or boot/login/package activation was performed.
