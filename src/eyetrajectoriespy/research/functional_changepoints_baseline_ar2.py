"""Research-only F5 independent-baseline scalar AR(2) null reference.

Unknown AR(2) coefficients and whole-functional innovations are learned
ONLY from disjoint stationary baseline participants. A nuisance bootstrap
re-fits BOTH coefficients, propagates estimation variation to null
trajectories, and retains stationarity failures. This is model-conditional,
not valid generic unknown-dependence inference or a promoted release API.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from eyetrajectoriespy.types import TrajectorySet
from .functional_changepoints import FunctionalChangepointResult
from .functional_changepoints_baseline_ar1 import _check_independent_baseline


def _ar2_coefficients(x: np.ndarray) -> np.ndarray:
    """Pooled least-squares lag regression over whole-curve vectors."""
    v=np.asarray(x,float)
    centered=v-v.mean(axis=0,keepdims=True)
    lag=np.stack([centered[1:-1].reshape(-1),centered[:-2].reshape(-1)],axis=1)
    y=centered[2:].reshape(-1)
    if len(v)<24 or not np.isfinite(lag).all() or not np.isfinite(y).all():
        raise ValueError("at least 24 independent finite baseline curves required")
    if np.linalg.matrix_rank(lag)<2:
        raise ValueError("baseline has rank-deficient AR2 lag design")
    beta=np.linalg.lstsq(lag,y,rcond=None)[0]
    if not np.isfinite(beta).all():
        raise ValueError("nonfinite estimated AR2 coefficients")
    return beta


def _stationary(phi:np.ndarray,threshold:float=.995)->bool:
    """Root condition on AR(2) companion eigenvalues, not size tuning."""
    p=np.asarray(phi,dtype=float)
    if p.shape!=(2,) or not np.isfinite(p).all():
        return False
    roots=np.linalg.eigvals(np.asarray([[p[0],p[1]],[1.,0.]]))
    return bool(np.max(np.abs(roots))<threshold)


def _simulate(
    baseline_centered:np.ndarray, innovation:np.ndarray,
    phi:np.ndarray,n:int,rng:np.random.Generator,
)->np.ndarray:
    if n<3 or not _stationary(phi):
        raise ValueError("simulated AR2 null must be stationary with >=3 curves")
    out=np.empty((n,*baseline_centered.shape[1:]),float)
    first=int(rng.integers(len(baseline_centered)-1))
    out[:2]=baseline_centered[first:first+2]
    ii=rng.integers(len(innovation),size=n-2)
    for j,z in enumerate(ii,start=2):
        out[j]=phi[0]*out[j-1]+phi[1]*out[j-2]+innovation[z]
    return out


def infer_ordered_functional_changepoint_baseline_ar2(
    trajectories:TrajectorySet,
    *,independent_stationary_baseline:TrajectorySet,
    n_null_simulations:int=499,n_parameter_bootstrap:int=199,
    min_segment:int=6,random_state:int=2026,
)->FunctionalChangepointResult:
    """Experimental AR2 reference with two uncertain externally trained lags.

    This method assumes a shared stationary scalar AR(2) law over all
    coordinate/time dimensions and iid innovation *function vectors*.
    No test-series nuisance estimates, p-value tuning or AR order
    selection are permitted. Stability filters discard nonstationary
    nuisance-bootstrap coefficients and record the discard fraction;
    the resulting conditional bootstrap is NOT calibrated.
    """
    x,b=_check_independent_baseline(trajectories,independent_stationary_baseline)
    if (not isinstance(n_null_simulations,int)
        or isinstance(n_null_simulations,bool) or n_null_simulations<99
        or not isinstance(n_parameter_bootstrap,int)
        or isinstance(n_parameter_bootstrap,bool) or n_parameter_bootstrap<99):
        raise ValueError("at least 99 integer null and parameter-bootstrap draws required")
    if (not isinstance(min_segment,int) or isinstance(min_segment,bool)
        or min_segment<3 or 2*min_segment>len(x)):
        raise ValueError("invalid change-point segment boundaries")
    if not isinstance(random_state,int) or isinstance(random_state,bool):
        raise ValueError("random_state must be integer")
    phi=_ar2_coefficients(b)
    if not _stationary(phi):
        raise ValueError("independent baseline fitted nonstationary AR2 law")
    centered=b-b.mean(axis=0,keepdims=True)
    eps=centered[2:]-phi[0]*centered[1:-1]-phi[1]*centered[:-2]
    eps-=eps.mean(axis=0,keepdims=True)
    if not np.isfinite(eps).all():
        raise ValueError("invalid baseline AR2 innovations")
    rng=np.random.default_rng(random_state)
    estimates=np.empty((n_parameter_bootstrap,2),float)
    for j in range(n_parameter_bootstrap):
        boot=_simulate(centered,eps,phi,len(b),rng)
        estimates[j]=_ar2_coefficients(boot)
    bias=estimates.mean(axis=0)-phi
    # Bootstrap-centred nuisance coefficient distribution (bias-adjusted
    # point + refit-centred deviations). Stability is an explicit
    # *assumption boundary*, not a p-value correction.
    candidate=phi-bias+(estimates-estimates.mean(axis=0))
    valid=np.asarray([_stationary(p) for p in candidate])
    n_unstable=int(np.count_nonzero(~valid))
    if valid.sum()<max(70,int(.7*n_parameter_bootstrap)):
        raise RuntimeError("too many estimated nuisance laws are nonstationary")
    draws=candidate[valid]
    n=len(x)
    split=np.arange(min_segment,n-min_segment+1)
    scale=np.sqrt(split*(n-split)/n)
    t=np.asarray(trajectories.time)
    def scan(z):
        cumulative=np.cumsum(z,axis=0)
        left=cumulative[split-1]/split[:,None,None]
        right=(cumulative[-1]-cumulative[split-1])/(n-split)[:,None,None]
        integral=trapezoid((left-right)**2,x=t,axis=1).sum(axis=1)
        return scale*np.sqrt(np.maximum(integral,0.))
    observed=scan(x)
    null=np.empty(n_null_simulations,float)
    for i in range(n_null_simulations):
        coefficient=draws[int(rng.integers(len(draws)))]
        null[i]=float(scan(_simulate(centered,eps,coefficient,n,rng)).max())
    if not np.isfinite(null).all():
        raise ValueError("nonfinite AR2 null distribution")
    return FunctionalChangepointResult(
        split_index=int(split[np.argmax(observed)]),
        statistic=float(observed.max()),
        scan=pd.DataFrame({"split_index":split,"cusum_norm":observed}),
        null_statistics=null,
        p_value_experimental=float((1+np.count_nonzero(null>=observed.max()))/(n_null_simulations+1)),
        evidence={
            "model":"independently_estimated_stationary_scalar_AR2_whole_functional_innovations",
            "experimental":True,
            "baseline_and_test_independent_disjoint_participants_checked":True,
            "nuisance_estimated_from_test_series":False,
            "model_order_predeclared_not_selected_from_test":True,
            "estimated_ar2_coefficient":[float(v) for v in phi],
            "bootstrap_ar2_coefficient_bias":[float(v) for v in bias],
            "n_parameter_bootstrap":n_parameter_bootstrap,
            "n_parameter_draws_rejected_nonstationary":n_unstable,
            "n_valid_parameter_draws":len(draws),
            "n_baseline":len(b),"n_test":n,
            "n_null_simulations":n_null_simulations,
            "bootstrapped_nuisance_is_not_validated_confidence_distribution":True,
            "stationarity_and_shared_scalar_AR2_assumed":True,
            "non_AR2_or_nonstationary_processes_qualified":False,
            "hierarchical_participant_data_qualified":False,
            "unknown_dependence_inference_qualified":False,
            "scientific_inference_qualified":False,
            "release_authorized":False,
        },
    )
