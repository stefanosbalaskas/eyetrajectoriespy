"""B6 native Gibbs finite-basis Bayesian sparse factor research contracts."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.bayesian import fit_bayesian_sparse_fpca
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis


def _fixture(seed=99, n=22):
    rng=np.random.default_rng(seed)
    grid=np.linspace(0,1,37)
    mean_coeff=np.array([.37,.40,.45,.32,.28])
    loading_coeff=np.array([.13,.08,.19,.11,.02])
    scores=rng.normal(size=n)
    times,values=[],[]
    for i in range(n):
        ti=np.sort(rng.uniform(.015,.985,size=14+(i%5)))
        basis=_spline_basis(ti,grid[0],grid[-1],5)
        yi=basis@(mean_coeff+loading_coeff*scores[i])
        yi+=rng.normal(scale=.035,size=len(ti))
        times.append(ti)
        values.append(yi[:,None])
    data=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"subject_{i}" for i in range(n)),
        dimension_names=("x",),coordinate_system="normalized",
        time_unit="normalized",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(n)]}),
    )
    truth=_spline_basis(grid,grid[0],grid[-1],5)@mean_coeff
    return data,grid,truth


def _fit(data,grid,seed=642):
    return fit_bayesian_sparse_fpca(
        data,dimension="x",evaluation_grid=grid,
        n_components=1,n_basis=5,
        noise_sd=.035,mean_prior_sd=1.,
        loading_prior_sd=.25,
        n_chains=2,n_draws=25,warmup=45,thin=1,
        random_state=seed,
    )


def test_b6_learned_population_mean_covariance_and_reproducibility():
    data,grid,truth=_fixture()
    fit=_fit(data,grid)
    assert fit.population_mean_draws.shape==(2,25,len(grid))
    assert fit.population_covariance_draws.shape==(2,25,len(grid),len(grid))
    assert fit.loading_function_draws.shape==(2,25,1,len(grid))
    assert fit.latent_score_draws.shape==(2,25,data.n_curves,1)
    assert fit.reconstructed_latent_draws.shape==(2,25,data.n_curves,len(grid))
    assert np.isfinite(fit.population_mean_draws).all()
    estimated=fit.population_mean_draws.mean(axis=(0,1))
    assert np.mean(np.abs(estimated-truth)) < .18
    for c in range(2):
        for d in range(25):
            matrix=fit.population_covariance_draws[c,d]
            np.testing.assert_allclose(matrix,matrix.T,atol=1e-12)
            assert np.linalg.eigvalsh(matrix).min() > -1e-9
            assert np.any(np.diag(matrix)>0)
    summary=fit.posterior_population_frame()
    assert len(summary)==len(grid)
    assert summary.credible_intervals_not_scientifically_calibrated.all()
    assert fit.evidence["population_mean_learned"]
    assert fit.evidence["population_covariance_learned"]
    assert fit.evidence["orthonormal_identified_eigenfunctions_estimated"] is False
    assert fit.evidence["posterior_inference_scientifically_qualified"] is False
    with pytest.raises(ValueError):
        fit.population_mean_draws[0,0,0]=500.
    second=_fit(data,grid)
    np.testing.assert_array_equal(fit.population_mean_draws,second.population_mean_draws)
    np.testing.assert_array_equal(fit.population_covariance_draws,second.population_covariance_draws)


def test_b6_learned_factor_rejects_pseudoreplication_and_missing_support():
    gaze,grid,_=_fixture(n=12)
    duplicated_meta=gaze.metadata.reset_index(drop=True).copy()
    duplicated_meta.iloc[1,0]=duplicated_meta.iloc[0,0]
    repeated=IrregularTrajectorySet(
        time=gaze.time,values=gaze.values,
        curve_ids=gaze.curve_ids,dimension_names=gaze.dimension_names,
        metadata=duplicated_meta,coordinate_system=gaze.coordinate_system,
        time_unit=gaze.time_unit,
    )
    with pytest.raises(ValueError,match="repeated participants"):
        _fit(repeated,grid)
    with pytest.raises(ValueError,match="noise_sd"):
        fit_bayesian_sparse_fpca(
            gaze,dimension="x",evaluation_grid=grid,noise_sd=0,
        )
    with pytest.raises(ValueError,match="rank"):
        fit_bayesian_sparse_fpca(
            gaze,dimension="x",evaluation_grid=grid,
            n_components=6,n_basis=5,noise_sd=.04,
        )
    with pytest.raises(ValueError,match="grid"):
        fit_bayesian_sparse_fpca(
            gaze,dimension="x",evaluation_grid=np.linspace(.1,.9,21),
            noise_sd=.04,
        )


def test_b6_learned_factor_explicit_nan_missingness_only():
    gaze,grid,_=_fixture(n=12)
    vals=[x.copy() for x in gaze.values]
    vals[0][0,0]=np.nan
    modified=IrregularTrajectorySet(
        time=gaze.time,values=tuple(vals),
        curve_ids=gaze.curve_ids,dimension_names=gaze.dimension_names,
        metadata=gaze.metadata,coordinate_system=gaze.coordinate_system,
        time_unit=gaze.time_unit,
    )
    fit=fit_bayesian_sparse_fpca(
        modified,dimension="x",evaluation_grid=grid,
        noise_sd=.035,n_chains=2,n_draws=20,warmup=25,thin=1,
        n_basis=5,n_components=1,
    )
    assert fit.evidence["min_samples_per_curve"] >= 4
    assert not fit.evidence["raw_sparse_observations_resampled"]
    vals[0][1,0]=np.inf
    bad=IrregularTrajectorySet(
        time=gaze.time,values=tuple(vals),
        curve_ids=gaze.curve_ids,dimension_names=gaze.dimension_names,
        metadata=gaze.metadata,
    )
    with pytest.raises(ValueError,match="infinities"):
        fit_bayesian_sparse_fpca(
            bad,dimension="x",evaluation_grid=grid,noise_sd=.035,
        )


def test_b6_covariance_is_invariant_to_latent_factor_rotations():
    rng=np.random.default_rng(15)
    f=rng.normal(size=(13,2))
    theta=.6
    rot=np.array([[np.cos(theta),-np.sin(theta)],
                  [np.sin(theta),np.cos(theta)]])
    np.testing.assert_allclose(f@f.T,(f@rot)@(f@rot).T,atol=1e-12)
