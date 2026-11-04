# tam-workstation-upgrade

Upgrade a supported Tamlinux workstation to a **released** assembly from text
login, without keeping component checkouts or promoting stage branches.

Design: [`docs/plans/workstation-upgrade.md`](../../docs/plans/workstation-upgrade.md).

| Invocation | Result |
| --- | --- |
| `tam-workstation-upgrade --check` | Show installed identity, selected release, native stops; change nothing |
| `tam-workstation-upgrade` | Same plan, then ask before applying |
| `tam-workstation-upgrade --version X.Y.Z` | Plan that release |
| `… --version X.Y.Z --revision SHA --yes` | Apply only if the release resolves to SHA |
| `tam-workstation-upgrade --status` | Show the last local receipt (offline) |
| `tam-workstation-upgrade --recover ID` | Recover using `tam-deploy back` for that receipt |

Apply uses `tam-deploy follow <revision>`. Recovery uses `tam-deploy back`.
Unknown or unmet native requirements stop before activation (D156).

```bash
make check
make install PREFIX=$HOME/.local/dev
```
