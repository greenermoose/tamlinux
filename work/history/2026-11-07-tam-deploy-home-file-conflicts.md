# Session: 2026-11-07 — `tam-deploy` Home-File Conflict Detection, `.pre-<version>` Backups, and Non-Consumer Cleanliness

- **CLI Tool**: Antigravity CLI (`agy`) `1.5.3`
- **Model**: `claude-opus-5.5-high` / `gemini-4-argon-high`
- **Commit**: `03232ff`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > I told codex to package up and test Tamlinux 0.6.15. It just ran out of tokens. Take over from it and get this done.
  >
  > Yes, include these fixes. Regarding tam, no, do not uninstall the development version I'm working on now. What other questions do you have?
  >
  > (Selections approved: Rename the existing file to `<name>.pre-<version>` automatically and list it in the plan; Ignore uncommitted files that the Test build doesn't read and note them in the output; Keep going.)
- **Key Decisions & Implementation Notes**:
  - Added read-only home-file conflict detection (`find_home_file_conflicts` and `tam-deploy conflicts <generation> [--json]`) that walks `generation/home-files` and identifies unmanaged `$HOME` files, directories, and non-Home Manager symlinks (as well as non-directory parent blockers) that activation would overwrite, computing deterministic `<path>.pre-<version>` backup paths (falling back to `.pre-tamlinux` when no version stamp is present).
  - Included the detected `conflicts` list in `tam-deploy preflight <assembly> [--json]` output.
  - Updated `Deployment.activate` to verify that no `<path>.pre-<version>` backup already exists (refusing with `DeploymentError` before mutating anything if one exists), rename conflicting unmanaged files to `<path>.pre-<version>` before running `activate`, pass `HOME_MANAGER_BACKUP_EXT=pre-<version>` in the activation environment, and record `backedUp` in the deployment transaction and state records.
  - Added automatic backup restoration (`restore_home_file_backups`) on direct activation failure, `install` rollback, and `tam-deploy back`.
  - Excluded non-consumer paths outside the Home Manager Nix evaluation inputs from `check_clean` and `preparation_identity`, printing a note to standard error when unrelated paths are uncommitted.
- **Verification**:
  - `make -C commands/tam-deploy check`: 103 unit tests pass (including 6 new tests in `HomeFileConflicts`, `LivePaths`, and `Arguments`).
