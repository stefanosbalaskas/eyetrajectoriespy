"""Generate the historical 1.0 API boundary and verify 1.x compatibility.

The persisted ``ONE_DOT_ZERO_API_STABILITY.json`` file is immutable historical
1.0 evidence.  During 1.0 stabilization the live public namespace had to match
that boundary exactly.  On the 1.x line the compatibility rule is intentionally
asymmetric: every frozen 1.0 export must remain available, frozen stable
signatures/result-schema fields must remain unchanged, but reviewed additive
1.x exports are allowed without rewriting the historical 1.0 manifest.
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


def _signature_schema_records(
    names: list[str],
    *,
    records_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    import eyetrajectoriespy as et

    records: list[dict[str, Any]] = []
    for name in sorted(names):
        record = records_by_name[name]
        value = getattr(et, name)
        records.append(
            {
                "name": name,
                "family": record["family"],
                "posture": record["posture"],
                "signature": _signature(value),
                "schema_fields": _schema_fields(value),
            }
        )
    return records


def build_contract() -> dict[str, Any]:
    """Build an observational boundary from the current live public surface."""

    audit = _audit()
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

    signature_schema_records = _signature_schema_records(
        stable_names,
        records_by_name=records_by_name,
    )

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
        "stable_exports": stable_names,
        "stable_exports_sha256": _digest(stable_names),
        "stable_signature_schema_sha256": _digest(signature_schema_records),
        "experimental_exports": experimental_names,
        "compatibility_exports": compatibility_names,
        "public_namespace_sha256": _digest(all_names),
    }


def verify_frozen_compatibility(expected: dict[str, Any]) -> dict[str, Any]:
    """Verify that the immutable 1.0 boundary is preserved by the live 1.x API."""

    audit = _audit()
    import eyetrajectoriespy as et

    records_by_name = {record["name"]: record for record in audit["exports"]}
    live_names = list(et.__all__)
    live_set = set(live_names)

    stable_names = sorted(expected["stable_exports"])
    experimental_names = sorted(expected["experimental_exports"])
    compatibility_names = sorted(expected["compatibility_exports"])
    frozen_names = sorted(stable_names + experimental_names)
    frozen_set = set(frozen_names)

    counts = expected["counts"]
    if counts["stable_exports"] != len(stable_names):
        raise RuntimeError("frozen 1.0 stable-export count is internally inconsistent")
    if counts["experimental_exports"] != len(experimental_names):
        raise RuntimeError(
            "frozen 1.0 experimental-export count is internally inconsistent"
        )
    if counts["compatibility_exports"] != len(compatibility_names):
        raise RuntimeError(
            "frozen 1.0 compatibility-export count is internally inconsistent"
        )
    if counts["public_exports"] != len(frozen_names):
        raise RuntimeError("frozen 1.0 public-export count is internally inconsistent")
    if len(frozen_names) != len(frozen_set):
        raise RuntimeError("frozen 1.0 stable/experimental export sets overlap")

    if _digest(stable_names) != expected["stable_exports_sha256"]:
        raise RuntimeError("frozen 1.0 stable-export digest is internally inconsistent")
    if _digest(frozen_names) != expected["public_namespace_sha256"]:
        raise RuntimeError("frozen 1.0 public-namespace digest is internally inconsistent")

    missing = sorted(frozen_set - live_set)
    if missing:
        raise RuntimeError(
            "live 1.x API is missing frozen 1.0 exports: " + ", ".join(missing)
        )

    stable_signature_schema = _signature_schema_records(
        stable_names,
        records_by_name=records_by_name,
    )
    current_digest = _digest(stable_signature_schema)
    if current_digest != expected["stable_signature_schema_sha256"]:
        raise RuntimeError(
            "frozen 1.0 stable signature/result-schema contract drifted; "
            "stable 1.x names, signatures and result fields must remain compatible"
        )

    reclassified_experimental = sorted(
        name
        for name in experimental_names
        if records_by_name[name]["posture"] != "experimental"
    )
    if reclassified_experimental:
        raise RuntimeError(
            "frozen 1.0 experimental classifications changed without explicit review: "
            + ", ".join(reclassified_experimental)
        )

    reclassified_compatibility = sorted(
        name
        for name in compatibility_names
        if records_by_name[name]["posture"] != "compatibility"
    )
    if reclassified_compatibility:
        raise RuntimeError(
            "frozen 1.0 compatibility routes changed classification: "
            + ", ".join(reclassified_compatibility)
        )

    additive = sorted(live_set - frozen_set)
    return {
        "frozen_public_exports": len(frozen_names),
        "live_public_exports": len(live_names),
        "missing_frozen_exports": [],
        "additive_exports": additive,
        "additive_export_count": len(additive),
        "stable_signature_schema_sha256": current_digest,
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
        help=(
            "fail unless the immutable frozen 1.0 boundary remains a compatible "
            "subset of the live 1.x public API"
        ),
    )
    args = parser.parse_args()

    candidate = build_contract()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(_render(candidate), encoding="utf-8")

    compatibility = None
    if args.check is not None:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        compatibility = verify_frozen_compatibility(expected)

    if args.output is None and args.check is None:
        print(_render(candidate), end="")
        return

    if compatibility is not None:
        additions = compatibility["additive_exports"]
        addition_text = ", ".join(additions) if additions else "none"
        print(
            "1.0 frozen compatibility: "
            f"{compatibility['frozen_public_exports']}/"
            f"{compatibility['frozen_public_exports']} frozen exports preserved; "
            f"{compatibility['additive_export_count']} additive live exports "
            f"({addition_text})"
        )
        return

    print(
        "live API observation: "
        f"{candidate['counts']['stable_exports']} stable / "
        f"{candidate['counts']['experimental_exports']} experimental / "
        f"{candidate['counts']['public_exports']} total"
    )


if __name__ == "__main__":
    main()
