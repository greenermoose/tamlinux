# Make shared `/var/lib/tamlinux` traversable (`0755`) in `tamlinux.conf`

Changes `/var/lib/tamlinux` in `desktop/native/integration/tamlinux.conf` from
`0700` to `0755` (`d /var/lib/tamlinux 0755 root root -`) so non-root consumers
(such as `tam-deploy status` reading `/var/lib/tamlinux/system` and
`/var/lib/tamlinux/transaction`, and desktop menu checks under
`/var/lib/tamlinux/recovery/`) can traverse the shared parent directory without
elevated privileges. Private native recovery subdirectories
(`/var/lib/tamlinux/browser-recovery`, `network-recovery`, `native-defaults`)
enforce `0o700` on their own directories.

Verification: `desktop/tests/test_product_install.py` and
`desktop/tests/test_native_defaults.py` (`Ran 12 tests in 3.659s`, `OK`).

- **Date:** 2026-11-14
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.9`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted fix and regression test.

## Guiding prompts

> Step 3 follow-ups from slowhp bundle testing
