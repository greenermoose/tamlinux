# Recreate pruned empty parent directories on `tam-deploy return-nix`

When transitioning from Home Manager to `tam-bundle`, retiring every managed
Home Manager symlink under a directory such as `~/.local/share/tamlinux`
allows Home Manager activation to prune that now-empty parent directory. During
`tam-deploy return-nix`, `HomeLinkMigration.restore()` previously failed with
`FileNotFoundError` inside `HomeLinkMigration.parent()` while validating the
retired entry's missing directory.

- **`HomeLinkMigration.parent()` (`commands/tam-deploy/tam-deploy`):** Adds
  `create=False` and `allow_missing=False`. Any existing ancestor must still be
  a real non-symlink directory (`stat.S_ISDIR`); when `create=True`, missing
  parent directories are recreated with `0o755` and `fsync`ed cleanly.
- **`HomeLinkMigration.read()` & `restore()` (`commands/tam-deploy/tam-deploy`):**
  Permits missing parent directories for already-applied entries and during
  `restore()` (`allow_missing=True`), and recreates missing parents (`create=True`)
  once the saved `original/` symlink target is verified before renaming it back
  into place.
- **Regression test (`commands/tam-deploy/tests/test_home_migration.py`):**
  `test_return_recreates_pruned_parent_directory_and_refuses_linked_parent`
  proves that pruning `.local/bin` after retirement restores cleanly on
  `restore()`, while replacing that pruned directory with a symlink still refuses
  with `DeploymentError`.

Verification: `python3 -m unittest discover -s commands/tam-deploy/tests -v`
ran 131 tests in 62.308s with zero failures or skips.

- **Date:** 2026-11-14
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.9`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation and tests.

## Guiding prompts

> check
