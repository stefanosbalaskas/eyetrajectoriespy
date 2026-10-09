"""B7 experimental prediction for a NEW participant from learned planar factors.

Propagates stored population mean/loading posterior uncertainty, a fresh shared
Gaussian score per retained Gibbs draw, and declared channel-specific observation
noise. Predictions are only evaluated at EXACT recorded evaluation-grid indices;
no implicit interpolation, clock alignment, or use of fitted participant scores.
This is posterior predictive Monte Carlo, NOT validated predictive calibration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from .planar_factor_gibbs import BayesianPlanarFactorFit


@dataclass(frozen=True)
class BayesianPlanarNewParticipantPrediction:
    """Draws indexed as (chain, retained_population_draw, observation_row)."""

    row_frame: pd.DataFrame
    latent_draws: np.ndarray
    observed_draws: np.ndarray
    evidence: Mapping[str, Any]

    def summary_frame(self) -> pd.DataFrame:
        flat=self.observed_draws.reshape(-1,self.observed_draws.shape[-1])
        result=self.row_frame.copy(deep=True)
        result["predictive_mean"]=flat.mean(axis=0)
        result["predictive_q05"]=np.quantile(flat,.05,axis=0)
        result["predictive_q95"]=np.quantile(flat,.95,axis=0)
        result["predictive_interval_coverage_qualified"]=False
        return result


def _indices(values: Sequence[int], grid_length: int, name: str) -> np.ndarray:
    idx=np.asarray(values)
    if (idx.ndim!=1 or len(idx)<1 or idx.dtype.kind not in "iu" or
        (idx<0).any() or (idx>=grid_length).any() or
        len(np.unique(idx))!=len(idx)):
        raise ValueError(
            f"{name} must be distinct integer indices within evaluation_grid"
        )
    return idx.astype(int,copy=True)


def predict_bayesian_planar_new_participant(
    fitted: BayesianPlanarFactorFit,
    *,
    evaluation_indices_x: Sequence[int],
    evaluation_indices_y: Sequence[int],
    observation_noise_sd: tuple[float,float],
    random_state: int=2026,
) -> BayesianPlanarNewParticipantPrediction:
    """Predict independent NEW x/y trajectory values without train-score reuse.

    The caller supplies x/y *index arrays* into the declared evaluation grid.
    Selection by index is deliberate: none of the native observed timestamps is
    interpolated to another channel's clock. Both coordinates use the SAME
    freshly sampled subject factor within each chain/posterior iteration.
    """
    if not isinstance(fitted,BayesianPlanarFactorFit):
        raise TypeError("a learned planar factor posterior is required")
    noise=np.asarray(observation_noise_sd,dtype=float)
    if noise.shape!=(2,) or not np.isfinite(noise).all() or (noise<=0).any():
        raise ValueError("observation_noise_sd must be two positive finite values")
    g=len(fitted.evaluation_grid)
    ix=_indices(evaluation_indices_x,g,"evaluation_indices_x")
    iy=_indices(evaluation_indices_y,g,"evaluation_indices_y")
    mu=fitted.population_mean_draws
    load=fitted.loading_function_draws
    if (mu.ndim!=4 or mu.shape[-2:]!=(g,2) or
        load.ndim!=5 or load.shape[:2]!=mu.shape[:2] or
        load.shape[-2:]!=(g,2)):
        raise ValueError("inconsistent joint planar posterior draw dimensions")
    c,d=mu.shape[:2]
    k=load.shape[2]
    rng=np.random.default_rng(random_state)
    z=rng.normal(size=(c,d,k))
    indices=np.r_[ix,iy]
    coordinate=np.r_[np.zeros(len(ix),dtype=int),np.ones(len(iy),dtype=int)]
    latent=np.empty((c,d,len(indices)))
    noisy=np.empty_like(latent)
    for col,(index,channel) in enumerate(zip(indices,coordinate,strict=True)):
        mean=mu[:,:,index,channel]
        factors=load[:,:,:,index,channel]
        expected=mean+np.sum(factors*z,axis=-1)
        latent[:,:,col]=expected
        noisy[:,:,col]=expected+rng.normal(0,noise[channel],size=(c,d))
    for arr in (latent,noisy):
        arr.setflags(write=False)
    rows=pd.DataFrame({
        "observation_row":np.arange(len(indices)),
        "grid_index":indices,
        "time":fitted.evaluation_grid[indices],
        "dimension":[fitted.dimensions[int(v)] for v in coordinate],
        "channel":coordinate,
    })
    return BayesianPlanarNewParticipantPrediction(
        row_frame=rows,latent_draws=latent,observed_draws=noisy,
        evidence={
            "experimental":True,
            "new_independent_participant":True,
            "training_participant_scores_used":False,
            "shared_new_subject_scores_across_xy":True,
            "population_mean_and_loading_uncertainty_propagated":True,
            "channel_specific_observation_noise_declared":True,
            "prediction_times_are_exact_grid_indices":True,
            "clock_alignment_or_interpolation":False,
            "pointwise_predictive_calibration_qualified":False,
            "simultaneous_functional_predictive_coverage_qualified":False,
            "n_population_draws":int(c*d),
            "n_observation_rows":len(indices),
            "seed":random_state,
        },
    )
