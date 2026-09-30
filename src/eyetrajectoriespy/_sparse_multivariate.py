"""Private numerical core for native sparse multivariate FPCA.

This module extends the qualified univariate sparse machinery with the pieces
that are genuinely multivariate: cross-channel covariance smoothing, weighted
block-operator PSD handling/eigendecomposition, and joint PACE scoring.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

from ._sparse_native import (
    CovariancePSDAudit,
    CovariancePSDResult,
    LocalLinear2DResult,
    PACEScoreResult,
    RawCovariancePairs,
    SparseNativeError,
    WeightedEigendecomposition,
    epanechnikov_kernel,
    evaluate_fitted_function,
)
from .fpca import functional_trapezoid_weights


def raw_cross_covariance_pairs(
    curve_times: Sequence[np.ndarray],
    left_residuals: Sequence[np.ndarray],
    right_residuals: Sequence[np.ndarray],
) -> RawCovariancePairs:
    """Construct all within-curve cross-channel residual products.

    Equal-index/equal-time products are retained. Under the first 0.12
    measurement-error contract, cross-channel measurement errors are
    independent, so no cross-channel diagonal is removed.
    """

    if not (
        len(curve_times) == len(left_residuals) == len(right_residuals)
    ):
        raise ValueError(
            "curve_times and both residual sequences must have equal length"
        )

    s_values: list[float] = []
    t_values: list[float] = []
    products: list[float] = []
    curve_indices: list[int] = []

    for curve_index, (time, left, right) in enumerate(
        zip(curve_times, left_residuals, right_residuals, strict=True)
    ):
        time = np.asarray(time, dtype=float)
        left = np.asarray(left, dtype=float)
        right = np.asarray(right, dtype=float)
        if (
            time.ndim != 1
            or left.ndim != 1
            or right.ndim != 1
            or time.shape != left.shape
            or time.shape != right.shape
        ):
            raise ValueError(
                "each curve time/left/right residual triplet must be "
                "one-dimensional and aligned"
            )
        if not (
            np.all(np.isfinite(time))
            and np.all(np.isfinite(left))
            and np.all(np.isfinite(right))
        ):
            raise ValueError("curve times and residuals must be finite")

        for left_index, s_value in enumerate(time):
            for right_index, t_value in enumerate(time):
                s_values.append(float(s_value))
                t_values.append(float(t_value))
                products.append(
                    float(left[left_index] * right[right_index])
                )
                curve_indices.append(curve_index)

    if len(products) < 3:
        raise SparseNativeError(
            "insufficient_cross_covariance_pairs",
            "fewer than three cross-channel covariance pairs are available",
            details={"n_pairs": len(products)},
        )

    return RawCovariancePairs(
        s=np.asarray(s_values, dtype=float),
        t=np.asarray(t_values, dtype=float),
        products=np.asarray(products, dtype=float),
        curve_index=np.asarray(curve_indices, dtype=int),
        mirrored=False,
    )


def local_linear_cross_covariance_surface(
    pairs: RawCovariancePairs,
    evaluation_grid: np.ndarray,
    *,
    bandwidth: float,
    min_local_pairs: int = 6,
) -> LocalLinear2DResult:
    """Smooth a directed cross-channel covariance surface.

    Unlike the univariate covariance smoother, the result is not symmetrized
    in its two time arguments. The paired channel block is formed later by
    transpose.
    """

    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            "evaluation_grid must be finite, one-dimensional and strictly increasing"
        )
    bandwidth = float(bandwidth)
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("bandwidth must be finite and positive")
    if isinstance(min_local_pairs, bool) or not isinstance(
        min_local_pairs, int
    ):
        raise TypeError("min_local_pairs must be an integer")
    if min_local_pairs < 3:
        raise ValueError("min_local_pairs must be at least 3")

    surface = np.empty((grid.size, grid.size), dtype=float)
    support = np.empty_like(surface, dtype=int)
    for row, s0 in enumerate(grid):
        ds = pairs.s - s0
        ws = epanechnikov_kernel(ds / bandwidth)
        for column, t0 in enumerate(grid):
            dt = pairs.t - t0
            weights = ws * epanechnikov_kernel(dt / bandwidth)
            mask = weights > 0
            count = int(np.count_nonzero(mask))
            support[row, column] = count
            if count < min_local_pairs:
                raise SparseNativeError(
                    "insufficient_cross_covariance_local_support",
                    "local cross-covariance smoothing has too few pairs",
                    details={
                        "s": float(s0),
                        "t": float(t0),
                        "support_count": count,
                        "required_count": int(min_local_pairs),
                        "bandwidth": bandwidth,
                    },
                )

            design = np.column_stack(
                [
                    np.ones(count, dtype=float),
                    ds[mask],
                    dt[mask],
                ]
            )
            local_weights = weights[mask]
            weighted_design = design * np.sqrt(local_weights)[:, None]
            if np.linalg.matrix_rank(weighted_design) < 3:
                raise SparseNativeError(
                    "insufficient_cross_covariance_local_support",
                    "local cross-covariance design is rank deficient",
                    details={
                        "s": float(s0),
                        "t": float(t0),
                        "support_count": count,
                        "bandwidth": bandwidth,
                    },
                )
            weighted_product = pairs.products[mask] * np.sqrt(local_weights)
            beta, *_ = np.linalg.lstsq(
                weighted_design,
                weighted_product,
                rcond=None,
            )
            surface[row, column] = beta[0]

    return LocalLinear2DResult(
        values=surface,
        support_counts=support,
        bandwidth=bandwidth,
        kernel="product_epanechnikov",
    )


def block_quadrature_weights(
    evaluation_grid: np.ndarray,
    *,
    n_dimensions: int,
) -> np.ndarray:
    """Return dimension-major trapezoidal weights for a block operator."""

    if isinstance(n_dimensions, bool) or not isinstance(n_dimensions, int):
        raise TypeError("n_dimensions must be an integer")
    if n_dimensions < 2:
        raise ValueError("n_dimensions must be at least two")
    weights = functional_trapezoid_weights(evaluation_grid)
    return np.tile(weights, n_dimensions)


def covariance_blocks_to_matrix(blocks: np.ndarray) -> np.ndarray:
    """Flatten covariance blocks in dimension-major order."""

    array = np.asarray(blocks, dtype=float)
    if array.ndim != 4:
        raise ValueError("blocks must have shape (D, M, D, M)")
    d1, m1, d2, m2 = array.shape
    if d1 != d2 or m1 != m2:
        raise ValueError("blocks must have shape (D, M, D, M)")
    if d1 < 2 or m1 < 2:
        raise ValueError("block covariance requires at least 2 dimensions/grid points")
    if not np.all(np.isfinite(array)):
        raise ValueError("blocks must contain only finite values")
    return array.reshape(d1 * m1, d1 * m1)


def covariance_matrix_to_blocks(
    covariance: np.ndarray,
    *,
    n_dimensions: int,
    n_grid: int,
) -> np.ndarray:
    """Reshape a dimension-major block covariance matrix."""

    matrix = np.asarray(covariance, dtype=float)
    expected = n_dimensions * n_grid
    if matrix.shape != (expected, expected):
        raise ValueError(
            f"covariance must have shape ({expected}, {expected})"
        )
    return matrix.reshape(n_dimensions, n_grid, n_dimensions, n_grid)


def repair_block_covariance_psd(
    blocks: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    action: str = "error",
    tolerance: float = 1e-8,
) -> CovariancePSDResult:
    """Audit and optionally project a multivariate block covariance to PSD."""

    array = np.asarray(blocks, dtype=float)
    if array.ndim != 4:
        raise ValueError("blocks must have shape (D, M, D, M)")
    n_dimensions, n_grid, d2, m2 = array.shape
    if n_dimensions != d2 or n_grid != m2:
        raise ValueError("blocks must have shape (D, M, D, M)")
    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.shape != (n_grid,)
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError("evaluation_grid must align with covariance blocks")
    if action not in {"error", "project"}:
        raise ValueError("action must be 'error' or 'project'")
    tolerance = float(tolerance)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")

    matrix = covariance_blocks_to_matrix(array)
    matrix = 0.5 * (matrix + matrix.T)
    weights = block_quadrature_weights(
        grid,
        n_dimensions=n_dimensions,
    )
    sqrt_weights = np.sqrt(weights)
    weighted_operator = (
        sqrt_weights[:, None] * matrix * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    negative = eigenvalues < 0
    substantial = eigenvalues < -tolerance
    most_negative = float(np.min(eigenvalues))
    negative_count = int(np.count_nonzero(negative))
    substantial_count = int(np.count_nonzero(substantial))

    if action == "error" and substantial_count:
        raise SparseNativeError(
            "block_covariance_psd_failure",
            "fitted block covariance operator has eigenvalues below "
            "the PSD tolerance",
            details={
                "most_negative_eigenvalue": most_negative,
                "negative_eigenvalue_count": negative_count,
                "substantial_negative_eigenvalue_count": substantial_count,
                "tolerance": tolerance,
            },
        )

    clipped = eigenvalues.copy()
    applied_action = "none"
    if action == "project" and negative_count:
        clipped[negative] = 0.0
        applied_action = "project"
    elif action == "error" and negative_count:
        clipped[negative] = 0.0
        applied_action = "numerical_clip_within_tolerance"

    if applied_action == "none":
        repaired = matrix.copy()
    else:
        repaired_weighted = (eigenvectors * clipped[None, :]) @ eigenvectors.T
        repaired = (
            repaired_weighted
            / sqrt_weights[:, None]
            / sqrt_weights[None, :]
        )
        repaired = 0.5 * (repaired + repaired.T)

    correction = repaired - matrix
    correction_norm = float(np.linalg.norm(correction, ord="fro"))
    baseline_norm = float(np.linalg.norm(matrix, ord="fro"))
    relative_norm = (
        0.0 if baseline_norm == 0 else correction_norm / baseline_norm
    )
    operator_correction = (
        sqrt_weights[:, None]
        * correction
        * sqrt_weights[None, :]
    )
    operator_correction_norm = float(
        np.linalg.norm(operator_correction, ord="fro")
    )
    operator_baseline_norm = float(
        np.linalg.norm(weighted_operator, ord="fro")
    )
    relative_operator_norm = (
        0.0
        if operator_baseline_norm == 0
        else operator_correction_norm / operator_baseline_norm
    )
    audit = CovariancePSDAudit(
        requested_action=action,
        applied_action=applied_action,
        tolerance=tolerance,
        pre_repair_operator_eigenvalues=eigenvalues.copy(),
        negative_eigenvalue_count=negative_count,
        substantial_negative_eigenvalue_count=substantial_count,
        most_negative_eigenvalue=most_negative,
        correction_frobenius_norm=correction_norm,
        relative_correction_frobenius_norm=relative_norm,
        operator_correction_frobenius_norm=operator_correction_norm,
        relative_operator_correction_frobenius_norm=relative_operator_norm,
    )
    return CovariancePSDResult(covariance=repaired, audit=audit)


def weighted_block_covariance_eigendecomposition(
    covariance: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    n_dimensions: int,
    n_components: int,
    positive_tolerance: float = 1e-10,
) -> WeightedEigendecomposition:
    """Solve a quadrature-weighted multivariate block covariance eigenproblem."""

    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            "evaluation_grid must be finite, one-dimensional and strictly increasing"
        )
    if isinstance(n_dimensions, bool) or not isinstance(n_dimensions, int):
        raise TypeError("n_dimensions must be an integer")
    if n_dimensions < 2:
        raise ValueError("n_dimensions must be at least two")
    matrix = np.asarray(covariance, dtype=float)
    expected = n_dimensions * grid.size
    if matrix.shape != (expected, expected):
        raise ValueError(
            f"covariance must have shape ({expected}, {expected})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError("covariance must contain only finite values")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    positive_tolerance = float(positive_tolerance)
    if not np.isfinite(positive_tolerance) or positive_tolerance < 0:
        raise ValueError(
            "positive_tolerance must be finite and non-negative"
        )

    weights = block_quadrature_weights(
        grid,
        n_dimensions=n_dimensions,
    )
    sqrt_weights = np.sqrt(weights)
    matrix = 0.5 * (matrix + matrix.T)
    weighted_operator = (
        sqrt_weights[:, None] * matrix * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    positive = eigenvalues > positive_tolerance
    n_positive = int(np.count_nonzero(positive))
    if n_components > n_positive:
        raise SparseNativeError(
            "insufficient_positive_joint_components",
            "fitted block covariance has fewer positive components than requested",
            details={
                "requested_components": n_components,
                "positive_components": n_positive,
                "positive_tolerance": positive_tolerance,
            },
        )

    eigenvalues = eigenvalues[:n_components].copy()
    eigenvectors = eigenvectors[:, :n_components].copy()
    eigenfunctions = (eigenvectors / sqrt_weights[:, None]).T

    for component in range(n_components):
        pivot = int(np.argmax(np.abs(eigenfunctions[component])))
        if eigenfunctions[component, pivot] < 0:
            eigenfunctions[component] *= -1.0

    return WeightedEigendecomposition(
        eigenvalues=eigenvalues,
        eigenfunctions=eigenfunctions,
        quadrature_weights=weights,
    )


def evaluate_fitted_cross_covariance(
    evaluation_grid: np.ndarray,
    fitted_covariance: np.ndarray,
    left_times: np.ndarray,
    right_times: np.ndarray,
) -> np.ndarray:
    """Evaluate a directed fitted covariance block at native times."""

    grid = np.asarray(evaluation_grid, dtype=float)
    covariance = np.asarray(fitted_covariance, dtype=float)
    left = np.asarray(left_times, dtype=float)
    right = np.asarray(right_times, dtype=float)
    if covariance.shape != (grid.size, grid.size):
        raise ValueError(
            f"fitted_covariance must have shape ({grid.size}, {grid.size})"
        )
    if (
        left.ndim != 1
        or right.ndim != 1
        or not np.all(np.isfinite(left))
        or not np.all(np.isfinite(right))
    ):
        raise ValueError("native times must be finite one-dimensional arrays")
    if (
        np.any(left < grid[0])
        or np.any(left > grid[-1])
        or np.any(right < grid[0])
        or np.any(right > grid[-1])
    ):
        raise SparseNativeError(
            "native_time_outside_fitted_support",
            "native observation times fall outside fitted covariance support",
            details={
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
                "left_min": float(np.min(left)),
                "left_max": float(np.max(left)),
                "right_min": float(np.min(right)),
                "right_max": float(np.max(right)),
            },
        )

    interpolator = RegularGridInterpolator(
        (grid, grid),
        covariance,
        method="linear",
        bounds_error=True,
    )
    left_grid, right_grid = np.meshgrid(left, right, indexing="ij")
    points = np.column_stack(
        [left_grid.ravel(), right_grid.ravel()]
    )
    return np.asarray(interpolator(points), dtype=float).reshape(
        left.size,
        right.size,
    )


def multivariate_pace_scores(
    curve_ids: Sequence[str],
    curve_times: Sequence[np.ndarray],
    curve_values: Sequence[np.ndarray],
    *,
    evaluation_grid: np.ndarray,
    fitted_mean: np.ndarray,
    fitted_covariance_blocks: np.ndarray,
    eigenvalues: np.ndarray,
    eigenfunctions: np.ndarray,
    noise_variances: np.ndarray,
    n_components: int,
    score_ridge: float = 0.0,
    condition_limit: float = 1e12,
    min_score_samples: int = 2,
    failure_action: str = "error",
) -> PACEScoreResult:
    """Recover joint conditional scores from the full fitted block covariance."""

    if not (
        len(curve_ids) == len(curve_times) == len(curve_values)
    ):
        raise ValueError(
            "curve_ids, curve_times, and curve_values must have equal length"
        )

    grid = np.asarray(evaluation_grid, dtype=float)
    mean = np.asarray(fitted_mean, dtype=float)
    blocks = np.asarray(fitted_covariance_blocks, dtype=float)
    values = np.asarray(eigenvalues, dtype=float)
    functions = np.asarray(eigenfunctions, dtype=float)
    noise = np.asarray(noise_variances, dtype=float)

    if mean.ndim != 2 or mean.shape[0] != grid.size:
        raise ValueError("fitted_mean must have shape (n_grid, n_dimensions)")
    n_dimensions = mean.shape[1]
    if n_dimensions < 2:
        raise ValueError("joint scoring requires at least two dimensions")
    if blocks.shape != (
        n_dimensions,
        grid.size,
        n_dimensions,
        grid.size,
    ):
        raise ValueError(
            "fitted_covariance_blocks must have shape (D, M, D, M)"
        )
    if (
        functions.ndim != 3
        or functions.shape[1:] != (grid.size, n_dimensions)
    ):
        raise ValueError(
            "eigenfunctions must have shape "
            "(n_available_components, n_grid, n_dimensions)"
        )
    if values.ndim != 1 or values.size != functions.shape[0]:
        raise ValueError("eigenvalues must align with eigenfunctions")
    if noise.shape != (n_dimensions,):
        raise ValueError(
            "noise_variances must contain one value per selected dimension"
        )
    if not np.all(np.isfinite(noise)) or np.any(noise < 0):
        raise ValueError(
            "noise_variances must be finite and non-negative"
        )
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1 or n_components > values.size:
        raise ValueError(
            "n_components is outside the available eigenfunction range"
        )
    score_ridge = float(score_ridge)
    if not np.isfinite(score_ridge) or score_ridge < 0:
        raise ValueError("score_ridge must be finite and non-negative")
    condition_limit = float(condition_limit)
    if not np.isfinite(condition_limit) or condition_limit <= 1:
        raise ValueError(
            "condition_limit must be finite and greater than 1"
        )
    if isinstance(min_score_samples, bool) or not isinstance(
        min_score_samples, int
    ):
        raise TypeError("min_score_samples must be an integer")
    if min_score_samples < 1:
        raise ValueError("min_score_samples must be positive")
    if failure_action not in {"error", "retain_nan"}:
        raise ValueError(
            "failure_action must be 'error' or 'retain_nan'"
        )

    scores = np.full((len(curve_ids), n_components), np.nan, dtype=float)
    rows: list[dict[str, Any]] = []
    first_failure: tuple[str, str, dict[str, Any]] | None = None

    for curve_index, (curve_id, time, observed) in enumerate(
        zip(curve_ids, curve_times, curve_values, strict=True)
    ):
        time = np.asarray(time, dtype=float)
        observed = np.asarray(observed, dtype=float)
        if (
            time.ndim != 1
            or observed.ndim != 2
            or observed.shape != (time.size, n_dimensions)
        ):
            raise ValueError(
                "each curve value matrix must have shape "
                "(n_samples, n_dimensions)"
            )
        if not np.all(np.isfinite(time)) or not np.all(np.isfinite(observed)):
            raise ValueError("curve times and observed values must be finite")

        status_code = "ok"
        solve_status = "not_attempted"
        condition_number = np.nan
        minimum_eigenvalue = np.nan
        maximum_eigenvalue = np.nan

        if time.size < min_score_samples:
            status_code = "curve_too_sparse_for_joint_score_system"
        else:
            mean_parts = [
                evaluate_fitted_function(grid, mean[:, d], time)
                for d in range(n_dimensions)
            ]
            mean_i = np.concatenate(mean_parts)
            observed_i = observed.T.reshape(-1)
            n_time = time.size
            sigma_i = np.empty(
                (n_dimensions * n_time, n_dimensions * n_time),
                dtype=float,
            )
            for left_dimension in range(n_dimensions):
                left_slice = slice(
                    left_dimension * n_time,
                    (left_dimension + 1) * n_time,
                )
                for right_dimension in range(n_dimensions):
                    right_slice = slice(
                        right_dimension * n_time,
                        (right_dimension + 1) * n_time,
                    )
                    sigma_i[left_slice, right_slice] = (
                        evaluate_fitted_cross_covariance(
                            grid,
                            blocks[
                                left_dimension,
                                :,
                                right_dimension,
                                :,
                            ],
                            time,
                            time,
                        )
                    )

            sigma_i += np.diag(
                np.repeat(noise + score_ridge, n_time)
            )
            sigma_i = 0.5 * (sigma_i + sigma_i.T)
            sigma_eigenvalues = np.linalg.eigvalsh(sigma_i)
            minimum_eigenvalue = float(np.min(sigma_eigenvalues))
            maximum_eigenvalue = float(np.max(sigma_eigenvalues))
            condition_number = (
                np.inf
                if minimum_eigenvalue <= 0
                else maximum_eigenvalue / minimum_eigenvalue
            )

            if minimum_eigenvalue <= 0:
                status_code = "joint_score_covariance_not_positive_definite"
            elif condition_number > condition_limit:
                status_code = "joint_score_covariance_ill_conditioned"
            else:
                centered = observed_i - mean_i
                solved = np.linalg.solve(sigma_i, centered)
                phi_i = np.empty(
                    (n_dimensions * n_time, n_components),
                    dtype=float,
                )
                for component in range(n_components):
                    phi_i[:, component] = np.concatenate(
                        [
                            evaluate_fitted_function(
                                grid,
                                functions[component, :, dimension],
                                time,
                            )
                            for dimension in range(n_dimensions)
                        ]
                    )
                scores[curve_index] = values[:n_components] * (
                    phi_i.T @ solved
                )
                solve_status = "solved"

        row = {
            "curve_id": str(curve_id),
            "n_samples": int(time.size),
            "n_scalar_observations": int(time.size * n_dimensions),
            "n_dimensions": int(n_dimensions),
            "status_code": status_code,
            "solve_status": solve_status,
            "condition_number": float(condition_number),
            "minimum_eigenvalue": float(minimum_eigenvalue),
            "maximum_eigenvalue": float(maximum_eigenvalue),
            "score_ridge": score_ridge,
            "condition_limit": condition_limit,
        }
        rows.append(row)
        if status_code != "ok" and first_failure is None:
            first_failure = (status_code, str(curve_id), dict(row))

    diagnostics = pd.DataFrame(rows)
    if first_failure is not None and failure_action == "error":
        code, curve_id, details = first_failure
        raise SparseNativeError(
            code,
            f"joint PACE score system failed for curve {curve_id!r}",
            details={
                "curve_id": curve_id,
                **details,
            },
        )

    return PACEScoreResult(
        scores=scores,
        diagnostics=diagnostics,
        covariance_source=(
            "full_fitted_block_covariance_plus_dimension_noise"
        ),
    )
