"""R45 prospective observed-only propensity and interval boundary tests."""
import copy

import numpy as np
import pytest

from scripts import run_w3_r43_missingness_covariance_stress as r43
from scripts import run_w3_r44_response_selection as r44
from scripts import run_w3_r45_observed_propensity_pointwise as r45


def test_full_registered_denominator_and_genuine_new_primitive_source():
    assert r45.MASTER_SEED not in (r43.MASTER_SEED,r44.MASTER_SEED)
    assert r45.BLOCKS==12
    assert r45.SIZES==(24,48)
    assert r45.N_SOURCE==96
    assert r45.N_OBSERVATION==384
    assert r45.N_INTERVALS==576
    assert r45.NOMINAL==.90
    assert r45.METHODS["missing_y_MNAR_point"]==("observed_WLS_CR1",)
    assert r45.METHODS["latent_y_whole_participant_selection"]==(
        "observed_WLS_CR1",)
    assert "fitted_observed_propensity_IPW_CR1" in (
        r45.METHODS["observed_time_x_MAR_point"]
    )


def test_primitive_independence_nested_prefix_and_real_zero_slope():
    a=r45.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    b=r45.gaussian_source(0,48,"ordinary_dependent","positive_slope")
    z=r45.gaussian_source(0,24,"ordinary_dependent","zero_slope")
    second=r45.gaussian_source(1,24,"ordinary_dependent","positive_slope")
    past=r44.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    np.testing.assert_array_equal(
        a[0]["participant_intercept"],
        b[0]["participant_intercept"][:24],
    )
    assert z[0] is None
    assert not np.array_equal(
        a[0]["sensor_noise"],second[0]["sensor_noise"]
    )
    assert not np.array_equal(
        a[0]["sensor_noise"],past[0]["sensor_noise"]
    )
    np.testing.assert_array_equal(a[2],z[2])
    with pytest.raises(ValueError,match="outside frozen"):
        r45.gaussian_source(12,24,"ordinary_dependent","positive_slope")


def test_missing_data_never_leaks_into_observed_panel_and_endpoints_exact():
    original=r45.gaussian_source(
        0,24,"ordinary_dependent","positive_slope"
    )
    for method in ("observed_time_x_MAR_point","missing_y_MNAR_point"):
        panel,stats=r45.observation_panel(
            original,0,"ordinary_dependent",method
        )
        assert stats["retained_participants"]==24
        assert 0<stats["retained_native_point_fraction"]<1.
        for trial in panel:
            mask=trial["retained_indicator"]
            assert mask[0] and mask[-1]
            assert np.isnan(
                trial["observed_y_nan_if_missing"][~mask]
            ).all()
            assert np.isfinite(
                trial["observed_y_nan_if_missing"][mask]
            ).all()
            if method=="missing_y_MNAR_point":
                assert trial["known_design_p_for_benchmark"] is None


def test_fitted_observed_propensity_invariant_to_any_gaze_y():
    original=r45.gaussian_source(
        0,24,"ordinary_dependent","positive_slope"
    )
    panel,_=r45.observation_panel(
        original,0,"ordinary_dependent","observed_time_x_MAR_point"
    )
    theta,diag=r45.fit_observed_logistic_propensity(panel)
    corrupted=copy.deepcopy(panel)
    for trial in corrupted:
        trial["observed_y_nan_if_missing"][:]=np.nan
    theta2,diag2=r45.fit_observed_logistic_propensity(corrupted)
    np.testing.assert_allclose(theta,theta2,atol=0.,rtol=0.)
    assert diag["no_outcome_data_in_propensity_model"]
    assert diag2["no_outcome_data_in_propensity_model"]


def test_three_MAR_methods_and_frozen_focal_truth():
    original=r45.gaussian_source(
        0,24,"ordinary_dependent","zero_slope"
    )
    complete,_=r45.observation_panel(
        original,0,"ordinary_dependent","complete"
    )
    true=float(r45.r16.truth_coefficients(
        np.array([r45.FOCAL_TIME]))[1][0,0])
    full=r45.pointwise_cluster_CR1(
        complete,"observed_WLS_CR1",true,0.
    )["point"]
    mar,_=r45.observation_panel(
        original,0,"ordinary_dependent","observed_time_x_MAR_point"
    )
    for method in r45.METHODS["observed_time_x_MAR_point"]:
        fit=r45.pointwise_cluster_CR1(mar,method,true,full)
        assert fit["status"]=="ok"
        assert fit["upper_90"]>fit["lower_90"]
        assert fit["participant_cluster_df"]==23
        assert fit["CR1_not_CR2"]
        assert fit["nominal_90_not_qualified"]
        assert fit["no_simultaneous_band"]
    with pytest.raises(ValueError,match="unregistered"):
        r45.construct_estimator_rows(mar,"fake_ipw")


def test_unit_selection_excludes_entire_participant_record_not_zero_filling():
    original=r45.gaussian_source(
        0,48,"extreme_dependent","positive_slope"
    )
    panel,stats=r45.observation_panel(
        original,0,"extreme_dependent",
        "latent_y_whole_participant_selection"
    )
    assert stats["excluded_participants"]>0
    assert stats["retained_participants"]<48
    assert len({p["person"] for p in panel})==stats["retained_participants"]
    assert all(t["retained_indicator"].all() for t in panel)
    assert all(np.isfinite(
        t["observed_y_nan_if_missing"]).all() for t in panel)


def test_full_source_one_case_contains_six_interval_slots():
    case=r45.evaluate(0,24,"ordinary_dependent","zero_slope")
    assert case["source_status"]=="ok",case["source_error"]
    assert len(case["observation_cases"])==4
    assert all(z["status"]=="ok" for z in case["observation_cases"])
    assert sum(len(z["interval_results"])
               for z in case["observation_cases"])==6
    report=r45.summarize([case])
    assert report["recorded_pointwise_interval_records"]==6
    assert report["planned_pointwise_interval_records"]==576
    assert not report["complete_original_design_recorded"]
    assert report["no_90_pointwise_coverage_qualification"]
    assert report["no_90_simultaneous_whole_function_band_qualification"]
    assert not report["release_authorized"]


def test_failed_original_sources_cannot_pass_or_silently_drop():
    row={"primitive_block":0,"full_participants":24,
         "support":"ordinary_dependent","true_slope_state":"zero_slope",
         "source_status":"failed","observation_cases":[]}
    report=r45.summarize([row])
    assert report["source_errors"]==1
    assert report["recorded_pointwise_interval_records"]==0
    assert not report["complete_original_design_recorded"]
    assert report["independent_primitive_blocks"]==12
    with pytest.raises(ValueError,match="duplicate"):
        r45.summarize([row,row])
