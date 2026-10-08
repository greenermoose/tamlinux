# Session: 2026-10-08 — Compositor protocol layer and base-plan additions

- **CLI Tool**: Claude Code (`claude`) `2.1.294`, checked from the running tool.
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`), from the session's model identification.
- **Authorship**: Fred supplied the direction and accepted the approach. Claude researched peer projects, reviewed the Sway adapter, probed Quickshell on the running compositor, and wrote the planning text.
- **Commit**: Not yet committed; awaiting Fred's review. No implementation or deployment.
- **Product version**: Unchanged at accepted 0.3.3.
- **Transcript**: Retained privately by the author.

## Guiding prompts

> Think about what I'm attempting with tamlinux. Do some research to find other developers doing similar projects. Write up a report so we can learn from their experience and avoid making unnecessary mistakes.

> First question for you: based on what you've found, do you think we should re-revaluate the decision to use sway as our compositor? What other options do we have for Wayland?

> Explain more about how to write the plugin backends against the standard protocols first. Does our plan not have us do that?

> I accept your proposed shape. Make it the plan.

> For the compositor-protocol-layer, I see three open decisions. Let's decide those now. Please make recommendations and explain the pros and cons of your proposed action versus other possibilities.

> I agree with all three.

## Decisions and work

Sway remains the selected compositor. The research found no new evidence
against it: Void packages Sway 1.12, which implements `ext-workspace-v1`.
Peer Quickshell shells treat Sway as a secondary target, so Tamlinux builds
its own Sway backend.

The existing plan already preferred standard protocols, but only the Sway
adapter attempted it. A review and a standalone probe (Quickshell 0.3.1 on
Hyprland 0.56.2) found three gaps in that adapter's protocol path: one-time
reads of a lazily evaluated property return no workspaces; workspace-to-output
assignment is discarded; and nothing updates after startup. Hyprland 0.56.2
implements the same standard protocols.

Added [the compositor protocol layer plan](../plans/compositor-protocol-layer.md):
one shared component with bound protocol state; adapters reduced to gap
fillers; shadow comparison on the daily Hyprland desktop, then authoritative
use on Hyprland; the Sway adapter rebuilt on the layer at 0.7.0. It is linked
from the plan index, the Sway plan and the desktop decoupling plan.

Fred then decided the plan's three open questions:
- Shadow mode becomes the step after 0.4.0, with its shared code developed
  alongside 0.4.0.
- Authoritative use on Hyprland requires 14 days without unexplained
  differences, plus specified display, power and hotplug events, each seen
  at least three times.
- Display power stays on compositor IPC until 0.7.0, because existing
  display-fault mitigations depend on Hyprland's own handling.

The same session added, at Fred's acceptance of the research
recommendations:
- A tested route back to plain Arch at gate A, and back to plain Void in the
  1.2 pilot.
- Permanent carriage of `xbps-src` templates under Void's contribution
  policy.
- The pilot's handling of XBPS's lack of transaction hooks.

## Verification

- Wayland protocol support was checked against the installed compositor's
  protocol headers and binary symbols, and with a Wayland client trace.
- Quickshell's behaviour was observed with a standalone probe instance that
  changed nothing on the running desktop.
- Quickshell's `WindowManager` API names were checked against its v0.3.0
  documentation and v0.3.1 source.
- Relative links in the changed plans resolve. No application tests were run.
