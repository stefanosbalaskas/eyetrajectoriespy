"""Conditional uncertainty for native sparse-FPCA PACE scores.

The uncertainty reported here is conditional on the fitted sparse population
objects (mean, covariance surface, eigensystem, and measurement-error
variance). It does not propagate uncertainty from estimating those objects.
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


_METHOD = "conditional_gaussian_given_fitted_population"


@dataclass(frozen=True)
class SparseFPCAScoreUncertaintyResult:
    """Conditional Gaussian covariance for native sparse PACE scores.

    Notes
    -----
    These covariances condition on the fitted mean, covariance surface,
    eigensystem, measurement-error variance, and declared score-system
    regularization. They are not full sampling uncertainty for sparse FPCA.
    """

    reference: SparseFPCAResult
    curve_ids: tuple[str, ...]
    covariance: np.ndarray
    standard_errors: np.ndarray
    diagnostics: pd.DataFrame
    n_components: int
    method: str = _METHOD
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @property
    def correlations(self) -> np.ndarray:
        """Return per-curve conditional score correlation matrices."""

        out = np.full_like(self.covariance, np.nan, dtype=float)
        for index in range(len(self.curve_ids)):
            covariance = self.covariance[index]
            standard_errors = self.standard_errors[index]
            if not np.all(np.isfinite(covariance)):
                continue
            denominator = np.outer(standard_errors, standard_errors)
            np.divide(
                covariance,
                denominator,
                out=out[index],
                where=denominator > 0,
            )
            zero = standard_errors == 0
            for component in np.flatnonzero(zero):
                out[index, component, component] = 1.0
            finite_diag = np.isfinite(standard_errors) & ~zero
            diag = np.flatnonzero(finite_diag)
            out[index, diag, diag] = 1.0
        return out


def _native_sparse_provenance(fit: SparseFPCAResult) -> Mapping[str, Any]:
    if not isinstance(fit, SparseFPCAResult):
        raise TypeError("fit must be a SparseFPCAResult")
    if fit.fit_method != "native_covariance":
        raise ValueError(
            "sparse_fpca_score_uncertainty requires a native sparse FPCA fit"
        )
    sparse = fit.provenance.get("sparse_fpca", {})
    if not isinstance(sparse, Mapping) or sparse.get("backend") != "native":
        raise ValueError(
            "fit provenance does not identify the native sparse FPCA backend"
        )
    return sparse


def _effective_times(
    fit: SparseFPCAResult,
    trajectories: IrregularTrajectorySet,
    sparse_provenance: Mapping[str, Any],
) -> tuple[np.ndarray, ...]:
    if fit.evaluation_grid is None:
        raise ValueError("fit does not retain an evaluation grid")
    grid = np.asarray(fit.evaluation_grid, dtype=float)
    if grid.ndim != 1 or grid.size < 2:
        raise ValueError("fit evaluation grid is invalid")

    action = sparse_provenance.get("analysis_support_action", "error")
    if action not in {"error", "restrict"}:
        raise ValueError("fit has an unsupported analysis-support policy")

    effective: list[np.ndarray] = []
    outside_counts: list[int] = []
    for time in trajectories.time:
        time_array = np.asarray(time, dtype=float)
        mask = (time_array >= grid[0]) & (time_array <= grid[-1])
        outside_counts.append(int(np.count_nonzero(~mask)))
        if action == "restrict":
            effective.append(time_array[mask].copy())
        elif np.any(~mask):
            raise SparseNativeError(
                "observations_outside_analysis_support",
                "observations lie outside the fitted evaluation-grid support",
                details={
                    "analysis_support": [float(grid[0]), float(grid[-1])],
                    "outside_counts_by_curve": outside_counts,
                },
            )
        else:
            effective.append(time_array.copy())
    return tuple(effective)


def _validate_alignment(
    fit: SparseFPCAResult,
    trajectories: IrregularTrajectorySet,
) -> None:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if tuple(trajectories.curve_ids) != tuple(fit.curve_ids):
        raise ValueError(
            "trajectories curve_ids and order must exactly match the sparse FPCA fit"
        )
    if fit.dimension not in trajectories.dimension_names:
        raise ValueError(
            f"fit dimension {fit.dimension!r} is absent from trajectories"
        )
    if trajectories.coordinate_system != fit.coordinate_system:
        raise ValueError("trajectory coordinate_system does not match fit")
    if trajectories.time_unit != fit.time_unit:
        raise ValueError("trajectory time_unit does not match fit")


def _required_population_arrays(
    fit: SparseFPCAResult,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    if fit.evaluation_grid is None:
        raise ValueError("fit does not retain an evaluation grid")
    if fit.covariance is None:
        raise ValueError("fit does not retain its fitted covariance")
    if fit.eigenfunctions is None:
        raise ValueError("fit does not retain fitted eigenfunctions")
    if fit.noise_variance is None:
        raise ValueError("fit does not retain measurement-error variance")

    grid = np.asarray(fit.evaluation_grid, dtype=float)
    covariance = np.asarray(fit.covariance, dtype=float)
    eigenvalues = np.asarray(fit.eigenvalues, dtype=float)
    eigenfunctions = np.asarray(fit.eigenfunctions, dtype=float)
    noise_variance = float(fit.noise_variance)

    if grid.ndim != 1 or grid.size < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("fit evaluation grid is invalid")
    if covariance.shape != (grid.size, grid.size):
        raise ValueError("fit covariance shape does not match evaluation grid")
    if eigenfunctions.ndim != 2 or eigenfunctions.shape[1] != grid.size:
        raise ValueError("fit eigenfunctions do not align with evaluation grid")
    if eigenvalues.ndim != 1 or eigenvalues.size < fit.n_components:
        raise ValueError("fit eigenvalues do not cover retained components")
    if eigenfunctions.shape[0] < fit.n_components:
        raise ValueError("fit eigenfunctions do not cover retained components")
    if not np.all(np.isfinite(eigenvalues[: fit.n_components])):
        raise ValueError("retained fit eigenvalues must be finite")
    if np.any(eigenvalues[: fit.n_components] < 0):
        raise ValueError("retained fit eigenvalues must be non-negative")
    if not np.isfinite(noise_variance) or noise_variance < 0:
        raise ValueError("fit noise_variance must be finite and non-negative")
    return grid, covariance, eigenvalues, eigenfunctions, noise_variance


def sparse_fpca_score_uncertainty(
    fit: SparseFPCAResult,
    trajectories: IrregularTrajectorySet,
    *,
    condition_limit: float | None = None,
    failure_action: str = "error",
) -> SparseFPCAScoreUncertaintyResult:
    """Compute conditional covariance of native sparse PACE scores.

    For retained score vector ``xi_i`` and native observation times ``T_i``,
    this evaluates

    ``Lambda - Lambda Phi_i.T Sigma_i^{-1} Phi_i Lambda``

    using the same full fitted covariance-plus-noise system as native PACE
    scoring. The calculation is conditional on the fitted population objects;
    population-estimation uncertainty is deliberately excluded.
    """

    sparse = _native_sparse_provenance(fit)
    _validate_alignment(fit, trajectories)
    if failure_action not in {"error", "retain_nan"}:
        raise ValueError("failure_action must be 'error' or 'retain_nan'")

    grid, fitted_covariance, eigenvalues, eigenfunctions, noise_variance = (
        _required_population_arrays(fit)
    )
    n_components = int(fit.n_components)
    retained_values = eigenvalues[:n_components]
    retained_functions = eigenfunctions[:n_components]

    score_ridge = float(sparse.get("score_ridge", 0.0))
    if not np.isfinite(score_ridge) or score_ridge < 0:
        raise ValueError("fit score_ridge must be finite and non-negative")

    fitted_condition_limit = float(sparse.get("score_condition_limit", 1e12))
    if condition_limit is None:
        selected_condition_limit = fitted_condition_limit
        condition_limit_source = "fitted_score_condition_limit"
    else:
        selected_condition_limit = float(condition_limit)
        condition_limit_source = "explicit_override"
    if not np.isfinite(selected_condition_limit) or selected_condition_limit <= 1:
        raise ValueError("condition_limit must be finite and greater than 1")

    min_score_samples = int(sparse.get("min_score_samples", 2))
    if min_score_samples < 1:
        raise ValueError("fit min_score_samples must be positive")

    times = _effective_times(fit, trajectories, sparse)
    fitted_sample_counts = sparse.get("sample_counts")
    if fitted_sample_counts is not None:
        expected_counts = tuple(int(value) for value in fitted_sample_counts)
        actual_counts = tuple(int(time.size) for time in times)
        if expected_counts != actual_counts:
            raise ValueError(
                "trajectories do not reproduce the effective sample counts used by the fit"
            )

    covariance_out = np.full(
        (len(fit.curve_ids), n_components, n_components),
        np.nan,
        dtype=float,
    )
    standard_errors = np.full(
        (len(fit.curve_ids), n_components),
        np.nan,
        dtype=float,
    )
    prior_covariance = np.diag(retained_values)
    posterior_psd_tolerance = 1e-10 * max(
        1.0,
        float(np.max(np.abs(retained_values))),
    )

    rows: list[dict[str, Any]] = []
    first_failure: tuple[str, str, dict[str, Any]] | None = None

    for index, (curve_id, time) in enumerate(
        zip(fit.curve_ids, times, strict=True)
    ):
        status_code = "ok"
        solve_status = "not_attempted"
        condition_number = np.nan
        minimum_eigenvalue = np.nan
        maximum_eigenvalue = np.nan
        posterior_minimum_eigenvalue = np.nan
        solve_relative_residual = np.nan
        posterior_psd_repair_applied = False

        if time.size < min_score_samples:
            status_code = "curve_too_sparse_for_score_system"
        else:
            covariance_i = evaluate_fitted_covariance(
                grid,
                fitted_covariance,
                time,
            )
            sigma_i = covariance_i + (
                noise_variance + score_ridge
            ) * np.eye(time.size)
            sigma_i = 0.5 * (sigma_i + sigma_i.T)
            sigma_eigenvalues = np.linalg.eigvalsh(sigma_i)
            minimum_eigenvalue = float(np.min(sigma_eigenvalues))
            maximum_eigenvalue = float(np.max(sigma_eigenvalues))
            condition_number = (
                np.inf
                if minimum_eigenvalue <= 0
                else maximum_eigenvalue / minimum_eigenvalue
            )

            if minimum_eigenvalue <= 0:
                status_code = "score_covariance_not_positive_definite"
            elif condition_number > selected_condition_limit:
                status_code = "score_covariance_ill_conditioned"
            else:
                phi_i = np.column_stack(
                    [
                        evaluate_fitted_function(
                            grid,
                            retained_functions[component],
                            time,
                        )
                        for component in range(n_components)
                    ]
                )
                rhs = phi_i @ prior_covariance
                solved = np.linalg.solve(sigma_i, rhs)
                denominator = max(1.0, float(np.linalg.norm(rhs)))
                solve_relative_residual = float(
                    np.linalg.norm(sigma_i @ solved - rhs) / denominator
                )
                posterior = prior_covariance - rhs.T @ solved
                posterior = 0.5 * (posterior + posterior.T)
                posterior_eigenvalues = np.linalg.eigvalsh(posterior)
                posterior_minimum_eigenvalue = float(
                    np.min(posterior_eigenvalues)
                )
                if posterior_minimum_eigenvalue < -posterior_psd_tolerance:
                    status_code = "conditional_score_covariance_not_psd"
                else:
                    if posterior_minimum_eigenvalue < 0:
                        values, vectors = np.linalg.eigh(posterior)
                        values = np.maximum(values, 0.0)
                        posterior = (vectors * values) @ vectors.T
                        posterior = 0.5 * (posterior + posterior.T)
                        posterior_psd_repair_applied = True
                    covariance_out[index] = posterior
                    standard_errors[index] = np.sqrt(
                        np.maximum(np.diag(posterior), 0.0)
                    )
                    solve_status = "solved"

        row = {
            "curve_id": str(curve_id),
            "n_samples": int(time.size),
            "status_code": status_code,
            "solve_status": solve_status,
            "condition_number": float(condition_number),
            "minimum_eigenvalue": float(minimum_eigenvalue),
            "maximum_eigenvalue": float(maximum_eigenvalue),
            "posterior_minimum_eigenvalue": float(
                posterior_minimum_eigenvalue
            ),
            "posterior_psd_repair_applied": bool(
                posterior_psd_repair_applied
            ),
            "solve_relative_residual": float(solve_relative_residual),
            "score_ridge": score_ridge,
            "condition_limit": selected_condition_limit,
        }
        rows.append(row)
        if status_code != "ok" and first_failure is None:
            first_failure = (status_code, str(curve_id), dict(row))

    diagnostics = pd.DataFrame(rows)
    if first_failure is not None and failure_action == "error":
        code, curve_id, details = first_failure
        raise SparseNativeError(
            code,
            f"conditional PACE uncertainty system failed for curve {curve_id!r}",
            details={
                **details,
                "all_curve_diagnostics": diagnostics.to_dict(orient="records"),
            },
        )

    provenance = {
        "method": _METHOD,
        "covariance_source": "full_fitted_covariance_plus_noise_and_declared_score_ridge",
        "fitted_covariance_source": "SparseFPCAResult.covariance",
        "fitted_noise_source": "SparseFPCAResult.noise_variance",
        "eigensystem_source": "SparseFPCAResult.eigenvalues_and_eigenfunctions",
        "native_observation_times": True,
        "raw_sparse_trajectory_interpolation_performed": False,
        "score_ridge": score_ridge,
        "condition_limit": selected_condition_limit,
        "condition_limit_source": condition_limit_source,
        "failure_action": failure_action,
        "posterior_psd_tolerance": posterior_psd_tolerance,
        "population_estimation_uncertainty_included": False,
        "mean_estimation_uncertainty_included": False,
        "covariance_estimation_uncertainty_included": False,
        "eigensystem_estimation_uncertainty_included": False,
        "noise_variance_estimation_uncertainty_included": False,
        "bandwidth_uncertainty_included": False,
        "interpretation": (
            "conditional on fitted mean/covariance/eigensystem and measurement-error "
            "variance; excludes population-estimation uncertainty"
        ),
    }
    return SparseFPCAScoreUncertaintyResult(
        reference=fit,
        curve_ids=tuple(fit.curve_ids),
        covariance=covariance_out,
        standard_errors=standard_errors,
        diagnostics=diagnostics,
        n_components=n_components,
        provenance=provenance,
    )


def sparse_fpca_score_uncertainty_frame(
    result: SparseFPCAScoreUncertaintyResult,
) -> pd.DataFrame:
    """Return one tidy row per curve and retained score component."""

    if not isinstance(result, SparseFPCAScoreUncertaintyResult):
        raise TypeError("result must be a SparseFPCAScoreUncertaintyResult")
    diagnostic = result.diagnostics.set_index("curve_id", drop=False)
    rows: list[dict[str, Any]] = []
    for curve_index, curve_id in enumerate(result.curve_ids):
        curve_diagnostic = diagnostic.loc[str(curve_id)]
        for component in range(result.n_components):
            rows.append(
                {
                    "curve_id": str(curve_id),
                    "component": component + 1,
                    "conditional_variance": float(
                        result.covariance[curve_index, component, component]
                    ),
                    "conditional_standard_error": float(
                        result.standard_errors[curve_index, component]
                    ),
                    "status_code": str(curve_diagnostic["status_code"]),
                    "condition_number": float(
                        curve_diagnostic["condition_number"]
                    ),
                    "method": result.method,
                }
            )
    return pd.DataFrame(rows)
