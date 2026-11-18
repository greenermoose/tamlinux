# Conventional workstation recipe layout

- **Date**: 2026-11-10
- **CLI Tool**: Codex CLI (`codex`) `0.167.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted staging implementation and verification.

> Approve 0.8 tool; continue recipes

`install-bundle` stages with `PREFIX=/usr`. The command scripts get fixed
private data paths under `/usr/lib/tamlinux/current`. The format-2 builder
can split that tree away from real command files, manuals and vendor
files. The existing relocatable install target remains available.

The staging target copies origin-checked vendor defaults, expresses the
two session service links as a systemd `Wants` drop-in, and materializes
the fontconfig default as a regular file. The bundle stages the renamed
`tam-start` and `tam-suspend-unless-stay-awake` executables. The tam nut
owns the console aliases `hi` and `start` and the bootstrap command
`tam-nut`. The hardware provider descriptor expects `asdcontrol`
at its native `/usr/bin` path, with that third-party binary supplied by
the rootstock. Login activation and package ownership transition are
later integration work.

`python3 -B -m unittest discover -s desktop/tests -p test_product_install.py -q`
passed all four tests, including the staged layout, known private data
paths, regular vendor files and rejection of invalid staging roots. This
verification exercised temporary directories. It supplies no installed
candidate or hardware acceptance.

## Console activation integration

> Approve tam nut development; continue integration

The format-2 native menu is `tam-start` 0.3.0. Its interactive entry
finishes the prepared system/settings transaction before drawing the menu
and re-executes the selected real command when the version link changes.
The staged `tam-desktop` entry follows the same protocol.

Libtam-based native commands use the shared startup barrier. The
`tam-monitor` repair child retains its existing recovery entry.
Staged service launch wrappers use the lightweight system barrier.
The native product build, menu checks, three isolated entry tests and
four product staging tests passed using a temporary library prefix.
This verifies source behavior. Real login and display acceptance remain.

## Bundle delivery discovery and preflight

The delivery draft reads a bounded, duplicate-free record from the exact
assembly commit. It checks the frozen recipe's ancestry, version and
component pins, then verifies the cached archive's bytes, carried identity
and native runtime requirements. Private settings captures are refused in
public delivery records. Read-only preflight invokes no Nix build,
privileged preparation or live activation.

All 121 deployment tests passed, including the existing Nix activation and
recovery fixtures. Five bundle fixtures cover source agreement, metadata
bounds, tool minimums and exact-archive preflight. The runtime refusal case
was also checked after that combined run. These are isolated fixture tests.
Bundle install/init explicitly refuse while migration activation is still
incomplete; the existing Nix path continues unchanged.
