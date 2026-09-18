import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    cluster_fpca_scores, fit_mfpca, fit_multilevel_fpca,
    fit_scalar_on_function_regression, functional_l2_distance,
    nearest_trajectory_indices, pairwise_functional_distances,
    score_distance_matrix, simulate_planar_trajectories,
)

def test_multilevel_scores_match_levels():
    x=simulate_planar_trajectories(n_participants=7,trials_per_participant=4,n_time=51)
    ml=fit_multilevel_fpca(x,participant_column="participant_id",participant_components=.9,trial_components=.9,scaling="dimension_sd")
    assert len(ml.participant_scores)==7
    assert len(ml.trial_scores)==28
    assert ml.participant_scores["participant_id"].nunique()==7

def test_multilevel_requires_participant_metadata():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=31)
    with pytest.raises(ValueError):
        fit_multilevel_fpca(x,participant_column="missing")

def test_functional_distances_are_symmetric_and_zero_diagonal():
    x=simulate_planar_trajectories(n_participants=3,trials_per_participant=2,n_time=31)
    d=pairwise_functional_distances(x)
    assert np.allclose(d,d.T)
    assert np.allclose(np.diag(d),0)
    assert functional_l2_distance(x.values[0],x.values[0],time=x.time)==pytest.approx(0)
    nearest=nearest_trajectory_indices(x,index=0,n_neighbors=2)
    assert len(nearest)==2 and 0 not in nearest

def test_score_clustering_reproducible():
    x=simulate_planar_trajectories(n_participants=8,trials_per_participant=2,n_time=41)
    fit=fit_mfpca(x,n_components=4,scaling="dimension_sd")
    a=cluster_fpca_scores(fit,n_clusters=2,random_state=11)
    b=cluster_fpca_scores(fit,n_clusters=2,random_state=11)
    assert np.array_equal(a.labels,b.labels)
    assert score_distance_matrix(fit,n_components=2).shape==(16,16)

def test_scalar_on_function_regression_gaussian_and_binomial():
    x=simulate_planar_trajectories(n_participants=10,trials_per_participant=2,n_time=41)
    fit=fit_mfpca(x,n_components=4,scaling="dimension_sd")
    y=2*fit.scores[:,0] + .2
    reg=fit_scalar_on_function_regression(fit,y,n_components=2)
    assert reg.model.rsquared > .95
    rng=np.random.default_rng(9)
    logits=0.7*fit.scores[:,0] + rng.normal(0,1,len(y))
    binary=(logits>np.median(logits)).astype(float)
    blog=fit_scalar_on_function_regression(fit,binary,n_components=1,family="binomial")
    assert blog.predictions.shape==(20,)
    with pytest.raises(ValueError):
        fit_scalar_on_function_regression(fit,np.arange(3))
    with pytest.raises(ValueError):
        fit_scalar_on_function_regression(fit,y,family="poisson")
