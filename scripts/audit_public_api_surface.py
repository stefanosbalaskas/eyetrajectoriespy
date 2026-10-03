"""Generate the post-0.12 public-surface audit used for 1.0 readiness.

The audit is intentionally observational.  It does not rename, deprecate or
remove public APIs.  It inventories the exact installed ``__all__`` surface,
checks the conventions we are already willing to enforce, and assigns a
*review posture* rather than a 1.0 stability guarantee.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import inspect
import json
from pathlib import Path
import runpy
from typing import Any

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "PUBLIC_API_1_0_AUDIT.json"
WORKFLOWS_PATH = ROOT / "CANONICAL_WORKFLOWS.json"
GALLERY_MANIFEST_PATH = ROOT / "scripts" / "docs_gallery_manifest.py"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _workflow_roles(workflows: dict[str, Any]) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = defaultdict(set)
    for workflow in workflows["workflows"]:
        for key, value in workflow.items():
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, str) and item in et.__all__:
                    roles[item].add(key)
    return roles


def _family(name: str, value: Any) -> str:
    if name.startswith("fit_"):
        return "estimator"
    if name.startswith("bootstrap_"):
        return "bootstrap"
    if name.startswith("plot_"):
        return "plot"
    if name.endswith("_frame"):
        return "frame"
    if name.endswith("_reporting_text"):
        return "reporting_text"
    if inspect.isclass(value) and name.endswith("Result"):
        return "result_object"
    if inspect.isclass(value):
        return "public_class"
    if inspect.isfunction(value):
        return "public_function"
    return "public_value"


def _posture(
    name: str,
    value: Any,
    *,
    policy: dict[str, Any],
    roles: dict[str, set[str]],
) -> str:
    overrides = policy["explicit_overrides"]
    for posture in ("compatibility", "experimental", "reproducibility"):
        if name in overrides[posture]:
            return posture

    role_set = roles.get(name, set())
    if "experimental_branches" in role_set:
        return "experimental"
    if "diagnostic_branches" in role_set:
        return "diagnostic_candidate"
    if role_set & {"entry_points", "bootstrap", "reporting", "summaries"}:
        return "canonical_candidate"
    if inspect.isclass(value) and name.endswith("Result"):
        return "result_object_candidate"
    if any(
        token in name
        for token in (
            "diagnostic",
            "sensitivity",
            "recovery",
            "influence",
            "stability",
            "validation",
        )
    ):
        return "diagnostic_candidate"
    return "supported_candidate"


def _identity_alias_groups(public_names: list[str]) -> list[list[str]]:
    by_identity: dict[int, list[str]] = defaultdict(list)
    for name in public_names:
        value = getattr(et, name)
        if inspect.isfunction(value) or inspect.isclass(value):
            by_identity[id(value)].append(name)
    return sorted(
        (sorted(names) for names in by_identity.values() if len(names) > 1),
        key=lambda names: names[0],
    )


def build_audit() -> dict[str, Any]:
    policy = _load_json(POLICY_PATH)
    workflows = _load_json(WORKFLOWS_PATH)
    roles = _workflow_roles(workflows)
    public_names = list(et.__all__)

    if len(public_names) != len(set(public_names)):
        raise RuntimeError("eyetrajectoriespy.__all__ contains duplicate names")

    reporting = [name for name in public_names if "reporting" in name.lower()]
    malformed_reporting = [
        name for name in reporting if not name.endswith("_reporting_text")
    ]
    if malformed_reporting:
        raise RuntimeError(
            "public reporting names must end in _reporting_text: "
            + ", ".join(malformed_reporting)
        )

    frame_like = [name for name in public_names if "_frame" in name]
    malformed_frames = [name for name in frame_like if not name.endswith("_frame")]
    if malformed_frames:
        raise RuntimeError(
            "public frame names must end in _frame: " + ", ".join(malformed_frames)
        )

    explicit = {
        name
        for names in policy["explicit_overrides"].values()
        for name in names
    }
    missing_explicit = sorted(explicit - set(public_names))
    if missing_explicit:
        raise RuntimeError(
            "stale explicit API-audit overrides: " + ", ".join(missing_explicit)
        )

    gallery_globals = runpy.run_path(str(GALLERY_MANIFEST_PATH))
    gallery_plots = set(gallery_globals["GALLERY_PLOTS"])
    public_plots = {
        name
        for name in public_names
        if name.startswith("plot_") and callable(getattr(et, name, None))
    }
    if gallery_plots != public_plots:
        raise RuntimeError(
            "public plotting/gallery contract mismatch: "
            f"missing={sorted(public_plots - gallery_plots)}, "
            f"stale={sorted(gallery_plots - public_plots)}"
        )

    records = []
    for name in public_names:
        value = getattr(et, name)
        records.append(
            {
                "name": name,
                "family": _family(name, value),
                "posture": _posture(
                    name,
                    value,
                    policy=policy,
                    roles=roles,
                ),
                "workflow_roles": sorted(roles.get(name, set())),
            }
        )

    family_counts = Counter(record["family"] for record in records)
    posture_counts = Counter(record["posture"] for record in records)
    return {
        "schema_version": 1,
        "package_version": et.__version__,
        "policy_decision_state": policy["decision_state"],
        "one_dot_zero_commitment": policy["one_dot_zero_commitment"],
        "summary": {
            "public_exports": len(public_names),
            "families": dict(sorted(family_counts.items())),
            "postures": dict(sorted(posture_counts.items())),
            "public_plot_apis": len(public_plots),
            "documented_gallery_plots": len(gallery_plots),
            "identity_alias_groups": _identity_alias_groups(public_names),
            "deprecation_candidates": policy["deprecation_candidates"],
            "removal_candidates": policy["removal_candidates"],
        },
        "exports": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        help="optional JSON output path; otherwise print to stdout",
    )
    args = parser.parse_args()
    audit = build_audit()
    rendered = json.dumps(audit, indent=2, sort_keys=False) + "\n"
    if args.output is None:
        print(rendered, end="")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"public API audit: {audit['summary']['public_exports']} exports; "
        f"{audit['summary']['public_plot_apis']} plots; "
        f"1.0 commitment={audit['one_dot_zero_commitment']}"
    )


if __name__ == "__main__":
    main()
