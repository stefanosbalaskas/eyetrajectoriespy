"""Experimental Gaussian factor loading update with participant scores marginalized.

Elliptical-slice sampling (ESS) preserves the exact zero-centred Gaussian
loading prior and updates loading columns jointly against the *integrated*
score marginal likelihood. Model-specific mean, noise, rank and prior values
are unchanged. This is an internal research transition, not proven
scientific coverage or a promoted API.
"""
from __future__ import annotations

import numpy as np


def _score_marginal_loading_loglike(
    loading: np.ndarray, gram: np.ndarray, cross: np.ndarray,
    mean: np.ndarray, noise: np.ndarray,
) -> float:
    """L-dependent part of log p(Y|L,mu), with z_i ~ N(0,I).

    Inputs are channel-major: loading [d,q,k], gram [d,n,q,q],
    cross [d,n,q], mean [d,q], noise [d]. Unknown participant
    scores are analytically integrated via the determinant lemma.
    Constants depending only on Y, mu and noise cancel for ESS.
    """
    load=np.asarray(loading,dtype=float)
    G=np.asarray(gram,dtype=float)
    C=np.asarray(cross,dtype=float)
    m=np.asarray(mean,dtype=float)
    noise=np.asarray(noise,dtype=float)
    if load.ndim!=3:
        raise ValueError("loading must be channel-by-basis-by-component")
    d,q,k=load.shape
    if G.ndim!=4 or G.shape[0]!=d or G.shape[2:]!=(q,q):
        raise ValueError("channel-major gram tensor shape mismatch")
    n=G.shape[1]
    if (C.shape!=(d,n,q) or m.shape!=(d,q) or noise.shape!=(d,)
        or not np.isfinite(noise).all() or (noise<=0).any()):
        raise ValueError("invalid score-marginal Gaussian contract")
    if not all(np.isfinite(z).all() for z in (load,G,C,m)):
        raise ValueError("nonfinite marginal Gaussian input")
    w=1./noise**2
    result=0.
    eye=np.eye(k)
    for i in range(n):
        Q=eye.copy()
        v=np.zeros(k)
        for j in range(d):
            lj=load[j]
            gj=G[j,i]
            Q+=w[j]*(lj.T@gj@lj)
            v+=w[j]*lj.T@(C[j,i]-gj@m[j])
        sign, logdet=np.linalg.slogdet(Q)
        if sign<=0 or not np.isfinite(logdet):
            raise ValueError("score-integrated covariance precision not PD")
        result += .5*(float(v@np.linalg.solve(Q,v))-float(logdet))
    if not np.isfinite(result):
        raise ValueError("nonfinite score-marginal loading likelihood")
    return float(result)


def _elliptical_slice_score_marginal_loading(
    loading:np.ndarray,gram:np.ndarray,cross:np.ndarray,mean:np.ndarray,
    noise:np.ndarray,prior_sd:float,rng:np.random.Generator,
    *,max_bracket_steps:int=10000,
)->tuple[np.ndarray,int]:
    """Exact ESS transition for loading|mu,Y after integrating scores.

    Prior is iid N(0,prior_sd**2) over every channel/basis/component
    loading; ESS uses one prior draw and shrinks a full [0,2pi] angular
    bracket. No sample-dependent step size or acceptance target.
    Raises on numerical problems rather than retaining an invalid draw.
    """
    if (not np.isfinite(prior_sd) or prior_sd<=0 or
        isinstance(max_bracket_steps,bool) or
        not isinstance(max_bracket_steps,int) or max_bracket_steps<1):
        raise ValueError("positive finite loading prior SD and bracket limit needed")
    current=np.asarray(loading,dtype=float)
    ell=rng.normal(scale=prior_sd,size=current.shape)
    logy=_score_marginal_loading_loglike(current,gram,cross,mean,noise)+np.log(rng.random())
    theta=float(rng.uniform(0.,2*np.pi))
    lo,hi=theta-2*np.pi,theta
    for trial in range(max_bracket_steps):
        proposed=current*np.cos(theta)+ell*np.sin(theta)
        candidate=_score_marginal_loading_loglike(proposed,gram,cross,mean,noise)
        if candidate>=logy:
            return proposed,trial+1
        if theta<0.:
            lo=theta
        else:
            hi=theta
        theta=float(rng.uniform(lo,hi))
    raise RuntimeError("score-marginal loading ESS failed to find valid slice")
