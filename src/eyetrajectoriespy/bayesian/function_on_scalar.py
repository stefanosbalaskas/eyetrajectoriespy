"""B8 native conjugate Gaussian function-on-scalar pilot (unpublished).

Posterior regression coefficients are sampled with a *fixed and prespecified*
independent Gaussian observation noise SD, Gaussian ridge prior and cubic
B-spline time basis. Not a functional mixed model: repeated-participant,
within-curve residual autocorrelation and population noise uncertainty are
all excluded from the likelihood, not silently ignored.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import BSpline
from scipy.linalg import cho_factor, cho_solve
from eyetrajectoriespy.types import TrajectorySet
from .evidence import BayesianFunctionalDraws


@dataclass(frozen=True)
class BayesianFunctionOnScalarFit:
    predictor_names: tuple[str, ...]
    time: np.ndarray
    dimension_names: tuple[str, ...]
    posterior_coefficient_draws: np.ndarray
    posterior_mean_coefficients: np.ndarray
    fitted_mean: np.ndarray
    posterior_precision: np.ndarray
    noise_sd: float
    prior_sd: float
    evidence: Mapping[str, Any]

    def coefficient_posterior(self, name: str) -> BayesianFunctionalDraws:
        if name not in self.predictor_names:
            raise KeyError(name)
        j = self.predictor_names.index(name)
        return BayesianFunctionalDraws(
            values=self.posterior_coefficient_draws[:, j][None, :, :, :],
            time=self.time, dimension_names=self.dimension_names,
            provenance=dict(self.evidence, coefficient_name=name),
        )


def _bspline_basis(t: np.ndarray, count: int, degree: int = 3) -> np.ndarray:
    if count < degree+1 or count > len(t):
        raise ValueError("n_basis must be 4..n_time for cubic splines")
    t01 = (t-t[0]) / (t[-1]-t[0])
    interior = np.linspace(0, 1, count-degree+1)[1:-1]
    knots = np.r_[np.repeat(0.0, degree+1), interior, np.repeat(1.0, degree+1)]
    matrix = BSpline.design_matrix(t01, knots, degree).toarray()
    if matrix.shape != (len(t), count) or not np.isfinite(matrix).all():
        raise RuntimeError("invalid cubic B-spline design")
    return matrix


def fit_bayesian_function_on_scalar(
    trajectories: TrajectorySet, *,
    design: pd.DataFrame,
    predictors: Sequence[str],
    noise_sd: float,
    prior_sd: float = 2.0,
    n_basis: int = 6,
    n_draws: int = 500,
    random_state: int = 0,
) -> BayesianFunctionOnScalarFit:
    """Conjugate spline coefficient posterior conditional on known noise SD.

    Design must contain exactly one row per curve in trajectories.curve_ids
    order with a curve_id column. The user must *explicitly include* an
    intercept column if desired. Repeated participant IDs are rejected.
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("common-grid TrajectorySet required")
    if not isinstance(design, pd.DataFrame) or "curve_id" not in design:
        raise ValueError("design must be a DataFrame with curve_id")
    if design["curve_id"].astype(str).tolist() != list(trajectories.curve_ids):
        raise ValueError("design curve_id must exactly match gaze curve order")
    names = tuple(predictors)
    if not names or len(names) != len(set(names)) or any(n not in design or not isinstance(n, str) or not n for n in names):
        raise ValueError("predictors must be unique, nonempty design columns")
    if len(names) > 10:
        raise ValueError("at most ten predictors in the experimental conjugate pilot")
    if "participant_id" in trajectories.metadata and trajectories.metadata["participant_id"].astype(str).duplicated().any():
        raise ValueError("repeated participants require a Bayesian mixed model; independent-curve likelihood is not appropriate")
    values = np.asarray(trajectories.values, float)
    if not np.isfinite(values).all():
        raise ValueError("finite complete trajectories required; no hidden missing-value handling")
    x = design.loc[:, names].to_numpy(dtype=float)
    if not np.isfinite(x).all() or np.linalg.matrix_rank(x) != x.shape[1]:
        raise ValueError("finite full-rank regression design required")
    if isinstance(n_draws, bool) or not isinstance(n_draws, int) or n_draws < 20:
        raise ValueError("n_draws must be >=20")
    if isinstance(n_basis, bool) or not isinstance(n_basis, int) or n_basis < 4:
        raise ValueError("n_basis must be >=4")
    if not np.isfinite(noise_sd) or noise_sd <= 0 or not np.isfinite(prior_sd) or prior_sd <= 0:
        raise ValueError("fixed noise_sd and prior_sd must be positive finite")
    if len(trajectories.time) < n_basis:
        raise ValueError("n_basis cannot exceed observed time points")
    if trajectories.n_curves < max(8, len(names)+2):
        raise ValueError("too few independent curves")
    basis = _bspline_basis(trajectories.time, n_basis)
    forward = np.einsum("ip,tq->itpq", x, basis).reshape(
        trajectories.n_curves * len(trajectories.time), len(names) * n_basis
    )
    precision = forward.T @ forward / noise_sd**2 + np.eye(forward.shape[1]) / prior_sd**2
    factor = cho_factor(precision, lower=True)
    cov = cho_solve(factor, np.eye(precision.shape[0]))
    rhs = forward.T @ values.reshape(-1, trajectories.n_dimensions) / noise_sd**2
    posterior_mean = cho_solve(factor, rhs)
    rng = np.random.default_rng(random_state)
    coeff = np.stack([
        rng.multivariate_normal(posterior_mean[:, j], cov, size=n_draws)
        for j in range(trajectories.n_dimensions)
    ], axis=-1).reshape(n_draws, len(names), n_basis, trajectories.n_dimensions)
    beta = np.einsum("spqd,tq->sptd", coeff, basis)
    estimated = (forward @ posterior_mean).reshape(values.shape)
    return BayesianFunctionOnScalarFit(
        predictor_names=names, time=trajectories.time.copy(),
        dimension_names=trajectories.dimension_names,
        posterior_coefficient_draws=beta,
        posterior_mean_coefficients=np.einsum(
            "pqd,tq->ptd", posterior_mean.reshape(len(names), n_basis, -1), basis
        ), fitted_mean=estimated, posterior_precision=precision,
        noise_sd=float(noise_sd), prior_sd=float(prior_sd),
        evidence={
            "experimental": True,
            "model": "Gaussian_Bspline_conjugate_function_on_scalar",
            "likelihood_noise_sd_fixed_known": True,
            "prior": "iid_zero_mean_normal_basis_coefficients",
            "prior_sd": float(prior_sd), "n_basis": n_basis,
            "posterior_population_regression_coefficient_uncertainty": True,
            "observation_noise_uncertainty_included": False,
            "serial_residual_dependence_modelled": False,
            "participant_random_effects_modelled": False,
            "repeated_participants_rejected": True,
            "credible_bands_not_frequentist_calibrated": True,
            "n_draws": n_draws, "seed": random_state,
        },
    )
