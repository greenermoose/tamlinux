# Session: 2026-10-03 — Workstation package route and version series

- **Date:** 2026-10-03
- **CLI tool:** Claude Code `2.1.288` (`claude --version`, checked live)
- **Model:** Claude Opus 5.5 (`claude-opus-5-5`)
- **Commit:** This commit.
- **Transcript:** Retained privately by the author.
- **Scope:** Documentation only; no runtime code changed, nothing installed,
  and the product version stays 0.0.1.

## User direction

> Add a README.md to [redacted: private repository]/plans that explains the whole process by which we will rewrite the existing fred.* plugins, remove all Omarchy dependencies from my current system, and step by step create a [redacted: unannounced plans] package (including Wayland + sway + all my plugins + third-party packages + the [redacted: unannounced plans] CLI command) that can be installed to turn any linux system into a [redacted: unannounced plans] that works the way this system does. Ask if you have questions or whether the above does not comport with what we have already documented in our repos describing tamlinux and [redacted: unannounced plans]. [redacted: unannounced plans]

> In the README.md, describe the version #s that tamlinux will have and what they will correspond to in terms of the journey from omarchy linux to tamlinux to [redacted: unannounced plans].

> I have reviewed, edited, and accepted the README file. Please read it, ask any questions, and then commit and push once you're satisfied you understand it. Next, update the documents described in section 8 so they match the README. Then commit and push those changes. Close the nano review window.

> [redacted: unannounced plans]

## Decisions (Fred's, from the agent's questions)

1. The workstation package (Sway session, independent shell, `fred.*`
   plugins, selected third-party tools, and the command) installs on existing
   distributions; the Void base later carries the same package.
2. Fred's Arch workstation installs the package first and then removes
   Omarchy and Hyprland (1.0.0); the Void pilot follows on secondary hardware.
3. The package and command are named `tamlinux`.
4. Delivery: a Nix flake with a Home Manager module and a native host adapter
   on existing distributions; native `xbps-src` packages from the same
   sources on Void.
5. The version series in [`VERSIONING.md`](../../VERSIONING.md), which Fred
   confirmed as decided.

The phase breakdown, the version table, the host-ownership split, and the
early risks (graphics bridge for Nix-built Sway, locker PAM, portals and
keyring) are the agent's drafting, reviewed and edited by Fred.

## Changes

- `VERSIONING.md`: the 0.0.x–1.3 series; no planned 2.x; rewritten plugins
  become `fred.<id>` 2.0.0.
- `README.md`, `CHANGELOG.md`, `docs/plans/README.md`,
  `docs/plans/installation-framework.md`, `docs/plans/base-operating-system.md`,
  and `docs/plans/desktop-decoupling.md`: package-first route, Arch profile and
  host adapter, Nix/XBPS split, and desktop milestones renumbered 4–11 to
  match the version series.
- Reworded earlier public text about what follows Tamlinux, and redacted the
  matching quoted prompts in earlier session records. One record was renamed
  to `2026-09-28-antix-base-and-product-vision.md`.

## Verification

- Relative Markdown links in the changed files resolve.
- The public check in the provenance standard found no session IDs, store
  paths, local paths, or private repository names; the diff was read for
  shortened IDs.
