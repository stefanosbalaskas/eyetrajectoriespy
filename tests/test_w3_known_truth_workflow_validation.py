"""Independent W3 analytical oracle and generating truth, two inference units."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from scripts.run_w3_known_truth_workflow_validation import (
    BLOCKS, DESIGNS, ORACLE_TOLERANCE, audit, evaluate, generate_block,
)


@pytest.mark.parametrize("design",DESIGNS)
def test_zero_noise_exact_known_truth_inference_unit(design):
    row=evaluate(0,design,no_noise=True)
    assert row["status"]=="ok",row["exception"]
    assert row["n_inference_units"]==(36 if design=="participant" else 72)
    assert row["max_abs_workflow_oracle_difference"]<=ORACLE_TOLERANCE
    assert row["max_abs_workflow_primitive_difference"]<=ORACLE_TOLERANCE
    assert row["slope_truth_rmse"]<1e-12


@pytest.mark.parametrize("design",DESIGNS)
def test_independent_lstsq_oracle_noisy_case(design):
    row=evaluate(2,design)
    assert row["status"]=="ok",row["exception"]
    assert row["oracle_agreement_met"]
    assert row["known_truth_recovery_target_met"]
    assert row["n_source_curves"]==(108 if design=="participant" else 72)


def test_participant_design_repeats_predictor_but_not_inference_unit():
    gaze,design,truth,oracle=generate_block(0,"participant")
    assert gaze.n_curves==108
    assert gaze.metadata["participant_id"].nunique()==36
    for i in range(36):
        np.testing.assert_array_equal(design.condition.iloc[3*i:3*i+3],
                                      [design.condition.iloc[3*i]]*3)
    assert oracle.shape==truth.shape==(2,31,2)


def test_independence_of_distinct_generating_blocks():
    a,_x,_t,_o=generate_block(0,"curve")
    b,_x,_t,_o=generate_block(1,"curve")
    assert not np.array_equal(a.values,b.values)


def test_audit_preserves_missing_failed_and_nonindependent_cells():
    good=evaluate(0,"curve",no_noise=True)
    output=audit([good],blocks=2)
    assert output["planned_independent_generating_blocks"]==2
    assert output["present_cases"]==1
    assert len(output["missing_cases"])==3
    assert output["simulation_cases_not_independent_blocks"]
    assert output["per_design"]["participant"]["completed"]==0
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good],blocks=1)
    with pytest.raises(ValueError,match="undeclared"):
        audit([dict(good,block=BLOCKS)],blocks=1)


def test_fail_closed_unlisted_block():
    with pytest.raises(ValueError,match="prespecified"):
        generate_block(BLOCKS,"curve")
    with pytest.raises(ValueError,match="prespecified"):
        generate_block(0,"invalid")
