"""Internal multivariate sparse-functional primitives for the 0.12 line.

This module deliberately stays below the public estimator surface.  It
contains joint planar covariance algebra plus the direct vector-mean and
latent covariance-block estimation machinery used to qualify that algebra
before joint PACE scoring is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ._sparse_native import (
    LocalLinear2DResult,
    RawCovariancePairs,
    SparseNativeError,
    epanechnikov_kernel,
    local_linear_smooth_1d,
    raw_offdiagonal_covariance_pairs,
)
from .fpca import functional_trapezoid_weights
from .types import IrregularTrajectorySet


@dataclass(frozen=True)
class PlanarCovarianceAudit:
    """Diagnostics for symmetry and PSD handling of a planar covariance."""

    requested_action: str
    applied_action: str
    tolerance: float
    symmetry_tolerance: float
    pre_enforcement_symmetry_error: float
    pre_repair_operator_eigenvalues: np.ndarray
    negative_eigenvalue_count: int
    substantial_negative_eigenvalue_count: int
    most_negative_eigenvalue: float
    correction_frobenius_norm: float
    relative_correction_frobenius_norm: float
    operator_correction_frobenius_norm: float
    relative_operator_correction_frobenius_norm: float


@dataclass(frozen=True)
class PlanarCovarianceBlocks:
    """Named planar covariance blocks."""

    cxx: np.ndarray
    cxy: np.ndarray
    cyx: np.ndarray
    cyy: np.ndarray

    @property
    def matrix(self) -> np.ndarray:
        """Return channel-major block matrix."""

        return np.block(
            [
                [self.cxx, self.cxy],
                [self.cyx, self.cyy],
            ]
        )


@dataclass(frozen=True)
class PlanarCovarianceSupport:
    """Local support counts for directly fitted xx, xy, and yy blocks."""

    cxx: np.ndarray
    cxy: np.ndarray
    cyy: np.ndarray


@dataclass(frozen=True)
class PlanarCovarianceOperatorResult:
    """Smoothed and downstream covariance blocks plus the repair audit.

    The smoothed fields retain exactly what entered the joint operator audit.
    The cxx/cxy/cyx/cyy fields are the covariance blocks actually used
    downstream after symmetry enforcement and any requested PSD projection.
    """

    smoothed_cxx: np.ndarray
    smoothed_cxy: np.ndarray
    smoothed_cyx: np.ndarray
    smoothed_cyy: np.ndarray
    smoothed_covariance_matrix: np.ndarray
    cxx: np.ndarray
    cxy: np.ndarray
    cyx: np.ndarray
    cyy: np.ndarray
    covariance_matrix: np.ndarray
    quadrature_weights: np.ndarray
    audit: PlanarCovarianceAudit

    @property
    def smoothed_covariance_blocks(self) -> PlanarCovarianceBlocks:
        return PlanarCovarianceBlocks(
            cxx=self.smoothed_cxx,
            cxy=self.smoothed_cxy,
            cyx=self.smoothed_cyx,
            cyy=self.smoothed_cyy,
        )

    @property
    def covariance_blocks(self) -> PlanarCovarianceBlocks:
        return PlanarCovarianceBlocks(
            cxx=self.cxx,
            cxy=self.cxy,
            cyx=self.cyx,
            cyy=self.cyy,
        )


@dataclass(frozen=True)
class PlanarWeightedEigendecomposition:
    """Quadrature-weighted joint eigendecomposition."""

    eigenvalues: np.ndarray
    eigenfunctions: np.ndarray
    quadrature_weights: np.ndarray


@dataclass(frozen=True)
class RawPlanarCovariancePairs:
    """Off-diagonal residual products for direct planar covariance fitting."""

    xx: RawCovariancePairs
    xy: RawCovariancePairs
    yy: RawCovariancePairs
    same_time_pairs_excluded: bool = True
    yx_estimated_independently: bool = False


@dataclass(frozen=True)
class SparsePlanarMeanCovarianceResult:
    """Internal direct sparse vector-mean and covariance-block fit."""

    evaluation_grid: np.ndarray
    dimension_names: tuple[str, str]
    mean: np.ndarray
    mean_support_counts: np.ndarray
    smoothed_covariance_blocks: PlanarCovarianceBlocks
    covariance_blocks: PlanarCovarianceBlocks
    covariance_support_counts: PlanarCovarianceSupport
    covariance_pair_counts: dict[str, int]
    operator_audit: PlanarCovarianceAudit
    curve_ids: tuple[str, ...]
    analysis_sample_counts: tuple[int, ...]
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


def _validate_block(
    block: np.ndarray,
    *,
    grid_size: int,
    name: str,
) -> np.ndarray:
    matrix = np.asarray(block, dtype=float)
    if matrix.shape != (grid_size, grid_size):
        raise ValueError(
            f"{name} must have shape ({grid_size}, {grid_size})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must contain only finite values")
    return matrix


def _relative_frobenius(delta: np.ndarray, baseline: np.ndarray) -> float:
    numerator = float(np.linalg.norm(delta, ord="fro"))
    denominator = float(np.linalg.norm(baseline, ord="fro"))
    return 0.0 if denominator == 0.0 else numerator / denominator


def _validate_planar_input(
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
        raise KeyError(
            f"Unknown planar dimension in {dimensions!r}"
        ) from exc
    if trajectories.n_curves < 3:
        raise SparseNativeError(
            "insufficient_joint_support",
            "sparse planar covariance estimation requires at least three curves",
            details={"n_curves": trajectories.n_curves},
        )

    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        x = np.asarray(values[:, x_index], dtype=float)
        y = np.asarray(values[:, y_index], dtype=float)
        finite_x = np.isfinite(x)
        finite_y = np.isfinite(y)
        coordinate_mismatch = finite_x != finite_y
        if np.any(coordinate_mismatch):
            indices = np.flatnonzero(coordinate_mismatch)
            raise SparseNativeError(
                "coordinate_specific_missingness_unsupported",
                "x and y must be jointly observed at every retained sparse timestamp",
                details={
                    "curve_id": str(curve_id),
                    "n_coordinate_specific_missing": int(indices.size),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
        jointly_nonfinite = ~(finite_x & finite_y)
        if np.any(jointly_nonfinite):
            indices = np.flatnonzero(jointly_nonfinite)
            raise SparseNativeError(
                "nonfinite_sparse_planar_observation",
                "absent planar observations must be represented by absent samples",
                details={
                    "curve_id": str(curve_id),
                    "n_nonfinite_joint_samples": int(indices.size),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
    return x_index, y_index


def _prepare_planar_analysis_views(
    trajectories: IrregularTrajectorySet,
    *,
    x_index: int,
    y_index: int,
    evaluation_grid: np.ndarray,
    action: str,
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    dict[str, object],
]:
    if action not in {"error", "restrict"}:
        raise ValueError(
            "analysis_support_action must be 'error' or 'restrict'"
        )

    grid = _validate_grid(evaluation_grid)
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

    start = float(grid[0])
    end = float(grid[-1])
    times_out: list[np.ndarray] = []
    x_out: list[np.ndarray] = []
    y_out: list[np.ndarray] = []
    outside_counts: list[int] = []
    in_support_counts: list[int] = []

    for time, values in zip(
        trajectories.time,
        trajectories.values,
        strict=True,
    ):
        time_array = np.asarray(time, dtype=float)
        x = np.asarray(values[:, x_index], dtype=float)
        y = np.asarray(values[:, y_index], dtype=float)
        mask = (time_array >= start) & (time_array <= end)
        outside_counts.append(int(np.count_nonzero(~mask)))
        in_support_counts.append(int(np.count_nonzero(mask)))
        if action == "restrict":
            times_out.append(time_array[mask].copy())
            x_out.append(x[mask].copy())
            y_out.append(y[mask].copy())
        else:
            times_out.append(time_array.copy())
            x_out.append(x.copy())
            y_out.append(y.copy())

    outside_total = int(np.sum(outside_counts))
    if action == "error" and outside_total:
        raise SparseNativeError(
            "observations_outside_analysis_support",
            "observations lie outside the declared evaluation-grid support",
            details={
                "analysis_support": [start, end],
                "outside_observation_count": outside_total,
                "outside_counts_by_curve": outside_counts,
            },
        )

    total_in_support = int(np.sum(in_support_counts))
    if total_in_support < 3:
        raise SparseNativeError(
            "insufficient_joint_support",
            "fewer than three planar observations remain on declared support",
            details={
                "analysis_support": [start, end],
                "in_support_observation_count": total_in_support,
                "in_support_counts_by_curve": in_support_counts,
            },
        )

    diagnostics: dict[str, object] = {
        "analysis_support": [start, end],
        "analysis_support_action": action,
        "outside_observation_count": outside_total,
        "outside_counts_by_curve": outside_counts,
        "original_sample_counts": trajectories.sample_counts.tolist(),
        "analysis_sample_counts": in_support_counts,
    }
    return (
        tuple(times_out),
        tuple(x_out),
        tuple(y_out),
        diagnostics,
    )


def raw_planar_covariance_pairs(
    curve_times: Sequence[np.ndarray],
    residual_x: Sequence[np.ndarray],
    residual_y: Sequence[np.ndarray],
) -> RawPlanarCovariancePairs:
    """Construct direct xx, xy, and yy latent covariance pair sets.

    All three pair sets exclude same-time products.  For xy, every ordered
    pair j != l is generated explicitly as rx_j * ry_l at
    (t_j, t_l).  The cross surface is therefore directional and is never
    created by mirroring one triangular set of products.
    """

    if not (
        len(curve_times) == len(residual_x) == len(residual_y)
    ):
        raise ValueError(
            "curve_times, residual_x, and residual_y must have equal length"
        )

    xx = raw_offdiagonal_covariance_pairs(
        curve_times,
        residual_x,
        include_mirror=True,
    )
    yy = raw_offdiagonal_covariance_pairs(
        curve_times,
        residual_y,
        include_mirror=True,
    )

    s_values: list[float] = []
    t_values: list[float] = []
    products: list[float] = []
    curve_indices: list[int] = []

    for curve_index, (time, x_residual, y_residual) in enumerate(
        zip(curve_times, residual_x, residual_y, strict=True)
    ):
        time_array = np.asarray(time, dtype=float)
        x_array = np.asarray(x_residual, dtype=float)
        y_array = np.asarray(y_residual, dtype=float)
        if (
            time_array.ndim != 1
            or x_array.ndim != 1
            or y_array.ndim != 1
            or time_array.shape != x_array.shape
            or time_array.shape != y_array.shape
        ):
            raise ValueError(
                "each curve time/x-residual/y-residual triplet must be "
                "one-dimensional and aligned"
            )
        if (
            not np.all(np.isfinite(time_array))
            or not np.all(np.isfinite(x_array))
            or not np.all(np.isfinite(y_array))
        ):
            raise ValueError(
                "curve times and planar residuals must contain only finite values"
            )

        for left in range(time_array.size):
            for right in range(time_array.size):
                if left == right:
                    continue
                s_values.append(float(time_array[left]))
                t_values.append(float(time_array[right]))
                products.append(
                    float(x_array[left] * y_array[right])
                )
                curve_indices.append(curve_index)

    if len(products) < 3:
        raise SparseNativeError(
            "insufficient_cross_covariance_pairs",
            "fewer than three off-diagonal cross-covariance pairs are available",
            details={"n_pairs": len(products)},
        )

    xy = RawCovariancePairs(
        s=np.asarray(s_values, dtype=float),
        t=np.asarray(t_values, dtype=float),
        products=np.asarray(products, dtype=float),
        curve_index=np.asarray(curve_indices, dtype=int),
        mirrored=False,
    )
    return RawPlanarCovariancePairs(xx=xx, xy=xy, yy=yy)


def _local_linear_planar_surface(
    pairs: RawCovariancePairs,
    evaluation_grid: np.ndarray,
    *,
    bandwidth: float,
    min_local_pairs: int,
    block_name: str,
) -> LocalLinear2DResult:
    grid = _validate_grid(evaluation_grid)
    bandwidth = _positive_finite(
        bandwidth,
        name="covariance_bandwidth",
    )
    if isinstance(min_local_pairs, bool) or not isinstance(
        min_local_pairs, int
    ):
        raise TypeError("min_local_pairs must be an integer")
    if min_local_pairs < 3:
        raise ValueError("min_local_pairs must be at least 3")
    if block_name not in {"xx", "xy", "yy"}:
        raise ValueError("block_name must be 'xx', 'xy', or 'yy'")

    failure_code = (
        "insufficient_cross_covariance_local_support"
        if block_name == "xy"
        else "insufficient_covariance_local_support"
    )
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
                    failure_code,
                    "local planar covariance smoothing has too few "
                    "off-diagonal pairs",
                    details={
                        "block": block_name,
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
            weighted_design = (
                design * np.sqrt(local_weights)[:, None]
            )
            if np.linalg.matrix_rank(weighted_design) < 3:
                raise SparseNativeError(
                    failure_code,
                    "local planar covariance design is rank deficient",
                    details={
                        "block": block_name,
                        "s": float(s0),
                        "t": float(t0),
                        "support_count": int(support[row, column]),
                        "bandwidth": bandwidth,
                    },
                )
            weighted_product = (
                pairs.products[mask] * np.sqrt(local_weights)
            )
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


def smooth_planar_covariance_pairs(
    pairs: RawPlanarCovariancePairs,
    evaluation_grid: np.ndarray,
    *,
    bandwidth: float,
    min_local_pairs: int = 6,
) -> tuple[PlanarCovarianceBlocks, PlanarCovarianceSupport]:
    """Smooth xx, xy, and yy directly; define yx only as xy transpose."""

    xx = _local_linear_planar_surface(
        pairs.xx,
        evaluation_grid,
        bandwidth=bandwidth,
        min_local_pairs=min_local_pairs,
        block_name="xx",
    )
    xy = _local_linear_planar_surface(
        pairs.xy,
        evaluation_grid,
        bandwidth=bandwidth,
        min_local_pairs=min_local_pairs,
        block_name="xy",
    )
    yy = _local_linear_planar_surface(
        pairs.yy,
        evaluation_grid,
        bandwidth=bandwidth,
        min_local_pairs=min_local_pairs,
        block_name="yy",
    )

    blocks = PlanarCovarianceBlocks(
        cxx=xx.values.copy(),
        cxy=xy.values.copy(),
        cyx=xy.values.T.copy(),
        cyy=yy.values.copy(),
    )
    support = PlanarCovarianceSupport(
        cxx=xx.support_counts.copy(),
        cxy=xy.support_counts.copy(),
        cyy=yy.support_counts.copy(),
    )
    return blocks, support


def audit_repair_planar_covariance(
    cxx: np.ndarray,
    cxy: np.ndarray,
    cyy: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    cyx: np.ndarray | None = None,
    action: str = "error",
    tolerance: float = 1e-8,
    symmetry_tolerance: float = 1e-10,
) -> PlanarCovarianceOperatorResult:
    """Audit and optionally project a full planar covariance operator to PSD.

    Blocks use channel-major ordering in the assembled operator:
    x(grid) followed by y(grid). Symmetry is assessed jointly, including
    Cyx(s,t) = Cxy(t,s). Tiny numerical asymmetry within the declared
    tolerance is enforced explicitly; material asymmetry fails closed.

    The input smoothed surfaces are retained separately from the covariance
    blocks used downstream after symmetry enforcement and optional PSD repair.
    Cxy is never symmetrized against its own transpose.
    """

    grid = _validate_grid(evaluation_grid)
    if action not in {"error", "project"}:
        raise ValueError("action must be 'error' or 'project'")
    tolerance = float(tolerance)
    symmetry_tolerance = float(symmetry_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")
    if not np.isfinite(symmetry_tolerance) or symmetry_tolerance < 0:
        raise ValueError(
            "symmetry_tolerance must be finite and non-negative"
        )

    size = grid.size
    raw_xx = _validate_block(cxx, grid_size=size, name="cxx")
    raw_xy = _validate_block(cxy, grid_size=size, name="cxy")
    raw_yy = _validate_block(cyy, grid_size=size, name="cyy")
    raw_yx = (
        raw_xy.T.copy()
        if cyx is None
        else _validate_block(cyx, grid_size=size, name="cyx")
    )

    smoothed_matrix = np.block(
        [
            [raw_xx, raw_xy],
            [raw_yx, raw_yy],
        ]
    )
    symmetry_error = max(
        float(np.max(np.abs(raw_xx - raw_xx.T))),
        float(np.max(np.abs(raw_yy - raw_yy.T))),
        float(np.max(np.abs(raw_yx - raw_xy.T))),
    )
    if symmetry_error > symmetry_tolerance:
        raise SparseNativeError(
            "joint_covariance_symmetry_failure",
            "planar covariance blocks violate joint symmetry tolerance",
            details={
                "maximum_symmetry_error": symmetry_error,
                "symmetry_tolerance": symmetry_tolerance,
            },
        )

    sym_xx = 0.5 * (raw_xx + raw_xx.T)
    sym_yy = 0.5 * (raw_yy + raw_yy.T)
    sym_xy = 0.5 * (raw_xy + raw_yx.T)
    sym_yx = sym_xy.T
    matrix = np.block([[sym_xx, sym_xy], [sym_yx, sym_yy]])

    weights = functional_trapezoid_weights(grid)
    joint_weights = np.concatenate([weights, weights])
    sqrt_weights = np.sqrt(joint_weights)
    weighted_operator = (
        sqrt_weights[:, None] * matrix * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    negative = eigenvalues < 0.0
    substantial = eigenvalues < -tolerance
    negative_count = int(np.count_nonzero(negative))
    substantial_count = int(np.count_nonzero(substantial))
    most_negative = float(np.min(eigenvalues))

    if action == "error" and substantial_count:
        raise SparseNativeError(
            "joint_covariance_psd_failure",
            "planar covariance operator has eigenvalues below the PSD tolerance",
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
        repaired_weighted = (
            (eigenvectors * clipped[None, :]) @ eigenvectors.T
        )
        repaired = (
            repaired_weighted
            / sqrt_weights[:, None]
            / sqrt_weights[None, :]
        )
        repaired = 0.5 * (repaired + repaired.T)

    correction = repaired - matrix
    operator_correction = (
        sqrt_weights[:, None] * correction * sqrt_weights[None, :]
    )
    correction_norm = float(np.linalg.norm(correction, ord="fro"))
    operator_correction_norm = float(
        np.linalg.norm(operator_correction, ord="fro")
    )
    operator_baseline_norm = float(
        np.linalg.norm(weighted_operator, ord="fro")
    )
    relative_operator_norm = (
        0.0
        if operator_baseline_norm == 0.0
        else operator_correction_norm / operator_baseline_norm
    )

    repaired_xx = repaired[:size, :size].copy()
    repaired_xy = repaired[:size, size:].copy()
    repaired_yx = repaired[size:, :size].copy()
    repaired_yy = repaired[size:, size:].copy()
    audit = PlanarCovarianceAudit(
        requested_action=action,
        applied_action=applied_action,
        tolerance=tolerance,
        symmetry_tolerance=symmetry_tolerance,
        pre_enforcement_symmetry_error=symmetry_error,
        pre_repair_operator_eigenvalues=eigenvalues.copy(),
        negative_eigenvalue_count=negative_count,
        substantial_negative_eigenvalue_count=substantial_count,
        most_negative_eigenvalue=most_negative,
        correction_frobenius_norm=correction_norm,
        relative_correction_frobenius_norm=_relative_frobenius(
            correction, matrix
        ),
        operator_correction_frobenius_norm=operator_correction_norm,
        relative_operator_correction_frobenius_norm=relative_operator_norm,
    )
    return PlanarCovarianceOperatorResult(
        smoothed_cxx=raw_xx.copy(),
        smoothed_cxy=raw_xy.copy(),
        smoothed_cyx=raw_yx.copy(),
        smoothed_cyy=raw_yy.copy(),
        smoothed_covariance_matrix=smoothed_matrix.copy(),
        cxx=repaired_xx,
        cxy=repaired_xy,
        cyx=repaired_yx,
        cyy=repaired_yy,
        covariance_matrix=repaired,
        quadrature_weights=weights,
        audit=audit,
    )


def estimate_sparse_planar_mean_covariance(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    covariance_bandwidth: float,
    analysis_support_action: str = "error",
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    symmetry_tolerance: float = 1e-10,
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
) -> SparsePlanarMeanCovarianceResult:
    """Estimate a direct sparse vector mean and latent planar covariance.

    This internal 0.12 primitive intentionally stops before joint PACE
    scoring.  Same-time xx, xy, and yy residual products are excluded so the
    latent covariance estimate is not contaminated by contemporaneous
    measurement-error covariance.  Cxy is fitted directionally and Cyx is
    defined only as its transpose.
    """

    x_index, y_index = _validate_planar_input(
        trajectories,
        dimensions,
    )
    grid = _validate_grid(evaluation_grid)
    mean_bandwidth = _positive_finite(
        mean_bandwidth,
        name="mean_bandwidth",
    )
    covariance_bandwidth = _positive_finite(
        covariance_bandwidth,
        name="covariance_bandwidth",
    )
    (
        curve_times,
        curve_x,
        curve_y,
        support_diagnostics,
    ) = _prepare_planar_analysis_views(
        trajectories,
        x_index=x_index,
        y_index=y_index,
        evaluation_grid=grid,
        action=analysis_support_action,
    )

    pooled_time = np.concatenate(curve_times)
    pooled_x = np.concatenate(curve_x)
    pooled_y = np.concatenate(curve_y)

    mean_x = local_linear_smooth_1d(
        pooled_time,
        pooled_x,
        grid,
        bandwidth=mean_bandwidth,
        min_local_points=mean_min_local_points,
    )
    mean_y = local_linear_smooth_1d(
        pooled_time,
        pooled_y,
        grid,
        bandwidth=mean_bandwidth,
        min_local_points=mean_min_local_points,
    )

    residual_x: list[np.ndarray] = []
    residual_y: list[np.ndarray] = []
    for time, observed_x, observed_y in zip(
        curve_times,
        curve_x,
        curve_y,
        strict=True,
    ):
        if time.size == 0:
            residual_x.append(np.asarray([], dtype=float))
            residual_y.append(np.asarray([], dtype=float))
            continue
        mean_x_native = local_linear_smooth_1d(
            pooled_time,
            pooled_x,
            time,
            bandwidth=mean_bandwidth,
            min_local_points=mean_min_local_points,
        ).values
        mean_y_native = local_linear_smooth_1d(
            pooled_time,
            pooled_y,
            time,
            bandwidth=mean_bandwidth,
            min_local_points=mean_min_local_points,
        ).values
        residual_x.append(observed_x - mean_x_native)
        residual_y.append(observed_y - mean_y_native)

    pairs = raw_planar_covariance_pairs(
        curve_times,
        tuple(residual_x),
        tuple(residual_y),
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
        "backend": "native_internal_0.12",
        "dimensions": list(dimensions),
        "mean_smoother": "local_linear_epanechnikov",
        "covariance_smoother": "local_linear_product_epanechnikov",
        "mean_bandwidth": mean_bandwidth,
        "covariance_bandwidth": covariance_bandwidth,
        "same_time_covariance_products_excluded": True,
        "cross_covariance_same_time_products_excluded": True,
        "measurement_error_cross_covariance_contamination_avoided": True,
        "measurement_error_independent_across_time_assumed": True,
        "yx_estimated_independently": False,
        "cross_covariance_self_symmetrized": False,
        "raw_sparse_trajectory_interpolation_performed": False,
        "population_function_evaluation_at_native_times": True,
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "symmetry_tolerance": float(symmetry_tolerance),
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        **support_diagnostics,
    }
    return SparsePlanarMeanCovarianceResult(
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
            "xx": pairs.xx.n_pairs,
            "xy": pairs.xy.n_pairs,
            "yy": pairs.yy.n_pairs,
        },
        operator_audit=operator.audit,
        curve_ids=trajectories.curve_ids,
        analysis_sample_counts=tuple(
            int(value)
            for value in support_diagnostics["analysis_sample_counts"]
        ),
        provenance=provenance,
    )


def weighted_planar_covariance_eigendecomposition(
    covariance_matrix: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    n_components: int,
    positive_tolerance: float = 1e-10,
) -> PlanarWeightedEigendecomposition:
    """Solve the quadrature-weighted bivariate covariance eigenproblem."""

    grid = _validate_grid(evaluation_grid)
    matrix = np.asarray(covariance_matrix, dtype=float)
    size = grid.size
    if matrix.shape != (2 * size, 2 * size):
        raise ValueError(
            "covariance_matrix must have shape "
            f"({2 * size}, {2 * size})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError("covariance_matrix must contain only finite values")
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
    joint_weights = np.concatenate([weights, weights])
    sqrt_weights = np.sqrt(joint_weights)
    symmetric = 0.5 * (matrix + matrix.T)
    weighted_operator = (
        sqrt_weights[:, None] * symmetric * sqrt_weights[None, :]
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
            "joint covariance has fewer positive components than requested",
            details={
                "requested_components": n_components,
                "positive_components": n_positive,
                "positive_tolerance": positive_tolerance,
            },
        )

    selected_values = eigenvalues[:n_components].copy()
    selected_vectors = eigenvectors[:, :n_components].copy()
    flat_functions = (
        selected_vectors / sqrt_weights[:, None]
    ).T

    for component in range(n_components):
        pivot = int(np.argmax(np.abs(flat_functions[component])))
        if flat_functions[component, pivot] < 0:
            flat_functions[component] *= -1.0

    eigenfunctions = flat_functions.reshape(n_components, 2, size)
    return PlanarWeightedEigendecomposition(
        eigenvalues=selected_values,
        eigenfunctions=eigenfunctions,
        quadrature_weights=weights,
    )
