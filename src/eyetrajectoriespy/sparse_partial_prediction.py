"""Conditional future-trajectory prediction from a native sparse FPCA fit.

This module predicts a future latent trajectory from a partially observed
native sparse history.  The calculation is conditional on fitted population
objects retained by :class:`~eyetrajectoriespy.types.SparseFPCAResult`; it does
not propagate uncertainty from estimating the mean/covariance/noise model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_native import (
    SparseNativeError,
    evaluate_fitted_covariance,
    evaluate_fitted_function,
)
from .types import IrregularTrajectorySet, SparseFPCAResult


_METHOD = "conditional_gaussian_future_given_native_sparse_history"


@dataclass(frozen=True)
class SparseFPCAPartialPredictionResult:
    """Conditional prediction of a future trajectory segment.

    The latent covariance is conditional on the fitted population mean,
    covariance surface, measurement-error variance and declared history-system
    regularization.  ``observed_predictive_covariance`` additionally includes
    the fitted measurement-error variance at each future target point.  The
    numerical history ridge is never relabelled as future measurement noise.
    """

    reference: SparseFPCAResult
    curve_id: str
    dimension: str
    history_cutoff: float
    history_times: np.ndarray
    history_values: np.ndarray
    prediction_grid: np.ndarray
    conditional_mean: np.ndarray
    latent_covariance: np.ndarray
    latent_standard_errors: np.ndarray
    observed_predictive_covariance: np.ndarray
    observed_predictive_standard_errors: np.ndarray
    diagnostics: pd.DataFrame
    method: str = _METHOD
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def n_history(self) -> int:
        return int(self.history_times.size)

    @property
    def n_prediction(self) -> int:
        return int(self.prediction_grid.size)


def _native_sparse_provenance(fit: SparseFPCAResult) -> Mapping[str, Any]:
    if not isinstance(fit, SparseFPCAResult):
        raise TypeError("fit must be a SparseFPCAResult")
    if fit.fit_method != "native_covariance":
        raise ValueError(
            "sparse partial prediction requires a native sparse FPCA fit"
        )
    sparse = fit.provenance.get("sparse_fpca", {})
    if not isinstance(sparse, Mapping) or sparse.get("backend") != "native":
        raise ValueError(
            "fit provenance does not identify the native sparse FPCA backend"
        )
    return sparse


def _population_arrays(
    fit: SparseFPCAResult,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    if fit.evaluation_grid is None:
        raise ValueError("fit does not retain an evaluation grid")
    if fit.mean is None:
        raise ValueError("fit does not retain its fitted mean")
    if fit.covariance is None:
        raise ValueError("fit does not retain its fitted covariance")
    if fit.noise_variance is None:
        raise ValueError("fit does not retain measurement-error variance")

    grid = np.asarray(fit.evaluation_grid, dtype=float)
    mean = np.asarray(fit.mean, dtype=float)
    covariance = np.asarray(fit.covariance, dtype=float)
    noise_variance = float(fit.noise_variance)

    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError("fit evaluation grid is invalid")
    if mean.shape != (grid.size,) or not np.all(np.isfinite(mean)):
        raise ValueError("fit mean does not align with evaluation grid")
    if (
        covariance.shape != (grid.size, grid.size)
        or not np.all(np.isfinite(covariance))
    ):
        raise ValueError("fit covariance does not align with evaluation grid")
    if not np.isfinite(noise_variance) or noise_variance < 0:
        raise ValueError("fit noise_variance must be finite and non-negative")
    return grid, mean, covariance, noise_variance


def _validate_target(
    fit: SparseFPCAResult,
    trajectory: IrregularTrajectorySet,
) -> tuple[np.ndarray, np.ndarray, str]:
    if not isinstance(trajectory, IrregularTrajectorySet):
        raise TypeError("trajectory must be an IrregularTrajectorySet")
    if trajectory.n_curves != 1:
        raise ValueError("trajectory must contain exactly one target curve")
    if fit.dimension not in trajectory.dimension_names:
        raise ValueError(
            f"fit dimension {fit.dimension!r} is absent from target trajectory"
        )
    if trajectory.coordinate_system != fit.coordinate_system:
        raise ValueError("target coordinate_system does not match fit")
    if trajectory.time_unit != fit.time_unit:
        raise ValueError("target time_unit does not match fit")

    index = trajectory.dimension_names.index(fit.dimension)
    time = np.asarray(trajectory.time[0], dtype=float)
    values = np.asarray(trajectory.values[0][:, index], dtype=float)
    return time, values, str(trajectory.curve_ids[0])


def sparse_fpca_partial_trajectory_prediction(
    fit: SparseFPCAResult,
    trajectory: IrregularTrajectorySet,
    *,
    history_cutoff: float,
    prediction_grid: np.ndarray,
    min_history_observations: int = 2,
    condition_limit: float | None = None,
    history_ridge: float | None = None,
) -> SparseFPCAPartialPredictionResult:
    """Predict a latent future trajectory from native sparse history.

    The conditional predictor uses the complete fitted covariance surface:

    ``mu_f + C_fo Sigma_oo^{-1} (Y_o - mu_o)``

    with latent conditional covariance

    ``C_ff - C_fo Sigma_oo^{-1} C_of``.

    ``Sigma_oo`` contains the full fitted history covariance plus fitted
    measurement-error variance and an optional numerical history ridge.  The
    raw target history is never interpolated and observations after
    ``history_cutoff`` are ignored completely.
    """

    sparse = _native_sparse_provenance(fit)
    grid, fitted_mean, fitted_covariance, noise_variance = _population_arrays(fit)
    time, values, curve_id = _validate_target(fit, trajectory)

    cutoff = float(history_cutoff)
    if not np.isfinite(cutoff):
        raise ValueError("history_cutoff must be finite")
    if cutoff < grid[0] or cutoff >= grid[-1]:
        raise SparseNativeError(
            "history_cutoff_outside_fitted_support",
            "history_cutoff must lie inside fitted support and before its end",
            details={
                "history_cutoff": cutoff,
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
            },
        )

    target = np.asarray(prediction_grid, dtype=float)
    if (
        target.ndim != 1
        or target.size < 1
        or not np.all(np.isfinite(target))
        or (target.size > 1 and not np.all(np.diff(target) > 0))
    ):
        raise ValueError(
            "prediction_grid must be a finite strictly increasing one-dimensional array"
        )
    if np.any(target <= cutoff):
        raise SparseNativeError(
            "prediction_grid_not_strictly_future",
            "all prediction_grid values must be strictly after history_cutoff",
            details={
                "history_cutoff": cutoff,
                "prediction_grid_min": float(np.min(target)),
            },
        )
    if target[0] < grid[0] or target[-1] > grid[-1]:
        raise SparseNativeError(
            "prediction_grid_outside_fitted_support",
            "prediction_grid must lie within fitted evaluation-grid support",
            details={
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
                "prediction_start": float(target[0]),
                "prediction_end": float(target[-1]),
            },
        )

    if isinstance(min_history_observations, bool) or not isinstance(
        min_history_observations, int
    ):
        raise TypeError("min_history_observations must be an integer")
    if min_history_observations < 1:
        raise ValueError("min_history_observations must be positive")

    history_mask = time <= cutoff
    history_times = time[history_mask].copy()
    history_values = values[history_mask].copy()
    if history_times.size < min_history_observations:
        raise SparseNativeError(
            "insufficient_history_observations",
            "target history has fewer observations than required",
            details={
                "curve_id": curve_id,
                "history_cutoff": cutoff,
                "n_history": int(history_times.size),
                "min_history_observations": int(min_history_observations),
            },
        )
    if not np.all(np.isfinite(history_values)):
        raise SparseNativeError(
            "nonfinite_history_observation",
            "history observations for the fitted dimension must be finite",
            details={
                "curve_id": curve_id,
                "n_nonfinite": int(np.count_nonzero(~np.isfinite(history_values))),
            },
        )
    if history_times[0] < grid[0] or history_times[-1] > grid[-1]:
        raise SparseNativeError(
            "history_observations_outside_fitted_support",
            "history observations lie outside fitted evaluation-grid support",
            details={
                "curve_id": curve_id,
                "history_min": float(history_times[0]),
                "history_max": float(history_times[-1]),
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
            },
        )

    fitted_condition_limit = float(sparse.get("score_condition_limit", 1e12))
    selected_condition_limit = (
        fitted_condition_limit if condition_limit is None else float(condition_limit)
    )
    if not np.isfinite(selected_condition_limit) or selected_condition_limit <= 1:
        raise ValueError("condition_limit must be finite and greater than 1")

    fitted_ridge = float(sparse.get("score_ridge", 0.0))
    selected_ridge = fitted_ridge if history_ridge is None else float(history_ridge)
    if not np.isfinite(selected_ridge) or selected_ridge < 0:
        raise ValueError("history_ridge must be finite and non-negative")

    combined = np.concatenate([history_times, target])
    combined_covariance = evaluate_fitted_covariance(
        grid,
        fitted_covariance,
        combined,
    )
    n_history = history_times.size
    c_oo = combined_covariance[:n_history, :n_history]
    c_of = combined_covariance[:n_history, n_history:]
    c_fo = combined_covariance[n_history:, :n_history]
    c_ff = combined_covariance[n_history:, n_history:]

    mu_o = evaluate_fitted_function(grid, fitted_mean, history_times)
    mu_f = evaluate_fitted_function(grid, fitted_mean, target)
    sigma_oo = c_oo + (noise_variance + selected_ridge) * np.eye(n_history)
    sigma_oo = 0.5 * (sigma_oo + sigma_oo.T)

    sigma_eigenvalues = np.linalg.eigvalsh(sigma_oo)
    minimum_eigenvalue = float(np.min(sigma_eigenvalues))
    maximum_eigenvalue = float(np.max(sigma_eigenvalues))
    condition_number = (
        np.inf
        if minimum_eigenvalue <= 0
        else maximum_eigenvalue / minimum_eigenvalue
    )
    if minimum_eigenvalue <= 0:
        raise SparseNativeError(
            "history_covariance_not_positive_definite",
            "history conditioning covariance is not positive definite",
            details={
                "curve_id": curve_id,
                "minimum_eigenvalue": minimum_eigenvalue,
                "history_ridge": selected_ridge,
            },
        )
    if condition_number > selected_condition_limit:
        raise SparseNativeError(
            "history_covariance_ill_conditioned",
            "history conditioning covariance exceeds condition_limit",
            details={
                "curve_id": curve_id,
                "condition_number": condition_number,
                "condition_limit": selected_condition_limit,
            },
        )

    centered_history = history_values - mu_o
    rhs = np.column_stack([centered_history, c_of])
    solved = np.linalg.solve(sigma_oo, rhs)
    conditional_mean = mu_f + c_fo @ solved[:, 0]
    latent_covariance = c_ff - c_fo @ solved[:, 1:]
    latent_covariance = 0.5 * (latent_covariance + latent_covariance.T)

    covariance_scale = max(1.0, float(np.max(np.abs(c_ff))))
    posterior_psd_tolerance = 1e-10 * covariance_scale
    posterior_eigenvalues = np.linalg.eigvalsh(latent_covariance)
    posterior_minimum_eigenvalue = float(np.min(posterior_eigenvalues))
    posterior_psd_repair_applied = False
    if posterior_minimum_eigenvalue < -posterior_psd_tolerance:
        raise SparseNativeError(
            "conditional_future_covariance_not_psd",
            "conditional latent future covariance is not PSD within tolerance",
            details={
                "curve_id": curve_id,
                "minimum_eigenvalue": posterior_minimum_eigenvalue,
                "tolerance": posterior_psd_tolerance,
            },
        )
    if posterior_minimum_eigenvalue < 0:
        values_psd, vectors_psd = np.linalg.eigh(latent_covariance)
        values_psd = np.maximum(values_psd, 0.0)
        latent_covariance = (vectors_psd * values_psd) @ vectors_psd.T
        latent_covariance = 0.5 * (latent_covariance + latent_covariance.T)
        posterior_psd_repair_applied = True

    latent_standard_errors = np.sqrt(
        np.maximum(np.diag(latent_covariance), 0.0)
    )
    observed_predictive_covariance = latent_covariance + noise_variance * np.eye(
        target.size
    )
    observed_predictive_standard_errors = np.sqrt(
        np.maximum(np.diag(observed_predictive_covariance), 0.0)
    )

    residual_scale = max(1.0, float(np.linalg.norm(rhs)))
    solve_relative_residual = float(
        np.linalg.norm(sigma_oo @ solved - rhs) / residual_scale
    )
    future_rows_ignored = int(np.count_nonzero(time > cutoff))
    diagnostics = pd.DataFrame(
        [
            {
                "curve_id": curve_id,
                "history_cutoff": cutoff,
                "n_history": int(history_times.size),
                "n_prediction": int(target.size),
                "future_rows_ignored": future_rows_ignored,
                "condition_number": float(condition_number),
                "minimum_eigenvalue": minimum_eigenvalue,
                "maximum_eigenvalue": maximum_eigenvalue,
                "conditional_covariance_minimum_eigenvalue": (
                    posterior_minimum_eigenvalue
                ),
                "conditional_covariance_psd_repair_applied": bool(
                    posterior_psd_repair_applied
                ),
                "solve_relative_residual": solve_relative_residual,
                "measurement_error_variance": noise_variance,
                "history_ridge": selected_ridge,
                "condition_limit": selected_condition_limit,
                "status_code": "ok",
            }
        ]
    )

    provenance: dict[str, Any] = {
        "method": _METHOD,
        "prediction_target": "latent_future_trajectory_conditional_on_fitted_population",
        "observed_predictive_covariance_includes_measurement_error": True,
        "history_ridge_in_observed_future_noise": False,
        "covariance_source": "full_fitted_repaired_covariance",
        "rank_k_covariance_used_for_prediction": False,
        "raw_history_interpolation_performed": False,
        "future_observations_after_cutoff_used": False,
        "population_function_evaluation_at_native_and_target_times": True,
        "measurement_error_variance": noise_variance,
        "history_ridge": selected_ridge,
        "history_ridge_source": (
            "fitted_score_ridge" if history_ridge is None else "explicit_override"
        ),
        "condition_limit": selected_condition_limit,
        "condition_limit_source": (
            "fitted_score_condition_limit"
            if condition_limit is None
            else "explicit_override"
        ),
        "population_estimation_uncertainty_included": False,
        "bandwidth_uncertainty_included": False,
        "conformal_calibration_applied": False,
        "coverage_claim": "none_model_based_conditional_moments_only",
    }
    return SparseFPCAPartialPredictionResult(
        reference=fit,
        curve_id=curve_id,
        dimension=fit.dimension,
        history_cutoff=cutoff,
        history_times=history_times,
        history_values=history_values,
        prediction_grid=target.copy(),
        conditional_mean=np.asarray(conditional_mean, dtype=float),
        latent_covariance=np.asarray(latent_covariance, dtype=float),
        latent_standard_errors=np.asarray(latent_standard_errors, dtype=float),
        observed_predictive_covariance=np.asarray(
            observed_predictive_covariance,
            dtype=float,
        ),
        observed_predictive_standard_errors=np.asarray(
            observed_predictive_standard_errors,
            dtype=float,
        ),
        diagnostics=diagnostics,
        provenance=provenance,
    )


def sparse_fpca_partial_prediction_frame(
    result: SparseFPCAPartialPredictionResult,
) -> pd.DataFrame:
    """Return one row per future prediction-grid point."""

    if not isinstance(result, SparseFPCAPartialPredictionResult):
        raise TypeError("result must be a SparseFPCAPartialPredictionResult")
    return pd.DataFrame(
        {
            "curve_id": result.curve_id,
            "dimension": result.dimension,
            "time": result.prediction_grid,
            "conditional_mean": result.conditional_mean,
            "latent_standard_error": result.latent_standard_errors,
            "observed_predictive_standard_error": (
                result.observed_predictive_standard_errors
            ),
        }
    )


def sparse_fpca_partial_prediction_reporting_text(
    result: SparseFPCAPartialPredictionResult,
    *,
    digits: int = 3,
) -> str:
    """Generate audit-oriented wording for a sparse partial prediction."""

    if not isinstance(result, SparseFPCAPartialPredictionResult):
        raise TypeError("result must be a SparseFPCAPartialPredictionResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")

    row = result.diagnostics.iloc[0]
    return (
        f"A native sparse partial-trajectory prediction was computed for curve "
        f"{result.curve_id!r} and dimension {result.dimension!r} from "
        f"{result.n_history} observed history value(s) through cutoff "
        f"{result.history_cutoff:.{digits}f}, predicting {result.n_prediction} "
        f"future grid point(s). The conditional mean and latent covariance used "
        f"the full fitted/repaired sparse-FPCA covariance, not a rank-K "
        f"reconstruction, with fitted measurement-error variance "
        f"{float(row['measurement_error_variance']):.{digits}f} and history "
        f"ridge {float(row['history_ridge']):.{digits}f}. Raw history was not "
        f"interpolated and observations after the cutoff were ignored. The "
        f"reported latent uncertainty is conditional on fitted population "
        f"objects; the observed predictive standard errors additionally include "
        f"measurement noise. No conformal calibration or frequentist coverage "
        f"claim is attached to this result."
    )
