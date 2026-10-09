"""Experimental F5 independent-baseline AR(1) change-point null.

The nuisance AR(1) parameter and whole-curve innovations are fitted ONLY
from a separately supplied stationary baseline of distinct participants.
The change-point test series is not used to estimate nuisance dependence
or the empirical innovation distribution. Two nested simulation layers
approximate baseline parameter-estimation uncertainty and the null scan.

This is NOT a calibrated test of generic serial dependence, nor an
automatic replacement for any existing F5 API.
"""
from __future__ import annotations

from typing import Any
import numpy as np
from scipy.integrate import trapezoid
import pandas as pd

from eyetrajectoriespy.types import TrajectorySet
from .functional_changepoints import FunctionalChangepointResult
from .functional_changepoints_ar1_reference import _array


def _baseline_phi_ols(x: np.ndarray) -> float:
    centered=x-x.mean(axis=0,keepdims=True)
    denominator=float(np.sum(centered[:-1]**2))
    if not np.isfinite(denominator) or denominator<1.e-12:
        raise ValueError("independent baseline lacks lagged variation")
    return float(np.sum(centered[:-1]*centered[1:])/denominator)


def _check_independent_baseline(
    tested: TrajectorySet, baseline: TrajectorySet,
) -> tuple[np.ndarray,np.ndarray]:
    a=_array(tested)
    b=_array(baseline)
    if len(b)<24:
        raise ValueError("independent baseline needs at least 24 ordered curves")
    if a.shape[1:]!=b.shape[1:]:
        raise ValueError("independent baseline must have same grid and dimensions")
    if not np.allclose(tested.time,baseline.time,rtol=0,atol=1.e-12):
        raise ValueError("independent baseline grid must match test series")
    if tuple(tested.dimension_names)!=tuple(baseline.dimension_names):
        raise ValueError("independent baseline dimension order must match")
    for data in (tested,baseline):
        if "participant_id" not in data.metadata:
            raise ValueError("independent baseline requires explicit participant_id")
        ids=data.metadata["participant_id"]
        if (ids.isna().any() or ids.astype(str).duplicated().any()
            or len(ids)!=data.n_curves):
            raise ValueError("baseline and tested series need distinct unique participant_id")
    lhs=set(tested.metadata["participant_id"].astype(str))
    rhs=set(baseline.metadata["participant_id"].astype(str))
    if lhs.intersection(rhs):
        raise ValueError("baseline participant_id must be disjoint from tested participants")
    return a,b


def infer_ordered_functional_changepoint_baseline_ar1(
    trajectories: TrajectorySet,
    *, independent_stationary_baseline: TrajectorySet,
    n_null_simulations: int = 499,
    n_parameter_bootstrap: int = 199,
    min_segment: int = 6,
    random_state: int = 2026,
    null_coefficient_policy: str = "baseline_uncertainty",
) -> FunctionalChangepointResult:
    """Exploratory unknown-phi AR1 inference from disjoint stationary baseline.

    Baseline phi and whole-function innovations are estimated without
    examining the test-series residuals. The baseline parametric bootstrap
    estimates finite-baseline bias and variance of pooled scalar phi.
    Every simulated null trajectory samples one phi from its uncertainty
    distribution and resamples whole-curve stationary baseline innovations.

    Approximate empirical Bayes/parametric-bootstrap uncertainty is not a
    calibrated confidence distribution. The baseline must be independent,
    unchanging, and representative of the test-series nuisance process.

    The research-only 'baseline_plugin' mode removes phi uncertainty and
    bias correction from null simulations, using the same baseline-only
    OLS coefficient and innovations. It is a diagnostic ablation, never
    a calibrated inferential alternative. Default behaviour is unchanged.
    """
    if null_coefficient_policy not in ("baseline_uncertainty", "baseline_plugin"):
        raise ValueError("research coefficient policy must be baseline_uncertainty or baseline_plugin")
    x,b=_check_independent_baseline(trajectories,independent_stationary_baseline)
    if (isinstance(n_null_simulations,bool) or
        not isinstance(n_null_simulations,int) or n_null_simulations<99):
        raise ValueError("n_null_simulations must be an integer >=99")
    if (isinstance(n_parameter_bootstrap,bool) or
        not isinstance(n_parameter_bootstrap,int) or n_parameter_bootstrap<99):
        raise ValueError("n_parameter_bootstrap must be an integer >=99")
    if (isinstance(min_segment,bool) or not isinstance(min_segment,int)
        or min_segment<3 or len(x)<2*min_segment):
        raise ValueError("invalid min_segment for ordered sample")
    if isinstance(random_state,bool) or not isinstance(random_state,int):
        raise ValueError("random_state must be integer")

    phi_hat=_baseline_phi_ols(b)
    if not np.isfinite(phi_hat) or abs(phi_hat)>=.98:
        raise ValueError("baseline estimated nonstationary or near-unit-root dependence")
    baseline_centered=b-b.mean(axis=0,keepdims=True)
    innovation=baseline_centered[1:]-phi_hat*baseline_centered[:-1]
    innovation=innovation-innovation.mean(axis=0,keepdims=True)
    rng=np.random.default_rng(random_state)
    n_baseline=len(b)
    n=len(x)
    boot_phi=np.empty(n_parameter_bootstrap,float)
    # Nested baseline-only nuisance bootstrap: simulate independent stationary
    # baselines and re-fit phi on EVERY replicate, never on tested data.
    for j in range(n_parameter_bootstrap):
        ref=np.empty_like(b)
        ref[0]=baseline_centered[int(rng.integers(n_baseline))]
        innovation_indices=rng.integers(len(innovation),size=n_baseline-1)
        for i,z in enumerate(innovation_indices,start=1):
            ref[i]=phi_hat*ref[i-1]+innovation[z]
        boot_phi[j]=_baseline_phi_ols(ref)
    bias=float(boot_phi.mean()-phi_hat)
    center=float(np.clip(phi_hat-bias,-.97,.97))
    parameter_draws=np.clip(center+(boot_phi-boot_phi.mean()),-.97,.97)
    phi_quantiles=np.quantile(parameter_draws,[.025,.5,.975])

    split=np.arange(min_segment,n-min_segment+1)
    scale=np.sqrt(split*(n-split)/n)
    t=np.asarray(trajectories.time)
    def scan(z:np.ndarray)->np.ndarray:
        cum=np.cumsum(z,axis=0)
        mleft=cum[split-1]/split[:,None,None]
        mright=(cum[-1]-cum[split-1])/(n-split)[:,None,None]
        sq=trapezoid((mleft-mright)**2,x=t,axis=1).sum(axis=1)
        return scale*np.sqrt(np.maximum(sq,0.))

    observed=scan(x)
    null=np.empty(n_null_simulations,float)
    for j in range(n_null_simulations):
        # Explicit nuisance ablation: same independent baseline and null model.
        # Do not interpret the plug-in mode as validated inference.
        phi=(float(parameter_draws[int(rng.integers(n_parameter_bootstrap))])
             if null_coefficient_policy=="baseline_uncertainty" else float(phi_hat))
        initial=baseline_centered[int(rng.integers(n_baseline))]
        sample=np.empty_like(x)
        sample[0]=initial
        indices=rng.integers(len(innovation),size=n-1)
        for i,z in enumerate(indices,start=1):
            initial=phi*initial+innovation[z]
            sample[i]=initial
        null[j]=float(scan(sample).max())
    if not np.isfinite(null).all():
        raise RuntimeError("nonfinite independent-baseline AR1 null simulation")
    p=float((1+np.count_nonzero(null>=observed.max()))/(n_null_simulations+1))
    return FunctionalChangepointResult(
        split_index=int(split[np.argmax(observed)]),
        statistic=float(observed.max()),
        scan=pd.DataFrame({"split_index":split,"cusum_norm":observed}),
        null_statistics=null,
        p_value_experimental=p,
        evidence={
            "model":"external_stationary_scalar_functional_AR1",
            "experimental":True,
            "independent_baseline_required_and_checked":True,
            "participant_ids_disjoint_checked":True,
            "parameter_fitted_on_test_series":False,
            "innovation_samples_from_test_series":False,
            "unknown_phi_not_oracle":True,
            "null_coefficient_policy":null_coefficient_policy,
            "plugin_is_unqualified_nuisance_ablation":null_coefficient_policy=="baseline_plugin",
            "baseline_n_ordered_curves":n_baseline,
            "test_n_ordered_curves":n,
            "baseline_pooled_phi_ols":float(phi_hat),
            "baseline_bootstrap_phi_bias":bias,
            "bias_corrected_phi":center,
            "approximate_phi_uncertainty_quantiles_025_50_975":[
                float(v) for v in phi_quantiles],
            "phi_bootstrap_draws":n_parameter_bootstrap,
            "null_simulations":n_null_simulations,
            "whole_function_innovation_resampling":True,
            "single_shared_scalar_phi_across_time_and_channels":True,
            "assumes_stationary_iid_innovation_vectors":True,
            "estimated_phi_sampling_distribution_is_not_a_validated_confidence_posterior":True,
            "non_AR1_dependence_qualified":False,
            "baseline_transferability_qualified":False,
            "hierarchical_repeated_participants_supported":False,
            "nominal_false_positive_calibration_qualified":False,
            "scientific_inference_qualified":False,
            "release_authorized":False,
        },
    )
