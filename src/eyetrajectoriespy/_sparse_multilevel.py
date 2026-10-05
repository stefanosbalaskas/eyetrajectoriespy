"""Numerical primitives for native sparse participant/trial multilevel FPCA.

The private layer implements only hierarchy-specific algebra. Population
smoothing, PSD policy, eigendecomposition, and measurement-error estimation are
composed from the already-qualified native sparse-FPCA primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

from ._sparse_native import (
    RawCovariancePairs,
    SparseNativeError,
    evaluate_fitted_function,
)


@dataclass(frozen=True)
class SparseMultilevelScoreResult:
    """Joint participant/trial BLUP scores and participant-level diagnostics."""

    participant_ids: tuple[str, ...]
    curve_ids: tuple[str, ...]
    participant_scores: np.ndarray
    trial_scores: np.ndarray
    diagnostics: pd.DataFrame
    covariance_source: str = "full_fitted_between_plus_within_plus_noise"


def _validate_aligned_sequences(
    curve_times: Sequence[np.ndarray],
    curve_values: Sequence[np.ndarray],
    participant_ids: Sequence[str],
    curve_ids: Sequence[str] | None = None,
) -> None:
    n_curves = len(curve_times)
    if len(curve_values) != n_curves or len(participant_ids) != n_curves:
        raise ValueError(
            "curve_times, curve_values, and participant_ids must have equal length"
        )
    if curve_ids is not None and len(curve_ids) != n_curves:
        raise ValueError("curve_ids must align with curve_times")
    if n_curves == 0:
        raise ValueError("at least one curve is required")
    for time, values in zip(curve_times, curve_values, strict=True):
        time_array = np.asarray(time, dtype=float)
        value_array = np.asarray(values, dtype=float)
        if (
            time_array.ndim != 1
            or value_array.ndim != 1
            or time_array.shape != value_array.shape
        ):
            raise ValueError(
                "each curve time/value pair must be one-dimensional and aligned"
            )
        if not np.all(np.isfinite(time_array)) or not np.all(np.isfinite(value_array)):
            raise ValueError("curve times and values must be finite")


def raw_cross_trial_covariance_pairs(
    curve_times: Sequence[np.ndarray],
    curve_residuals: Sequence[np.ndarray],
    participant_ids: Sequence[str],
    *,
    include_mirror: bool = True,
) -> RawCovariancePairs:
    """Construct same-participant, distinct-trial covariance products.

    Every product uses observations from two *different* curves belonging to the
    same participant. Products from different participants are never included.
    With ``include_mirror=True`` each product is represented at both ``(s, t)``
    and ``(t, s)`` so the population between-participant covariance smoother is
    explicitly symmetric.
    """

    _validate_aligned_sequences(curve_times, curve_residuals, participant_ids)
    participant_array = np.asarray([str(value) for value in participant_ids], dtype=object)
    unique_participants = tuple(pd.unique(participant_array).tolist())
    participant_lookup = {
        participant: index for index, participant in enumerate(unique_participants)
    }

    s_values: list[float] = []
    t_values: list[float] = []
    products: list[float] = []
    participant_indices: list[int] = []

    for participant in unique_participants:
        curve_indices = np.flatnonzero(participant_array == participant)
        if curve_indices.size < 2:
            continue
        participant_index = participant_lookup[participant]
        for left_position in range(curve_indices.size - 1):
            left_index = int(curve_indices[left_position])
            left_time = np.asarray(curve_times[left_index], dtype=float)
            left_residual = np.asarray(curve_residuals[left_index], dtype=float)
            for right_position in range(left_position + 1, curve_indices.size):
                right_index = int(curve_indices[right_position])
                right_time = np.asarray(curve_times[right_index], dtype=float)
                right_residual = np.asarray(curve_residuals[right_index], dtype=float)
                for left_sample in range(left_time.size):
                    for right_sample in range(right_time.size):
                        product = float(
                            left_residual[left_sample] * right_residual[right_sample]
                        )
                        s_values.append(float(left_time[left_sample]))
                        t_values.append(float(right_time[right_sample]))
                        products.append(product)
                        participant_indices.append(participant_index)
                        if include_mirror:
                            s_values.append(float(right_time[right_sample]))
                            t_values.append(float(left_time[left_sample]))
                            products.append(product)
                            participant_indices.append(participant_index)

    if len(products) < 3:
        repeated = sum(
            int(np.count_nonzero(participant_array == participant) >= 2)
            for participant in unique_participants
        )
        raise SparseNativeError(
            "insufficient_between_covariance_pairs",
            "fewer than three same-participant cross-trial covariance pairs are available",
            details={
                "n_pairs": len(products),
                "n_participants": len(unique_participants),
                "n_repeated_participants": repeated,
            },
        )

    return RawCovariancePairs(
        s=np.asarray(s_values, dtype=float),
        t=np.asarray(t_values, dtype=float),
        products=np.asarray(products, dtype=float),
        curve_index=np.asarray(participant_indices, dtype=int),
        mirrored=bool(include_mirror),
    )


def evaluate_fitted_cross_covariance(
    evaluation_grid: np.ndarray,
    fitted_covariance: np.ndarray,
    left_times: np.ndarray,
    right_times: np.ndarray,
) -> np.ndarray:
    """Evaluate one fitted covariance surface on two native time vectors."""

    grid = np.asarray(evaluation_grid, dtype=float)
    covariance = np.asarray(fitted_covariance, dtype=float)
    left = np.asarray(left_times, dtype=float)
    right = np.asarray(right_times, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError("evaluation_grid must be finite and strictly increasing")
    if covariance.shape != (grid.size, grid.size) or not np.all(np.isfinite(covariance)):
        raise ValueError(
            "fitted_covariance must be finite with shape "
            f"({grid.size}, {grid.size})"
        )
    if left.ndim != 1 or right.ndim != 1:
        raise ValueError("left_times and right_times must be one-dimensional")
    if not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
        raise ValueError("left_times and right_times must be finite")
    if (
        np.any(left < grid[0])
        or np.any(left > grid[-1])
        or np.any(right < grid[0])
        or np.any(right > grid[-1])
    ):
        raise SparseNativeError(
            "native_time_outside_fitted_support",
            "native observation times fall outside fitted covariance support",
            details={
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
                "left_min": None if left.size == 0 else float(np.min(left)),
                "left_max": None if left.size == 0 else float(np.max(left)),
                "right_min": None if right.size == 0 else float(np.min(right)),
                "right_max": None if right.size == 0 else float(np.max(right)),
            },
        )
    if left.size == 0 or right.size == 0:
        return np.empty((left.size, right.size), dtype=float)

    interpolator = RegularGridInterpolator(
        (grid, grid),
        covariance,
        method="linear",
        bounds_error=True,
    )
    left_mesh, right_mesh = np.meshgrid(left, right, indexing="ij")
    points = np.column_stack([left_mesh.ravel(), right_mesh.ravel()])
    return np.asarray(interpolator(points), dtype=float).reshape(
        left.size,
        right.size,
    )


def _validate_eigenpairs(
    eigenvalues: np.ndarray,
    eigenfunctions: np.ndarray,
    grid: np.ndarray,
    *,
    n_components: int,
    level: str,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(eigenvalues, dtype=float)
    functions = np.asarray(eigenfunctions, dtype=float)
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError(f"{level}_components must be an integer")
    if n_components < 1:
        raise ValueError(f"{level}_components must be positive")
    if values.ndim != 1 or functions.ndim != 2:
        raise ValueError(f"{level} eigenpairs have invalid dimensions")
    if functions.shape[1] != grid.size or values.size != functions.shape[0]:
        raise ValueError(f"{level} eigenvalues/eigenfunctions are misaligned")
    if n_components > values.size:
        raise ValueError(f"{level}_components exceeds available eigenpairs")
    if (
        not np.all(np.isfinite(values[:n_components]))
        or np.any(values[:n_components] < 0)
        or not np.all(np.isfinite(functions[:n_components]))
    ):
        raise ValueError(f"retained {level} eigenpairs must be finite and non-negative")
    return values[:n_components].copy(), functions[:n_components].copy()


def sparse_multilevel_blup_scores(
    curve_ids: Sequence[str],
    participant_ids: Sequence[str],
    curve_times: Sequence[np.ndarray],
    curve_values: Sequence[np.ndarray],
    *,
    evaluation_grid: np.ndarray,
    fitted_mean: np.ndarray,
    between_covariance: np.ndarray,
    within_covariance: np.ndarray,
    participant_eigenvalues: np.ndarray,
    participant_eigenfunctions: np.ndarray,
    trial_eigenvalues: np.ndarray,
    trial_eigenfunctions: np.ndarray,
    noise_variance: float,
    participant_components: int,
    trial_components: int,
    score_ridge: float = 0.0,
    condition_limit: float = 1e12,
    min_participant_samples: int = 2,
    failure_action: str = "error",
) -> SparseMultilevelScoreResult:
    """Recover participant and trial scores jointly from the full hierarchy.

    The observation covariance for each participant uses the complete fitted
    between- and within-level covariance surfaces. Retained component counts
    control only the returned score vectors; they do not truncate the
    observation covariance used by the BLUP solve.
    """

    _validate_aligned_sequences(
        curve_times,
        curve_values,
        participant_ids,
        curve_ids,
    )
    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError("evaluation_grid must be finite and strictly increasing")
    mean = np.asarray(fitted_mean, dtype=float)
    between = np.asarray(between_covariance, dtype=float)
    within = np.asarray(within_covariance, dtype=float)
    if mean.shape != (grid.size,) or not np.all(np.isfinite(mean)):
        raise ValueError("fitted_mean must be finite with one value per grid point")
    for name, matrix in (("between_covariance", between), ("within_covariance", within)):
        if matrix.shape != (grid.size, grid.size) or not np.all(np.isfinite(matrix)):
            raise ValueError(
                f"{name} must be finite with shape ({grid.size}, {grid.size})"
            )

    participant_values, participant_functions = _validate_eigenpairs(
        participant_eigenvalues,
        participant_eigenfunctions,
        grid,
        n_components=participant_components,
        level="participant",
    )
    trial_values, trial_functions = _validate_eigenpairs(
        trial_eigenvalues,
        trial_eigenfunctions,
        grid,
        n_components=trial_components,
        level="trial",
    )

    noise_variance = float(noise_variance)
    score_ridge = float(score_ridge)
    condition_limit = float(condition_limit)
    if not np.isfinite(noise_variance) or noise_variance < 0:
        raise ValueError("noise_variance must be finite and non-negative")
    if not np.isfinite(score_ridge) or score_ridge < 0:
        raise ValueError("score_ridge must be finite and non-negative")
    if not np.isfinite(condition_limit) or condition_limit <= 1:
        raise ValueError("condition_limit must be finite and greater than 1")
    if isinstance(min_participant_samples, bool) or not isinstance(
        min_participant_samples, int
    ):
        raise TypeError("min_participant_samples must be an integer")
    if min_participant_samples < 1:
        raise ValueError("min_participant_samples must be positive")
    if failure_action not in {"error", "retain_nan"}:
        raise ValueError("failure_action must be 'error' or 'retain_nan'")

    curve_ids_tuple = tuple(str(value) for value in curve_ids)
    participant_by_curve = np.asarray(
        [str(value) for value in participant_ids],
        dtype=object,
    )
    unique_participants = tuple(pd.unique(participant_by_curve).tolist())
    participant_scores = np.full(
        (len(unique_participants), participant_components),
        np.nan,
        dtype=float,
    )
    trial_scores = np.full(
        (len(curve_ids_tuple), trial_components),
        np.nan,
        dtype=float,
    )
    diagnostic_rows: list[dict[str, Any]] = []
    first_failure: tuple[str, str, dict[str, Any]] | None = None

    for participant_position, participant in enumerate(unique_participants):
        curve_indices = np.flatnonzero(participant_by_curve == participant)
        local_times = [np.asarray(curve_times[index], dtype=float) for index in curve_indices]
        local_values = [np.asarray(curve_values[index], dtype=float) for index in curve_indices]
        counts = [int(time.size) for time in local_times]
        offsets = np.cumsum([0, *counts])
        n_samples = int(offsets[-1])

        status_code = "ok"
        solve_status = "not_attempted"
        condition_number = np.nan
        minimum_eigenvalue = np.nan
        maximum_eigenvalue = np.nan
        solve_relative_residual = np.nan

        if n_samples < min_participant_samples:
            status_code = "participant_too_sparse_for_multilevel_score_system"
        else:
            sigma = np.empty((n_samples, n_samples), dtype=float)
            centered_parts: list[np.ndarray] = []
            for left_position, left_time in enumerate(local_times):
                left_slice = slice(offsets[left_position], offsets[left_position + 1])
                left_mean = evaluate_fitted_function(grid, mean, left_time)
                centered_parts.append(local_values[left_position] - left_mean)
                for right_position, right_time in enumerate(local_times):
                    right_slice = slice(
                        offsets[right_position], offsets[right_position + 1]
                    )
                    block = evaluate_fitted_cross_covariance(
                        grid,
                        between,
                        left_time,
                        right_time,
                    )
                    if left_position == right_position:
                        block = block + evaluate_fitted_cross_covariance(
                            grid,
                            within,
                            left_time,
                            right_time,
                        )
                        block = block + (
                            noise_variance + score_ridge
                        ) * np.eye(left_time.size)
                    sigma[left_slice, right_slice] = block

            sigma = 0.5 * (sigma + sigma.T)
            sigma_eigenvalues = np.linalg.eigvalsh(sigma)
            minimum_eigenvalue = float(np.min(sigma_eigenvalues))
            maximum_eigenvalue = float(np.max(sigma_eigenvalues))
            condition_number = (
                np.inf
                if minimum_eigenvalue <= 0
                else maximum_eigenvalue / minimum_eigenvalue
            )
            if minimum_eigenvalue <= 0:
                status_code = "multilevel_score_covariance_not_positive_definite"
            elif condition_number > condition_limit:
                status_code = "multilevel_score_covariance_ill_conditioned"
            else:
                centered = np.concatenate(centered_parts)
                solved = np.linalg.solve(sigma, centered)
                denominator = max(float(np.linalg.norm(centered)), np.finfo(float).eps)
                solve_relative_residual = float(
                    np.linalg.norm(sigma @ solved - centered) / denominator
                )

                participant_phi = np.vstack(
                    [
                        np.column_stack(
                            [
                                evaluate_fitted_function(
                                    grid,
                                    participant_functions[component],
                                    time,
                                )
                                for component in range(participant_components)
                            ]
                        )
                        for time in local_times
                    ]
                )
                participant_scores[participant_position] = participant_values * (
                    participant_phi.T @ solved
                )

                for local_position, curve_index in enumerate(curve_indices):
                    local_slice = slice(
                        offsets[local_position], offsets[local_position + 1]
                    )
                    time = local_times[local_position]
                    trial_phi = np.column_stack(
                        [
                            evaluate_fitted_function(
                                grid,
                                trial_functions[component],
                                time,
                            )
                            for component in range(trial_components)
                        ]
                    )
                    trial_scores[int(curve_index)] = trial_values * (
                        trial_phi.T @ solved[local_slice]
                    )
                solve_status = "solved"

        row = {
            "participant_id": str(participant),
            "n_trials": int(curve_indices.size),
            "n_samples": n_samples,
            "status_code": status_code,
            "solve_status": solve_status,
            "condition_number": float(condition_number),
            "minimum_eigenvalue": float(minimum_eigenvalue),
            "maximum_eigenvalue": float(maximum_eigenvalue),
            "solve_relative_residual": float(solve_relative_residual),
            "score_ridge": score_ridge,
            "condition_limit": condition_limit,
        }
        diagnostic_rows.append(row)
        if status_code != "ok" and first_failure is None:
            first_failure = (status_code, str(participant), dict(row))

    diagnostics = pd.DataFrame(diagnostic_rows)
    if first_failure is not None and failure_action == "error":
        code, participant, details = first_failure
        raise SparseNativeError(
            code,
            f"sparse multilevel score system failed for participant {participant!r}",
            details={"participant_id": participant, **details},
        )

    return SparseMultilevelScoreResult(
        participant_ids=unique_participants,
        curve_ids=curve_ids_tuple,
        participant_scores=participant_scores,
        trial_scores=trial_scores,
        diagnostics=diagnostics,
    )
