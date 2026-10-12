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
