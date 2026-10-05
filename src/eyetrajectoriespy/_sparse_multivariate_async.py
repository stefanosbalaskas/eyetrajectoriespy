"""Private asynchronous sparse-planar MFPCA numerical primitives.

This module generalizes the native planar observation model so x and y may be
observed on different native time grids.  It does not interpolate, synchronize,
bin, or otherwise manufacture raw coordinate observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd

from ._sparse_multivariate import (
    PlanarCovarianceBlocks,
    PlanarCovarianceSupport,
    RawPlanarCovariancePairs,
    audit_repair_planar_covariance,
    evaluate_fitted_surface,
    resolve_measurement_error_covariance,
    smooth_planar_covariance_pairs,
)
from ._sparse_native import (
    RawCovariancePairs,
    SparseNativeError,
    local_linear_smooth_1d,
    raw_offdiagonal_covariance_pairs,
)
from .types import IrregularTrajectorySet


@dataclass(frozen=True)
class AsyncSparsePlanarMeanCovarianceResult:
    """Fitted asynchronous planar population mean/covariance objects."""

    evaluation_grid: np.ndarray
    dimension_names: tuple[str, str]
    mean: np.ndarray
    mean_support_counts: np.ndarray
    smoothed_covariance_blocks: PlanarCovarianceBlocks
    covariance_blocks: PlanarCovarianceBlocks
    covariance_support_counts: PlanarCovarianceSupport
    covariance_pair_counts: dict[str, int]
    operator_audit: Any
    curve_ids: tuple[str, ...]
    x_times: tuple[np.ndarray, ...]
    x_values: tuple[np.ndarray, ...]
    y_times: tuple[np.ndarray, ...]
    y_values: tuple[np.ndarray, ...]
    support_diagnostics: dict[str, object]
    pair_diagnostics: dict[str, object]
    provenance: dict[str, object]


@dataclass(frozen=True)
class AsyncObservationLayout:
    """One curve's deterministic scalar observation layout."""

    times: np.ndarray
    channels: np.ndarray
    values: np.ndarray
    source_indices: np.ndarray
    n_x: int
    n_y: int
    n_simultaneous_pairs: int
    order: str = "time_major_x_before_y_for_ties"


@dataclass(frozen=True)
class AsyncJointPACEScoreResult:
    """Asynchronous joint-PACE scores and per-curve diagnostics."""

    scores: np.ndarray
    diagnostics: pd.DataFrame
    measurement_error_covariance: np.ndarray
    provenance: dict[str, object]


def _validate_grid(evaluation_grid: np.ndarray) -> np.ndarray:
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
    return grid


def _positive_finite(value: float, *, name: str) -> float:
    number = float(value)
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def _same_time_tolerance(value: float) -> float:
    tolerance = float(value)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("same_time_tolerance must be finite and non-negative")
    return tolerance


def _validate_async_planar_input(
    trajectories: IrregularTrajectorySet,
    dimensions: tuple[str, str],
) -> tuple[int, int]:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if not isinstance(dimensions, tuple) or len(dimensions) != 2:
        raise TypeError("dimensions must be a two-name tuple")
    x_name, y_name = map(str, dimensions)
    if x_name == y_name:
        raise ValueError("dimensions must name two distinct coordinates")
    try:
        x_index = trajectories.dimension_names.index(x_name)
        y_index = trajectories.dimension_names.index(y_name)
    except ValueError as exc:
        raise KeyError(f"Unknown planar dimension in {dimensions!r}") from exc
    if trajectories.n_curves < 3:
        raise SparseNativeError(
            "insufficient_joint_support",
            "asynchronous sparse planar covariance estimation requires at least three curves",
            details={"n_curves": trajectories.n_curves},
        )

    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        x = np.asarray(values[:, x_index], dtype=float)
        y = np.asarray(values[:, y_index], dtype=float)
        if np.any(np.isinf(x)) or np.any(np.isinf(y)):
            raise SparseNativeError(
                "nonfinite_sparse_async_observation",
                "coordinate values may be finite or NaN but never infinite",
                details={"curve_id": str(curve_id)},
            )
        empty = np.isnan(x) & np.isnan(y)
        if np.any(empty):
            indices = np.flatnonzero(empty)
            raise SparseNativeError(
                "empty_async_timestamp_row",
                "each union timestamp must contain at least one requested coordinate",
                details={
                    "curve_id": str(curve_id),
                    "sample_indices": indices.tolist(),
                    "n_empty_rows": int(indices.size),
                },
            )
    return x_index, y_index


def prepare_async_planar_views(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    evaluation_grid: np.ndarray,
    analysis_support_action: str = "error",
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    dict[str, object],
]:
    """Extract exact coordinate-specific native views without interpolation."""

    if analysis_support_action not in {"error", "restrict"}:
        raise ValueError("analysis_support_action must be 'error' or 'restrict'")
    x_index, y_index = _validate_async_planar_input(trajectories, dimensions)
    grid = _validate_grid(evaluation_grid)
    start, end = float(grid[0]), float(grid[-1])

    x_times_out: list[np.ndarray] = []
    x_values_out: list[np.ndarray] = []
    y_times_out: list[np.ndarray] = []
    y_values_out: list[np.ndarray] = []

    original_union_counts: list[int] = []
    original_x_counts: list[int] = []
    original_y_counts: list[int] = []
    effective_x_counts: list[int] = []
    effective_y_counts: list[int] = []
    x_outside_counts: list[int] = []
    y_outside_counts: list[int] = []
    simultaneous_counts: list[int] = []
    x_only_counts: list[int] = []
    y_only_counts: list[int] = []

    pooled_x_times: list[np.ndarray] = []
    pooled_y_times: list[np.ndarray] = []

    for time, values in zip(trajectories.time, trajectories.values, strict=True):
        t = np.asarray(time, dtype=float)
        x = np.asarray(values[:, x_index], dtype=float)
        y = np.asarray(values[:, y_index], dtype=float)
        finite_x = np.isfinite(x)
        finite_y = np.isfinite(y)

        tx_raw = t[finite_x]
        xv_raw = x[finite_x]
        ty_raw = t[finite_y]
        yv_raw = y[finite_y]

        original_union_counts.append(int(t.size))
        original_x_counts.append(int(tx_raw.size))
        original_y_counts.append(int(ty_raw.size))
        simultaneous_counts.append(int(np.count_nonzero(finite_x & finite_y)))
        x_only_counts.append(int(np.count_nonzero(finite_x & ~finite_y)))
        y_only_counts.append(int(np.count_nonzero(~finite_x & finite_y)))
        pooled_x_times.append(tx_raw)
        pooled_y_times.append(ty_raw)

        x_inside = (tx_raw >= start) & (tx_raw <= end)
        y_inside = (ty_raw >= start) & (ty_raw <= end)
        x_outside_counts.append(int(np.count_nonzero(~x_inside)))
        y_outside_counts.append(int(np.count_nonzero(~y_inside)))

        if analysis_support_action == "restrict":
            tx = tx_raw[x_inside].copy()
            xv = xv_raw[x_inside].copy()
            ty = ty_raw[y_inside].copy()
            yv = yv_raw[y_inside].copy()
        else:
            tx = tx_raw.copy()
            xv = xv_raw.copy()
            ty = ty_raw.copy()
            yv = yv_raw.copy()

        x_times_out.append(tx)
        x_values_out.append(xv)
        y_times_out.append(ty)
        y_values_out.append(yv)
        effective_x_counts.append(int(tx.size))
        effective_y_counts.append(int(ty.size))

    all_x = np.concatenate(pooled_x_times)
    all_y = np.concatenate(pooled_y_times)
    if all_x.size < 3:
        raise SparseNativeError(
            "insufficient_async_x_support",
            "fewer than three x observations are available",
            details={"n_x_observations": int(all_x.size)},
        )
    if all_y.size < 3:
        raise SparseNativeError(
            "insufficient_async_y_support",
            "fewer than three y observations are available",
            details={"n_y_observations": int(all_y.size)},
        )

    x_min, x_max = float(np.min(all_x)), float(np.max(all_x))
    y_min, y_max = float(np.min(all_y)), float(np.max(all_y))
    scale = max(1.0, abs(x_min), abs(x_max), abs(y_min), abs(y_max))
    tolerance = 1e-12 * scale
    if (
        start < x_min - tolerance
        or end > x_max + tolerance
        or start < y_min - tolerance
        or end > y_max + tolerance
    ):
        raise SparseNativeError(
            "evaluation_grid_outside_coordinate_support",
            "evaluation_grid must lie within pooled observed support of both coordinates",
            details={
                "grid_start": start,
                "grid_end": end,
                "x_support": [x_min, x_max],
                "y_support": [y_min, y_max],
            },
        )

    outside_total = int(np.sum(x_outside_counts) + np.sum(y_outside_counts))
    if analysis_support_action == "error" and outside_total:
        raise SparseNativeError(
            "observations_outside_analysis_support",
            "coordinate observations lie outside the declared evaluation-grid support",
            details={
                "analysis_support": [start, end],
                "x_outside_counts_by_curve": x_outside_counts,
                "y_outside_counts_by_curve": y_outside_counts,
                "outside_coordinate_observation_count": outside_total,
            },
        )

    if int(np.sum(effective_x_counts)) < 3:
        raise SparseNativeError(
            "insufficient_async_x_support",
            "fewer than three x observations remain on declared support",
            details={"analysis_sample_count_x": int(np.sum(effective_x_counts))},
        )
    if int(np.sum(effective_y_counts)) < 3:
        raise SparseNativeError(
            "insufficient_async_y_support",
            "fewer than three y observations remain on declared support",
            details={"analysis_sample_count_y": int(np.sum(effective_y_counts))},
        )

    diagnostics: dict[str, object] = {
        "analysis_support": [start, end],
        "analysis_support_action": analysis_support_action,
        "original_union_sample_counts": original_union_counts,
        "original_x_sample_counts": original_x_counts,
        "original_y_sample_counts": original_y_counts,
        "analysis_x_sample_counts": effective_x_counts,
        "analysis_y_sample_counts": effective_y_counts,
        "x_outside_counts_by_curve": x_outside_counts,
        "y_outside_counts_by_curve": y_outside_counts,
        "simultaneous_sample_counts": simultaneous_counts,
        "x_only_sample_counts": x_only_counts,
        "y_only_sample_counts": y_only_counts,
        "outside_coordinate_observation_count": outside_total,
    }
    return (
        tuple(x_times_out),
        tuple(x_values_out),
        tuple(y_times_out),
        tuple(y_values_out),
        diagnostics,
    )


def raw_async_planar_covariance_pairs(
    x_times: Sequence[np.ndarray],
    residual_x: Sequence[np.ndarray],
    y_times: Sequence[np.ndarray],
    residual_y: Sequence[np.ndarray],
    *,
    same_time_tolerance: float = 0.0,
) -> tuple[RawPlanarCovariancePairs, dict[str, object]]:
    """Construct xx/xy/yy residual-product sets on coordinate-specific grids."""

    if not (
        len(x_times)
        == len(residual_x)
        == len(y_times)
        == len(residual_y)
    ):
        raise ValueError("asynchronous coordinate sequences must have equal curve counts")
    tolerance = _same_time_tolerance(same_time_tolerance)

    xx = raw_offdiagonal_covariance_pairs(
        x_times,
        residual_x,
        include_mirror=True,
    )
    yy = raw_offdiagonal_covariance_pairs(
        y_times,
        residual_y,
        include_mirror=True,
    )

    s_values: list[float] = []
    t_values: list[float] = []
    products: list[float] = []
    curve_indices: list[int] = []
    candidate_count = 0
    excluded_same_time_count = 0

    for curve_index, (tx, rx, ty, ry) in enumerate(
        zip(x_times, residual_x, y_times, residual_y, strict=True)
    ):
        txa = np.asarray(tx, dtype=float)
        rxa = np.asarray(rx, dtype=float)
        tya = np.asarray(ty, dtype=float)
        rya = np.asarray(ry, dtype=float)
        if (
            txa.ndim != 1
            or rxa.ndim != 1
            or tya.ndim != 1
            or rya.ndim != 1
            or txa.shape != rxa.shape
            or tya.shape != rya.shape
        ):
            raise ValueError("each coordinate time/residual pair must be aligned")
        if (
            not np.all(np.isfinite(txa))
            or not np.all(np.isfinite(rxa))
            or not np.all(np.isfinite(tya))
            or not np.all(np.isfinite(rya))
        ):
            raise ValueError("asynchronous coordinate times/residuals must be finite")

        for ix, tx_value in enumerate(txa):
            for iy, ty_value in enumerate(tya):
                candidate_count += 1
                if abs(float(tx_value) - float(ty_value)) <= tolerance:
                    excluded_same_time_count += 1
                    continue
                s_values.append(float(tx_value))
                t_values.append(float(ty_value))
                products.append(float(rxa[ix] * rya[iy]))
                curve_indices.append(curve_index)

    if len(products) < 3:
        raise SparseNativeError(
            "insufficient_async_cross_covariance_pairs",
            "fewer than three asynchronous x-y covariance pairs remain after same-time exclusion",
            details={
                "candidate_cross_pairs": candidate_count,
                "same_time_pairs_excluded": excluded_same_time_count,
                "retained_cross_pairs": len(products),
                "same_time_tolerance": tolerance,
            },
        )

    xy = RawCovariancePairs(
        s=np.asarray(s_values, dtype=float),
        t=np.asarray(t_values, dtype=float),
        products=np.asarray(products, dtype=float),
        curve_index=np.asarray(curve_indices, dtype=int),
        mirrored=False,
    )
    pairs = RawPlanarCovariancePairs(
        xx=xx,
        xy=xy,
        yy=yy,
        same_time_pairs_excluded=True,
        yx_estimated_independently=False,
    )
    diagnostics = {
        "cross_candidate_pair_count": int(candidate_count),
        "cross_same_time_pair_count_excluded": int(excluded_same_time_count),
        "cross_retained_pair_count": int(len(products)),
        "same_time_tolerance": float(tolerance),
    }
    return pairs, diagnostics


def estimate_async_sparse_planar_mean_covariance(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    covariance_bandwidth: float,
    analysis_support_action: str = "error",
    same_time_tolerance: float = 0.0,
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    symmetry_tolerance: float = 1e-10,
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
) -> AsyncSparsePlanarMeanCovarianceResult:
    """Estimate asynchronous vector mean and latent planar covariance."""

    grid = _validate_grid(evaluation_grid)
    mean_bandwidth = _positive_finite(mean_bandwidth, name="mean_bandwidth")
    covariance_bandwidth = _positive_finite(
        covariance_bandwidth,
        name="covariance_bandwidth",
    )
    tolerance = _same_time_tolerance(same_time_tolerance)
    (
        x_times,
        x_values,
        y_times,
        y_values,
        support_diagnostics,
    ) = prepare_async_planar_views(
        trajectories,
        dimensions=dimensions,
        evaluation_grid=grid,
        analysis_support_action=analysis_support_action,
    )

    pooled_tx = np.concatenate(x_times)
    pooled_x = np.concatenate(x_values)
    pooled_ty = np.concatenate(y_times)
    pooled_y = np.concatenate(y_values)

    mean_x = local_linear_smooth_1d(
        pooled_tx,
        pooled_x,
        grid,
        bandwidth=mean_bandwidth,
        min_local_points=mean_min_local_points,
    )
    mean_y = local_linear_smooth_1d(
        pooled_ty,
        pooled_y,
        grid,
        bandwidth=mean_bandwidth,
        min_local_points=mean_min_local_points,
    )

    residual_x: list[np.ndarray] = []
    residual_y: list[np.ndarray] = []
    for tx, observed_x, ty, observed_y in zip(
        x_times,
        x_values,
        y_times,
        y_values,
        strict=True,
    ):
        if tx.size:
            mx = local_linear_smooth_1d(
                pooled_tx,
                pooled_x,
                tx,
                bandwidth=mean_bandwidth,
                min_local_points=mean_min_local_points,
            ).values
            residual_x.append(observed_x - mx)
        else:
            residual_x.append(np.asarray([], dtype=float))
        if ty.size:
            my = local_linear_smooth_1d(
                pooled_ty,
                pooled_y,
                ty,
                bandwidth=mean_bandwidth,
                min_local_points=mean_min_local_points,
            ).values
            residual_y.append(observed_y - my)
        else:
            residual_y.append(np.asarray([], dtype=float))

    pairs, pair_diagnostics = raw_async_planar_covariance_pairs(
        x_times,
        tuple(residual_x),
        y_times,
        tuple(residual_y),
        same_time_tolerance=tolerance,
    )
    smoothed_blocks, support_counts = smooth_planar_covariance_pairs(
        pairs,
        grid,
        bandwidth=covariance_bandwidth,
        min_local_pairs=covariance_min_local_pairs,
    )
    operator = audit_repair_planar_covariance(
        smoothed_blocks.cxx,
        smoothed_blocks.cxy,
        smoothed_blocks.cyy,
        grid,
        cyx=smoothed_blocks.cyx,
        action=psd_action,
        tolerance=psd_tolerance,
        symmetry_tolerance=symmetry_tolerance,
    )

    provenance: dict[str, object] = {
        "backend": "native_async_planar_covariance",
        "dimensions": [str(dimensions[0]), str(dimensions[1])],
        "input_representation": "exact_union_of_native_coordinate_timestamps",
        "coordinate_specific_missingness_supported": True,
        "raw_sparse_trajectory_interpolation_performed": False,
        "nearest_neighbour_synchronization_performed": False,
        "time_binning_performed": False,
        "population_function_evaluation_at_native_times": True,
        "mean_smoother": "local_linear_epanechnikov_per_coordinate",
        "covariance_smoother": "local_linear_product_epanechnikov",
        "mean_bandwidth": float(mean_bandwidth),
        "covariance_bandwidth": float(covariance_bandwidth),
        "cross_covariance_same_time_products_excluded": True,
        "measurement_error_cross_covariance_contamination_avoided": True,
        "measurement_error_independent_across_distinct_times_assumed": True,
        "same_time_tolerance": float(tolerance),
        "yx_estimated_independently": False,
        "cross_covariance_self_symmetrized": False,
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "symmetry_tolerance": float(symmetry_tolerance),
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        **support_diagnostics,
        **pair_diagnostics,
    }
    return AsyncSparsePlanarMeanCovarianceResult(
        evaluation_grid=grid.copy(),
        dimension_names=(str(dimensions[0]), str(dimensions[1])),
        mean=np.vstack([mean_x.values, mean_y.values]),
        mean_support_counts=np.vstack(
            [mean_x.support_counts, mean_y.support_counts]
        ),
        smoothed_covariance_blocks=operator.smoothed_covariance_blocks,
        covariance_blocks=operator.covariance_blocks,
        covariance_support_counts=support_counts,
        covariance_pair_counts={
            "xx": int(pairs.xx.n_pairs),
            "xy": int(pairs.xy.n_pairs),
            "yy": int(pairs.yy.n_pairs),
        },
        operator_audit=operator.audit,
        curve_ids=trajectories.curve_ids,
        x_times=tuple(value.copy() for value in x_times),
        x_values=tuple(value.copy() for value in x_values),
        y_times=tuple(value.copy() for value in y_times),
        y_values=tuple(value.copy() for value in y_values),
        support_diagnostics=dict(support_diagnostics),
        pair_diagnostics=dict(pair_diagnostics),
        provenance=provenance,
    )


def build_async_observation_layout(
    x_times: np.ndarray,
    x_values: np.ndarray,
    y_times: np.ndarray,
    y_values: np.ndarray,
    *,
    same_time_tolerance: float = 0.0,
) -> AsyncObservationLayout:
    """Stack finite coordinate observations by time, x before y for ties."""

    tx = np.asarray(x_times, dtype=float)
    xv = np.asarray(x_values, dtype=float)
    ty = np.asarray(y_times, dtype=float)
    yv = np.asarray(y_values, dtype=float)
    tolerance = _same_time_tolerance(same_time_tolerance)
    if (
        tx.ndim != 1
        or xv.ndim != 1
        or ty.ndim != 1
        or yv.ndim != 1
        or tx.shape != xv.shape
        or ty.shape != yv.shape
    ):
        raise ValueError("coordinate times/values must be aligned one-dimensional arrays")
    if (
        not np.all(np.isfinite(tx))
        or not np.all(np.isfinite(xv))
        or not np.all(np.isfinite(ty))
        or not np.all(np.isfinite(yv))
    ):
        raise ValueError("coordinate-specific observations must be finite")

    entries: list[tuple[float, int, float, int]] = []
    entries.extend(
        (float(time), 0, float(value), int(index))
        for index, (time, value) in enumerate(zip(tx, xv, strict=True))
    )
    entries.extend(
        (float(time), 1, float(value), int(index))
        for index, (time, value) in enumerate(zip(ty, yv, strict=True))
    )
    entries.sort(key=lambda row: (row[0], row[1]))
    times = np.asarray([row[0] for row in entries], dtype=float)
    channels = np.asarray([row[1] for row in entries], dtype=int)
    values = np.asarray([row[2] for row in entries], dtype=float)
    source_indices = np.asarray([row[3] for row in entries], dtype=int)

    simultaneous = 0
    for x_time in tx:
        simultaneous += int(np.count_nonzero(np.abs(ty - x_time) <= tolerance))

    return AsyncObservationLayout(
        times=times,
        channels=channels,
        values=values,
        source_indices=source_indices,
        n_x=int(tx.size),
        n_y=int(ty.size),
        n_simultaneous_pairs=int(simultaneous),
    )


def evaluate_async_planar_covariance(
    evaluation_grid: np.ndarray,
    covariance_blocks: PlanarCovarianceBlocks,
    layout: AsyncObservationLayout,
) -> np.ndarray:
    """Evaluate full fitted planar covariance on arbitrary scalar observations."""

    grid = _validate_grid(evaluation_grid)
    times = np.asarray(layout.times, dtype=float)
    channels = np.asarray(layout.channels, dtype=int)
    if times.ndim != 1 or channels.shape != times.shape:
        raise ValueError("layout times/channels must be aligned")
    if np.any((channels < 0) | (channels > 1)):
        raise ValueError("layout channels must be 0 (x) or 1 (y)")
    if times.size == 0:
        return np.empty((0, 0), dtype=float)

    result = np.empty((times.size, times.size), dtype=float)
    ix = np.flatnonzero(channels == 0)
    iy = np.flatnonzero(channels == 1)

    if ix.size:
        result[np.ix_(ix, ix)] = evaluate_fitted_surface(
            grid,
            covariance_blocks.cxx,
            times[ix],
            times[ix],
        )
    if iy.size:
        result[np.ix_(iy, iy)] = evaluate_fitted_surface(
            grid,
            covariance_blocks.cyy,
            times[iy],
            times[iy],
        )
    if ix.size and iy.size:
        xy = evaluate_fitted_surface(
            grid,
            covariance_blocks.cxy,
            times[ix],
            times[iy],
        )
        result[np.ix_(ix, iy)] = xy
        result[np.ix_(iy, ix)] = xy.T

    return 0.5 * (result + result.T)


def build_async_measurement_error_covariance(
    layout: AsyncObservationLayout,
    measurement_error_covariance: np.ndarray,
    *,
    same_time_tolerance: float = 0.0,
) -> tuple[np.ndarray, int]:
    """Place channel noise variances and simultaneous cross-channel covariance."""

    tolerance = _same_time_tolerance(same_time_tolerance)
    resolved = resolve_measurement_error_covariance(
        "fixed_matrix",
        measurement_error_covariance=measurement_error_covariance,
    )
    times = np.asarray(layout.times, dtype=float)
    channels = np.asarray(layout.channels, dtype=int)
    noise = np.zeros((times.size, times.size), dtype=float)
    if times.size == 0:
        return noise, 0

    noise[np.diag_indices(times.size)] = resolved.covariance[channels, channels]
    cross_links = 0
    for left in range(times.size):
        for right in range(left + 1, times.size):
            if channels[left] == channels[right]:
                continue
            if abs(float(times[left]) - float(times[right])) <= tolerance:
                value = float(
                    resolved.covariance[channels[left], channels[right]]
                )
                noise[left, right] = value
                noise[right, left] = value
                cross_links += 1
    return noise, int(cross_links)


def stack_async_mean(
    evaluation_grid: np.ndarray,
    fitted_mean: np.ndarray,
    layout: AsyncObservationLayout,
) -> np.ndarray:
    """Evaluate the correct coordinate mean for every scalar observation."""

    grid = _validate_grid(evaluation_grid)
    mean = np.asarray(fitted_mean, dtype=float)
    if mean.shape != (2, grid.size):
        raise ValueError(f"fitted_mean must have shape (2, {grid.size})")
    output = np.empty(layout.times.size, dtype=float)
    for channel in (0, 1):
        indices = np.flatnonzero(layout.channels == channel)
        if indices.size:
            output[indices] = np.interp(
                layout.times[indices],
                grid,
                mean[channel],
            )
    return output


def stack_async_eigenfunctions(
    evaluation_grid: np.ndarray,
    eigenfunctions: np.ndarray,
    layout: AsyncObservationLayout,
    *,
    n_components: int,
) -> np.ndarray:
    """Evaluate the correct eigenfunction channel for every observation."""

    grid = _validate_grid(evaluation_grid)
    functions = np.asarray(eigenfunctions, dtype=float)
    if (
        functions.ndim != 3
        or functions.shape[1] != 2
        or functions.shape[2] != grid.size
    ):
        raise ValueError(
            "eigenfunctions must have shape (n_available_components, 2, n_grid)"
        )
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1 or n_components > functions.shape[0]:
        raise ValueError("n_components is outside the available eigenfunction range")

    output = np.empty((layout.times.size, n_components), dtype=float)
    for component in range(n_components):
        for channel in (0, 1):
            indices = np.flatnonzero(layout.channels == channel)
            if indices.size:
                output[indices, component] = np.interp(
                    layout.times[indices],
                    grid,
                    functions[component, channel],
                )
    return output


def async_joint_pace_scores(
    curve_ids: Sequence[str],
    x_times: Sequence[np.ndarray],
    x_values: Sequence[np.ndarray],
    y_times: Sequence[np.ndarray],
    y_values: Sequence[np.ndarray],
    *,
    evaluation_grid: np.ndarray,
    fitted_mean: np.ndarray,
    covariance_blocks: PlanarCovarianceBlocks,
    eigenvalues: np.ndarray,
    eigenfunctions: np.ndarray,
    measurement_error_covariance: np.ndarray,
    n_components: int,
    same_time_tolerance: float = 0.0,
    score_ridge: float = 0.0,
    condition_limit: float = 1e12,
    min_score_observations: int = 2,
    failure_action: str = "error",
) -> AsyncJointPACEScoreResult:
    """Recover joint PACE scores on genuinely asynchronous scalar observations."""

    if not (
        len(curve_ids)
        == len(x_times)
        == len(x_values)
        == len(y_times)
        == len(y_values)
    ):
        raise ValueError("curve and coordinate sequences must have equal lengths")
    grid = _validate_grid(evaluation_grid)
    mean = np.asarray(fitted_mean, dtype=float)
    values = np.asarray(eigenvalues, dtype=float)
    functions = np.asarray(eigenfunctions, dtype=float)
    if mean.shape != (2, grid.size):
        raise ValueError(f"fitted_mean must have shape (2, {grid.size})")
    if (
        functions.ndim != 3
        or functions.shape[1] != 2
        or functions.shape[2] != grid.size
    ):
        raise ValueError(
            "eigenfunctions must have shape (n_available_components, 2, n_grid)"
        )
    if values.ndim != 1 or values.size != functions.shape[0]:
        raise ValueError("eigenvalues must align with eigenfunctions")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1 or n_components > values.size:
        raise ValueError("n_components is outside the available eigenfunction range")

    resolved_error = resolve_measurement_error_covariance(
        "fixed_matrix",
        measurement_error_covariance=measurement_error_covariance,
    )
    tolerance = _same_time_tolerance(same_time_tolerance)
    score_ridge = float(score_ridge)
    if not np.isfinite(score_ridge) or score_ridge < 0:
        raise ValueError("score_ridge must be finite and non-negative")
    condition_limit = float(condition_limit)
    if not np.isfinite(condition_limit) or condition_limit <= 1:
        raise ValueError("condition_limit must be finite and greater than 1")
    if isinstance(min_score_observations, bool) or not isinstance(
        min_score_observations, int
    ):
        raise TypeError("min_score_observations must be an integer")
    if min_score_observations < 1:
        raise ValueError("min_score_observations must be positive")
    if failure_action not in {"error", "retain_nan"}:
        raise ValueError("failure_action must be 'error' or 'retain_nan'")

    scores = np.full((len(curve_ids), n_components), np.nan, dtype=float)
    rows: list[dict[str, Any]] = []
    first_failure: tuple[str, str, dict[str, Any]] | None = None

    for index, (curve_id, tx, xv, ty, yv) in enumerate(
        zip(curve_ids, x_times, x_values, y_times, y_values, strict=True)
    ):
        layout = build_async_observation_layout(
            tx,
            xv,
            ty,
            yv,
            same_time_tolerance=tolerance,
        )
        status_code = "ok"
        solve_status = "not_attempted"
        condition_number = np.nan
        minimum_eigenvalue = np.nan
        maximum_eigenvalue = np.nan
        cross_noise_links = 0

        if layout.times.size < min_score_observations:
            status_code = "curve_too_sparse_for_async_joint_score_system"
        else:
            try:
                latent = evaluate_async_planar_covariance(
                    grid,
                    covariance_blocks,
                    layout,
                )
                noise, cross_noise_links = build_async_measurement_error_covariance(
                    layout,
                    resolved_error.covariance,
                    same_time_tolerance=tolerance,
                )
                sigma = latent + noise + score_ridge * np.eye(layout.times.size)
                sigma = 0.5 * (sigma + sigma.T)
                sigma_eigenvalues = np.linalg.eigvalsh(sigma)
                minimum_eigenvalue = float(np.min(sigma_eigenvalues))
                maximum_eigenvalue = float(np.max(sigma_eigenvalues))
                condition_number = (
                    np.inf
                    if minimum_eigenvalue <= 0
                    else maximum_eigenvalue / minimum_eigenvalue
                )
                if minimum_eigenvalue <= 0:
                    status_code = (
                        "async_joint_score_covariance_not_positive_definite"
                    )
                elif condition_number > condition_limit:
                    status_code = "async_joint_score_covariance_ill_conditioned"
                else:
                    centered = layout.values - stack_async_mean(
                        grid,
                        mean,
                        layout,
                    )
                    phi = stack_async_eigenfunctions(
                        grid,
                        functions,
                        layout,
                        n_components=n_components,
                    )
                    solved = np.linalg.solve(sigma, centered)
                    scores[index] = values[:n_components] * (phi.T @ solved)
                    solve_status = "solved"
            except SparseNativeError as exc:
                status_code = exc.code

        row = {
            "curve_id": str(curve_id),
            "n_x_observations": int(layout.n_x),
            "n_y_observations": int(layout.n_y),
            "n_scalar_observations": int(layout.times.size),
            "n_simultaneous_pairs": int(layout.n_simultaneous_pairs),
            "measurement_error_cross_links": int(cross_noise_links),
            "status_code": status_code,
            "solve_status": solve_status,
            "condition_number": float(condition_number),
            "minimum_eigenvalue": float(minimum_eigenvalue),
            "maximum_eigenvalue": float(maximum_eigenvalue),
            "score_ridge": score_ridge,
            "condition_limit": condition_limit,
            "observation_order": layout.order,
        }
        rows.append(row)
        if status_code != "ok" and first_failure is None:
            first_failure = (status_code, str(curve_id), dict(row))

    diagnostics = pd.DataFrame(rows)
    if first_failure is not None and failure_action == "error":
        code, curve_id, details = first_failure
        raise SparseNativeError(
            code,
            f"asynchronous joint PACE score system failed for curve {curve_id!r}",
            details={
                **details,
                "all_curve_diagnostics": diagnostics.to_dict(orient="records"),
            },
        )

    provenance: dict[str, object] = {
        "score_observation_order": "time_major_x_before_y_for_ties",
        "paired_reduction_order": "time_major_interleaved_xy",
        "score_covariance_source": (
            "full_fitted_joint_covariance_plus_async_measurement_error"
        ),
        "rank_k_covariance_used_for_scoring": False,
        "raw_sparse_trajectory_interpolation_performed": False,
        "nearest_neighbour_synchronization_performed": False,
        "time_binning_performed": False,
        "population_function_evaluation_at_native_times": True,
        "measurement_error_covariance_mode": resolved_error.mode,
        "measurement_error_cross_covariance_scope": "simultaneous_xy_only",
        "same_time_tolerance": float(tolerance),
        "score_ridge": score_ridge,
        "condition_limit": condition_limit,
    }
    return AsyncJointPACEScoreResult(
        scores=scores,
        diagnostics=diagnostics,
        measurement_error_covariance=resolved_error.covariance.copy(),
        provenance=provenance,
    )
