"""Private validation metrics for native sparse FPCA/PACE."""

from __future__ import annotations

from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment

import numpy as np

from ._sparse_truth import SparseFunctionalTruth
from .fpca import functional_trapezoid_weights
from .types import SparseFPCAResult


@dataclass(frozen=True)
class SparseRecoveryMetrics:
    """Invariant-aware recovery metrics for one fitted sparse-FPCA result."""

    mean_ise: float
    covariance_ise: float
    eigenvalue_relative_error: np.ndarray
    component_absolute_similarity: np.ndarray
    subspace_principal_cosines: np.ndarray
    score_correlation: np.ndarray
    score_rmse: np.ndarray
    score_failure_rate: float
    matched_truth_components: np.ndarray
    alignment_signs: np.ndarray


def _normalized_functions(
    functions: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    matrix = np.asarray(functions, dtype=float)
    norms = np.sqrt(np.sum(matrix**2 * weights[None, :], axis=1))
    if np.any(~np.isfinite(norms)) or np.any(norms <= 0):
        raise ValueError("functional basis contains an invalid weighted norm")
    return matrix / norms[:, None]


def _principal_cosines(
    estimated: np.ndarray,
    truth: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    sqrt_weights = np.sqrt(weights)
    estimated_weighted = estimated.T * sqrt_weights[:, None]
    truth_weighted = truth.T * sqrt_weights[:, None]
    estimated_q, _ = np.linalg.qr(estimated_weighted)
    truth_q, _ = np.linalg.qr(truth_weighted)
    return np.linalg.svd(
        estimated_q.T @ truth_q,
        compute_uv=False,
    )


def evaluate_sparse_truth_recovery(
    result: SparseFPCAResult,
    truth: SparseFunctionalTruth,
) -> SparseRecoveryMetrics:
    """Evaluate one native sparse fit against known latent truth.

    Individual components are matched by maximum absolute weighted functional
    similarity. Subspace cosines are additionally retained because individual
    eigenfunctions are not identifiable under tied or nearly tied eigenvalues.
    """

    if result.evaluation_grid is None:
        raise ValueError("result does not contain an evaluation grid")
    if result.mean is None or result.covariance is None:
        raise ValueError("result does not contain native mean/covariance")
    if result.eigenfunctions is None:
        raise ValueError("result does not contain native eigenfunctions")

    grid = np.asarray(result.evaluation_grid, dtype=float)
    weights = (
        functional_trapezoid_weights(grid)
        if result.quadrature_weights is None
        else np.asarray(result.quadrature_weights, dtype=float)
    )
    estimated_phi = _normalized_functions(
        np.asarray(result.eigenfunctions, dtype=float),
        weights,
    )
    truth_phi_all = _normalized_functions(
        np.vstack([function(grid) for function in truth.eigenfunctions]),
        weights,
    )
    if result.n_components > truth_phi_all.shape[0]:
        raise ValueError(
            "truth contains fewer components than the fitted result"
        )

    similarity = np.abs(
        estimated_phi @ np.diag(weights) @ truth_phi_all.T
    )
    row_index, truth_index = linear_sum_assignment(-similarity)
    order = np.argsort(row_index)
    truth_index = truth_index[order]
    matched_similarity = similarity[
        np.arange(result.n_components),
        truth_index,
    ]

    signs = np.empty(result.n_components, dtype=float)
    for component, reference in enumerate(truth_index):
        inner = float(
            np.sum(
                weights
                * estimated_phi[component]
                * truth_phi_all[reference]
            )
        )
        signs[component] = 1.0 if inner >= 0 else -1.0

    true_mean = np.asarray(truth.mean(grid), dtype=float)
    mean_error = np.asarray(result.mean, dtype=float) - true_mean
    mean_ise = float(np.sum(weights * mean_error**2))

    raw_truth_phi = np.vstack(
        [function(grid) for function in truth.eigenfunctions]
    )
    true_covariance = np.zeros((grid.size, grid.size), dtype=float)
    for eigenvalue, function_values in zip(
        truth.eigenvalues,
        raw_truth_phi,
        strict=True,
    ):
        true_covariance += float(eigenvalue) * np.outer(
            function_values,
            function_values,
        )
    covariance_error = (
        np.asarray(result.covariance, dtype=float) - true_covariance
    )
    covariance_ise = float(
        np.sum(
            covariance_error**2
            * np.outer(weights, weights)
        )
    )

    matched_truth_eigenvalues = truth.eigenvalues[truth_index]
    eigenvalue_relative_error = np.abs(
        np.asarray(result.eigenvalues, dtype=float)
        - matched_truth_eigenvalues
    ) / np.abs(matched_truth_eigenvalues)

    subspace_cosines = _principal_cosines(
        estimated_phi,
        truth_phi_all[truth_index],
        weights,
    )

    score_correlation = np.full(result.n_components, np.nan, dtype=float)
    score_rmse = np.full(result.n_components, np.nan, dtype=float)
    estimated_scores = np.asarray(result.scores, dtype=float)
    for component, reference in enumerate(truth_index):
        estimate = signs[component] * estimated_scores[:, component]
        target = np.asarray(truth.scores[:, reference], dtype=float)
        finite = np.isfinite(estimate) & np.isfinite(target)
        if np.count_nonzero(finite) >= 2:
            score_correlation[component] = float(
                np.corrcoef(estimate[finite], target[finite])[0, 1]
            )
            score_rmse[component] = float(
                np.sqrt(
                    np.mean((estimate[finite] - target[finite]) ** 2)
                )
            )

    diagnostics = result.score_diagnostics
    if len(diagnostics):
        score_failure_rate = float(
            np.mean(diagnostics["status_code"].to_numpy() != "ok")
        )
    else:
        score_failure_rate = float(
            np.mean(~np.all(np.isfinite(estimated_scores), axis=1))
        )

    return SparseRecoveryMetrics(
        mean_ise=mean_ise,
        covariance_ise=covariance_ise,
        eigenvalue_relative_error=eigenvalue_relative_error,
        component_absolute_similarity=matched_similarity,
        subspace_principal_cosines=subspace_cosines,
        score_correlation=score_correlation,
        score_rmse=score_rmse,
        score_failure_rate=score_failure_rate,
        matched_truth_components=truth_index.astype(int),
        alignment_signs=signs,
    )
