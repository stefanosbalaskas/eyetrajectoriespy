"""Public asynchronous sparse planar MFPCA/PACE composition for the 1.1 line."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_multivariate import (
    resolve_measurement_error_covariance,
    weighted_planar_covariance_eigendecomposition,
)
from ._sparse_multivariate_async import (
    async_joint_pace_scores,
    estimate_async_sparse_planar_mean_covariance,
)
from .types import IrregularTrajectorySet


@dataclass(frozen=True)
class SparseAsyncMFPCAResult:
    """Native asynchronous sparse planar MFPCA/PACE result.

    The input may contain coordinate-specific missingness on each curve's exact
    union of native x/y timestamps. No raw interpolation or synchronization is
    implied by this result.
    """

    scores: np.ndarray
    eigenvalues: np.ndarray
    eigenfunctions: np.ndarray
    mean: np.ndarray
    evaluation_grid: np.ndarray
    dimensions: tuple[str, str]
    curve_ids: tuple[str, ...]
    metadata: pd.DataFrame
    coordinate_system: str
    time_unit: str
    n_components: int
    quadrature_weights: np.ndarray
    smoothed_cxx: np.ndarray
    smoothed_cxy: np.ndarray
    smoothed_cyx: np.ndarray
    smoothed_cyy: np.ndarray
    covariance_cxx: np.ndarray
    covariance_cxy: np.ndarray
    covariance_cyx: np.ndarray
    covariance_cyy: np.ndarray
    measurement_error_covariance: np.ndarray
    score_diagnostics: pd.DataFrame
    mean_support_counts: np.ndarray
    covariance_support_counts: Mapping[str, np.ndarray]
    covariance_pair_counts: Mapping[str, int]
    covariance_diagnostics: Mapping[str, Any]
    support_diagnostics: Mapping[str, Any]
    fit_method: str
    score_method: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_curves(self) -> int:
        return len(self.curve_ids)


def _covariance_audit_mapping(audit: Any) -> dict[str, Any]:
    return {
        "requested_action": audit.requested_action,
        "applied_action": audit.applied_action,
        "tolerance": float(audit.tolerance),
        "symmetry_tolerance": float(audit.symmetry_tolerance),
        "pre_enforcement_symmetry_error": float(
            audit.pre_enforcement_symmetry_error
        ),
        "pre_repair_operator_eigenvalues": (
            audit.pre_repair_operator_eigenvalues.copy()
        ),
        "negative_eigenvalue_count": int(audit.negative_eigenvalue_count),
        "substantial_negative_eigenvalue_count": int(
            audit.substantial_negative_eigenvalue_count
        ),
        "most_negative_eigenvalue": float(audit.most_negative_eigenvalue),
        "correction_frobenius_norm": float(
            audit.correction_frobenius_norm
        ),
        "relative_correction_frobenius_norm": float(
            audit.relative_correction_frobenius_norm
        ),
        "operator_correction_frobenius_norm": float(
            audit.operator_correction_frobenius_norm
        ),
        "relative_operator_correction_frobenius_norm": float(
            audit.relative_operator_correction_frobenius_norm
        ),
    }


def fit_sparse_mfpca_async(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    n_components: int,
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    covariance_bandwidth: float,
    measurement_error: str,
    measurement_error_variance: tuple[float, float] | None = None,
    measurement_error_covariance: np.ndarray | None = None,
    analysis_support_action: str = "error",
    same_time_tolerance: float = 0.0,
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    positive_eigen_tolerance: float = 1e-10,
    score_ridge: float = 0.0,
    score_condition_limit: float = 1e12,
    min_score_observations: int = 2,
    score_failure_action: str = "error",
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
) -> SparseAsyncMFPCAResult:
    """Fit native asynchronous sparse planar MFPCA with joint PACE scores.

    Each curve may observe x and y on different native grids. The existing
    :class:`IrregularTrajectorySet` is interpreted as an exact union-of-native-
    timestamps representation: a coordinate-specific ``NaN`` means that
    coordinate was not observed at that exact timestamp. Rows where both
    requested coordinates are absent are invalid.

    Raw observations are never interpolated, nearest-neighbour synchronized,
    or binned. The common ``evaluation_grid`` belongs only to fitted population
    functions. Latent Cxy excludes simultaneous x-y residual products, while a
    declared correlated measurement-error covariance is used only for x/y
    scalar observations that are simultaneous within ``same_time_tolerance``.
    """

    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")

    resolved_error = resolve_measurement_error_covariance(
        measurement_error,
        measurement_error_variance=measurement_error_variance,
        measurement_error_covariance=measurement_error_covariance,
    )

    population = estimate_async_sparse_planar_mean_covariance(
        trajectories,
        dimensions=dimensions,
        evaluation_grid=evaluation_grid,
        mean_bandwidth=mean_bandwidth,
        covariance_bandwidth=covariance_bandwidth,
        analysis_support_action=analysis_support_action,
        same_time_tolerance=same_time_tolerance,
        psd_action=psd_action,
        psd_tolerance=psd_tolerance,
        mean_min_local_points=mean_min_local_points,
        covariance_min_local_pairs=covariance_min_local_pairs,
    )

    eigen = weighted_planar_covariance_eigendecomposition(
        population.covariance_blocks.matrix,
        population.evaluation_grid,
        n_components=n_components,
        positive_tolerance=positive_eigen_tolerance,
    )

    scores = async_joint_pace_scores(
        trajectories.curve_ids,
        population.x_times,
        population.x_values,
        population.y_times,
        population.y_values,
        evaluation_grid=population.evaluation_grid,
        fitted_mean=population.mean,
        covariance_blocks=population.covariance_blocks,
        eigenvalues=eigen.eigenvalues,
        eigenfunctions=eigen.eigenfunctions,
        measurement_error_covariance=resolved_error.covariance,
        n_components=n_components,
        same_time_tolerance=same_time_tolerance,
        score_ridge=score_ridge,
        condition_limit=score_condition_limit,
        min_score_observations=min_score_observations,
        failure_action=score_failure_action,
    )

    covariance_diagnostics = _covariance_audit_mapping(population.operator_audit)
    covariance_support_counts = {
        "cxx": population.covariance_support_counts.cxx.copy(),
        "cxy": population.covariance_support_counts.cxy.copy(),
        "cyy": population.covariance_support_counts.cyy.copy(),
    }
    covariance_pair_counts = {
        key: int(value) for key, value in population.covariance_pair_counts.items()
    }
    support_diagnostics = {
        **dict(population.support_diagnostics),
        **dict(population.pair_diagnostics),
    }

    async_provenance: dict[str, Any] = {
        "backend": "native",
        "fit_method": "direct_async_sparse_block_covariance",
        "score_method": "asynchronous_joint_PACE",
        "dimensions": list(dimensions),
        "n_components": int(n_components),
        "component_rank_rule": "positive_fitted_joint_operator_spectrum",
        "input_representation": "exact_union_of_native_coordinate_timestamps",
        "coordinate_specific_missingness_supported": True,
        "mean_bandwidth": float(mean_bandwidth),
        "covariance_bandwidth": float(covariance_bandwidth),
        "analysis_support": list(population.provenance["analysis_support"]),
        "analysis_support_action": analysis_support_action,
        "same_time_tolerance": float(same_time_tolerance),
        "cross_covariance_same_time_products_excluded": True,
        "cross_covariance_same_time_pair_count_excluded": int(
            population.pair_diagnostics["cross_same_time_pair_count_excluded"]
        ),
        "measurement_error_independent_across_distinct_times_assumed": True,
        "measurement_error_cross_covariance_scope": "simultaneous_xy_only",
        "yx_estimated_independently": False,
        "cross_covariance_self_symmetrized": False,
        "score_observation_order": scores.provenance["score_observation_order"],
        "paired_reduction_order": scores.provenance["paired_reduction_order"],
        "score_covariance_source": scores.provenance["score_covariance_source"],
        "rank_k_covariance_used_for_scoring": False,
        "measurement_error_mode": measurement_error,
        "measurement_error_covariance": resolved_error.covariance.copy(),
        "measurement_error_covariance_eigenvalues": resolved_error.eigenvalues.copy(),
        "measurement_error_covariance_symmetry_error": float(
            resolved_error.symmetry_error
        ),
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "positive_eigen_tolerance": float(positive_eigen_tolerance),
        "score_ridge": float(score_ridge),
        "score_condition_limit": float(score_condition_limit),
        "min_score_observations": int(min_score_observations),
        "score_failure_action": score_failure_action,
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "raw_sparse_trajectory_interpolation_performed": False,
        "nearest_neighbour_synchronization_performed": False,
        "time_binning_performed": False,
        "population_function_evaluation_at_native_times": True,
        "automatic_bandwidth_selection_performed": False,
        "cross_channel_covariance_modeled": True,
        "covariance_psd": covariance_diagnostics,
    }

    return SparseAsyncMFPCAResult(
        scores=scores.scores.copy(),
        eigenvalues=eigen.eigenvalues.copy(),
        eigenfunctions=np.transpose(eigen.eigenfunctions, (0, 2, 1)).copy(),
        mean=population.mean.T.copy(),
        evaluation_grid=population.evaluation_grid.copy(),
        dimensions=(str(dimensions[0]), str(dimensions[1])),
        curve_ids=trajectories.curve_ids,
        metadata=trajectories.metadata.reset_index(drop=True).copy(),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        n_components=int(n_components),
        quadrature_weights=eigen.quadrature_weights.copy(),
        smoothed_cxx=population.smoothed_covariance_blocks.cxx.copy(),
        smoothed_cxy=population.smoothed_covariance_blocks.cxy.copy(),
        smoothed_cyx=population.smoothed_covariance_blocks.cyx.copy(),
        smoothed_cyy=population.smoothed_covariance_blocks.cyy.copy(),
        covariance_cxx=population.covariance_blocks.cxx.copy(),
        covariance_cxy=population.covariance_blocks.cxy.copy(),
        covariance_cyx=population.covariance_blocks.cyx.copy(),
        covariance_cyy=population.covariance_blocks.cyy.copy(),
        measurement_error_covariance=resolved_error.covariance.copy(),
        score_diagnostics=scores.diagnostics.copy(),
        mean_support_counts=population.mean_support_counts.T.copy(),
        covariance_support_counts=covariance_support_counts,
        covariance_pair_counts=covariance_pair_counts,
        covariance_diagnostics=covariance_diagnostics,
        support_diagnostics=support_diagnostics,
        fit_method="direct_async_sparse_block_covariance",
        score_method="asynchronous_joint_PACE",
        provenance={
            **dict(trajectories.provenance),
            "sparse_mfpca_async": async_provenance,
        },
    )


def sparse_mfpca_async_score_frame(
    result: SparseAsyncMFPCAResult,
) -> pd.DataFrame:
    """Return asynchronous joint scores with curve IDs and metadata."""

    if not isinstance(result, SparseAsyncMFPCAResult):
        raise TypeError("result must be a SparseAsyncMFPCAResult")
    frame = result.metadata.reset_index(drop=True).copy()
    frame.insert(0, "curve_id", list(result.curve_ids))
    for component in range(result.n_components):
        frame[f"ASM FPC{component + 1}".replace(" ", "")] = result.scores[:, component]
    return frame


def sparse_mfpca_async_reporting_text(
    result: SparseAsyncMFPCAResult,
    *,
    digits: int = 3,
) -> str:
    """Generate audit-oriented reporting text for asynchronous sparse MFPCA."""

    if not isinstance(result, SparseAsyncMFPCAResult):
        raise TypeError("result must be a SparseAsyncMFPCAResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")

    provenance = result.provenance.get("sparse_mfpca_async", {})
    status = result.score_diagnostics["status_code"].astype(str).to_numpy()
    failed = int(np.count_nonzero(status != "ok"))
    solved = int(np.count_nonzero(status == "ok"))
    psd = result.covariance_diagnostics
    error_text = np.array2string(
        result.measurement_error_covariance,
        precision=digits,
        separator=", ",
    )

    return (
        f"Native asynchronous sparse planar MFPCA was fitted to dimensions "
        f"{result.dimensions[0]!r} and {result.dimensions[1]!r} for "
        f"{result.n_curves} curve(s), retaining {result.n_components} joint "
        f"component(s). Coordinate-specific native timestamps were retained "
        f"without interpolation, nearest-neighbour synchronization, or time "
        f"binning. Separate coordinate means and direct Cxx/Cxy/Cyy latent "
        f"covariance surfaces used declared local-linear bandwidths "
        f"{provenance.get('mean_bandwidth')} and "
        f"{provenance.get('covariance_bandwidth')}. Cxy used asynchronous "
        f"x-y residual products and excluded "
        f"{provenance.get('cross_covariance_same_time_pair_count_excluded')} "
        f"simultaneous cross-product(s) from latent covariance fitting. Cyx "
        f"was defined as Cxy transpose. The full joint operator used PSD action "
        f"{psd.get('requested_action')!r} (applied={psd.get('applied_action')!r}; "
        f"relative operator correction="
        f"{float(psd.get('relative_operator_correction_frobenius_norm', np.nan)):.{digits}f}). "
        f"Measurement error used mode {provenance.get('measurement_error_mode')!r} "
        f"with R_epsilon={error_text}; off-diagonal measurement-error covariance "
        f"was added only for simultaneous x/y observations. Asynchronous joint "
        f"PACE used the full fitted covariance plus measurement error and "
        f"ridge={provenance.get('score_ridge')}, never a rank-K covariance "
        f"reconstruction. {solved} curve(s) were scored successfully and "
        f"{failed} retained score-system failure(s) were recorded under "
        f"failure_action={provenance.get('score_failure_action')!r}."
    )
