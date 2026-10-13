"""R14 numerical-factorial and failure-inclusive independent-source contracts."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from scipy.stats import norm, t

from scripts.run_w3_r13_exact_r11_conditional_oracle import (
    case as r13_case, N_PARTICIPANTS, CONFIDENCE, BLOCKS, MODELS, COHORTS,
)
from scripts.run_w3_r14_variance_reference_factorial import (
    METHODS, CONTRASTS, crossed_case, audit,
)


def original_row(estimate=1.0, truth=1.0, cr1_se=.1, oracle_se=.12):
    tcrit = t.ppf((1 + CONFIDENCE) / 2, N_PARTICIPANTS - 1)
    zcrit = norm.ppf((1 + CONFIDENCE) / 2)
    return {
        "block": 0, "cohort": COHORTS[0], "model": MODELS[0],
        "status": "ok", "known_truth": truth, "estimate": estimate,
        "methods": {
            "participant_cr1_t": {
                "se": cr1_se, "width": 2 * cr1_se * tcrit,
                "known_truth_included": abs(estimate - truth) <= cr1_se * tcrit,
            },
            "conditional_gaussian_oracle_normal": {
                "se": oracle_se, "width": 2 * oracle_se * zcrit,
                "known_truth_included": abs(estimate - truth) <= oracle_se * zcrit,
            },
        },
    }


def test_crossing_preserves_original_diagonal_and_is_independent_numerically():
    original = original_row(estimate=.83)
    result = crossed_case(original)
    assert result["status"] == "ok", result["exception"]
    assert set(result["methods"]) == set(METHODS)
    assert result["original_r13_diagnostic_identity_verified"]
    for m in METHODS:
        s = result["methods"][m]
        assert s["known_truth_included"] == (abs(.83 - 1.0) <= s["width"] / 2)
        assert s["width"] > 0
    assert result["methods"]["cr1_t"]["width"] > result["methods"]["cr1_normal"]["width"]
    assert result["methods"]["oracle_t"]["width"] > result["methods"]["oracle_normal"]["width"]
    assert result["methods"]["oracle_t"]["width"] > result["methods"]["cr1_t"]["width"]
    assert not result["release_authorized"]
    assert json.loads(json.dumps(result))["status"] == "ok"


@pytest.mark.parametrize("breakage", ["bad_width", "bad_decision", "zero_se", "nan_se"])
def test_source_r13_disagreements_preserve_failure(breakage):
    row = original_row()
    if breakage == "bad_width":
        row["methods"]["participant_cr1_t"]["width"] += 1
    elif breakage == "bad_decision":
        row["methods"]["conditional_gaussian_oracle_normal"]["known_truth_included"] = False
    elif breakage == "zero_se":
        row["methods"]["participant_cr1_t"]["se"] = 0
    else:
        row["methods"]["participant_cr1_t"]["se"] = float("nan")
    result = crossed_case(row)
    assert result["status"] == "failed"
    assert result["exception"] is not None
    assert result["methods"] == {}


def test_original_upstream_failure_not_dropped():
    broken = original_row()
    broken["status"] = "failed"
    broken["exception"] = {"type": "IntentionalSourceFailure"}
    result = crossed_case(broken)
    assert result["status"] == "failed"
    assert result["exception"]["type"] == "IntentionalSourceFailure"


def test_audit_does_not_relabel_four_methods_as_four_replicates():
    row = crossed_case(original_row())
    output = audit([row])
    assert output["recorded_cases"] == 1
    assert output["completed_cases"] == 1
    assert output["distinct_independent_source_blocks_across_cohorts"] == BLOCKS * len(COHORTS)
    assert len(output["missing_cases"]) == BLOCKS * len(MODELS) * len(COHORTS) - 1
    assert set(CONTRASTS).issubset(
        output["groups"][COHORTS[0]][MODELS[0]]["paired_within_block_contrasts"]
    )
    assert not output["pointwise_inference_qualified"]
    assert not output["publication_authorized"]
    assert output["no_new_independent_source_replications"]
    with pytest.raises(ValueError, match="duplicate"):
        audit([row, deepcopy(row)])


@pytest.mark.parametrize("model", MODELS)
def test_original_r13_fit_reconstructed_without_changing_any_observation(model):
    original = r13_case(0, "historical_R11", model)
    assert original["status"] == "ok", original.get("exception")
    crossed = crossed_case(original)
    assert crossed["status"] == "ok", crossed.get("exception")
    assert crossed["source_is_existing_r13_not_new_replication"]
    assert crossed["methods"]["cr1_t"]["known_truth_included"] == original[
        "methods"]["participant_cr1_t"]["known_truth_included"]
    assert crossed["methods"]["oracle_normal"]["known_truth_included"] == original[
        "methods"]["conditional_gaussian_oracle_normal"]["known_truth_included"]
    assert np.isclose(crossed["estimate"], original["estimate"])
