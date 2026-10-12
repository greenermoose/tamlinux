# 0.4.3 OpenClaw retirement and continuation

- **CLI Tool**: Codex CLI `0.162.1` (checked live).
- **Model**: `gpt-6.1-sol` (runtime detected).
- **Transcript**: Retained privately by the author.
- **Stage**: Develop. No candidate built or activated in this slice.

## Guiding prompts

> Advance tamlinux 0.4.3, while also looking for ways to improve your time and token efficiency. You should have a handoff available. Look for the handoff, read it, and plan the next slice of work to do. This could include improvements to your time and token efficiency, or it could be exclusivelly work to get tamlinux 0.4.3 ready for testing. Ask if you have any questions.

> Why are we talking about OpenClaw? I'm not using it.

> Retire OpenClaw support from the product.

## Change and authorship

The owner explicitly changed the retained-function boundary. Codex removed the
OpenClaw default-agent menu entry and `tam-agent` dispatch branch, added an
installed-command regression, and updated current engineering handoffs.
OpenClaw launch/onboarding helpers were never installed by this product source;
their transfer is no longer required. Existing user selections and application
data are preserved. Other agent choices remain supported.

Historical menu/keybinding and package-output evidence remains unchanged and is
identified as historical. Its prior hashes/counts do not describe a rebuilt
retirement output. The next slice owns retained default-agent selection and
transitive dependencies, followed by controls/plugin setters.

Efficiency measures target bounded inspection, correct owning-repo working
directories, compact audit artifacts and focused checks before package builds.
No comparative token or wall-time saving is claimed.

## Verification

- 15 staged installed-helper tests pass (`make check` in `commands/tam-shell`).
- 5 menu-parser tests pass, including default-menu parsing and route validation.
- The retirement regression rejects the preceding installed `tam-agent` in
  temporary staging (two failing launch-mode cases), and passes after removal.
  It supplies installed OpenClaw/adapter recorders, verifies no process launch,
  and checks the existing selection remains intact.
- `git diff --check` passes.
- Package-output builds, actual graphical launch, clean-host I01–I09 and physical
  acceptance remain outside this source-retirement verification.


## Accepted follow-through: agent defaults and microphone controls

Guiding prompt (excerpt; time/token discipline also followed):

> I accept your assessment of Hermes. Proceed with that in mind. I also accept the following recommendations from your 18-step-0.4.3-next-slice report
>
> 1) Transfer tam-default-agent into tamlinux/commands
> 2) Remove OpenClaw branches
> 3) Inspect every helper and tool edge before adding delivery wrappers.
> 4) Verify state read/write agreement with isolated HOME/XDG paths, alias selection,
> installation failure without changing the default, unbuilt Hermes stubs, prompt
> argv and retired selections.
> 5) Extend the existing installed-helper harness;
> reuse its recorded terminal/service boundaries without running real agents or
> installers.
> 6) Then build the changed command output and installed integration
> under short exclusive claims, run actual-output probes, and audit all five outputs
> with `--format compact --report /tmp/0.4.3-agent-audit.json`.
> 7) Afterward, take one controls caller chain at a time: audio/network/power controls
> and plugin setters. Inspect mutable writers before choosing the first controls
> batch; monitor brightness/text size reach hardware, theme and terminal writers
> and should not be treated as two isolated scripts.

Codex transferred `tam-default-agent` with canonical alias checks, atomic XDG
selection writes and declared coreutils/grep/Mise dependencies. Hermes integration
was retired on the owner's accepted assessment. OpenClaw and Hermes requests are
rejected before executing stubs, installing, launching or changing defaults.
The first controls chain owns microphone default and existing capture-stream
routing with `wpctl`, `pactl` and awk. Host sound servers own the resulting state;
the prior best-effort behavior is retained. Other mutable controls chains were
inspected before choosing this operation.

Twenty-five installed-helper tests and five menu-parser tests pass; Nix command
builds and installed-component integration pass. Original-code comparisons reject
the previous retired-agent and alias behavior. The agent stage passes 23 isolated
real-output probes, followed by 24 after microphone routing. The five-output
audits report 99 then 98 unresolved lexical names, with 52 inherited-name locations.
Readiness remains false, with nine pending requirements and no clean-host proof.

[Current work and limits](../plans/0.4.3-agent-default-closure.md) records provider
boundaries, actual-output evidence and the next three actions. No real agents,
installers or live sound servers were run; no candidate pin/version/activation
changed. Inspection used bounded ranges and compact artifacts, with repeat
builds limited to the new controls code. No comparative savings are claimed.
