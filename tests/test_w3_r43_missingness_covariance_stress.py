"""R43 numerical stress contracts: fresh primitive blocks, no disguised MAR/MNAR."""
import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r42_independent_kkt_validation as r42
from scripts import run_w3_r43_missingness_covariance_stress as r43


def test_frozen_full_factorial_is_not_mislabelled_independent():
    assert r43.MASTER_SEED not in (r42.MASTER_SEED,202610164040)
    assert r43.BLOCKS==4
    assert r43.SIZES==(24,48)
    assert r43.PLANNED_SOURCE_CASES==64
    assert r43.PLANNED_FIT_CELLS==256
    assert r43.PLANNED_STAGE_RECORDS==512
    assert r43.STAGES==("original_R40_raw_linear","stricter_LBFGSB_restart")
    assert r43.INITIALIZER=="intercept_near_lower"
    assert r43.SLOPE_RATIOS==(0.,.75)
    assert r43.WORKING==("matched_predictor_scaled","misspecified_shared_slope")
    assert r43.MCAR_INTERIOR_KEEP_PROBABILITY==.70
    assert r43.KKT_TOL==r42.KKT_TOL
    assert r43.NLL_TOL==r42.NLL_TOL


def test_new_primitive_blocks_and_nested_participant_sample():
    p24=r43.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    p48=r43.gaussian_source(0,48,"ordinary_dependent","positive_slope")
    another=r43.gaussian_source(1,24,"ordinary_dependent","positive_slope")
    old=r42.independent_source(0,"ordinary_dependent","positive_slope")
    np.testing.assert_array_equal(
        p24[0]["participant_intercept"][:24],
        p48[0]["participant_intercept"][:24])
    assert not np.array_equal(
        p24[0]["participant_intercept"][:24],
        another[0]["participant_intercept"][:24])
    assert not np.array_equal(
        p24[0]["participant_intercept"][:24],
        old[0]["participant_intercept"][:24])
    with pytest.raises(ValueError):
        r43.gaussian_source(4,24,"ordinary_dependent","positive_slope")


def test_genuine_zero_slope_pairing_and_mask_independence():
    pos=r43.gaussian_source(0,24,"ordinary_dependent","positive_slope")
    zero=r43.gaussian_source(0,24,"ordinary_dependent","zero_slope")
    assert zero[0] is None
    np.testing.assert_array_equal(pos[2],zero[2])
    np.testing.assert_array_equal(pos[3],zero[3])
    m1=r43.retained_indices_for_case(pos,0,"ordinary_dependent")
    m2=r43.retained_indices_for_case(zero,0,"ordinary_dependent")
    assert len(m1)==len(m2)
    for i in range(len(m1)):
        np.testing.assert_array_equal(m1[i],m2[i])
    for c in range(min(4,len(pos[1].time))):
        time=np.asarray(pos[1].time[c])
        who=int(pos[3][c]);x=float(pos[2][c])
        expected=(r16.SIGMA_RANDOM_SLOPE
                  *pos[0]["participant_slope"][who,0,0]*x
                  *(1.+.25*time[:,None]))
        np.testing.assert_allclose(
            pos[1].values[c]-zero[1].values[c],
            expected,atol=1e-10,rtol=1e-10)


def test_dropout_uses_original_native_observed_points_and_no_interpolation():
    data=r43.condition_source(
        0,24,"extreme_dependent","positive_slope",
        "anchored_independent_point_dropout")
    complete=r43.condition_source(
        0,24,"extreme_dependent","positive_slope","complete")
    assert len(data[1].time)==len(complete[1].time)
    assert data[1].provenance["interpolation_performed"] is False
    assert data[1].provenance["response_dependent_loss"] is False
    retained=0;available=0
    for t,v,tall,vall in zip(
        data[1].time,data[1].values,complete[1].time,complete[1].values
    ):
        assert len(t)>=r43.MIN_POINTS_PER_NATIVE_TRIAL
        assert len(t)<=len(tall)
        assert np.all(np.diff(t)>0)
        assert t[0]==tall[0] and t[-1]==tall[-1]
        ix=np.searchsorted(tall,t)
        np.testing.assert_array_equal(tall[ix],t)
        np.testing.assert_array_equal(vall[ix],v)
        retained+=len(t);available+=len(tall)
    assert 0<retained<available


def test_paired_working_covariance_is_distinct_on_observed_design():
    correct,ref1,points1,trials1=r43.prepare_case(
        0,24,"ordinary_dependent","positive_slope",
        "anchored_independent_point_dropout","matched_predictor_scaled")
    wrong,ref2,points2,trials2=r43.prepare_case(
        0,24,"ordinary_dependent","positive_slope",
        "anchored_independent_point_dropout","misspecified_shared_slope")
    assert ref1==pytest.approx(ref2,rel=1e-13)
    assert points1==points2 and trials1==trials2
    assert len(correct)==len(wrong)==24
    assert any(
        not np.allclose(a[2][1],b[2][1])
        for a,b in zip(correct,wrong)
    )


def test_reconstruct_one_small_pair_and_explicit_closed_gates():
    case=r43.source_evaluation(
        0,24,"ordinary_dependent","zero_slope","complete"
    )
    assert case["source_status"]=="ok",case["source_error"]
    assert len(case["model_profiles"])==2
    assert all(len(m["slope_profiles"])==2
               for m in case["model_profiles"])
    assert all(len(p["stage_fits"])==2
               for m in case["model_profiles"] for p in m["slope_profiles"])
    stats=r43.summarize([case])
    assert stats["recorded_source_cases"]==1
    assert stats["missing_source_cases"]==63
    assert stats["recorded_optimizer_stage_records"]==8
    assert not stats["full_design_recorded"]
    assert all(v is False for v in stats["numerical_only_gates"].values())
    assert stats["new_independent_primitive_blocks"]==4
    assert stats["no_response_dependent_loss_sensitivity"]
    assert stats["no_fitted_covariance_CR2_or_simultaneous_band_inference"]
    assert not stats["release_authorized"]


def test_partial_failure_not_promoted():
    row={
        "primitive_block":0,"participants":24,"support":"ordinary_dependent",
        "true_random_slope_state":"zero_slope",
        "observation_process":"complete",
        "source_status":"failed","model_profiles":[],
    }
    s=r43.summarize([row])
    assert s["source_failures"]==1
    assert s["recorded_optimizer_stage_records"]==0
    assert s["numerical_only_gates"][r43.STAGES[1]] is False
    with pytest.raises(ValueError,match="duplicated"):
        r43.summarize([row,row])
