"""R25 experimental Gaussian restricted-likelihood covariance component estimator.

Uses ONLY observed native responses, WLS design and the predeclared four
working covariance kernels. Analytic REML gradient includes estimation of
fixed mean coefficients. Does not use the true simulator coefficients or
Gaussian innovations. An interior log-variance parameterization can approach
but cannot attain zero; report near-boundary estimates explicitly.

Simulation-aligned working covariance family, not a general eyetracking
covariance model. No fitted-target CR2 inference or API is qualified.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

from scripts.w3_r20_estimated_working_target import (
    COMPONENTS, MODELS, _kernels)

LOWER_LOG_RATIO=-13.8
UPPER_LOG_RATIO=7.0
BOUNDARY_RELATIVE_REFERENCE=1e-4
MAXITER=125


def prepare_reml_design(X,y,weight,cluster,time,trial,x,*,slope):
    if slope not in MODELS:
        raise ValueError("working covariance family must be predeclared")
    X=np.asarray(X,float);y=np.asarray(y,float);weight=np.asarray(weight,float)
    cluster=np.asarray(cluster);time=np.asarray(time,float)
    trial=np.asarray(trial);x=np.asarray(x,float)
    n=len(y)
    if (X.ndim!=2 or X.shape[0]!=n or n<=X.shape[1]
        or any(v.shape!=(n,) for v in (weight,cluster,time,trial,x))
        or not all(np.isfinite(v).all() for v in (X,y,weight,time,x))
        or np.any(weight<=0)):
        raise ValueError("invalid observed WLS source")
    groups=np.unique(cluster)
    if len(groups)<6:
        raise ValueError("at least six participants required")
    Z=X*np.sqrt(weight)[:,None]
    yy=y*np.sqrt(weight)
    if np.linalg.matrix_rank(Z)<X.shape[1]:
        raise ValueError("rank-deficient fixed mean design")
    prepared=[]
    for label in groups:
        ix=np.flatnonzero(cluster==label)
        if not np.allclose(x[ix],x[ix][0],rtol=0,atol=1e-12):
            raise ValueError("predictor must remain constant within participant")
        K=_kernels(time[ix],trial[ix],x[ix],weight[ix],slope)
        prepared.append((Z[ix],yy[ix],K))
    return prepared


def restricted_loglik_and_gradient(log_ratios,prepared,reference):
    """One half minus log restricted likelihood (irrelevant constants removed).

    G=Σ Z_i' V_i^-1 Z_i, beta=G^-1 Σ Z_i' V_i^-1 y_i.
    ℓ_REML=-1/2(Σlog|V_i|+log|G|+y'Py);
    d(-ℓ)/dθ_k=1/2[tr(P K_k)-y'P K_k P y].
    Returns derivative with respect to *log variance ratios*.
    """
    log_ratios=np.asarray(log_ratios,float)
    if log_ratios.shape!=(len(COMPONENTS),) or not np.isfinite(log_ratios).all():
        raise ValueError("four finite log variance ratios required")
    theta=float(reference)*np.exp(log_ratios)
    p=prepared[0][0].shape[1]
    G=np.zeros((p,p));g=np.zeros(p)
    y_vinv_y=0.;logdet=0.;blocks=[]
    for Zi,yi,ki in prepared:
        V=sum(float(theta[k])*Ki for k,Ki in enumerate(ki))
        fac=cho_factor((V+V.T)*.5,lower=True,check_finite=False)
        U=cho_solve(fac,Zi,check_finite=False)
        vy=cho_solve(fac,yi,check_finite=False)
        G+=Zi.T@U
        g+=Zi.T@vy
        y_vinv_y+=float(yi@vy)
        logdet+=float(2*np.log(np.diag(fac[0])).sum())
        blocks.append((Zi,yi,ki,fac,U))
    sign,lg=np.linalg.slogdet(G)
    if sign<=0:
        raise ValueError("generalized least squares Gram matrix not positive definite")
    B=np.linalg.solve(G,np.eye(p))
    beta=B@g
    py_variance=max(0.,float(y_vinv_y-g@beta))
    objective=.5*(logdet+float(lg)+py_variance)
    grad=np.zeros(len(COMPONENTS))
    for Zi,yi,ki,fac,U in blocks:
        residual=yi-Zi@beta
        Py=cho_solve(fac,residual,check_finite=False)
        Vinv=cho_solve(fac,np.eye(len(yi)),check_finite=False)
        for k,K in enumerate(ki):
            # For symmetric Vinv and K: trace(Vinv K) = sum(Vinv*K).
            tr_v=float(np.sum(Vinv*K))
            tr_leverage=float(np.trace(B@(U.T@K@U)))
            quad=float(Py@K@Py)
            grad[k]+=.5*(tr_v-tr_leverage-quad)
    return objective,grad*theta


def estimate_reml_components(X,y,weight,cluster,time,trial,x,*,slope,
                             initializer=None,maxiter=MAXITER):
    """Return observable-only fitted variance components and diagnostics.

    This is a bounded interior Gaussian REML *candidate*, not a calibrated
    estimator; the lower bound is disclosed, and numerical nonconvergence is
    never silently replaced with a different estimate.
    """
    prepared=prepare_reml_design(
        X,y,weight,cluster,time,trial,x,slope=slope)
    X=np.asarray(X,float);y=np.asarray(y,float);weight=np.asarray(weight,float)
    Z=X*np.sqrt(weight)[:,None]
    beta=np.linalg.lstsq(Z,y*np.sqrt(weight),rcond=None)[0]
    resid=y-X@beta
    reference=max(float(np.mean(resid**2)),1e-8)
    if initializer is None:
        guess=np.full(len(COMPONENTS),.1*reference)
        guess[-1]=reference
    else:
        guess=np.array([float(initializer[k]) for k in COMPONENTS])
        if not np.isfinite(guess).all() or np.any(guess<0):
            raise ValueError("initializer must contain finite nonnegative components")
        guess=np.maximum(guess,reference*.01)
    guess=np.clip(guess/reference,np.exp(LOWER_LOG_RATIO)*2,
                  np.exp(UPPER_LOG_RATIO)/2)
    start=np.log(guess)
    fitted=minimize(
        restricted_loglik_and_gradient,start,args=(prepared,reference),
        method="L-BFGS-B",jac=True,
        bounds=[(LOWER_LOG_RATIO,UPPER_LOG_RATIO)]*len(COMPONENTS),
        options={"maxiter":int(maxiter),"ftol":1e-10,"gtol":1e-6,
                 "maxls":30},
    )
    estimates=reference*np.exp(fitted.x)
    boundary=estimates<=reference*BOUNDARY_RELATIVE_REFERENCE
    near_box=np.abs(fitted.x-LOWER_LOG_RATIO)<1e-4
    blocks=[]
    for _,_,Ks in prepared:
        V=sum(float(estimates[k])*K for k,K in enumerate(Ks))
        if not np.linalg.cholesky((V+V.T)*.5).shape:
            raise ValueError("unreachable SPD check")
        blocks.append((V+V.T)*.5)
    return {
        "status":"ok" if fitted.success and np.isfinite(fitted.fun) else "nonconverged",
        "variance_components":{k:float(v) for k,v in zip(COMPONENTS,estimates)},
        "near_boundary_components":{
            k:bool(v) for k,v in zip(COMPONENTS,boundary)},
        "active_lower_box_components":{
            k:bool(v) for k,v in zip(COMPONENTS,near_box)},
        "sensor_variance_floor_applied":False,
        "restricted_negative_loglik":float(fitted.fun),
        "optimizer_iterations":int(fitted.nit),
        "optimizer_evaluations":int(fitted.nfev),
        "optimizer_success":bool(fitted.success),
        "optimizer_message":str(fitted.message),
        "maximum_absolute_logscore":float(np.max(abs(fitted.jac))),
        "reference_variance_scale_from_observed_residuals":reference,
        "working_blocks":blocks,
        "clusters":len(prepared),
        "estimated_from_observed_responses":True,
        "uses_source_gaussian_oracle":False,
        "estimated_nuisance_uncertainty_accounted_for":False,
        "component_covariance_qualified":False,
        "pointwise_coverage_qualified":False,
        "public_api_authorized":False,
    }
