# Host-safe fleet workflow

Develop `tam-fleet` and explicit local-host selection in `tam-deploy`.
Private membership, capabilities, hardware pages and observations remain in
consumer repositories. The public tool has no embedded fleet inventory.

Implemented: registration, status, generated index, structural/live checks,
root preview, local capture and success-only reconciliation. Captures cannot
write a neighbor's state, shared root intent or a public registry. An
explicit commit option creates one exact-path commit per owning repository;
it never pushes. Deployment rejects a different registered host's profile.

Verification: 18 fleet regression tests and 47 deployment tests pass, including
cross-host capture, preserved dirty state, rejected symlink writes, failed
reconciliation timestamps, root traversal and exact-path commits.

The small `tam-nut` welcome/inspection helper is assembled into development
live media separately. It performs no disk or installation action.
Physical second-host installation, per-device SSH setup, package delivery,
reconciliation on both hosts and acceptance remain outside source evidence.
No Test, Run or Release is authorized by these checks.

First-install support is developed for 0.5.0: `tam-deploy init` builds and
activates the exact selected consumer generation from a text session, requires
registered local identity and an already promoted assembly, verifies endpoints
and records the absence of a previous generation. It does not enable graphical
login or manufacture a recovery generation. A failed partial activation retains
its attempt record and blocks retries until reviewed. Console-first boot and
optional native feature packages are separate work; no login policy is changed.
