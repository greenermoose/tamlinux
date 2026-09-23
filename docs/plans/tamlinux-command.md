# The `tamlinux` command and offline guide

**Status:** First command slice approved by Fred on 2026-09-23;
implementation has not started. Later slices remain proposals.

## Purpose

Give Tamlinux one discoverable command for installation, orientation, and
local help. It should be useful in a terminal before the desktop is running,
and it should answer basic questions without a network connection. The first
slice is deliberately small so the installation framework has a stable entry
point and the guide can grow from actual user questions.

## First command slice

| Command | First behavior |
| :-- | :-- |
| `tamlinux --help` | Show available commands and where to start. |
| `tamlinux --version` | Read the product version from installed metadata; label command version separately if it differs. |
| `tamlinux install ...` | Delegate to the installation contract in [the installation plan](installation-framework.md). |
| `tamlinux` | Show welcome on the first interactive use, then open the local guide on later uses; print a short text index when output is piped. |
| `tamlinux welcome` | Open orientation explicitly at any time; never require it before `--help` or installation. |
| `tamlinux explain <topic>` | Initially match curated local topics and give a clear miss message. |

The first interactive bare invocation shows welcome automatically. Record that
welcome was shown in `$XDG_STATE_HOME/tamlinux/welcome_seen` (falling back to
`~/.local/state/tamlinux/welcome_seen`) after it is displayed successfully,
whether through Lynx or the text fallback. Explicit `tamlinux welcome` also
records it. `--help`, `--version`, installation commands, and the bare command
when piped leave first-use state unchanged. The command must distinguish
terminal output from piped output and never emit browser control text into a
pipeline. It must check
whether Lynx is available and, if absent, show readable text and instructions
for installing Lynx so that HTML can be rendered.

## Knowledge format

Ship a small, semantic HTML corpus with relative links and a plain-text
fallback. Lynx is the optional terminal browser because it is already used on
the current workstation and works offline. If Lynx is unavailable, show the
text guide and instructions for installing it on the detected base; do not
start an installation automatically. `tamlinux` locates the installed
corpus through package data, not a fixed `/usr/share` path, so NixOS, native
Arch packages, and user installations can share the same content.

The first pages are welcome, a command index, installation overview, and a
short guide to shell pipelines and man pages. Pages about plugins and AI tools
come from verified component behavior and versions, rather than copying a
workstation snapshot into general guidance. External links are labeled as
external; opening the local guide must not fetch network content.

## Later slices

- Expand `explain` from curated terms to safe parsing of command lines,
  options, pipes, and redirection. The parser must only describe input; it
  must never execute it. Man-page integration can follow once formatting and
  links are reliable.
- Add `tamlinux ai` after hardware estimates can report their assumptions and
  uncertainty. A calculated speed is an estimate, not a measured benchmark.
- Add `tamlinux config` once each setting has a clear owner and reversible
  operation. Read-only inspection should come first.

These are development directions, not features in the first release. The
first implementation should use the Python standard library. Lynx enables
interactive browsing when installed; plain-text help must work without it.

## Implementation order and review points

1. Set the command layout and version source; make `--help`, `--version`, and
   `install inspect` work before any state-changing installer step.
2. Package the minimal guide; check for Lynx before interactive browsing and
   provide the text guide plus installation instructions when it is missing.
   Keep piped output predictable in both cases.
3. Add `welcome`, first-use state for the interactive bare command, and the
   first curated `explain` topics.
4. Extend installation, explanation, AI, and configuration in that order,
   recording what each addition actually does in this plan.

## Review record

- **2026-09-23:** Fred confirmed the first command slice above, including the
  runtime Lynx check and readable text with installation instructions when
  Lynx is unavailable.
- **2026-09-23:** Fred confirmed automatic welcome on the first use of the bare
  command.
- **Still open:** The later compound-command `explain`, `ai`, and `config`
  expansions need their own review before implementation.
