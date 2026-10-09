"""Independent Gaussian conditional checks for B6/B7 conjugate Gibbs blocks.

These tests derive the exact posterior from explicit observation-row design
matrices, not from the Gibbs functions' sufficient-statistic calculations.
Conditional correctness does NOT prove joint chain mixing or calibrated
credible intervals.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from eyetrajectoriespy.bayesian.sparse_factor_gibbs import _draw_gaussian_precision


def _reference(design:np.ndarray,values:np.ndarray,prior_sd:float,
               noise_sd:float):
    """Ordinary independent linear-Gaussian regression posterior."""
    width=design.shape[1]
    precis=np.eye(width)/prior_sd**2+design.T@design/noise_sd**2
    rhs=design.T@values/noise_sd**2
    return precis,np.linalg.solve(precis,rhs)


def test_B6_population_mean_gaussian_conditional_vs_explicit_rows():
    rng=np.random.default_rng(33)
    q,k,n=5,2,6
    Bs=[rng.normal(size=(9+(i%3),q)) for i in range(n)]
    z=rng.normal(size=(n,k))
    load=rng.normal(size=(q,k))
    mu=rng.normal(size=q)
    y=[b@(mu+load@zi)+rng.normal(0,.05,len(b)) for b,zi in zip(Bs,z)]
    prior_sd,noise=.42,.05
    design=np.vstack(Bs)
    adjusted=np.concatenate([yi-b@load@zi for b,yi,zi in zip(Bs,y,z)])
    precision,posterior_mean=_reference(design,adjusted,prior_sd,noise)
    gram=sum((b.T@b for b in Bs))
    cross=sum((b.T@(yi-b@load@zi) for b,yi,zi in zip(Bs,y,z)))
    ps=gram/noise**2+np.eye(q)/prior_sd**2
    ms=cho_solve(cho_factor(ps),cross/noise**2)
    np.testing.assert_allclose(ps,precision,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(ms,posterior_mean,rtol=1e-11,atol=1e-11)


def test_B6_rank2_loading_gaussian_conditional_vs_explicit_row_design():
    rng=np.random.default_rng(63)
    q,k,n=5,2,6
    Bs=[rng.normal(size=(8+i%3,q)) for i in range(n)]
    z=rng.normal(size=(n,k))
    mu=rng.normal(size=q)
    y=[b@mu+rng.normal(size=len(b))*.06 for b in Bs]
    prior_sd,noise=.31,.06
    explicit=np.vstack([
        np.einsum("iq,k->iqk",b,zi).reshape(len(b),q*k)
        for b,zi in zip(Bs,z)])
    target=np.concatenate([yi-b@mu for b,yi in zip(Bs,y)])
    p_ref,m_ref=_reference(explicit,target,prior_sd,noise)
    p_code=np.eye(q*k)/prior_sd**2
    rhs=np.zeros((q,k))
    for b,zi,yi in zip(Bs,z,y):
        gram=b.T@b
        p_code+=np.kron(gram,np.outer(zi,zi))/noise**2
        rhs+=np.outer(b.T@yi-gram@mu,zi)
    m_code=np.linalg.solve(p_code,(rhs/noise**2).ravel())
    np.testing.assert_allclose(p_code,p_ref,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(m_code,m_ref,rtol=1e-11,atol=1e-11)


def test_B7_async_two_channel_shared_score_conditional_vs_stacked_rows():
    rng=np.random.default_rng(301)
    q,k=5,2
    Bs=[rng.normal(size=(9,q)),rng.normal(size=(13,q))]
    load=[rng.normal(size=(q,k)) for _ in range(2)]
    means=[rng.normal(size=q) for _ in range(2)]
    noise=np.array([.03,.08])
    y=[b@mean+rng.normal(size=len(b))*sd
       for b,mean,sd in zip(Bs,means,noise)]
    # Different channel observation counts; never align/interpolate clocks.
    design=np.vstack([b@ld/sd for b,ld,sd in zip(Bs,load,noise)])
    target=np.concatenate([(yi-b@mean)/sd
                           for b,yi,mean,sd in zip(Bs,y,means,noise)])
    p_ref=np.eye(k)+design.T@design
    m_ref=np.linalg.solve(p_ref,design.T@target)
    p_code=np.eye(k)
    rhs=np.zeros(k)
    for b,ld,mean,yi,sd in zip(Bs,load,means,y,noise):
        gram=b.T@b
        p_code+=(ld.T@gram@ld)/sd**2
        rhs+=ld.T@(b.T@yi-gram@mean)/sd**2
    np.testing.assert_allclose(p_code,p_ref,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(np.linalg.solve(p_code,rhs),m_ref,rtol=1e-11,atol=1e-11)


def test_B7_async_two_channel_loading_conditionals_explicit_rows():
    rng=np.random.default_rng(743)
    q,k=5,2
    z=rng.normal(size=(7,k))
    Bs=[rng.normal(size=(10+i,q)) for i in range(len(z))]
    mean=rng.normal(size=q)
    prior_sd,noise=.2,.04
    y=[b@mean+rng.normal(size=len(b))*noise for b in Bs]
    explicit=np.vstack([
        np.einsum("iq,k->iqk",b,zi).reshape(len(b),q*k)
        for b,zi in zip(Bs,z)])
    residual=np.concatenate([yi-b@mean for b,yi in zip(Bs,y)])
    pref,mref=_reference(explicit,residual,prior_sd,noise)
    p=np.eye(q*k)/prior_sd**2
    rhs=np.zeros((q,k))
    for b,zi,yi in zip(Bs,z,y):
        gram=b.T@b
        p+=np.kron(gram,np.outer(zi,zi))/noise**2
        rhs+=np.outer(b.T@yi-gram@mean,zi)
    np.testing.assert_allclose(p,pref,rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(np.linalg.solve(p,(rhs/noise**2).ravel()),
                              mref,rtol=1e-11,atol=1e-11)


def test_gaussian_precision_sampler_recovers_known_analytic_conditional():
    rng=np.random.default_rng(8120)
    a=rng.normal(size=(4,4))
    p=a.T@a+np.eye(4)*2.
    rhs=rng.normal(size=4)
    target_mean=np.linalg.solve(p,rhs)
    target_cov=np.linalg.inv(p)
    draws=np.asarray([_draw_gaussian_precision(p,rhs,rng) for _ in range(5000)])
    np.testing.assert_allclose(draws.mean(axis=0),target_mean,rtol=0,atol=.065)
    np.testing.assert_allclose(np.cov(draws,rowvar=False),target_cov,rtol=.11,atol=.04)
