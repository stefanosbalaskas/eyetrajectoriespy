"""W3 R7 source-contract tests: participants, not repeated trials, are units."""
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_w3_r7_async_repeated_trials import (
    BLOCKS, N_PARTICIPANTS, MAX_TRIALS, TIME, DIMS,
    TRIAL_SCHEMES, LOSS_MECHANISMS, WEIGHTINGS,
    generate, independent_basis_fit, evaluate, audit, mc_interval,
)


@pytest.mark.parametrize("trial_scheme",TRIAL_SCHEMES)
def test_two_dropout_mechanisms_share_exact_source_trials(trial_scheme):
    a=generate(0,trial_scheme,"mcar")
    b=generate(0,trial_scheme,"latent_response_dependent")
    for p,q in zip(a[0].time,b[0].time):
        np.testing.assert_array_equal(p,q)
    for p,q in zip(a[0].values,b[0].values):
        np.testing.assert_array_equal(p,q)
    np.testing.assert_array_equal(a[4],b[4])
    np.testing.assert_array_equal(a[6],b[6])
    np.testing.assert_array_equal(a[7],b[7])
    np.testing.assert_array_equal(a[8],b[8])
    assert len(set(a[3]))==N_PARTICIPANTS
    if trial_scheme=="balanced3":
        assert (a[4]==MAX_TRIALS).all()
    else:
        assert 1<=int(a[4].min())<int(a[4].max())<=MAX_TRIALS


@pytest.mark.parametrize("trial_scheme",TRIAL_SCHEMES)
@pytest.mark.parametrize("mechanism",LOSS_MECHANISMS)
def test_true_native_times_preserved_without_interpolation(trial_scheme,mechanism):
    full,recorded,cond,participants,k,lost,x,times,y=generate(
        1,trial_scheme,mechanism
    )
    assert len(full.time)==int(k.sum())==len(recorded.time)
    assert len(set(participants))==N_PARTICIPANTS
    seen=0
    for i in range(N_PARTICIPANTS):
        assert np.isfinite(x[i])
        for j in range(int(k[i])):
            original=full.time[seen]
            values=full.values[seen]
            actual=recorded.time[seen]
            np.testing.assert_array_equal(original,times[i,j])
            np.testing.assert_array_equal(values,y[i,j])
            assert np.all(np.diff(actual)>0)
            assert len(actual) in (len(TIME),len(TIME)-8)
            mask=np.isin(original,actual)
            np.testing.assert_array_equal(actual,original[mask])
            np.testing.assert_array_equal(recorded.values[seen],values[mask])
            seen+=1
    assert seen==len(participants)


@pytest.mark.parametrize("trial_scheme",TRIAL_SCHEMES)
@pytest.mark.parametrize("mechanism",LOSS_MECHANISMS)
def test_actual_ols_qr_oracle_and_complete_participant_support(trial_scheme,mechanism):
    result=evaluate(0,trial_scheme,mechanism)
    assert result["status"]=="ok",result["exception"]
    assert result["n_independent_participants"]==N_PARTICIPANTS
    assert result["all_participants_preserved"]
    assert result["native_times_and_values_unchanged"]
    assert result["current_dense_W3_rejected_native"]
    assert result["minimum_trial_count"]>=1
    assert result["maximum_trial_count"]<=3
    assert result["n_observed_native_values"]<=result["n_original_observations"]
    for mode in WEIGHTINGS:
        assert result[f"{mode}_qr_error"]<=2e-8
        assert np.isfinite(result[f"{mode}_slope_rmse"])
    if trial_scheme=="balanced3":
        assert abs(result["trial_slope_rmse"]-result["participant_slope_rmse"])<2e-8
    assert json.loads(json.dumps(result))["status"]=="ok"
    assert not result["hierarchical_inference_qualified"]
    assert not result["release_authorized"]


def test_participant_balanced_weights_not_equivalent_under_unbalanced_trials():
    full,recorded,cond,part,k,*_=generate(0,"unbalanced1to3","mcar")
    a,*_=independent_basis_fit(recorded,cond,part,"sample")
    b,*_=independent_basis_fit(recorded,cond,part,"trial")
    c,*_=independent_basis_fit(recorded,cond,part,"participant")
    assert np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(c).all()
    assert not np.allclose(b,c,atol=1e-12,rtol=0)


def test_original_source_blocks_are_new_and_guarded():
    a=generate(0,"balanced3","mcar")
    b=generate(1,"balanced3","mcar")
    assert not np.array_equal(a[8],b[8])
    with pytest.raises(ValueError,match="outside"):
        generate(BLOCKS,"balanced3","mcar")
    with pytest.raises(ValueError,match="undeclared"):
        generate(0,"balanced3","unlisted")


def test_mc_bootstrap_and_failure_inclusive_ledger_are_block_level():
    x=[.1,-.3,.2,.04]
    assert mc_interval(x,seed=55)==mc_interval(x,seed=55)
    assert mc_interval([],seed=55) is None
    row=evaluate(0,"balanced3","mcar")
    bad=dict(row,mechanism="latent_response_dependent",status="failed",
             exception={"type":"IntentionalResearchFailure"})
    result=audit([row,bad])
    assert result["planned_cases"]==BLOCKS*len(TRIAL_SCHEMES)*len(LOSS_MECHANISMS)
    assert result["completed_cases"]==1
    assert result["failed_cases"]==1
    assert len(result["missing_cases"])==result["planned_cases"]-2
    assert result["groups"]["balanced3"]["mcar"]["attempted"]==BLOCKS
    assert not result["hierarchical_uncertainty_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([row,row])
