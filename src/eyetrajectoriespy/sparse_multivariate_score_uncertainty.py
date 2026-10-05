"""Conditional uncertainty for native sparse-MFPCA joint-PACE scores.

The uncertainty reported here is conditional on the fitted joint sparse
population objects: covariance operator, eigensystem, measurement-error
covariance, and declared score-system regularization. It does not propagate
uncertainty from estimating or selecting those objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._sparse_multivariate import (
    PlanarCovarianceBlocks,
    _prepare_planar_analysis_views,
    build_joint_score_covariance,
    evaluate_planar_covariance,
    resolve_measurement_error_covariance,
    stack_planar_eigenfunctions,
)
from ._sparse_native import SparseNativeError
from .types import IrregularTrajectorySet, SparseMFPCAResult


_METHOD = "conditional_gaussian_given_fitted_joint_population"


@dataclass(frozen=True)
class SparseMFPCAScoreUncertaintyResult:
    """Conditional Gaussian covariance for native sparse joint-PACE scores.

    Notes
    -----
    These covariances condition on the fitted joint covariance, eigensystem,
    measurement-error covariance, analysis support, and score-system ridge.
    They are not full sampling uncertainty for sparse multivariate FPCA.
    """

    reference: SparseMFPCAResult
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
            diagonal = np.flatnonzero(finite_diag)
            out[index, diagonal, diagonal] = 1.0
        return out


def _native_joint_provenance(
    fit: SparseMFPCAResult,
) -> Mapping[str, Any]:
    if not isinstance(fit, SparseMFPCAResult):
        raise TypeError("fit must be a SparseMFPCAResult")
    if fit.fit_method != "direct_sparse_block_covariance":
        raise ValueError(
            "sparse_mfpca_score_uncertainty requires the native direct "
            "sparse block-covariance fit"
        )
    if fit.score_method != "joint_PACE":
        raise ValueError(
            "sparse_mfpca_score_uncertainty requires joint_PACE scores"
        )
    sparse = fit.provenance.get("sparse_mfpca", {})
    if not isinstance(sparse, Mapping) or sparse.get("backend") != "native":
        raise ValueError(
            "fit provenance does not identify the native sparse MFPCA backend"
        )
    if sparse.get("score_method") != "joint_PACE":
        raise ValueError("fit provenance does not identify joint_PACE scoring")
    if sparse.get("operator_storage_order") != "channel_major":
        raise ValueError("fit has an unsupported joint-operator storage order")
    if sparse.get("score_observation_order") != "time_major_interleaved_xy":
        raise ValueError("fit has an unsupported joint score observation order")
    if sparse.get("rank_k_covariance_used_for_scoring") is not False:
        raise ValueError(
            "fit does not retain the required full-covariance score contract"
        )
    return sparse


def _validate_alignment(
    fit: SparseMFPCAResult,
    trajectories: IrregularTrajectorySet,
) -> tuple[int, int]:
    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if tuple(trajectories.curve_ids) != tuple(fit.curve_ids):
        raise ValueError(
            "trajectories curve_ids and order must exactly match the sparse MFPCA fit"
        )
    if len(fit.dimensions) != 2 or fit.dimensions[0] == fit.dimensions[1]:
        raise ValueError("fit must retain exactly two distinct planar dimensions")
    x_name, y_name = map(str, fit.dimensions)
    try:
        x_index = trajectories.dimension_names.index(x_name)
        y_index = trajectories.dimension_names.index(y_name)
    except ValueError as exc:
        raise KeyError(
            f"Unknown planar dimension in {fit.dimensions!r}"
        ) from exc
    if trajectories.coordinate_system != fit.coordinate_system:
        raise ValueError("trajectory coordinate_system does not match fit")
    if trajectories.time_unit != fit.time_unit:
        raise ValueError("trajectory time_unit does not match fit")

    # A valid sparse-MFPCA fit already passed the covariance-estimation support
    # requirement (at least three curves). Posterior score uncertainty must not
    # re-apply that fit-time population-support rule; it only needs to confirm
    # that the supplied scoring trajectories reproduce the synchronous planar
    # observation contract used by the fitted joint-PACE system.
    for curve_id, values in zip(
        trajectories.curve_ids,
        trajectories.values,
        strict=True,
    ):
        x = np.asarray(values[:, x_index], dtype=float)
        y = np.asarray(values[:, y_index], dtype=float)
        finite_x = np.isfinite(x)
        finite_y = np.isfinite(y)
        coordinate_mismatch = finite_x != finite_y
        if np.any(coordinate_mismatch):
            indices = np.flatnonzero(coordinate_mismatch)
            raise SparseNativeError(
                "coordinate_specific_missingness_unsupported",
                "x and y must be jointly observed at every retained sparse timestamp",
                details={
                    "curve_id": str(curve_id),
                    "n_coordinate_specific_missing": int(indices.size),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
        jointly_nonfinite = ~(finite_x & finite_y)
        if np.any(jointly_nonfinite):
            indices = np.flatnonzero(jointly_nonfinite)
            raise SparseNativeError(
                "nonfinite_sparse_planar_observation",
                "absent planar observations must be represented by absent samples",
                details={
                    "curve_id": str(curve_id),
                    "n_nonfinite_joint_samples": int(indices.size),
                    "sample_indices": indices.tolist(),
                    "dimensions": [x_name, y_name],
                },
            )
    return x_index, y_index


def _required_population_arrays(
    fit: SparseMFPCAResult,
) -> tuple[
    np.ndarray,
    PlanarCovarianceBlocks,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    grid = np.asarray(fit.evaluation_grid, dtype=float)
    eigenvalues = np.asarray(fit.eigenvalues, dtype=float)
    eigenfunctions_public = np.asarray(fit.eigenfunctions, dtype=float)
    measurement_error = np.asarray(
        fit.measurement_error_covariance,
        dtype=float,
    )
    if grid.ndim != 1 or grid.size < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("fit evaluation grid is invalid")
    if eigenvalues.ndim != 1 or eigenvalues.size < fit.n_components:
        raise ValueError("fit eigenvalues do not cover retained components")
    if not np.all(np.isfinite(eigenvalues[: fit.n_components])):
        raise ValueError("retained fit eigenvalues must be finite")
    if np.any(eigenvalues[: fit.n_components] < 0):
        raise ValueError("retained fit eigenvalues must be non-negative")
    if (
        eigenfunctions_public.ndim != 3
        or eigenfunctions_public.shape[0] < fit.n_components
        or eigenfunctions_public.shape[1] != grid.size
        or eigenfunctions_public.shape[2] != 2
    ):
        raise ValueError(
            "fit eigenfunctions must align with retained components, grid, "
            "and two planar dimensions"
        )
    expected_shape = (grid.size, grid.size)
    block_values = {
        "cxx": np.asarray(fit.covariance_cxx, dtype=float),
        "cxy": np.asarray(fit.covariance_cxy, dtype=float),
        "cyx": np.asarray(fit.covariance_cyx, dtype=float),
        "cyy": np.asarray(fit.covariance_cyy, dtype=float),
    }
    for name, value in block_values.items():
        if value.shape != expected_shape or not np.all(np.isfinite(value)):
            raise ValueError(
                f"fit covariance_{name} must be finite with shape {expected_shape}"
            )
    if not np.allclose(
        block_values["cyx"],
        block_values["cxy"].T,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise ValueError("fit covariance_cyx must equal covariance_cxy.T")
    resolved_error = resolve_measurement_error_covariance(
        "fixed_matrix",
        measurement_error_covariance=measurement_error,
    )
    blocks = PlanarCovarianceBlocks(
        cxx=block_values["cxx"],
        cxy=block_values["cxy"],
        cyx=block_values["cyx"],
        cyy=block_values["cyy"],
    )
    eigenfunctions_private = np.transpose(
        eigenfunctions_public[: fit.n_components],
        (0, 2, 1),
    )
    return (
        grid,
        blocks,
        eigenvalues[: fit.n_components].copy(),
        eigenfunctions_private,
        resolved_error.covariance,
    )


def _effective_times(
    fit: SparseMFPCAResult,
    trajectories: IrregularTrajectorySet,
    sparse_provenance: Mapping[str, Any],
    *,
    x_index: int,
    y_index: int,
) -> tuple[np.ndarray, ...]:
    action = sparse_provenance.get("analysis_support_action", "error")
    if action not in {"error", "restrict"}:
        raise ValueError("fit has an unsupported analysis-support policy")
    curve_times, _, _, support = _prepare_planar_analysis_views(
        trajectories,
        x_index=x_index,
        y_index=y_index,
        evaluation_grid=np.asarray(fit.evaluation_grid, dtype=float),
        action=action,
    )
    actual_counts = tuple(int(time.size) for time in curve_times)
    fitted_counts = sparse_provenance.get("analysis_sample_counts")
    if fitted_counts is not None:
        expected_counts = tuple(int(value) for value in fitted_counts)
        if actual_counts != expected_counts:
            raise ValueError(
                "trajectories do not reproduce the effective native time-point "
                "counts used by the sparse MFPCA fit"
            )
    support_counts = tuple(
        int(value) for value in support["analysis_sample_counts"]
    )
    if actual_counts != support_counts:
        raise RuntimeError(
            "internal support invariant failed for joint score uncertainty"
        )
    return tuple(np.asarray(time, dtype=float).copy() for time in curve_times)


def _fit_score_statuses(fit: SparseMFPCAResult) -> dict[str, str]:
    diagnostics = fit.score_diagnostics
    if not isinstance(diagnostics, pd.DataFrame) or diagnostics.empty:
        return {}
    if "curve_id" not in diagnostics or "status_code" not in diagnostics:
        return {}
    return {
        str(row.curve_id): str(row.status_code)
        for row in diagnostics[["curve_id", "status_code"]].itertuples(index=False)
    }


def sparse_mfpca_score_uncertainty(
    fit: SparseMFPCAResult,
    trajectories: IrregularTrajectorySet,
    *,
    condition_limit: float | None = None,
    failure_action: str = "error",
) -> SparseMFPCAScoreUncertaintyResult:
    """Compute conditional covariance of native sparse joint-PACE scores.

    For the retained joint score vector ``xi_i`` this evaluates

    ``Lambda - Lambda Phi_i.T Sigma_i^{-1} Phi_i Lambda``

    using exactly the full fitted joint latent covariance, two-channel
    measurement-error covariance, native-time observation order, and score
    ridge used by ``joint_pace_scores``. Population-estimation uncertainty is
    deliberately excluded.
    """

    sparse = _native_joint_provenance(fit)
    x_index, y_index = _validate_alignment(fit, trajectories)
    if failure_action not in {"error", "retain_nan"}:
        raise ValueError("failure_action must be 'error' or 'retain_nan'")

    (
        grid,
        covariance_blocks,
        retained_values,
        retained_functions,
        measurement_error,
    ) = _required_population_arrays(fit)
    n_components = int(fit.n_components)

    score_ridge = float(sparse.get("score_ridge", 0.0))
    if not np.isfinite(score_ridge) or score_ridge < 0:
        raise ValueError("fit score_ridge must be finite and non-negative")
    fitted_condition_limit = float(
        sparse.get("score_condition_limit", sparse.get("condition_limit", 1e12))
    )
    if condition_limit is None:
        selected_condition_limit = fitted_condition_limit
        condition_limit_source = "fitted_score_condition_limit"
    else:
        selected_condition_limit = float(condition_limit)
        condition_limit_source = "explicit_override"
    if not np.isfinite(selected_condition_limit) or selected_condition_limit <= 1:
        raise ValueError("condition_limit must be finite and greater than 1")

    min_time_points = int(sparse.get("min_score_time_points", 2))
    if min_time_points < 1:
        raise ValueError("fit min_score_time_points must be positive")
    times = _effective_times(
        fit,
        trajectories,
        sparse,
        x_index=x_index,
        y_index=y_index,
    )
    fit_statuses = _fit_score_statuses(fit)

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

        if time.size < min_time_points:
            status_code = "curve_too_sparse_for_joint_score_system"
        else:
            try:
                native_covariance = evaluate_planar_covariance(
                    grid,
                    covariance_blocks,
                    time,
                    order="time_major",
                )
                sigma = build_joint_score_covariance(
                    native_covariance,
                    measurement_error,
                    score_ridge=score_ridge,
                )
                sigma_eigenvalues = np.linalg.eigvalsh(sigma)
                minimum_eigenvalue = float(np.min(sigma_eigenvalues))
                maximum_eigenvalue = float(np.max(sigma_eigenvalues))
                condition_number = (
                    np.inf
                    if minimum_eigenvalue <= 0
                    else maximum_eigenvalue / minimum_eigenvalue
                )
                if minimum_eigenvalue <= 0:
                    status_code = "joint_score_covariance_not_positive_definite"
                elif condition_number > selected_condition_limit:
                    status_code = "joint_score_covariance_ill_conditioned"
                else:
                    phi_i = stack_planar_eigenfunctions(
                        grid,
                        retained_functions,
                        time,
                        n_components=n_components,
                    )
                    rhs = phi_i @ prior_covariance
                    solved = np.linalg.solve(sigma, rhs)
                    denominator = max(1.0, float(np.linalg.norm(rhs)))
                    solve_relative_residual = float(
                        np.linalg.norm(sigma @ solved - rhs) / denominator
                    )
                    posterior = prior_covariance - rhs.T @ solved
                    posterior = 0.5 * (posterior + posterior.T)
                    posterior_eigenvalues = np.linalg.eigvalsh(posterior)
                    posterior_minimum_eigenvalue = float(
                        np.min(posterior_eigenvalues)
                    )
                    if posterior_minimum_eigenvalue < -posterior_psd_tolerance:
                        status_code = "conditional_joint_score_covariance_not_psd"
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
            except SparseNativeError as exc:
                status_code = exc.code
            except np.linalg.LinAlgError:
                status_code = "joint_score_covariance_solve_failed"

        row = {
            "curve_id": str(curve_id),
            "n_time_points": int(time.size),
            "n_planar_observations": int(2 * time.size),
            "status_code": status_code,
            "fit_score_status": fit_statuses.get(str(curve_id), "unknown"),
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
            "observation_order": "time_major_interleaved_xy",
        }
        rows.append(row)
        if status_code != "ok" and first_failure is None:
            first_failure = (status_code, str(curve_id), dict(row))

    diagnostics = pd.DataFrame(rows)
    if first_failure is not None and failure_action == "error":
        code, curve_id, details = first_failure
        raise SparseNativeError(
            code,
            f"conditional joint-PACE uncertainty failed for curve {curve_id!r}",
            details={
                **details,
                "all_curve_diagnostics": diagnostics.to_dict(orient="records"),
            },
        )

    provenance = {
        "method": _METHOD,
        "covariance_source": (
            "full_fitted_joint_covariance_plus_measurement_error_and_declared_score_ridge"
        ),
        "fitted_covariance_source": (
            "SparseMFPCAResult.covariance_cxx/cxy/cyx/cyy"
        ),
        "fitted_measurement_error_source": (
            "SparseMFPCAResult.measurement_error_covariance"
        ),
        "eigensystem_source": (
            "SparseMFPCAResult.eigenvalues_and_eigenfunctions"
        ),
        "operator_storage_order": "channel_major",
        "score_observation_order": "time_major_interleaved_xy",
        "ordering_permutation_applied": True,
        "native_observation_times": True,
        "raw_sparse_trajectory_interpolation_performed": False,
        "rank_k_covariance_used_for_uncertainty": False,
        "score_ridge": score_ridge,
        "condition_limit": selected_condition_limit,
        "condition_limit_source": condition_limit_source,
        "failure_action": failure_action,
        "posterior_psd_tolerance": posterior_psd_tolerance,
        "population_estimation_uncertainty_included": False,
        "mean_estimation_uncertainty_included": False,
        "covariance_estimation_uncertainty_included": False,
        "eigensystem_estimation_uncertainty_included": False,
        "measurement_error_specification_uncertainty_included": False,
        "bandwidth_uncertainty_included": False,
        "asynchronous_channel_grids_supported": False,
        "interpretation": (
            "conditional on fitted joint covariance/eigensystem, measurement-error "
            "covariance, and score regularization; excludes population-estimation "
            "and bandwidth uncertainty"
        ),
    }
    return SparseMFPCAScoreUncertaintyResult(
        reference=fit,
        curve_ids=tuple(fit.curve_ids),
        covariance=covariance_out,
        standard_errors=standard_errors,
        diagnostics=diagnostics,
        n_components=n_components,
        provenance=provenance,
    )


def sparse_mfpca_score_uncertainty_frame(
    result: SparseMFPCAScoreUncertaintyResult,
) -> pd.DataFrame:
    """Return one tidy row per curve and retained joint score component."""

    if not isinstance(result, SparseMFPCAScoreUncertaintyResult):
        raise TypeError("result must be a SparseMFPCAScoreUncertaintyResult")
    rows: list[dict[str, Any]] = []
    diagnostics = result.diagnostics.set_index("curve_id", drop=False)
    for curve_index, curve_id in enumerate(result.curve_ids):
        diagnostic = diagnostics.loc[str(curve_id)]
        for component in range(result.n_components):
            variance = result.covariance[curve_index, component, component]
            rows.append(
                {
                    "curve_id": str(curve_id),
                    "component": component + 1,
                    "score": float(
                        result.reference.scores[curve_index, component]
                    ),
                    "conditional_variance": float(variance),
                    "conditional_se": float(
                        result.standard_errors[curve_index, component]
                    ),
                    "status_code": str(diagnostic["status_code"]),
                    "fit_score_status": str(diagnostic["fit_score_status"]),
                    "condition_number": float(
                        diagnostic["condition_number"]
                    ),
                    "method": result.method,
                }
            )
    return pd.DataFrame(rows)


def sparse_mfpca_score_uncertainty_reporting_text(
    result: SparseMFPCAScoreUncertaintyResult,
    *,
    digits: int = 3,
) -> str:
    """Generate conservative manuscript-ready conditional-uncertainty text."""

    if not isinstance(result, SparseMFPCAScoreUncertaintyResult):
        raise TypeError("result must be a SparseMFPCAScoreUncertaintyResult")
    if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
        raise ValueError("digits must be a non-negative integer")
    status = result.diagnostics["status_code"].astype(str).to_numpy()
    solved = int(np.count_nonzero(status == "ok"))
    failed = int(status.size - solved)
    finite_se = result.standard_errors[np.isfinite(result.standard_errors)]
    median_se = float(np.median(finite_se)) if finite_se.size else np.nan
    return (
        "Conditional joint-PACE score uncertainty was computed for "
        f"{len(result.curve_ids)} curve(s) and {result.n_components} retained "
        "joint component(s) using the full fitted planar covariance, declared "
        "measurement-error covariance, native observation times, and the fitted "
        f"score ridge. {solved} curve(s) were solved and {failed} failure(s) "
        "were retained under the declared failure policy; the median finite "
        f"conditional score SE was {median_se:.{digits}f}. These covariances "
        "condition on the fitted joint population objects and do not include "
        "uncertainty from estimating the mean, covariance, eigensystem, "
        "measurement-error specification, or smoothing bandwidths."
    )
