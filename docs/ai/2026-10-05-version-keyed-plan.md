# Session: 2026-10-05 — Every accepted step is a version

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > 1 add a short slice. Do not break keybindings. The sooner all keybindings
  > work under tamlinux the better.
  > 2 make it so the 2.0.0 plugins do not depend on omarchy. They should get
  > everythign they need from tamlinux.
  > 3 Put R9d where it needs to go
  > 4 We can freeze updates while we're making the transition from omarchy to
  > tamlinux
  > 5 I have another project in the works to deal with the boot partition.
  > Postpone that if possible, or if we need to fix the boot partition sooner
  > for some reason, let me know that and I can prioritize the boot clean up.
  >
  > This would be a good time to think through the entire plan very carefully
  > and do a renumbering. The R4.15abc stuff is ridiculous. We should have a
  > more thoughtful numbering system. Also think more carefully about the
  > versioning for tamlinux. We seem to be doing a lot of work for zero
  > increase in version numbers.
  >
  > Ask if you have questions. I think this is a good opportunity to do a
  > thorough, careful, and rational rewrite and renumbering of the entire
  > omarchy to tamlinux project and all plans.

  > I would like to use tamlinux version numbers as the key to the whole plan.
  > Each step should correspond to some increase in the tamlinux versioning
  > scheme.

  > 2 commit the private plans and public drafts

  > I do have one question for you: why do you call it the "omarchy shell" but
  > the "tamlinux host"? What is the difference? It seems like functionality
  > the Omarchy "shell" was providing is now being povided by the tamlinux
  > "host". Why call it a "host"?

  > Yes, do the Tamlinux shell sweep now. Explain the change in terminology.

  > Explain the verb "to vendor." You use that in an unusual way in the plan.
  > Where did that usage come from? Is there a more common way to describe
  > porting over code from working in the omarchy shell to working in the
  > tamlinux shell? To "vendor" something isn't clear to me what that means.

  > I want both. Lets use the word "port" to describe what we're doing: we're
  > porting packages from the omarchy shell to the tamlinux shell.

## Key decisions and implementation notes

- Fred chose, from options the agent offered: the **minor version is a stage
  and the patch is a step**, so each accepted step is the next patch (the
  step's version is its name); the steps accepted since 0.0.2 are **numbered
  retroactively** in acceptance order (0.1.0–0.1.22), untagged; and the
  freeze covers only the inherited desktop's package repository, not Arch
  updates.
- The stages after 0.1 were re-planned around a re-audit: 0.2 moves every key
  binding and menu entry first (the inherited shell's audio, Bluetooth,
  network, power, Wi-Fi QR, and speed-test panels had no owned equivalent, and
  stopping that shell would have broken their keys), 0.3 is the bar, 0.4 the
  compositor contract, 0.5 the look, 0.6 removal, 0.7 the package beside
  Hyprland, 0.8 Sway as the daily driver. 1.0.0 still removes Hyprland.
- The planned 0.0.3 was never issued. The four earlier numbering schemes for
  the same journey (phases, desktop-decoupling steps, a working plan's step
  names, fixed-meaning versions) are retired.
- **Terminology.** The agent answered that there is no difference: "host"
  came from the first proof, whose only job was to host one plugin, and
  stuck as the program grew into a full shell. Fred asked for the sweep: the
  program is now *the Tamlinux shell*, and "host" means only the plugin-host
  contract and, for the workstation package, the host distribution and host
  adapter. Current docs were swept; dated records keep the old word, and
  `desktop/README.md` says so.
- **"Port" for code taken over.** The agent explained that "vendoring"
  usually means keeping an unchanged copy of a dependency, which hides the
  adapting and owning. Fred chose "port": the shell's file headers, the
  service table in `desktop/README.md`, and its names note now say "ported".
- Changed: `VERSIONING.md` (rules and stage table), `CHANGELOG.md` (the
  0.1.0–0.1.22 table), `VERSION` (0.1.22), `README.md` status, the desktop
  decoupling milestone table and status, the plans index, the installation
  framework's version references, and `desktop/README.md` (also its names
  note).

## Verification

- Every retroactive number follows the order of Fred's recorded acceptances.
- The `omarchy-*` command inventory after 0.1.23's code assigns each of its
  39 remaining names to a planned step; none is unassigned.
- Documentation only in this repository; no code changed.
