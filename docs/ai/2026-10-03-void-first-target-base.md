# Void-first target base and repository alignment

- **Date:** 2026-10-03.
- **CLI Tool:** Codex CLI (`codex`) `0.160.0`, checked live and against session metadata.
- **Model:** `gpt-6.1-sol`, verified against logged turn metadata.
- **Authorship:** Fred selected the target/fallback order; Codex authored the documentation updates.
- **Commit:** This record accompanies the Void-first target documentation commit.
- **Approval:** Fred explicitly authorized updating repositories, committing, and pushing.
- **Transcript:** Retained privately by the author.

## Guiding prompts

> Update all repost to reflect this latest thinking: We will try void as our base linux distro. If we run into a showstopper, then we will try antix core. After you have update all repos to clarify this target base operating system, then commit and push. Ask if you have any questions.

> Rewrite documents; don't do stuff like 'Where this document says "River", read "Sway".'

## Decisions and work

Set Void Linux as the first base to try, with antiX Core if Void has a
showstopper. Keep runit and Sway/seatd, prefer Btrfs for the pilot, and compare
musl/glibc. Evaluate native XBPS/xbps-src packaging while retaining portable
installation on existing Linux as a delivery goal; Nix remains a candidate.
Resource and security benefits are hypotheses until measured.

Rewrite active architecture, diagrams, installation, ownership, and milestone
sections directly. Preserve dated quotations and captured evidence. The
[base plan](../plans/base-operating-system.md) records the target and acceptance
criteria; README, versioning, installation, desktop decoupling, and plan indexes
are aligned. Documentation changes do not migrate the workstation, install
packages, promote the shell candidate, or bump the product version.

## Verification

- Audited target references across the local Tamlinux and Suspra repositories;
  updated the three repositories carrying target architecture and planning.
- Checked changed Markdown links and fenced-code balance, and Git whitespace checks.
- Checked syntax of the dependency collector after changing its target-description text.
- Reviewed the public changes for private paths, repository names, and session identifiers.
- Fetched the affected remotes and verified the local branches matched their remote heads before committing.
- No Void installation, hardware reliability, libc savings, or rollback implementation is claimed by this documentation work.
