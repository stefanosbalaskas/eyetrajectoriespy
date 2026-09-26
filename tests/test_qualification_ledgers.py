import json
from pathlib import Path

import eyetrajectoriespy as et


ROOT = Path(__file__).resolve().parents[1]


def _all_test_source():
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "tests").glob("test_*.py"))
    )


def test_reference_validation_ledger_has_explicit_evidence_strengths():
    ledger = json.loads(
        (ROOT / "REFERENCE_VALIDATION.json").read_text(encoding="utf-8")
    )
    tolerances = json.loads(
        (ROOT / "VALIDATION_TOLERANCES.json").read_text(encoding="utf-8")
    )

    assert ledger["package_version"] == et.__version__
    assert tolerances["package_version"] == et.__version__
    assert set(ledger["evidence_types"]) == {
        "analytical_truth",
        "independent_implementation_equivalence",
        "simulation_recovery",
    }

    tolerance_ids = {item["id"] for item in tolerances["classes"]}
    test_source = _all_test_source()
    required = {
        "id",
        "method",
        "scientific_quantity",
        "reference_source",
        "reference_type",
        "dataset_problem",
        "expected_result",
        "comparison_metric",
        "tolerance_class",
        "tolerance",
        "platforms",
        "ci_test",
        "status",
        "limitations",
    }

    ids = []
    evidence_seen = set()
    for entry in ledger["entries"]:
        assert required <= set(entry)
        ids.append(entry["id"])
        evidence_seen.add(entry["reference_type"])
        assert entry["reference_type"] in ledger["evidence_types"]
        assert entry["tolerance_class"] in tolerance_ids
        assert entry["status"] == "qualified"
        assert f"def {entry['ci_test']}(" in test_source

    assert len(ids) == len(set(ids))
    assert evidence_seen == set(ledger["evidence_types"])


def test_tolerance_policy_does_not_use_one_universal_threshold():
    data = json.loads(
        (ROOT / "VALIDATION_TOLERANCES.json").read_text(encoding="utf-8")
    )
    classes = {item["id"]: item for item in data["classes"]}

    assert classes["exact_combinatorial"]["default_rtol"] == 0.0
    assert classes["external_backend_equivalence"]["default_rtol"] is None
    assert classes["simulation_recovery"]["default_atol"] is None
    assert "subspaces" in classes["linear_algebra_invariant"]["policy"]


def test_performance_envelope_declares_noncomparative_repeated_workloads():
    ledger = json.loads(
        (ROOT / "PERFORMANCE_ENVELOPE.json").read_text(encoding="utf-8")
    )
    assert ledger["package_version"] == et.__version__
    assert ledger["comparative_benchmark"] is False
    assert ledger["profile"] == "ci-qualification"

    expected_cases = {
        "fpca_bootstrap",
        "mixed_full_refit_bootstrap",
        "nested_mixed_fit",
        "generalized_gee_bootstrap",
        "recurrence_rqa",
        "nonlinear_sensitivity",
    }
    rows = {row["case"]: row for row in ledger["results"]}
    assert set(rows) == expected_cases
    assert all(row["repeats"] >= 3 for row in rows.values())

    if ledger["status"] == "qualified":
        assert ledger["qualification_commit"]
        assert ledger["qualification_run_id"]
        assert ledger["environment"]
        for row in rows.values():
            observed = row["observed"]
            assert observed is not None
            assert observed["runtime_seconds"]["median"] >= 0.0
            assert observed["runtime_seconds"]["q1"] <= observed[
                "runtime_seconds"
            ]["q3"]
            assert observed["peak_memory_mib"]["median"] > 0.0
    else:
        assert ledger["status"] == "pending_ci_measurement"
