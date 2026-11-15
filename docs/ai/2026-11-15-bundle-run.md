# Bundle Run without Home Manager

- **Tool:** Codex CLI 0.169.0
- **Model:** gpt-6.1-sol
- **Transcript:** Retained privately by the author.
- **Prompt:** “Implement the plan.”

Bundle Run no longer reads a Home Manager generation when updating the bill
of materials. Its generation field is null, consistent with bundle delivery;
Nix promotion retains its generation requirement. A regression fixture makes
any generation lookup fail while checking successful bundle promotion.

No stage move or installation was performed.
