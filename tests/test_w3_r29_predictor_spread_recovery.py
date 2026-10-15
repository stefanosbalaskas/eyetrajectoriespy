"""R29 counterfactual source reconstruction and paired estimator contracts."""
import numpy as np
import pytest
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r29_predictor_spread_recovery as r29
from scripts import run_w3_r16_leverage_covariance_factorial as r16


@pytest.mark.parametrize("support",r29.SUPPORT)
def test_baseline_rebuild_exact_original_gaze_and_no_interpolation(support):
    source=fresh.fresh_source(
        0,support,n=24,master_seed=r29.SOURCE_SEED,
        n_blocks=r29.BLOCKS,max_n=max(r29.SIZES))
    other=r29.rescaled_source(source,1.)
    assert other[1].provenance["interpolation_performed"] is False
    assert len(other[1].time)==len(source[1].time)
    for before,after in zip(source[1].time,other[1].time):
        np.testing.assert_array_equal(before,after)
    for before,after in zip(source[1].values,other[1].values):
        np.testing.assert_allclose(before,after,rtol=0,atol=4e-15)
    np.testing.assert_array_equal(other[2],source[2])
    np.testing.assert_array_equal(other[3],source[3])
    np.testing.assert_array_equal(other[4],source[4])


@pytest.mark.parametrize("support",r29.SUPPORT)
def test_counterfactual_2x_reuses_primitive_noise_and_changes_matching_mean(support):
    source=fresh.fresh_source(
        0,support,n=24,master_seed=r29.SOURCE_SEED,
        n_blocks=r29.BLOCKS,max_n=max(r29.SIZES))
    double=r29.rescaled_source(source,2.)
    np.testing.assert_allclose(double[2],2*np.asarray(source[2]),rtol=0,atol=1e-14)
    for j,(time,first,second) in enumerate(zip(
            source[1].time,source[1].values,double[1].values)):
        np.testing.assert_array_equal(time,double[1].time[j])
        mu_first=r16.truth_coefficients(time)[0]+source[2][j]*r16.truth_coefficients(time)[1]
        mu_second=r16.truth_coefficients(time)[0]+double[2][j]*r16.truth_coefficients(time)[1]
        if support.endswith("_independent"):
            np.testing.assert_allclose(
                first-mu_first,second-mu_second,rtol=0,atol=1e-13)
        else:
            who=int(source[3][j])
            primitive=(r16.SIGMA_RANDOM_SLOPE*
                source[0]["participant_slope"][who,0,0]*
                source[2][j]*(1+.25*time[:,None]))
            np.testing.assert_allclose(
                (second-mu_second)-(first-mu_first),
                primitive,rtol=0,atol=2e-13)


def test_reject_unregistered_spread():
    source=fresh.fresh_source(
        0,"ordinary_dependent",n=24,master_seed=r29.SOURCE_SEED,
        n_blocks=r29.BLOCKS,max_n=max(r29.SIZES))
    for bad in (0.,-1.,3.,float("nan")):
        with pytest.raises(ValueError,match="multiplier"):
            r29.rescaled_source(source,bad)


def test_observed_only_estimators_and_failure_inclusive_summary():
    assert r29.SOURCE_SEED not in (202610153626,202610152929-1)
    assert r29.PLANNED==192
    out=r29.evaluate(0,24,"ordinary_dependent",2.)
    assert out["source_generated"],out["source_error"]
    assert out["truth_passed_to_estimators"] is False
    assert not out["confidence_interval_coverage_evaluated"]
    for method in r29.METHODS:
        item=out["methods"][method]
        assert item["status"] in ("ok","failed","nonconverged")
        if item["status"]=="ok":
            assert len(item["postfit_relative_error"])==4
            assert len(item["postfit_below_5pct_true"])==4
    s=r29.summarize([out])
    assert s["recorded_cases"]==1
    assert s["missing_cases"]==191
    assert s["independent_generating_blocks"]==12
    assert s["new_observations_are_independent_across_multiplier"] is False
    assert not s["no_method_winner_selected"] is False
    assert not s["release_authorized"]


def test_bootstrap_requires_paired_multiplier_outcomes():
    out=r29.evaluate(0,24,"ordinary_dependent",1.)
    d=r29.bootstrap_block_difference(
        [out],24,"ordinary_dependent","gaussian_reml","participant_slope")
    assert d["paired_blocks"]==0
    assert d["whole_block_bootstrap_95pct"] is None
