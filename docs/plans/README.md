# Development plans

Tamlinux is an independent Linux workstation environment. The package remains
`tamlinux`; its terminal command is `tam`. A plan describes work and
acceptance, not an installed component.

**Status (2026-10-31):** Product develop is **Blue Sparkler 0.5.11**
([VERSION](../../VERSION), [CULTIVAR](../../CULTIVAR)). Gate A closed with
released **0.4.8** (2026-10-22): Omarchy packages are gone; Arch/Hyprland
remains the current host. Candidate assemblies and deployment live in
[tamlinux-packages](https://github.com/greenermoose/tamlinux-packages).

This index lists **open** product plans only. Finished Gate A / 0.4.3–0.4.4
plans and dated evidence are in Git; see [FILING-CARD.md](FILING-CARD.md).
Do not treat filing-card entries as current guidance.

Stage and branch rules for public repos are in
[VERSIONING.md](../../VERSIONING.md). Full stage policy (who may move Test,
Run, and Release) is private operating procedure, not duplicated here.

| Plan | Current scope |
| --- | --- |
| [Easy workstation upgrades](workstation-upgrade.md) | Approved 2026-10-30: released-assembly upgrades and recovery. |
| [Input usability](input-usability.md) | Approved for 0.5 (K22–K25): modifier model, clipboard, titlebar close. |
| [Keybinding usability](keybinding-usability.md) | Open 0.5 binding and explorer work. |
| [Start menu](start-menu.md) | Combined Quick Launch + Settings; packaged acceptance pending. |
| [Console-first startup](console-first-startup.md) | Text login; optional desktop via `tam-desktop`. |
| [Console welcome](console-welcome.md) | Console greeting and first-run messaging. |
| [Targeted text-console monitors](console-monitor-control.md) | Console fb mapping and native monitor CLI/TUI. |
| [Native input startup](native-input-startup.md) | Input stack at session start. |
| [Remove screensaver](remove-screensaver.md) | Retire screensaver paths. |
| [Theme system](theme-system.md) | Retained theme ownership; Tamarack redesign in 0.5. |
| [Fleet](fleet.md) | Registered-host deploy and fleet tools. |
| [`tam` command](tamlinux-command.md) | Workstation plan for the separate `tam` component. |
| [Compositor protocol layer](compositor-protocol-layer.md) | Protocol facade; Sway adapter later. |
| [Sway integration](sway-integration.md) | After dependable Hyprland baseline (0.7+). |
| [Base operating system](base-operating-system.md) | Second distro, then Void pilot. |
| [Operating-system horizons](operating-system-horizons.md) | Research only; chooses no base. |
| [Retire hey](retire-hey.md) | Remove remaining hey identifiers. |

Product behavior and generic defaults belong here. Exact assemblies belong in
`tamlinux-packages`; personal selections belong in consumer config. New Develop
source needs its own exact delivery selection; moving source does not establish
runtime parity.
