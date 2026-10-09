"""B10 experimental single-break change posterior of a DECLARED scalar projection.

This deliberately does not implement a general Bayesian functional change-point
model. It integrates unknown Gaussian segment means under known scalar noise
SD and a declared one-break prior. The functional projection is fixed before
inspection. Serial dependence, multiple breaks, projection selection and
population functional covariance are NOT inferred.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.special import expit, logsumexp
from eyetrajectoriespy.types import TrajectorySet


@dataclass(frozen=True)
class BayesianFunctionalChangepointPilot:
    projected_trial_scores: np.ndarray
    split_posterior: pd.DataFrame
    posterior_probability_one_break: float
    posterior_probability_no_break: float
    conditional_map_split_index: int
    evidence: Mapping[str, Any]


def fit_bayesian_functional_changepoints(
    trajectories: TrajectorySet, *,
    functional_projection: np.ndarray,
    observation_noise_sd: float,
    segment_mean_prior_sd: float,
    prior_probability_one_break: float = .5,
    min_segment: int = 5,
) -> BayesianFunctionalChangepointPilot:
    """Compare no-break against one-break projected independent Gaussian means.

    Projection is a fully analyst-declared functional direction on the
    common grid; it is normalized in the trapezoid L2 norm. No projection
    selection from the observed sequence is performed. Under each segment
    the unknown scalar mean has Normal(0, segment_mean_prior_sd**2) prior,
    with fixed residual Normal(0, observation_noise_sd**2).
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("common-grid functional trajectories required")
    y=np.asarray(trajectories.values,dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("finite observations required: no hidden imputation")
    if "participant_id" in trajectories.metadata and trajectories.metadata["participant_id"].astype(str).duplicated().any():
        raise ValueError("repeated participants require hierarchical/dependent change point model")
    proj=np.asarray(functional_projection,dtype=float)
    if proj.shape != y.shape[1:] or not np.isfinite(proj).all():
        raise ValueError("projection must match (time,dimensions) and be finite")
    norm2=float(np.sum(trapezoid(proj**2,x=trajectories.time,axis=0)))
    if norm2<=1e-14:
        raise ValueError("functional_projection has zero integrated norm")
    if any(not np.isfinite(v) or v<=0 for v in (observation_noise_sd,segment_mean_prior_sd)):
        raise ValueError("noise and segment prior standard deviations must be positive")
    if isinstance(min_segment,bool) or not isinstance(min_segment,int) or min_segment<3 or len(y)<2*min_segment:
        raise ValueError("invalid minimum segment or insufficient ordered trials")
    if not np.isfinite(prior_probability_one_break) or not 0<prior_probability_one_break<1:
        raise ValueError("prior_probability_one_break must be strictly between zero and one")
    projection=proj/np.sqrt(norm2)
    z=np.sum(trapezoid(y*projection[None,:,:],x=trajectories.time,axis=1),axis=1)
    n=len(z)
    sigma2=float(observation_noise_sd)**2
    tau2=float(segment_mean_prior_sd)**2
    def log_marginal(segment: np.ndarray) -> float:
        m=len(segment)
        sumz=float(segment.sum())
        quad=float(np.dot(segment,segment))/sigma2
        quad-=sumz**2/sigma2**2/(1/tau2 + m/sigma2)
        logdet=m*np.log(sigma2) + np.log1p(m*tau2/sigma2)
        return float(-.5*(m*np.log(2*np.pi)+logdet+max(0.,quad)))
    no_break=log_marginal(z)
    splits=np.arange(min_segment,n-min_segment+1)
    log_each=np.asarray([
        log_marginal(z[:s])+log_marginal(z[s:]) for s in splits
    ])
    log_one=logsumexp(log_each)-np.log(len(splits))
    logodds=np.log(prior_probability_one_break/(1-prior_probability_one_break))
    p_one=float(expit(logodds + log_one - no_break))
    conditional=np.exp(log_each-logsumexp(log_each))
    frame=pd.DataFrame({
        "split_index":splits,
        "posterior_split_given_exactly_one_break":conditional,
        "posterior_split_unconditional":conditional*p_one,
    })
    return BayesianFunctionalChangepointPilot(
        projected_trial_scores=z,
        split_posterior=frame,
        posterior_probability_one_break=p_one,
        posterior_probability_no_break=1-p_one,
        conditional_map_split_index=int(splits[np.argmax(conditional)]),
        evidence={
            "experimental":True,
            "model":"fixed_projection_single_break_conjugate_Gaussian_scalar_scores",
            "functional_projection_selected_from_data":False,
            "projection_L2_normalized":True,
            "likelihood_noise_sd_fixed":True,
            "segment_means_integrated_out_analytically":True,
            "multiple_changes_modelled":False,
            "serial_trial_dependence_modelled":False,
            "full_functional_changepoint_posterior_implemented":False,
            "change_location_calibration_qualified":False,
            "posterior_probability_not_frequentist_p_value":True,
        },
    )
