"""Leakage-aware FPCA component selection by held-out reconstruction."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

from .fpca import fit_fpca, fit_mfpca, reconstruct_fpca, transform_fpca
from .types import FPCACrossValidationResult, TrajectorySet
from .validation import validate_trajectory_set


def _candidate_counts(candidate_components: Sequence[int]) -> tuple[int, ...]:
    raw = tuple(candidate_components)
    if not raw:
        raise ValueError("candidate_components must contain at least one component count")
    if any(isinstance(k, bool) or not isinstance(k, (int, np.integer)) for k in raw):
        raise TypeError("candidate_components must contain integers")
    counts = tuple(sorted(set(int(k) for k in raw)))
    if counts[0] < 1:
        raise ValueError("candidate component counts must be positive")
    return counts


def _fit(trajectories: TrajectorySet, *, n_components: int, scaling: str):
    if trajectories.n_dimensions > 1:
        return fit_mfpca(
            trajectories,
            n_components=n_components,
            scaling=scaling,
        )
    return fit_fpca(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )


def _integrated_rmse(
    values: np.ndarray,
    reconstructed: np.ndarray,
    weights: np.ndarray,
) -> np.ndarray:
    error = reconstructed - values
    mse = np.sum(
        error**2 * weights[None, :, None],
        axis=(1, 2),
    ) / (weights.sum() * values.shape[2])
    return np.sqrt(mse)


def cross_validate_fpca_reconstruction(
    trajectories: TrajectorySet,
    *,
    candidate_components: Sequence[int] = (1, 2, 3, 4, 5),
    n_splits: int = 5,
    scaling: str = "none",
    cv_unit: str = "curve",
    group_column: str | None = None,
    shuffle: bool = True,
    random_state: int | None = 0,
) -> FPCACrossValidationResult:
    """Evaluate candidate FPC counts by held-out reconstruction error.

    FPCA is refitted inside every training fold. With cv_unit="group", every
    curve sharing group_column is held out together so repeated measurements
    from the same participant or other grouping unit cannot leak into both
    train and test folds.

    The function returns diagnostics only. It never chooses a component count
    unless select_fpca_components_cv() is called explicitly.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    counts = _candidate_counts(candidate_components)

    if isinstance(n_splits, bool) or not isinstance(n_splits, int) or n_splits < 2:
        raise ValueError("n_splits must be an integer >= 2")
    if cv_unit not in {"curve", "group"}:
        raise ValueError("cv_unit must be 'curve' or 'group'")

    indices = np.arange(trajectories.n_curves)
    if cv_unit == "curve":
        if n_splits > trajectories.n_curves:
            raise ValueError("n_splits cannot exceed number of trajectories")
        splitter = KFold(
            n_splits=n_splits,
            shuffle=shuffle,
            random_state=random_state if shuffle else None,
        )
        split_iter = splitter.split(indices)
        groups = None
    else:
        if group_column is None:
            raise ValueError("group_column is required for group cross-validation")
        if group_column not in trajectories.metadata.columns:
            raise ValueError(f"metadata does not contain group column {group_column!r}")
        if trajectories.metadata[group_column].isna().any():
            raise ValueError("group_column contains missing values")
        groups = trajectories.metadata[group_column].astype(str).to_numpy()
        n_groups = len(pd.unique(groups))
        if n_splits > n_groups:
            raise ValueError("n_splits cannot exceed number of unique groups")
        splitter = GroupKFold(n_splits=n_splits)
        split_iter = splitter.split(indices, groups=groups)

    fold_rows: list[dict[str, int | float]] = []
    assignment_rows: list[dict[str, int | str]] = []

    for fold, (train_idx, test_idx) in enumerate(split_iter):
        max_train_components = min(
            len(train_idx) - 1,
            trajectories.n_time * trajectories.n_dimensions,
        )
        if counts[-1] > max_train_components:
            raise ValueError(
                f"candidate component count {counts[-1]} exceeds training-fold "
                f"maximum {max_train_components}; reduce candidate_components "
                "or n_splits"
            )

        train = trajectories.subset(train_idx)
        test = trajectories.subset(test_idx)
        fit = _fit(
            train,
            n_components=counts[-1],
            scaling=scaling,
        )
        test_scores = transform_fpca(fit, test)

        for n_components in counts:
            reconstructed = reconstruct_fpca(
                fit,
                scores=test_scores,
                n_components=n_components,
            )
            rmse = _integrated_rmse(
                test.values,
                reconstructed,
                fit.weights,
            )
            fold_rows.append(
                {
                    "fold": fold,
                    "n_components": n_components,
                    "mean_integrated_rmse": float(np.mean(rmse)),
                    "median_integrated_rmse": float(np.median(rmse)),
                    "n_train_curves": int(len(train_idx)),
                    "n_test_curves": int(len(test_idx)),
                }
            )

        for index in test_idx:
            row: dict[str, int | str] = {
                "curve_id": trajectories.curve_ids[index],
                "fold": fold,
            }
            if groups is not None:
                row["group"] = str(groups[index])
            assignment_rows.append(row)

    return FPCACrossValidationResult(
        fold_errors=pd.DataFrame(fold_rows),
        assignments=pd.DataFrame(assignment_rows),
        component_counts=counts,
        cv_unit=cv_unit,
        n_splits=n_splits,
        group_column=group_column if cv_unit == "group" else None,
        scaling=scaling,
        random_state=random_state if cv_unit == "curve" and shuffle else None,
        provenance={
            "method": "heldout_reconstruction_cv",
            "fit_inside_fold": True,
            "shuffle": bool(shuffle) if cv_unit == "curve" else False,
            "group_leakage_prevented": cv_unit == "group",
        },
    )


def summarise_fpca_cross_validation(
    result: FPCACrossValidationResult,
) -> pd.DataFrame:
    """Aggregate fold-level held-out reconstruction errors."""

    grouped = result.fold_errors.groupby(
        "n_components",
        sort=True,
    )["mean_integrated_rmse"]
    summary = grouped.agg(
        [
            ("mean_rmse", "mean"),
            ("sd_rmse", "std"),
            ("n_folds", "count"),
        ]
    ).reset_index()
    summary["sd_rmse"] = summary["sd_rmse"].fillna(0.0)
    summary["se_rmse"] = summary["sd_rmse"] / np.sqrt(summary["n_folds"])
    return summary


def select_fpca_components_cv(
    result: FPCACrossValidationResult,
    *,
    rule: str = "minimum",
) -> int:
    """Select a component count using an explicit reconstruction-CV rule.

    "minimum" selects the component count with the smallest mean fold RMSE.

    "one_se" selects the smallest component count whose mean RMSE is within one
    standard error of the minimum-RMSE candidate. This is a parsimony heuristic
    rather than an inferential guarantee.
    """

    if rule not in {"minimum", "one_se"}:
        raise ValueError("rule must be 'minimum' or 'one_se'")

    summary = summarise_fpca_cross_validation(result)
    best_index = int(summary["mean_rmse"].idxmin())
    best = summary.loc[best_index]

    if rule == "minimum":
        return int(best["n_components"])

    cutoff = float(best["mean_rmse"] + best["se_rmse"])
    eligible = summary[summary["mean_rmse"] <= cutoff]
    return int(eligible["n_components"].min())
