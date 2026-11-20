# Keep bundle deployment working after profile retirement

- **CLI tool**: Codex 0.169.1
- **Model**: GPT-6.2 Sol (`gpt-6.2-sol`)
- **Transcript**: Retained privately by the author.
- **Prompt**: “Uninstall nix and Home Manager for Tamlinux 0.6.30.”

Codex implemented and tested the bundle deployment change. Bundle receipts
retain their historical generation identity when the Home Manager profile
has been removed. A present profile still has to match the saved identity.
The legacy migration path continues to verify and activate its profile.

Isolated tests with /nix hidden exercised first-account bundle activation,
bundle updates and rollback with a removed profile, and the existing
rollback path while a profile is present.
