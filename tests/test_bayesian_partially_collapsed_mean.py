"""Independent exact Gaussian marginal p(mu | loading,Y) Woodbury contracts."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from scipy.linalg import block_diag

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import (
    _collapsed_sparse_mean_precision_rhs,fit_bayesian_sparse_fpca,
)
from eyetrajectoriespy.bayesian.planar_factor_gibbs import (
    _collapsed_planar_mean_precision_rhs,fit_bayesian_planar_factor,
)
from eyetrajectoriespy.types import IrregularTrajectorySet


def test_B6_collapsed_mean_matches_independent_full_marginal_likelihood():
    rng=np.random.default_rng(44)
    n,q,k=5,5,2
    L=rng.normal(size=(q,k))*.2
    Bs=[rng.normal(size=(8+i,q)) for i in range(n)]
    ys=[rng.normal(size=len(b)) for b in Bs]
    noise,mu_sd=.065,.4
    G=[b.T@b for b in Bs]
    c=[b.T@y for b,y in zip(Bs,ys)]
    P,rhs=_collapsed_sparse_mean_precision_rhs(G,c,L,noise,mu_sd)
    P_ref=np.eye(q)/mu_sd**2
    rhs_ref=np.zeros(q)
    for B,y in zip(Bs,ys):
        A=B@L
        V=noise**2*np.eye(len(y))+A@A.T
        P_ref+=B.T@np.linalg.solve(V,B)
        rhs_ref+=B.T@np.linalg.solve(V,y)
    np.testing.assert_allclose(P,P_ref,rtol=1e-10,atol=1e-10)
    np.testing.assert_allclose(rhs,rhs_ref,rtol=1e-10,atol=1e-10)
    assert np.linalg.eigvalsh(P).min()>0
    np.testing.assert_allclose(np.linalg.solve(P,rhs),
                              np.linalg.solve(P_ref,rhs_ref),atol=1e-10)


def test_B7_shared_latent_cross_channel_posterior_vs_dense_async_rows():
    rng=np.random.default_rng(124)
    q,k,n=5,2,5
    L=rng.normal(size=(2,q,k))*.2
    noise=np.array([.04,.075]);mu_sd=.5
    Gram=np.empty((2,n,q,q))
    Cross=np.empty((2,n,q))
    data=[]
    for i in range(n):
        Bx=rng.normal(size=(7+i,q))
        By=rng.normal(size=(10+i,q))
        yx=rng.normal(size=len(Bx))
        yy=rng.normal(size=len(By))
        data.append((Bx,By,yx,yy))
        Gram[0,i]=Bx.T@Bx;Gram[1,i]=By.T@By
        Cross[0,i]=Bx.T@yx;Cross[1,i]=By.T@yy
    P,rhs=_collapsed_planar_mean_precision_rhs(Gram,Cross,L,noise,mu_sd)
    p_ref=np.eye(2*q)/mu_sd**2
    b_ref=np.zeros(2*q)
    for Bx,By,yx,yy in data:
        X=block_diag(Bx,By)
        A=np.vstack([Bx@L[0],By@L[1]])
        v=np.diag(np.r_[np.repeat(noise[0]**2,len(yx)),
                        np.repeat(noise[1]**2,len(yy))])+A@A.T
        observed=np.r_[yx,yy]
        p_ref+=X.T@np.linalg.solve(v,X)
        b_ref+=X.T@np.linalg.solve(v,observed)
    np.testing.assert_allclose(P,p_ref,atol=1e-9,rtol=1e-9)
    np.testing.assert_allclose(rhs,b_ref,atol=1e-9,rtol=1e-9)
    assert np.linalg.eigvalsh(P).min()>0
    # Marginally shared x/y scores induce genuinely off-diagonal
    # cross-channel precision structure, never two separate regressions.
    assert np.linalg.norm(P[:q,q:])>1.e-4


def _data(dimensions=1):
    rng=np.random.default_rng(1701)
    t=[];observed=[]
    for i in range(12):
        x=np.sort(rng.uniform(.02,.98,9+i%3))
        if dimensions==1:
            times=x
            data=(.42+.08*np.sin(np.pi*x)+rng.normal(0,.05,len(x)))[:,None]
        else:
            y=np.sort(rng.uniform(.02,.98,10+i%2))
            times=np.sort(np.r_[x,y])
            data=np.full((len(times),2),np.nan)
            data[np.searchsorted(times,x),0]=.42+.08*np.sin(np.pi*x)+rng.normal(0,.05,len(x))
            data[np.searchsorted(times,y),1]=.52+.04*np.cos(np.pi*y)+rng.normal(0,.06,len(y))
        t.append(times);observed.append(data)
    return IrregularTrajectorySet(time=tuple(t),values=tuple(observed),
        curve_ids=tuple(f"c{i}" for i in range(12)),
        dimension_names=("x",) if dimensions==1 else ("x","y"),
        coordinate_system="normalized",time_unit="s",
        metadata=pd.DataFrame({"participant_id":[f"p{i}" for i in range(12)]}))


def test_B6_real_collapsed_sampler_optin_and_exact_default_noop():
    data=_data(1)
    args=dict(trajectories=data,dimension="x",evaluation_grid=np.linspace(0,1,21),
        n_components=2,n_basis=5,noise_sd=.05,mean_prior_sd=.5,
        loading_prior_sd=.2,n_chains=2,n_draws=20,warmup=25,thin=1,random_state=701)
    initial=fit_bayesian_sparse_fpca(**args)
    same=fit_bayesian_sparse_fpca(**args,collapsed_population_mean_update=False)
    np.testing.assert_array_equal(initial.population_covariance_draws,
                                  same.population_covariance_draws)
    candidate=fit_bayesian_sparse_fpca(**args,collapsed_population_mean_update=True)
    assert candidate.evidence["collapsed_population_mean_experimental_opt_in"]
    assert not candidate.evidence["collapsed_mean_inferential_qualification"]
    assert not candidate.evidence["posterior_inference_scientifically_qualified"]
    assert np.isfinite(candidate.population_mean_draws).all()
    assert np.isfinite(candidate.population_covariance_draws).all()
    with pytest.raises(ValueError,match="collapsed_population_mean_update"):
        fit_bayesian_sparse_fpca(**args,collapsed_population_mean_update=1)


def test_B7_real_async_collapsed_sampler_and_release_flags():
    data=_data(2)
    args=dict(trajectories=data,evaluation_grid=np.linspace(0,1,21),
        observation_noise_sd=(.05,.06),n_components=2,n_basis=5,
        mean_prior_sd=.5,loading_prior_sd=.2,
        n_chains=2,n_draws=20,warmup=25,thin=1,random_state=801)
    initial=fit_bayesian_planar_factor(**args)
    same=fit_bayesian_planar_factor(**args,collapsed_population_mean_update=False)
    np.testing.assert_array_equal(initial.joint_population_covariance_draws,
                                  same.joint_population_covariance_draws)
    candidate=fit_bayesian_planar_factor(**args,collapsed_population_mean_update=True)
    assert candidate.evidence["collapsed_population_mean_experimental_opt_in"]
    assert not candidate.evidence["collapsed_mean_inferential_qualification"]
    assert not candidate.evidence["native_full_Bayesian_planar_MFPCA_scientifically_qualified"]
    assert not candidate.evidence["release_authorized"]
    assert np.isfinite(candidate.population_mean_draws).all()
    assert np.isfinite(candidate.joint_population_covariance_draws).all()
    with pytest.raises(ValueError,match="collapsed_population_mean_update"):
        fit_bayesian_planar_factor(**args,collapsed_population_mean_update="yes")
