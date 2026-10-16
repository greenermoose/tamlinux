# 0.4.4e boot handoff preparation

- **Date**: 2026-10-16
- **CLI Tool**: Codex CLI (`codex`) `0.163.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted planning and package identity preparation directed by Fred.
- **Prompts**:
  > Make a step by step work plan for Tamlinux 0.4.4e. Decide when to review and pin the independent boot-hook builds. Think carefully about what you are doing; don't just blindly flail around and be especially careful about asking me to do things that don't make sense.

  > This is good. Work through this list. Let me know what you need from me.

Advance the product identity to e while retaining d's runtime implementation.
Document the boot-provider selection and consumer recovery contract. The
assembly records independently built native providers; machine-specific boot
settings remain consumer-owned. Retain the existing native login artifact when
its implementation is unchanged, rather than rebuilding it solely for metadata.

Provider preparation reviewed the unchanged upstream AUR recipes and final
archive overrides, built both providers in an isolated native Arch guest, and
rehearsed masked replacement, UKI generation, both EFI destinations, snapshot
retention and preserving file restoration. The matching assembly repository
holds the exact recipe/source/archive identities and development evidence.

No host boot mutation or lifecycle promotion is implied by this version change.
Physical boot/update, Windows, fallback and other pre-removal Run observations
remain separate gates.
