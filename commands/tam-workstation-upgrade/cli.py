#!/usr/bin/env python3
"""Upgrade a Tamlinux workstation to a released assembly from text login.

Does not promote stage branches. Applies through `tam-deploy follow` and
recovers with `tam-deploy recover ID`. Stops before activation when native or other
privileged workstation work remains.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import compat
import host
import receipt
import release


class UpgradeError(Exception):
    pass


OUTCOMES = {
    "no_change": 0,
    "ready": 0,
    "blocked_native": 3,
    "blocked_unknown_native": 3,
    "blocked_compatibility": 3,
    "blocked_privileged": 3,
    "failed": 1,
    "incomplete_recovery": 1,
}


def build_plan(version: None | str = None, revision: None | str = None, fetch=release.get_json) -> dict:
    profile = host.local_profile()
    selection = release.resolve(version, fetch=fetch)
    if revision is not None:
        if not release.REVISION.fullmatch(revision):
            raise UpgradeError("revision must be a full 40-character commit")
        if selection["revision"] != revision:
            raise UpgradeError(
                f"release {selection['version']} resolves to {selection['revision']}, not {revision}"
            )
    assessment = compat.assess(profile, selection)
    return {
        "version": selection["version"],
        "revision": selection["revision"],
        "components": selection["components"],
        "profile": {
            "hostname": profile["hostname"],
            "username": profile["username"],
            "architecture": profile["architecture"],
            "assembly": profile.get("assembly"),
            "generation": profile.get("generation"),
            "deployStage": profile.get("deployStage"),
            "native": profile.get("native"),
            "baselineToken": profile.get("baselineToken"),
            "config": profile.get("config"),
        },
        "outcome": assessment["outcome"],
        "reason": assessment["reason"],
        "native": assessment["native"],
        "stops": assessment["stops"],
        "compatibility": assessment.get("compatibility"),
    }


def format_plan(plan: dict) -> str:
    lines = [
        f"Release: {plan['version']} ({plan['revision']})",
        f"Host: {plan['profile']['username']}@{plan['profile']['hostname']} ({plan['profile']['architecture']})",
        f"Installed assembly: {plan['profile'].get('assembly') or 'unknown'}",
        f"Installed generation: {plan['profile'].get('generation') or 'unknown'}",
        f"Installed native: {format_native(plan['profile'].get('native'))}",
        f"Outcome: {plan['outcome']}",
        f"Reason: {plan['reason']}",
    ]
    if plan.get("stops"):
        lines.append("Stops:")
        lines.extend(f"  - {stop}" for stop in plan["stops"])
    return "\n".join(lines) + "\n"


def format_native(value) -> str:
    if not value:
        return "none"
    return f"{value.get('name')} {value.get('version')}"


def confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        raise UpgradeError("refusing interactive confirmation without a terminal")
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def run_deploy(*args: str) -> None:
    binary = shutil.which("tam-deploy")
    if not binary:
        raise UpgradeError("tam-deploy is not on PATH")
    result = subprocess.run([binary, *args], text=True)
    if result.returncode != 0:
        raise UpgradeError(f"tam-deploy {' '.join(args)} failed with exit {result.returncode}")


def backend_transaction_digest(store: receipt.Store) -> str | None:
    path = store.root.parent / "deploy-transaction.json"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def require_idle(store: receipt.Store) -> None:
    current = store.read_current()
    if current and not (
        current.get("phase") in ("complete", "recovered")
        or (current.get("phase") == "failed" and current.get("recoveryRequired") is False)
    ):
        raise UpgradeError(
            f"incomplete upgrade receipt {current['id']} phase={current['phase']}; "
            f"recover with tam-workstation-upgrade --recover {current['id']}"
        )


def verify_baseline(data: dict) -> None:
    actual = host.local_profile()
    if (actual.get("assembly") != data["baselineAssembly"]
            or actual.get("generation") != data["baselineGeneration"]):
        raise UpgradeError("recovery did not restore the recorded baseline assembly and generation")


def apply_plan(plan: dict, *, yes: bool, store: receipt.Store) -> dict:
    require_idle(store)
    if plan["outcome"] == "no_change":
        return plan
    if plan["outcome"] != "ready":
        raise UpgradeError(plan["reason"] + ("\n" + "\n".join(plan["stops"]) if plan["stops"] else ""))
    selected = plan["profile"]
    if not selected.get("baselineToken"):
        raise UpgradeError("cannot apply without an identifiable baseline; inspect deployment status")
    print(format_plan(plan), end="")
    if not yes and not confirm("Apply this released upgrade? [y/N] "):
        raise UpgradeError("upgrade cancelled")
    actual = host.local_profile()
    if (actual.get("baselineToken") != selected["baselineToken"]
            or any(actual.get(k) != selected.get(k) for k in ("hostname", "username", "architecture", "config", "native"))):
        raise UpgradeError("local starting state changed after planning; plan again")
    receipt_id = store.new_id()
    body = {
        "id": receipt_id,
        "phase": "confirmed",
        "version": plan["version"],
        "revision": plan["revision"],
        "baselineAssembly": selected.get("assembly"),
        "baselineGeneration": selected.get("generation"),
        "baselineToken": selected["baselineToken"],
        "backendTransactionDigest": backend_transaction_digest(store),
        "profile": selected["hostname"],
        "username": selected["username"],
        "architecture": selected["architecture"],
        "config": selected.get("config"),
        "recoveryRequired": True,
    }
    store.write(body)
    try:
        store.write({**body, "phase": "applying"})
        run_deploy("follow", plan["revision"], "--transaction", receipt_id,
                   "--expect-baseline", selected["baselineToken"])
        store.write({**body, "phase": "verifying"})
        after = host.local_profile()
        if after.get("assembly") != plan["revision"] or not after.get("generation"):
            raise UpgradeError("installed assembly or generation does not match the selected release")
        store.write({**body, "phase": "complete", "generation": after["generation"], "recoveryRequired": False})
        return {**plan, "outcome": "complete", "receipt": receipt_id}
    except Exception as exc:
        # A refusal/build failure before the backend prepared a transaction must
        # never roll an existing deployment back. A changed backend record, even
        # at the same generation, cannot be adopted as our own transaction.
        try:
            unchanged = (backend_transaction_digest(store) == body["backendTransactionDigest"]
                         and host.local_profile().get("baselineToken") == body["baselineToken"])
        except (OSError, ValueError, host.HostError):
            unchanged = False
        if unchanged:
            store.write({**body, "phase": "failed", "error": str(exc), "recoveryRequired": False})
            raise UpgradeError(f"upgrade failed before deployment; baseline unchanged: {exc}") from exc
        store.write({**body, "phase": "recovering", "error": str(exc)})
        try:
            run_deploy("recover", receipt_id)
            verify_baseline(body)
        except Exception as recovery:
            store.write({**body, "phase": "failed", "error": str(exc), "recoveryError": str(recovery)})
            raise UpgradeError(
                f"upgrade failed ({exc}); recovery incomplete ({recovery}). "
                f"Receipt {receipt_id} retained under {store.history}"
            ) from recovery
        store.write({**body, "phase": "recovered", "error": str(exc), "recoveryRequired": False})
        # This belongs outside the recovery try: a failed upgrade is still a
        # failure, but it must not be caught as a failed recovery.
        raise UpgradeError(f"upgrade failed and recovered: {exc}") from exc


def recover(transaction: str, *, yes: bool, store: receipt.Store) -> None:
    if not receipt.IDENTIFIER.fullmatch(transaction):
        raise UpgradeError("invalid recovery transaction ID")
    current = store.read_current()
    if current is None or current["id"] != transaction:
        raise UpgradeError("stale recovery receipt; nothing changed")
    if current.get("phase") in ("complete", "recovered") or current.get("recoveryRequired") is False:
        print(f"Receipt {transaction} needs no recovery (phase={current['phase']}).")
        return
    path = store.history / f"{transaction}.json"
    data = json.loads(path.read_text())
    if data != current:
        raise UpgradeError("current and historical receipts disagree; inspect before recovery")
    actual = host.local_profile()
    if (not data.get("baselineToken") or any(data.get(k) != actual.get(v) for k, v in (
            ("profile", "hostname"), ("username", "username"), ("architecture", "architecture"), ("config", "config")))):
        raise UpgradeError("legacy or foreign receipt has no safe recovery identity; inspect manually")
    print(json.dumps(data, indent=2))
    if not yes and not confirm(f"Recover transaction {transaction} to its recorded baseline? [y/N] "):
        raise UpgradeError("recovery cancelled")
    store.write({**data, "phase": "recovering"})
    try:
        run_deploy("recover", transaction)
        verify_baseline(data)
    except Exception as exc:
        store.write({**data, "phase": "failed", "recoveryError": str(exc), "recoveryRequired": True})
        raise UpgradeError(f"recovery incomplete: {exc}") from exc
    store.write({**data, "phase": "recovered", "recoveryRequired": False})
    print(f"Recovered receipt {transaction}; verified its recorded baseline.")


def status(store: receipt.Store) -> int:
    current = store.read_current()
    if current is None:
        print("No local workstation-upgrade receipt.")
        return 0
    print(json.dumps(current, indent=2, sort_keys=True))
    phase = current.get("phase")
    if phase not in ("complete", "recovered") and current.get("recoveryRequired") is not False:
        print(
            f"Recovery may be needed: tam-workstation-upgrade --recover {current['id']}",
            file=sys.stderr,
        )
        return OUTCOMES["incomplete_recovery"]
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tam-workstation-upgrade",
        description="Plan or apply a released Tamlinux workstation upgrade from text login.",
    )
    parser.add_argument("--check", action="store_true", help="show plan only; change nothing")
    parser.add_argument("--status", action="store_true", help="show last local receipt; offline")
    parser.add_argument("--recover", metavar="TRANSACTION", help="recover using a retained receipt")
    parser.add_argument("--version", dest="release", metavar="X.Y.Z", help="select that release")
    parser.add_argument("--revision", metavar="SHA", help="require the release resolves to SHA")
    parser.add_argument("--yes", action="store_true", help="apply or recover without asking")
    parser.add_argument("--json", action="store_true", help="print machine-readable plan/status")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    store = receipt.Store()
    try:
        if args.status:
            if args.check or args.recover or args.release or args.revision:
                raise UpgradeError("--status cannot combine with plan/apply options")
            return status(store)
        if args.recover:
            with store:
                recover(args.recover, yes=args.yes, store=store)
            return 0
        if args.check:
            plan = build_plan(args.release, args.revision)
            if args.json:
                print(json.dumps(plan, indent=2, sort_keys=True))
            else:
                print(format_plan(plan), end="")
            return OUTCOMES.get(plan["outcome"], 1)
        with store:
            require_idle(store)
            plan = build_plan(args.release, args.revision)
            result = apply_plan(plan, yes=args.yes, store=store)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif result.get("outcome") == "no_change":
            print(format_plan(result), end="")
            print("No change.")
        elif result.get("outcome") == "complete":
            print(f"Upgrade complete. Receipt {result.get('receipt')}.")
        return 0 if result.get("outcome") in ("complete", "no_change", "ready") else OUTCOMES.get(result.get("outcome"), 1)
    except (UpgradeError, host.HostError, release.ReleaseError, receipt.ReceiptError, compat.CompatError, OSError, ValueError, KeyError) as exc:
        print(f"tam-workstation-upgrade: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
