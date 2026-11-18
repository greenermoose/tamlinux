# Independent keyboard development application

- **Date**: 2026-11-01
- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.

## Prompts

> The last session was working on an update to fred.keyboard but could not install it. Can you?

> I do not want a packaged Tamlinux candidate. Why is this necessary? Override the policy and just install a new keyboard app so I can test it without going through a big rigamarole for the rest of the system.

## Changes

Codex implemented an independent development launcher and a small QML host
for the existing keyboard widget. The host supplies its own read-only
keyboard/keymap and shortcut state, reuses the complete widget UI, and exits
when the panel closes. The installed shell is not contacted or replaced.
The keyboard rendering fix remains the existing development implementation.

The installer archives an exact commit, verifies it, and installs under the
user's development prefix with a desktop entry named Keyboard (Development).
It records the revision, launcher, runtime and build directory, preserving
earlier launchers for restoration. Uninstall removes the trial and restores
those files. This is an explicitly requested independent development trial;
no Tamlinux candidate or stage transition is involved.

## Verification

- The existing real-QML rendering regression passes for the bundled boards,
  including keycap spacing and press/release highlighting.
- The invisible standalone load check detects the physical keyboard, loads
  the six-row fallback board and reads 226 compositor shortcuts, without
  opening a panel or taking keyboard focus.
- Installation repeats both checks against the archived source before
  writing the launcher. Physical typing acceptance belongs to the user.
