"""Mathematically reversible MH interweaving checks; no mixing qualification."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import (
    _factor_scale_log_mh_ratio,
    _metropolis_scale_interweave,
    fit_bayesian_sparse_fpca,
)
from eyetrajectoriespy.bayesian.planar_factor_gibbs import fit_bayesian_planar_factor
from eyetrajectoriespy.types import IrregularTrajectorySet
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis


@pytest.mark.parametrize("planar", [False,True])
def test_exact_log_jacobian_and_involution_at_each_factor(planar):
    rng=np.random.default_rng(261120)
    q,k,n=5,2,17
    loading=rng.normal(scale=.2,size=(2,q,k) if planar else (q,k))
    scores=rng.normal(size=(n,k))
    for j in range(k):
        scale=.21 if j==0 else -.32
        score0=scores.copy()
        load0=loading.copy()
        before=np.einsum("...qk,nk->n...q",loading,scores)
        log_ratio=_factor_scale_log_mh_ratio(loading,scores,j,scale,.2)
        loading[...,j]*=np.exp(scale)
        scores[:,j]*=np.exp(-scale)
        after=np.einsum("...qk,nk->n...q",loading,scores)
        np.testing.assert_allclose(before,after,atol=1e-12,rtol=1e-12)
        inverse=_factor_scale_log_mh_ratio(loading,scores,j,-scale,.2)
        np.testing.assert_allclose(log_ratio+inverse,0,atol=1e-10)
        # Derive full log-prior ratio from independent Gaussian densities,
        # and include the deterministic change-of-variable Jacobian.
        ld=loading.reshape(-1,k)
        old=load0.reshape(-1,k)
        prior_delta=-.5*((np.sum(ld**2)-np.sum(old**2))/.2**2
                           +np.sum(scores**2)-np.sum(score0**2))
        log_jacobian=(len(old)-len(scores))*scale
        np.testing.assert_allclose(log_ratio,prior_delta+log_jacobian,atol=1e-10)


def test_zero_scale_is_exact_noop_for_sampler_and_rng():
    rng=np.random.default_rng(2026)
    load=rng.normal(size=(5,2))
    scores=rng.normal(size=(12,2))
    load_original=load.copy()
    scores_original=scores.copy()
    state=repr(rng.bit_generator.state)
    accepted=_metropolis_scale_interweave(load,scores,rng,0.,.2)
    assert accepted==0 and repr(rng.bit_generator.state)==state
    np.testing.assert_array_equal(load,load_original)
    np.testing.assert_array_equal(scores,scores_original)


def test_B6_actual_native_sparse_sampler_with_optin_interweaving():
    rng=np.random.default_rng(88)
    grid=np.linspace(0,1,21)
    times=[];values=[]
    for i in range(10):
        t=np.sort(rng.uniform(.02,.98,9+i%3))
        y=.45+.05*np.sin(np.pi*t)+rng.normal(0,.05,len(t))
        times.append(t);values.append(y[:,None])
    trajectories=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"c{i}" for i in range(10)),
        dimension_names=("x",),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"p{i}" for i in range(10)]}))
    args=dict(trajectories=trajectories,dimension="x",evaluation_grid=grid,
              n_components=1,n_basis=5,noise_sd=.05,mean_prior_sd=.5,
              loading_prior_sd=.2,n_chains=2,n_draws=20,warmup=30,
              thin=1,random_state=404)
    baseline=fit_bayesian_sparse_fpca(**args)
    no_interweave=fit_bayesian_sparse_fpca(**args,scale_interweave_proposal_sd=0.)
    np.testing.assert_array_equal(baseline.population_mean_draws,
                                  no_interweave.population_mean_draws)
    candidate=fit_bayesian_sparse_fpca(**args,scale_interweave_proposal_sd=.22)
    assert candidate.evidence["scale_interweave_attempted"]==2*(30+20)
    assert 0<candidate.evidence["scale_interweave_accepted"] <= candidate.evidence["scale_interweave_attempted"]
    assert not candidate.evidence["scale_interweave_inferential_qualification"]
    np.testing.assert_array_equal(candidate.population_covariance_draws,
                                  fit_bayesian_sparse_fpca(
                                      **args,scale_interweave_proposal_sd=.22
                                  ).population_covariance_draws)


def test_B7_actual_async_planar_rank2_sampler_scale_move():
    rng=np.random.default_rng(222)
    grid=np.linspace(0,1,21)
    ts=[];ys=[]
    for i in range(12):
        tx=np.sort(rng.uniform(.02,.98,9))
        ty=np.sort(rng.uniform(.02,.98,11))
        union=np.sort(np.r_[tx,ty])
        vals=np.full((len(union),2),np.nan)
        vals[np.searchsorted(union,tx),0]=.45+.1*np.sin(np.pi*tx)+rng.normal(0,.04,len(tx))
        vals[np.searchsorted(union,ty),1]=.52+.1*np.cos(np.pi*ty)+rng.normal(0,.06,len(ty))
        ts.append(union);ys.append(vals)
    trajectories=IrregularTrajectorySet(
        time=tuple(ts),values=tuple(ys),curve_ids=tuple(f"c{i}" for i in range(12)),
        dimension_names=("x","y"),coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"p{i}" for i in range(12)]}))
    args=dict(trajectories=trajectories,evaluation_grid=grid,
        observation_noise_sd=(.04,.06),n_components=2,n_basis=5,
        mean_prior_sd=.6,loading_prior_sd=.2,n_chains=2,
        n_draws=20,warmup=30,thin=1,random_state=606)
    result=fit_bayesian_planar_factor(**args,scale_interweave_proposal_sd=.2)
    assert result.evidence["scale_interweave_attempted"]==2*(30+20)*2
    assert result.evidence["scale_interweave_accepted"]>0
    assert not result.evidence["posterior_mixing_scientifically_qualified"]
    assert not result.evidence["scale_interweave_inferential_qualification"]
    for draws in (result.population_mean_draws,
                  result.joint_population_covariance_draws):
        assert np.isfinite(draws).all()
    for bad in [-.1,float("nan"),1.1,True]:
        with pytest.raises(ValueError,match="scale_interweave"):
            fit_bayesian_planar_factor(
                **args,scale_interweave_proposal_sd=bad)
