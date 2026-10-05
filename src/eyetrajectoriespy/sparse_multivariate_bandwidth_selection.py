"""Audited bandwidth selection for native sparse planar MFPCA.

The selector is deliberately separate from :func:`fit_sparse_mfpca`. Each
candidate refits only the native planar population mean/covariance objects
inside training folds and evaluates whole held-out curves under the full joint
Gaussian observation model. Joint-PACE scores are not part of the selection
criterion and no validation observation contributes to population fitting.

The first qualified multivariate tranche tunes only mean and latent-covariance
bandwidths. The declared 2x2 measurement-error covariance is held fixed across
all candidates and folds.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import product
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_multivariate import (
    PlanarCovarianceBlocks,
    SparsePlanarMeanCovarianceResult,
    build_joint_score_covariance,
    estimate_sparse_planar_mean_covariance,
    evaluate_planar_covariance,
    resolve_measurement_error_covariance,
    stack_planar_mean,
    stack_planar_observations,
)
from ._sparse_native import SparseNativeError
from .sparse_bandwidth_selection import (
    _make_folds,
    _positive_grid,
    _validate_evaluation_grid,
)
from .types import IrregularTrajectorySet


_CRITERION = "mean_curve_planar_gaussian_nll"
_METHOD = "group_aware_training_fold_sparse_planar_population_cv"


@dataclass(frozen=True)
class SparseMFPCABandwidthSelectionResult:
    """Auditable CV result for sparse-MFPCA mean/covariance bandwidths."""

    assignments: pd.DataFrame
    fold_results: pd.DataFrame
    curve_losses: pd.DataFrame
    candidate_summary: pd.DataFrame
    candidates: pd.DataFrame
    selected_bandwidths: Mapping[str, float | str] | None
    criterion: str
    resampling_unit: str
    n_splits: int
    group_column: str | None
    min_valid_folds: int
    status_code: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


def _validate_dimensions(
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
            "sparse planar bandwidth selection requires at least three curves",
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
        mismatch = finite_x != finite_y
        if np.any(mismatch):
            indices = np.flatnonzero(mismatch)
            raise SparseNativeError(
                "coordinate_specific_missingness_unsupported",
                "x and y must be jointly observed at every retained sparse timestamp",
                details={
                    "curve_id": str(curve_id),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
        nonfinite = ~(finite_x & finite_y)
        if np.any(nonfinite):
            indices = np.flatnonzero(nonfinite)
            raise SparseNativeError(
                "nonfinite_sparse_planar_observation",
                "bandwidth selection requires finite paired planar samples",
                details={
                    "curve_id": str(curve_id),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
    return x_index, y_index


def _validate_selector_inputs(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str],
    evaluation_grid: np.ndarray,
    measurement_error: str,
    measurement_error_variance: tuple[float, float] | None,
    measurement_error_covariance: np.ndarray | None,
    analysis_support_action: str,
    n_splits: int,
    resampling_unit: str,
    group_column: str | None,
    min_valid_folds: int | None,
    predictive_condition_limit: float,
    failure_action: str,
) -> tuple[
    np.ndarray,
    tuple[int, int],
    np.ndarray,
    int,
]:
    indices = _validate_dimensions(trajectories, dimensions)
    grid = _validate_evaluation_grid(evaluation_grid)
    if analysis_support_action not in {"error", "restrict"}:
        raise ValueError("analysis_support_action must be 'error' or 'restrict'")
    if analysis_support_action == "error":
        outside = [
            str(curve_id)
            for curve_id, time in zip(
                trajectories.curve_ids,
                trajectories.time,
                strict=True,
            )
            if np.any((time < grid[0]) | (time > grid[-1]))
        ]
        if outside:
            raise SparseNativeError(
                "observations_outside_analysis_support",
                "training/validation observations lie outside declared support",
                details={
                    "analysis_support": [float(grid[0]), float(grid[-1])],
                    "curve_ids": outside,
                },
            )

    resolved_error = resolve_measurement_error_covariance(
        measurement_error,
        measurement_error_variance=measurement_error_variance,
        measurement_error_covariance=measurement_error_covariance,
    )

    if isinstance(n_splits, bool) or not isinstance(n_splits, int) or n_splits < 2:
        raise ValueError("n_splits must be an integer >= 2")
    if resampling_unit not in {"curve", "group"}:
        raise ValueError("resampling_unit must be 'curve' or 'group'")
    if resampling_unit == "curve":
        if n_splits > trajectories.n_curves:
            raise ValueError("n_splits cannot exceed number of trajectories")
    else:
        if group_column is None:
            raise ValueError("group_column is required for group resampling")
        if group_column not in trajectories.metadata.columns:
            raise ValueError(f"metadata does not contain group column {group_column!r}")
        if trajectories.metadata[group_column].isna().any():
            raise ValueError("group_column contains missing values")
        n_groups = trajectories.metadata[group_column].astype(str).nunique()
        if n_splits > n_groups:
            raise ValueError("n_splits cannot exceed number of unique groups")

    if min_valid_folds is None:
        required_folds = n_splits
    elif (
        isinstance(min_valid_folds, bool)
        or not isinstance(min_valid_folds, int)
        or min_valid_folds < 1
        or min_valid_folds > n_splits
    ):
        raise ValueError("min_valid_folds must be an integer in [1, n_splits]")
    else:
        required_folds = min_valid_folds

    limit = float(predictive_condition_limit)
    if not np.isfinite(limit) or limit <= 1:
        raise ValueError("predictive_condition_limit must be finite and > 1")
    if failure_action not in {"retain", "error"}:
        raise ValueError("failure_action must be 'retain' or 'error'")
    return grid, indices, resolved_error.covariance.copy(), int(required_folds)


def _candidate_table(
    mean_bandwidths: tuple[float, ...],
    covariance_bandwidths: tuple[float, ...],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (mean_bw, covariance_bw) in enumerate(
        product(mean_bandwidths, covariance_bandwidths)
    ):
        rows.append(
            {
                "candidate_id": f"candidate_{index:04d}",
                "mean_bandwidth": float(mean_bw),
                "covariance_bandwidth": float(covariance_bw),
            }
        )
    return pd.DataFrame(rows)


def _effective_time_point_count(
    trajectories: IrregularTrajectorySet,
    grid: np.ndarray,
    *,
    action: str,
) -> int:
    if action == "error":
        return int(np.sum(trajectories.sample_counts))
    start = float(grid[0])
    end = float(grid[-1])
    return int(
        np.sum(
            [
                np.count_nonzero(
                    (np.asarray(time, dtype=float) >= start)
                    & (np.asarray(time, dtype=float) <= end)
                )
                for time in trajectories.time
            ]
        )
    )


def _effective_validation_curve(
    time: np.ndarray,
    values: np.ndarray,
    *,
    x_index: int,
    y_index: int,
    grid: np.ndarray,
    action: str,
) -> tuple[np.ndarray, np.ndarray, int]:
    target = np.asarray(time, dtype=float)
    planar = np.asarray(values[:, [x_index, y_index]], dtype=float)
    mask = (target >= grid[0]) & (target <= grid[-1])
    outside = int(np.count_nonzero(~mask))
    if action == "error" and outside:
        raise SparseNativeError(
            "observations_outside_analysis_support",
            "held-out planar curve has observations outside declared support",
            details={"outside_observation_count": outside},
        )
    if action == "restrict":
        target = target[mask]
        planar = planar[mask]
    if target.size == 0:
        raise SparseNativeError(
            "no_validation_observations_on_support",
            "held-out planar curve has no observations on declared support",
        )
    if not np.all(np.isfinite(target)) or not np.all(np.isfinite(planar)):
        raise SparseNativeError(
            "nonfinite_sparse_planar_observation",
            "held-out planar curve contains non-finite retained observations",
        )
    return target, planar, outside


def _curve_planar_gaussian_nll(
    population: SparsePlanarMeanCovarianceResult,
    time: np.ndarray,
    observed: np.ndarray,
    *,
    measurement_error_covariance: np.ndarray,
    predictive_condition_limit: float,
) -> tuple[float, float, float, float]:
    target = np.asarray(time, dtype=float)
    planar = np.asarray(observed, dtype=float)
    if target.ndim != 1 or planar.shape != (target.size, 2):
        raise ValueError("time/observed must have shapes (m,) and (m, 2)")

    native_covariance = evaluate_planar_covariance(
        population.evaluation_grid,
        population.covariance_blocks,
        target,
        order="time_major",
    )
    sigma = build_joint_score_covariance(
        native_covariance,
        measurement_error_covariance,
        score_ridge=0.0,
    )
    eigenvalues = np.linalg.eigvalsh(sigma)
    minimum = float(np.min(eigenvalues))
    maximum = float(np.max(eigenvalues))
    condition = np.inf if minimum <= 0 else maximum / minimum
    if minimum <= 0:
        raise SparseNativeError(
            "predictive_joint_covariance_not_positive_definite",
            "held-out planar predictive covariance is not positive definite",
            details={
                "minimum_eigenvalue": minimum,
                "maximum_eigenvalue": maximum,
            },
        )
    if condition > predictive_condition_limit:
        raise SparseNativeError(
            "predictive_joint_covariance_ill_conditioned",
            "held-out planar predictive covariance exceeds the condition-number limit",
            details={
                "condition_number": float(condition),
                "condition_limit": float(predictive_condition_limit),
            },
        )

    residual = stack_planar_observations(planar) - stack_planar_mean(
        population.evaluation_grid,
        population.mean,
        target,
    )
    solved = np.linalg.solve(sigma, residual)
    quadratic = float(residual @ solved)
    log_determinant = float(np.sum(np.log(eigenvalues)))
    dimension = int(2 * target.size)
    nll = 0.5 * (
        log_determinant
        + quadratic
        + dimension * np.log(2.0 * np.pi)
    )
    return (
        float(nll / dimension),
        float(condition),
        minimum,
        maximum,
    )


def _failure_details(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, SparseNativeError):
        return exc.code, str(exc)
    return type(exc).__name__, str(exc)


def _summarise_candidates(
    candidates: pd.DataFrame,
    fold_results: pd.DataFrame,
    *,
    min_valid_folds: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate in candidates.to_dict(orient="records"):
        candidate_id = str(candidate["candidate_id"])
        subset = fold_results[fold_results["candidate_id"] == candidate_id]
        valid = subset[subset["status_code"] == "ok"]
        losses = valid[_CRITERION].to_numpy(dtype=float)
        mean_loss = float(np.mean(losses)) if losses.size else np.nan
        sd_loss = float(np.std(losses, ddof=1)) if losses.size > 1 else 0.0
        se_loss = float(sd_loss / np.sqrt(losses.size)) if losses.size else np.nan
        rows.append(
            {
                **candidate,
                "mean_loss": mean_loss,
                "sd_loss": sd_loss,
                "se_loss": se_loss,
                "n_valid_folds": int(losses.size),
                "n_failed_folds": int(len(subset) - losses.size),
                "eligible": bool(losses.size >= min_valid_folds),
            }
        )
    return pd.DataFrame(rows)


def _select_minimum_candidate(
    summary: pd.DataFrame,
) -> Mapping[str, float | str] | None:
    eligible = summary[
        summary["eligible"] & np.isfinite(summary["mean_loss"])
    ].copy()
    if eligible.empty:
        return None
    eligible = eligible.sort_values(
        [
            "mean_loss",
            "mean_bandwidth",
            "covariance_bandwidth",
            "candidate_id",
        ],
        ascending=[True, False, False, True],
        kind="mergesort",
    )
    best = eligible.iloc[0]
    return {
        "candidate_id": str(best["candidate_id"]),
        "mean_bandwidth": float(best["mean_bandwidth"]),
        "covariance_bandwidth": float(best["covariance_bandwidth"]),
    }


def select_sparse_mfpca_bandwidths(
    trajectories: IrregularTrajectorySet,
    *,
    dimensions: tuple[str, str] = ("x", "y"),
    evaluation_grid: np.ndarray,
    mean_bandwidths: Sequence[float],
    covariance_bandwidths: Sequence[float],
    measurement_error: str,
    measurement_error_variance: tuple[float, float] | None = None,
    measurement_error_covariance: np.ndarray | None = None,
    analysis_support_action: str = "error",
    n_splits: int = 5,
    resampling_unit: str = "curve",
    group_column: str | None = None,
    shuffle: bool = True,
    random_state: int | None = 0,
    min_valid_folds: int | None = None,
    failure_action: str = "retain",
    predictive_condition_limit: float = 1e12,
    psd_action: str = "error",
    psd_tolerance: float = 1e-8,
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
) -> SparseMFPCABandwidthSelectionResult:
    """Select native sparse-MFPCA mean/covariance bandwidths by CV likelihood.

    Each candidate refits the direct sparse planar population mean and
    Cxx/Cxy/Cyy covariance surfaces from training curves only. Held-out loss is
    the Gaussian negative log predictive density from the full fitted joint
    covariance plus the analyst-declared 2x2 measurement-error covariance,
    normalized by the number of scalar planar observations (2*m_i). Fold loss
    is the equal-weight mean across held-out curves.

    Joint-PACE score estimation is not part of the criterion. The selector does
    not tune measurement error, rank, score ridge, PSD policy, evaluation grid,
    or support policy and never applies selected bandwidths automatically to
    :func:`fit_sparse_mfpca`.
    """

    mean_grid = _positive_grid(mean_bandwidths, name="mean_bandwidths")
    covariance_grid = _positive_grid(
        covariance_bandwidths,
        name="covariance_bandwidths",
    )
    (
        grid,
        (x_index, y_index),
        resolved_error,
        required_folds,
    ) = _validate_selector_inputs(
        trajectories,
        dimensions=dimensions,
        evaluation_grid=evaluation_grid,
        measurement_error=measurement_error,
        measurement_error_variance=measurement_error_variance,
        measurement_error_covariance=measurement_error_covariance,
        analysis_support_action=analysis_support_action,
        n_splits=n_splits,
        resampling_unit=resampling_unit,
        group_column=group_column,
        min_valid_folds=min_valid_folds,
        predictive_condition_limit=predictive_condition_limit,
        failure_action=failure_action,
    )
    splits, assignments, groups = _make_folds(
        trajectories,
        n_splits=n_splits,
        resampling_unit=resampling_unit,
        group_column=group_column,
        shuffle=shuffle,
        random_state=random_state,
    )
    candidates = _candidate_table(mean_grid, covariance_grid)

    fold_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    for candidate in candidates.to_dict(orient="records"):
        candidate_id = str(candidate["candidate_id"])
        mean_bandwidth = float(candidate["mean_bandwidth"])
        covariance_bandwidth = float(candidate["covariance_bandwidth"])
        for fold, (train_idx, validation_idx) in enumerate(splits):
            train = trajectories.subset(train_idx)
            validation = trajectories.subset(validation_idx)
            raw_train_time_points = int(np.sum(train.sample_counts))
            raw_validation_time_points = int(np.sum(validation.sample_counts))
            effective_train_time_points = _effective_time_point_count(
                train,
                grid,
                action=analysis_support_action,
            )
            effective_validation_time_points = _effective_time_point_count(
                validation,
                grid,
                action=analysis_support_action,
            )
            base_row: dict[str, Any] = {
                "candidate_id": candidate_id,
                "fold": int(fold),
                "mean_bandwidth": mean_bandwidth,
                "covariance_bandwidth": covariance_bandwidth,
                "n_train_curves": int(train.n_curves),
                "n_validation_curves": int(validation.n_curves),
                "n_train_time_points_raw": raw_train_time_points,
                "n_validation_time_points_raw": raw_validation_time_points,
                "n_train_time_points_effective": effective_train_time_points,
                "n_validation_time_points_effective": effective_validation_time_points,
                "n_train_planar_observations_raw": 2 * raw_train_time_points,
                "n_validation_planar_observations_raw": 2 * raw_validation_time_points,
                "n_train_planar_observations_effective": 2
                * effective_train_time_points,
                "n_validation_planar_observations_effective": 2
                * effective_validation_time_points,
            }
            try:
                population = estimate_sparse_planar_mean_covariance(
                    train,
                    dimensions=dimensions,
                    evaluation_grid=grid,
                    mean_bandwidth=mean_bandwidth,
                    covariance_bandwidth=covariance_bandwidth,
                    analysis_support_action=analysis_support_action,
                    psd_action=psd_action,
                    psd_tolerance=psd_tolerance,
                    mean_min_local_points=mean_min_local_points,
                    covariance_min_local_pairs=covariance_min_local_pairs,
                )
            except (SparseNativeError, ValueError, np.linalg.LinAlgError) as exc:
                code, message = _failure_details(exc)
                fold_rows.append(
                    {
                        **base_row,
                        "status_code": "fit_failure",
                        "failure_code": code,
                        "failure_message": message,
                        _CRITERION: np.nan,
                        "median_curve_planar_gaussian_nll": np.nan,
                        "n_evaluated_curves": 0,
                        "n_evaluated_time_points": 0,
                        "n_evaluated_planar_observations": 0,
                        "psd_applied_action": None,
                        "psd_relative_operator_correction": np.nan,
                    }
                )
                if failure_action == "error":
                    raise
                continue

            validation_losses: list[float] = []
            validation_time_points = 0
            validation_failed = False
            first_validation_failure: tuple[str, str] | None = None
            for curve_id, time, values in zip(
                validation.curve_ids,
                validation.time,
                validation.values,
                strict=True,
            ):
                raw_time_points = int(len(time))
                try:
                    effective_time, planar, outside = _effective_validation_curve(
                        time,
                        values,
                        x_index=x_index,
                        y_index=y_index,
                        grid=grid,
                        action=analysis_support_action,
                    )
                    loss, condition, minimum, maximum = _curve_planar_gaussian_nll(
                        population,
                        effective_time,
                        planar,
                        measurement_error_covariance=resolved_error,
                        predictive_condition_limit=predictive_condition_limit,
                    )
                    validation_losses.append(loss)
                    validation_time_points += int(effective_time.size)
                    curve_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "fold": int(fold),
                            "curve_id": str(curve_id),
                            "status_code": "ok",
                            "failure_code": None,
                            "failure_message": None,
                            "planar_gaussian_nll_per_scalar_observation": float(loss),
                            "n_time_points_raw": raw_time_points,
                            "n_time_points_evaluated": int(effective_time.size),
                            "n_planar_observations_evaluated": int(2 * effective_time.size),
                            "outside_support_time_points": int(outside),
                            "predictive_condition_number": float(condition),
                            "predictive_minimum_eigenvalue": float(minimum),
                            "predictive_maximum_eigenvalue": float(maximum),
                            "observation_order": "time_major_interleaved_xy",
                        }
                    )
                except (SparseNativeError, ValueError, np.linalg.LinAlgError) as exc:
                    validation_failed = True
                    code, message = _failure_details(exc)
                    if first_validation_failure is None:
                        first_validation_failure = (code, message)
                    curve_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "fold": int(fold),
                            "curve_id": str(curve_id),
                            "status_code": "validation_failure",
                            "failure_code": code,
                            "failure_message": message,
                            "planar_gaussian_nll_per_scalar_observation": np.nan,
                            "n_time_points_raw": raw_time_points,
                            "n_time_points_evaluated": 0,
                            "n_planar_observations_evaluated": 0,
                            "outside_support_time_points": np.nan,
                            "predictive_condition_number": np.nan,
                            "predictive_minimum_eigenvalue": np.nan,
                            "predictive_maximum_eigenvalue": np.nan,
                            "observation_order": "time_major_interleaved_xy",
                        }
                    )
                    if failure_action == "error":
                        raise

            audit = population.operator_audit
            if validation_failed:
                code, message = first_validation_failure or (
                    "validation_failure",
                    "held-out planar validation failed",
                )
                fold_rows.append(
                    {
                        **base_row,
                        "status_code": "validation_failure",
                        "failure_code": code,
                        "failure_message": message,
                        _CRITERION: np.nan,
                        "median_curve_planar_gaussian_nll": np.nan,
                        "n_evaluated_curves": int(len(validation_losses)),
                        "n_evaluated_time_points": int(validation_time_points),
                        "n_evaluated_planar_observations": int(
                            2 * validation_time_points
                        ),
                        "psd_applied_action": audit.applied_action,
                        "psd_relative_operator_correction": float(
                            audit.relative_operator_correction_frobenius_norm
                        ),
                    }
                )
                continue

            losses = np.asarray(validation_losses, dtype=float)
            fold_rows.append(
                {
                    **base_row,
                    "status_code": "ok",
                    "failure_code": None,
                    "failure_message": None,
                    _CRITERION: float(np.mean(losses)),
                    "median_curve_planar_gaussian_nll": float(np.median(losses)),
                    "n_evaluated_curves": int(losses.size),
                    "n_evaluated_time_points": int(validation_time_points),
                    "n_evaluated_planar_observations": int(
                        2 * validation_time_points
                    ),
                    "psd_applied_action": audit.applied_action,
                    "psd_relative_operator_correction": float(
                        audit.relative_operator_correction_frobenius_norm
                    ),
                }
            )

    fold_results = pd.DataFrame(fold_rows)
    curve_losses = pd.DataFrame(curve_rows)
    summary = _summarise_candidates(
        candidates,
        fold_results,
        min_valid_folds=required_folds,
    )
    selected = _select_minimum_candidate(summary)
    status_code = "ok" if selected is not None else "no_eligible_candidate"

    provenance: dict[str, Any] = {
        "method": _METHOD,
        "criterion": _CRITERION,
        "criterion_formula": (
            "0.5*(logdet(Sigma_i)+r_i^T Sigma_i^-1 r_i+"
            "2*m_i*log(2*pi))/(2*m_i); fold mean weights held-out curves equally"
        ),
        "predictive_covariance": "full_fitted_joint_covariance_plus_declared_measurement_error",
        "population_refit_inside_fold": True,
        "joint_pace_scoring_performed": False,
        "validation_observations_used_for_population_fitting": False,
        "validation_observations_used_for_score_fitting": False,
        "full_fitted_joint_covariance_used_for_validation": True,
        "rank_k_covariance_used_for_validation": False,
        "score_ridge_included_in_validation_covariance": False,
        "raw_sparse_trajectory_interpolation_performed": False,
        "score_observation_order": "time_major_interleaved_xy",
        "operator_storage_order": "channel_major",
        "measurement_error_mode": measurement_error,
        "measurement_error_covariance": resolved_error.copy(),
        "measurement_error_tuned": False,
        "measurement_error_policy": "fixed_declared_across_candidates_and_folds",
        "resampling_unit": resampling_unit,
        "group_column": group_column if resampling_unit == "group" else None,
        "group_leakage_prevented": resampling_unit == "group",
        "n_splits": int(n_splits),
        "shuffle": bool(shuffle) if resampling_unit == "curve" else False,
        "random_state": (
            random_state if resampling_unit == "curve" and shuffle else None
        ),
        "min_valid_folds": int(required_folds),
        "failure_action": failure_action,
        "predictive_condition_limit": float(predictive_condition_limit),
        "candidate_order": "sorted_unique_mean_x_covariance_cartesian_product",
        "selection_rule": "minimum_mean_fold_loss",
        "tie_break_rule": (
            "minimum loss, then larger mean/covariance bandwidths "
            "lexicographically, then candidate_id"
        ),
        "one_se_rule_implemented": False,
        "one_se_reason": (
            "no predeclared scalar simplicity ordering for a multidimensional "
            "bandwidth tuple"
        ),
        "automatic_fit_bandwidth_selection_performed": False,
        "selected_values_must_be_passed_explicitly_to_fit_sparse_mfpca": True,
        "rank_tuned": False,
        "score_ridge_tuned": False,
        "evaluation_grid_tuned": False,
        "psd_policy_tuned": False,
        "support_policy_tuned": False,
        "evaluation_grid": grid.tolist(),
        "analysis_support_action": analysis_support_action,
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "candidate_count": int(len(candidates)),
        "fold_assignment_count": int(len(assignments)),
    }
    if groups is not None:
        provenance["group_count"] = int(len(pd.unique(groups)))

    return SparseMFPCABandwidthSelectionResult(
        assignments=assignments,
        fold_results=fold_results,
        curve_losses=curve_losses,
        candidate_summary=summary,
        candidates=candidates,
        selected_bandwidths=selected,
        criterion=_CRITERION,
        resampling_unit=resampling_unit,
        n_splits=int(n_splits),
        group_column=group_column if resampling_unit == "group" else None,
        min_valid_folds=int(required_folds),
        status_code=status_code,
        provenance=provenance,
    )


def sparse_mfpca_bandwidth_selection_reporting_text(
    result: SparseMFPCABandwidthSelectionResult,
    *,
    digits: int = 3,
) -> str:
    """Return conservative audit-oriented reporting text for the selector."""

    if not isinstance(result, SparseMFPCABandwidthSelectionResult):
        raise TypeError("result must be a SparseMFPCABandwidthSelectionResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")

    eligible = int(np.count_nonzero(result.candidate_summary["eligible"]))
    failed_folds = int(
        np.count_nonzero(result.fold_results["status_code"].to_numpy() != "ok")
    )
    selected = result.selected_bandwidths
    if selected is None:
        selection = "No candidate met the declared valid-fold requirement."
    else:
        selected_id = str(selected["candidate_id"])
        row = result.candidate_summary[
            result.candidate_summary["candidate_id"] == selected_id
        ].iloc[0]
        selection = (
            f"The minimum eligible mean fold loss selected {selected_id} "
            f"(mean bandwidth={float(selected['mean_bandwidth']):.{digits}f}, "
            f"covariance bandwidth={float(selected['covariance_bandwidth']):.{digits}f}, "
            f"mean loss={float(row['mean_loss']):.{digits}f})."
        )

    unit_text = (
        "curves"
        if result.resampling_unit == "curve"
        else f"groups from metadata column {result.group_column!r}"
    )
    return (
        f"Sparse planar MFPCA bandwidth selection evaluated "
        f"{len(result.candidates)} declared mean/covariance candidate(s) using "
        f"{result.n_splits}-fold cross-validation over {unit_text}. Population "
        f"mean and full joint latent covariance surfaces were refitted from "
        f"training curves only. Held-out curves were scored by Gaussian negative "
        f"log predictive density from the full fitted joint covariance plus the "
        f"fixed declared 2x2 measurement-error covariance, normalised per scalar "
        f"planar observation and then averaged equally across curves. Joint-PACE "
        f"scores were not used for selection. {eligible} candidate(s) were "
        f"eligible and {failed_folds} candidate-fold failure(s) were retained. "
        f"{selection} Selected values are not applied automatically to "
        f"fit_sparse_mfpca(); they must be supplied explicitly."
    )
