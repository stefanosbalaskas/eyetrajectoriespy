"""Audited bandwidth selection for native univariate sparse FPCA.

The selector is deliberately separate from :func:`fit_sparse_fpca`.  It refits
population objects inside curve/group training folds and evaluates whole
held-out curves under the fitted Gaussian observation model.  No validation
observation contributes to training-fold smoothing or noise estimation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import product
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

from ._sparse_native import (
    SparseNativeError,
    evaluate_fitted_covariance,
    evaluate_fitted_function,
)
from .sparse_native import fit_sparse_fpca
from .types import IrregularTrajectorySet


_CRITERION = "mean_curve_gaussian_nll"
_METHOD = "group_aware_training_fold_sparse_population_cv"


@dataclass(frozen=True)
class SparseFPCABandwidthSelectionResult:
    """Auditable cross-validation result for sparse-FPCA bandwidth tuples."""

    assignments: pd.DataFrame
    fold_results: pd.DataFrame
    curve_losses: pd.DataFrame
    candidate_summary: pd.DataFrame
    candidates: pd.DataFrame
    selected_bandwidths: Mapping[str, float | None] | None
    criterion: str
    resampling_unit: str
    n_splits: int
    group_column: str | None
    min_valid_folds: int
    status_code: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


def _positive_grid(values: Sequence[float], *, name: str) -> tuple[float, ...]:
    raw = tuple(values)
    if not raw:
        raise ValueError(f"{name} must contain at least one candidate")
    converted: list[float] = []
    for value in raw:
        if isinstance(value, bool):
            raise TypeError(f"{name} must contain numeric bandwidths")
        number = float(value)
        if not np.isfinite(number) or number <= 0:
            raise ValueError(f"{name} must contain finite positive bandwidths")
        converted.append(number)
    return tuple(sorted(set(converted)))


def _validate_evaluation_grid(evaluation_grid: np.ndarray) -> np.ndarray:
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


def _validate_selector_inputs(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    evaluation_grid: np.ndarray,
    noise_variance_method: str,
    measurement_error_variance: float | None,
    noise_support: tuple[float, float] | None,
    analysis_support_action: str,
    n_splits: int,
    resampling_unit: str,
    group_column: str | None,
    min_valid_folds: int | None,
    predictive_condition_limit: float,
    failure_action: str,
) -> tuple[np.ndarray, int]:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    dimension_index = trajectories.dimension_names.index(dimension)
    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        selected = np.asarray(values[:, dimension_index], dtype=float)
        if not np.all(np.isfinite(selected)):
            raise SparseNativeError(
                "nonfinite_sparse_observation",
                "bandwidth selection requires finite observed sparse samples",
                details={"curve_id": str(curve_id), "dimension": dimension},
            )

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
                "validation/training observations lie outside declared support",
                details={
                    "analysis_support": [float(grid[0]), float(grid[-1])],
                    "curve_ids": outside,
                },
            )

    if noise_variance_method not in {"diagonal_difference", "fixed"}:
        raise ValueError(
            "noise_variance_method must be 'diagonal_difference' or 'fixed'"
        )
    if noise_variance_method == "diagonal_difference":
        if measurement_error_variance is not None:
            raise ValueError(
                "measurement_error_variance must be None for diagonal_difference"
            )
        if noise_support is None:
            raise ValueError(
                "noise_support is required for diagonal_difference bandwidth selection"
            )
    else:
        if measurement_error_variance is None:
            raise ValueError(
                "measurement_error_variance is required when noise_variance_method='fixed'"
            )
        variance = float(measurement_error_variance)
        if not np.isfinite(variance) or variance < 0:
            raise ValueError(
                "measurement_error_variance must be finite and non-negative"
            )
        if noise_support is not None:
            raise ValueError(
                "noise_support must be None when noise_variance_method='fixed'"
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
    else:
        if (
            isinstance(min_valid_folds, bool)
            or not isinstance(min_valid_folds, int)
            or min_valid_folds < 1
            or min_valid_folds > n_splits
        ):
            raise ValueError("min_valid_folds must be an integer in [1, n_splits]")
        required_folds = min_valid_folds

    limit = float(predictive_condition_limit)
    if not np.isfinite(limit) or limit <= 1:
        raise ValueError("predictive_condition_limit must be finite and > 1")
    if failure_action not in {"retain", "error"}:
        raise ValueError("failure_action must be 'retain' or 'error'")
    return grid, required_folds


def _make_folds(
    trajectories: IrregularTrajectorySet,
    *,
    n_splits: int,
    resampling_unit: str,
    group_column: str | None,
    shuffle: bool,
    random_state: int | None,
) -> tuple[tuple[tuple[np.ndarray, np.ndarray], ...], pd.DataFrame, np.ndarray | None]:
    indices = np.arange(trajectories.n_curves)
    groups: np.ndarray | None = None
    if resampling_unit == "curve":
        splitter = KFold(
            n_splits=n_splits,
            shuffle=shuffle,
            random_state=random_state if shuffle else None,
        )
        raw_splits = splitter.split(indices)
    else:
        groups = trajectories.metadata[group_column].astype(str).to_numpy()
        splitter = GroupKFold(n_splits=n_splits)
        raw_splits = splitter.split(indices, groups=groups)

    splits: list[tuple[np.ndarray, np.ndarray]] = []
    assignment_rows: list[dict[str, Any]] = []
    for fold, (train_idx, validation_idx) in enumerate(raw_splits):
        train_idx = np.asarray(train_idx, dtype=int)
        validation_idx = np.asarray(validation_idx, dtype=int)
        if np.intersect1d(train_idx, validation_idx).size:
            raise RuntimeError("cross-validation split contains curve leakage")
        if groups is not None:
            train_groups = set(groups[train_idx].tolist())
            validation_groups = set(groups[validation_idx].tolist())
            if train_groups.intersection(validation_groups):
                raise RuntimeError("group cross-validation split contains group leakage")
        splits.append((train_idx, validation_idx))
        for index in validation_idx:
            row: dict[str, Any] = {
                "curve_id": str(trajectories.curve_ids[index]),
                "fold": int(fold),
            }
            if groups is not None:
                row["group"] = str(groups[index])
            assignment_rows.append(row)
    return tuple(splits), pd.DataFrame(assignment_rows), groups


def _candidate_table(
    mean_bandwidths: tuple[float, ...],
    covariance_bandwidths: tuple[float, ...],
    noise_bandwidths: tuple[float, ...] | None,
) -> pd.DataFrame:
    noise_values: tuple[float | None, ...]
    if noise_bandwidths is None:
        noise_values = (None,)
    else:
        noise_values = tuple(noise_bandwidths)
    rows: list[dict[str, Any]] = []
    for index, (mean_bw, covariance_bw, noise_bw) in enumerate(
        product(mean_bandwidths, covariance_bandwidths, noise_values)
    ):
        rows.append(
            {
                "candidate_id": f"candidate_{index:04d}",
                "mean_bandwidth": float(mean_bw),
                "covariance_bandwidth": float(covariance_bw),
                "noise_bandwidth": None if noise_bw is None else float(noise_bw),
            }
        )
    return pd.DataFrame(rows)


def _effective_validation_curve(
    time: np.ndarray,
    observed: np.ndarray,
    grid: np.ndarray,
    *,
    action: str,
) -> tuple[np.ndarray, np.ndarray, int]:
    time = np.asarray(time, dtype=float)
    observed = np.asarray(observed, dtype=float)
    mask = (time >= grid[0]) & (time <= grid[-1])
    outside = int(np.count_nonzero(~mask))
    if action == "error" and outside:
        raise SparseNativeError(
            "observations_outside_analysis_support",
            "held-out curve has observations outside declared support",
            details={"outside_observation_count": outside},
        )
    if action == "restrict":
        time = time[mask]
        observed = observed[mask]
    if time.size == 0:
        raise SparseNativeError(
            "no_validation_observations_on_support",
            "held-out curve has no observations on declared support",
        )
    return time, observed, outside


def _curve_gaussian_nll(
    fit,
    time: np.ndarray,
    observed: np.ndarray,
    *,
    predictive_condition_limit: float,
) -> tuple[float, float, float, float]:
    if fit.evaluation_grid is None or fit.mean is None or fit.covariance is None:
        raise ValueError("training-fold sparse fit does not retain population objects")
    if fit.noise_variance is None:
        raise ValueError("training-fold sparse fit does not retain noise variance")

    mean = evaluate_fitted_function(fit.evaluation_grid, fit.mean, time)
    latent_covariance = evaluate_fitted_covariance(
        fit.evaluation_grid,
        fit.covariance,
        time,
    )
    sigma = latent_covariance + float(fit.noise_variance) * np.eye(time.size)
    sigma = 0.5 * (sigma + sigma.T)
    eigenvalues = np.linalg.eigvalsh(sigma)
    minimum = float(np.min(eigenvalues))
    maximum = float(np.max(eigenvalues))
    condition = np.inf if minimum <= 0 else maximum / minimum
    if minimum <= 0:
        raise SparseNativeError(
            "predictive_covariance_not_positive_definite",
            "held-out predictive covariance is not positive definite",
            details={"minimum_eigenvalue": minimum, "maximum_eigenvalue": maximum},
        )
    if condition > predictive_condition_limit:
        raise SparseNativeError(
            "predictive_covariance_ill_conditioned",
            "held-out predictive covariance exceeds the condition-number limit",
            details={
                "condition_number": float(condition),
                "condition_limit": float(predictive_condition_limit),
            },
        )

    residual = observed - mean
    solved = np.linalg.solve(sigma, residual)
    quadratic = float(residual @ solved)
    log_determinant = float(np.sum(np.log(eigenvalues)))
    nll = 0.5 * (
        log_determinant + quadratic + time.size * np.log(2.0 * np.pi)
    )
    return float(nll / time.size), float(condition), minimum, maximum


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
        losses = valid["mean_curve_gaussian_nll"].to_numpy(dtype=float)
        mean_loss = float(np.mean(losses)) if losses.size else np.nan
        sd_loss = float(np.std(losses, ddof=1)) if losses.size > 1 else 0.0
        se_loss = float(sd_loss / np.sqrt(losses.size)) if losses.size else np.nan
        row = dict(candidate)
        row.update(
            {
                "mean_loss": mean_loss,
                "sd_loss": sd_loss,
                "se_loss": se_loss,
                "n_valid_folds": int(losses.size),
                "n_failed_folds": int(len(subset) - losses.size),
                "eligible": bool(losses.size >= min_valid_folds),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _select_minimum_candidate(
    summary: pd.DataFrame,
) -> Mapping[str, float | None] | None:
    eligible = summary[summary["eligible"] & np.isfinite(summary["mean_loss"])].copy()
    if eligible.empty:
        return None
    eligible["noise_bandwidth_sort"] = eligible["noise_bandwidth"].fillna(-np.inf)
    eligible = eligible.sort_values(
        [
            "mean_loss",
            "mean_bandwidth",
            "covariance_bandwidth",
            "noise_bandwidth_sort",
            "candidate_id",
        ],
        ascending=[True, False, False, False, True],
        kind="mergesort",
    )
    best = eligible.iloc[0]
    noise = best["noise_bandwidth"]
    return {
        "candidate_id": str(best["candidate_id"]),
        "mean_bandwidth": float(best["mean_bandwidth"]),
        "covariance_bandwidth": float(best["covariance_bandwidth"]),
        "noise_bandwidth": None if pd.isna(noise) else float(noise),
    }


def select_sparse_fpca_bandwidths(
    trajectories: IrregularTrajectorySet,
    *,
    dimension: str,
    evaluation_grid: np.ndarray,
    mean_bandwidths: Sequence[float],
    covariance_bandwidths: Sequence[float],
    noise_bandwidths: Sequence[float] | None = None,
    noise_support: tuple[float, float] | None = None,
    analysis_support_action: str = "error",
    noise_variance_method: str = "diagonal_difference",
    measurement_error_variance: float | None = None,
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
    positive_eigen_tolerance: float = 1e-10,
    mean_smoother: str = "local_linear",
    covariance_smoother: str = "local_linear",
    kernel: str = "epanechnikov",
    mean_min_local_points: int = 3,
    covariance_min_local_pairs: int = 6,
    noise_min_local_points: int = 3,
) -> SparseFPCABandwidthSelectionResult:
    """Select sparse-FPCA smoothing bandwidths by audited held-out likelihood.

    Each candidate is fitted from scratch inside every training fold.  The loss
    for a held-out curve is its per-observation Gaussian negative log predictive
    density under the training-only fitted mean, full latent covariance, and
    measurement-error variance.  Fold loss is the mean of the held-out curve
    losses, so curves rather than individual observations are the primary
    validation unit.

    This selector never changes :func:`fit_sparse_fpca` defaults and never
    invokes automatic tuning from inside the fitter.  The selected numeric
    bandwidths must be passed explicitly to a subsequent fit.
    """

    mean_grid = _positive_grid(mean_bandwidths, name="mean_bandwidths")
    covariance_grid = _positive_grid(
        covariance_bandwidths,
        name="covariance_bandwidths",
    )
    if noise_variance_method == "diagonal_difference":
        if noise_bandwidths is None:
            raise ValueError(
                "noise_bandwidths is required for diagonal_difference selection"
            )
        noise_grid = _positive_grid(noise_bandwidths, name="noise_bandwidths")
    else:
        if noise_bandwidths is not None:
            raise ValueError(
                "noise_bandwidths must be None when noise_variance_method='fixed'"
            )
        noise_grid = None

    grid, required_folds = _validate_selector_inputs(
        trajectories,
        dimension=dimension,
        evaluation_grid=evaluation_grid,
        noise_variance_method=noise_variance_method,
        measurement_error_variance=measurement_error_variance,
        noise_support=noise_support,
        analysis_support_action=analysis_support_action,
        n_splits=n_splits,
        resampling_unit=resampling_unit,
        group_column=group_column,
        min_valid_folds=min_valid_folds,
        predictive_condition_limit=predictive_condition_limit,
        failure_action=failure_action,
    )
    dimension_index = trajectories.dimension_names.index(dimension)
    splits, assignments, groups = _make_folds(
        trajectories,
        n_splits=n_splits,
        resampling_unit=resampling_unit,
        group_column=group_column,
        shuffle=shuffle,
        random_state=random_state,
    )
    candidates = _candidate_table(mean_grid, covariance_grid, noise_grid)

    fold_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []

    for candidate in candidates.to_dict(orient="records"):
        candidate_id = str(candidate["candidate_id"])
        mean_bandwidth = float(candidate["mean_bandwidth"])
        covariance_bandwidth = float(candidate["covariance_bandwidth"])
        raw_noise_bandwidth = candidate["noise_bandwidth"]
        noise_bandwidth = (
            None if pd.isna(raw_noise_bandwidth) else float(raw_noise_bandwidth)
        )

        for fold, (train_idx, validation_idx) in enumerate(splits):
            train = trajectories.subset(train_idx)
            validation = trajectories.subset(validation_idx)
            base_row: dict[str, Any] = {
                "candidate_id": candidate_id,
                "fold": int(fold),
                "mean_bandwidth": mean_bandwidth,
                "covariance_bandwidth": covariance_bandwidth,
                "noise_bandwidth": noise_bandwidth,
                "n_train_curves": int(train.n_curves),
                "n_validation_curves": int(validation.n_curves),
                "n_train_observations": int(np.sum(train.sample_counts)),
                "n_validation_observations": int(np.sum(validation.sample_counts)),
            }
            try:
                fit = fit_sparse_fpca(
                    train,
                    dimension=dimension,
                    n_components=1,
                    evaluation_grid=grid,
                    mean_bandwidth=mean_bandwidth,
                    covariance_bandwidth=covariance_bandwidth,
                    noise_bandwidth=noise_bandwidth,
                    noise_support=noise_support,
                    analysis_support_action=analysis_support_action,
                    mean_smoother=mean_smoother,
                    covariance_smoother=covariance_smoother,
                    kernel=kernel,
                    noise_variance_method=noise_variance_method,
                    measurement_error_variance=measurement_error_variance,
                    psd_action=psd_action,
                    psd_tolerance=psd_tolerance,
                    positive_eigen_tolerance=positive_eigen_tolerance,
                    score_failure_action="retain_nan",
                    mean_min_local_points=mean_min_local_points,
                    covariance_min_local_pairs=covariance_min_local_pairs,
                    noise_min_local_points=noise_min_local_points,
                )
            except (SparseNativeError, ValueError, np.linalg.LinAlgError) as exc:
                code, message = _failure_details(exc)
                fold_rows.append(
                    {
                        **base_row,
                        "status_code": "fit_failure",
                        "failure_code": code,
                        "failure_message": message,
                        "mean_curve_gaussian_nll": np.nan,
                        "median_curve_gaussian_nll": np.nan,
                        "n_evaluated_curves": 0,
                        "n_evaluated_observations": 0,
                        "fitted_noise_variance": np.nan,
                    }
                )
                if failure_action == "error":
                    raise
                continue

            validation_losses: list[float] = []
            validation_observations = 0
            validation_failed = False
            first_validation_failure: tuple[str, str] | None = None
            for curve_id, time, values in zip(
                validation.curve_ids,
                validation.time,
                validation.values,
                strict=True,
            ):
                observed = np.asarray(values[:, dimension_index], dtype=float)
                try:
                    effective_time, effective_observed, outside = (
                        _effective_validation_curve(
                            time,
                            observed,
                            grid,
                            action=analysis_support_action,
                        )
                    )
                    loss, condition, minimum, maximum = _curve_gaussian_nll(
                        fit,
                        effective_time,
                        effective_observed,
                        predictive_condition_limit=predictive_condition_limit,
                    )
                    validation_losses.append(loss)
                    validation_observations += int(effective_time.size)
                    curve_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "fold": int(fold),
                            "curve_id": str(curve_id),
                            "status_code": "ok",
                            "failure_code": None,
                            "failure_message": None,
                            "gaussian_nll_per_observation": float(loss),
                            "n_evaluated_observations": int(effective_time.size),
                            "outside_support_observations": int(outside),
                            "predictive_condition_number": float(condition),
                            "predictive_minimum_eigenvalue": float(minimum),
                            "predictive_maximum_eigenvalue": float(maximum),
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
                            "gaussian_nll_per_observation": np.nan,
                            "n_evaluated_observations": 0,
                            "outside_support_observations": np.nan,
                            "predictive_condition_number": np.nan,
                            "predictive_minimum_eigenvalue": np.nan,
                            "predictive_maximum_eigenvalue": np.nan,
                        }
                    )
                    if failure_action == "error":
                        raise

            if validation_failed:
                code, message = first_validation_failure or (
                    "validation_failure",
                    "held-out validation failed",
                )
                fold_rows.append(
                    {
                        **base_row,
                        "status_code": "validation_failure",
                        "failure_code": code,
                        "failure_message": message,
                        "mean_curve_gaussian_nll": np.nan,
                        "median_curve_gaussian_nll": np.nan,
                        "n_evaluated_curves": int(len(validation_losses)),
                        "n_evaluated_observations": int(validation_observations),
                        "fitted_noise_variance": float(fit.noise_variance),
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
                    "mean_curve_gaussian_nll": float(np.mean(losses)),
                    "median_curve_gaussian_nll": float(np.median(losses)),
                    "n_evaluated_curves": int(losses.size),
                    "n_evaluated_observations": int(validation_observations),
                    "fitted_noise_variance": float(fit.noise_variance),
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

    provenance = {
        "method": _METHOD,
        "criterion": _CRITERION,
        "criterion_formula": (
            "curve mean of 0.5*(logdet(Sigma_i)+r_i^T Sigma_i^-1 r_i+"
            "m_i*log(2*pi))/m_i; fold mean weights held-out curves equally"
        ),
        "validation_distribution": (
            "Gaussian observation model from training-only fitted mean, full latent "
            "covariance, and measurement-error variance"
        ),
        "fit_inside_fold": True,
        "validation_observations_used_for_training": False,
        "validation_observations_used_for_pace_scoring": False,
        "full_fitted_covariance_used_for_validation": True,
        "score_ridge_included_in_validation_covariance": False,
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
        "candidate_order": "sorted_unique_cartesian_product",
        "selection_rule": "minimum_mean_fold_loss",
        "tie_break_rule": (
            "minimum loss, then larger mean/covariance/noise bandwidths "
            "lexicographically, then candidate_id"
        ),
        "one_se_rule_implemented": False,
        "one_se_reason": (
            "no predeclared scalar simplicity ordering for a multidimensional "
            "bandwidth tuple"
        ),
        "automatic_fit_bandwidth_selection_performed": False,
        "selected_values_must_be_passed_explicitly_to_fit_sparse_fpca": True,
        "evaluation_grid": grid.tolist(),
        "analysis_support_action": analysis_support_action,
        "noise_variance_method": noise_variance_method,
        "noise_support": None if noise_support is None else list(noise_support),
        "measurement_error_variance": (
            None
            if measurement_error_variance is None
            else float(measurement_error_variance)
        ),
        "psd_action": psd_action,
        "psd_tolerance": float(psd_tolerance),
        "positive_eigen_tolerance": float(positive_eigen_tolerance),
        "mean_smoother": mean_smoother,
        "covariance_smoother": covariance_smoother,
        "kernel": kernel,
        "mean_min_local_points": int(mean_min_local_points),
        "covariance_min_local_pairs": int(covariance_min_local_pairs),
        "noise_min_local_points": int(noise_min_local_points),
        "candidate_count": int(len(candidates)),
        "fold_assignment_count": int(len(assignments)),
        "training_population_fit_n_components": 1,
        "training_score_failure_action": "retain_nan",
    }
    if groups is not None:
        provenance["group_count"] = int(len(pd.unique(groups)))

    return SparseFPCABandwidthSelectionResult(
        assignments=assignments,
        fold_results=fold_results,
        curve_losses=curve_losses,
        candidate_summary=summary,
        candidates=candidates,
        selected_bandwidths=selected,
        criterion=_CRITERION,
        resampling_unit=resampling_unit,
        n_splits=n_splits,
        group_column=group_column if resampling_unit == "group" else None,
        min_valid_folds=required_folds,
        status_code=status_code,
        provenance=provenance,
    )


def sparse_fpca_bandwidth_selection_reporting_text(
    result: SparseFPCABandwidthSelectionResult,
) -> str:
    """Return compact manuscript-ready wording for an audited selector result."""

    if not isinstance(result, SparseFPCABandwidthSelectionResult):
        raise TypeError("result must be a SparseFPCABandwidthSelectionResult")
    n_candidates = len(result.candidates)
    failures = int(np.count_nonzero(result.fold_results["status_code"] != "ok"))
    unit = (
        f"grouped by {result.group_column!r}"
        if result.resampling_unit == "group"
        else "at the curve level"
    )
    prefix = (
        f"Sparse-FPCA smoothing bandwidths were evaluated using {result.n_splits}-fold "
        f"cross-validation {unit}. Population mean, covariance, and measurement-noise "
        "objects were refitted using training curves only. The prespecified criterion "
        "was mean held-out-curve Gaussian negative log predictive density, using the "
        "full fitted latent covariance plus measurement-error variance; held-out "
        "observations were not used for population fitting or PACE score estimation. "
        f"The audit evaluated {n_candidates} bandwidth candidate(s) and retained "
        f"{failures} failed candidate-fold evaluation(s)."
    )
    if result.selected_bandwidths is None:
        return prefix + " No candidate satisfied the declared valid-fold requirement."
    selected = result.selected_bandwidths
    text = (
        prefix
        + " The minimum mean fold loss selected mean bandwidth "
        + f"{selected['mean_bandwidth']:g} and covariance bandwidth "
        + f"{selected['covariance_bandwidth']:g}"
    )
    if selected["noise_bandwidth"] is not None:
        text += f", with noise bandwidth {selected['noise_bandwidth']:g}"
    return text + ". The selected numeric values were not applied automatically to the fitter."
