"""W3 R9 fixed rich-basis cluster uncertainty and source-integrity contracts."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r9_mean_basis_selection_stress import (
    BLOCKS,N,SCHEMES,LOSSES,TRUTHS,MODELS,FOCAL,TIME,KNOTS,N_SPLINE,
    source,basis,fit_model,evaluate,audit,wilson,paired_interval,localized_bump,
)


def test_fixed_basis_specifications_are_real_and_predeclared():
    times=np.array([0,.13,.5,.87,1.])
    assert basis(times,"legendre5").shape==(5,6)
    assert basis(times,"legendre11").shape==(5,12)
    assert basis(times,"cubic_spline13").shape==(5,13)
    assert N_SPLINE==13
    np.testing.assert_allclose(basis(times,"cubic_spline13").sum(axis=1),1,atol=1e-12)
    with pytest.raises(ValueError,match="unplanned"):
        basis(times,"optimized_after_results")


def test_same_independent_sources_across_truths_and_loss():
    a=source(0,"balanced3","mcar","baseline")
    b=source(0,"balanced3","mcar","localized_bump")
    c=source(0,"balanced3","latent_response_dependent","baseline")
    for obj in (b,c):
        np.testing.assert_array_equal(a[2],obj[2])
        np.testing.assert_array_equal(a[3],obj[3])
        np.testing.assert_array_equal(a[4],obj[4])
    # Paired generating truths preserve precisely the same recorded windows.
    for ta,tb in zip(a[0].time,b[0].time):
        np.testing.assert_array_equal(ta,tb)
    # Different recording-loss mechanisms are allowed to mask distinct times.
    # Their genuinely shared source timepoints still have identical values.
    for (ta,va),(tc,vc) in zip(
        zip(a[0].time,a[0].values),zip(c[0].time,c[0].values)
    ):
        common,ia,ic=np.intersect1d(ta,tc,return_indices=True)
        assert len(common)>=15
        np.testing.assert_array_equal(va[ia],vc[ic])
    np.testing.assert_allclose(
        b[5][FOCAL]-a[5][FOCAL],localized_bump(TIME[FOCAL]),atol=1e-14
    )
    assert not np.array_equal(a[0].values[0],b[0].values[0])


@pytest.mark.parametrize("scheme",SCHEMES)
@pytest.mark.parametrize("loss",LOSSES)
@pytest.mark.parametrize("truth_mode",TRUTHS)
def test_original_source_all_model_oracles_and_native_support(scheme,loss,truth_mode):
    row=evaluate(0,scheme,loss,truth_mode)
    assert row["status"]=="ok",row["exception"]
    assert row["n_independent_participants"]==N
    assert row["native_irregular_rejected_by_supported_W3"]
    assert row["all_recorded_source_values_preserved"]
    assert set(row["models"])==set(MODELS)
    assert json.loads(json.dumps(row))["status"]=="ok"
    for name in MODELS:
        m=row["models"][name]
        assert m["qr_error"]<=4e-7
        assert m["cluster_score_error"]<=4e-7
        assert m["width"]>0
        assert m["se"]>0
        assert m["number_points"]==row["n_source_observed_points"]
        assert isinstance(m["true_point_included"],bool)
        assert np.isfinite(m["projection_bias"])
    assert not row["simultaneous_calibration_qualified"]
    assert not row["model_winner_selected"]
    assert not row["release_authorized"]


def test_independent_participant_units_and_different_trial_support():
    source_obj=source(1,"unbalanced1to3","mcar","baseline")
    gaze,mu,x,part,trial,truth,counts=source_obj
    assert len(np.unique(part))==N
    assert int(counts.min())==1
    assert int(counts.max())==3
    assert len(np.unique(trial))==sum(counts)
    assert all(len(t) in (len(TIME),len(TIME)-8) for t in gaze.time)
    model=fit_model(gaze,mu,x,part,trial,"cubic_spline13")
    assert model["number_coefficients"]==26
    assert model["qr_error"]<=4e-7
    assert model["cluster_score_error"]<=4e-7
    assert len(model["slope"])==len(TIME)
    assert len(model["slope_projection"])==len(TIME)


def test_fresh_seed_family_and_input_validation():
    a=source(0,"balanced3","mcar","baseline")
    b=source(1,"balanced3","mcar","baseline")
    assert not np.array_equal(a[2],b[2])
    with pytest.raises(ValueError,match="outside"):
        source(BLOCKS,"balanced3","mcar","baseline")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"balanced3","mcar","added_after_results")
    with pytest.raises(ValueError,match="unplanned"):
        source(0,"unknown","mcar","baseline")


def test_block_level_mc_and_failure_inclusive_denominators():
    values=[.1,-.3,.15,.22]
    assert paired_interval(values,seed=7)==paired_interval(values,seed=7)
    assert paired_interval([],seed=7) is None
    assert wilson(0,0) is None
    assert wilson(0,64)[0]==0
    assert wilson(64,64)[1]==1
    good=evaluate(0,"balanced3","mcar","baseline")
    failed=dict(good,truth_mode="localized_bump",status="failed",
                exception={"type":"ControlledReferenceFailure"})
    result=audit([good,failed])
    assert result["planned_cases"]==BLOCKS*len(SCHEMES)*len(LOSSES)*len(TRUTHS)
    assert result["recorded_cases"]==2
    assert result["completed_cases"]==1 and result["failed_cases"]==1
    assert len(result["missing_cases"])==result["planned_cases"]-2
    assert result["groups"]["balanced3"]["mcar"]["baseline"]["attempted"]==BLOCKS
    assert not result["nominal_simultaneous_functional_inference_qualified"]
    assert not result["selected_optimal_basis"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([good,good])
