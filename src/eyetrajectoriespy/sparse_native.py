"""Native univariate sparse FPCA + PACE composition for the 0.10 branch."""

from __future__ import annotations

from typing import Any

import numpy as np

from ._sparse_native import (
    SparseNativeError,
    estimate_noise_variance_diagonal_difference,
    local_linear_covariance_surface,
    local_linear_smooth_1d,
    pace_scores,
    raw_offdiagonal_covariance_pairs,
    repair_covariance_psd,
    rotated_local_quadratic_covariance_diagonal,
    weighted_covariance_eigendecomposition,
)
from .types import IrregularTrajectorySet, SparseFPCAResult


def _validate_native_sparse_dimension(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
) -> int:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if trajectories.n_curves < 3:
        raise SparseNativeError(
            "insufficient_pooled_support",
            "native sparse FPCA requires at least three curves",
            details={"n_curves": trajectories.n_curves},
        )
    index = trajectories.dimension_names.index(dimension)
    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        selected = np.asarray(values[:, index], dtype=float)
        if not np.all(np.isfinite(selected)):
            raise SparseNativeError(
                "nonfinite_sparse_observation",
                "absent sparse observations must be represented by absent samples",
                details={
                    "curve_id": str(curve_id),
                    "dimension": dimension,
                    "n_nonfinite": int(np.count_nonzero(~np.isfinite(selected))),
                },
            )
    return index


def _validate_evaluation_grid(
    trajectories: IrregularTrajectorySet,
    evaluation_grid: np.ndarray,
) -> np.ndarray:
    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 3
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            "evaluation_grid must be a finite, strictly increasing "
            "one-dimensional array with at least three points"
        )
    pooled_start = min(float(time[0]) for time in trajectories.time)
    pooled_end = max(float(time[-1]) for time in trajectories.time)
    scale = max(1.0, abs(pooled_start), abs(pooled_end))
    tolerance = 1e-12 * scale
    if (
        float(grid[0]) < pooled_start - tolerance
        or float(grid[-1]) > pooled_end + tolerance
    ):
        raise SparseNativeError(
            "evaluation_grid_outside_pooled_support",
            "evaluation_grid must lie within the pooled observed support",
            details={
                "pooled_start": pooled_start,
                "pooled_end": pooled_end,
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
            },
        )
    return grid

def _analysis_support_views(
    trajectories: IrregularTrajectorySet,
    curve_values: tuple[np.ndarray, ...],
    grid: np.ndarray,
    *,
    action: str,
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...], dict[str, Any]]:
    """Apply an explicitly declared analysis-support policy."""

    if action not in {"error", "restrict"}:
        raise ValueError(
            "analysis_support_action must be 'error' or 'restrict'"
        )
    start = float(grid[0])
    end = float(grid[-1])
    effective_times: list[np.ndarray] = []
    effective_values: list[np.ndarray] = []
    outside_counts: list[int] = []
    in_support_counts: list[int] = []

    for time, observed in zip(
        trajectories.time, curve_values, strict=True
    ):
        time_array = np.asarray(time, dtype=float)
        value_array = np.asarray(observed, dtype=float)
        mask = (time_array >= start) & (time_array <= end)
        outside_counts.append(int(np.count_nonzero(~mask)))
        in_support_counts.append(int(np.count_nonzero(mask)))
        if action == "restrict":
            effective_times.append(time_array[mask].copy())
            effective_values.append(value_array[mask].copy())
        else:
            effective_times.append(time_array.copy())
            effective_values.append(value_array.copy())

    outside_total = int(np.sum(outside_counts))
    curves_with_outside = int(
        np.count_nonzero(np.asarray(outside_counts) > 0)
    )
    curves_without_support = int(
        np.count_nonzero(np.asarray(in_support_counts) == 0)
    )
    if action == "error" and outside_total:
        raise SparseNativeError(
            "observations_outside_analysis_support",
            "observations lie outside the declared evaluation-grid support",
            details={
                "analysis_support": [start, end],
                "outside_observation_count": outside_total,
                "curves_with_outside_observations": curves_with_outside,
                "outside_counts_by_curve": outside_counts,
            },
        )

    total_in_support = int(np.sum(in_support_counts))
    if total_in_support < 3:
        raise SparseNativeError(
            "insufficient_pooled_support",
            "fewer than three observations remain on declared support",
            details={
                "analysis_support": [start, end],
                "in_support_observation_count": total_in_support,
                "in_support_counts_by_curve": in_support_counts,
            },
        )

    diagnostics = {
        "analysis_support": [start, end],
        "analysis_support_action": action,
        "outside_observation_count": outside_total,
        "curves_with_outside_observations": curves_with_outside,
        "curves_without_in_support_observations": curves_without_support,
        "outside_counts_by_curve": outside_counts,
        "original_sample_counts": trajectories.sample_counts.tolist(),
        "analysis_sample_counts": in_support_counts,
    }
    return tuple(effective_times), tuple(effective_values), diagnostics


def _validate_native_sparse_settings(
    *,
    n_components: int,
    mean_smoother: str,
    covariance_smoother: str,
    kernel: str,
    noise_variance_method: str,
    measurement_error_variance: float | None,
    noise_support: tuple[float, float] | None,
) -> None:
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    if mean_smoother != "local_linear":
        raise ValueError(
            "mean_smoother must be 'local_linear' in the first native tranche"
        )
    if covariance_smoother != "local_linear":
        raise ValueError(
            "covariance_smoother must be 'local_linear' in the first native tranche"
        )
    if kernel != "epanechnikov":
        raise ValueError(
            "kernel must be 'epanechnikov' in the first native tranche"
        )
    if noise_variance_method not in {"diagonal_difference", "fixed"}:
        raise ValueError(
            "noise_variance_method must be 'diagonal_difference' or 'fixed'"
        )
    if noise_variance_method == "fixed":
        if measurement_error_variance is None:
            raise ValueError(
                "measurement_error_variance is required when "
                "noise_variance_method='fixed'"
            )
        value = float(measurement_error_variance)
        if not np.isfinite(value) or value < 0:
            raise ValueError(
                "measurement_error_variance must be finite and non-negative"
            )
        if noise_support is not None:
            raise ValueError(
                "noise_support must be None when "
                "noise_variance_method='fixed'"
            )
    else:
        if measurement_error_variance is not None:
            raise ValueError(
                "measurement_error_variance must be None when "
                "noise_variance_method='diagonal_difference'"
            )
        if noise_support is None:
            raise ValueError(
                "noise_support is required when "
                "noise_variance_method='diagonal_difference'"
            )


def fit_sparse_fpca(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    n_components: int,
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    covariance_bandwidth: float,
    noise_bandwidth: float | None = None,
    noise_support: tuple[float, float] | None = None,
    analysis_support_action: str = "error",
    mean_smoother: str = "local_linear",
    covariance_smoother: str = "local_linear",
    kernel: str = "epanechnikov",
    noise_variance_method: str = "diagonal_difference",
    measurement_error_variance: float | None = None,
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    positive_eigen_tolerance: float = 1e-10,
    score_ridge: float = 0.0,
    score_condition_limit: float = 1e12,
    min_score_samples: int = 2,
    score_failure_action: str = "error",
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
    noise_min_local_points: int = 3,
) -> SparseFPCAResult:
    """Fit native univariate sparse FPCA and recover PACE scores.

    Sparse raw trajectories remain on their native grids. Population mean,
    covariance, and eigenfunctions are smooth fitted objects that may be
    evaluated at native observation times; this is model evaluation, not
    interpolation of raw sparse trajectories.

    The evaluation-grid endpoints define the analysis support. The grid may be
    a strict subinterval of pooled observed time. Observations outside that
    support raise an error by default and are only excluded when
    analysis_support_action="restrict" is explicitly requested and audited.

    The PACE conditional covariance system uses the complete fitted/repaired
    covariance surface plus measurement-error variance. n_components controls
    returned eigenfunctions and scores, not the rank of that conditional
    covariance system. Component availability is determined by the positive
    spectrum of the fitted covariance operator rather than a dense-data
    n_curves - 1 rank rule.

    Bandwidths are declared numerically in this tranche. No automatic CV/GCV
    bandwidth selection is performed.
    """

    index = _validate_native_sparse_dimension(
        trajectories,
        dimension=dimension,
    )
    grid = _validate_evaluation_grid(trajectories, evaluation_grid)
    _validate_native_sparse_settings(
        n_components=n_components,
        mean_smoother=mean_smoother,
        covariance_smoother=covariance_smoother,
        kernel=kernel,
        noise_variance_method=noise_variance_method,
        measurement_error_variance=measurement_error_variance,
        noise_support=noise_support,
    )

    original_curve_values = tuple(
        np.asarray(values[:, index], dtype=float)
        for values in trajectories.values
    )
    curve_times, curve_values, support_diagnostics = _analysis_support_views(
        trajectories,
        original_curve_values,
        grid,
        action=analysis_support_action,
    )
    pooled_time = np.concatenate(curve_times)
    pooled_values = np.concatenate(curve_values)

    mean_fit = local_linear_smooth_1d(
        pooled_time,
        pooled_values,
        grid,
        bandwidth=mean_bandwidth,
        min_local_points=mean_min_local_points,
    )

    residuals: list[np.ndarray] = []
    for time, observed in zip(
        curve_times,
        curve_values,
        strict=True,
    ):
        if len(time) == 0:
            residuals.append(np.asarray([], dtype=float))
            continue
        mean_at_native = local_linear_smooth_1d(
            pooled_time,
            pooled_values,
            time,
            bandwidth=mean_bandwidth,
            min_local_points=mean_min_local_points,
        ).values
        residuals.append(observed - mean_at_native)

    pairs = raw_offdiagonal_covariance_pairs(
        curve_times,
        tuple(residuals),
        include_mirror=True,
    )
    covariance_fit = local_linear_covariance_surface(
        pairs,
        grid,
        bandwidth=covariance_bandwidth,
        min_local_pairs=covariance_min_local_pairs,
    )

    noise_result = None
    if noise_variance_method == "diagonal_difference":
        if noise_bandwidth is None:
            raise ValueError(
                "noise_bandwidth is required when "
                "noise_variance_method='diagonal_difference'"
            )
        noise_diagonal_fit = rotated_local_quadratic_covariance_diagonal(
            pairs,
            grid,
            bandwidth=covariance_bandwidth,
            min_local_pairs=covariance_min_local_pairs,
        )
        noise_result = estimate_noise_variance_diagonal_difference(
            curve_times,
            tuple(residuals),
            grid,
            covariance_fit.values,
            latent_diagonal=noise_diagonal_fit.values,
            bandwidth=noise_bandwidth,
            noise_support=noise_support,
            min_local_points=noise_min_local_points,
        )
        if noise_result.status_code != "ok":
            raise SparseNativeError(
                "noise_variance_invalid",
                "diagonal-difference measurement-noise estimate is not positive",
                details={
                    "estimated_noise_variance": float(noise_result.variance),
                    "minimum_diagonal_difference": float(
                        np.min(noise_result.diagonal_difference)
                    ),
                    "maximum_diagonal_difference": float(
                        np.max(noise_result.diagonal_difference)
                    ),
                },
            )
        noise_variance = float(noise_result.variance)
    else:
        noise_variance = float(measurement_error_variance)

    psd = repair_covariance_psd(
        covariance_fit.values,
        grid,
        action=psd_action,
        tolerance=psd_tolerance,
    )
    eigen = weighted_covariance_eigendecomposition(
        psd.covariance,
        grid,
        n_components=n_components,
        positive_tolerance=positive_eigen_tolerance,
    )
    scores = pace_scores(
        trajectories.curve_ids,
        curve_times,
        curve_values,
        evaluation_grid=grid,
        fitted_mean=mean_fit.values,
        fitted_covariance=psd.covariance,
        eigenvalues=eigen.eigenvalues,
        eigenfunctions=eigen.eigenfunctions,
        noise_variance=noise_variance,
        n_components=n_components,
        score_ridge=score_ridge,
        condition_limit=score_condition_limit,
        min_score_samples=min_score_samples,
        failure_action=score_failure_action,
    )

    covariance_diagnostics: dict[str, Any] = {
        "requested_action": psd.audit.requested_action,
        "applied_action": psd.audit.applied_action,
        "tolerance": psd.audit.tolerance,
        "pre_repair_operator_eigenvalues": (
            psd.audit.pre_repair_operator_eigenvalues.tolist()
        ),
        "negative_eigenvalue_count": psd.audit.negative_eigenvalue_count,
        "substantial_negative_eigenvalue_count": (
            psd.audit.substantial_negative_eigenvalue_count
        ),
        "most_negative_eigenvalue": psd.audit.most_negative_eigenvalue,
        "correction_frobenius_norm": psd.audit.correction_frobenius_norm,
        "relative_correction_frobenius_norm": (
            psd.audit.relative_correction_frobenius_norm
        ),
        "operator_correction_frobenius_norm": (
            psd.audit.operator_correction_frobenius_norm
        ),
        "relative_operator_correction_frobenius_norm": (
            psd.audit.relative_operator_correction_frobenius_norm
        ),
    }
    sparse_provenance: dict[str, Any] = {
        "backend": "native",
        "dimension": dimension,
        "n_components": n_components,
        "component_rank_rule": "positive_fitted_operator_spectrum",
        "mean_smoother": mean_smoother,
        "covariance_smoother": covariance_smoother,
        "kernel": kernel,
        "mean_bandwidth": float(mean_bandwidth),
        "covariance_bandwidth": float(covariance_bandwidth),
        "noise_bandwidth": (
            None if noise_bandwidth is None else float(noise_bandwidth)
        ),
        "noise_variance_method": noise_variance_method,
        "noise_variance": noise_variance,
        "noise_latent_diagonal_method": (
            None
            if noise_result is None
            else "rotated_local_quadratic_offdiagonal"
        ),
        "noise_latent_diagonal_bandwidth": (
            None
            if noise_result is None
            else float(covariance_bandwidth)
        ),
        "noise_support": (
            None
            if noise_result is None
            else list(noise_result.support_interval)
        ),
        "evaluation_grid": grid.tolist(),
        **support_diagnostics,
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "positive_eigen_tolerance": float(positive_eigen_tolerance),
        "score_method": "PACE",
        "score_covariance_source": scores.covariance_source,
        "score_ridge": float(score_ridge),
        "score_condition_limit": float(score_condition_limit),
        "min_score_samples": int(min_score_samples),
        "score_failure_action": score_failure_action,
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "noise_min_local_points": int(noise_min_local_points),
        "sample_counts": [int(len(time)) for time in curve_times],
        "raw_sparse_trajectory_interpolation_performed": False,
        "population_function_evaluation_at_native_times": True,
        "cross_channel_covariance_modeled": False,
        "automatic_bandwidth_selection_performed": False,
        "covariance_psd": covariance_diagnostics,
    }
    if measurement_error_variance is not None:
        sparse_provenance["measurement_error_variance_supplied"] = float(
            measurement_error_variance
        )

    return SparseFPCAResult(
        scores=scores.scores,
        eigenvalues=eigen.eigenvalues,
        dimension=dimension,
        curve_ids=trajectories.curve_ids,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        n_components=n_components,
        fit_method="native_covariance",
        fit_smoothing="local_linear_epanechnikov",
        score_method="PACE",
        score_smoothing=None,
        tolerance=float(positive_eigen_tolerance),
        normalize=False,
        provenance={
            **dict(trajectories.provenance),
            "sparse_fpca": sparse_provenance,
        },
        evaluation_grid=grid.copy(),
        mean=mean_fit.values.copy(),
        covariance=psd.covariance.copy(),
        eigenfunctions=eigen.eigenfunctions.copy(),
        noise_variance=noise_variance,
        quadrature_weights=eigen.quadrature_weights.copy(),
        score_diagnostics=scores.diagnostics.copy(),
        covariance_diagnostics=covariance_diagnostics,
        mean_support_counts=mean_fit.support_counts.copy(),
        covariance_support_counts=covariance_fit.support_counts.copy(),
        noise_raw_diagonal=(
            None
            if noise_result is None
            else noise_result.raw_diagonal.copy()
        ),
        noise_diagonal_difference=(
            None
            if noise_result is None
            else noise_result.diagonal_difference.copy()
        ),
    )
