"""R23 observable-only covariance identification: source and failure contracts."""
import numpy as np
import pytest

from scripts import run_w3_r23_estimated_target_identifiability as r23
from scripts import run_w3_r17_fresh_feasibility as source
from scripts import run_w3_r20_estimated_target_pilot as r20
from scripts import run_w3_r16_leverage_covariance_factorial as r16


def test_new_source_seed_nested_participants_and_predeclared_design():
    assert r23.MASTER_SEED not in (r20.MASTER_SEED,source.R17_SEED,r16.SEED)
    assert r23.BLOCKS==12
    assert r23.SIZES==(24,48,96)
    assert r23.PLANNED==576
    a=source.fresh_source(0,"ordinary_independent",n=24,
                          master_seed=r23.MASTER_SEED,
                          n_blocks=r23.BLOCKS,max_n=96)
    b=source.fresh_source(0,"ordinary_independent",n=48,
                          master_seed=r23.MASTER_SEED,
                          n_blocks=r23.BLOCKS,max_n=96)
    for (at,av),(bt,bv) in zip(zip(a[1].time,a[1].values),
                              zip(b[1].time,b[1].values)):
        np.testing.assert_array_equal(at,bt)
        np.testing.assert_array_equal(av,bv)
    assert a[1].provenance["interpolation_performed"] is False
    assert a[1].provenance["fresh_master_seed"]==r23.MASTER_SEED


@pytest.mark.parametrize("n,support,model,family",[
    (24,"ordinary_independent","legendre5","shared_slope"),
    (48,"extreme_dependent","cubic_spline13","predictor_scaled_slope"),
    (96,"ordinary_dependent","legendre5","shared_slope"),
])
def test_feasible_target_identifiability_and_explicit_refusal(n,support,model,family):
    row=r23.evaluate(0,n,support,model,family)
    assert row["source_generated"]
    assert row["generated_truth_passed_to_estimator"] is False
    assert not row["estimated_target_inference_qualified"]
    assert not row["release_authorized"]
    assert row["numerical_cr2_status"] in ("accepted","refused","not_attempted")
    if row["estimator_status"]=="ok":
        assert row["estimated_from_outcomes"]
        assert not row["working_target_is_simulation_oracle"]
        assert not row["covariance_estimation_uncertainty_accounted_for"]
        assert row["component_rank"]<=4
        assert len(row["component_variances"])==4
        assert all(np.isfinite(list(row["component_variances"].values())))
        if row["numerical_cr2_status"]=="accepted":
            assert row["relative_cr2_identity_error"]<=3e-7
            assert row["pointwise_coverage_evaluated"] is False
        else:
            assert row["numerical_error"] is not None
    else:
        assert row["estimator_error"] is not None
        assert row["numerical_cr2_status"]=="not_attempted"


def test_full_ledger_accounting_and_failure_preservation():
    one=r23.evaluate(0,24,"ordinary_independent","legendre5","shared_slope")
    two=dict(one,working_family="predictor_scaled_slope",
             estimator_status="failed",
             numerical_cr2_status="not_attempted",
             estimator_error={"type":"Fixture","message":"retain failure"})
    summary=r23.summarize([one,two])
    assert summary["planned_evaluations"]==576
    assert summary["recorded_evaluations"]==2
    assert summary["missing_evaluations"]==574
    assert summary["estimator_failures"]>=1
    assert summary["pointwise_coverage_evaluated"] is False
    assert not summary["release_authorized"]
    assert not summary["covariance_estimation_uncertainty_qualified"]


def test_wilson_mc_boundaries_not_claimed_as_coverage():
    assert r23.binomial_wilson(0,0) is None
    for success in (0,2,9,12):
        lo,hi=r23.binomial_wilson(success,12)
        assert lo<=success/12<=hi
        assert 0<=lo<=hi<=1
