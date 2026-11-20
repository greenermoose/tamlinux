# Bug 0001 — Native Qt applications inherit incompatible shell plugin paths

- **Status:** Fix available. Source behavior checks pass; differing-provider installed-app proof remains separate.
- **Severity:** Medium; an affected application aborts before opening its window.
- **Affected:** Application launches from a Qt-based shell when native and shell Qt providers differ and shell-only plugin/import paths are inherited.
- **Fixed:** Environment isolation is present in the product source; see the regression checks below.
- **Next:** Verify a retained native Qt application from the packaged menu with differing Qt providers.

## Reproduce

Use a shell and native Qt application built against differing Qt providers.
Launch the native application from a shell menu that inherits the shell's
QT_PLUGIN_PATH or QML import settings. Compare a terminal launch with a menu
launch. Keep private host captures outside this public record.

## Expected and actual

The native application should use its own Qt integration. In the affected
path it aborts during Qt platform initialization. A native application's
successful startup with the same Qt version on both sides does not prove
the differing-provider case.

## Workaround

Launch through an isolated host environment or outside the shell. Retire the
workaround once the packaged isolation is verified on differing providers.

## Fix and verification

Host launch isolation lives in `desktop/shell/modules/Tam/Commons/Util.qml`.
[Environment regression tests](../desktop/tests/test_launch_environment.py)
execute the host argument/environment behavior and detached child contract.
These pass on 2026-11-11. Source regression success is not physical native-app
acceptance under differing library versions.

## Resolution

Open for the stated installed behavior proof. This software record owns the
source defect; host investigations separately own their recovery and acceptance.
