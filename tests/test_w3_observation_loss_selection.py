"""W3 R4 explicit observation loss and complete-unit selection integrity tests."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_observation_loss_selection import (
    STUDY, SEED, BLOCKS, DESIGNS, MECHANISMS, GAP, TRIALS, UNITS,
    generate, evaluate, independent_ols, audit, percentile_block_interval,
)


@pytest.mark.parametrize("design",DESIGNS)
def test_mcar_and_latent_loss_are_paired_at_same_complete_source(design):
    a=generate(0,design,"mcar")
    b=generate(0,design,"latent_response_dependent")
    np.testing.assert_array_equal(a[0].values,b[0].values)
    np.testing.assert_array_equal(a[5],b[5])
    np.testing.assert_array_equal(a[4],b[4])
    assert a[0].n_curves == UNITS[design]*TRIALS[design]
    assert len(a[7])==UNITS[design]
    assert a[7].dtype==bool
    assert np.all(a[8]==.35)
    assert not np.all(b[8]==.35)
    assert not np.array_equal(a[8],b[8])


@pytest.mark.parametrize("mechanism",MECHANISMS)
@pytest.mark.parametrize("design",DESIGNS)
def test_mask_is_genuine_native_gap_and_never_truncates_original_source(design,mechanism):
    complete,masked,native,df,truth,X,Y,lost,p=generate(1,design,mechanism)
    assert complete.values.shape==masked.values.shape
    np.testing.assert_array_equal(X[:,1],df.condition.to_numpy()[::TRIALS[design]])
    assert np.isfinite(complete.values).all()
    assert len(native.time)==complete.n_curves
    assert sum(len(t)<len(complete.time) for t in native.time)==sum(lost)
    for i in range(UNITS[design]):
        if lost[i]:
            first=i*TRIALS[design]
            assert np.isnan(masked.values[first,GAP,:]).all()
            assert len(native.time[first])==len(complete.time)-(GAP.stop-GAP.start)
            for j in range(1,TRIALS[design]):
                assert np.isfinite(masked.values[first+j]).all()
        else:
            for j in range(TRIALS[design]):
                assert np.isfinite(masked.values[i*TRIALS[design]+j]).all()


@pytest.mark.parametrize("design",DESIGNS)
@pytest.mark.parametrize("mechanism",MECHANISMS)
def test_actual_full_and_explicit_complete_unit_workflows_match_oracles(design,mechanism):
    row=evaluate(0,design,mechanism)
    assert row["status"]=="ok",row["exception"]
    assert row["missing_grid_rejected"]
    assert row["irregular_grid_rejected"]
    assert row["preflight_retained_all_curves"]
    assert row["preflight_reported_missingness"]
    assert row["no_interpolation_or_automatic_exclusion"]
    assert row["oracle_full_max_error"]<=2e-10
    assert row["oracle_cc_max_error"]<=2e-10
    assert row["n_complete_units"]+row["n_lost_units"]==UNITS[design]
    assert row["n_explicit_retained_curves"]==row["n_complete_units"]*TRIALS[design]
    assert row["missing_data_inference_qualified"] is False
    assert row["release_authorized"] is False


def test_new_generating_blocks_and_invalid_designs_are_rejected():
    a=generate(0,"curve","mcar")
    b=generate(1,"curve","mcar")
    assert not np.array_equal(a[0].values,b[0].values)
    with pytest.raises(ValueError,match="outside"):
        generate(BLOCKS,"curve","mcar")
    with pytest.raises(ValueError,match="unplanned"):
        generate(0,"curve","not-declared")


def test_failed_source_rows_retained_in_attempted_denominators():
    a=evaluate(0,"curve","mcar")
    failed=dict(a,mechanism="latent_response_dependent",status="failed",
                exception={"type":"ControlledResearchFailure"})
    result=audit([a,failed])
    assert result["planned_cases"]==BLOCKS*len(DESIGNS)*len(MECHANISMS)
    assert result["observed_cases"]==2
    assert result["failures"]==1
    assert len(result["missing_cases"])==result["planned_cases"]-2
    assert result["groups"]["curve"]["mcar"]["attempted"]==BLOCKS
    assert result["groups"]["curve"]["mcar"]["completed"]==1
    assert not result["statistical_missingness_correction_qualified"]
    with pytest.raises(ValueError,match="duplicated"):
        audit([a,a])


def test_mc_intervals_sample_independent_blocks_not_curves():
    assert percentile_block_interval([],seed=SEED) is None
    data=[.3,-.1,.5,.2,0.]
    interval=percentile_block_interval(data,seed=17,draws=500)
    assert interval==percentile_block_interval(data,seed=17,draws=500)
    assert interval[0]<=np.mean(data)<=interval[1]


def test_independent_ols_fails_with_small_or_rank_deficient_selected_units():
    Y=np.ones((5,31,2))
    with pytest.raises(ValueError,match="insufficient"):
        independent_ols(np.column_stack([np.ones(5),np.arange(5)]),Y)
    Y2=np.ones((10,31,2))
    with pytest.raises(ValueError,match="rank deficient"):
        independent_ols(np.ones((10,2)),Y2)
