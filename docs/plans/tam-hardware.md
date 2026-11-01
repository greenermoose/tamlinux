# tam-hardware

Status: implemented on `develop` (awaiting packaged assembly delivery).
Command name is `tam-hardware` (no abbreviation). Implements the product
probe from D209 beside C + `libtam` (D160).

`tam-hardware` is a read-only C probe that reports what this machine can
run: architecture, CPU identity, ISA feature flags, topology, caches, and
unprivileged DMI identity. Agents use it instead of scraping `lscpu` /
`inxi` / `dmidecode`.

## Behaviour

```text
tam-hardware           # short human summary
tam-hardware --json    # schema version 1 document
tam-hardware --version # command semver (also -v)
tam-hardware --help
```

Exit codes: `0` successful report (fields may be partial); `1` usage or
unknown option; `2` architecture cannot be determined.

Sources: `libcpuid` for CPU/ISA/caches; `/sys/class/dmi/id` for
world-readable DMI strings (never serial fields); `uname` for architecture.
No subprocesses, no root, no writes.

Out of scope: disks (`tam-drive-info`), displays (`tam-monitor`), energy
(`tam-meter`).

## Delivery

Lives in `commands/tam-hardware/`. Discovered automatically by
`tamlinux-packages` when its Makefile exists. Links `libtam` and
`libcpuid`. Tests use fixtures (`TAM_HARDWARE_SYSFS_ROOT`,
`TAM_HARDWARE_FIXTURE_CPU`) so checks do not depend on the build host CPU.

## Acceptance

- Human and `--json` forms work without root.
- JSON `schema` is `1`; `features` are sorted lowercase names; no serial
  fields.
- `make -C commands/tam-hardware check` passes offline.
- README names related commands for disks, monitors and energy.
