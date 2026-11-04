"""Compatibility assessment against a release delivery record."""
from __future__ import annotations

from copy import deepcopy

SUPPORTED_SCHEMA = 1


class CompatError(Exception):
    pass


def synthesize(record: dict) -> dict | None:
    """Reviewed adapter for deliveries that carry nativePackage/readiness only."""
    native = record.get("nativePackage")
    readiness = record.get("readiness") or {}
    if not isinstance(native, dict) or not native.get("name") or not native.get("version"):
        return None
    if "sha256" not in native and "archiveSha256" not in native:
        return None
    return {
        "schemaVersion": SUPPORTED_SCHEMA,
        "source": "delivery-nativePackage-adapter",
        "platforms": ["x86_64-linux"],
        "consumerSchema": 1,
        "native": {
            "required": bool(readiness.get("nativeInstallationRequired")),
            "package": {
                "name": native["name"],
                "version": native["version"],
                "sha256": native.get("sha256") or native.get("archiveSha256"),
                "archive": native.get("archive"),
            },
        },
        "migrations": [],
        "privilegedStops": [],
        "notes": list(readiness.get("remaining") or []),
    }


def compatibility_of(record: dict) -> dict | None:
    declared = record.get("compatibility")
    if isinstance(declared, dict):
        if declared.get("schemaVersion") != SUPPORTED_SCHEMA:
            raise CompatError(
                f"unsupported compatibility schemaVersion {declared.get('schemaVersion')!r}"
            )
        return deepcopy(declared)
    return synthesize(record)


def assess(profile: dict, selection: dict) -> dict:
    """Return a plan fragment describing compatibility for this host and release."""
    record = selection["record"]
    try:
        compat = compatibility_of(record)
    except CompatError as exc:
        return {
            "outcome": "blocked_compatibility",
            "reason": str(exc),
            "compatibility": None,
            "native": {"required": True, "satisfied": False, "detail": str(exc)},
            "stops": [str(exc)],
        }
    if compat is None:
        return {
            "outcome": "blocked_unknown_native",
            "reason": "release has no compatibility or native metadata; unknown requirements",
            "compatibility": None,
            "native": {"required": True, "satisfied": False, "detail": "missing metadata"},
            "stops": [
                "Unknown native/boot/login requirements. Review the release and record a "
                "compatibility entry before upgrading."
            ],
        }
    platforms = compat.get("platforms") or []
    if profile["architecture"] not in platforms:
        return {
            "outcome": "blocked_compatibility",
            "reason": f"architecture {profile['architecture']} is not in {platforms}",
            "compatibility": compat,
            "native": {"required": False, "satisfied": True, "detail": "not assessed"},
            "stops": [f"Unsupported architecture {profile['architecture']}"],
        }
    native_spec = (compat.get("native") or {})
    required = bool(native_spec.get("required"))
    expected = native_spec.get("package") or {}
    installed = profile.get("native")
    stops = []
    privileged = list(compat.get("privilegedStops") or [])
    for item in privileged:
        stops.append(f"Privileged step required before activation: {item}")
    if required:
        if not isinstance(expected, dict) or not expected.get("name") or not expected.get("version"):
            return {
                "outcome": "blocked_unknown_native",
                "reason": "native requirement is incomplete",
                "compatibility": compat,
                "native": {"required": True, "satisfied": False, "detail": "incomplete requirement"},
                "stops": ["Native requirement lacks package name/version identity"],
            }
        if not installed or installed.get("name") != expected["name"]:
            detail = "tamlinux-native is not installed"
            stops.append(
                f"Install native package {expected['name']} {expected['version']} "
                f"(sha256 {expected.get('sha256', 'unknown')}) with a recorded rollback point (D156)."
            )
            return {
                "outcome": "blocked_native",
                "reason": detail,
                "compatibility": compat,
                "native": {
                    "required": True,
                    "satisfied": False,
                    "expected": expected,
                    "installed": installed,
                    "detail": detail,
                },
                "stops": stops,
            }
        if installed.get("version") != expected["version"]:
            detail = (
                f"installed {installed['name']} {installed['version']} "
                f"!= required {expected['version']}"
            )
            stops.append(
                f"Replace native package with {expected['name']} {expected['version']} "
                f"(sha256 {expected.get('sha256', 'unknown')}) under D156 before activation."
            )
            return {
                "outcome": "blocked_native",
                "reason": detail,
                "compatibility": compat,
                "native": {
                    "required": True,
                    "satisfied": False,
                    "expected": expected,
                    "installed": installed,
                    "detail": detail,
                },
                "stops": stops,
            }
        # Version identity matches. Archive digest confirmation is a separate
        # reviewed step when the archive is present; version match alone is not
        # treated as full proof for apply when sha256 is declared.
        native_ok = {
            "required": True,
            "satisfied": True,
            "expected": expected,
            "installed": installed,
            "detail": "installed name/version match; confirm archive sha256 at apply time",
            "sha256": expected.get("sha256"),
        }
    else:
        native_ok = {
            "required": False,
            "satisfied": True,
            "detail": "no native package change required",
            "installed": installed,
        }
    if stops:
        return {
            "outcome": "blocked_privileged",
            "reason": "privileged workstation steps remain",
            "compatibility": compat,
            "native": native_ok,
            "stops": stops,
        }
    installed_assembly = profile.get("assembly")
    if installed_assembly and installed_assembly == selection["revision"]:
        return {
            "outcome": "no_change",
            "reason": "exact released assembly is already installed",
            "compatibility": compat,
            "native": native_ok,
            "stops": [],
        }
    return {
        "outcome": "ready",
        "reason": "release is eligible for this host",
        "compatibility": compat,
        "native": native_ok,
        "stops": [],
    }
