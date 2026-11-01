# tam-hardware

Read-only probe for host architecture, CPU identity, ISA feature flags,
caches and unprivileged DMI identity. Implemented in C with `libtam` and
`libcpuid`. No root and no subprocesses.

```sh
tam-hardware           # human summary
tam-hardware --json    # schema version 1 for agents
tam-hardware --version # command semver (also -v)
tam-hardware --help
```

Command version is `TAM_HARDWARE_VERSION` in `version.h` (currently 0.1.0).

Related commands elsewhere: disks → `tam-drive-info`; displays →
`tam-monitor`; energy → future `tam-meter`.

Tests may set `TAM_HARDWARE_SYSFS_ROOT` (fake DMI tree) and
`TAM_HARDWARE_FIXTURE_CPU` (key=value CPU fixture file).
