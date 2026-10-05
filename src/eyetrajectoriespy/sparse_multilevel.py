"""Native sparse participant/trial multilevel FPCA for irregular trajectories.

This 1.1 development capability implements the exchangeable two-level model

    Y_ij(t) = mu(t) + U_i(t) + V_ij(t) + epsilon_ij(t)

without interpolating raw sparse trajectories onto a common grid. Population
functions are smoothed on a declared evaluation grid and then evaluated at
native times for joint Gaussian BLUP score recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_multilevel import (
    raw_cross_trial_covariance_pairs,
    sparse_multilevel_blup_scores,
)
from ._sparse_native import (
    SparseNativeError,
    estimate_noise_variance_diagonal_difference,
    local_linear_covariance_surface,
    local_linear_smooth_1d,
    raw_offdiagonal_covariance_pairs,
    repair_covariance_psd,
    rotated_local_quadratic_covariance_diagonal,
    weighted_covariance_eigendecomposition,
)
from .sparse_native import (
    _analysis_support_views,
    _validate_evaluation_grid,
    _validate_native_sparse_dimension,
    _validate_native_sparse_settings,
)
from .types import IrregularTrajectorySet


@dataclass(frozen=True)
class SparseMultilevelFPCAResult:
    """Native sparse two-level participant/trial functional decomposition."""

    evaluation_grid: np.ndarray
    dimension: str
    participant_column: str
    curve_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]
    grand_mean: np.ndarray
    smoothed_total_covariance: np.ndarray
    smoothed_between_covariance: np.ndarray
    smoothed_within_covariance: np.ndarray
    total_covariance: np.ndarray
    between_covariance: np.ndarray
    within_covariance: np.ndarray
    participant_eigenvalues: np.ndarray
    participant_eigenfunctions: np.ndarray
    trial_eigenvalues: np.ndarray
    trial_eigenfunctions: np.ndarray
    participant_scores: pd.DataFrame
    trial_scores: pd.DataFrame
    score_diagnostics: pd.DataFrame
    noise_variance: float
    quadrature_weights: np.ndarray
    mean_support_counts: np.ndarray
    total_covariance_support_counts: np.ndarray
    between_covariance_support_counts: np.ndarray
    covariance_diagnostics: Mapping[str, Any]
    support_diagnostics: Mapping[str, Any]
    noise_raw_diagonal: np.ndarray | None = None
    noise_diagonal_difference: np.ndarray | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


def _psd_audit_dict(result) -> dict[str, Any]:
    audit = result.audit
    return {
        "requested_action": audit.requested_action,
        "applied_action": audit.applied_action,
        "tolerance": float(audit.tolerance),
        "pre_repair_operator_eigenvalues": (
            audit.pre_repair_operator_eigenvalues.tolist()
        ),
        "negative_eigenvalue_count": int(audit.negative_eigenvalue_count),
        "substantial_negative_eigenvalue_count": int(
            audit.substantial_negative_eigenvalue_count
        ),
        "most_negative_eigenvalue": float(audit.most_negative_eigenvalue),
        "correction_frobenius_norm": float(audit.correction_frobenius_norm),
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


def _validate_hierarchy(
    trajectories: IrregularTrajectorySet,
    *,
    participant_column: str,
) -> tuple[np.ndarray, tuple[str, ...], dict[str, int]]:
    if not isinstance(participant_column, str) or not participant_column:
        raise ValueError("participant_column must be a non-empty string")
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column {participant_column!r}"
        )
    raw = trajectories.metadata[participant_column]
    if raw.isna().any():
        raise ValueError("participant metadata must not contain missing values")
    participants = raw.astype(str).to_numpy()
    if np.any(np.char.str_len(participants.astype(str)) == 0):
        raise ValueError("participant identifiers must be non-empty")
    unique = tuple(pd.unique(participants).tolist())
    if len(unique) < 3:
        raise SparseNativeError(
            "insufficient_participants",
            "native sparse multilevel FPCA requires at least three participants",
            details={"n_participants": len(unique)},
        )
    trial_counts = {
        participant: int(np.count_nonzero(participants == participant))
        for participant in unique
    }
    repeated = [
        participant
        for participant, count in trial_counts.items()
        if count >= 2
    ]
    if len(repeated) < 3:
        raise SparseNativeError(
            "insufficient_repeated_participants",
            "between-participant covariance requires at least three participants with repeated trials",
            details={
                "n_participants": len(unique),
                "n_repeated_participants": len(repeated),
                "trial_counts": trial_counts,
            },
        )
    return participants, unique, trial_counts


def _validate_multilevel_settings(
    *,
    participant_components: int,
    trial_components: int,
    weighting: str,
    mean_smoother: str,
    covariance_smoother: str,
    kernel: str,
    noise_variance_method: str,
    measurement_error_variance: float | None,
    noise_support: tuple[float, float] | None,
) -> None:
    _validate_native_sparse_settings(
        n_components=participant_components,
        mean_smoother=mean_smoother,
        covariance_smoother=covariance_smoother,
        kernel=kernel,
        noise_variance_method=noise_variance_method,
        measurement_error_variance=measurement_error_variance,
        noise_support=noise_support,
    )
    if isinstance(trial_components, bool) or not isinstance(trial_components, int):
        raise TypeError("trial_components must be an integer")
    if trial_components < 1:
        raise ValueError("trial_components must be positive")
    if weighting != "observation":
        raise ValueError(
            "weighting must be 'observation' in the first sparse multilevel tranche"
        )


def fit_sparse_multilevel_fpca(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    participant_column: str,
    participant_components: int,
    trial_components: int,
    evaluation_grid: np.ndarray,
    mean_bandwidth: float,
    total_covariance_bandwidth: float,
    between_covariance_bandwidth: float,
    noise_bandwidth: float | None = None,
    noise_support: tuple[float, float] | None = None,
    analysis_support_action: str = "error",
    weighting: str = "observation",
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
    min_participant_score_samples: int = 2,
    score_failure_action: str = "error",
    mean_min_local_points: int = 3,
    total_covariance_min_local_pairs: int = 6,
    between_covariance_min_local_pairs: int = 6,
    noise_min_local_points: int = 3,
) -> SparseMultilevelFPCAResult:
    """Fit native sparse participant/trial multilevel FPCA.

    The estimator targets an exchangeable two-level hierarchy. Trial-condition
    or visit-specific fixed functional effects are not estimated; users must
    stratify or remove such effects upstream when scientifically required.

    Raw sparse trials remain on native grids. ``evaluation_grid`` is used only
    for fitted population functions/operators. Population quantities are later
    evaluated at native times for joint participant/trial BLUP scores.

    The first tranche uses observation/raw-pair weighting. Participants with
    more retained observations or covariance pairs can therefore contribute
    more to local smoothers; this is recorded explicitly and is not described as
    equal-participant weighting.
    """

    dimension_index = _validate_native_sparse_dimension(
        trajectories,
        dimension=dimension,
    )
    participants, unique_participants, raw_trial_counts = _validate_hierarchy(
        trajectories,
        participant_column=participant_column,
    )
    grid = _validate_evaluation_grid(trajectories, evaluation_grid)
    _validate_multilevel_settings(
        participant_components=participant_components,
        trial_components=trial_components,
        weighting=weighting,
        mean_smoother=mean_smoother,
        covariance_smoother=covariance_smoother,
        kernel=kernel,
        noise_variance_method=noise_variance_method,
        measurement_error_variance=measurement_error_variance,
        noise_support=noise_support,
    )

    original_values = tuple(
        np.asarray(values[:, dimension_index], dtype=float)
        for values in trajectories.values
    )
    curve_times, curve_values, support = _analysis_support_views(
        trajectories,
        original_values,
        grid,
        action=analysis_support_action,
    )
    analysis_counts = np.asarray(
        [int(time.size) for time in curve_times],
        dtype=int,
    )
    if np.any(analysis_counts == 0):
        failed = [
            str(trajectories.curve_ids[index])
            for index in np.flatnonzero(analysis_counts == 0)
        ]
        raise SparseNativeError(
            "curve_without_analysis_support",
            "every trial must retain at least one observation on analysis support",
            details={"curve_ids": failed},
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
    for time, observed in zip(curve_times, curve_values, strict=True):
        native_mean = local_linear_smooth_1d(
            pooled_time,
            pooled_values,
            np.asarray(time, dtype=float),
            bandwidth=mean_bandwidth,
            min_local_points=mean_min_local_points,
        ).values
        residuals.append(np.asarray(observed, dtype=float) - native_mean)
    residual_tuple = tuple(residuals)

    total_pairs = raw_offdiagonal_covariance_pairs(
        curve_times,
        residual_tuple,
        include_mirror=True,
    )
    between_pairs = raw_cross_trial_covariance_pairs(
        curve_times,
        residual_tuple,
        participants,
        include_mirror=True,
    )
    total_fit = local_linear_covariance_surface(
        total_pairs,
        grid,
        bandwidth=total_covariance_bandwidth,
        min_local_pairs=total_covariance_min_local_pairs,
    )
    between_fit = local_linear_covariance_surface(
        between_pairs,
        grid,
        bandwidth=between_covariance_bandwidth,
        min_local_pairs=between_covariance_min_local_pairs,
    )
    smoothed_within = 0.5 * (
        (total_fit.values - between_fit.values)
        + (total_fit.values - between_fit.values).T
    )

    noise_result = None
    if noise_variance_method == "diagonal_difference":
        if noise_bandwidth is None:
            raise ValueError(
                "noise_bandwidth is required when noise_variance_method='diagonal_difference'"
            )
        latent_diagonal = rotated_local_quadratic_covariance_diagonal(
            total_pairs,
            grid,
            bandwidth=total_covariance_bandwidth,
            min_local_pairs=total_covariance_min_local_pairs,
        )
        noise_result = estimate_noise_variance_diagonal_difference(
            curve_times,
            residual_tuple,
            grid,
            total_fit.values,
            latent_diagonal=latent_diagonal.values,
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

    between_psd = repair_covariance_psd(
        between_fit.values,
        grid,
        action=psd_action,
        tolerance=psd_tolerance,
    )
    within_psd = repair_covariance_psd(
        smoothed_within,
        grid,
        action=psd_action,
        tolerance=psd_tolerance,
    )
    between_eigen = weighted_covariance_eigendecomposition(
        between_psd.covariance,
        grid,
        n_components=participant_components,
        positive_tolerance=positive_eigen_tolerance,
    )
    within_eigen = weighted_covariance_eigendecomposition(
        within_psd.covariance,
        grid,
        n_components=trial_components,
        positive_tolerance=positive_eigen_tolerance,
    )

    score_result = sparse_multilevel_blup_scores(
        trajectories.curve_ids,
        participants,
        curve_times,
        curve_values,
        evaluation_grid=grid,
        fitted_mean=mean_fit.values,
        between_covariance=between_psd.covariance,
        within_covariance=within_psd.covariance,
        participant_eigenvalues=between_eigen.eigenvalues,
        participant_eigenfunctions=between_eigen.eigenfunctions,
        trial_eigenvalues=within_eigen.eigenvalues,
        trial_eigenfunctions=within_eigen.eigenfunctions,
        noise_variance=noise_variance,
        participant_components=participant_components,
        trial_components=trial_components,
        score_ridge=score_ridge,
        condition_limit=score_condition_limit,
        min_participant_samples=min_participant_score_samples,
        failure_action=score_failure_action,
    )

    participant_scores = pd.DataFrame(
        score_result.participant_scores,
        columns=[
            f"participant_FPC{component + 1}"
            for component in range(participant_components)
        ],
    )
    participant_scores.insert(
        0,
        participant_column,
        list(score_result.participant_ids),
    )
    trial_scores = pd.DataFrame(
        score_result.trial_scores,
        columns=[f"trial_FPC{component + 1}" for component in range(trial_components)],
    )
    trial_scores.insert(0, participant_column, participants.tolist())
    trial_scores.insert(0, "curve_id", list(score_result.curve_ids))

    between_psd_diagnostics = _psd_audit_dict(between_psd)
    within_psd_diagnostics = _psd_audit_dict(within_psd)
    covariance_diagnostics: dict[str, Any] = {
        "between": between_psd_diagnostics,
        "within": within_psd_diagnostics,
        "smoothed_within_definition": "smoothed_total_minus_smoothed_between",
        "score_total_definition": "repaired_between_plus_repaired_within",
        "post_psd_total_difference_frobenius_norm": float(
            np.linalg.norm(
                (between_psd.covariance + within_psd.covariance)
                - total_fit.values
            )
        ),
    }

    trial_counts = {
        participant: int(np.count_nonzero(participants == participant))
        for participant in unique_participants
    }
    participant_sample_counts = {
        participant: int(
            np.sum(analysis_counts[np.flatnonzero(participants == participant)])
        )
        for participant in unique_participants
    }
    between_pair_counts = np.bincount(
        between_pairs.curve_index,
        minlength=len(unique_participants),
    )
    support_diagnostics: dict[str, Any] = {
        **support,
        "n_participants": int(len(unique_participants)),
        "n_repeated_participants": int(
            sum(count >= 2 for count in trial_counts.values())
        ),
        "raw_trial_counts_by_participant": raw_trial_counts,
        "analysis_trial_counts_by_participant": trial_counts,
        "analysis_sample_counts_by_participant": participant_sample_counts,
        "total_covariance_pair_count": int(total_pairs.n_pairs),
        "between_covariance_pair_count": int(between_pairs.n_pairs),
        "between_pair_counts_by_participant": {
            participant: int(between_pair_counts[index])
            for index, participant in enumerate(unique_participants)
        },
        "single_trial_participants": [
            participant
            for participant, count in trial_counts.items()
            if count == 1
        ],
    }

    total_used = between_psd.covariance + within_psd.covariance
    provenance: dict[str, Any] = {
        **dict(trajectories.provenance),
        "sparse_multilevel_fpca": {
            "backend": "native",
            "method": "sparse_two_level_covariance_BLUP",
            "model": "Y_ij(t)=mu(t)+U_i(t)+V_ij(t)+epsilon_ij(t)",
            "dimension": dimension,
            "participant_column": participant_column,
            "participant_components": int(participant_components),
            "trial_components": int(trial_components),
            "n_participants": int(len(unique_participants)),
            "n_trials": int(trajectories.n_curves),
            "exchangeable_trials_assumed": True,
            "trial_fixed_effects_estimated": False,
            "fixed_effect_requirement": (
                "condition_or_visit effects must be absent, stratified, or removed upstream"
            ),
            "weighting": weighting,
            "weighting_interpretation": (
                "pooled native observations for mean smoothing; pooled raw covariance pairs for covariance smoothing"
            ),
            "equal_participant_weighting_claimed": False,
            "mean_smoother": mean_smoother,
            "covariance_smoother": covariance_smoother,
            "kernel": kernel,
            "mean_bandwidth": float(mean_bandwidth),
            "total_covariance_bandwidth": float(total_covariance_bandwidth),
            "between_covariance_bandwidth": float(between_covariance_bandwidth),
            "between_covariance_source": (
                "same_participant_distinct_trial_cross_products"
            ),
            "total_covariance_source": "within_trial_offdiagonal_products",
            "within_covariance_definition": "smoothed_total_minus_smoothed_between",
            "measurement_error_method": noise_variance_method,
            "noise_variance": float(noise_variance),
            "noise_bandwidth": (
                None if noise_bandwidth is None else float(noise_bandwidth)
            ),
            "noise_support": (
                None if noise_support is None else list(noise_support)
            ),
            "psd_action": psd_action,
            "psd_tolerance": float(psd_tolerance),
            "positive_eigen_tolerance": float(positive_eigen_tolerance),
            "score_method": "joint_hierarchical_Gaussian_BLUP",
            "score_covariance_source": score_result.covariance_source,
            "rank_k_covariance_used_for_scoring": False,
            "score_ridge": float(score_ridge),
            "score_condition_limit": float(score_condition_limit),
            "min_participant_score_samples": int(min_participant_score_samples),
            "score_failure_action": score_failure_action,
            "raw_sparse_trajectory_interpolation_performed": False,
            "population_function_evaluation_at_native_times": True,
            "automatic_bandwidth_selection_performed": False,
            "population_estimation_uncertainty_propagated": False,
            "analysis_support_action": analysis_support_action,
            "covariance_psd": covariance_diagnostics,
        },
    }
    if measurement_error_variance is not None:
        provenance["sparse_multilevel_fpca"][
            "measurement_error_variance_supplied"
        ] = float(measurement_error_variance)

    return SparseMultilevelFPCAResult(
        evaluation_grid=grid.copy(),
        dimension=dimension,
        participant_column=participant_column,
        curve_ids=tuple(str(value) for value in trajectories.curve_ids),
        participant_ids=tuple(str(value) for value in score_result.participant_ids),
        grand_mean=mean_fit.values.copy(),
        smoothed_total_covariance=total_fit.values.copy(),
        smoothed_between_covariance=between_fit.values.copy(),
        smoothed_within_covariance=smoothed_within.copy(),
        total_covariance=total_used.copy(),
        between_covariance=between_psd.covariance.copy(),
        within_covariance=within_psd.covariance.copy(),
        participant_eigenvalues=between_eigen.eigenvalues.copy(),
        participant_eigenfunctions=between_eigen.eigenfunctions.copy(),
        trial_eigenvalues=within_eigen.eigenvalues.copy(),
        trial_eigenfunctions=within_eigen.eigenfunctions.copy(),
        participant_scores=participant_scores,
        trial_scores=trial_scores,
        score_diagnostics=score_result.diagnostics.copy(),
        noise_variance=float(noise_variance),
        quadrature_weights=between_eigen.quadrature_weights.copy(),
        mean_support_counts=mean_fit.support_counts.copy(),
        total_covariance_support_counts=total_fit.support_counts.copy(),
        between_covariance_support_counts=between_fit.support_counts.copy(),
        covariance_diagnostics=covariance_diagnostics,
        support_diagnostics=support_diagnostics,
        noise_raw_diagonal=(
            None if noise_result is None else noise_result.raw_diagonal.copy()
        ),
        noise_diagonal_difference=(
            None
            if noise_result is None
            else noise_result.diagonal_difference.copy()
        ),
        provenance=provenance,
    )


def sparse_multilevel_fpca_reporting_text(
    result: SparseMultilevelFPCAResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-ready wording for the sparse multilevel fit."""

    if not isinstance(result, SparseMultilevelFPCAResult):
        raise TypeError("result must be a SparseMultilevelFPCAResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")
    provenance = result.provenance.get("sparse_multilevel_fpca", {})
    failed = int(
        np.count_nonzero(result.score_diagnostics["status_code"].to_numpy() != "ok")
    )
    between_action = result.covariance_diagnostics["between"]["applied_action"]
    within_action = result.covariance_diagnostics["within"]["applied_action"]
    return (
        "Native sparse multilevel FPCA modeled irregular trials as "
        "Y_ij(t)=mu(t)+U_i(t)+V_ij(t)+epsilon_ij(t), with "
        f"{len(result.participant_ids)} participants and {len(result.curve_ids)} trials. "
        "The grand mean used pooled native observations; total latent covariance "
        "used within-trial off-diagonal products and between-participant covariance "
        "used same-participant cross-trial products. The within-trial operator was "
        "defined as smoothed total minus smoothed between covariance before the "
        f"declared PSD policy (between={between_action}, within={within_action}). "
        f"Measurement-error variance was {result.noise_variance:.{digits}g}. "
        "Participant and trial scores were recovered jointly by Gaussian BLUP using "
        "the full repaired between/within covariance surfaces at native timestamps, "
        "not rank-truncated reconstructions. "
        f"{failed} participant score systems failed under the declared policy. "
        "The first sparse multilevel tranche assumes exchangeable repeated trials, "
        "does not estimate trial-condition fixed functional effects, uses observation/"
        "raw-pair weighting rather than equal-participant weighting, does not "
        "interpolate raw sparse trajectories, and does not propagate population-"
        "estimation or bandwidth uncertainty."
    )
