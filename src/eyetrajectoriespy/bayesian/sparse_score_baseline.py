"""B6 conditioning benchmark: exact Gaussian sparse score posterior, not FPCA.

Population mean curves, basis eigenfunctions and prior score variances are
supplied as KNOWN quantities. The procedure estimates none of them and has
no full-population Bayesian uncertainty. It is an analytic reference for B6
model verification and contrasts with frozen/native PACE conditional scoring.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from eyetrajectoriespy.types import IrregularTrajectorySet


@dataclass(frozen=True)
class BayesianSparseScoreBenchmark:
    posterior_score_mean: np.ndarray
    posterior_score_covariance: np.ndarray
    posterior_score_draws: np.ndarray
    conditional_latent_trajectory_draws: np.ndarray
    evaluation_grid: np.ndarray
    dimension: str
    evidence: Mapping[str, Any]


def fit_bayesian_sparse_score_baseline(
    trajectories: IrregularTrajectorySet, *,
    dimension: str,
    evaluation_grid: np.ndarray,
    population_mean: np.ndarray,
    population_components: np.ndarray,
    score_prior_variances: np.ndarray,
    noise_sd: float,
    n_draws: int = 200,
    random_state: int = 0,
) -> BayesianSparseScoreBenchmark:
    """Conjugate posterior for subject scores given fixed population functions.

    Eigenbasis components (K,T) and mean (T,) are **externally supplied** on
    evaluation_grid. Per-subject irregular observations are mapped onto the
    *fixed known basis* by linear evaluation. Neither observation resampling
    nor covariance/eigensystem estimation occurs.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("requires irregular native trajectories")
    if dimension not in trajectories.dimension_names:
        raise ValueError("dimension must match observed data")
    j = trajectories.dimension_names.index(dimension)
    grid = np.asarray(evaluation_grid, dtype=float)
    mean = np.asarray(population_mean, dtype=float)
    components = np.asarray(population_components, dtype=float)
    prior = np.asarray(score_prior_variances, dtype=float)
    if grid.ndim != 1 or len(grid) < 3 or not np.isfinite(grid).all() or not np.all(np.diff(grid) > 0):
        raise ValueError("finite strictly increasing evaluation_grid required")
    if mean.shape != (len(grid),) or components.ndim != 2 or components.shape[1] != len(grid):
        raise ValueError("mean (T,) and known components (K,T) must align to grid")
    k = len(components)
    if not k or prior.shape != (k,) or not np.isfinite(prior).all() or np.any(prior <= 0):
        raise ValueError("positive prior score variances required for every component")
    if not np.isfinite(components).all() or not np.isfinite(mean).all():
        raise ValueError("fixed population functions must be finite")
    if not np.isfinite(noise_sd) or noise_sd <= 0 or isinstance(n_draws, bool) or not isinstance(n_draws, int) or n_draws < 20:
        raise ValueError("noise_sd positive and n_draws >= 20 required")
    rng = np.random.default_rng(random_state)
    n = trajectories.n_curves
    means = np.empty((n, k))
    covs = np.empty((n, k, k))
    posterior = np.empty((n, n_draws, k))
    latents = np.empty((n, n_draws, len(grid)))
    for i, (times, values) in enumerate(zip(trajectories.time, trajectories.values, strict=True)):
        observed = np.asarray(values[:, j], dtype=float)
        times = np.asarray(times, dtype=float)
        valid = np.isfinite(observed)
        if not np.isfinite(times).all() or np.any(times[valid] < grid[0]) or np.any(times[valid] > grid[-1]):
            raise ValueError("observation times must fall inside declared population grid")
        if np.count_nonzero(valid) < 2:
            raise ValueError("each curve needs at least two finite observations")
        ti = times[valid]
        design = np.column_stack([np.interp(ti, grid, phi) for phi in components])
        baseline = np.interp(ti, grid, mean)
        precision = np.diag(1.0/prior) + (design.T @ design) / noise_sd**2
        factor = cho_factor(precision, lower=True, check_finite=True)
        cov = cho_solve(factor, np.eye(k))
        mu = cho_solve(factor, design.T @ (observed[valid] - baseline) / noise_sd**2)
        draws = rng.multivariate_normal(mu, cov, size=n_draws)
        means[i], covs[i], posterior[i] = mu, cov, draws
        latents[i] = mean + draws @ components
    return BayesianSparseScoreBenchmark(
        posterior_score_mean=means, posterior_score_covariance=covs,
        posterior_score_draws=posterior,
        conditional_latent_trajectory_draws=latents,
        evaluation_grid=grid.copy(), dimension=dimension,
        evidence={
            "experimental": True, "baseline": "known_population_gaussian_score_posterior",
            "mean_components_prior_and_noise_all_fixed": True,
            "functional_eigenfunctions_estimated": False,
            "population_parameter_uncertainty": False,
            "interpolation": "linear_basis_evaluation_at_native_irregular_times",
            "observed_series_resampled": False,
            "full_native_bayesian_fpca_implemented": False,
            "n_draws": n_draws, "seed": random_state,
        },
    )
