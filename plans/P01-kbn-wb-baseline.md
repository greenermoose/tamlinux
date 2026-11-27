# P01 · KBN WB dependable Arch baseline

- **Phase:** PH02
- **Status:** Done (2026-11-27). Whole-checklist Test accepted on 0.6.39; 0.6.42
  advanced to Run, accepted in daily use, and released as the final KBN WB
  baseline (`0.6.42`, `v0.6.42`, `0.6`, `v0.6`).
- **Versions:** 0.6.42

## Goal

Make the Arch/Hyprland workstation dependable in daily and console use,
including updates and recovery. Establish reproducible source delivery
before changing the compositor in PH03.

## Milestones

1. **Stabilize the workstation.** Prove the GPU-resume and hibernation
   mitigations, carry only bounded upstream patches, and check the
   retained console, input, laptop, and desktop workflows.
2. **Prove locked source delivery.** Build pinned Git clones with
   `make` and `make install`; use Pacman for Arch dependencies. Exercise
   fresh-file and bare-rootstock installs, preserving upgrades, and
   source rollback across the fleet. See [P21](P21-source-install.md)
   and the [candidate workflow](P05-candidate-workflow.md).
3. **Accept the baseline in daily use.** Bind the release evidence to the
   recorded candidate, account for the required fleet checks, and record
   Fred's final daily-use acceptance and separate Release instruction.

## Acceptance and dependencies

The work retains Arch Linux, Hyprland, and Quickshell. Close the phase when
the console and desktop, retained daily workflows, laptop operation, and
source-install recovery have passed their applicable checks and the release
has shipped. Keep a tested recovery point when trying Northern Torch.
PH03 development and trials can overlap this closeout.

## 0.6.28 candidate plan · historical checkpoint

Approved on 2026-11-16. This was a bundle-era candidate plan, with its
physical acceptance pending at the original planning checkpoint.
The later source-install transition is covered by P21 above.

### Product

Use only `tam-suspend-unless-stay-awake` throughout source, packaging and new
idle configurations. No compatibility executable or repairs of older installed
versions. Native tam reads the selected format-2 identity rather than inherited
environment metadata. Target tam 0.61.0 / corpus 0.95.0, libtam 0.7.1,
tam-edit 1.0.3, tam-data 1.0.1 and tam-bundle 0.14.0.

### Documentation

Info, curated tldr and Arch Wiki are independently optional per host. Canonical
roots are `/usr/share/doc/info`, `/usr/share/doc/tldr`, and
`/usr/share/doc/arch-wiki`. Core guide installation excludes tldr data.
The same artifact carries verified optional groups. Selection is recorded in
prepare/apply transactions, verification and recovery; native-owned collections
are reused only when their content matches, and are never overwritten or removed.
Documentation payloads contain non-executable data only.

The guide supplies `data-doc-source` link attributes and `data-doc-missing`
spans. Its text describes unavailable collections without active links. The
reader probes the same roots used by its documentation commands on every page
load. Empty directories or index-only placeholders do not count as installed.

### Rollout

First prove declared dependencies in a minimal isolated Arch root. Install the
same frozen assembly on a clean console-only Arch test host, with a clean home
and all three optional collections. Save unpublished work before resetting it.
Then upgrade the reserve laptop while keeping the daily driver available;
upgrade the daily driver last. Preserve personal data, credentials, unrelated
software and hardware settings on both preserving upgrades.

Physical acceptance covers console/desktop startup, versions, fonts, networking,
applications, sound, blanking, suspend/resume and hibernation where supported.
Keep host-specific timeouts and locking policy. No speculative blanking patch:
the reported intermittent behavior recovered and its separate cause is unknown.

Package/Test, privileged steps, Run and Release retain their separate authority.
Record exact source, artifact, bootstrap, per-host selections and recovery.
A changed frozen payload needs a new candidate instruction.

Claude's reviewed display bug-hunt fixes are included: refresh bounded
workspace reconciliation retries after late output return, select the corrected
MSI wake helper in declared host sources, and correct installed-state records.
The integrated desktop suite passes 877 tests (14 skipped). The corrected
MSI helper and repaired host paths are selected in committed host sources.
Physical acceptance was pending at that checkpoint.
