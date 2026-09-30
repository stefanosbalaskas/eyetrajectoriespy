"""Native sparse multivariate FPCA for joint irregular functional channels."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from ._sparse_multivariate import (
    covariance_matrix_to_blocks,
    local_linear_cross_covariance_surface,
    multivariate_pace_scores,
    raw_cross_covariance_pairs,
    repair_block_covariance_psd,
    weighted_block_covariance_eigendecomposition,
)
from ._sparse_native import (
    SparseNativeError,
    estimate_noise_variance_diagonal_difference,
    local_linear_covariance_surface,
    local_linear_smooth_1d,
    raw_offdiagonal_covariance_pairs,
    rotated_local_quadratic_covariance_diagonal,
)
from .fpca import functional_trapezoid_weights
from .types import IrregularTrajectorySet, SparseMFPCAResult


def _validate_dimensions(
    trajectories: IrregularTrajectorySet,
    dimensions: tuple[str, ...] | None,
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if trajectories.n_curves < 3:
        raise SparseNativeError(
            "insufficient_pooled_support",
            "native sparse MFPCA requires at least three curves",
            details={"n_curves": trajectories.n_curves},
        )

    selected = (
        trajectories.dimension_names
        if dimensions is None
        else tuple(map(str, dimensions))
    )
    if len(selected) < 2:
        raise ValueError("fit_sparse_mfpca requires at least two dimensions")
    if len(set(selected)) != len(selected):
        raise ValueError("dimensions must be unique")
    unknown = [
        dimension
        for dimension in selected
        if dimension not in trajectories.dimension_names
    ]
    if unknown:
        raise KeyError(f"Unknown dimensions: {unknown!r}")

    indices = tuple(
        trajectories.dimension_names.index(dimension)
        for dimension in selected
    )
    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        chosen = np.asarray(values[:, indices], dtype=float)
        if not np.all(np.isfinite(chosen)):
            raise SparseNativeError(
                "nonfinite_sparse_observation",
                "absent sparse observations must be represented by absent samples",
                details={
                    "curve_id": str(curve_id),
                    "dimensions": list(selected),
                    "n_nonfinite": int(
                        np.count_nonzero(~np.isfinite(chosen))
                    ),
                },
            )
    return selected, indices


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
    selected_indices: tuple[int, ...],
    grid: np.ndarray,
    *,
    action: str,
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...], dict[str, Any]]:
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

    for time, values in zip(
        trajectories.time,
        trajectories.values,
        strict=True,
    ):
        time_array = np.asarray(time, dtype=float)
        value_array = np.asarray(values[:, selected_indices], dtype=float)
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


def _validate_settings(
    *,
    n_components: int,
    mean_smoother: str,
    covariance_smoother: str,
    kernel: str,
    noise_variance_method: str,
    measurement_error_variances: Mapping[str, float] | None,
    selected_dimensions: tuple[str, ...],
    noise_support: tuple[float, float] | None,
    noise_bandwidth: float | None,
    cross_channel_measurement_error: str,
) -> dict[str, float] | None:
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
    if cross_channel_measurement_error != "independent":
        raise ValueError(
            "cross_channel_measurement_error must be 'independent' "
            "in the first native tranche"
        )
    if noise_variance_method not in {"diagonal_difference", "fixed"}:
        raise ValueError(
            "noise_variance_method must be 'diagonal_difference' or 'fixed'"
        )

    if noise_variance_method == "fixed":
        if measurement_error_variances is None:
            raise ValueError(
                "measurement_error_variances is required when "
                "noise_variance_method='fixed'"
            )
        supplied = dict(measurement_error_variances)
        if set(supplied) != set(selected_dimensions):
            raise ValueError(
                "measurement_error_variances must contain exactly the "
                "selected dimension names"
            )
        parsed: dict[str, float] = {}
        for dimension in selected_dimensions:
            value = float(supplied[dimension])
            if not np.isfinite(value) or value < 0:
                raise ValueError(
                    "measurement_error_variances must be finite and non-negative"
                )
            parsed[dimension] = value
        if noise_support is not None or noise_bandwidth is not None:
            raise ValueError(
                "noise_support and noise_bandwidth must be None when "
                "noise_variance_method='fixed'"
            )
        return parsed

    if measurement_error_variances is not None:
        raise ValueError(
            "measurement_error_variances must be None when "
            "noise_variance_method='diagonal_difference'"
        )
    if noise_support is None:
        raise ValueError(
            "noise_support is required when "
            "noise_variance_method='diagonal_difference'"
        )
    if noise_bandwidth is None:
        raise ValueError(
            "noise_bandwidth is required when "
            "noise_variance_method='diagonal_difference'"
        )
    return None


def fit_sparse_mfpca(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, ...] | None = None,
    n_components: int,
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    covariance_bandwidth: float,
    cross_covariance_bandwidth: float | None = None,
    noise_bandwidth: float | None = None,
    noise_support: tuple[float, float] | None = None,
    noise_variance_method: str = "diagonal_difference",
    measurement_error_variances: Mapping[str, float] | None = None,
    cross_channel_measurement_error: str = "independent",
    analysis_support_action: str = "error",
    mean_smoother: str = "local_linear",
    covariance_smoother: str = "local_linear",
    kernel: str = "epanechnikov",
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    positive_eigen_tolerance: float = 1e-10,
    score_ridge: float = 0.0,
    score_condition_limit: float = 1e12,
    min_score_samples: int = 2,
    score_failure_action: str = "error",
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
    cross_covariance_min_local_pairs: int = 6,
    noise_min_local_points: int = 3,
) -> SparseMFPCAResult:
    """Fit native sparse multivariate FPCA with joint conditional scores.

    The estimator fits channel-specific pooled means and marginal latent
    covariance surfaces, directed cross-channel covariance surfaces, one joint
    block covariance operator, one joint eigensystem, and PACE-style
    conditional scores from the full fitted block covariance.

    Raw sparse trajectories remain on native curve-specific grids. No automatic
    bandwidth selection, interpolation, channel selection, or cross-channel
    measurement-error estimation is performed.
    """

    selected_dimensions, selected_indices = _validate_dimensions(
        trajectories,
        dimensions,
    )
    grid = _validate_evaluation_grid(trajectories, evaluation_grid)
    fixed_noise = _validate_settings(
        n_components=n_components,
        mean_smoother=mean_smoother,
        covariance_smoother=covariance_smoother,
        kernel=kernel,
        noise_variance_method=noise_variance_method,
        measurement_error_variances=measurement_error_variances,
        selected_dimensions=selected_dimensions,
        noise_support=noise_support,
        noise_bandwidth=noise_bandwidth,
        cross_channel_measurement_error=cross_channel_measurement_error,
    )
    cross_bandwidth = (
        float(covariance_bandwidth)
        if cross_covariance_bandwidth is None
        else float(cross_covariance_bandwidth)
    )
    if not np.isfinite(cross_bandwidth) or cross_bandwidth <= 0:
        raise ValueError(
            "cross_covariance_bandwidth must be finite and positive"
        )

    curve_times, curve_values, support_diagnostics = _analysis_support_views(
        trajectories,
        selected_indices,
        grid,
        action=analysis_support_action,
    )
    pooled_time = np.concatenate(curve_times)
    n_dimensions = len(selected_dimensions)
    n_grid = grid.size

    means = np.empty((n_grid, n_dimensions), dtype=float)
    covariance_blocks = np.empty(
        (n_dimensions, n_grid, n_dimensions, n_grid),
        dtype=float,
    )
    noise_variances = np.empty(n_dimensions, dtype=float)

    residuals_by_dimension: list[tuple[np.ndarray, ...]] = []
    mean_support_counts: dict[str, np.ndarray] = {}
    covariance_support_counts: dict[str, np.ndarray] = {}
    cross_support_counts: dict[str, np.ndarray] = {}
    noise_raw_diagonal: dict[str, np.ndarray] = {}
    noise_diagonal_difference: dict[str, np.ndarray] = {}

    for dimension_index, dimension in enumerate(selected_dimensions):
        scalar_values = tuple(
            np.asarray(values[:, dimension_index], dtype=float)
            for values in curve_values
        )
        pooled_values = np.concatenate(scalar_values)
        mean_fit = local_linear_smooth_1d(
            pooled_time,
            pooled_values,
            grid,
            bandwidth=mean_bandwidth,
            min_local_points=mean_min_local_points,
        )
        means[:, dimension_index] = mean_fit.values
        mean_support_counts[dimension] = mean_fit.support_counts.copy()

        residuals: list[np.ndarray] = []
        for time, observed in zip(
            curve_times,
            scalar_values,
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
        residual_tuple = tuple(residuals)
        residuals_by_dimension.append(residual_tuple)

        pairs = raw_offdiagonal_covariance_pairs(
            curve_times,
            residual_tuple,
            include_mirror=True,
        )
        covariance_fit = local_linear_covariance_surface(
            pairs,
            grid,
            bandwidth=covariance_bandwidth,
            min_local_pairs=covariance_min_local_pairs,
        )
        covariance_blocks[
            dimension_index,
            :,
            dimension_index,
            :,
        ] = covariance_fit.values
        covariance_support_counts[
            dimension
        ] = covariance_fit.support_counts.copy()

        if noise_variance_method == "diagonal_difference":
            noise_diagonal_fit = (
                rotated_local_quadratic_covariance_diagonal(
                    pairs,
                    grid,
                    bandwidth=covariance_bandwidth,
                    min_local_pairs=covariance_min_local_pairs,
                )
            )
            noise_result = estimate_noise_variance_diagonal_difference(
                curve_times,
                residual_tuple,
                grid,
                covariance_fit.values,
                latent_diagonal=noise_diagonal_fit.values,
                bandwidth=float(noise_bandwidth),
                noise_support=noise_support,
                min_local_points=noise_min_local_points,
            )
            if noise_result.status_code != "ok":
                raise SparseNativeError(
                    "noise_variance_invalid",
                    "diagonal-difference measurement-noise estimate "
                    f"is not positive for dimension {dimension!r}",
                    details={
                        "dimension": dimension,
                        "estimated_noise_variance": float(
                            noise_result.variance
                        ),
                        "minimum_diagonal_difference": float(
                            np.min(noise_result.diagonal_difference)
                        ),
                        "maximum_diagonal_difference": float(
                            np.max(noise_result.diagonal_difference)
                        ),
                    },
                )
            noise_variances[dimension_index] = float(noise_result.variance)
            noise_raw_diagonal[dimension] = (
                noise_result.raw_diagonal.copy()
            )
            noise_diagonal_difference[dimension] = (
                noise_result.diagonal_difference.copy()
            )
        else:
            noise_variances[dimension_index] = float(
                fixed_noise[dimension]
            )

    for left_dimension in range(n_dimensions - 1):
        for right_dimension in range(left_dimension + 1, n_dimensions):
            pairs = raw_cross_covariance_pairs(
                curve_times,
                residuals_by_dimension[left_dimension],
                residuals_by_dimension[right_dimension],
            )
            cross_fit = local_linear_cross_covariance_surface(
                pairs,
                grid,
                bandwidth=cross_bandwidth,
                min_local_pairs=cross_covariance_min_local_pairs,
            )
            covariance_blocks[
                left_dimension,
                :,
                right_dimension,
                :,
            ] = cross_fit.values
            covariance_blocks[
                right_dimension,
                :,
                left_dimension,
                :,
            ] = cross_fit.values.T
            key = (
                f"{selected_dimensions[left_dimension]}|"
                f"{selected_dimensions[right_dimension]}"
            )
            cross_support_counts[key] = cross_fit.support_counts.copy()

    psd = repair_block_covariance_psd(
        covariance_blocks,
        grid,
        action=psd_action,
        tolerance=psd_tolerance,
    )
    repaired_blocks = covariance_matrix_to_blocks(
        psd.covariance,
        n_dimensions=n_dimensions,
        n_grid=n_grid,
    )
    eigen = weighted_block_covariance_eigendecomposition(
        psd.covariance,
        grid,
        n_dimensions=n_dimensions,
        n_components=n_components,
        positive_tolerance=positive_eigen_tolerance,
    )
    eigenfunctions = (
        eigen.eigenfunctions
        .reshape(n_components, n_dimensions, n_grid)
        .transpose(0, 2, 1)
    )

    total_variance = float(
        np.sum(
            np.diag(psd.covariance)
            * eigen.quadrature_weights
        )
    )
    if not np.isfinite(total_variance) or total_variance <= 0:
        raise SparseNativeError(
            "nonpositive_joint_variance",
            "repaired block covariance has non-positive integrated variance",
            details={"total_variance": total_variance},
        )
    explained_variance_ratio = eigen.eigenvalues / total_variance

    scores = multivariate_pace_scores(
        trajectories.curve_ids,
        curve_times,
        curve_values,
        evaluation_grid=grid,
        fitted_mean=means,
        fitted_covariance_blocks=repaired_blocks,
        eigenvalues=eigen.eigenvalues,
        eigenfunctions=eigenfunctions,
        noise_variances=noise_variances,
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
        "correction_frobenius_norm": (
            psd.audit.correction_frobenius_norm
        ),
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

    sparse_mfpca_provenance: dict[str, Any] = {
        "backend": "native",
        "dimensions": list(selected_dimensions),
        "n_components": int(n_components),
        "component_rank_rule": "positive_fitted_block_operator_spectrum",
        "mean_smoother": mean_smoother,
        "covariance_smoother": covariance_smoother,
        "cross_covariance_smoother": "local_linear",
        "kernel": kernel,
        "mean_bandwidth": float(mean_bandwidth),
        "covariance_bandwidth": float(covariance_bandwidth),
        "cross_covariance_bandwidth": cross_bandwidth,
        "noise_bandwidth": (
            None if noise_bandwidth is None else float(noise_bandwidth)
        ),
        "noise_variance_method": noise_variance_method,
        "noise_variances": {
            dimension: float(noise_variances[index])
            for index, dimension in enumerate(selected_dimensions)
        },
        "cross_channel_measurement_error": (
            cross_channel_measurement_error
        ),
        "cross_channel_noise_covariance_estimated": False,
        "evaluation_grid": grid.tolist(),
        **support_diagnostics,
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "positive_eigen_tolerance": float(positive_eigen_tolerance),
        "score_method": "joint_PACE",
        "score_covariance_source": scores.covariance_source,
        "score_ridge": float(score_ridge),
        "score_condition_limit": float(score_condition_limit),
        "min_score_samples": int(min_score_samples),
        "score_failure_action": score_failure_action,
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "cross_covariance_min_local_pairs": int(
            cross_covariance_min_local_pairs
        ),
        "noise_min_local_points": int(noise_min_local_points),
        "sample_counts": [int(len(time)) for time in curve_times],
        "raw_sparse_trajectory_interpolation_performed": False,
        "population_function_evaluation_at_native_times": True,
        "cross_channel_covariance_modeled": True,
        "automatic_bandwidth_selection_performed": False,
        "automatic_dimension_selection_performed": False,
        "joint_covariance_representation": "dimension_major_block_operator",
        "covariance_psd": covariance_diagnostics,
    }
    if noise_support is not None:
        sparse_mfpca_provenance["noise_support"] = list(noise_support)
    if fixed_noise is not None:
        sparse_mfpca_provenance[
            "measurement_error_variances_supplied"
        ] = dict(fixed_noise)

    return SparseMFPCAResult(
        scores=scores.scores,
        eigenvalues=eigen.eigenvalues.copy(),
        explained_variance_ratio=explained_variance_ratio.copy(),
        dimension_names=selected_dimensions,
        curve_ids=trajectories.curve_ids,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        n_components=n_components,
        evaluation_grid=grid.copy(),
        mean=means.copy(),
        covariance=repaired_blocks.copy(),
        eigenfunctions=eigenfunctions.copy(),
        noise_variances=noise_variances.copy(),
        quadrature_weights=functional_trapezoid_weights(grid),
        score_diagnostics=scores.diagnostics.copy(),
        covariance_diagnostics=covariance_diagnostics,
        mean_support_counts={
            key: value.copy()
            for key, value in mean_support_counts.items()
        },
        covariance_support_counts={
            key: value.copy()
            for key, value in covariance_support_counts.items()
        },
        cross_covariance_support_counts={
            key: value.copy()
            for key, value in cross_support_counts.items()
        },
        noise_raw_diagonal={
            key: value.copy()
            for key, value in noise_raw_diagonal.items()
        },
        noise_diagonal_difference={
            key: value.copy()
            for key, value in noise_diagonal_difference.items()
        },
        provenance={
            **dict(trajectories.provenance),
            "sparse_mfpca": sparse_mfpca_provenance,
        },
    )
