# 2026-10-28 — system layers account and US resize chords

- **CLI Tool:** Cursor `3.27.22` (from `cursor --version`); earlier draft by Codex CLI `0.165.0` (session version)
- **Model:** Composer (`composer`) for this Cursor handoff; Codex draft used `gpt-6.1-terra`
- **Authorship:** Codex drafted the uncommitted product changes. Fred handed them to Cursor after Codex ran out of tokens. Cursor reviewed, corrected the resize keysyms, and committed.
- **Transcript:** Retained privately by the author.
- **Guiding requests:**

> Codex is out of tokens. Please take these over from codex, review them, improve them if necessary, and commit them.

Earlier Codex prompts that produced the draft (retained privately; summarized here only as context for the handoff): plan and implement Tamlinux 0.5.6 input work; restore opposite window-resize shortcuts on the physical period/> key while keeping Transcode on Super+Ctrl+period; add the short public architecture account for K32.

- **Key decisions & implementation notes:**
  - Product window-resize defaults use US `less` / `greater` keysyms instead of `code:20` / `code:21`, matching the host override’s left half and restoring the missing right half.
  - `SUPER + CTRL + greater` carries large horizontal resize; `SUPER + CTRL + period` stays Transcode (Fred, 2026-10-28).
  - Transcode bind corrected to lowercase `period` (same xkbcommon rule as `comma`).
  - Removed default `SUPER + CTRL + Q` calculator chord (already DONE in the input plan; `XF86Calculator` remains).
  - Added `docs/system-layers.md` for the 0.5 K32 architecture account (Arch / Tamlinux / Blue Sparkler).
- **Verification:**
  - `luac -p` on `tiling.lua` and `utilities.lua`
  - `python3 -m unittest tests.test_keybindings` — 34 tests OK
  - Not live until packaged; host override still supplies only the `less` half
