"""B7 Gaussian learned planar shared-score research numerical contracts."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.bayesian import fit_bayesian_planar_factor
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
from eyetrajectoriespy.types import IrregularTrajectorySet


def _fixture(*, async_channels=True, rank=1, n=12, seed=149):
    rng=np.random.default_rng(seed)
    grid=np.linspace(0,1,25)
    q=5
    mu=np.asarray([
        [.30,.38,.42,.35,.27],
        [.47,.52,.49,.56,.51],
    ])
    loading=np.asarray([
        [[.18,.13],[.11,-.06],[.20,.16],[.09,.07],[.10,.13]],
        [[.14,.08],[.12,.15],[.17,-.03],[.14,.13],[.07,.10]],
    ])[:,:,:rank]
    times, values=[], []
    for i in range(n):
        tx=np.sort(rng.uniform(.02,.98,10+i%3))
        ty=np.sort(rng.uniform(.02,.98,9+i%4)) if async_channels else tx.copy()
        z=rng.normal(size=rank)
        bx=_spline_basis(tx,0,1,q)
        by=_spline_basis(ty,0,1,q)
        obsx=bx@(mu[0]+loading[0]@z)+rng.normal(0,.04,len(tx))
        obsy=by@(mu[1]+loading[1]@z)+rng.normal(0,.06,len(ty))
        if async_channels:
            union=np.sort(np.r_[tx,ty])
            arr=np.full((len(union),2),np.nan)
            arr[np.searchsorted(union,tx),0]=obsx
            arr[np.searchsorted(union,ty),1]=obsy
        else:
            union=tx
            arr=np.column_stack([obsx,obsy])
        times.append(union)
        values.append(arr)
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"g{i}" for i in range(n)),
        dimension_names=("x","y"),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(n)]}),
    )
    basis=_spline_basis(grid,0,1,q)
    truth=np.column_stack([basis@mu[0],basis@mu[1]])
    return gaze,grid,truth


def _fit(gaze,grid,rank=1,seed=2026):
    return fit_bayesian_planar_factor(
        gaze,evaluation_grid=grid,
        observation_noise_sd=(.04,.06),n_components=rank,n_basis=5,
        mean_prior_sd=.8,loading_prior_sd=.25,
        n_chains=2,n_draws=20,warmup=25,thin=1,random_state=seed)


@pytest.mark.parametrize("async_channels", [False, True])
def test_learned_planar_population_covariance_shape_and_exact_order(async_channels):
    gaze,grid,truth=_fixture(async_channels=async_channels)
    result=_fit(gaze,grid)
    g=len(grid)
    assert result.population_mean_draws.shape==(2,20,g,2)
    assert result.joint_population_covariance_draws.shape==(2,20,2*g,2*g)
    assert result.loading_function_draws.shape==(2,20,1,g,2)
    assert result.shared_score_draws.shape==(2,20,gaze.n_curves,1)
    assert result.reconstructed_latent_draws.shape==(2,20,gaze.n_curves,g,2)
    assert result.evidence["asynchronous_coordinate_observations"] is async_channels
    assert result.evidence["native_observation_times_interpolated"] is False
    assert result.evidence["joint_covariance_flattening_order"]=="channel_major_xgrid_then_ygrid"
    assert result.evidence["population_mean_and_joint_covariance_learned"]
    assert not result.evidence["native_full_Bayesian_planar_MFPCA_scientifically_qualified"]
    summary=result.posterior_population_frame()
    assert len(summary)==g and not summary.scientific_coverage_qualified.any()
    assert np.mean(np.abs(result.population_mean_draws.mean((0,1))-truth))<.28
    cov=result.joint_population_covariance_draws[0,0]
    np.testing.assert_allclose(cov,cov.T,atol=1e-12)
    assert np.linalg.eigvalsh(cov).min()>-1e-9
    # The cross-channel block is nonzero and is constructed by SHARED factors.
    assert np.max(np.abs(cov[:g,g:]))>0
    load=result.loading_function_draws[0,0]
    flattened=np.concatenate([load[0,:,0],load[0,:,1]])
    np.testing.assert_allclose(cov,np.outer(flattened,flattened),atol=1e-12)
    with pytest.raises(ValueError):
        result.population_mean_draws[0,0,0,0]=100


def test_asynchronous_rank2_joint_covariance_psd_and_reproducibility():
    gaze,grid,_=_fixture(rank=2,seed=119)
    fit1=_fit(gaze,grid,rank=2,seed=998)
    fit2=_fit(gaze,grid,rank=2,seed=998)
    np.testing.assert_array_equal(fit1.population_mean_draws,fit2.population_mean_draws)
    np.testing.assert_array_equal(fit1.joint_population_covariance_draws,
                                  fit2.joint_population_covariance_draws)
    cov=fit1.joint_population_covariance_draws[1,0]
    assert np.linalg.eigvalsh(cov).min()>-1e-9
    assert np.linalg.matrix_rank(cov,tol=1e-8)<=2
    assert fit1.evidence["n_components"]==2


def test_pseudoreplication_and_missing_coordinate_fail_closed():
    gaze,grid,_=_fixture()
    meta=gaze.metadata.copy()
    meta.iloc[1,0]=meta.iloc[0,0]
    repeated=IrregularTrajectorySet(
        time=gaze.time,values=gaze.values,
        curve_ids=gaze.curve_ids,dimension_names=gaze.dimension_names,
        metadata=meta,
    )
    with pytest.raises(ValueError,match="participant_id"):
        _fit(repeated,grid)
    modified=[x.copy() for x in gaze.values]
    modified[0][:,1]=np.nan
    incomplete=IrregularTrajectorySet(
        time=gaze.time,values=tuple(modified),
        curve_ids=gaze.curve_ids,dimension_names=gaze.dimension_names,
        metadata=gaze.metadata,
    )
    with pytest.raises(ValueError,match="at least four"):
        _fit(incomplete,grid)
    with pytest.raises(ValueError,match="observation_noise_sd"):
        fit_bayesian_planar_factor(
            gaze,evaluation_grid=grid,observation_noise_sd=(.04,0))
    with pytest.raises(ValueError,match="rank"):
        fit_bayesian_planar_factor(
            gaze,evaluation_grid=grid,observation_noise_sd=(.04,.06),
            n_components=6,n_basis=5)
