"""R33 high-leverage oracle truth, deliberate covariance misspecification and failures."""
import numpy as np
import pytest

from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r33_leverage_misspecified_cr2 as study
from scripts.w3_r20_estimated_working_target import _kernels


@pytest.mark.parametrize("support",[
    "ordinary_independent","extreme_independent",
    "ordinary_dependent","extreme_dependent",
])
def test_independently_rebuilt_original_gaussian_target_matches_R17(support):
    raw=study.original_source(0,24,support)
    X,y,w,g,expected=fresh.prepare(raw,study.BASIS)
    p=study.native_problem(0,24,support)
    np.testing.assert_array_equal(p["X"],X)
    np.testing.assert_array_equal(p["y"],y)
    np.testing.assert_array_equal(p["w"],w)
    np.testing.assert_array_equal(p["groups"],g)
    assert len(expected)==len(p["oracle"])==24
    for a,b in zip(expected,p["oracle"]):
        np.testing.assert_allclose(a,b,atol=1e-12,rtol=2e-12)
    assert p["extreme_predictor_count"]==(2 if support.startswith("extreme") else 0)
    assert np.isfinite(p["truth"])
    assert abs(p["truth"]-p["original_focal_truth"])<.5


@pytest.mark.parametrize("support",["ordinary_independent","extreme_dependent"])
def test_predeclared_wrong_family_is_different_covariance_structure(support):
    p=study.native_problem(0,24,support)
    matched=study.source_working_family(support)
    wrong=next(x for x in study.WORKING_FAMILIES if x!=matched)
    indices=np.flatnonzero(p["groups"]==0)
    true=_kernels(p["time"][indices],p["trial"][indices],p["x"][indices],
                 p["w"][indices],matched)[1]
    incorrect=_kernels(p["time"][indices],p["trial"][indices],p["x"][indices],
                      p["w"][indices],wrong)[1]
    # For x close to one the difference might be small but not identically zero.
    assert not np.allclose(true,incorrect,rtol=1e-8,atol=1e-15)


@pytest.mark.parametrize("support,family",[
    ("extreme_independent","shared_slope"),
    ("extreme_independent","predictor_scaled_slope"),
    ("extreme_dependent","shared_slope"),
])
def test_source_and_failure_inclusive_result_under_high_leverage(support,family):
    result=study.evaluate(0,24,support,family)
    assert result["source_generated"],result["source_failure"]
    assert result["extreme_predictor_count"]==2
    assert result["simulation_truth_not_passed_to_rem_likelihood"]
    assert result["estimated_variances_from_observed_only"]
    assert result["rem_likelihood_status"] in ("ok","failed","nonconverged")
    assert result["targets"]["known_source_covariance"]["status"] in (
        "accepted","refused")
    assert result["targets"]["observed_reml_working_covariance"]["status"] in (
        "accepted","refused","nuisance_estimation_failure")
    assert result["no_statistical_coverage_qualification"]
    assert not result["release_authorized"]
    if result["both_targets_accepted"]:
        pair=result["pair_diagnostics"]
        assert pair["plug_in_to_oracle_cr2_se_ratio"]>0
        assert pair["plug_in_to_oracle_90pct_halfwidth_ratio"]>0


def test_unique_predeclared_matrix_and_no_method_winner():
    assert study.BLOCKS==24
    assert study.SIZES==(24,96)
    assert len(study.SUPPORT)==4
    assert len(study.WORKING_FAMILIES)==2
    assert study.PLANNED==384
    assert study.MASTER_SEED!=202610153232
    assert study.wilson(0,0) is None
    for k in (0,1,12,24):
        lo,hi=study.wilson(k,24)
        assert 0<=lo<=k/24<=hi<=1
    a=study.evaluate(0,24,"ordinary_independent","shared_slope")
    s=study.aggregate([a])
    assert s["recorded_model_source_evaluations"]==1
    assert s["missing_model_source_evaluations"]==383
    assert s["model_families_share_original_response_in_each_source_case"]
    assert s["all_source_outcomes_including_refusals_preserved"]
    assert not s["pointwise_coverage_qualified"]
    assert not s["whole_function_simultaneous_bands_qualified"]
    assert not s["release_authorized"]


def test_reject_undeclared_covariance_family_or_source():
    with pytest.raises(ValueError,match="undeclared"):
        study.evaluate(0,24,"extreme_dependent","true_source_oracle")
    with pytest.raises(ValueError,match="unregistered"):
        study.source_working_family("future_source")
