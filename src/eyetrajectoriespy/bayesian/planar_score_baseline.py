"""B7 native shared-score Gaussian conditional planar benchmark.

All population mean, eigenfunctions, latent-score variances, and per-channel
observation variances are externally supplied. It handles asynchronous
coordinate-specific observations *without resampling*, but does not estimate
the joint population covariance/eigensystem or reproduce Bayesian MFPCA.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from eyetrajectoriespy.types import IrregularTrajectorySet


@dataclass(frozen=True)
class BayesianPlanarScoreBenchmark:
    posterior_score_mean: np.ndarray
    posterior_score_covariance: np.ndarray
    posterior_score_draws: np.ndarray
    latent_trajectory_draws: np.ndarray
    evaluation_grid: np.ndarray
    dimensions: tuple[str, str]
    evidence: Mapping[str, Any]


def fit_bayesian_planar_score_baseline(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    evaluation_grid: np.ndarray,
    population_mean: np.ndarray,
    population_components: np.ndarray,
    score_prior_variances: np.ndarray,
    observation_noise_sd: tuple[float, float],
    n_draws: int = 200,
    random_state: int = 0,
) -> BayesianPlanarScoreBenchmark:
    """Fixed-population shared-score posterior on paired OR asynchronous x/y.

    Each observed (curve,time,channel) value contributes one likelihood row.
    Missing values are excluded *only at explicitly unobserved coordinates*.
    The original observation times and values are not interpolated; known
    functions are evaluated linearly at their native timestamp positions.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("IrregularTrajectorySet required")
    if len(dimensions) != 2 or len(set(dimensions)) != 2 or any(d not in trajectories.dimension_names for d in dimensions):
        raise ValueError("two distinct present dimensions required")
    columns = tuple(trajectories.dimension_names.index(d) for d in dimensions)
    grid = np.asarray(evaluation_grid, dtype=float)
    mean = np.asarray(population_mean, dtype=float)
    modes = np.asarray(population_components, dtype=float)
    prior = np.asarray(score_prior_variances, dtype=float)
    noise = np.asarray(observation_noise_sd, dtype=float)
    if grid.ndim != 1 or grid.size < 3 or not np.isfinite(grid).all() or not np.all(np.diff(grid) > 0):
        raise ValueError("grid must be strictly increasing, finite and at least 3 long")
    if mean.shape != (len(grid), 2) or modes.ndim != 3 or modes.shape[1:] != (len(grid),2):
        raise ValueError("known population mean (T,2) and components (K,T,2) required")
    k = len(modes)
    if k < 1 or prior.shape != (k,) or not np.isfinite(prior).all() or (prior<=0).any():
        raise ValueError("positive fixed score variances required")
    if noise.shape != (2,) or not np.isfinite(noise).all() or (noise<=0).any():
        raise ValueError("positive fixed noise SD per channel required")
    if not np.isfinite(modes).all() or not np.isfinite(mean).all():
        raise ValueError("known population functions must be finite")
    if isinstance(n_draws,bool) or not isinstance(n_draws,int) or n_draws < 20:
        raise ValueError("n_draws must be >=20")
    rng = np.random.default_rng(random_state)
    n = trajectories.n_curves
    score_mu = np.empty((n,k))
    score_cov = np.empty((n,k,k))
    score_samples = np.empty((n,n_draws,k))
    recon = np.empty((n,n_draws,len(grid),2))
    asynchronous = False
    for i,(times, values) in enumerate(zip(trajectories.time,trajectories.values,strict=True)):
        observation = np.asarray(values[:,columns],float)
        t = np.asarray(times,float)
        if np.isinf(observation).any():
            raise ValueError("Inf is invalid, use NaN for deliberately unobserved channel")
        rows = []
        targets = []
        weights = []
        channel_times = []
        for channel in range(2):
            observed = np.isfinite(observation[:,channel])
            if observed.sum() < 2:
                raise ValueError("at least two observations required per channel and curve")
            ti=t[observed]
            if ti[0] < grid[0] or ti[-1] > grid[-1]:
                raise ValueError("observation time lies outside fixed evaluation_grid")
            basis=np.column_stack([np.interp(ti,grid,modes[j,:,channel]) for j in range(k)])
            baseline=np.interp(ti,grid,mean[:,channel])
            rows.append(basis)
            targets.append(observation[observed,channel]-baseline)
            weights.append(np.full(observed.sum(), 1.0/(noise[channel]**2)))
            channel_times.append(tuple(ti))
        asynchronous = asynchronous or (channel_times[0] != channel_times[1])
        design = np.vstack(rows)
        target = np.concatenate(targets)
        inv_diag = np.concatenate(weights)
        precision = np.diag(1/prior) + design.T @ (inv_diag[:,None]*design)
        factor=cho_factor(precision,lower=True)
        covariance=cho_solve(factor,np.eye(k))
        conditioned=cho_solve(factor,design.T@(inv_diag*target))
        samples=rng.multivariate_normal(conditioned,covariance,size=n_draws)
        score_mu[i],score_cov[i],score_samples[i]=conditioned,covariance,samples
        recon[i] = mean[None,...]+np.einsum("sk,ktd->std",samples,modes)
    return BayesianPlanarScoreBenchmark(
        posterior_score_mean=score_mu,posterior_score_covariance=score_cov,
        posterior_score_draws=score_samples,latent_trajectory_draws=recon,
        evaluation_grid=grid.copy(),dimensions=dimensions,
        evidence={
            "experimental":True,
            "model":"known_population_conditional_shared_planar_scores",
            "observation_layout":"asynchronous_per_coordinate" if asynchronous else "paired",
            "raw_observation_times_resampled":False,
            "known_basis_linear_evaluated_at_native_observation_times":True,
            "latent_shared_scores_for_x_y":True,
            "population_parameters_learned":False,
            "native_full_Bayesian_planar_MFPCA_implemented":False,
            "coordinate_noise_covariance":"diagonal_fixed",
            "n_draws":n_draws,"seed":random_state,
        },
    )
