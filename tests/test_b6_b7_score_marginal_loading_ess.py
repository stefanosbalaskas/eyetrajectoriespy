"""Independent dense Gaussian checks for integrated loading likelihood and ESS moves."""
from __future__ import annotations

import numpy as np
import pytest

from eyetrajectoriespy.bayesian._score_marginal_loading import (
    _score_marginal_loading_loglike,
    _elliptical_slice_score_marginal_loading,
)
from eyetrajectoriespy.bayesian.sparse_factor_gibbs import (
    fit_bayesian_sparse_fpca,
)
from eyetrajectoriespy.bayesian.planar_factor_gibbs import (
    fit_bayesian_planar_factor,
)


@pytest.mark.parametrize("n_channels,n_components",[(1,1),(2,1),(2,2)])
def test_score_integrated_loading_loglike_matches_independent_dense_gaussian(
    n_channels,n_components,
):
    rng=np.random.default_rng(1319+n_channels*31+n_components)
    d,q,k=n_channels,4,n_components
    obs=[(5+channel) for channel in range(d)]
    B=[rng.normal(size=(n,q)) for n in obs]
    y=[rng.normal(size=n) for n in obs]
    mu=rng.normal(size=(d,q))
    sigma=np.linspace(.2,.3,d)
    G=np.stack([(b.T@b)[None,:,:] for b in B])
    C=np.stack([(b.T@v)[None,:] for b,v in zip(B,y,strict=True)])
    L0=rng.normal(size=(d,q,k))*.2
    L1=rng.normal(size=(d,q,k))*.5
    def marginal_native(L):
        return _score_marginal_loading_loglike(L,G,C,mu,sigma)
    def marginal_dense(L):
        A=np.concatenate([B[j]@L[j] for j in range(d)],axis=0)
        z=np.concatenate([y[j]-B[j]@mu[j] for j in range(d)])
        diag=np.concatenate([np.full(n,sigma[j]**2) for j,n in enumerate(obs)])
        V=np.diag(diag)+A@A.T
        sign,logdet=np.linalg.slogdet(V)
        assert sign>0
        return -.5*(z@np.linalg.solve(V,z)+logdet)
    np.testing.assert_allclose(marginal_native(L1)-marginal_native(L0),
        marginal_dense(L1)-marginal_dense(L0),rtol=1e-10,atol=1e-10)


def test_loading_ess_is_seed_reproducible_finite_and_prior_preserving():
    rng=np.random.default_rng(441)
    d,n,q,k=2,5,4,1
    G=np.stack([np.stack([np.eye(q)*1.5]*n)]*d)
    C=rng.normal(size=(d,n,q))
    mu=np.zeros((d,q))
    noise=np.array([.1,.2])
    loading=rng.normal(scale=.3,size=(d,q,k))
    a,num_a=_elliptical_slice_score_marginal_loading(
        loading,G,C,mu,noise,.3,np.random.default_rng(2026))
    b,num_b=_elliptical_slice_score_marginal_loading(
        loading,G,C,mu,noise,.3,np.random.default_rng(2026))
    np.testing.assert_array_equal(a,b)
    assert num_a==num_b and num_a>=1
    assert np.isfinite(a).all()
    assert not np.array_equal(a,loading)
    with pytest.raises(ValueError,match="loading prior"):
        _elliptical_slice_score_marginal_loading(
            loading,G,C,mu,noise,0.,np.random.default_rng(3))


def test_new_B6_B7_loading_default_remains_disabled_and_evidence_failclosed():
    from eyetrajectoriespy.types import IrregularTrajectorySet
    from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _spline_basis
    import pandas as pd
    rng=np.random.default_rng(13)
    GRID=np.linspace(0.,1.,23)
    N_BASIS=5
    MEAN_PRIOR_SD=.45
    times=[];values=[]
    for i in range(12):
        ti=np.linspace(.03,.96,9+i%3)
        bx=_spline_basis(ti,0,1,N_BASIS)
        xi=.15+bx@rng.normal(size=N_BASIS)*.1
        times.append(ti)
        values.append(xi[:,None])
    gaze=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"P{i}" for i in range(12)),
        dimension_names=("x",),time_unit="s",
        coordinate_system="normalized",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(12)]}))
    options=dict(dimension="x",evaluation_grid=GRID,n_basis=N_BASIS,
        noise_sd=.05,mean_prior_sd=MEAN_PRIOR_SD,
        loading_prior_sd=.2,n_chains=2,n_draws=20,warmup=20,
        collapsed_population_mean_update=True,random_state=135)
    b=fit_bayesian_sparse_fpca(gaze,**options)
    assert b.evidence["score_marginal_loading_ess_experimental_opt_in"] is False
    assert b.evidence["score_marginal_loading_ess_likelihood_evaluations"]==0
    e=fit_bayesian_sparse_fpca(gaze,**options,score_marginal_loading_ess=True)
    assert e.evidence["score_marginal_loading_ess_likelihood_evaluations"]>0
    assert not e.evidence["score_marginal_loading_ess_scientifically_qualified"]
    assert not e.evidence["release_authorized"]
    assert np.isfinite(e.population_covariance_draws).all()
    times=[];values=[]
    for i in range(12):
        tx=np.linspace(.03,.95,9+i%3)
        ty=np.linspace(.04,.94,10+i%3)
        t=np.sort(np.r_[tx,ty])
        v=np.full((len(t),2),np.nan)
        v[np.searchsorted(t,tx),0]=.15+rng.normal(scale=.05,size=len(tx))
        v[np.searchsorted(t,ty),1]=.2+rng.normal(scale=.05,size=len(ty))
        times.append(t)
        values.append(v)
    planar=IrregularTrajectorySet(
        time=tuple(times),values=tuple(values),
        curve_ids=tuple(f"P{i}" for i in range(12)),
        dimension_names=("x","y"),time_unit="s",
        coordinate_system="normalized",
        metadata=pd.DataFrame({"participant_id":[f"P{i}" for i in range(12)]}))
    grid=GRID
    noise=(.04,.06)
    options7=dict(dimensions=("x","y"),evaluation_grid=grid,
       observation_noise_sd=noise,n_basis=5,n_components=1,
       mean_prior_sd=.45,loading_prior_sd=.2,n_chains=2,n_draws=20,
       warmup=20,collapsed_population_mean_update=True,random_state=217)
    p=fit_bayesian_planar_factor(planar,**options7,score_marginal_loading_ess=True)
    assert p.evidence["score_marginal_loading_ess_experimental_opt_in"] is True
    assert p.evidence["score_marginal_loading_ess_likelihood_evaluations"]>0
    assert p.evidence["asynchronous_coordinate_observations"] is True
    assert np.isfinite(p.joint_population_covariance_draws).all()
    assert not p.evidence["native_full_Bayesian_planar_MFPCA_scientifically_qualified"]
    with pytest.raises(ValueError,match="score_marginal_loading_ess"):
        fit_bayesian_planar_factor(planar,**options7,score_marginal_loading_ess=1)
