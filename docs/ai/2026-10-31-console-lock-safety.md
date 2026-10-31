# Console deployment lock checks and GTK media proof

- **CLI Tool**: Codex CLI (`codex`) `0.166.0`
- **Model**: `gpt-6.1-terra`
- **Transcript**: Retained privately by the author.
- **Prompts** (excerpt):
  > The goal is to produce a quality Tamlinux 0.5.12 candidate I can Test, without spending excessive time and tokens.
  >
  > continue and try to take more and biggers steps this time before stopping for my input
- **Work**: Check all of the user's non-manager login sessions for locks
  before graphical deployment, rollback, shell restart and automatic
  generation recovery; refuse unknown state. Add an opt-in GTK 4 media-query
  proof using both generated Tamarack palettes in one running window.
- **Verification**: 77 deployment tests and three isolated GTK proofs pass.
  The GTK test changes settings inside the application and does not prove
  desktop portal propagation, installed adapter behavior or recovery.

## Follow-up: isolated portal proof

- **Prompt** (excerpt):
  > Continue.
- A separate opt-in proof sets the temporary display, D-Bus environment and
  uniquely named dconf database before starting the session bus. It checks the
  dconf service environment and temporary database, then changes the colour
  preference through the portal and observes the generated dark and light
  foregrounds in one running libadwaita window. The proof passed on GTK 4.24.1.
  All four opt-in GTK rendering/portal proofs and all 77 deployment tests pass.
  It does not establish installed adapter behavior, other controls or recovery.

## Follow-up: GTK surface palette

- **Prompt** (excerpt):
  > continue and try to take more steps before stopping next time.
- The inactive GTK 4 prototype now maps view, headerbar, sidebar, card,
  dialog, popover, overview and thumbnail foreground/background roles to
  generated colours. The private portal proof exercises a running text view
  and suggested/destructive buttons in both variants, checking rendered fills
  and button text. All 43 theme ownership tests and four opt-in GTK probes
  passed. This is not an installed adapter or proof of all application states.

The additional request for tracing individual commands during boot was
deferred to 0.6 under the requested 0.5.12 scope discipline. Normal visible
boot progress and its physical fleet verification remain in 0.5.
