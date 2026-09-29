"""Native sparse-FPCA numerical building blocks for the 0.10 research branch.

This private module contains the validated numerical machinery used by the
public :func:`eyetrajectoriespy.fit_sparse_fpca` composition layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

from .fpca import functional_trapezoid_weights


class SparseNativeError(ValueError):
    """Structured failure from the native sparse-FPCA numerical layer."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.details = {} if details is None else dict(details)


@dataclass(frozen=True)
class LocalLinear1DResult:
    """One-dimensional local-linear smoother output and local support counts."""

    values: np.ndarray
    support_counts: np.ndarray
    bandwidth: float
    kernel: str


@dataclass(frozen=True)
class RawCovariancePairs:
    """Off-diagonal within-curve covariance products."""

    s: np.ndarray
    t: np.ndarray
    products: np.ndarray
    curve_index: np.ndarray
    mirrored: bool

    @property
    def n_pairs(self) -> int:
        return int(self.products.size)


@dataclass(frozen=True)
class LocalLinear2DResult:
    """Two-dimensional local-linear covariance-surface smoother output."""

    values: np.ndarray
    support_counts: np.ndarray
    bandwidth: float
    kernel: str


@dataclass(frozen=True)
class RotatedCovarianceDiagonalResult:
    """Diagonal-specific covariance smoother in 45-degree rotated coordinates."""

    values: np.ndarray
    support_counts: np.ndarray
    bandwidth: float
    kernel: str
    rotation: str


@dataclass(frozen=True)
class NoiseVarianceResult:
    """Diagonal-difference measurement-noise estimate without silent clipping."""

    variance: float
    raw_diagonal: np.ndarray
    latent_diagonal: np.ndarray
    diagonal_difference: np.ndarray
    status_code: str
    bandwidth: float
    support_interval: tuple[float, float]
    support_mask: np.ndarray


@dataclass(frozen=True)
class CovariancePSDAudit:
    """Audit trail for covariance positive-semidefinite handling."""

    requested_action: str
    applied_action: str
    tolerance: float
    pre_repair_operator_eigenvalues: np.ndarray
    negative_eigenvalue_count: int
    substantial_negative_eigenvalue_count: int
    most_negative_eigenvalue: float
    correction_frobenius_norm: float
    relative_correction_frobenius_norm: float
    operator_correction_frobenius_norm: float
    relative_operator_correction_frobenius_norm: float


@dataclass(frozen=True)
class CovariancePSDResult:
    """Repaired covariance grid plus the complete repair audit."""

    covariance: np.ndarray
    audit: CovariancePSDAudit


@dataclass(frozen=True)
class WeightedEigendecomposition:
    """Quadrature-weighted covariance eigendecomposition."""

    eigenvalues: np.ndarray
    eigenfunctions: np.ndarray
    quadrature_weights: np.ndarray


@dataclass(frozen=True)
class PACEScoreResult:
    """PACE scores and per-curve conditioning/status diagnostics."""

    scores: np.ndarray
    diagnostics: pd.DataFrame
    covariance_source: str = "full_fitted_covariance_plus_noise"


def _validate_grid(grid: np.ndarray, *, name: str = "grid") -> np.ndarray:
    arr = np.asarray(grid, dtype=float)
    if (
        arr.ndim != 1
        or arr.size < 2
        or not np.all(np.isfinite(arr))
        or not np.all(np.diff(arr) > 0)
    ):
        raise ValueError(
            f"{name} must be a finite, strictly increasing one-dimensional array"
        )
    return arr


def _positive_finite(value: float, *, name: str) -> float:
    number = float(value)
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def epanechnikov_kernel(u: np.ndarray) -> np.ndarray:
    """Evaluate the compact-support Epanechnikov kernel."""

    values = np.asarray(u, dtype=float)
    out = np.zeros_like(values, dtype=float)
    inside = np.abs(values) <= 1.0
    out[inside] = 0.75 * (1.0 - values[inside] ** 2)
    return out


def local_linear_smooth_1d(
    x: np.ndarray,
    y: np.ndarray,
    evaluation_points: np.ndarray,
    *,
    bandwidth: float,
    min_local_points: int = 3,
) -> LocalLinear1DResult:
    """Fit a local-linear smoother on explicitly supplied evaluation points."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    points = np.asarray(evaluation_points, dtype=float)
    bandwidth = _positive_finite(bandwidth, name="bandwidth")
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError("x and y must be one-dimensional arrays with equal length")
    if points.ndim != 1 or points.size < 1 or not np.all(np.isfinite(points)):
        raise ValueError("evaluation_points must be a finite one-dimensional array")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("x and y must be finite")
    if isinstance(min_local_points, bool) or not isinstance(min_local_points, int):
        raise TypeError("min_local_points must be an integer")
    if min_local_points < 2:
        raise ValueError("min_local_points must be at least 2")

    fitted = np.empty(points.size, dtype=float)
    support = np.empty(points.size, dtype=int)
    for index, point in enumerate(points):
        delta = x - point
        weights = epanechnikov_kernel(delta / bandwidth)
        mask = weights > 0
        support[index] = int(np.count_nonzero(mask))
        if support[index] < min_local_points:
            raise SparseNativeError(
                "insufficient_mean_local_support",
                "local-linear mean smoothing has too few observations",
                details={
                    "evaluation_point": float(point),
                    "support_count": int(support[index]),
                    "required_count": int(min_local_points),
                    "bandwidth": bandwidth,
                },
            )
        local_delta = delta[mask]
        local_weights = weights[mask]
        design = np.column_stack(
            [np.ones(local_delta.size, dtype=float), local_delta]
        )
        weighted_design = design * np.sqrt(local_weights)[:, None]
        if np.linalg.matrix_rank(weighted_design) < 2:
            raise SparseNativeError(
                "insufficient_mean_local_support",
                "local-linear mean design is rank deficient",
                details={
                    "evaluation_point": float(point),
                    "support_count": int(support[index]),
                    "bandwidth": bandwidth,
                },
            )
        weighted_y = y[mask] * np.sqrt(local_weights)
        beta, *_ = np.linalg.lstsq(weighted_design, weighted_y, rcond=None)
        fitted[index] = beta[0]

    return LocalLinear1DResult(
        values=fitted,
        support_counts=support,
        bandwidth=bandwidth,
        kernel="epanechnikov",
    )


def raw_offdiagonal_covariance_pairs(
    curve_times: Sequence[np.ndarray],
    curve_residuals: Sequence[np.ndarray],
    *,
    include_mirror: bool = True,
) -> RawCovariancePairs:
    """Construct within-curve off-diagonal residual products."""

    if len(curve_times) != len(curve_residuals):
        raise ValueError("curve_times and curve_residuals must have equal length")
    s_values: list[float] = []
    t_values: list[float] = []
    products: list[float] = []
    curve_indices: list[int] = []

    for curve_index, (time, residual) in enumerate(
        zip(curve_times, curve_residuals, strict=True)
    ):
        time = np.asarray(time, dtype=float)
        residual = np.asarray(residual, dtype=float)
        if time.ndim != 1 or residual.ndim != 1 or time.shape != residual.shape:
            raise ValueError(
                "each curve time/residual pair must be one-dimensional and aligned"
            )
        if not np.all(np.isfinite(time)) or not np.all(np.isfinite(residual)):
            raise ValueError("curve times and residuals must be finite")
        for left in range(time.size - 1):
            for right in range(left + 1, time.size):
                product = float(residual[left] * residual[right])
                s_values.append(float(time[left]))
                t_values.append(float(time[right]))
                products.append(product)
                curve_indices.append(curve_index)
                if include_mirror:
                    s_values.append(float(time[right]))
                    t_values.append(float(time[left]))
                    products.append(product)
                    curve_indices.append(curve_index)

    if len(products) < 3:
        raise SparseNativeError(
            "insufficient_within_curve_covariance_pairs",
            "fewer than three off-diagonal covariance pairs are available",
            details={"n_pairs": len(products)},
        )

    return RawCovariancePairs(
        s=np.asarray(s_values, dtype=float),
        t=np.asarray(t_values, dtype=float),
        products=np.asarray(products, dtype=float),
        curve_index=np.asarray(curve_indices, dtype=int),
        mirrored=bool(include_mirror),
    )


def local_linear_covariance_surface(
    pairs: RawCovariancePairs,
    evaluation_grid: np.ndarray,
    *,
    bandwidth: float,
    min_local_pairs: int = 6,
) -> LocalLinear2DResult:
    """Smooth raw off-diagonal covariance products with a 2-D local plane."""

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    bandwidth = _positive_finite(bandwidth, name="bandwidth")
    if isinstance(min_local_pairs, bool) or not isinstance(min_local_pairs, int):
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
            support[row, column] = int(np.count_nonzero(mask))
            if support[row, column] < min_local_pairs:
                raise SparseNativeError(
                    "insufficient_covariance_local_support",
                    "local covariance smoothing has too few off-diagonal pairs",
                    details={
                        "s": float(s0),
                        "t": float(t0),
                        "support_count": int(support[row, column]),
                        "required_count": int(min_local_pairs),
                        "bandwidth": bandwidth,
                    },
                )
            design = np.column_stack(
                [
                    np.ones(support[row, column], dtype=float),
                    ds[mask],
                    dt[mask],
                ]
            )
            local_weights = weights[mask]
            weighted_design = design * np.sqrt(local_weights)[:, None]
            if np.linalg.matrix_rank(weighted_design) < 3:
                raise SparseNativeError(
                    "insufficient_covariance_local_support",
                    "local covariance design is rank deficient",
                    details={
                        "s": float(s0),
                        "t": float(t0),
                        "support_count": int(support[row, column]),
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

    surface = 0.5 * (surface + surface.T)
    return LocalLinear2DResult(
        values=surface,
        support_counts=support,
        bandwidth=bandwidth,
        kernel="product_epanechnikov",
    )


def rotated_local_quadratic_covariance_diagonal(
    pairs: RawCovariancePairs,
    evaluation_grid: np.ndarray,
    *,
    bandwidth: float,
    min_local_pairs: int = 6,
) -> RotatedCovarianceDiagonalResult:
    """Estimate the latent covariance diagonal with the PACE rotated smoother.

    The off-diagonal covariance pairs are rotated by 45 degrees. At each
    diagonal target, the local model is linear along the diagonal direction
    and quadratic in the direction perpendicular to the diagonal. This is
    deliberately separate from the generic local-linear covariance-surface
    smoother used for the FPCA operator itself.
    """

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    bandwidth = _positive_finite(bandwidth, name="bandwidth")
    if isinstance(min_local_pairs, bool) or not isinstance(min_local_pairs, int):
        raise TypeError("min_local_pairs must be an integer")
    if min_local_pairs < 3:
        raise ValueError("min_local_pairs must be at least 3")

    root_two = np.sqrt(2.0)
    along = (pairs.s + pairs.t) / root_two
    perpendicular = (-pairs.s + pairs.t) / root_two

    fitted = np.empty(grid.size, dtype=float)
    support = np.empty(grid.size, dtype=int)
    for index, point in enumerate(grid):
        target_along = root_two * point
        delta_along = along - target_along
        delta_perpendicular = perpendicular
        weights = (
            epanechnikov_kernel(delta_along / bandwidth)
            * epanechnikov_kernel(delta_perpendicular / bandwidth)
        )
        mask = weights > 0
        support[index] = int(np.count_nonzero(mask))
        if support[index] < min_local_pairs:
            raise SparseNativeError(
                "insufficient_noise_diagonal_local_support",
                "rotated covariance-diagonal smoothing has too few off-diagonal pairs",
                details={
                    "evaluation_point": float(point),
                    "support_count": int(support[index]),
                    "required_count": int(min_local_pairs),
                    "bandwidth": bandwidth,
                },
            )

        local_along = delta_along[mask]
        local_perpendicular = delta_perpendicular[mask]
        design = np.column_stack(
            [
                np.ones(support[index], dtype=float),
                local_along,
                local_perpendicular**2,
            ]
        )
        local_weights = weights[mask]
        weighted_design = design * np.sqrt(local_weights)[:, None]
        if np.linalg.matrix_rank(weighted_design) < 3:
            raise SparseNativeError(
                "insufficient_noise_diagonal_local_support",
                "rotated covariance-diagonal design is rank deficient",
                details={
                    "evaluation_point": float(point),
                    "support_count": int(support[index]),
                    "bandwidth": bandwidth,
                },
            )
        weighted_product = pairs.products[mask] * np.sqrt(local_weights)
        beta, *_ = np.linalg.lstsq(
            weighted_design,
            weighted_product,
            rcond=None,
        )
        fitted[index] = beta[0]

    return RotatedCovarianceDiagonalResult(
        values=fitted,
        support_counts=support,
        bandwidth=bandwidth,
        kernel="rotated_product_epanechnikov",
        rotation="45_degrees_linear_along_diagonal_quadratic_perpendicular",
    )


def estimate_noise_variance_diagonal_difference(
    observation_times: Sequence[np.ndarray],
    residuals: Sequence[np.ndarray],
    evaluation_grid: np.ndarray,
    latent_covariance: np.ndarray,
    *,
    latent_diagonal: np.ndarray | None = None,
    bandwidth: float,
    noise_support: tuple[float, float],
    min_local_points: int = 3,
) -> NoiseVarianceResult:
    """Estimate measurement-error variance from raw versus latent diagonals.

    A non-positive estimate is retained and flagged rather than silently clipped.
    """

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    covariance = np.asarray(latent_covariance, dtype=float)
    if covariance.shape != (grid.size, grid.size):
        raise ValueError(
            "latent_covariance must have shape "
            f"({grid.size}, {grid.size})"
        )
    if len(observation_times) != len(residuals):
        raise ValueError("observation_times and residuals must have equal length")

    pooled_time = np.concatenate(
        [np.asarray(time, dtype=float) for time in observation_times]
    )
    pooled_square = np.concatenate(
        [np.asarray(residual, dtype=float) ** 2 for residual in residuals]
    )
    diagonal_fit = local_linear_smooth_1d(
        pooled_time,
        pooled_square,
        grid,
        bandwidth=bandwidth,
        min_local_points=min_local_points,
    )
    if (
        not isinstance(noise_support, tuple)
        or len(noise_support) != 2
    ):
        raise TypeError("noise_support must be a (start, end) tuple")
    support_start = float(noise_support[0])
    support_end = float(noise_support[1])
    if (
        not np.isfinite(support_start)
        or not np.isfinite(support_end)
        or support_end <= support_start
    ):
        raise ValueError(
            "noise_support must contain finite values with end > start"
        )
    if support_start < grid[0] or support_end > grid[-1]:
        raise ValueError(
            "noise_support must lie within the evaluation-grid support"
        )

    if latent_diagonal is None:
        effective_latent_diagonal = np.diag(covariance).copy()
    else:
        effective_latent_diagonal = np.asarray(latent_diagonal, dtype=float)
        if effective_latent_diagonal.shape != (grid.size,):
            raise ValueError(
                "latent_diagonal must have shape "
                f"({grid.size},)"
            )
        if not np.all(np.isfinite(effective_latent_diagonal)):
            raise ValueError("latent_diagonal must contain only finite values")
        effective_latent_diagonal = effective_latent_diagonal.copy()
    difference = diagonal_fit.values - effective_latent_diagonal
    support_mask = (
        (grid >= support_start)
        & (grid <= support_end)
    )
    support_grid = grid[support_mask]
    if support_grid.size < 2:
        raise SparseNativeError(
            "insufficient_noise_support",
            "noise_support contains fewer than two evaluation-grid points",
            details={
                "noise_support": [support_start, support_end],
                "n_grid_points": int(support_grid.size),
            },
        )
    support_weights = functional_trapezoid_weights(support_grid)
    support_difference = difference[support_mask]
    variance = float(
        np.sum(support_weights * support_difference)
        / np.sum(support_weights)
    )
    status = (
        "ok"
        if np.isfinite(variance) and variance > 0
        else "noise_variance_invalid"
    )
    return NoiseVarianceResult(
        variance=variance,
        raw_diagonal=diagonal_fit.values,
        latent_diagonal=effective_latent_diagonal,
        diagonal_difference=difference,
        status_code=status,
        bandwidth=float(bandwidth),
        support_interval=(support_start, support_end),
        support_mask=support_mask,
    )


def repair_covariance_psd(
    covariance: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    action: str = "error",
    tolerance: float = 1e-8,
) -> CovariancePSDResult:
    """Audit and optionally project a fitted covariance operator to PSD."""

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (grid.size, grid.size):
        raise ValueError(
            f"covariance must have shape ({grid.size}, {grid.size})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError("covariance must contain only finite values")
    if action not in {"error", "project"}:
        raise ValueError("action must be 'error' or 'project'")
    tolerance = float(tolerance)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")

    matrix = 0.5 * (matrix + matrix.T)
    weights = functional_trapezoid_weights(grid)
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
            "covariance_psd_failure",
            "fitted covariance operator has eigenvalues below the PSD tolerance",
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


def weighted_covariance_eigendecomposition(
    covariance: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    n_components: int,
    positive_tolerance: float = 1e-10,
) -> WeightedEigendecomposition:
    """Solve the quadrature-weighted covariance eigenproblem."""

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (grid.size, grid.size):
        raise ValueError(
            f"covariance must have shape ({grid.size}, {grid.size})"
        )
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    positive_tolerance = float(positive_tolerance)
    if not np.isfinite(positive_tolerance) or positive_tolerance < 0:
        raise ValueError(
            "positive_tolerance must be finite and non-negative"
        )

    weights = functional_trapezoid_weights(grid)
    sqrt_weights = np.sqrt(weights)
    weighted_operator = (
        sqrt_weights[:, None]
        * (0.5 * (matrix + matrix.T))
        * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    positive = eigenvalues > positive_tolerance
    n_positive = int(np.count_nonzero(positive))
    if n_components > n_positive:
        raise SparseNativeError(
            "insufficient_positive_components",
            "fitted covariance has fewer positive components than requested",
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


def evaluate_fitted_function(
    evaluation_grid: np.ndarray,
    fitted_values: np.ndarray,
    times: np.ndarray,
) -> np.ndarray:
    """Evaluate a fitted population function on native observation times."""

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    values = np.asarray(fitted_values, dtype=float)
    target = np.asarray(times, dtype=float)
    if values.shape != (grid.size,):
        raise ValueError(
            "fitted_values must have one value per evaluation-grid point"
        )
    if target.ndim != 1 or not np.all(np.isfinite(target)):
        raise ValueError("times must be a finite one-dimensional array")
    if np.any(target < grid[0]) or np.any(target > grid[-1]):
        raise SparseNativeError(
            "native_time_outside_fitted_support",
            "native observation times fall outside fitted population support",
            details={
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
                "target_min": float(np.min(target)),
                "target_max": float(np.max(target)),
            },
        )
    return np.interp(target, grid, values)


def evaluate_fitted_covariance(
    evaluation_grid: np.ndarray,
    fitted_covariance: np.ndarray,
    times: np.ndarray,
) -> np.ndarray:
    """Evaluate a fitted covariance surface on one curve's native times."""

    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    covariance = np.asarray(fitted_covariance, dtype=float)
    target = np.asarray(times, dtype=float)
    if covariance.shape != (grid.size, grid.size):
        raise ValueError(
            f"fitted_covariance must have shape ({grid.size}, {grid.size})"
        )
    if target.ndim != 1 or not np.all(np.isfinite(target)):
        raise ValueError("times must be a finite one-dimensional array")
    if np.any(target < grid[0]) or np.any(target > grid[-1]):
        raise SparseNativeError(
            "native_time_outside_fitted_support",
            "native observation times fall outside fitted covariance support",
            details={
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
                "target_min": float(np.min(target)),
                "target_max": float(np.max(target)),
            },
        )

    interpolator = RegularGridInterpolator(
        (grid, grid),
        covariance,
        method="linear",
        bounds_error=True,
    )
    left, right = np.meshgrid(target, target, indexing="ij")
    points = np.column_stack([left.ravel(), right.ravel()])
    result = np.asarray(interpolator(points), dtype=float).reshape(
        target.size,
        target.size,
    )
    return 0.5 * (result + result.T)


def pace_scores(
    curve_ids: Sequence[str],
    curve_times: Sequence[np.ndarray],
    curve_values: Sequence[np.ndarray],
    *,
    evaluation_grid: np.ndarray,
    fitted_mean: np.ndarray,
    fitted_covariance: np.ndarray,
    eigenvalues: np.ndarray,
    eigenfunctions: np.ndarray,
    noise_variance: float,
    n_components: int,
    score_ridge: float = 0.0,
    condition_limit: float = 1e12,
    min_score_samples: int = 2,
    failure_action: str = "error",
) -> PACEScoreResult:
    """Recover PACE scores from the full fitted covariance-plus-noise system.

    n_components controls returned scores only. The conditional covariance
    system always uses the full fitted covariance surface, not a rank-K
    reconstruction from retained components.
    """

    if len(curve_ids) != len(curve_times) or len(curve_ids) != len(curve_values):
        raise ValueError(
            "curve_ids, curve_times, and curve_values must have equal length"
        )
    grid = _validate_grid(evaluation_grid, name="evaluation_grid")
    mean = np.asarray(fitted_mean, dtype=float)
    covariance = np.asarray(fitted_covariance, dtype=float)
    values = np.asarray(eigenvalues, dtype=float)
    functions = np.asarray(eigenfunctions, dtype=float)
    if mean.shape != (grid.size,):
        raise ValueError(
            "fitted_mean must have one value per evaluation-grid point"
        )
    if covariance.shape != (grid.size, grid.size):
        raise ValueError(
            f"fitted_covariance must have shape ({grid.size}, {grid.size})"
        )
    if functions.ndim != 2 or functions.shape[1] != grid.size:
        raise ValueError(
            "eigenfunctions must have shape "
            "(n_available_components, n_grid)"
        )
    if values.ndim != 1 or values.size != functions.shape[0]:
        raise ValueError("eigenvalues must align with eigenfunctions")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1 or n_components > values.size:
        raise ValueError(
            "n_components is outside the available eigenfunction range"
        )
    noise_variance = float(noise_variance)
    if not np.isfinite(noise_variance) or noise_variance < 0:
        raise ValueError(
            "noise_variance must be finite and non-negative"
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
        min_score_samples,
        int,
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

    for index, (curve_id, time, observed) in enumerate(
        zip(curve_ids, curve_times, curve_values, strict=True)
    ):
        time = np.asarray(time, dtype=float)
        observed = np.asarray(observed, dtype=float)
        if time.ndim != 1 or observed.ndim != 1 or time.shape != observed.shape:
            raise ValueError(
                "each curve time/value pair must be one-dimensional and aligned"
            )
        if not np.all(np.isfinite(time)) or not np.all(np.isfinite(observed)):
            raise ValueError(
                "curve times and observed values must be finite"
            )

        status_code = "ok"
        solve_status = "not_attempted"
        condition_number = np.nan
        minimum_eigenvalue = np.nan
        maximum_eigenvalue = np.nan

        if time.size < min_score_samples:
            status_code = "curve_too_sparse_for_score_system"
        else:
            mean_i = evaluate_fitted_function(grid, mean, time)
            covariance_i = evaluate_fitted_covariance(
                grid,
                covariance,
                time,
            )
            sigma_i = covariance_i + (
                noise_variance + score_ridge
            ) * np.eye(time.size)
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
                status_code = (
                    "score_covariance_not_positive_definite"
                )
            elif condition_number > condition_limit:
                status_code = "score_covariance_ill_conditioned"
            else:
                centered = observed - mean_i
                solved = np.linalg.solve(sigma_i, centered)
                phi_i = np.column_stack(
                    [
                        evaluate_fitted_function(
                            grid,
                            functions[component],
                            time,
                        )
                        for component in range(n_components)
                    ]
                )
                scores[index] = values[:n_components] * (
                    phi_i.T @ solved
                )
                solve_status = "solved"

        row = {
            "curve_id": str(curve_id),
            "n_samples": int(time.size),
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
            f"PACE score system failed for curve {curve_id!r}",
            details={
                **details,
                "all_curve_diagnostics": diagnostics.to_dict(
                    orient="records"
                ),
            },
        )

    return PACEScoreResult(scores=scores, diagnostics=diagnostics)
