# The `tam` command and offline guide

**Project scope (2026-10-06):** Tamlinux is an independent, continuing Linux
workstation environment aimed at the best possible user experience on any
hardware. The workstation package remains `tamlinux`; the terminal command is `tam`
(named 2026-10-07). Existing-distribution
Nix delivery and native Void packaging are Tamlinux engineering work. Hardware
profiles are capability-based; circa-2006 machines are validation examples,
not a universal age cutoff.

**Status:** First command slice approved by Fred on 2026-09-23;
local component repository scaffold prepared on 2026-10-08; command
implementation has not started. The command was named `tam` on 2026-10-07;
the package/data namespace remains `tamlinux`. Later slices remain proposals.
The approved first slice can develop independently and feeds 0.7 packaging;
it does not block settings/menu/theme ownership or Omarchy removal.

## Purpose

Give Tamlinux one discoverable command for installation, orientation, and
local help. It should be useful in a terminal before the desktop is running,
and it should answer basic questions without a network connection. The first
slice is deliberately small so the installation framework has a stable entry
point and the guide can grow from actual user questions. Command source,
bundled knowledge, tests and component planning belong in the separate `tam`
repository. This repository retains workstation assembly and the installation
framework; `libtam` remains a separate dependency.

## First command slice

| Command | First behavior |
| :-- | :-- |
| `tam --help` | Show available commands and where to start. |
| `tam --version` | Read the product version from installed metadata; label command version separately if it differs. |
| `tam install ...` | Delegate to the installation contract in [the installation plan](installation-framework.md). |
| `tam` | Print a concise introduction and available starting points, then exit successfully. |
| `tam browse` | Explicitly open the local guide; print a readable text index when output is piped. |
| `tam welcome` | Open orientation explicitly at any time; never require it before `--help` or installation. |
| `tam explain <topic>` | Initially match curated local topics and give a clear miss message. |

Bare invocation never opens the browser or changes first-use state, whether
interactive or piped. `tam welcome` explicitly displays orientation. Record
that welcome was shown in `$XDG_STATE_HOME/tamlinux/welcome_seen` (falling back
to `~/.local/state/tamlinux/welcome_seen`) only after successful display,
whether through Lynx or the text fallback. `browse`, `--help`, `--version`,
and installation commands leave first-use state unchanged. The command must distinguish
terminal output from piped output and never emit browser control text into a
pipeline. It must check
whether Lynx is available and, if absent, show readable text and instructions
for installing Lynx so that HTML can be rendered.

## Knowledge format

Ship a small, semantic HTML corpus with relative links and a plain-text
fallback. Lynx is the optional terminal browser because it is already used on
the current workstation and works offline. If Lynx is unavailable, show the
text guide and instructions for installing it on the detected base; do not
start an installation automatically. `tam` locates the installed
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
- Add `tam ai` after hardware estimates can report their assumptions and
  uncertainty. A calculated speed is an estimate, not a measured benchmark.
- Add `tam config` once each setting has a clear owner and reversible
  operation. Read-only inspection should come first.

These are development directions, not features in the first release. The
first implementation uses C with the separate `libtam` foundation library,
following Fred's 2026-10-08 language directive. Lynx enables
interactive browsing when installed; plain-text help must work without it.

## Implementation order and review points

1. Set the command layout and version source; make `--help`, `--version`, and
   `install inspect` work before any state-changing installer step.
2. Package the minimal guide; check for Lynx before interactive browsing and
   provide the text guide plus installation instructions when it is missing.
   Keep piped output predictable in both cases.
3. Add explicit `welcome`, its successfully-displayed state, and the
   first curated `explain` topics.
4. Extend installation, explanation, AI, and configuration in that order,
   recording what each addition actually does in this plan.

## Review record

- **2026-09-23:** Fred confirmed the first command slice above, including the
  runtime Lynx check and readable text with installation instructions when
  Lynx is unavailable.
- **2026-09-23:** Fred confirmed automatic welcome on the first use of the bare
  command.
- **2026-10-07:** Terminal command renamed `tam`; install/help/welcome/explain
  behavior remains the approved first slice. Package and XDG namespace stay
  `tamlinux`; no additional features are authorized by the rename.
- **2026-10-08:** Fred specified that bare `tam` prints a concise introduction
  and exits, and `tam browse` explicitly opens the guide. This supersedes the
  automatic welcome/guide behavior of bare invocation. Implementation uses C
  with `libtam`; the separate local `tam` component repository contains the
  command development plan and scaffold.
- **Still open:** The later compound-command `explain`, `ai`, and `config`
  expansions need their own review before implementation.
