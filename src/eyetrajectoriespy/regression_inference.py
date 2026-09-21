"""Paired-bootstrap uncertainty for Gaussian FPCA scalar regression."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .analysis import fit_scalar_on_function_regression
from .fpca import transform_fpca
from .stability import _fit_for_trajectories
from .types import (
    FPCARegressionSlopeBandResult,
    FPCARegressionUncertaintyResult,
    FPCAResult,
    FunctionalRegressionResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _validate_complete_finite(
    trajectories: TrajectorySet,
    *,
    name: str,
) -> None:
    validate_trajectory_set(trajectories, require_complete=True)
    if trajectories.n_curves < 1:
        raise ValueError(f"{name} must contain at least one trajectory")
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError(f"{name} must contain only finite trajectory values")


def _validate_targets(
    training: TrajectorySet,
    targets: TrajectorySet,
) -> None:
    _validate_complete_finite(targets, name="targets")
    if not np.array_equal(training.time, targets.time):
        raise ValueError("targets must use the exact training time grid")
    if training.dimension_names != targets.dimension_names:
        raise ValueError(
            "targets must use the same functional dimension names and order"
        )
    if training.coordinate_system != targets.coordinate_system:
        raise ValueError("targets must use the same coordinate_system as training")
    if training.time_unit != targets.time_unit:
        raise ValueError("targets must use the same time_unit as training")


def _functional_slope(
    fpca: FPCAResult,
    regression: FunctionalRegressionResult,
    *,
    n_components: int,
) -> np.ndarray:
    """Reconstruct the FPCR slope in original trajectory coordinate units."""

    names = [f"FPC{k + 1}" for k in range(n_components)]
    try:
        coefficients = regression.coefficients.loc[names].to_numpy(dtype=float)
    except KeyError as exc:
        raise ValueError("regression result does not contain the required FPC coefficients") from exc

    if fpca.scale.shape != (len(fpca.dimension_names),):
        raise ValueError("FPCA scale vector is incompatible with its dimensions")
    if np.any(fpca.scale <= np.finfo(float).eps):
        raise ValueError("FPCA scale must be strictly positive")

    # score_j = sum_{t,d} (x - mean) * component_j * weight / scale_d^2
    # so beta(t,d) = sum_j b_j * component_j(t,d) / scale_d^2.
    slope = np.einsum(
        "k,ktd->td",
        coefficients,
        fpca.components[:n_components],
    ) / (fpca.scale[None, :] ** 2)
    if not np.all(np.isfinite(slope)):
        raise RuntimeError("reconstructed functional slope contains non-finite values")
    return slope


def _check_regression_design(
    fpca: FPCAResult,
    *,
    n_components: int,
    context: str,
) -> None:
    design = np.column_stack(
        [
            np.ones(len(fpca.curve_ids), dtype=float),
            fpca.scores[:, :n_components],
        ]
    )
    required_rank = n_components + 1
    rank = int(np.linalg.matrix_rank(design))
    if rank < required_rank:
        raise RuntimeError(
            f"{context} FPCA regression design is rank deficient "
            f"(rank={rank}, required={required_rank}); reduce n_components or "
            "use a larger/more variable independent-unit sample"
        )


def _curve_bootstrap_indices(
    trajectories: TrajectorySet,
    rng: np.random.Generator,
) -> np.ndarray:
    return rng.integers(
        0,
        trajectories.n_curves,
        size=trajectories.n_curves,
    )


def _participant_bootstrap_indices(
    trajectories: TrajectorySet,
    rng: np.random.Generator,
    *,
    participant_column: str,
) -> np.ndarray:
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column {participant_column!r}"
        )
    if trajectories.metadata[participant_column].isna().any():
        raise ValueError("participant_column contains missing values")
    participant = trajectories.metadata[participant_column].astype(str).to_numpy()
    unique = pd.unique(participant)
    if len(unique) < 2:
        raise ValueError("At least two participants are required for participant bootstrap")
    draws = rng.choice(unique, size=len(unique), replace=True)
    indices: list[int] = []
    for participant_id in draws:
        indices.extend(np.flatnonzero(participant == participant_id).tolist())
    return np.asarray(indices, dtype=int)


def _bootstrap_sample(
    trajectories: TrajectorySet,
    indices: np.ndarray,
    *,
    replicate: int,
) -> TrajectorySet:
    metadata = trajectories.metadata.iloc[indices].reset_index(drop=True)
    curve_ids = tuple(
        f"bootstrap_{replicate:05d}_{j:05d}|{trajectories.curve_ids[i]}"
        for j, i in enumerate(indices)
    )
    return TrajectorySet(
        time=trajectories.time,
        values=trajectories.values[indices],
        curve_ids=curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=metadata,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "paired_regression_bootstrap": {
                "replicate": replicate,
                "source_indices": indices.astype(int).tolist(),
            },
        },
    )


def _mean_predictions(
    fpca: FPCAResult,
    regression: FunctionalRegressionResult,
    targets: TrajectorySet,
    *,
    n_components: int,
) -> np.ndarray:
    scores = transform_fpca(fpca, targets)[:, :n_components]
    names = [f"FPC{k + 1}" for k in range(n_components)]
    coefficients = regression.coefficients.loc[names].to_numpy(dtype=float)
    intercept = float(regression.coefficients.loc["const"])
    predictions = intercept + scores @ coefficients
    if not np.all(np.isfinite(predictions)):
        raise RuntimeError("FPCA regression produced non-finite mean predictions")
    return np.asarray(predictions, dtype=float)


def bootstrap_fpca_regression_uncertainty(
    trajectories: TrajectorySet,
    outcome: np.ndarray | pd.Series,
    *,
    targets: TrajectorySet | None = None,
    n_bootstrap: int = 500,
    n_components: int = 3,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    level: float = 0.95,
    random_state: int | None = 0,
) -> FPCARegressionUncertaintyResult:
    """Paired-bootstrap uncertainty for Gaussian scalar-on-function FPCR.

    The independent sampling unit is resampled together with its scalar outcome.
    FPCA/MFPCA and the Gaussian score regression are refitted in every bootstrap
    replicate. The component count is held fixed.

    Returned slope envelopes are pointwise percentile bootstrap summaries for
    the reconstructed slope in original trajectory coordinate units. Returned
    target intervals are uncertainty intervals for the fitted *conditional mean*
    response of fixed target curves, not prediction intervals for future noisy
    outcomes.

    This routine does not implement the operator-scaled bootstrap test proposed
    in the 2026 FPCR inference literature, does not reselect the component count
    inside bootstrap replicates, and does not support binomial regression.
    """

    _validate_complete_finite(trajectories, name="training trajectories")
    y = np.asarray(outcome, dtype=float)
    if y.shape != (trajectories.n_curves,):
        raise ValueError("outcome must contain exactly one value per training trajectory")
    if not np.all(np.isfinite(y)):
        raise ValueError("outcome must contain only finite values")

    if targets is None:
        target_set = trajectories
        target_source = "training"
    else:
        target_set = targets
        target_source = "external"
        _validate_targets(trajectories, target_set)

    if isinstance(n_bootstrap, bool) or not isinstance(
        n_bootstrap,
        (int, np.integer),
    ):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 20:
        raise ValueError("n_bootstrap must be at least 20")

    if isinstance(n_components, bool) or not isinstance(
        n_components,
        (int, np.integer),
    ):
        raise TypeError("n_components must be an integer")
    n_components = int(n_components)
    max_nonzero_rank = min(
        trajectories.n_curves - 1,
        trajectories.n_time * trajectories.n_dimensions,
    )
    if n_components < 1 or n_components > max_nonzero_rank:
        raise ValueError(
            f"n_components must be in [1, {max_nonzero_rank}] for non-zero-rank FPCA"
        )

    if scaling not in {"none", "dimension_sd"}:
        raise ValueError("scaling must be 'none' or 'dimension_sd'")
    if resample_unit not in {"curve", "participant"}:
        raise ValueError("resample_unit must be 'curve' or 'participant'")
    if resample_unit == "curve" and participant_column is not None:
        raise ValueError(
            "participant_column must be None when resample_unit='curve'"
        )
    if resample_unit == "participant" and not participant_column:
        raise ValueError(
            "participant_column is required when resample_unit='participant'"
        )
    if not 0 < level < 1:
        raise ValueError("level must lie in (0, 1)")

    reference_fpca = _fit_for_trajectories(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    _check_regression_design(
        reference_fpca,
        n_components=n_components,
        context="reference",
    )
    reference_regression = fit_scalar_on_function_regression(
        reference_fpca,
        y,
        n_components=n_components,
        family="gaussian",
    )
    reference_slope = _functional_slope(
        reference_fpca,
        reference_regression,
        n_components=n_components,
    )
    reference_intercept = float(reference_regression.coefficients.loc["const"])
    reference_predictions = _mean_predictions(
        reference_fpca,
        reference_regression,
        target_set,
        n_components=n_components,
    )

    rng = np.random.default_rng(random_state)
    bootstrap_slopes = np.empty(
        (
            n_bootstrap,
            trajectories.n_time,
            trajectories.n_dimensions,
        ),
        dtype=float,
    )
    bootstrap_intercepts = np.empty(n_bootstrap, dtype=float)
    bootstrap_predictions = np.empty(
        (n_bootstrap, target_set.n_curves),
        dtype=float,
    )

    for bootstrap_index in range(n_bootstrap):
        if resample_unit == "curve":
            indices = _curve_bootstrap_indices(trajectories, rng)
        else:
            indices = _participant_bootstrap_indices(
                trajectories,
                rng,
                participant_column=str(participant_column),
            )

        if indices.size <= n_components:
            raise RuntimeError(
                f"bootstrap replicate {bootstrap_index} has too few paired observations "
                f"for {n_components} FPC predictors"
            )

        sample = _bootstrap_sample(
            trajectories,
            indices,
            replicate=bootstrap_index,
        )
        candidate_fpca = _fit_for_trajectories(
            sample,
            n_components=n_components,
            scaling=scaling,
        )
        _check_regression_design(
            candidate_fpca,
            n_components=n_components,
            context=f"bootstrap replicate {bootstrap_index}",
        )
        candidate_regression = fit_scalar_on_function_regression(
            candidate_fpca,
            y[indices],
            n_components=n_components,
            family="gaussian",
        )

        bootstrap_slopes[bootstrap_index] = _functional_slope(
            candidate_fpca,
            candidate_regression,
            n_components=n_components,
        )
        bootstrap_intercepts[bootstrap_index] = float(
            candidate_regression.coefficients.loc["const"]
        )
        bootstrap_predictions[bootstrap_index] = _mean_predictions(
            candidate_fpca,
            candidate_regression,
            target_set,
            n_components=n_components,
        )

    alpha = (1.0 - float(level)) / 2.0
    slope_lower = np.quantile(bootstrap_slopes, alpha, axis=0)
    slope_median = np.quantile(bootstrap_slopes, 0.5, axis=0)
    slope_upper = np.quantile(bootstrap_slopes, 1.0 - alpha, axis=0)
    slope_se = np.std(bootstrap_slopes, axis=0, ddof=1)

    prediction_lower = np.quantile(bootstrap_predictions, alpha, axis=0)
    prediction_median = np.quantile(bootstrap_predictions, 0.5, axis=0)
    prediction_upper = np.quantile(bootstrap_predictions, 1.0 - alpha, axis=0)
    prediction_se = np.std(bootstrap_predictions, axis=0, ddof=1)

    return FPCARegressionUncertaintyResult(
        reference_fpca=reference_fpca,
        reference_regression=reference_regression,
        reference_slope=reference_slope,
        bootstrap_slopes=bootstrap_slopes,
        slope_lower=slope_lower,
        slope_median=slope_median,
        slope_upper=slope_upper,
        slope_se=slope_se,
        reference_intercept=reference_intercept,
        bootstrap_intercepts=bootstrap_intercepts,
        target_curve_ids=target_set.curve_ids,
        reference_mean_predictions=reference_predictions,
        bootstrap_mean_predictions=bootstrap_predictions,
        prediction_lower=prediction_lower,
        prediction_median=prediction_median,
        prediction_upper=prediction_upper,
        prediction_se=prediction_se,
        level=float(level),
        n_components=n_components,
        scaling=scaling,
        resampling_unit=resample_unit,
        participant_column=(
            participant_column if resample_unit == "participant" else None
        ),
        target_source=target_source,
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_regression_uncertainty": {
                "method": "paired_nonparametric_bootstrap_full_fpcr_refit",
                "family": "gaussian",
                "n_bootstrap": n_bootstrap,
                "n_components": n_components,
                "component_count_fixed": True,
                "component_selection_uncertainty_included": False,
                "scaling": scaling,
                "resample_unit": resample_unit,
                "participant_column": (
                    participant_column if resample_unit == "participant" else None
                ),
                "level": float(level),
                "slope_interval": "pointwise_percentile_bootstrap",
                "prediction_interval": "fixed_target_conditional_mean_percentile_bootstrap",
                "future_outcome_prediction_interval": False,
                "target_source": target_source,
                "target_curves_fixed": True,
                "fpc_label_matching_required": False,
                "fpc_label_invariance_reason": (
                    "slope_and_mean_prediction_reconstructed_from_each_complete_refit"
                ),
                "operator_scaled_fpcr_test": False,
                "random_state": random_state,
            },
        },
    )


def fpca_regression_slope_simultaneous_band(
    result: FPCARegressionUncertaintyResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "global",
) -> FPCARegressionSlopeBandResult:
    """Calibrate an observed-grid simultaneous band from paired FPCR bootstraps.

    Global scope uses one maximum over the full observed time-by-dimension
    slope grid. Dimension scope calibrates one maximum over time separately
    within each functional dimension.

    The procedure is a studentized maximum-deviation bootstrap approximation
    derived from already-computed paired-bootstrap slope replicates. It is not
    a continuous-domain confidence band and is not the operator-scaled FPCR
    significance test from recent asymptotic theory.
    """

    if not isinstance(result, FPCARegressionUncertaintyResult):
        raise TypeError(
            "result must be an FPCARegressionUncertaintyResult from "
            "bootstrap_fpca_regression_uncertainty()"
        )
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"global", "dimension"}:
        raise ValueError(
            "simultaneous_scope must be 'global' or 'dimension'"
        )

    reference = np.asarray(result.reference_slope, dtype=float)
    bootstrap = np.asarray(result.bootstrap_slopes, dtype=float)
    if bootstrap.ndim != 3 or bootstrap.shape[1:] != reference.shape:
        raise ValueError("bootstrap slope array is incompatible with reference slope")
    if bootstrap.shape[0] < 2:
        raise ValueError("at least two bootstrap slope replicates are required")
    if not np.all(np.isfinite(reference)) or not np.all(np.isfinite(bootstrap)):
        raise ValueError("reference and bootstrap slopes must be finite")

    deviations = bootstrap - reference[None, :, :]
    pointwise_se = np.std(deviations, axis=0, ddof=1)
    scale = max(1.0, float(np.max(np.abs(reference))))
    positive_variance = pointwise_se > np.finfo(float).eps * scale
    tolerance = 100.0 * np.finfo(float).eps * scale

    degenerate = (~positive_variance) & (
        np.max(np.abs(deviations), axis=0) > tolerance
    )
    if np.any(degenerate):
        positions = np.argwhere(degenerate)
        preview = [
            {
                "time_index": int(time_index),
                "dimension": result.reference_fpca.dimension_names[int(dimension_index)],
            }
            for time_index, dimension_index in positions[:8]
        ]
        raise RuntimeError(
            "FPCR slope-band calibration is degenerate: zero bootstrap SE with "
            f"non-zero reference discrepancy at {len(positions)} grid cell(s); "
            f"first cells={preview}"
        )

    standardized = np.zeros_like(deviations)
    np.divide(
        deviations,
        pointwise_se[None, :, :],
        out=standardized,
        where=positive_variance[None, :, :],
    )
    absolute_statistics = np.abs(standardized)

    if simultaneous_scope == "global":
        max_statistics = np.max(absolute_statistics, axis=(1, 2))
        critical = float(
            np.quantile(
                max_statistics,
                confidence_level,
                method="higher",
            )
        )
        critical_values = np.full(reference.shape[1], critical, dtype=float)
    else:
        max_statistics = np.max(absolute_statistics, axis=1)
        critical_values = np.quantile(
            max_statistics,
            confidence_level,
            axis=0,
            method="higher",
        ).astype(float)

    half_width = pointwise_se * critical_values[None, :]
    lower = reference - half_width
    upper = reference + half_width

    return FPCARegressionSlopeBandResult(
        regression_uncertainty=result,
        lower=lower,
        upper=upper,
        pointwise_se=pointwise_se,
        critical_values=np.asarray(critical_values, dtype=float),
        max_statistics=np.asarray(max_statistics, dtype=float),
        confidence_level=float(confidence_level),
        simultaneous_scope=simultaneous_scope,
        provenance={
            **dict(result.provenance),
            "fpca_regression_slope_band": {
                "method": "studentized_bootstrap_maximum_observed_grid",
                "confidence_level": float(confidence_level),
                "simultaneous_scope": simultaneous_scope,
                "domain": "observed_time_by_dimension_grid",
                "continuous_between_grid_points": False,
                "operator_scaled_fpcr_test": False,
                "bootstrap_reused_from_regression_uncertainty": True,
                "n_bootstrap": result.n_bootstrap,
                "zero_variance_cells": int((~positive_variance).sum()),
            },
        },
    )


def fpca_regression_slope_band_frame(
    result: FPCARegressionSlopeBandResult,
) -> pd.DataFrame:
    """Return long-form observed-grid simultaneous slope-band summaries."""

    rows: list[dict[str, float | str]] = []
    reference = result.regression_uncertainty.reference_slope
    fpca = result.regression_uncertainty.reference_fpca
    for time_index, time in enumerate(fpca.time):
        for dimension_index, dimension in enumerate(fpca.dimension_names):
            rows.append(
                {
                    "time": float(time),
                    "dimension": dimension,
                    "reference_slope": float(
                        reference[time_index, dimension_index]
                    ),
                    "pointwise_se": float(
                        result.pointwise_se[time_index, dimension_index]
                    ),
                    "critical_value": float(
                        result.critical_values[dimension_index]
                    ),
                    "lower": float(result.lower[time_index, dimension_index]),
                    "upper": float(result.upper[time_index, dimension_index]),
                }
            )
    return pd.DataFrame(rows)


def fpca_regression_slope_uncertainty_frame(
    result: FPCARegressionUncertaintyResult,
) -> pd.DataFrame:
    """Return long-form pointwise functional-slope uncertainty summaries."""

    rows: list[dict[str, float | str]] = []
    for time_index, time in enumerate(result.reference_fpca.time):
        for dimension_index, dimension in enumerate(
            result.reference_fpca.dimension_names
        ):
            rows.append(
                {
                    "time": float(time),
                    "dimension": dimension,
                    "reference_slope": float(
                        result.reference_slope[time_index, dimension_index]
                    ),
                    "bootstrap_median": float(
                        result.slope_median[time_index, dimension_index]
                    ),
                    "bootstrap_se": float(
                        result.slope_se[time_index, dimension_index]
                    ),
                    "lower": float(
                        result.slope_lower[time_index, dimension_index]
                    ),
                    "upper": float(
                        result.slope_upper[time_index, dimension_index]
                    ),
                }
            )
    return pd.DataFrame(rows)


def fpca_regression_prediction_uncertainty_frame(
    result: FPCARegressionUncertaintyResult,
) -> pd.DataFrame:
    """Return fixed-target conditional-mean uncertainty summaries."""

    return pd.DataFrame(
        {
            "curve_id": result.target_curve_ids,
            "reference_mean_prediction": result.reference_mean_predictions,
            "bootstrap_median": result.prediction_median,
            "bootstrap_se": result.prediction_se,
            "lower": result.prediction_lower,
            "upper": result.prediction_upper,
        }
    )
