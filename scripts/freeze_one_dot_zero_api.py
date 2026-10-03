"""Generate and verify the frozen eyetrajectoriespy 1.0 API boundary.

The contract is deliberately conservative: every currently public export remains
public, no deprecation or removal is introduced, and only APIs already labelled
``experimental`` by the post-0.12 audit are excluded from the 1.0 stability
promise. Compatibility routes remain stable public names/signatures while their
backend-specific interpretation stays explicit.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import inspect
import json
from pathlib import Path
import runpy
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "scripts" / "audit_public_api_surface.py"
DEFAULT_CONTRACT = ROOT / "ONE_DOT_ZERO_API_STABILITY.json"
BASELINE_COMMIT = "382c5940e090faf0f74f9bce4e9180a9e14f1eca"

STABLE_POSTURES = {
    "canonical_candidate",
    "supported_candidate",
    "diagnostic_candidate",
    "compatibility",
    "reproducibility",
    "result_object_candidate",
}
NONSTABLE_POSTURES = {"experimental"}


def _audit() -> dict[str, Any]:
    namespace = runpy.run_path(str(AUDIT_SCRIPT))
    return namespace["build_audit"]()


def _digest(payload: Any) -> str:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _signature(value: Any) -> str | None:
    if not callable(value):
        return None
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return None


def _schema_fields(value: Any) -> list[str]:
    if not inspect.isclass(value):
        return []
    if dataclasses.is_dataclass(value):
        return [field.name for field in dataclasses.fields(value)]
    annotations = getattr(value, "__annotations__", None)
    if isinstance(annotations, dict):
        return list(annotations)
    return []


def build_contract() -> dict[str, Any]:
    audit = _audit()
    import eyetrajectoriespy as et

    records_by_name = {record["name"]: record for record in audit["exports"]}
    all_names = sorted(records_by_name)
    stable_names = sorted(
        name
        for name, record in records_by_name.items()
        if record["posture"] in STABLE_POSTURES
    )
    experimental_names = sorted(
        name
        for name, record in records_by_name.items()
        if record["posture"] in NONSTABLE_POSTURES
    )
    compatibility_names = sorted(
        name
        for name, record in records_by_name.items()
        if record["posture"] == "compatibility"
    )

    unclassified = sorted(
        name
        for name, record in records_by_name.items()
        if record["posture"] not in STABLE_POSTURES | NONSTABLE_POSTURES
    )
    if unclassified:
        raise RuntimeError(
            "1.0 API contract contains unclassified postures: "
            + ", ".join(unclassified)
        )
    if set(stable_names) & set(experimental_names):
        raise RuntimeError("stable and experimental API sets overlap")
    if sorted(stable_names + experimental_names) != all_names:
        raise RuntimeError("1.0 API contract does not partition the public namespace")

    stable_records = []
    for name in stable_names:
        record = records_by_name[name]
        value = getattr(et, name)
        stable_records.append(
            {
                "name": name,
                "family": record["family"],
                "posture": record["posture"],
                "signature": _signature(value),
                "schema_fields": _schema_fields(value),
            }
        )

    experimental_records = [
        {
            "name": name,
            "family": records_by_name[name]["family"],
            "posture": records_by_name[name]["posture"],
        }
        for name in experimental_names
    ]

    return {
        "schema_version": 1,
        "contract": "eyetrajectoriespy-1.0-public-api-stability-boundary",
        "baseline_commit": BASELINE_COMMIT,
        "boundary_state": "frozen_candidate_for_1_0",
        "selection_rule": (
            "all public exports in the frozen baseline are stable except APIs "
            "explicitly classified experimental"
        ),
        "semver_policy": {
            "stable_names_signatures_and_result_schema_fields": True,
            "experimental_apis_outside_1_0_compatibility_guarantee": True,
            "compatibility_routes_are_stable_public_names": True,
            "diagnostic_status_does_not_reduce_api_stability": True,
            "no_mass_rename": True,
            "deprecations_authorized": [],
            "removals_authorized": [],
        },
        "counts": {
            "public_exports": len(all_names),
            "stable_exports": len(stable_names),
            "experimental_exports": len(experimental_names),
            "compatibility_exports": len(compatibility_names),
        },
        "all_public_exports": all_names,
        "all_public_exports_sha256": _digest(all_names),
        "stable_exports": stable_records,
        "stable_exports_sha256": _digest(stable_records),
        "experimental_exports": experimental_records,
        "compatibility_exports": compatibility_names,
    }


def _render(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check",
        type=Path,
        nargs="?",
        const=DEFAULT_CONTRACT,
        help="fail unless the frozen contract exactly matches the live public API",
    )
    args = parser.parse_args()

    candidate = build_contract()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(_render(candidate), encoding="utf-8")

    if args.check is not None:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        if expected != candidate:
            raise RuntimeError(
                "frozen 1.0 API contract differs from the live public surface; "
                "regenerate and review ONE_DOT_ZERO_API_STABILITY.json explicitly"
            )

    if args.output is None and args.check is None:
        print(_render(candidate), end="")
        return

    print(
        "1.0 API boundary: "
        f"{candidate['counts']['stable_exports']} stable / "
        f"{candidate['counts']['experimental_exports']} experimental / "
        f"{candidate['counts']['public_exports']} total"
    )


if __name__ == "__main__":
    main()
