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
