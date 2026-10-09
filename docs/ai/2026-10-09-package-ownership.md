# 2026-10-09 — Public package-delivery ownership

- **CLI Tool**: Codex CLI `0.162.0` (live checked).
- **Model**: `gpt-6.1-sol`.
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted documentation directed by Fred.
- **Commit**: The ownership-alignment commit carrying this record.

> I have reviewed and approve Tamlinux repository ownership and package plan that is open in micro right now. Read that plan and begin implementing. Go ahead and close the micro window. Ask if you have any questions.

Updated the installation framework to place reusable Nix definitions, native
recipes, and exact delivery assemblies in tamlinux-packages. Product behavior,
defaults, installation/recovery contracts, and integration tests remain here.
The utility, command/guide, and C library source owners remain distinct. Every
installation includes a developer baseline. The engineering acceptance sequence
and unimplemented installer status are preserved.

Verification: scoped documentation diff and provenance reference check. The
separate packaging candidate owns its build and installed-package verification.
