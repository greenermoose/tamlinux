# Session: 2026-11-09 — Host-independent tam-open text-console image test

- **CLI Tool**: `claude` `2.1.319`
- **Model**: Claude Opus 5.5 (`claude-opus-5-5`)
- **Authorship**: AI-assisted, directed by Fred.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Package up and test Tamlinux 0.6.19

  The Tamlinux 0.6.19 candidate stopped before Test on this test.
- **Key Decisions & Implementation Notes**:
  - `test_image_tty_fails` expected `tam-open` to refuse an image on a text
    console, but kept the host `PATH` after its fake tools. On a host with
    `chafa` installed, `tam-open` correctly ran it and the test failed.
  - The test now runs with only its fake-tool directory on `PATH` (file types
    come from libmagic, not from `PATH`), and also checks the other case: with
    a viewer present, `tam-open` runs it. `tam-open` itself is unchanged.
- **Verification**:
  - `make -C commands/tam-open check`: 18 tests pass with `chafa` installed.
