"""Outcome-tuned FPCA regression selection with leakage-aware cross-validation."""

from __future__ import annotations

from collections.abc import Sequence
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import GroupKFold, KFold
from statsmodels.tools.sm_exceptions import PerfectSeparationError, PerfectSeparationWarning

from .fpca import transform_fpca
from .selection import _candidate_counts, _fit
from .types import FPCANestedRegressionCVResult, FPCARegressionCVResult, TrajectorySet
from .validation import validate_trajectory_set


def _validate_outcome(
    outcome: np.ndarray | pd.Series,
    *,
    n_curves: int,
    family: str,
) -> np.ndarray:
    values = np.asarray(outcome, dtype=float)
    if values.shape != (n_curves,):
        raise ValueError("outcome must contain exactly one value per trajectory")
    if not np.all(np.isfinite(values)):
        raise ValueError("outcome contains non-finite values; handle them explicitly")
    if family not in {"gaussian", "binomial"}:
        raise ValueError("family must be 'gaussian' or 'binomial'")
    if family == "binomial" and not set(np.unique(values)) <= {0.0, 1.0}:
        raise ValueError("binomial outcome must contain only 0/1 values")
    return values


def _validate_covariates(
    covariates: pd.DataFrame | None,
    *,
    n_curves: int,
) -> pd.DataFrame | None:
    if covariates is None:
        return None
    if not isinstance(covariates, pd.DataFrame):
        raise TypeError("covariates must be a pandas DataFrame or None")
    if len(covariates) != n_curves:
        raise ValueError("covariates must contain exactly one row per trajectory")
    if not covariates.columns.is_unique:
        raise ValueError("covariate column names must be unique")
    columns = [str(column) for column in covariates.columns]
    if "const" in columns or any(
        column.startswith("FPC") and column[3:].isdigit()
        for column in columns
    ):
        raise ValueError("covariate names cannot collide with 'const' or FPC score columns")
    try:
        values = covariates.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise TypeError("covariates must be numeric") from exc
    if not np.all(np.isfinite(values)):
        raise ValueError("covariates contain non-finite values")
    result = covariates.reset_index(drop=True).copy()
    result.columns = columns
    return result


def _resolve_loss(family: str, loss: str | None) -> str:
    if family == "gaussian":
        resolved = "rmse" if loss is None else loss
        if resolved not in {"rmse", "mae"}:
            raise ValueError("gaussian loss must be 'rmse' or 'mae'")
        return resolved
    if family == "binomial":
        resolved = "log_loss" if loss is None else loss
        if resolved not in {"log_loss", "brier"}:
            raise ValueError("binomial loss must be 'log_loss' or 'brier'")
        return resolved
    raise ValueError("family must be 'gaussian' or 'binomial'")


def _loss_value(
    observed: np.ndarray,
    prediction: np.ndarray,
    *,
    family: str,
    loss: str,
) -> float:
    if family == "gaussian":
        if loss == "rmse":
            return float(np.sqrt(np.mean((observed - prediction) ** 2)))
        return float(np.mean(np.abs(observed - prediction)))

    if loss == "brier":
        return float(np.mean((observed - prediction) ** 2))

    eps = np.finfo(float).eps
    probability = np.clip(prediction, eps, 1.0 - eps)
    return float(
        -np.mean(
            observed * np.log(probability)
            + (1.0 - observed) * np.log(1.0 - probability)
        )
    )


def _design_matrix(
    scores: np.ndarray,
    *,
    n_components: int,
    covariates: pd.DataFrame | None,
) -> pd.DataFrame:
    design = pd.DataFrame(
        scores[:, :n_components],
        columns=[f"FPC{index + 1}" for index in range(n_components)],
    )
    if covariates is not None:
        design = pd.concat(
            [design.reset_index(drop=True), covariates.reset_index(drop=True)],
            axis=1,
        )
    design = sm.add_constant(design, has_constant="add")
    matrix = np.asarray(design, dtype=float)
    if np.linalg.matrix_rank(matrix) < matrix.shape[1]:
        raise ValueError(
            "regression design matrix is rank deficient; remove redundant "
            "components/covariates before predictive FPCA regression"
        )
    return design


def _test_design_matrix(
    scores: np.ndarray,
    *,
    n_components: int,
    covariates: pd.DataFrame | None,
) -> pd.DataFrame:
    design = pd.DataFrame(
        scores[:, :n_components],
        columns=[f"FPC{index + 1}" for index in range(n_components)],
    )
    if covariates is not None:
        design = pd.concat(
            [design.reset_index(drop=True), covariates.reset_index(drop=True)],
            axis=1,
        )
    return sm.add_constant(design, has_constant="add")


def _fit_predict_regression(
    outcome_train: np.ndarray,
    train_scores: np.ndarray,
    test_scores: np.ndarray,
    *,
    n_components: int,
    family: str,
    covariates_train: pd.DataFrame | None,
    covariates_test: pd.DataFrame | None,
) -> np.ndarray:
    design_train = _design_matrix(
        train_scores,
        n_components=n_components,
        covariates=covariates_train,
    )
    design_test = _test_design_matrix(
        test_scores,
        n_components=n_components,
        covariates=covariates_test,
    )

    if family == "gaussian":
        model = sm.OLS(outcome_train, design_train).fit()
        prediction = np.asarray(model.predict(design_test), dtype=float)
    else:
        if len(np.unique(outcome_train)) < 2:
            raise ValueError(
                "each binomial training fold must contain both outcome classes"
            )
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model = sm.GLM(
                    outcome_train,
                    design_train,
                    family=sm.families.Binomial(),
                ).fit()
        except PerfectSeparationError as exc:
            raise RuntimeError(
                "binomial FPCA regression encountered perfect separation"
            ) from exc
        if any(
            issubclass(warning.category, PerfectSeparationWarning)
            for warning in caught
        ):
            raise RuntimeError(
                "binomial FPCA regression encountered perfect separation"
            )
        if not bool(getattr(model, "converged", True)):
            raise RuntimeError("binomial FPCA regression did not converge")
        prediction = np.asarray(model.predict(design_test), dtype=float)
        if not np.all(np.isfinite(prediction)) or np.any(
            (prediction < 0.0) | (prediction > 1.0)
        ):
            raise RuntimeError(
                "binomial FPCA regression returned invalid probabilities"
            )

    if not np.all(np.isfinite(prediction)):
        raise RuntimeError("FPCA regression returned non-finite predictions")
    return prediction


def _make_splits(
    trajectories: TrajectorySet,
    *,
    n_splits: int,
    cv_unit: str,
    group_column: str | None,
    shuffle: bool,
    random_state: int | None,
):
    if isinstance(n_splits, bool) or not isinstance(n_splits, (int, np.integer)):
        raise TypeError("n_splits must be an integer")
    n_splits = int(n_splits)
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
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
        return list(splitter.split(indices)), None

    if group_column is None:
        raise ValueError("group_column is required for group cross-validation")
    if group_column not in trajectories.metadata.columns:
        raise ValueError(f"metadata does not contain group column {group_column!r}")
    if trajectories.metadata[group_column].isna().any():
        raise ValueError("group_column contains missing values")
    groups = trajectories.metadata[group_column].astype(str).to_numpy()
    if n_splits > len(pd.unique(groups)):
        raise ValueError("n_splits cannot exceed number of unique groups")
    splitter = GroupKFold(n_splits=n_splits)
    return list(splitter.split(indices, groups=groups)), groups


def cross_validate_fpca_regression(
    trajectories: TrajectorySet,
    outcome: np.ndarray | pd.Series,
    *,
    candidate_components: Sequence[int] = (1, 2, 3, 4, 5),
    family: str = "gaussian",
    loss: str | None = None,
    covariates: pd.DataFrame | None = None,
    n_splits: int = 5,
    scaling: str = "none",
    cv_unit: str = "curve",
    group_column: str | None = None,
    shuffle: bool = True,
    random_state: int | None = 0,
) -> FPCARegressionCVResult:
    """Tune retained FPC count for scalar-outcome prediction.

    FPCA and scalar regression are both fitted inside every training fold.
    Group cross-validation holds all curves from a participant/group together.
    The function tunes an ordinary unsupervised FPCA basis for prediction; it
    does not construct supervised principal components.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    counts = _candidate_counts(candidate_components)
    values = _validate_outcome(
        outcome,
        n_curves=trajectories.n_curves,
        family=family,
    )
    covariate_frame = _validate_covariates(
        covariates,
        n_curves=trajectories.n_curves,
    )
    resolved_loss = _resolve_loss(family, loss)

    splits, groups = _make_splits(
        trajectories,
        n_splits=n_splits,
        cv_unit=cv_unit,
        group_column=group_column,
        shuffle=shuffle,
        random_state=random_state,
    )

    fold_rows = []
    assignment_rows = []
    prediction_rows = []

    for fold, (train_idx, test_idx) in enumerate(splits):
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
        fpca = _fit(
            train,
            n_components=counts[-1],
            scaling=scaling,
        )
        test_scores = transform_fpca(fpca, test)

        covariates_train = (
            None
            if covariate_frame is None
            else covariate_frame.iloc[train_idx].reset_index(drop=True)
        )
        covariates_test = (
            None
            if covariate_frame is None
            else covariate_frame.iloc[test_idx].reset_index(drop=True)
        )

        for n_components in counts:
            prediction = _fit_predict_regression(
                values[train_idx],
                fpca.scores,
                test_scores,
                n_components=n_components,
                family=family,
                covariates_train=covariates_train,
                covariates_test=covariates_test,
            )
            fold_loss = _loss_value(
                values[test_idx],
                prediction,
                family=family,
                loss=resolved_loss,
            )
            fold_rows.append(
                {
                    "fold": fold,
                    "n_components": n_components,
                    "loss": fold_loss,
                    "n_train_curves": int(len(train_idx)),
                    "n_test_curves": int(len(test_idx)),
                }
            )
            for position, index in enumerate(test_idx):
                prediction_rows.append(
                    {
                        "curve_id": trajectories.curve_ids[index],
                        "fold": fold,
                        "n_components": n_components,
                        "observed": float(values[index]),
                        "prediction": float(prediction[position]),
                    }
                )

        for index in test_idx:
            row = {
                "curve_id": trajectories.curve_ids[index],
                "fold": fold,
            }
            if groups is not None:
                row["group"] = str(groups[index])
            assignment_rows.append(row)

    return FPCARegressionCVResult(
        fold_losses=pd.DataFrame(fold_rows),
        assignments=pd.DataFrame(assignment_rows),
        predictions=pd.DataFrame(prediction_rows),
        component_counts=counts,
        family=family,
        loss=resolved_loss,
        cv_unit=cv_unit,
        n_splits=n_splits,
        group_column=group_column if cv_unit == "group" else None,
        scaling=scaling,
        random_state=random_state if cv_unit == "curve" and shuffle else None,
        provenance={
            "method": "outcome_tuned_fpca_regression_cv",
            "fit_fpca_inside_fold": True,
            "fit_regression_inside_fold": True,
            "group_leakage_prevented": cv_unit == "group",
            "covariates": (
                [] if covariate_frame is None else list(covariate_frame.columns)
            ),
            "scientific_warning": (
                "Grouped folds prevent train/test leakage but do not by themselves "
                "model within-group residual dependence or equalize group weights."
            ),
        },
    )


def summarise_fpca_regression_cv(
    result: FPCARegressionCVResult,
) -> pd.DataFrame:
    """Aggregate fold-level predictive loss by candidate FPC count."""

    grouped = result.fold_losses.groupby(
        "n_components",
        sort=True,
    )["loss"]
    summary = grouped.agg(
        [
            ("mean_loss", "mean"),
            ("sd_loss", "std"),
            ("n_folds", "count"),
        ]
    ).reset_index()
    summary["sd_loss"] = summary["sd_loss"].fillna(0.0)
    summary["se_loss"] = summary["sd_loss"] / np.sqrt(summary["n_folds"])
    return summary


def select_fpca_regression_components(
    result: FPCARegressionCVResult,
    *,
    rule: str = "minimum",
) -> int:
    """Choose retained FPC count from predictive CV losses."""

    if rule not in {"minimum", "one_se"}:
        raise ValueError("rule must be 'minimum' or 'one_se'")

    summary = summarise_fpca_regression_cv(result)
    best_index = int(summary["mean_loss"].idxmin())
    best = summary.loc[best_index]

    if rule == "minimum":
        return int(best["n_components"])

    cutoff = float(best["mean_loss"] + best["se_loss"])
    eligible = summary[summary["mean_loss"] <= cutoff]
    return int(eligible["n_components"].min())


def nested_cross_validate_fpca_regression(
    trajectories: TrajectorySet,
    outcome: np.ndarray | pd.Series,
    *,
    candidate_components: Sequence[int] = (1, 2, 3, 4, 5),
    family: str = "gaussian",
    loss: str | None = None,
    covariates: pd.DataFrame | None = None,
    outer_splits: int = 5,
    inner_splits: int = 4,
    selection_rule: str = "minimum",
    scaling: str = "none",
    cv_unit: str = "curve",
    group_column: str | None = None,
    shuffle: bool = True,
    random_state: int | None = 0,
) -> FPCANestedRegressionCVResult:
    """Estimate predictive performance with nested FPC-count selection."""

    validate_trajectory_set(trajectories, require_complete=True)
    counts = _candidate_counts(candidate_components)
    values = _validate_outcome(
        outcome,
        n_curves=trajectories.n_curves,
        family=family,
    )
    covariate_frame = _validate_covariates(
        covariates,
        n_curves=trajectories.n_curves,
    )
    resolved_loss = _resolve_loss(family, loss)
    if selection_rule not in {"minimum", "one_se"}:
        raise ValueError("selection_rule must be 'minimum' or 'one_se'")

    outer, groups = _make_splits(
        trajectories,
        n_splits=outer_splits,
        cv_unit=cv_unit,
        group_column=group_column,
        shuffle=shuffle,
        random_state=random_state,
    )

    outer_rows = []
    inner_rows = []
    prediction_rows = []

    for outer_fold, (train_idx, test_idx) in enumerate(outer):
        train = trajectories.subset(train_idx)
        outcome_train = values[train_idx]
        covariates_train = (
            None
            if covariate_frame is None
            else covariate_frame.iloc[train_idx].reset_index(drop=True)
        )

        inner = cross_validate_fpca_regression(
            train,
            outcome_train,
            candidate_components=counts,
            family=family,
            loss=resolved_loss,
            covariates=covariates_train,
            n_splits=inner_splits,
            scaling=scaling,
            cv_unit=cv_unit,
            group_column=group_column,
            shuffle=shuffle,
            random_state=(
                None if random_state is None else int(random_state) + outer_fold + 1
            ),
        )
        selected = select_fpca_regression_components(
            inner,
            rule=selection_rule,
        )
        inner_summary = summarise_fpca_regression_cv(inner).copy()
        inner_summary.insert(0, "outer_fold", outer_fold)
        inner_rows.append(inner_summary)

        fpca = _fit(
            train,
            n_components=selected,
            scaling=scaling,
        )
        test_scores = transform_fpca(
            fpca,
            trajectories.subset(test_idx),
        )
        covariates_test = (
            None
            if covariate_frame is None
            else covariate_frame.iloc[test_idx].reset_index(drop=True)
        )
        prediction = _fit_predict_regression(
            outcome_train,
            fpca.scores,
            test_scores,
            n_components=selected,
            family=family,
            covariates_train=covariates_train,
            covariates_test=covariates_test,
        )
        outer_loss = _loss_value(
            values[test_idx],
            prediction,
            family=family,
            loss=resolved_loss,
        )
        outer_rows.append(
            {
                "outer_fold": outer_fold,
                "selected_n_components": selected,
                "loss": outer_loss,
                "n_train_curves": int(len(train_idx)),
                "n_test_curves": int(len(test_idx)),
            }
        )

        for position, index in enumerate(test_idx):
            row = {
                "curve_id": trajectories.curve_ids[index],
                "outer_fold": outer_fold,
                "observed": float(values[index]),
                "prediction": float(prediction[position]),
                "selected_n_components": selected,
            }
            if groups is not None:
                row["group"] = str(groups[index])
            prediction_rows.append(row)

    return FPCANestedRegressionCVResult(
        outer_folds=pd.DataFrame(outer_rows),
        inner_summaries=pd.concat(inner_rows, ignore_index=True),
        predictions=pd.DataFrame(prediction_rows),
        family=family,
        loss=resolved_loss,
        selection_rule=selection_rule,
        component_counts=counts,
        outer_splits=outer_splits,
        inner_splits=inner_splits,
        cv_unit=cv_unit,
        group_column=group_column if cv_unit == "group" else None,
        scaling=scaling,
        random_state=random_state if cv_unit == "curve" and shuffle else None,
        provenance={
            "method": "nested_outcome_tuned_fpca_regression_cv",
            "nested_selection": True,
            "outer_performance_unseen_by_inner_selection": True,
            "group_leakage_prevented": cv_unit == "group",
            "covariates": (
                [] if covariate_frame is None else list(covariate_frame.columns)
            ),
            "scientific_warning": (
                "Outer-fold performance estimates the predictive pipeline with "
                "inner FPC-count selection. It does not remove within-group "
                "dependence from a curve-level outcome model."
            ),
        },
    )
