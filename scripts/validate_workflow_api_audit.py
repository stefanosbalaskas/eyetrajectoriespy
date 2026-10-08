"""Validate the frozen candidate workflow API boundary for the 1.2 line."""

from __future__ import annotations

import json
from pathlib import Path

import eyetrajectoriespy as et
import eyetrajectoriespy.workflows as workflows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    audit = json.loads(
        (root / "WORKFLOW_API_AUDIT.json").read_text(encoding="utf-8")
    )

    expected_exports = tuple(audit["exported_symbols"])
    actual_exports = tuple(workflows.__all__)
    if actual_exports != expected_exports:
        raise SystemExit(
            "workflow __all__ drifted from WORKFLOW_API_AUDIT.json\n"
            f"expected={expected_exports!r}\nactual={actual_exports!r}"
        )

    entry_points = tuple(audit["workflow_entry_points"])
    missing = [name for name in entry_points if not hasattr(workflows, name)]
    if missing:
        raise SystemExit(f"missing workflow entry points: {missing}")

    noncallable = [
        name for name in entry_points if not callable(getattr(workflows, name))
    ]
    if noncallable:
        raise SystemExit(f"workflow entry points are not callable: {noncallable}")

    leaked = [name for name in expected_exports if hasattr(et, name)]
    if leaked:
        raise SystemExit(
            "workflow candidate surface leaked into package root: "
            f"{leaked}"
        )

    contracts = tuple(audit["workflow_contracts"])
    if len(contracts) != len(entry_points):
        raise SystemExit(
            "workflow contract count must equal workflow entry-point count"
        )
    if len(set(contracts)) != len(contracts):
        raise SystemExit("workflow contracts must be unique")

    if audit["root_exports_promoted"] is not False:
        raise SystemExit("1.2 workflow audit must keep root promotion disabled")
    if audit["boundary_state"] != "module_scoped_stable_candidate":
        raise SystemExit("unexpected workflow API boundary state")

    print(
        "workflow API audit OK: "
        f"{len(expected_exports)} exports; "
        f"{len(entry_points)} workflow entry points; "
        "module-scoped; root promotion disabled"
    )


if __name__ == "__main__":
    main()
