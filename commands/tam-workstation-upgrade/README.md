# tam-workstation-upgrade

Plan or apply a **released** Tamlinux assembly from text login, without
promoting stage branches. Release discovery needs no component checkouts;
the current forward deployment backend still requires local component clones.
Transaction recovery uses only the local consumer configuration, retained
generation and saved package identities, without network discovery or builds.

Design: [`docs/plans/workstation-upgrade.md`](../../docs/plans/workstation-upgrade.md).

| Invocation | Result |
| --- | --- |
| `tam-workstation-upgrade --check` | Show installed identity, selected release, native stops; change nothing |
| `tam-workstation-upgrade` | Same plan, then ask before applying |
| `tam-workstation-upgrade --version X.Y.Z` | Plan that release |
| `… --version X.Y.Z --revision SHA --yes` | Apply only if the release resolves to SHA |
| `tam-workstation-upgrade --status` | Show the last local receipt (offline) |
| `tam-workstation-upgrade --recover ID` | Recover that transaction to its recorded baseline |

Apply binds `tam-deploy follow` to a unique transaction ID and a digest of the
confirmed assembly, generation, pin and deployment receipt. The backend checks
the digest under its shared deployment lock before and after preparation.
Recovery uses `tam-deploy recover ID`, never the unrelated previous deployment.

A failed upgrade with verified recovery remains an upgrade failure (exit 1),
but its receipt is `recovered` and offline `--status` succeeds. Incomplete
recovery retains both errors and blocks new upgrades, including no-op targets.
A failure before deployment changes nothing and records that recovery is not
needed. Explicit successful `--recover` returns 0 and is repeatable. Old or
foreign receipts without a provable recovery identity require manual review.
Unknown or unmet native requirements stop before activation.

Current and historical receipt files are replaced atomically. If publication
is interrupted between them, disagreement prevents automatic recovery.
Recovery preserves later user edits and reports conflicting original backups;
it never overwrites those edits to make a receipt look complete.

Full input-graph validation, settings-migration checkpoints and native archive
identity verification remain unfinished. Physical VT upgrade and recovery
proof requires eligible released assemblies and separate operator approval.

```bash
make check
make install PREFIX=$HOME/.local/dev
```
