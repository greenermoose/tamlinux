# Omarchy removed before Hyprland (0.3)

- **Date**: 2026-10-04.
- **CLI Tool**: Claude Code (`claude`) `2.1.289`, from `detect-runtime.sh`.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`).
- **Authorship**: Fred set the direction and made each decision. Claude
  inspected the workstation, proposed the milestone and plans, and wrote these
  documentation changes.
- **Commit**: This commit.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> I need to install sway on this system, but first I want to start removing all the omarchy shell stuff. Take a look at the tamlinux plan. Let's include a milestone for when all the omarchy stuff has been stripped away. Here's what I'm imagining:
>
> a) We remove all omarchy code carefully, piece by piece, and keep this system working.
> b) Anything that used to say "Omarchy" will say "Tamlinux" instead.
> c) You (or other AI) will propose a new font and look and feel for Tamlinux which will brand it as an eco-conscious, high-performance, super-efficient workstation environment for linux.
> d) We will bump the version of tamlinux to 0.0.2 once we have stripped away all the omarchy stuff.
>
> Please let me know what you think of this plan and tell me how we can execute this. Do we need to update any of the planning in our repos? How far along are we to having omarchy removed and just leaving hyprland, wayland, etc. on the machine to keep it working?

> 1 make this milestone 0.3.
> 2 Yes, draft D53 and plans 18 and 19 for my review
> 3 Yes, please install the test sway now

> I'll take a look at plan 18. But first, I'm not sure about the linxu kernel. Do more research into that. I'd rather upgrade to another kernal rather than use a kernel I've alrady downloaded. Let's look into the latest arch kernel and see if we can switch to that. What does omarchy package up in its kernel that we might need?

> My decisions:
> 1 stock linux
> 2 leave the mirror now

## Work and decisions

- **Order changed.** Omarchy leaves the workstation before Hyprland. Claude
  pointed out that calling the Omarchy-free state 0.0.2 would contradict the
  existing series, where 0.0.x is for fixes and 0.1–0.3 are the steps that
  replace Omarchy. Fred chose **0.3**. 0.4–0.9 now fall back to the Hyprland
  session, and 1.0.0 removes Hyprland. The 1.x anchor is unchanged.
- **What 0.3 includes.** Every Omarchy function is replaced. The Hyprland
  configuration, shell environment, session entry, and memory and boot settings
  become Tamlinux-owned. Omarchy's packages, package mirror, repository, and
  kernel are removed. Visible names and the look become Tamlinux's.
- **Kernel.** The workstation moves to Arch's stock `linux` kernel. Claude
  compared Omarchy's kernel with Arch's: the build configurations differ in 76
  options, none relevant to this hardware, and most of the extra patches target
  hardware the workstation does not have. Fred chose stock `linux` and to leave
  the snapshot package mirror now, which brings the current Arch kernel with a
  full system upgrade.
- **Test session.** Sway was installed from Arch's repositories as a test
  session for the Sway adapter. It is not the workstation package, which builds
  Sway with Nix.
- **Look.** An agent proposed a palette, typeface options, and shape rules;
  Fred chose among them. They will appear publicly when 0.3 is accepted.

## Verification

- Documentation only. The milestone rows in `VERSIONING.md`, the README,
  `CHANGELOG.md`, and the desktop decoupling plan were checked against each
  other. Product version remains 0.0.1.
