"""R44 source identity, missing-data semantics and failure-inclusive contracts."""
import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r43_missingness_covariance_stress as r43
from scripts import run_w3_r44_response_selection as r44


def test_frozen_original_design_and_new_source_units():
    assert r44.MASTER_SEED not in (r43.MASTER_SEED,202610164242)
    assert r44.BLOCKS==4
    assert r44.SIZES==(24,48)
    assert len(r44.PROCESSES)==4
    assert r44.N_SOURCE_CELLS==128
    assert r44.N_PROFILE_CELLS==256
    assert r44.N_STAGES==512
    assert r44.STAGES==("original_R40_raw_linear","stricter_LBFGSB_restart")
    assert r44.KKT_TOL==r43.KKT_TOL
    assert r44.SLOPE_RATIOS==(0.,.75)
    assert r44.INITIALIZER=="intercept_near_lower"


def test_new_gaussian_primitives_nested_and_true_zero_not_fake_label():
    positive=r44.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    zero=r44.gaussian_source(0,24,"ordinary_dependent","zero_slope")
    n48=r44.gaussian_source(0,48,"ordinary_dependent","positive_slope")
    other=r44.gaussian_source(1,24,"ordinary_dependent","positive_slope")
    previous=r43.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    assert zero[0] is None
    np.testing.assert_array_equal(positive[2],zero[2])
    np.testing.assert_array_equal(positive[3],zero[3])
    np.testing.assert_array_equal(positive[0]["sensor_noise"][:24],
                                  n48[0]["sensor_noise"][:24])
    assert not np.array_equal(positive[0]["sensor_noise"][:24],
                              other[0]["sensor_noise"][:24])
    assert not np.array_equal(positive[0]["sensor_noise"][:24],
                              previous[0]["sensor_noise"][:24])
    for c in range(min(4,len(positive[1].time))):
        t=positive[1].time[c];who=int(positive[3][c])
        x=float(positive[2][c])
        expected=(r16.SIGMA_RANDOM_SLOPE
                  *positive[0]["participant_slope"][who,0,0]*x
                  *(1.+.25*t[:,None]))
        np.testing.assert_allclose(
            positive[1].values[c]-zero[1].values[c],
            expected,atol=1e-10,rtol=1e-10)
    with pytest.raises(ValueError,match="outside"):
        r44.gaussian_source(4,24,"ordinary_dependent","positive_slope")


def test_complete_trajectories_retain_full_original_cohort():
    source=r44.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    observed,s=r44.apply_observation_process(
        source,0,"ordinary_dependent","complete")
    assert s["original_participants"]==s["retained_participants"]==24
    assert s["excluded_participants"]==0
    assert s["original_native_timepoints"]==s["retained_native_timepoints"]
    assert s["participant_retention_fraction"]==1.
    assert s["point_retention_fraction"]==1.
    assert r44.observed_mean_slope_contrast(observed)==pytest.approx(
        r44.observed_mean_slope_contrast(
            (None,source[1],source[2],source[3],source[4],None)),
        abs=1e-10)


def test_MAR_and_MNAR_pointwise_masks_have_distinct_selection_variables():
    src=r44.gaussian_source(0,24,"extreme_dependent","positive_slope")
    ma,sta=r44.apply_observation_process(
        src,0,"extreme_dependent",
        "predictor_time_conditioned_MAR_point")
    mn,stn=r44.apply_observation_process(
        src,0,"extreme_dependent",
        "unobserved_outcome_dependent_MNAR_point")
    for selected,stats in ((ma,sta),(mn,stn)):
        assert stats["original_participants"]==stats["retained_participants"]==24
        assert stats["retained_native_timepoints"]<stats["original_native_timepoints"]
        assert selected[1].provenance["native_points_only"] is True
        assert selected[1].provenance["interpolation_performed"] is False
        for t,v in zip(selected[1].time,selected[1].values):
            assert len(t)>=r44.MIN_POINTS_PER_RETAINED_TRIAL
            assert np.all(np.diff(t)>0)
    t=np.linspace(0,1,10); y=np.linspace(-2,2,10)
    _,pMAR=r44._point_retention(
        t,y,.2,0,"ordinary_dependent",0,0,
        "predictor_time_conditioned_MAR_point")
    _,pMAR2=r44._point_retention(
        t,y+5,.2,0,"ordinary_dependent",0,0,
        "predictor_time_conditioned_MAR_point")
    _,pMNAR=r44._point_retention(
        t,y,.2,0,"ordinary_dependent",0,0,
        "unobserved_outcome_dependent_MNAR_point")
    _,pMNAR2=r44._point_retention(
        t,y+5,.2,0,"ordinary_dependent",0,0,
        "unobserved_outcome_dependent_MNAR_point")
    np.testing.assert_array_equal(pMAR,pMAR2)
    assert not np.array_equal(pMNAR,pMNAR2)


def test_whole_participant_selection_retains_complete_trials_for_selected():
    src=r44.gaussian_source(0,48,"ordinary_dependent","positive_slope")
    obs,s=r44.apply_observation_process(
        src,0,"ordinary_dependent",
        "latent_outcome_dependent_participant_selection")
    assert 6<=s["retained_participants"]<=48
    assert s["excluded_participants"]>0
    assert s["retained_native_timepoints"]<s["original_native_timepoints"]
    original_people=np.asarray(src[3])
    kept=set(obs[3].tolist())
    # Whole participants, not scattered missing data.
    assert sum(original_people.tolist().count(p) for p in kept)==len(obs[3])
    for who in kept:
        assert sum(obs[3]==who)==sum(original_people==who)
    for person in set(original_people)-kept:
        assert person not in obs[3]
    assert 0<s["selection_probability_min"]<1
    assert 0<s["selection_probability_max"]<1
    assert obs[1].provenance["participant_selection_uses_full_latent_outcome"]


def test_failed_rows_do_not_qualify_inference_or_numerics():
    row={"block":0,"participants_full_cohort":24,
         "support":"ordinary_dependent","true_random_slope_state":"zero_slope",
         "source_status":"failed","observation_processes":[]}
    stats=r44.summarize([row])
    assert stats["recorded_source_variant_rows"]==1
    assert stats["recorded_optimizer_stage_records"]==0
    assert stats["source_or_observation_process_errors"]==1
    assert all(not v for v in stats["preliminary_numerical_only_gates"].values())
    assert stats["new_independent_primitive_blocks"]==4
    assert stats["full_cohort_is_reference_even_when_entire_participant_excluded"]
    assert stats["no_validity_claim_for_MNAR_or_selected_CR2_inference"]
    assert stats["no_90pct_pointwise_or_simultaneous_band_qualification"]
    assert not stats["release_authorized"]
    with pytest.raises(ValueError,match="duplicated"):
        r44.summarize([row,row])


def test_one_complete_r44_source_variant_preserves_every_stage():
    row=r44.evaluate(0,24,"ordinary_dependent","zero_slope")
    assert row["source_status"]=="ok",row["source_error"]
    assert len(row["observation_processes"])==4
    assert all(a["status"]=="ok" for a in row["observation_processes"])
    assert all(len(a["profiles"])==2 for a in row["observation_processes"])
    assert all(len(p["stage_fits"])==2
               for a in row["observation_processes"] for p in a["profiles"])
    original=row["full_cohort_source_full_cohort_slope_estimate"]
    assert original==pytest.approx(
        row["observation_processes"][0]["observed_focal_slope_estimate"])
    assert row["observation_processes"][0][
        "observed_minus_full_cohort_focal_slope"]==pytest.approx(0.,abs=1e-9)
    stats=r44.summarize([row])
    assert stats["recorded_observation_process_rows"]==4
    assert stats["recorded_optimizer_stage_records"]==16
    assert not stats["complete_original_design_including_failures"]
