"""R47 independent-block 90% pointwise Monte Carlo refusal contracts."""
import copy

import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r46_propensity_bootstrap as r46
from scripts import run_w3_r47_independent_pointwise_audit as r47


def test_fixed_independent_source_denominators_and_new_seed():
    assert r47.SOURCE_SEED != r46.SOURCE_SEED
    assert r47.OBSERVATION_SEED != r46.MASK_SEED
    assert r47.BLOCKS==256
    assert r47.PARTICIPANTS==24
    assert r47.SUPPORT=="ordinary_dependent"
    assert r47.TRUE_SLOPE=="positive_slope"
    assert r47.PLANNED_SOURCE_CASES==256
    assert r47.PLANNED_REGIME_CASES==768
    assert r47.PLANNED_INTERVALS==1792
    assert r47.PLANNED_REPLICATES==40448
    assert r47.BOOT_REPS==79
    assert r47.NOMINAL==.90


def test_original_new_source_independence_and_allowed_size():
    a=r47.generating_source(0)
    b=r47.generating_source(1)
    prev=r46.independent_source(
        0,"ordinary_dependent","positive_slope")
    assert len(np.unique(a[3]))==24
    assert not np.array_equal(
        a[0]["participant_intercept"],
        b[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],
        prev[0]["participant_intercept"])
    with pytest.raises(ValueError,match="outside"):
        r47.generating_source(256)


def test_missing_gaze_values_never_enter_propensity_and_regimes_are_paired():
    source=r47.generating_source(0)
    complete,stats=r47.observed_panel(source,0,"complete")
    matched,mstat=r47.observed_panel(
        source,0,"matched_observed_design_logit")
    weak,wstat=r47.observed_panel(
        source,0,"weak_overlap_observed_design_logit")
    assert stats["native_point_retention_fraction"]==1
    assert wstat["interior_retention_fraction"]<mstat[
        "interior_retention_fraction"]
    assert stats["observed_participants"]==24
    for case in (matched,weak):
        for trial in case:
            r=trial["observed_indicator"]
            assert r[0] and r[-1]
            assert np.isnan(
                trial["observed_gaze_NaN_if_missing"][~r]).all()
            assert np.isfinite(
                trial["observed_gaze_NaN_if_missing"][r]).all()
    theta,_=r46.fit_propensity(matched)
    corrupted=copy.deepcopy(matched)
    for trial in corrupted:
        trial["observed_gaze_NaN_if_missing"][:]=np.nan
    theta2,_=r46.fit_propensity(corrupted)
    np.testing.assert_array_equal(theta,theta2)
    assert np.isfinite(theta).all()


def test_full_participant_refit_matches_explicit_one_replicate():
    source=r47.generating_source(0)
    panel,_=r47.observed_panel(
        source,0,"matched_observed_design_logit")
    ids=np.asarray(sorted({x["participant"] for x in panel}),int)
    val=r47.refit_bootstrap_once(panel,ids,r47.RESAMPLE_SEED)
    refit=r46.bootstrap_once(panel,ids,r47.RESAMPLE_SEED)
    th,_=r46.fit_propensity(refit)
    expected,_=r46.focal_wls(refit,"ipw",th)
    assert val==pytest.approx(expected,abs=0,rel=0)


def test_true_generated_focal_slope_and_independent_MC_Wilson():
    truth=float(
        r16.truth_coefficients(np.array([r47.FOCAL_TIME]))[1][0,0])
    source=r47.generating_source(0)
    panel,_=r47.observed_panel(source,0,"complete")
    fit=r46.cr1_pointwise(panel,"naive",None,truth)
    wrapped=r47.interval_row("complete_WLS_CR1",fit)
    assert wrapped["status"]=="ok"
    assert wrapped["upper"]>wrapped["lower"]
    assert wrapped["not_validated_nominal_coverage"]
    lo,hi=r47.wilson(230,256)
    assert lo<230/256<hi
    assert lo<=.90<=hi
    with pytest.raises(ValueError):
        r47.wilson(257,256)
    with pytest.raises(ValueError):
        r47.wilson(0,0)


def test_incomplete_source_or_failed_bootstrap_cannot_pass():
    bad={"primitive_block":0,"source_status":"failed",
         "source_error":"refusal","regimes":[],"generating_truth":None}
    report=r47.summarize([bad])
    assert report["planned_bootstrap_attempts"]==40448
    assert report["recorded_bootstrap_attempts"]==0
    assert not report["complete_failure_inclusive_source_design"]
    assert report["results"]["complete"][
        "method_results"]["complete_WLS_CR1"][
            "truth_included_all_planned_independent_blocks_denominator"]==256
    assert report["no_fitted_working_covariance_CR2_or_Satterthwaite_inference"]
    assert report["no_simultaneous_whole_function_band"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r47.summarize([bad,bad])


def test_regime_and_method_contract_is_not_selectively_collapsible():
    assert len(r47.METHODS["complete"])==1
    assert len(r47.METHODS["matched_observed_design_logit"])==3
    assert len(r47.METHODS["weak_overlap_observed_design_logit"])==3
    assert r47.METHODS["matched_observed_design_logit"]==(
        r47.METHODS["weak_overlap_observed_design_logit"])
    assert r47.RESAMPLE_SEED not in (
        r47.SOURCE_SEED,r47.OBSERVATION_SEED)
