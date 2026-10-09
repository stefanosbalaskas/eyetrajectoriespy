"""B6 experimental sparse Bayesian functional-factor Gibbs sampler.

This independently developed Gaussian random functional-factor model learns
the population mean and rank-K latent covariance operator on a fixed cubic
B-spline dictionary. It is a probabilistic low-rank functional-factor model,
NOT a generally calibrated Bayesian FPCA eigensystem procedure.

Y_ij = B(t_ij) @ (mu + L @ z_i) + epsilon_ij
mu_q ~ N(0, mean_prior_sd**2), L_qk ~ N(0, loading_prior_sd**2),
z_ik ~ N(0, 1), epsilon_ij ~ N(0, noise_sd**2).

All conditionals are conjugate and sampled using exact Gaussian precision
Cholesky updates. Dictionary, factor rank, scale hyperparameters, and noise
SD remain fixed. Loading columns and scores are rotation/sign unidentified:
only reconstructed functions and covariance B L L.T B.T are meaningful without
additional alignment. Chain convergence and scientific coverage are NOT
certified by running this sampler.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.interpolate import BSpline
from scipy.linalg import cho_factor, cho_solve, solve_triangular

from eyetrajectoriespy.types import IrregularTrajectorySet


@dataclass(frozen=True)
class BayesianSparseFactorFPCAFit:
    evaluation_grid: np.ndarray
    dimension: str
    population_mean_draws: np.ndarray
    population_covariance_draws: np.ndarray
    loading_function_draws: np.ndarray
    latent_score_draws: np.ndarray
    reconstructed_latent_draws: np.ndarray
    evidence: Mapping[str, Any]

    @property
    def n_chains(self) -> int:
        return self.population_mean_draws.shape[0]

    @property
    def n_draws_per_chain(self) -> int:
        return self.population_mean_draws.shape[1]

    def posterior_population_frame(self) -> pd.DataFrame:
        """Marginal posterior summaries, not calibrated confidence bands."""
        mu = self.population_mean_draws.reshape(-1, len(self.evaluation_grid))
        variance = np.diagonal(
            self.population_covariance_draws, axis1=-2, axis2=-1
        ).reshape(-1, len(self.evaluation_grid))
        return pd.DataFrame({
            "time": self.evaluation_grid.copy(),
            "mean_posterior_mean": mu.mean(axis=0),
            "mean_posterior_q05": np.quantile(mu, .05, axis=0),
            "mean_posterior_q95": np.quantile(mu, .95, axis=0),
            "latent_covariance_diagonal_mean": variance.mean(axis=0),
            "latent_covariance_diagonal_q05": np.quantile(variance, .05, axis=0),
            "latent_covariance_diagonal_q95": np.quantile(variance, .95, axis=0),
            "credible_intervals_not_scientifically_calibrated": True,
        })

    def diagnostics_frame(self) -> pd.DataFrame:
        """ArviZ Rhat/ESS/MCSE of identifiable population summaries."""
        try:
            import arviz as az
        except ImportError as exc:
            raise ImportError("Install optional eyetrajectoriespy[bayesian]") from exc
        from .evidence import bayesian_diagnostics_frame

        mu = self.population_mean_draws
        covariance = self.population_covariance_draws
        t = self.evaluation_grid
        location = trapezoid(mu, x=t, axis=-1) / (t[-1] - t[0])
        pointwise = np.diagonal(covariance, axis1=-2, axis2=-1)
        variation = trapezoid(pointwise, x=t, axis=-1)
        idata = az.from_dict(posterior={
            "population_integrated_mean": location,
            "population_integrated_covariance": variation,
        })
        return bayesian_diagnostics_frame(idata)


def _spline_basis(time: np.ndarray, start: float, stop: float, count: int) -> np.ndarray:
    normalized = (time-start)/(stop-start)
    interior = np.linspace(0, 1, count-2)[1:-1]
    knots = np.r_[np.repeat(0.0, 4), interior, np.repeat(1.0, 4)]
    basis = BSpline.design_matrix(normalized, knots, 3).toarray()
    if basis.shape != (len(time), count) or not np.isfinite(basis).all():
        raise RuntimeError("invalid cubic B-spline dictionary evaluation")
    return basis


def _draw_gaussian_precision(
    precision: np.ndarray, right: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    factor = cho_factor(precision, lower=True, check_finite=True)
    center = cho_solve(factor, right, check_finite=True)
    # If P = LL^T, L^{-T} standard-normal is covariance P^{-1}.
    jitter = solve_triangular(
        factor[0].T, rng.normal(size=len(right)), lower=False, check_finite=True
    )
    return center + jitter



def _factor_scale_log_mh_ratio(
    loading: np.ndarray, scores: np.ndarray, component: int,
    log_scale: float, loading_prior_sd: float,
) -> float:
    """Exact reversible posterior move along likelihood-invariant scale orbit.

    L[:,k] -> exp(a)L[:,k], Z[:,k] -> exp(-a)Z[:,k] leaves every
    fitted function unchanged. The Gaussian-prior ratio plus Jacobian
    (number_of_loading_rows - number_of_scores)*a is essential.
    Both B6 loading (q,k) and B7 loading (channel,q,k) are supported.
    """
    columns = np.asarray(loading).reshape(-1,loading.shape[-1])
    c=component
    load_norm=float(np.sum(columns[:,c]**2))/loading_prior_sd**2
    score_norm=float(np.sum(scores[:,c]**2))
    a=float(log_scale)
    jacobian=(len(columns)-len(scores))*a
    return float(-.5*np.expm1(2*a)*load_norm
                 -.5*np.expm1(-2*a)*score_norm + jacobian)


def _metropolis_scale_interweave(
    loading: np.ndarray, scores: np.ndarray, rng: np.random.Generator,
    proposal_sd: float, loading_prior_sd: float,
) -> int:
    """One Metropolis-Hastings attempt per loading/score factor.

    Proposal in log-scale is symmetric; likelihood cancels exactly.
    Returns number of accepted scale moves (no release qualification).
    """
    if proposal_sd==0.:
        return 0
    accepted=0
    for c in range(scores.shape[1]):
        a=float(rng.normal(scale=proposal_sd))
        ratio=_factor_scale_log_mh_ratio(loading,scores,c,a,
                                         loading_prior_sd)
        if np.log(rng.random()) < ratio:
            loading[...,c]*=np.exp(a)
            scores[:,c]*=np.exp(-a)
            accepted+=1
    return accepted



def fit_bayesian_sparse_fpca(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    evaluation_grid: np.ndarray,
    n_components: int = 1,
    n_basis: int = 5,
    noise_sd: float,
    mean_prior_sd: float = 1.0,
    loading_prior_sd: float = 0.3,
    scale_interweave_proposal_sd: float = 0.0,
    n_chains: int = 2,
    n_draws: int = 60,
    warmup: int = 90,
    thin: int = 2,
    random_state: int = 2026,
) -> BayesianSparseFactorFPCAFit:
    """Draw a learned population mean/covariance posterior for sparse curves.

    Known fixed noise SD, fixed rank and dictionary. Results must be
    interpreted through rotation-invariant population covariance or
    reconstructed curves, not individual unaligned loading/eigenfunctions.
    """
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("native IrregularTrajectorySet required")
    if dimension not in trajectories.dimension_names:
        raise ValueError("selected dimension absent from data")
    for value, name, minimum in (
        (n_components, "n_components", 1),
        (n_basis, "n_basis", 4),
        (n_chains, "n_chains", 2),
        (n_draws, "n_draws", 20),
        (warmup, "warmup", 20),
        (thin, "thin", 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if n_components > min(n_basis, trajectories.n_curves-1):
        raise ValueError("n_components exceeds finite-basis/independent-curve rank")
    if n_basis > 12:
        raise ValueError("experimental model supports n_basis <= 12")
    if trajectories.n_curves < max(8, 2*n_components+2):
        raise ValueError("at least eight independent curves required")
    if "participant_id" not in trajectories.metadata:
        raise ValueError("explicit participant_id metadata is required to establish independent units")
    participant_ids = trajectories.metadata["participant_id"]
    if participant_ids.isna().any() or (
        participant_ids.astype(str).str.strip() == ""
    ).any():
        raise ValueError("participant_id cannot be missing or blank")
    if participant_ids.astype(str).duplicated().any():
        raise ValueError("repeated participants require hierarchical latent scores")
    for sd, name in (
        (noise_sd, "noise_sd"),
        (mean_prior_sd, "mean_prior_sd"),
        (loading_prior_sd, "loading_prior_sd"),
    ):
        if not np.isfinite(sd) or sd <= 0:
            raise ValueError(f"{name} must be finite and strictly positive")
    if (not np.isscalar(scale_interweave_proposal_sd)
        or isinstance(scale_interweave_proposal_sd,bool)
        or not np.isfinite(scale_interweave_proposal_sd)
        or not 0. <= scale_interweave_proposal_sd <= 1.):
        raise ValueError("scale_interweave_proposal_sd must be finite in [0,1]")
    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1 or len(grid) < max(5, n_basis)
        or not np.isfinite(grid).all() or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError("evaluation_grid must be finite, increasing and long enough")
    channel = trajectories.dimension_names.index(dimension)
    tables, products, cross, observed_counts = [], [], [], []
    for times, data in zip(trajectories.time, trajectories.values, strict=True):
        yy = np.asarray(data[:, channel], dtype=float)
        valid = np.isfinite(yy)
        if np.isinf(yy).any() or np.count_nonzero(valid) < 4:
            raise ValueError("each curve needs >=4 finite observations and no infinities")
        t = np.asarray(times)[valid]
        if t[0] < grid[0] or t[-1] > grid[-1]:
            raise ValueError("observed times exceed declared evaluation_grid support")
        bs = _spline_basis(t, grid[0], grid[-1], n_basis)
        tables.append(bs)
        products.append(bs.T @ bs)
        cross.append(bs.T @ yy[valid])
        observed_counts.append(int(valid.sum()))
    g = _spline_basis(grid, grid[0], grid[-1], n_basis)
    n = trajectories.n_curves
    q, k = n_basis, n_components
    inv_noise = 1.0 / float(noise_sd)**2
    sum_products = np.sum(products, axis=0)
    sum_cross = np.sum(cross, axis=0)
    mean_precision = (sum_products*inv_noise
                      + np.eye(q)/float(mean_prior_sd)**2)
    total_iterations = warmup+n_draws*thin
    mu_saved = np.empty((n_chains, n_draws, len(grid)))
    cov_saved = np.empty((n_chains, n_draws, len(grid), len(grid)))
    loading_saved = np.empty((n_chains, n_draws, k, len(grid)))
    score_saved = np.empty((n_chains, n_draws, n, k))
    latent_saved = np.empty((n_chains, n_draws, n, len(grid)))
    interweave_accepted=0
    interweave_attempted=0
    seed_sequence = np.random.SeedSequence(random_state)
    for chain, chain_seed in enumerate(seed_sequence.spawn(n_chains)):
        rng = np.random.default_rng(chain_seed)
        mu = cho_solve(cho_factor(mean_precision, lower=True),
                       sum_cross*inv_noise)
        loading = rng.normal(scale=loading_prior_sd, size=(q, k))
        scores = rng.normal(size=(n, k))
        retained = 0
        for sweep in range(total_iterations):
            # Conditional posterior p(mu | L,z,Y).
            mu_rhs = sum_cross.copy()
            for gram, zi in zip(products, scores, strict=True):
                mu_rhs -= gram @ loading @ zi
            mu = _draw_gaussian_precision(mean_precision, mu_rhs*inv_noise, rng)

            # Conditional posterior p(vec(L) | mu,z,Y).
            loading_precision = np.eye(q*k)/float(loading_prior_sd)**2
            loading_rhs = np.zeros((q,k))
            for gram, xiy, zi in zip(products, cross, scores, strict=True):
                loading_precision += inv_noise*np.kron(gram, np.outer(zi,zi))
                loading_rhs += np.outer(xiy-gram @ mu, zi)
            loading = _draw_gaussian_precision(
                loading_precision, loading_rhs.ravel()*inv_noise, rng
            ).reshape(q,k)

            # Conditional posterior p(z_i | mu,L,Y_i).
            for i,(gram,xiy) in enumerate(zip(products,cross,strict=True)):
                precision = np.eye(k)+inv_noise*loading.T @ gram @ loading
                rhs = inv_noise*loading.T@(xiy-gram@mu)
                scores[i] = _draw_gaussian_precision(precision, rhs, rng)

            if scale_interweave_proposal_sd > 0:
                interweave_accepted += _metropolis_scale_interweave(
                    loading,scores,rng,scale_interweave_proposal_sd,
                    loading_prior_sd)
                interweave_attempted += k

            if sweep >= warmup and (sweep-warmup)%thin == 0:
                if retained >= n_draws:
                    raise RuntimeError("incorrect sampling retention schedule")
                population_mean = g @ mu
                projected = g @ loading
                mu_saved[chain,retained] = population_mean
                cov_saved[chain,retained] = projected@projected.T
                loading_saved[chain,retained] = projected.T
                score_saved[chain,retained] = scores
                latent_saved[chain,retained] = (
                    population_mean[None,:]+scores@projected.T
                )
                retained += 1
        if retained != n_draws:
            raise RuntimeError("posterior draw schedule did not complete")
    for values in (grid, mu_saved, cov_saved, loading_saved, score_saved, latent_saved):
        values.setflags(write=False)
    return BayesianSparseFactorFPCAFit(
        evaluation_grid=grid, dimension=dimension,
        population_mean_draws=mu_saved,
        population_covariance_draws=cov_saved,
        loading_function_draws=loading_saved,
        latent_score_draws=score_saved,
        reconstructed_latent_draws=latent_saved,
        evidence={
            "experimental": True,
            "model": "finite_Bspline_Gaussian_latent_factor_Gibbs",
            "population_mean_learned": True,
            "population_covariance_learned": True,
            "population_posterior_conditional_on_noise_rank_priors": True,
            "observation_noise_sd_estimated": False,
            "basis_rank_or_knots_learned": False,
            "orthonormal_identified_eigenfunctions_estimated": False,
            "rotation_and_sign_alignment_qualified": False,
            "posterior_covariance_invariant_to_factor_rotation": True,
            "raw_sparse_observations_resampled": False,
            "known_prior_and_likelihood": True,
            "likelihood_iid_Gaussian_observation_errors": True,
            "participant_hierarchical_effects_modelled": False,
            "n_independent_curves": n,
            "min_samples_per_curve": int(min(observed_counts)),
            "n_components": k, "n_basis": q,
            "n_chains": n_chains, "draws_per_chain": n_draws,
            "warmup": warmup, "thin": thin,
            "scale_interweave_experimental_opt_in":scale_interweave_proposal_sd>0,
            "scale_interweave_proposal_sd":float(scale_interweave_proposal_sd),
            "scale_interweave_accepted":interweave_accepted,
            "scale_interweave_attempted":interweave_attempted,
            "scale_interweave_acceptance_rate":(
                interweave_accepted/interweave_attempted
                if interweave_attempted else None),
            "scale_interweave_inferential_qualification":False,
            "chain_diagnostics_checked": False,
            "rank_SBC_and_empirical_coverage_qualified": False,
            "posterior_inference_scientifically_qualified": False,
            "release_authorized": False,
            "seed": random_state,
        },
    )
