"""Participant-aware split-conformal bands for sparse partial prediction.

The conformal target is a future *observed* trajectory on one declared finite
target grid. Calibration responses must have been observed at those exact grid
points; this module never interpolates or synchronizes raw future responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_native import SparseNativeError
from .sparse_partial_prediction import (
    SparseFPCAPartialPredictionResult,
    sparse_fpca_partial_trajectory_prediction,
)
from .types import IrregularTrajectorySet, SparseFPCAResult


_CALIBRATION_METHOD = "participant_aware_split_conformal_max_standardized_future_residual"
_BAND_METHOD = "finite_grid_simultaneous_split_conformal_prediction_band"


@dataclass(frozen=True)
class SparseFPCAPartialConformalCalibrationResult:
    """Split-conformal calibration for a fixed future grid and cutoff."""

    reference: SparseFPCAResult
    calibration_curve_ids: tuple[str, ...]
    calibration_unit_ids: tuple[str, ...]
    curve_scores: pd.DataFrame
    unit_scores: np.ndarray
    alpha: float
    critical_value: float
    history_cutoff: float
    prediction_grid: np.ndarray
    group_column: str | None
    min_history_observations: int
    condition_limit: float | None
    history_ridge: float | None
    method: str = _CALIBRATION_METHOD
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_calibration_curves(self) -> int:
        return len(self.calibration_curve_ids)

    @property
    def n_calibration_units(self) -> int:
        return len(self.calibration_unit_ids)


@dataclass(frozen=True)
class SparseFPCAPartialConformalBandResult:
    """Simultaneous finite-grid band for a future observed trajectory."""

    calibration: SparseFPCAPartialConformalCalibrationResult
    prediction: SparseFPCAPartialPredictionResult
    lower: np.ndarray
    upper: np.ndarray
    critical_value: float
    alpha: float
    target_calibration_unit: str
    method: str = _BAND_METHOD
    provenance: Mapping[str, Any] = field(default_factory=dict)


def _exact_future_values(
    trajectory: IrregularTrajectorySet,
    *,
    dimension: str,
    prediction_grid: np.ndarray,
) -> np.ndarray:
    """Extract actual observations at every exact target-grid timestamp."""

    if trajectory.n_curves != 1:
        raise ValueError("trajectory must contain exactly one curve")
    if dimension not in trajectory.dimension_names:
        raise ValueError(f"dimension {dimension!r} is absent from trajectory")
    times = np.asarray(trajectory.time[0], dtype=float)
    values = np.asarray(
        trajectory.values[0][:, trajectory.dimension_names.index(dimension)],
        dtype=float,
    )
    target = np.asarray(prediction_grid, dtype=float)
    out = np.empty(target.size, dtype=float)
    for index, point in enumerate(target):
        matches = np.flatnonzero(times == point)
        if matches.size != 1:
            raise SparseNativeError(
                "calibration_future_grid_observation_missing",
                "each future target-grid time must correspond to one actual retained observation",
                details={
                    "curve_id": str(trajectory.curve_ids[0]),
                    "time": float(point),
                    "match_count": int(matches.size),
                    "raw_interpolation_performed": False,
                },
            )
        value = float(values[int(matches[0])])
        if not np.isfinite(value):
            raise SparseNativeError(
                "calibration_future_grid_observation_nonfinite",
                "future target-grid observations used for calibration must be finite",
                details={
                    "curve_id": str(trajectory.curve_ids[0]),
                    "time": float(point),
                },
            )
        out[index] = value
    return out


def _single_curve(
    trajectories: IrregularTrajectorySet,
    index: int,
) -> IrregularTrajectorySet:
    return trajectories.subset([int(index)])


def _validate_calibration_partition(
    fit: SparseFPCAResult,
    calibration: IrregularTrajectorySet,
    *,
    group_column: str | None,
) -> tuple[np.ndarray, tuple[str, ...]]:
    if not isinstance(calibration, IrregularTrajectorySet):
        raise TypeError("calibration must be an IrregularTrajectorySet")
    fit_ids = set(map(str, fit.curve_ids))
    calibration_ids = set(map(str, calibration.curve_ids))
    overlap = sorted(fit_ids & calibration_ids)
    if overlap:
        raise ValueError(
            "proper-training fit and calibration curve IDs must be disjoint; "
            f"overlap={overlap}"
        )
    if fit.dimension not in calibration.dimension_names:
        raise ValueError("fit dimension is absent from calibration trajectories")
    if fit.coordinate_system != calibration.coordinate_system:
        raise ValueError("calibration coordinate_system does not match fit")
    if fit.time_unit != calibration.time_unit:
        raise ValueError("calibration time_unit does not match fit")

    if group_column is None:
        unit_values = np.asarray(calibration.curve_ids, dtype=object)
        return unit_values, tuple(map(str, fit.curve_ids))

    if group_column not in calibration.metadata.columns:
        raise ValueError(
            f"group_column {group_column!r} is absent from calibration metadata"
        )
    if group_column not in fit.metadata.columns:
        raise ValueError(
            f"group_column {group_column!r} is absent from fitted proper-training metadata"
        )
    calibration_groups = calibration.metadata[group_column].astype(str).to_numpy()
    training_groups = tuple(fit.metadata[group_column].astype(str).tolist())
    overlap_groups = sorted(set(training_groups) & set(calibration_groups.tolist()))
    if overlap_groups:
        raise ValueError(
            "proper-training and calibration participant/group units must be disjoint; "
            f"overlap={overlap_groups}"
        )
    return calibration_groups, training_groups


def _split_conformal_critical_value(
    scores: np.ndarray,
    *,
    alpha: float,
) -> tuple[float, int]:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or values.size < 1 or not np.all(np.isfinite(values)):
        raise ValueError("calibration scores must be a non-empty finite vector")
    alpha = float(alpha)
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    rank = int(np.ceil((values.size + 1) * (1.0 - alpha)))
    if rank > values.size:
        raise SparseNativeError(
            "insufficient_calibration_units_for_alpha",
            "requested alpha is below the finite-sample resolution of the calibration set",
            details={
                "alpha": alpha,
                "n_calibration_units": int(values.size),
                "required_order_statistic": rank,
                "minimum_supported_alpha": float(1.0 / (values.size + 1.0)),
            },
        )
    ordered = np.sort(values)
    return float(ordered[rank - 1]), rank


def calibrate_sparse_fpca_partial_prediction_conformal(
    fit: SparseFPCAResult,
    calibration: IrregularTrajectorySet,
    *,
    history_cutoff: float,
    prediction_grid: np.ndarray,
    alpha: float = 0.05,
    group_column: str | None = None,
    min_history_observations: int = 2,
    condition_limit: float | None = None,
    history_ridge: float | None = None,
) -> SparseFPCAPartialConformalCalibrationResult:
    """Calibrate a simultaneous finite-grid future-observation band.

    Curve-level nonconformity is the maximum standardized absolute residual over
    the declared future target grid. With ``group_column`` supplied, curve
    scores are aggregated by maximum within participant/group before the
    conformal order statistic is computed, making the declared exchangeability
    unit the participant/group rather than repeated trial.
    """

    target_grid = np.asarray(prediction_grid, dtype=float)
    unit_values, training_units = _validate_calibration_partition(
        fit,
        calibration,
        group_column=group_column,
    )
    rows: list[dict[str, Any]] = []
    for index, curve_id in enumerate(calibration.curve_ids):
        curve = _single_curve(calibration, index)
        prediction = sparse_fpca_partial_trajectory_prediction(
            fit,
            curve,
            history_cutoff=history_cutoff,
            prediction_grid=target_grid,
            min_history_observations=min_history_observations,
            condition_limit=condition_limit,
            history_ridge=history_ridge,
        )
        observed_future = _exact_future_values(
            curve,
            dimension=fit.dimension,
            prediction_grid=target_grid,
        )
        scale = np.asarray(
            prediction.observed_predictive_standard_errors,
            dtype=float,
        )
        if np.any(~np.isfinite(scale)) or np.any(scale <= 0):
            raise SparseNativeError(
                "invalid_conformal_predictive_scale",
                "observed predictive standard errors must be finite and positive",
                details={"curve_id": str(curve_id)},
            )
        standardized = np.abs(observed_future - prediction.conditional_mean) / scale
        score = float(np.max(standardized))
        if not np.isfinite(score):
            raise SparseNativeError(
                "nonfinite_conformal_score",
                "calibration nonconformity score is not finite",
                details={"curve_id": str(curve_id)},
            )
        rows.append(
            {
                "curve_id": str(curve_id),
                "calibration_unit": str(unit_values[index]),
                "nonconformity_score": score,
                "n_history": int(prediction.n_history),
                "n_future_grid": int(target_grid.size),
            }
        )

    curve_scores = pd.DataFrame(rows)
    unit_frame = (
        curve_scores.groupby("calibration_unit", sort=True, as_index=False)[
            "nonconformity_score"
        ]
        .max()
        .sort_values("calibration_unit")
        .reset_index(drop=True)
    )
    unit_ids = tuple(unit_frame["calibration_unit"].astype(str).tolist())
    unit_scores = unit_frame["nonconformity_score"].to_numpy(dtype=float)
    critical_value, rank = _split_conformal_critical_value(unit_scores, alpha=alpha)

    provenance: dict[str, Any] = {
        "method": _CALIBRATION_METHOD,
        "prediction_target": "future_observed_measurements_on_declared_finite_grid",
        "nonconformity": "maximum_standardized_absolute_future_residual",
        "standardization": "model_based_observed_predictive_standard_error",
        "calibration_unit": "curve" if group_column is None else "group",
        "group_column": group_column,
        "group_aggregation": "maximum_curve_nonconformity_within_group",
        "proper_training_curve_ids_disjoint": True,
        "proper_training_units": list(training_units),
        "raw_future_response_interpolation_performed": False,
        "future_grid_observation_match": "exact_timestamp_equality",
        "finite_sample_order_statistic_rank": int(rank),
        "finite_sample_quantile_rule": "ceil((n_calibration_units+1)*(1-alpha))",
        "simultaneous_scope": "declared_finite_future_grid",
        "continuous_domain_coverage_claimed": False,
        "latent_function_coverage_claimed": False,
        "exchangeability_required": True,
        "population_estimation_uncertainty_separately_propagated": False,
    }
    return SparseFPCAPartialConformalCalibrationResult(
        reference=fit,
        calibration_curve_ids=tuple(map(str, calibration.curve_ids)),
        calibration_unit_ids=unit_ids,
        curve_scores=curve_scores,
        unit_scores=unit_scores,
        alpha=float(alpha),
        critical_value=critical_value,
        history_cutoff=float(history_cutoff),
        prediction_grid=target_grid.copy(),
        group_column=group_column,
        min_history_observations=int(min_history_observations),
        condition_limit=condition_limit,
        history_ridge=history_ridge,
        provenance=provenance,
    )


def sparse_fpca_conformal_prediction_band(
    calibration: SparseFPCAPartialConformalCalibrationResult,
    trajectory: IrregularTrajectorySet,
) -> SparseFPCAPartialConformalBandResult:
    """Apply a fitted conformal calibration to one new target trajectory."""

    if not isinstance(calibration, SparseFPCAPartialConformalCalibrationResult):
        raise TypeError(
            "calibration must be a SparseFPCAPartialConformalCalibrationResult"
        )
    if not isinstance(trajectory, IrregularTrajectorySet):
        raise TypeError("trajectory must be an IrregularTrajectorySet")
    if trajectory.n_curves != 1:
        raise ValueError("trajectory must contain exactly one target curve")

    target_curve_id = str(trajectory.curve_ids[0])
    training_ids = set(map(str, calibration.reference.curve_ids))
    calibration_ids = set(calibration.calibration_curve_ids)
    if target_curve_id in training_ids or target_curve_id in calibration_ids:
        raise ValueError(
            "target curve ID must be disjoint from proper training and calibration"
        )

    if calibration.group_column is None:
        target_unit = target_curve_id
    else:
        group_column = calibration.group_column
        if group_column not in trajectory.metadata.columns:
            raise ValueError(
                f"group_column {group_column!r} is absent from target metadata"
            )
        target_unit = str(trajectory.metadata.iloc[0][group_column])
        if target_unit in set(calibration.calibration_unit_ids):
            raise ValueError(
                "target participant/group must be disjoint from calibration units"
            )
        fit_metadata = calibration.reference.metadata
        if group_column not in fit_metadata.columns:
            raise ValueError(
                f"group_column {group_column!r} is absent from fitted metadata"
            )
        training_units = set(fit_metadata[group_column].astype(str).tolist())
        if target_unit in training_units:
            raise ValueError(
                "target participant/group must be disjoint from proper-training units"
            )

    prediction = sparse_fpca_partial_trajectory_prediction(
        calibration.reference,
        trajectory,
        history_cutoff=calibration.history_cutoff,
        prediction_grid=calibration.prediction_grid,
        min_history_observations=calibration.min_history_observations,
        condition_limit=calibration.condition_limit,
        history_ridge=calibration.history_ridge,
    )
    scale = prediction.observed_predictive_standard_errors
    lower = prediction.conditional_mean - calibration.critical_value * scale
    upper = prediction.conditional_mean + calibration.critical_value * scale
    provenance = {
        "method": _BAND_METHOD,
        "prediction_target": "future_observed_measurements_on_declared_finite_grid",
        "simultaneous_scope": "declared_finite_future_grid",
        "continuous_domain_coverage_claimed": False,
        "latent_function_coverage_claimed": False,
        "exchangeability_unit": (
            "curve" if calibration.group_column is None else "participant_or_group"
        ),
        "target_unit": target_unit,
        "calibration_critical_value": float(calibration.critical_value),
        "alpha": float(calibration.alpha),
        "raw_future_response_interpolation_performed": False,
    }
    return SparseFPCAPartialConformalBandResult(
        calibration=calibration,
        prediction=prediction,
        lower=np.asarray(lower, dtype=float),
        upper=np.asarray(upper, dtype=float),
        critical_value=float(calibration.critical_value),
        alpha=float(calibration.alpha),
        target_calibration_unit=target_unit,
        provenance=provenance,
    )


def sparse_fpca_conformal_band_frame(
    result: SparseFPCAPartialConformalBandResult,
) -> pd.DataFrame:
    """Return the finite-grid conformal prediction band as a tidy frame."""

    if not isinstance(result, SparseFPCAPartialConformalBandResult):
        raise TypeError("result must be a SparseFPCAPartialConformalBandResult")
    prediction = result.prediction
    return pd.DataFrame(
        {
            "curve_id": prediction.curve_id,
            "dimension": prediction.dimension,
            "time": prediction.prediction_grid,
            "conditional_mean": prediction.conditional_mean,
            "observed_predictive_standard_error": (
                prediction.observed_predictive_standard_errors
            ),
            "lower": result.lower,
            "upper": result.upper,
            "alpha": result.alpha,
            "critical_value": result.critical_value,
        }
    )


def sparse_fpca_conformal_band_reporting_text(
    result: SparseFPCAPartialConformalBandResult,
    *,
    digits: int = 3,
) -> str:
    """Generate reporting text with an explicit finite-grid coverage scope."""

    if not isinstance(result, SparseFPCAPartialConformalBandResult):
        raise TypeError("result must be a SparseFPCAPartialConformalBandResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")
    calibration = result.calibration
    unit = "curve" if calibration.group_column is None else "participant/group"
    return (
        f"A split-conformal simultaneous prediction band was calibrated from "
        f"{calibration.n_calibration_units} exchangeability unit(s) ({unit}) at "
        f"alpha={calibration.alpha:.{digits}f}. Nonconformity was the maximum "
        f"standardized absolute future residual over the declared "
        f"{calibration.prediction_grid.size}-point target grid, with critical "
        f"value {calibration.critical_value:.{digits}f}. Calibration responses "
        f"were required to be actually observed at every target-grid timestamp; "
        f"no interpolation was used. The resulting coverage interpretation is "
        f"simultaneous for future observed measurements on that declared finite "
        f"grid under the exchangeability/grouping contract. No continuous-domain "
        f"or latent-function coverage claim is made."
    )
