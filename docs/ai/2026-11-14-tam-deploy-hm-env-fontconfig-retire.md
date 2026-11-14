# Retire Home Manager environment and fontconfig links during bundle migration

Fixes `tam-deploy` console Home Manager-to-bundle migration so generated
Home Manager symlinks inside settings directories covered by the format-2 bundle
(`common .config/environment.d/` and `common .config/fontconfig/`) are retired
cleanly and restored intact on Nix return:

- **`HomeLinkMigration.plan` (`commands/tam-deploy/tam-deploy`):** Gives explicit
  `retire` precedence over directory-prefix `copy` matching so listed Home
  Manager files inside a tracked directory are retired instead of copied as
  dangling or store-backed files.
- **`bundle_home_plan` & `activate_bundle` (`commands/tam-deploy/tam-deploy`):**
  Adds `.config/environment.d/10-home-manager.conf`,
  `.config/fontconfig/conf.d/10-hm-fonts.conf`, and
  `.config/fontconfig/conf.d/52-hm-default-fonts.conf` to the retirement set and
  excludes `retire` entries alongside `regenerate` entries when auditing
  settings before migration activation removes those symlinks.
- **`bundle_profile_expression` (`commands/tam-deploy/tam-deploy`):** Disables
  `xdg.configFile."environment.d/10-home-manager.conf".enable` with
  `lib.mkForce false` when retiring `.config/environment.d/10-home-manager.conf`,
  because setting `home.file` alone does not remove XDG config files generated
  via `xdg.configFile`.
- **Regression test (`commands/tam-deploy/tests/bundle_integration.py`):**
  `test_hm_generated_env_and_fontconfig_files_retire_and_restore` verifies that
  all three links plan as `retire`, generate the `xdg.configFile` disable
  override, pass `activate_bundle`, are absent under the bundle, and restore as
  the exact original Home Manager symlinks on `return_bundle_to_nix`.

Verification: 18 real-engine `bundle_integration.py` tests passed in mandatory
PID namespace isolation; 128 `tam-deploy` unit tests passed (`python3 -B -m
unittest discover -s commands/tam-deploy/tests -v`).

- **Date:** 2026-11-14
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.9`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation, documentation and tests.

## Guiding prompts

> check p1-off. path 1
