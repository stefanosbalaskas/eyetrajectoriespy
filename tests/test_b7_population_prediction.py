"""Contract tests for B7/B9 independent-participant posterior predictive draws."""
from __future__ import annotations

import numpy as np
import pytest

from eyetrajectoriespy.bayesian import (
    BayesianPlanarFactorFit, predict_bayesian_planar_new_participant,
)
from eyetrajectoriespy.bayesian.planar_population_prediction import _indices


def _known_draws() -> BayesianPlanarFactorFit:
    """Artificial fixed population draws for an exact correlation test."""
    n_chain,n_draw,g,k=2,800,5,1
    mean=np.zeros((n_chain,n_draw,g,2))
    loading=np.ones((n_chain,n_draw,k,g,2))*.8
    cov=np.zeros((n_chain,n_draw,2*g,2*g))
    shared=np.ones(2*g)*.8
    cov[:]=np.outer(shared,shared)
    scores=np.zeros((n_chain,n_draw,12,k))
    reconstructed=np.zeros((n_chain,n_draw,12,g,2))
    for arr in (mean,loading,cov,scores,reconstructed):
        arr.setflags(write=False)
    grid=np.linspace(0,1,g)
    grid.setflags(write=False)
    return BayesianPlanarFactorFit(
        evaluation_grid=grid,dimensions=("x","y"),
        population_mean_draws=mean,joint_population_covariance_draws=cov,
        loading_function_draws=loading,shared_score_draws=scores,
        reconstructed_latent_draws=reconstructed,
        evidence={"experimental":True},
    )


def test_shared_new_factor_preserves_xy_and_temporal_dependence():
    fit=_known_draws()
    pred=predict_bayesian_planar_new_participant(
        fit,evaluation_indices_x=[0,1,4],evaluation_indices_y=[1,3],
        observation_noise_sd=(.0001,.0001),random_state=77,
    )
    assert pred.observed_draws.shape==(2,800,5)
    assert pred.latent_draws.shape==(2,800,5)
    assert list(pred.row_frame.dimension)==["x","x","x","y","y"]
    assert np.array_equal(pred.row_frame.grid_index.to_numpy(),[0,1,4,1,3])
    samples=pred.observed_draws.reshape(-1,5)
    assert np.corrcoef(samples[:,0],samples[:,4])[0,1]>.99
    assert np.corrcoef(samples[:,0],samples[:,2])[0,1]>.99
    assert pred.evidence["shared_new_subject_scores_across_xy"]
    assert pred.evidence["training_participant_scores_used"] is False
    assert pred.evidence["clock_alignment_or_interpolation"] is False
    assert not pred.evidence["pointwise_predictive_calibration_qualified"]
    assert not pred.evidence["simultaneous_functional_predictive_coverage_qualified"]
    summary=pred.summary_frame()
    assert list(summary.columns)[-1]=="predictive_interval_coverage_qualified"
    assert (summary.predictive_q05 < summary.predictive_q95).all()
    with pytest.raises(ValueError):
        pred.observed_draws[0,0,0]=99


def test_independent_predictor_seed_and_training_score_nonleakage():
    from dataclasses import replace
    fit=_known_draws()
    kwargs=dict(evaluation_indices_x=[0,2],
                evaluation_indices_y=[1],
                observation_noise_sd=(.02,.04),random_state=88)
    original=predict_bayesian_planar_new_participant(fit,**kwargs)
    same=predict_bayesian_planar_new_participant(fit,**kwargs)
    np.testing.assert_array_equal(original.observed_draws,same.observed_draws)
    changed=replace(fit,shared_score_draws=np.ones_like(fit.shared_score_draws)*1000)
    no_leak=predict_bayesian_planar_new_participant(changed,**kwargs)
    np.testing.assert_array_equal(original.observed_draws,no_leak.observed_draws)
    next_seed=predict_bayesian_planar_new_participant(fit,**(kwargs|{"random_state":89}))
    assert not np.array_equal(original.observed_draws,next_seed.observed_draws)


@pytest.mark.parametrize("invalid",[
    [],[0,0],[-1],[5],[1.5],[True],["2"],
])
def test_indices_fail_closed(invalid):
    with pytest.raises(ValueError,match="integer indices"):
        _indices(invalid,5,"grid")


def test_rejects_invalid_noise():
    fit=_known_draws()
    with pytest.raises(ValueError,match="observation_noise_sd"):
        predict_bayesian_planar_new_participant(
            fit,evaluation_indices_x=[1],evaluation_indices_y=[2],
            observation_noise_sd=(0,.1))


def test_new_participant_predictions_from_actual_async_rank_two_fit():
    from test_bayesian_b7_planar_factor import _fixture, _fit
    gaze,grid,_=_fixture(rank=2,n=12,seed=22)
    fit=_fit(gaze,grid,rank=2,seed=22)
    predicted=predict_bayesian_planar_new_participant(
        fit,evaluation_indices_x=[1,8,12],evaluation_indices_y=[5,9,18],
        observation_noise_sd=(.04,.06),random_state=22)
    assert predicted.observed_draws.shape==(2,20,6)
    assert predicted.row_frame.time.is_monotonic_increasing is False
    assert np.isfinite(predicted.observed_draws).all()
    assert predicted.summary_frame().predictive_q05.lt(
        predicted.summary_frame().predictive_q95).all()
