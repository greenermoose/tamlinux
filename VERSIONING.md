# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The product number is [`VERSION`](VERSION) in this repository and the
matching `VERSION` in `tamlinux-packages`. The latter assembles exact source
commits and dependencies into the package installed for Test and Run.

## What the numbers mean

**A minor version is a list of goals; the patch counts candidates toward
it.** Each minor version, such as 0.5, has a list of goals: what that
version will include. "Working toward Tamlinux 0.5" means working toward
that list. A candidate is one prepared package assembly that Fred can test
on his workstation. The first candidate of 0.5 is 0.5.0, the next 0.5.1, and
so on. Fred decides when a minor version starts and when a candidate is
prepared.

- A candidate's number is fixed when its assembly is prepared and is never
  reused. A fix to a prepared candidate is a new candidate with the next
  number; the earlier candidate's exact record stays as it was.
- Any candidate may be run day to day on Fred's word. "The 0.5 Run" is the
  Run of a candidate that meets every 0.5 goal; only such a candidate is
  released, and "Tamlinux 0.5" means that release.
- Not every number is released, so release tags have gaps. Development work
  and documentation that do not change an assembly do not raise the version.
- A minor version stays open for fixes until Fred starts the next one. After
  that, fixes arrive in the next minor version's candidates; a fix that
  cannot wait can still be released as the next patch of the released
  version.
- **0.4** removes Omarchy while Hyprland keeps running. Tamlinux 0.7.0
  starts tam-pane dogfooding with Hyprland available as a fallback.
  The timing of Hyprland retirement remains open.

**0.4 and 0.5 are complete.** Before this scheme, 0.4.0 to 0.4.4 were milestones of
their own, and 0.4.4 used lettered candidates (0.4.4-a to 0.4.4-m). From
0.4.5 the goal-list scheme applied; released **0.4.8** closed Gate A
(Omarchy removed) and released **0.5.12** completed **0.5** (Blue Sparkler).
Develop continues on **0.6** (KBN WB).

The scheme was adopted on 2026-10-05 and given goal lists on 2026-10-20.
Before 2026-10-05, minor versions were fixed milestones and work between them
raised no number, so the steps accepted since 0.0.2 were numbered afterwards,
in the order they were accepted (0.1.0–0.1.22; see
[`CHANGELOG.md`](CHANGELOG.md)). An earlier "0.0.3" was planned but never
issued.

## Versions

| Version | Goals |
| :-- | :-- |
| **0.0** | Foundation: Arch's own package mirror and stock kernel, with a Tamlinux-owned Hyprland configuration, shell environment, session entry and login screen. |
| **0.1** | The desktop's session services run in the Tamlinux shell beside the existing bar. |
| **0.2** | Every key binding and menu entry runs Tamlinux's own commands. |
| **0.3** | The Tamlinux shell and its rewritten plugins are the daily bar. |
| **0.4** | A packaged desktop independent of Omarchy: it installs on clean Arch/Hyprland, owns login, boot and sleep on this workstation, and the Omarchy packages are removed (first proof gate). |
| **0.5** | Input usability and a new look. |
| **0.6** | A dependable Arch/Hyprland baseline, also running on a second machine, with phased dependency reduction. |
| **0.7** | Start dogfooding tam-pane, tam-clam, tam-last and tam-edit in 0.7.0. Keep Hyprland as a fallback. |
| **0.8** | Compositor milestone open. |
| **1.0** | Prove the fresh-install path. |
| **1.1** | The same package on a second distribution. |
| **1.2** | A Void pilot with native packages. |
| **1.3** | Repeatable installs and a terminal-only profile. |

Tamlinux is an independent, continuing project. These versions do not define
an end date or a final 1.x release. Later versions will follow the project's
needs and compatibility rules; there is no planned retirement.

**0.0.1** is the first workstation snapshot: this daily driver, working as
Tamlinux.

## Cultivar names

Each minor version has a cultivar name, shown with its version:
`tam --version` prints `Tamlinux cultivar Incipiens 0.4.5`. The names come
from cultivars of the tamarack (*Larix laricina*), the tree behind the *Tam*
in Tamlinux, written as registered. The name of 0.4, Incipiens (Latin for
"beginning"), is coined rather than taken from a cultivar. The
[`CULTIVAR`](CULTIVAR) file holds the current minor version's name, and the
package installs it beside the version file. Candidates prepared before the
file existed (through 0.4.4-m) show no name.

## Other version numbers

Plugins version separately. Each rewritten plugin becomes `fred.<id>` 2.0.0,
because it drops the Omarchy shell's plugin API; the 1.x lines remain as
released. `tam`, `libtam` and `tamlinux-tools` keep their own versions. The
workstation package carries the Tamlinux version and records its component
versions in its manifest.

## Candidates and lifecycle branches

From 0.4.5, each prepared candidate has a plain `X.Y.Z` version: 0.4.5, then
0.4.6 for the next, and so on. `VERSION`, changelog headings, bundle and
native package recipes all write the same number, and tam-bundle and pacman
sort it correctly with no special spelling. Never reuse a number for a changed assembly: once an
assembly has been prepared under a number, fixes use the next number and
preserve the earlier candidate's exact record. A candidate has no release tag
or GitHub Release unless Fred releases it.

Before 0.4.5, candidates used letters: people said **0.4.4a**, and `VERSION`
and changelog headings wrote `0.4.4-a` while Nix and native package recipes
wrote `0.4.4pre.a`, so letters sorted before the plain version. Letters end
when the first 0.4.5 candidate is prepared. The preparation tool refuses a
letter at 0.4.5 or later, and a plain number for a version that already had
letters, so there is no plain 0.4.4. Letter identifiers keep their meaning in
historical records, and 0.4.5 and every later number sort after them.

| Branch | Meaning | Promotion |
| --- | --- | --- |
| feature branches | Experiments and work not ready for integration | Merge into dev when ready |
| `dev` | Work toward the next version; it may be broken | Selected on Fred's Test instruction |
| `test` | The exact candidate Fred is testing | Promoted on Fred's Run instruction |
| `main` | Code Fred runs; the default branch | Tagged only on Fred's Release or Ship instruction |

This model applies to `tamlinux`, `tamlinux-packages`, `tam`, `libtam` and
`tamlinux-tools`. Promotion is fast-forward only and moves the same selected
commits, without a merge commit. Fixes found in Test go back through Develop
and Test; they are not implicit Run acceptance. Keep unfinished work on feature
branches so the dev candidate can be promoted whole. The one exception
is a fix to a released version that cannot wait for the next minor version:
on Fred's word it is prepared on a short branch from `main`, goes through
Test and Run, and `main` is then merged into `dev` once.

A Test selects an exact committed assembly in `tamlinux-packages`; its lock
file pins the product, components and dependencies. Test and Run install the
same immutable package outputs through the same managed endpoints. Changed
source or package recipes create a new candidate requiring Test. Record the
exact assembly and active generation, verify installed endpoints, and retain
the prior generation plus any mutable-state recovery needed. The
[deployment contract](https://github.com/greenermoose/tamlinux-packages/blob/main/docs/deployment.md)
describes this boundary.

A release is a candidate Fred has tested and run that meets every goal of
its minor version. On Fred's Release instruction
the same accepted commits already on `main` are tagged `X.Y.Z` and `vX.Y.Z`,
plus floating `X.Y` and `vX.Y`, in both the product and delivery repositories,
with release notes covering everything since the previous release. There is no
final version bump or rebuild: the released package is the package that ran.
Candidate numbers that were never released are skipped in the tags. Automated
checks and version numbers do not replace Fred's physical acceptance.

## What Tamlinux version is not

Plugin versions (`fred.workspaces`, `fred.clock`, and the rest), the
`tam-plugin` CLI, and the `ecosystem-fred-tamlinux` patch registry stay
independent artifacts. They have their own `VERSION` or `manifest.json`
numbers.

The last overlay-era workstation composite was **1.5.1**. Those git
tags stay. They are no longer the product version. 0.0.1 is that overlay
frozen into Tamlinux.

## Where the installed version lives

A tam-bundle install records the version with the installed product:

```bash
cat /usr/lib/tamlinux/current/share/tamlinux/version    # e.g. 0.6.28
cat /usr/lib/tamlinux/current/share/tamlinux/cultivar   # e.g. KBN WB
tam-bundle status        # live and previous bundle, and their hashes
tam-deploy status        # the recorded assembly and stage
```

`/usr/lib/tamlinux/current` links to the live bundle's version directory, and
the previous bundle stays installed beside it for rollback. The shell copies
the version into `$TAMLINUX_VERSION` when it starts; a process that was already
running keeps the number it started with.

A Home Manager generation is not a Tamlinux version. Machines still carrying
a Home Manager profile from Nix delivery keep it only until Nix is retired;
never derive a version number from a generation counter.

Gate A (released 0.4.8) removed Omarchy as a dependency. Any leftover
`$OMARCHY_CONFIG_VERSION` or `~/.config/omarchy/version` paths on a host are
migration residue, not a second product version. Do not treat them as current
Tamlinux versioning.
