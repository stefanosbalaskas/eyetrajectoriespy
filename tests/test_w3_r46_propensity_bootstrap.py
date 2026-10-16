"""Frozen R46 independent Gaussian, MAR observability and bootstrap contracts."""
import copy

import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r45_observed_propensity_pointwise as r45
from scripts import run_w3_r46_propensity_bootstrap as r46


def test_new_primitive_denominator_and_full_bootstrap_failure_slots():
    assert r46.SOURCE_SEED != r45.MASTER_SEED
    assert r46.BLOCKS==32
    assert r46.N_PARTICIPANTS==24
    assert r46.N_SOURCE_VARIANTS==128
    assert r46.N_SOURCE_REGIMES==384
    assert r46.N_INTERVALS==1152
    assert r46.B_REPS==79
    assert r46.N_BOOT_ATTEMPTS==30336
    assert r46.NOMINAL==.90
    assert len(r46.REGIMES)==3
    assert r46.METHODS==(
        "naive_observed_WLS_CR1",
        "fitted_MAR_IPW_fixed_weight_CR1",
        "fitted_MAR_IPW_refit_pairs_bootstrap_percentile",
    )
    assert r46.PROPENSITY_MIN==.05


def test_source_independence_and_actual_exact_zero_slope():
    a=r46.independent_source(0,"ordinary_dependent","positive_slope")
    zero=r46.independent_source(0,"ordinary_dependent","zero_slope")
    second=r46.independent_source(1,"ordinary_dependent","positive_slope")
    previous=r45.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    assert zero[0] is None
    np.testing.assert_array_equal(a[2],zero[2])
    np.testing.assert_array_equal(a[3],zero[3])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        second[0]["participant_intercept"],
    )
    assert not np.array_equal(
        a[0]["participant_intercept"][:24],
        previous[0]["participant_intercept"][:24],
    )
    for j in range(min(4,len(a[1].time))):
        t=a[1].time[j];who=int(a[3][j]);x=float(a[2][j])
        expected=(r16.SIGMA_RANDOM_SLOPE
                  *a[0]["participant_slope"][who,0,0]*x
                  *(1.+.25*t[:,None]))
        np.testing.assert_allclose(
            a[1].values[j]-zero[1].values[j],
            expected,atol=1e-10,rtol=1e-10,
        )
    with pytest.raises(ValueError,match="outside frozen"):
        r46.independent_source(32,"ordinary_dependent","zero_slope")


def test_design_only_masks_and_nonobservable_y_remain_hidden():
    positive=r46.independent_source(0,"ordinary_dependent","positive_slope")
    zero=r46.independent_source(0,"ordinary_dependent","zero_slope")
    p,stats=r46.observation_panel(
        positive,0,"ordinary_dependent",r46.REGIMES[1])
    z,_=r46.observation_panel(
        zero,0,"ordinary_dependent",r46.REGIMES[1])
    assert 0<stats["interior_point_retained_fraction"]<1
    assert stats["retained_participants"]==r46.N_PARTICIPANTS
    for row,other in zip(p,z):
        assert row["observed_indicator"][0]
        assert row["observed_indicator"][-1]
        np.testing.assert_array_equal(
            row["observed_indicator"],other["observed_indicator"])
        assert np.isnan(
            row["observed_gaze_NaN_if_missing"][~row["observed_indicator"]]
        ).all()
        assert np.isfinite(
            row["observed_gaze_NaN_if_missing"][row["observed_indicator"]]
        ).all()


def test_prospective_propensity_model_never_uses_gaze_y():
    original=r46.independent_source(
        0,"ordinary_dependent","positive_slope")
    panel,_=r46.observation_panel(
        original,0,"ordinary_dependent",r46.REGIMES[0])
    theta,diagnostics=r46.fit_propensity(panel)
    clone=copy.deepcopy(panel)
    for trial in clone:
        trial["observed_gaze_NaN_if_missing"][:]=np.nan
    theta2,_=r46.fit_propensity(clone)
    np.testing.assert_allclose(theta,theta2,atol=0,rtol=0)
    assert diagnostics["fitted_propensity_does_not_see_missing_or_observed_gaze"]
    assert len(theta)==3


def test_weak_overlap_has_smaller_true_interior_probability():
    t=np.linspace(0,1,13)
    p_matched=r46.retention_probability(
        t,.5,"matched_observed_design_logit")
    p_weak=r46.retention_probability(
        t,.5,"weak_overlap_observed_design_logit")
    assert np.all(p_weak[1:-1]<p_matched[1:-1])
    assert p_weak[0]==p_weak[-1]==1
    assert p_matched[0]==p_matched[-1]==1
    with pytest.raises(ValueError):
        r46.retention_probability(t,.5,"invalid")


def test_participant_bootstrap_resamples_whole_original_unit():
    original=r46.independent_source(
        0,"ordinary_dependent","zero_slope")
    panel,_=r46.observation_panel(
        original,0,"ordinary_dependent",r46.REGIMES[0])
    ids=np.array(sorted({p["participant"] for p in panel}))
    resampled=r46.bootstrap_once(panel,ids,r46.BOOTSTRAP_SEED)
    assert len({p["participant"] for p in resampled})==24
    # Resampling entire participants changes the trial count if trial counts
    # differ by unit; never impose equal numbers of native trial records.
    selected=np.random.default_rng(r46.BOOTSTRAP_SEED).choice(
        ids,size=len(ids),replace=True)
    for new_who,original_who in enumerate(selected):
        assert sum(p["participant"]==new_who for p in resampled)==sum(
            p["participant"]==int(original_who) for p in panel)
    assert all(np.isnan(p["observed_gaze_NaN_if_missing"][
        ~p["observed_indicator"]]).all() for p in resampled)
    theta,_=r46.fit_propensity(resampled)
    point,meta=r46.focal_wls(resampled,"ipw",theta)
    assert np.isfinite(point)
    assert np.isfinite(meta[-1]["maximum_clipped_inverse_weight"])


def test_simple_cr1_and_full_refit_bootstrap_path_with_observed_only_inputs():
    original=r46.independent_source(
        0,"ordinary_dependent","zero_slope")
    panel,_=r46.observation_panel(
        original,0,"ordinary_dependent",r46.REGIMES[0])
    theta,_=r46.fit_propensity(panel)
    truth=float(r16.truth_coefficients(
        np.array([r46.FOCAL_TIME]))[1][0,0])
    naive=r46.cr1_pointwise(panel,"naive",None,truth)
    fixed=r46.cr1_pointwise(panel,"ipw",theta,truth)
    assert fixed["upper"]>fixed["lower"]
    assert naive["upper"]>naive["lower"]
    assert fixed["estimated_propensity_treated_as_fixed"]
    assert not naive["estimated_propensity_treated_as_fixed"]


def test_negative_refusal_cannot_create_calibrated_coverage_claim():
    row={
        "block":0,"support":"ordinary_dependent",
        "generating_slope_state":"zero_slope",
        "generating_fixed_focal_slope_truth":0.,
        "source_status":"failed","scenarios":[],
    }
    stats=r46.summarize([row])
    assert stats["recorded_source_variant_rows"]==1
    assert stats["recorded_interval_records"]==0
    assert stats["planned_bootstrap_replicate_attempts"]==30336
    assert not stats["complete_failure_inclusive_design"]
    assert stats["not_validated_nominal_90_pointwise_or_simultaneous_coverage"]
    assert not stats["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r46.summarize([row,row])
