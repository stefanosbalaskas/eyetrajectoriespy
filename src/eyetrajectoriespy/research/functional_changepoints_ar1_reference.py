"""Research-only F5 stationary scalar-AR(1) functional null comparator.

This is a deliberately separate experimental procedure, NOT a corrected
replacement for the previously unqualified weak-block bootstrap. Its
coefficient must come from known experimental truth or independently
validated/held-out baseline observations. Fitting phi on the test data and
then reporting nominal-size calibrated p-values is NOT supported.

X_i(t) - mu(t) = phi * [X_(i-1)(t) - mu(t)] + E_i(t),
E_i are iid *whole-function* innovations; scalar phi shared across channels.
Innovation-vector permutation preserves empirical contemporaneous geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from eyetrajectoriespy.types import TrajectorySet
from .functional_changepoints import FunctionalChangepointResult


def estimate_scalar_functional_ar1(trajectories: TrajectorySet) -> dict[str, Any]:
    """Descriptive pooled functional OLS phi: not a calibrated nuisance estimate.

    The finite-sample fit is generally downward biased when estimating the
    mean and can make naive null bootstrapping seriously anti-conservative.
    Returned phi is not automatically accepted by the inferential API.
    """
    x=_array(trajectories)
    centered=x-x.mean(axis=0)
    den=float(np.sum(centered[:-1]**2))
    if den<1.e-12:
        raise ValueError("not enough lagged trajectory variation to estimate phi")
    estimate=float(np.sum(centered[1:]*centered[:-1])/den)
    return {
        "ar1_coefficient_pooled_descriptive": estimate,
        "n_ordered_curves": len(x),
        "independent_baseline_or_oracle_coefficient_required_for_inference": True,
        "finite_sample_bias_not_qualified": True,
        "science_inference_qualified": False,
    }


def _array(trajectories: TrajectorySet) -> np.ndarray:
    if not isinstance(trajectories,TrajectorySet):
        raise TypeError("requires common-grid native TrajectorySet")
    x=np.asarray(trajectories.values,dtype=float)
    if x.ndim!=3 or len(x)<12 or not np.isfinite(x).all():
        raise ValueError("need at least 12 ordered finite common-grid curves")
    t=np.asarray(trajectories.time,dtype=float)
    if t.ndim!=1 or len(t)!=x.shape[1] or len(t)<3 or not np.all(np.diff(t)>0):
        raise ValueError("invalid strictly increasing time grid")
    if "participant_id" in trajectories.metadata:
        ids=trajectories.metadata["participant_id"]
        if ids.isna().any() or ids.astype(str).duplicated().any():
            raise ValueError("repeated/missing participant IDs require separate hierarchy")
    return x


def infer_ordered_functional_changepoint_ar1_reference(
    trajectories: TrajectorySet,
    *, ar1_coefficient_from_independent_baseline: float,
    n_bootstrap: int = 499,
    min_segment: int = 6,
    random_state: int = 2026,
) -> FunctionalChangepointResult:
    """Experimental AR(1) *externally-specified* null via permuted innovations.

    Requires prespecified, independently verified scalar-AR1 dependence.
    `ar1_coefficient_from_independent_baseline` may be the known true phi
    for synthetic model checks; no automatic in-sample phi selection.
    Bootstrap initial state is drawn from centered observed curves.
    The held-out baseline and test sequences must share dependence law.
    Residual innovations are permuted (not resampled with replacement).
    Outputs are model-conditional exploratory p-values, NOT qualified tests.
    """
    x=_array(trajectories)
    phi=ar1_coefficient_from_independent_baseline
    if (isinstance(phi,bool) or not np.isscalar(phi) or
        not np.isfinite(phi) or not (-.98<phi<.98)):
        raise ValueError("independent baseline scalar AR1 phi must be finite in (-.98,.98)")
    if (isinstance(n_bootstrap,bool) or not isinstance(n_bootstrap,int)
        or n_bootstrap<99):
        raise ValueError("at least 99 bootstrap permutations are required")
    if (isinstance(min_segment,bool) or not isinstance(min_segment,int)
        or min_segment<3 or len(x)<2*min_segment):
        raise ValueError("valid >=3 points per segment required")
    if isinstance(random_state,bool) or not isinstance(random_state,int):
        raise ValueError("random_state must be integer")

    n=len(x)
    split=np.arange(min_segment,n-min_segment+1)
    scale=np.sqrt(split*(n-split)/n)
    time=np.asarray(trajectories.time)
    def score(curves:np.ndarray)->np.ndarray:
        sums=np.cumsum(curves,axis=0)
        left=sums[split-1]/split[:,None,None]
        right=(sums[-1]-sums[split-1])/(n-split)[:,None,None]
        integral=trapezoid((left-right)**2,x=time,axis=1).sum(axis=1)
        return scale*np.sqrt(np.maximum(integral,0.))

    observed=score(x)
    mean=x.mean(axis=0)
    centered=x-mean
    residuals=centered[1:]-float(phi)*centered[:-1]
    residuals-=residuals.mean(axis=0)
    rng=np.random.default_rng(random_state)
    null=np.empty(n_bootstrap,float)
    for b in range(n_bootstrap):
        # Each bootstrap receives precisely one permutation of the observed
        # n-1 whole-curve innovation vectors. No within-function shuffling.
        permutation=rng.permutation(n-1)
        prior=centered[int(rng.integers(n))].copy()
        sampled=np.empty_like(x)
        sampled[0]=prior
        for i,j in enumerate(permutation,start=1):
            prior=phi*prior+residuals[j]
            sampled[i]=prior
        null[b]=float(score(sampled).max())
    if not np.isfinite(null).all():
        raise RuntimeError("AR1 innovation permutation generated nonfinite null")
    p=float((1+np.count_nonzero(null>=observed.max()))/(n_bootstrap+1))
    return FunctionalChangepointResult(
        split_index=int(split[np.argmax(observed)]),
        statistic=float(observed.max()),
        scan=pd.DataFrame({"split_index":split,"cusum_norm":observed}),
        null_statistics=null,
        p_value_experimental=p,
        evidence={
            "experimental":True,
            "model":"scalar_stationary_functional_AR1_with_iid_whole_curve_innovations",
            "ar1_coefficient_from_independent_baseline":float(phi),
            "coefficient_estimated_on_test_series":False,
            "separate_from_unqualified_weak_block_method":True,
            "bootstrap_type":"whole_curve_innovation_permutation_conditional_on_external_phi",
            "n_bootstrap":n_bootstrap,
            "sample_size":n,
            "n_unique_participants_required":True,
            "missingness_or_hierarchical_effects_modelled":False,
            "non_AR1_dependence_qualified":False,
            "finite_sample_null_calibration_qualified":False,
            "scientific_inference_qualified":False,
            "release_authorized":False,
        },
    )
