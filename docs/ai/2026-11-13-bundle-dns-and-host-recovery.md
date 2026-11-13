# Bundle DNS privilege boundary and host-first native recovery

Completes the remaining bundle runtime audit and host-first native rollback
lookup ahead of workstation bundle rebuilding:

- **`tam-dns` bundle support (`commands/tam-dns/tam-dns`):** `store_copy()`
  now permits the read-only, root-owned `/usr/bin/tam-dns` installed by format-2
  bundles alongside `/nix/store/*` copies when re-executing through `pkexec`,
  and `test_product_install.py` verifies that bundle staging rewrites
  `dns_recovery.py` to `/usr/lib/tamlinux/current/share/tamlinux`.
- **Host-first native rollback lookup (`commands/tam-deploy/tam-deploy`):**
  `bundle_native_recovery()` checks `hosts/<hostname>/bundle-nix-recovery.json`
  first (rejecting symlinks and oversized files without silently falling back)
  before falling back to `system/bundle-nix-recovery.json`, as documented in
  [the bundle delivery integration plan](../plans/bundle-delivery-integration.md).
- **Regression tests:** `bundle_integration.py` covers host-first / system
  fallback native recovery lookup and verifies that derived state files
  (`desktop-current`, `desktop-monitors`) do not block portable UX migration.

Verification: 17 real-engine `bundle_integration.py` tests in mandatory PID
namespace isolation; 128 `tam-deploy` unit tests; 4 `test_product_install.py`
tests; 22 `test_control_helpers.py` tests; 8 `test_dns_recovery.py` tests. No
host packages or system paths were altered.

- **Date:** 2026-11-13
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.8`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation, documentation and tests.

## Guiding prompts

> Plan the next milestone for [redacted: private backlog reference].
>
> yes, tam-deploy should check the hosts first and fall back
>
> Approve. proceed
