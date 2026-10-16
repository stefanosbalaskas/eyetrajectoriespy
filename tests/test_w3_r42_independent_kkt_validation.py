"""R42 independent Gaussian source and frozen complete-stage numerical validation."""
import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r40_fresh_source_nuisance as r40
from scripts import run_w3_r42_independent_kkt_validation as r42


def test_frozen_numerical_design_and_new_primitive_seed():
    assert r42.MASTER_SEED != r40.MASTER_SEED
    assert r42.MASTER_SEED == 202610164242
    assert r42.BLOCKS == 8
    assert r42.PLANNED_CASES == 32
    assert r42.PLANNED_PROFILES == 64
    assert r42.PLANNED_STARTS == 192
    assert r42.PLANNED_FITS == 576
    assert r42.KKT_TOL == r40.PHYSICAL_PROJECTED_KKT_TOL
    assert r42.NLL_TOL == r40.NLL_NEAR_BEST
    assert len(r42.METHODS) == 3
    assert r42.SLOPE_RATIOS == (0., .75)
    assert set(r42.SEED_RATIOS) == {
        "interior", "intercept_near_lower", "trial_near_lower"
    }


def test_new_primitive_blocks_and_genuine_paired_exact_zero_slope():
    positive = r42.independent_source(
        0, "ordinary_dependent", "positive_slope"
    )
    zero = r42.independent_source(
        0, "ordinary_dependent", "zero_slope"
    )
    fresh_block = r42.independent_source(
        1, "ordinary_dependent", "positive_slope"
    )
    old_r40 = r40.independent_source(
        0, "ordinary_dependent", "positive_slope"
    )
    assert not np.array_equal(
        positive[0]["participant_intercept"],
        fresh_block[0]["participant_intercept"],
    )
    assert not np.array_equal(
        positive[0]["participant_intercept"],
        old_r40[0]["participant_intercept"],
    )
    np.testing.assert_array_equal(positive[2], zero[2])
    np.testing.assert_array_equal(positive[3], zero[3])
    for j in range(min(4,len(positive[1].time))):
        who = int(positive[3][j])
        x = float(positive[2][j])
        t = positive[1].time[j]
        expected = (
            r16.SIGMA_RANDOM_SLOPE
            * positive[0]["participant_slope"][who,0,0]
            * x * (1.+.25*t[:,None])
        )
        np.testing.assert_allclose(
            positive[1].values[j]-zero[1].values[j],
            expected,atol=1e-10,rtol=1e-10
        )
    with pytest.raises(ValueError,match="outside frozen"):
        r42.independent_source(8,"ordinary_dependent","zero_slope")


def test_new_source_preparation_and_analytic_objective_contract():
    prepared,ref,points = r42.prepare_case(
        0,"ordinary_dependent","positive_slope"
    )
    assert ref>0 and np.isfinite(ref) and points>0
    assert len(prepared)==r42.PARTICIPANTS
    for start in r42.SEED_RATIOS:
        baseline,_=r42.original_fit(prepared,ref,0.,start)
        assert baseline["algorithm"]==r42.METHODS[0]
        assert baseline["status"] in {"ok","nonconverged","failed"}


def test_preserve_three_stage_slots_after_baseline_refusal():
    info=r42.failed_stage(
        r42.METHODS[1],"baseline_failed_explicit_refusal"
    )
    assert info["status"]=="not_attempted"
    assert info["fit"] is None
    assert info["error"]=="baseline_failed_explicit_refusal"


def test_complete_one_source_case_and_unique_method_identity():
    entry=r42.evaluate(0,"ordinary_dependent","zero_slope")
    assert entry["source_status"]=="ok",entry["source_error"]
    assert len(entry["profiles"])==2
    for profile in entry["profiles"]:
        assert len(profile["starting_configurations"])==3
        for trial in profile["starting_configurations"]:
            assert tuple(z["algorithm"] for z in trial["fits"])==r42.METHODS
            assert len(trial["fits"])==3
    partial=r42.summarize([entry])
    assert partial["recorded_optimizer_stage_records"]==18
    assert partial["missing_source_conditions"]==31
    assert not partial["all_source_conditions_and_stages_recorded"]
    assert all(
        not value for value in partial["preliminary_numerical_gates"].values()
    )
    assert not partial["release_authorized"]


def test_duplicate_source_rows_refused_and_no_statistical_claim():
    entry=r42.evaluate(0,"ordinary_dependent","zero_slope")
    with pytest.raises(ValueError,match="duplicated"):
        r42.summarize([entry,entry])
    r=r42.summarize([entry])
    assert r["no_global_optimizer_certificate"]
    assert r["no_boundary_variance_test_calibration"]
    assert r["no_fitted_covariance_CR2_functional_CI"]
    assert r["no_simultaneous_functional_band_qualification"]
    assert r["new_independent_primitive_blocks"]==8
