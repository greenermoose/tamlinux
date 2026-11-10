# Session: 2026-11-10 — Steady active monitor implementation plan

- **CLI Tool**: Codex CLI (`codex`) `0.167.0`
- **Model**: `gpt-6.1-sol`
- **Authorship**: AI-assisted planning directed and reviewed by Fred.
- **Commit**: The documentation commit introducing this record and the
  [approved plan](../plans/steady-active-monitor.md).
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Prepare the public implementation plan for review before Develop. Cover timestamped, output-specific display diagnostics; keeping the active Dell uninterrupted while side monitors wake; and removing Tamlinux 0.4.x-and-earlier logs after preserving evidence needed for active faults. Use the two recorded incidents as the starting evidence.

  (Excerpt; surrounding private planning references omitted.)

  > Looks good.

- **Decisions**: Distinguish observed HP wake churn from the unproven cause
  of Dell disruption. Require emission-time correlation and output identity
  before attributing DRM errors. Apply the active output's desktop first,
  preserve focus and let the latest request govern side-output repair.
  Preserve active-fault evidence before a separately reviewed cleanup set;
  retain mixed or unknown-version journals. Fred approved the plan and the
  proposed 20-switch physical matrix in Micro before this public commit.
- **Verification**: Rechecked both incidents' shell-journal events and
  inspected workspace/helper and native logger/error paths. Checked local
  Markdown links, whitespace and public/private boundaries. This is a
  documentation-only change; no product tests, live display trial, logging
  change, deployment or log deletion was performed.
