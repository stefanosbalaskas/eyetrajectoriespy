"""Public native sparse multivariate FPCA/PACE composition.

The numerical primitives live in the private sparse-multivariate module and
are qualified independently. This module is intentionally thin: it validates
the public contract, composes those primitives once, and converts internal
channel-major arrays to the package's public time-before-dimension convention.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ._sparse_multivariate import (
    _prepare_planar_analysis_views,
    _validate_planar_input,
    estimate_sparse_planar_mean_covariance,
    joint_pace_scores,
    resolve_measurement_error_covariance,
    weighted_planar_covariance_eigendecomposition,
)
from .types import IrregularTrajectorySet, SparseMFPCAResult


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


def fit_sparse_mfpca(
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
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    positive_eigen_tolerance: float = 1e-10,
    score_ridge: float = 0.0,
    score_condition_limit: float = 1e12,
    min_score_time_points: int = 2,
    score_failure_action: str = "error",
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
) -> SparseMFPCAResult:
    """Fit native direct sparse multivariate FPCA with joint PACE scores.

    The first public 0.12 contract supports exactly two jointly observed
    coordinates. Raw sparse trajectories are never interpolated onto a common
    grid. Population mean/covariance/eigenfunctions are fitted on the declared
    evaluation grid and evaluated at each curve's retained native times.

    measurement_error="diagonal" requires two declared variances.
    measurement_error="fixed_matrix" requires an analyst-supplied finite,
    symmetric, positive-semidefinite 2x2 covariance matrix. No measurement
    error covariance is estimated automatically in this tranche.

    The joint PACE score system always uses the full fitted joint covariance
    plus measurement error and optional ridge. n_components controls only the
    returned eigenfunctions and scores.
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

    mean_covariance = estimate_sparse_planar_mean_covariance(
        trajectories,
        dimensions=dimensions,
        evaluation_grid=evaluation_grid,
        mean_bandwidth=mean_bandwidth,
        covariance_bandwidth=covariance_bandwidth,
        analysis_support_action=analysis_support_action,
        psd_action=psd_action,
        psd_tolerance=psd_tolerance,
        mean_min_local_points=mean_min_local_points,
        covariance_min_local_pairs=covariance_min_local_pairs,
    )

    eigen = weighted_planar_covariance_eigendecomposition(
        mean_covariance.covariance_blocks.matrix,
        mean_covariance.evaluation_grid,
        n_components=n_components,
        positive_tolerance=positive_eigen_tolerance,
    )

    x_index, y_index = _validate_planar_input(
        trajectories,
        dimensions,
    )
    (
        curve_times,
        curve_x,
        curve_y,
        scoring_support,
    ) = _prepare_planar_analysis_views(
        trajectories,
        x_index=x_index,
        y_index=y_index,
        evaluation_grid=mean_covariance.evaluation_grid,
        action=analysis_support_action,
    )
    scoring_counts = tuple(int(len(time)) for time in curve_times)
    if scoring_counts != mean_covariance.analysis_sample_counts:
        raise RuntimeError(
            "internal support invariant failed: covariance-fit and joint-score "
            "sample counts differ"
        )
    if scoring_counts != tuple(
        int(value) for value in scoring_support["analysis_sample_counts"]
    ):
        raise RuntimeError(
            "internal support invariant failed: score-support diagnostics "
            "do not match retained score inputs"
        )

    planar_values = tuple(
        np.column_stack([x, y])
        for x, y in zip(curve_x, curve_y, strict=True)
    )
    scores = joint_pace_scores(
        trajectories.curve_ids,
        curve_times,
        planar_values,
        evaluation_grid=mean_covariance.evaluation_grid,
        fitted_mean=mean_covariance.mean,
        covariance_blocks=mean_covariance.covariance_blocks,
        eigenvalues=eigen.eigenvalues,
        eigenfunctions=eigen.eigenfunctions,
        measurement_error_covariance=resolved_error.covariance,
        n_components=n_components,
        score_ridge=score_ridge,
        condition_limit=score_condition_limit,
        min_score_time_points=min_score_time_points,
        failure_action=score_failure_action,
    )

    diagnostics = _covariance_audit_mapping(
        mean_covariance.operator_audit
    )
    covariance_support_counts = {
        "cxx": mean_covariance.covariance_support_counts.cxx.copy(),
        "cxy": mean_covariance.covariance_support_counts.cxy.copy(),
        "cyy": mean_covariance.covariance_support_counts.cyy.copy(),
    }
    covariance_pair_counts = {
        key: int(value)
        for key, value in mean_covariance.covariance_pair_counts.items()
    }

    sparse_provenance: dict[str, Any] = {
        "backend": "native",
        "fit_method": "direct_sparse_block_covariance",
        "score_method": "joint_PACE",
        "dimensions": list(dimensions),
        "n_components": int(n_components),
        "component_rank_rule": "positive_fitted_joint_operator_spectrum",
        "mean_bandwidth": float(mean_bandwidth),
        "covariance_bandwidth": float(covariance_bandwidth),
        "analysis_support": list(
            mean_covariance.provenance["analysis_support"]
        ),
        "analysis_support_action": analysis_support_action,
        "original_sample_counts": list(
            mean_covariance.provenance["original_sample_counts"]
        ),
        "analysis_sample_counts": list(
            mean_covariance.provenance["analysis_sample_counts"]
        ),
        "outside_observation_count": int(
            mean_covariance.provenance["outside_observation_count"]
        ),
        "same_time_covariance_products_excluded": True,
        "cross_covariance_same_time_products_excluded": True,
        "measurement_error_independent_across_time_assumed": True,
        "yx_estimated_independently": False,
        "cross_covariance_self_symmetrized": False,
        "operator_storage_order": scores.provenance[
            "operator_storage_order"
        ],
        "score_observation_order": scores.provenance[
            "score_observation_order"
        ],
        "ordering_permutation_applied": bool(
            scores.provenance["ordering_permutation_applied"]
        ),
        "score_covariance_source": scores.provenance[
            "score_covariance_source"
        ],
        "rank_k_covariance_used_for_scoring": bool(
            scores.provenance["rank_k_covariance_used_for_scoring"]
        ),
        "measurement_error_mode": measurement_error,
        "measurement_error_covariance": resolved_error.covariance.copy(),
        "measurement_error_covariance_eigenvalues": (
            resolved_error.eigenvalues.copy()
        ),
        "measurement_error_covariance_symmetry_error": float(
            resolved_error.symmetry_error
        ),
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "positive_eigen_tolerance": float(positive_eigen_tolerance),
        "score_ridge": float(score_ridge),
        "score_condition_limit": float(score_condition_limit),
        "min_score_time_points": int(min_score_time_points),
        "score_failure_action": score_failure_action,
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "raw_sparse_trajectory_interpolation_performed": False,
        "population_function_evaluation_at_native_times": True,
        "automatic_bandwidth_selection_performed": False,
        "cross_channel_covariance_modeled": True,
        "covariance_psd": diagnostics,
    }

    return SparseMFPCAResult(
        scores=scores.scores.copy(),
        eigenvalues=eigen.eigenvalues.copy(),
        eigenfunctions=np.transpose(
            eigen.eigenfunctions,
            (0, 2, 1),
        ).copy(),
        mean=mean_covariance.mean.T.copy(),
        evaluation_grid=mean_covariance.evaluation_grid.copy(),
        dimensions=(str(dimensions[0]), str(dimensions[1])),
        curve_ids=trajectories.curve_ids,
        metadata=trajectories.metadata.reset_index(drop=True).copy(),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        n_components=int(n_components),
        quadrature_weights=eigen.quadrature_weights.copy(),
        smoothed_cxx=mean_covariance.smoothed_covariance_blocks.cxx.copy(),
        smoothed_cxy=mean_covariance.smoothed_covariance_blocks.cxy.copy(),
        smoothed_cyx=mean_covariance.smoothed_covariance_blocks.cyx.copy(),
        smoothed_cyy=mean_covariance.smoothed_covariance_blocks.cyy.copy(),
        covariance_cxx=mean_covariance.covariance_blocks.cxx.copy(),
        covariance_cxy=mean_covariance.covariance_blocks.cxy.copy(),
        covariance_cyx=mean_covariance.covariance_blocks.cyx.copy(),
        covariance_cyy=mean_covariance.covariance_blocks.cyy.copy(),
        measurement_error_covariance=resolved_error.covariance.copy(),
        score_diagnostics=scores.diagnostics.copy(),
        mean_support_counts=mean_covariance.mean_support_counts.T.copy(),
        covariance_support_counts=covariance_support_counts,
        covariance_pair_counts=covariance_pair_counts,
        covariance_diagnostics=diagnostics,
        fit_method="direct_sparse_block_covariance",
        score_method="joint_PACE",
        provenance={
            **dict(trajectories.provenance),
            "sparse_mfpca": sparse_provenance,
        },
    )


def sparse_mfpca_score_frame(
    result: SparseMFPCAResult,
) -> pd.DataFrame:
    """Return joint sparse-MFPCA scores with curve IDs and metadata."""

    if not isinstance(result, SparseMFPCAResult):
        raise TypeError("result must be a SparseMFPCAResult")
    frame = result.metadata.reset_index(drop=True).copy()
    frame.insert(0, "curve_id", list(result.curve_ids))
    for component in range(result.n_components):
        frame[f"SMFPC{component + 1}"] = result.scores[:, component]
    return frame


def sparse_mfpca_reporting_text(
    result: SparseMFPCAResult,
    *,
    digits: int = 3,
) -> str:
    """Generate audit-oriented reporting text for sparse multivariate FPCA."""

    if not isinstance(result, SparseMFPCAResult):
        raise TypeError("result must be a SparseMFPCAResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")

    provenance = result.provenance.get("sparse_mfpca", {})
    diagnostics = result.score_diagnostics
    status = diagnostics["status_code"].astype(str)
    failed = int(np.count_nonzero(status.to_numpy() != "ok"))
    solved = int(np.count_nonzero(status.to_numpy() == "ok"))
    psd = result.covariance_diagnostics
    error_text = np.array2string(
        result.measurement_error_covariance,
        precision=digits,
        separator=", ",
    )

    return (
        f"Native sparse multivariate FPCA was fitted jointly to dimensions "
        f"{result.dimensions[0]!r} and {result.dimensions[1]!r} for "
        f"{result.n_curves} curve(s), retaining {result.n_components} joint "
        f"component(s). The vector mean and direct Cxx/Cxy/Cyy latent "
        f"covariance surfaces used declared local-linear bandwidths "
        f"{provenance.get('mean_bandwidth')} and "
        f"{provenance.get('covariance_bandwidth')}; all latent covariance "
        f"products excluded same-time pairs. Cxy was fitted directionally, "
        f"was not self-symmetrized, and Cyx was defined as its transpose. "
        f"The full joint operator used PSD action "
        f"{psd.get('requested_action')!r} (applied="
        f"{psd.get('applied_action')!r}; correction Frobenius norm="
        f"{float(psd.get('correction_frobenius_norm', np.nan)):.{digits}f}). "
        f"Measurement error used mode "
        f"{provenance.get('measurement_error_mode')!r} with R_epsilon="
        f"{error_text}. Joint PACE scores used the full fitted joint "
        f"covariance plus measurement error and ridge="
        f"{provenance.get('score_ridge')}, never a rank-K covariance "
        f"reconstruction. {solved} curve(s) were scored successfully and "
        f"{failed} retained score-system failure(s) were recorded under "
        f"failure_action={provenance.get('score_failure_action')!r}. Raw "
        f"sparse trajectories were not pre-interpolated; population "
        f"functions were evaluated at retained native times."
    )
