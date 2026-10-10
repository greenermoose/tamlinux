# Tamlinux versioning

Tamlinux uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The product number is [`VERSION`](VERSION) in this repository and the
matching `VERSION` in `tamlinux-packages`. The latter assembles exact source
commits and dependencies into the package installed for Test and Run.

## What the numbers mean

**The version is the plan.** The minor version names a *stage*, and the patch
names a *step* within it. A step is one change Fred tests on his workstation
and accepts into daily use; its version is its name. The first accepted step
of stage 0.3 is 0.3.0, the next 0.3.1, and so on. Every accepted step raises
the version, so the number shows which stage Tamlinux is in and how far
through it.

- A step's number is fixed when work on it starts. Steps not yet started may
  be split, merged, or renumbered when a stage is re-planned.
- Fixes ship with the step they belong to or the next one; they do not get a
  number of their own. Development work and documentation do not raise the
  version.
- **1.x** means Tamlinux no longer depends on [Omarchy](https://omarchy.com)
  or Hyprland. The 0.x stages remove Omarchy first (0.6), while Hyprland keeps
  running; **1.0.0** removes Hyprland. After 1.0.0 the same rule applies:
  stage 1.N, steps 1.N.k.

**Sequence revised 2026-10-07:** settings/state and menus (0.4), theme system,
fonts and identity (0.5), package/system ownership and boot-dependent final
removal (0.6), then Sway integration/package (0.7) and daily proof (0.8).
The former prepared compositor 0.4 schedule is deferred; accepted 0.0–0.3
versions and authored prototype records retain their identifiers. This
documentation change left the product version at 0.3.3. Fred subsequently
accepted settings/state step 0.4.0 on 2026-10-08 and daily protocol shadow
observation at 0.4.1 on 2026-10-09. Menu ownership follows at 0.4.2.

This scheme was adopted on 2026-10-05. Before it, minor versions were fixed
milestones and work between them raised no number, so the steps accepted
since 0.0.2 were numbered afterwards, in the order they were accepted
(0.1.0–0.1.22; see [`CHANGELOG.md`](CHANGELOG.md)). An earlier "0.0.3" was
planned but never issued.

| Stage | Tamlinux is there when | Base | Desktop |
| :-- | :-- | :-- | :-- |
| **0.0** | 0.0.1: the first workstation snapshot (Omarchy, Fred's patches, and the released `fred.*` 1.x plugins). 0.0.2: the foundation is owned: Arch's own package mirror and stock `linux` kernel, the Hyprland configuration, the shell environment, the session entry and units, and the login screen. | Arch | Omarchy shell on Hyprland |
| **0.1** | The desktop's session services run in the Tamlinux shell beside the existing bar: notifications, on-screen display, clipboard history, emoji and image pickers, reminders, the command menu, the background, screenshots and screen capture, the polkit agent, media keys, idle and Stay Awake, battery warnings, and the lock screen; and the commands the desktop calls are Tamlinux's own. | Arch | Existing bar, Tamlinux services |
| **0.2** | Every key binding and menu entry runs Tamlinux's own commands, including the keybinding viewer, night light, and the audio, Bluetooth, network, power, and speed-test panels. Only the bar's own keys and settings wait for 0.3, and the theme, branding, and boot-splash entries for 0.5 and the boot work. Reached 2026-10-05 (0.2.0–0.2.6). | Arch | Existing bar, Tamlinux services and panels |
| **0.3** | The Tamlinux shell, with all eight rewritten plugins and its own tray, indicators, and status widgets, is the daily bar. | Arch | Tamlinux shell on Hyprland |
| **0.4** | Tamlinux owns non-theme settings/state/cache, helper entry points and menu extensions. All readers/writers agree; theme and boot exceptions remain explicitly scheduled. | Arch | Tamlinux shell on Hyprland |
| **0.5** | Tamlinux's own look and name: one theme source for every application, its own fonts, and its name on the login screen, menus, and About. | Arch | Tamlinux shell on Hyprland |
| **0.6** | Package and system ownership are proved; Omarchy runtime dependencies are removed after independent boot/update/recovery is verified. Daily Tamlinux on Hyprland is accepted as the first proof gate. | Arch | Tamlinux on Hyprland |
| **0.7** | Helpers, night light and capture pass the compositor contract on both adapters; the package installs a verified Sway session beside independent Hyprland, with physical monitor-recovery evidence. | Arch | Both sessions available |
| **0.8** | Physical Sway daily use and all required workflow/plugin parity are accepted as the second proof gate, with independent Hyprland available as fallback. | Arch | Tamlinux on Sway |
| **1.0** | Hyprland is removed from the workstation after accepted independent Hyprland and Sway daily-use proofs; the installed workstation package runs Sway only. | Arch | Tamlinux on Sway |
| **1.1** | The same package installs on a second, different distribution on another machine. | Arch + one other | Tamlinux on Sway |
| **1.2** | Void pilot: the same sources as native `xbps-src` packages on Void + runit + Btrfs + seatd, with complete recovery proved. antiX Core + runit only if Void has a showstopper. | + Void pilot | Tamlinux on Sway |
| **1.3** | Repeatable live-media base install, single-command workstation activation, and the terminal-only profile. | + Void pilot | + terminal-only |

Tamlinux is an independent, continuing project. These milestones do not define
an end date or a final 1.x release. Later stages and major versions will follow
the project's needs and compatibility rules; there is no planned retirement.

Plugins version separately. Each rewritten plugin becomes `fred.<id>` 2.0.0,
because it drops the Omarchy shell's plugin API; the 1.x lines remain as released. The
workstation package carries the Tamlinux version and records its component
versions in its manifest.

**0.0.1** is the first workstation snapshot: this daily driver, working as
Tamlinux. Installing on a second computer comes at 1.1, after the
workstation package has replaced the inherited desktop on this machine.

## Candidate letters and lifecycle branches

Work toward a release uses letters: people say **0.4.2a**, **0.4.2b** and
**0.4.2c**. `VERSION` and changelog headings use the SemVer forms `0.4.2-a`,
`0.4.2-b` and `0.4.2-c`. Nix and native package recipes use `0.4.2pre.a`,
`0.4.2pre.b` and `0.4.2pre.c`, so candidates sort after 0.4.1 and before
0.4.2. The spelling `0.4.2a` is for conversation, not a package version.
Candidate letters have no release tags or GitHub Releases.

| Branch | Meaning | Promotion |
| --- | --- | --- |
| feature branches | Experiments and work not ready for integration | Merge into develop when ready |
| `develop` | Work toward the next version; it may be broken | Selected on Fred's Test instruction |
| `test` | The exact candidate Fred is testing | Promoted on Fred's Run instruction |
| `main` | Code Fred runs; the default branch | Tagged only on Fred's Release or Ship instruction |

This model applies to `tamlinux`, `tamlinux-packages`, `tam`, `libtam` and
`tamlinux-tools`. Promotion is fast-forward only and moves the same selected
commits, without a merge commit. Fixes found in Test go back through Develop
and Test; they are not implicit Run acceptance. Keep unfinished work on feature
branches so the develop candidate can be promoted whole.

A Test selects an exact committed assembly in `tamlinux-packages`; its lock
file pins the product, components and dependencies. Test and Run install the
same immutable package outputs through the same managed endpoints. Changed
source or package recipes create a new candidate requiring Test. Record the
exact assembly and active generation, verify installed endpoints, and retain
the prior generation plus any mutable-state recovery needed. The
[deployment contract](https://github.com/greenermoose/tamlinux-packages/blob/main/docs/deployment.md)
describes this boundary.

Before the final promotion for a release, change both `VERSION` files to the
plain version (for example `0.4.2`), consolidate its changelog entries under
that version, and record the exact component delivery. That produces a new
package which needs Test before Run. Release tags the same accepted commits
already on `main`: `X.Y.Z` and `vX.Y.Z`, plus floating `X.Y` and `vX.Y`, in
both the product and delivery repositories, with release notes. Automated
checks and version numbers do not replace Fred's physical acceptance.

## What Tamlinux version is not

Plugin versions (`fred.workspaces`, `fred.clock`, and the rest), the
`tam-plugin` CLI, and the `ecosystem-fred-tamlinux` patch registry stay
independent artifacts. They have their own `VERSION` or `manifest.json`
numbers.

The last overlay-era workstation composite was **1.5.1**. Those git
tags stay. They are no longer the product version. 0.0.1 is that overlay
frozen into Tamlinux.

## Tamlinux version vs Home Manager generation

These are two different counters. Do not set Tamlinux to `0.0.x` where `x` is
the Home Manager generation.

| | Tamlinux version | Home Manager generation |
| :-- | :-- | :-- |
| What it is | Declared product snapshot (portable, tagged, changelogged) | Local activation counter on one machine |
| Source of truth | `VERSION` files | `home-manager generations` / `~/.config/tamlinux/generation` |
| Advances when | Fred decides the product changed | Every successful `home-manager switch` |
| Portable? | Yes — the same number on a second computer | No — a fresh machine starts at 1 |

On a running workstation:

```bash
cat ~/.config/tamlinux/version           # product version of the active generation
echo "$TAMLINUX_VERSION"                 # the same number, as this process saw it
cat ~/.config/tamlinux/generation        # this machine's Home Manager generation
home-manager generations                 # full local rollback list
```

The file is the source of truth: activation writes it with every generation.
`$TAMLINUX_VERSION` is copied from it in three places. Every new bash shell
reads the file, the systemd user manager loads it at login (`environment.d`),
and each activation also sets it in the running user manager, so services
and applications started after a switch see the new number without a new
login. A process that was already running keeps the number it started with.

`$OMARCHY_CONFIG_VERSION` and `~/.config/omarchy/version` remain as
compatibility aliases of `$TAMLINUX_VERSION` until 0.5 removes them. They are
not a second product.
