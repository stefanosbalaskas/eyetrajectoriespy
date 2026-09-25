"""Nested participant/trial functional random effects for Gaussian trajectories."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.optimize import minimize

from .function_on_scalar import _validate_design_alignment
from .types import FunctionalMixedEffectsResult, TrajectorySet
from .validation import validate_trajectory_set
from .functional_mixed_effects import (
    _bspline_basis,
    _fixed_effect_design,
    _random_effect_design,
    _validate_dimension,
    _validate_participants,
    _validate_random_slope,
)


def _validate_trial_structure(
    trajectories: TrajectorySet,
    *,
    participant_column: str,
    trial_column: str,
    curve_participants: np.ndarray,
    participant_ids: tuple[str, ...],
) -> tuple[np.ndarray, tuple[str, ...]]:
    if not isinstance(trial_column, str) or not trial_column:
        raise TypeError("trial_column must be a non-empty string")
    if trial_column == participant_column:
        raise ValueError("trial_column must differ from participant_column")
    if trial_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain trial column {trial_column!r}"
        )
    series = trajectories.metadata[trial_column]
    if series.isna().any():
        raise ValueError("trial_column contains missing values")
    source_trials = series.astype(str).to_numpy()

    duplicate_pairs = pd.DataFrame(
        {
            "participant": curve_participants,
            "trial": source_trials,
        }
    ).duplicated(["participant", "trial"], keep=False)
    if bool(duplicate_pairs.any()):
        duplicate_rows = np.flatnonzero(duplicate_pairs.to_numpy())
        preview = ", ".join(
            (
                f"({curve_participants[index]!r}, "
                f"{source_trials[index]!r})"
            )
            for index in duplicate_rows[:5]
        )
        suffix = "" if duplicate_rows.size <= 5 else ", ..."
        raise ValueError(
            "trial identifiers must be unique within participant under the "
            "0.48 one-curve-per-trial contract; duplicated participant/trial "
            f"pairs include {preview}{suffix}"
        )

    for participant_id in participant_ids:
        n_trials = int(np.count_nonzero(curve_participants == participant_id))
        if n_trials < 2:
            raise ValueError(
                "trial functional random effects require at least two observed "
                "trials for every participant so participant and trial "
                "functional covariance components are separable; "
                f"participant {participant_id!r} has {n_trials}"
            )

    composite = tuple(
        f"{participant_id}::{trial_id}"
        for participant_id, trial_id in zip(
            curve_participants,
            source_trials,
            strict=True,
        )
    )
    return source_trials, composite


def _covariance_parameter_count(dimension: int) -> int:
    return dimension * (dimension + 1) // 2


def _pack_covariance_cholesky(covariance: np.ndarray) -> np.ndarray:
    chol = np.linalg.cholesky(np.asarray(covariance, dtype=float))
    values: list[float] = []
    for row in range(chol.shape[0]):
        for column in range(row + 1):
            if row == column:
                values.append(float(np.log(chol[row, column])))
            else:
                values.append(float(chol[row, column]))
    return np.asarray(values, dtype=float)


def _unpack_covariance_cholesky(
    values: np.ndarray,
    dimension: int,
) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    expected = _covariance_parameter_count(dimension)
    if values.size != expected:
        raise ValueError("unexpected Cholesky parameter count")
    chol = np.zeros((dimension, dimension), dtype=float)
    index = 0
    for row in range(dimension):
        for column in range(row + 1):
            value = float(values[index])
            chol[row, column] = np.exp(value) if row == column else value
            index += 1
    covariance = chol @ chol.T
    if not np.all(np.isfinite(covariance)):
        raise FloatingPointError("non-finite covariance")
    return covariance


def _covariance_diagnostics(
    covariance: np.ndarray,
) -> tuple[np.ndarray, float, bool, bool, float]:
    covariance = np.asarray(covariance, dtype=float)
    if not np.all(np.isfinite(covariance)):
        raise RuntimeError("fitted covariance contains non-finite values")
    if not np.allclose(
        covariance,
        covariance.T,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise RuntimeError("fitted covariance is not symmetric")

    eigenvalues = np.linalg.eigvalsh(covariance)
    scale = max(1.0, float(np.max(np.abs(covariance))))
    if float(np.min(eigenvalues)) < -1e-10 * scale:
        raise RuntimeError("fitted covariance is not positive semidefinite")

    boundary = bool(float(np.min(eigenvalues)) <= 1e-8 * scale)
    largest = float(np.max(np.abs(eigenvalues)))
    singular_tolerance = max(
        np.finfo(float).eps * max(1.0, largest),
        1e-14,
    )
    singular = bool(float(np.min(eigenvalues)) <= singular_tolerance)
    if float(np.min(eigenvalues)) <= 0.0:
        condition_number = float("inf")
    else:
        condition_number = float(
            np.max(eigenvalues) / np.min(eigenvalues)
        )
    return eigenvalues, condition_number, boundary, singular, scale


def _regular_grid_summary(
    time: np.ndarray,
) -> tuple[bool, float | None]:
    time = np.asarray(time, dtype=float)
    delta = np.diff(time)
    if delta.size == 0 or np.any(delta <= 0):
        return False, None
    reference = float(delta[0])
    regular = bool(
        np.allclose(
            delta,
            reference,
            rtol=1e-8,
            atol=max(1e-12, abs(reference) * 1e-10),
        )
    )
    return regular, reference if regular else None


def _residual_correlation_spec(
    residual_correlation: str,
    time: np.ndarray,
) -> dict[str, object]:
    if not isinstance(residual_correlation, str) or not residual_correlation:
        raise TypeError("residual_correlation must be a non-empty string")
    family = residual_correlation.lower().strip()
    if family not in {"iid", "exponential", "ar1"}:
        raise ValueError(
            "residual_correlation must be 'iid', 'exponential', or 'ar1'"
        )

    time = np.asarray(time, dtype=float)
    regular, interval = _regular_grid_summary(time)
    if family == "ar1" and not regular:
        raise ValueError(
            "residual_correlation='ar1' requires an equally spaced common "
            "time grid because AR(1) lag is defined in index steps; use "
            "'exponential' for physical-time correlation on irregular grids"
        )

    positive_delta = np.diff(time)
    positive_delta = positive_delta[positive_delta > 0]
    if positive_delta.size == 0:
        raise ValueError(
            "residual correlation requires at least two strictly increasing "
            "time points"
        )
    min_delta = float(np.min(positive_delta))
    span = float(time[-1] - time[0])

    if family == "exponential":
        lower = max(min_delta * 1e-4, np.finfo(float).tiny)
        upper = max(span * 1e4, lower * 10.0)
        return {
            "family": family,
            "parameter_name": "phi",
            "parameter_unit": None,
            "parameter_bounds": (lower, upper),
            "transformed_bounds": (float(np.log(lower)), float(np.log(upper))),
            "grid_regular": regular,
            "grid_interval": interval,
        }
    if family == "ar1":
        transformed_bounds = (-7.0, 7.0)
        return {
            "family": family,
            "parameter_name": "rho",
            "parameter_unit": "dimensionless",
            "parameter_bounds": (
                float(np.tanh(transformed_bounds[0])),
                float(np.tanh(transformed_bounds[1])),
            ),
            "transformed_bounds": transformed_bounds,
            "grid_regular": regular,
            "grid_interval": interval,
        }
    return {
        "family": family,
        "parameter_name": None,
        "parameter_unit": None,
        "parameter_bounds": None,
        "transformed_bounds": None,
        "grid_regular": regular,
        "grid_interval": interval,
    }


def _residual_correlation_matrix(
    *,
    family: str,
    time: np.ndarray,
    transformed_parameter: float | None,
) -> tuple[np.ndarray, float | None]:
    n_time = int(np.asarray(time).size)
    if family == "iid":
        return np.eye(n_time, dtype=float), None
    if transformed_parameter is None:
        raise ValueError("serial residual correlation requires a parameter")

    if family == "exponential":
        phi = float(np.exp(transformed_parameter))
        distance = np.abs(
            np.subtract.outer(
                np.asarray(time, dtype=float),
                np.asarray(time, dtype=float),
            )
        )
        correlation = np.exp(-distance / phi)
        return correlation, phi

    if family == "ar1":
        rho = float(np.tanh(transformed_parameter))
        order = np.abs(
            np.subtract.outer(
                np.arange(n_time, dtype=int),
                np.arange(n_time, dtype=int),
            )
        )
        correlation = np.power(rho, order)
        return correlation, rho

    raise ValueError(f"unsupported residual correlation family {family!r}")


def _block_residual_covariance(
    *,
    n_curves: int,
    residual_variance: float,
    correlation: np.ndarray,
) -> np.ndarray:
    n_time = correlation.shape[0]
    covariance = np.zeros(
        (n_curves * n_time, n_curves * n_time),
        dtype=float,
    )
    block = residual_variance * correlation
    for curve_index in range(n_curves):
        start = curve_index * n_time
        stop = start + n_time
        covariance[start:stop, start:stop] = block
    return covariance


def _residual_correlation_diagnostics(
    correlation: np.ndarray,
    *,
    transformed_parameter: float | None,
    transformed_bounds: tuple[float, float] | None,
) -> tuple[np.ndarray, float, bool]:
    eigenvalues = np.linalg.eigvalsh(
        np.asarray(correlation, dtype=float)
    )
    if float(np.min(eigenvalues)) <= 0.0:
        condition_number = float("inf")
    else:
        condition_number = float(
            np.max(eigenvalues) / np.min(eigenvalues)
        )
    if transformed_parameter is None or transformed_bounds is None:
        boundary = False
    else:
        lower, upper = transformed_bounds
        tolerance = max(1e-3, 1e-4 * (upper - lower))
        boundary = bool(
            transformed_parameter <= lower + tolerance
            or transformed_parameter >= upper - tolerance
        )
    return eigenvalues, condition_number, boundary


def functional_mixed_effects_whitened_residuals(
    result: FunctionalMixedEffectsResult,
) -> np.ndarray:
    """Return conditional residual functions whitened within each trial.

    Whitening uses the fitted residual covariance only. Random effects remain
    conditioned on their fitted BLUPs, so these are model-scale diagnostic
    residuals rather than independent observations with parameter uncertainty
    removed.
    """

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    residuals = np.asarray(result.residual_functions, dtype=float)
    if residuals.shape != (result.n_curves, result.time.size):
        raise ValueError(
            "residual_functions must have shape (n_curves, n_time)"
        )
    if not np.all(np.isfinite(residuals)):
        raise ValueError("residual_functions must be finite")
    if result.residual_variance <= 0 or not np.isfinite(
        result.residual_variance
    ):
        raise ValueError("residual_variance must be finite and positive")

    if result.residual_correlation_matrix is None:
        correlation = np.eye(result.time.size, dtype=float)
    else:
        correlation = np.asarray(
            result.residual_correlation_matrix,
            dtype=float,
        )
    if correlation.shape != (result.time.size, result.time.size):
        raise ValueError(
            "residual_correlation_matrix has an unexpected shape"
        )
    covariance = result.residual_variance * correlation
    try:
        chol = np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as exc:
        raise RuntimeError(
            "fitted residual covariance is not positive definite"
        ) from exc

    whitened = np.empty_like(residuals, dtype=float)
    for curve_index, residual in enumerate(residuals):
        whitened[curve_index] = solve_triangular(
            chol,
            residual,
            lower=True,
            check_finite=False,
        )
    return whitened


def _participant_blocks(
    *,
    fixed_exog: np.ndarray,
    participant_random_exog: np.ndarray,
    response: np.ndarray,
    curve_participants: np.ndarray,
    participant_ids: tuple[str, ...],
    n_time: int,
    trial_basis: np.ndarray | None,
) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    for participant_id in participant_ids:
        curve_indices = np.flatnonzero(
            curve_participants == participant_id
        )
        row_indices = (
            curve_indices[:, None] * n_time
            + np.arange(n_time, dtype=int)[None, :]
        ).reshape(-1)
        n_curves = int(curve_indices.size)
        trial_designs: list[np.ndarray] = []
        if trial_basis is not None:
            for within_index in range(n_curves):
                design = np.zeros(
                    (n_curves * n_time, trial_basis.shape[1]),
                    dtype=float,
                )
                start = within_index * n_time
                design[start : start + n_time] = trial_basis
                trial_designs.append(design)
        blocks.append(
            {
                "participant_id": str(participant_id),
                "curve_indices": curve_indices,
                "row_indices": row_indices,
                "response": response[row_indices],
                "fixed_exog": fixed_exog[row_indices],
                "participant_random_exog": participant_random_exog[row_indices],
                "trial_designs": tuple(trial_designs),
            }
        )
    return blocks


def _profiled_gaussian_state(
    theta: np.ndarray,
    *,
    blocks: list[dict[str, object]],
    participant_dimension: int,
    trial_dimension: int,
    n_fixed_parameters: int,
    time: np.ndarray,
    residual_correlation: str,
    reml: bool,
    return_state: bool = False,
):
    participant_count = _covariance_parameter_count(participant_dimension)
    trial_count = _covariance_parameter_count(trial_dimension)
    has_serial = residual_correlation != "iid"
    expected = participant_count + trial_count + 1 + int(has_serial)
    theta = np.asarray(theta, dtype=float)
    if theta.size != expected:
        raise ValueError("unexpected covariance parameter vector length")

    residual_index = participant_count + trial_count
    correlation_index = residual_index + 1 if has_serial else None

    try:
        participant_covariance = _unpack_covariance_cholesky(
            theta[:participant_count],
            participant_dimension,
        )
        if trial_dimension > 0:
            trial_covariance = _unpack_covariance_cholesky(
                theta[participant_count : participant_count + trial_count],
                trial_dimension,
            )
        else:
            trial_covariance = None
        residual_variance = float(np.exp(2.0 * theta[residual_index]))
        transformed_correlation = (
            float(theta[correlation_index])
            if correlation_index is not None
            else None
        )
        residual_correlation_matrix, residual_parameter = (
            _residual_correlation_matrix(
                family=residual_correlation,
                time=time,
                transformed_parameter=transformed_correlation,
            )
        )
    except (FloatingPointError, OverflowError, ValueError):
        return float("inf")

    if (
        not np.isfinite(residual_variance)
        or residual_variance <= np.finfo(float).tiny
        or not np.all(np.isfinite(residual_correlation_matrix))
    ):
        return float("inf")

    information = np.zeros(
        (n_fixed_parameters, n_fixed_parameters),
        dtype=float,
    )
    score = np.zeros(n_fixed_parameters, dtype=float)
    cache: list[tuple[np.ndarray, np.ndarray, tuple[np.ndarray, bool]]] = []
    log_determinant = 0.0
    n_observations = 0

    for block in blocks:
        y = np.asarray(block["response"], dtype=float)
        x = np.asarray(block["fixed_exog"], dtype=float)
        z = np.asarray(block["participant_random_exog"], dtype=float)
        trial_designs = block["trial_designs"]
        curve_indices = np.asarray(block["curve_indices"], dtype=int)

        marginal = (
            z @ participant_covariance @ z.T
            + _block_residual_covariance(
                n_curves=int(curve_indices.size),
                residual_variance=residual_variance,
                correlation=residual_correlation_matrix,
            )
        )
        if trial_covariance is not None:
            for trial_design in trial_designs:
                w = np.asarray(trial_design, dtype=float)
                marginal += w @ trial_covariance @ w.T

        try:
            factor = cho_factor(
                marginal,
                lower=True,
                check_finite=False,
            )
            inverse_x = cho_solve(
                factor,
                x,
                check_finite=False,
            )
            inverse_y = cho_solve(
                factor,
                y,
                check_finite=False,
            )
        except np.linalg.LinAlgError:
            return float("inf")

        diagonal = np.diag(factor[0])
        if np.any(diagonal <= 0) or not np.all(np.isfinite(diagonal)):
            return float("inf")
        log_determinant += float(2.0 * np.sum(np.log(diagonal)))
        information += x.T @ inverse_x
        score += x.T @ inverse_y
        cache.append((y, x, factor))
        n_observations += int(y.size)

    if np.linalg.matrix_rank(information) < n_fixed_parameters:
        return float("inf")
    try:
        fixed_parameters = np.linalg.solve(information, score)
    except np.linalg.LinAlgError:
        return float("inf")

    quadratic = 0.0
    for y, x, factor in cache:
        residual = y - x @ fixed_parameters
        quadratic += float(
            residual
            @ cho_solve(
                factor,
                residual,
                check_finite=False,
            )
        )

    if reml:
        sign, fixed_log_determinant = np.linalg.slogdet(information)
        if sign <= 0 or not np.isfinite(fixed_log_determinant):
            return float("inf")
        negative_log_likelihood = 0.5 * (
            log_determinant
            + fixed_log_determinant
            + quadratic
            + (n_observations - n_fixed_parameters) * np.log(2.0 * np.pi)
        )
    else:
        negative_log_likelihood = 0.5 * (
            log_determinant
            + quadratic
            + n_observations * np.log(2.0 * np.pi)
        )

    if not return_state:
        return float(negative_log_likelihood)
    return {
        "negative_log_likelihood": float(negative_log_likelihood),
        "fixed_parameters": fixed_parameters,
        "fixed_information": information,
        "participant_covariance": participant_covariance,
        "trial_covariance": trial_covariance,
        "residual_variance": residual_variance,
        "residual_correlation_matrix": residual_correlation_matrix,
        "residual_correlation_parameter": residual_parameter,
        "residual_correlation_transformed_parameter": transformed_correlation,
        "block_cache": cache,
    }


def fit_nested_functional_mixed_effects_regression(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictors,
    *,
    participant_column: str,
    trial_column: str,
    dimension: str,
    fixed_basis_size: int,
    random_basis_size: int,
    random_slope_predictor: str | None,
    trial_random_effect: str,
    trial_random_basis_size: int,
    spline_degree: int,
    reml: bool,
    method: str,
    maxiter: int,
) -> FunctionalMixedEffectsResult:
    """Fit participant and trial functional random effects by marginal likelihood."""

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError(
            "functional mixed-effects regression requires finite complete "
            "trajectories"
        )
    if trajectories.coordinate_system == "probability_simplex":
        raise ValueError(
            "Direct Gaussian functional mixed-effects regression is not "
            "supported for probability_simplex trajectories"
        )
    if trial_random_effect != "functional_intercept":
        raise ValueError(
            "trial_random_effect must be 'functional_intercept' for the "
            "0.48 contract"
        )
    if not isinstance(reml, bool):
        raise TypeError("reml must be boolean")
    if not isinstance(method, str) or not method:
        raise TypeError("method must be a non-empty string")
    normalized_method = method.lower().replace("_", "-")
    if normalized_method not in {"lbfgs", "l-bfgs-b"}:
        raise ValueError(
            "0.48 nested functional covariance currently supports only the "
            "explicit 'lbfgs' optimizer contract; no optimizer fallback is "
            "performed"
        )
    if isinstance(maxiter, bool) or not isinstance(maxiter, int):
        raise TypeError("maxiter must be an integer")
    if maxiter < 1:
        raise ValueError("maxiter must be positive")
    if (
        isinstance(trial_random_basis_size, bool)
        or not isinstance(trial_random_basis_size, int)
    ):
        raise TypeError("trial_random_basis_size must be an integer")

    aligned_design, predictor_names = _validate_design_alignment(
        trajectories,
        design,
        predictors,
    )
    dimension_index, dimension_name = _validate_dimension(
        trajectories,
        dimension,
    )
    fixed_basis, fixed_knots = _bspline_basis(
        trajectories.time,
        n_basis=fixed_basis_size,
        degree=spline_degree,
    )
    participant_basis, participant_knots = _bspline_basis(
        trajectories.time,
        n_basis=random_basis_size,
        degree=spline_degree,
    )
    trial_basis, trial_knots = _bspline_basis(
        trajectories.time,
        n_basis=trial_random_basis_size,
        degree=spline_degree,
    )
    if np.linalg.matrix_rank(trial_basis) != trial_random_basis_size:
        raise ValueError(
            "trial random-effect basis is rank deficient on the observed grid"
        )

    has_random_slope = random_slope_predictor is not None
    participant_dimension = random_basis_size * (
        2 if has_random_slope else 1
    )
    (
        curve_participants,
        participant_ids,
        curves_per_participant,
    ) = _validate_participants(
        trajectories,
        participant_column,
        random_effect_dimension=participant_dimension,
    )
    source_trial_ids, composite_trial_ids = _validate_trial_structure(
        trajectories,
        participant_column=participant_column,
        trial_column=trial_column,
        curve_participants=curve_participants,
        participant_ids=participant_ids,
    )

    slope_values = _validate_random_slope(
        random_slope_predictor=random_slope_predictor,
        predictor_names=predictor_names,
        aligned_design=aligned_design,
        curve_participants=curve_participants,
        participant_ids=participant_ids,
    )

    participant_covariance_parameter_count = _covariance_parameter_count(
        participant_dimension
    )
    if (
        has_random_slope
        and len(participant_ids) <= participant_covariance_parameter_count
    ):
        raise ValueError(
            "guarded random-functional-slope model requires the participant "
            "count to exceed the number of free unstructured random-effect "
            "covariance parameters; "
            f"got {len(participant_ids)} participants and "
            f"{participant_covariance_parameter_count} covariance parameters"
        )
    participant_complexity_warning = bool(
        len(participant_ids) <= participant_covariance_parameter_count
    )

    trial_covariance_parameter_count = _covariance_parameter_count(
        trial_random_basis_size
    )
    n_trials = len(composite_trial_ids)
    if n_trials <= trial_covariance_parameter_count:
        raise ValueError(
            "trial functional random-effect covariance requires the number of "
            "observed nested trials to exceed the number of free unstructured "
            "trial covariance parameters; "
            f"got {n_trials} trials and "
            f"{trial_covariance_parameter_count} covariance parameters"
        )
    trial_complexity_warning = bool(
        n_trials <= trial_covariance_parameter_count
    )

    predictor_matrix = aligned_design.loc[
        :, list(predictor_names)
    ].to_numpy(dtype=float)
    scalar_design = np.column_stack(
        [np.ones(trajectories.n_curves, dtype=float), predictor_matrix]
    )
    coefficient_names = ("Intercept",) + predictor_names
    scalar_rank = int(np.linalg.matrix_rank(scalar_design))
    if scalar_rank != scalar_design.shape[1]:
        raise ValueError(
            "scalar design matrix is rank deficient; remove redundant "
            "predictors or encode the model explicitly"
        )

    fixed_exog = _fixed_effect_design(scalar_design, fixed_basis)
    fixed_rank = int(np.linalg.matrix_rank(fixed_exog))
    if fixed_rank != fixed_exog.shape[1]:
        raise ValueError(
            "expanded functional fixed-effect design is rank deficient"
        )

    n_time = trajectories.n_time
    response = trajectories.values[:, :, dimension_index].reshape(-1)
    participant_random_exog = _random_effect_design(
        participant_basis,
        n_curves=trajectories.n_curves,
        slope_values=slope_values,
    )
    participant_random_rank = int(
        np.linalg.matrix_rank(participant_random_exog)
    )
    if participant_random_rank != participant_random_exog.shape[1]:
        raise ValueError(
            "expanded functional random-effect design is rank deficient"
        )

    blocks = _participant_blocks(
        fixed_exog=fixed_exog,
        participant_random_exog=participant_random_exog,
        response=response,
        curve_participants=curve_participants,
        participant_ids=participant_ids,
        n_time=n_time,
        trial_basis=trial_basis,
    )
    n_fixed_parameters = fixed_exog.shape[1]

    response_variance = max(
        float(np.var(response)),
        np.finfo(float).eps,
    )
    participant_initial = np.eye(
        participant_dimension,
        dtype=float,
    ) * max(0.15 * response_variance, 1e-6)
    trial_initial = np.eye(
        trial_random_basis_size,
        dtype=float,
    ) * max(0.15 * response_variance, 1e-6)
    residual_initial = max(0.40 * response_variance, 1e-6)
    initial = np.concatenate(
        [
            _pack_covariance_cholesky(participant_initial),
            _pack_covariance_cholesky(trial_initial),
            np.asarray([0.5 * np.log(residual_initial)], dtype=float),
        ]
    )

    participant_count = _covariance_parameter_count(participant_dimension)
    trial_count = _covariance_parameter_count(trial_random_basis_size)
    bounds: list[tuple[float | None, float | None]] = []
    for index in range(participant_count + trial_count):
        is_participant_diagonal = False
        cursor = 0
        for dimension_value in (
            participant_dimension,
            trial_random_basis_size,
        ):
            for row in range(dimension_value):
                for column in range(row + 1):
                    if cursor == index and row == column:
                        is_participant_diagonal = True
                    cursor += 1
        bounds.append(
            (-14.0, 8.0)
            if is_participant_diagonal
            else (None, None)
        )
    bounds.append((-14.0, 8.0))

    objective = lambda theta: _profiled_gaussian_state(
        theta,
        blocks=blocks,
        participant_dimension=participant_dimension,
        trial_dimension=trial_random_basis_size,
        n_fixed_parameters=n_fixed_parameters,
        reml=reml,
        return_state=False,
    )
    optimized = minimize(
        objective,
        initial,
        method="L-BFGS-B",
        bounds=bounds,
        options={
            "maxiter": int(maxiter),
            "ftol": 1e-9,
            "gtol": 1e-6,
        },
    )
    if not bool(optimized.success):
        raise RuntimeError(
            "nested functional mixed-effects optimization did not converge: "
            f"{optimized.message}"
        )

    state = _profiled_gaussian_state(
        optimized.x,
        blocks=blocks,
        participant_dimension=participant_dimension,
        trial_dimension=trial_random_basis_size,
        n_fixed_parameters=n_fixed_parameters,
        reml=reml,
        return_state=True,
    )
    if not isinstance(state, dict):
        raise RuntimeError(
            "nested functional mixed-effects optimizer produced an invalid "
            "final covariance state"
        )

    fixed_parameters = np.asarray(
        state["fixed_parameters"],
        dtype=float,
    )
    fixed_information = np.asarray(
        state["fixed_information"],
        dtype=float,
    )
    try:
        fixed_parameter_covariance = np.linalg.inv(fixed_information)
    except np.linalg.LinAlgError as exc:
        raise RuntimeError(
            "nested mixed-effects fixed-effect information matrix is singular"
        ) from exc

    fixed_basis_coefficients = fixed_parameters.reshape(
        len(coefficient_names),
        fixed_basis_size,
    )
    coefficient_functions = fixed_basis_coefficients @ fixed_basis.T
    coefficient_standard_errors = np.empty(
        (len(coefficient_names), n_time),
        dtype=float,
    )
    for coefficient_index in range(len(coefficient_names)):
        start = coefficient_index * fixed_basis_size
        stop = start + fixed_basis_size
        covariance_block = fixed_parameter_covariance[start:stop, start:stop]
        variance = np.einsum(
            "ti,ij,tj->t",
            fixed_basis,
            covariance_block,
            fixed_basis,
            optimize=True,
        )
        coefficient_standard_errors[coefficient_index] = np.sqrt(
            np.maximum(variance, 0.0)
        )

    participant_covariance = np.asarray(
        state["participant_covariance"],
        dtype=float,
    )
    trial_covariance = np.asarray(
        state["trial_covariance"],
        dtype=float,
    )
    residual_variance = float(state["residual_variance"])

    (
        participant_eigenvalues,
        participant_condition_number,
        participant_boundary,
        participant_singular,
        participant_scale,
    ) = _covariance_diagnostics(participant_covariance)
    (
        trial_eigenvalues,
        trial_condition_number,
        trial_boundary_base,
        trial_singular,
        trial_scale,
    ) = _covariance_diagnostics(trial_covariance)

    reference_scale = max(
        float(np.max(np.abs(participant_eigenvalues))),
        residual_variance,
        np.finfo(float).eps,
    )
    trial_boundary = bool(
        trial_boundary_base
        or float(np.max(trial_eigenvalues)) <= 0.10 * reference_scale
    )

    participant_coefficients = np.empty(
        (len(participant_ids), participant_dimension),
        dtype=float,
    )
    trial_coefficients = np.empty(
        (trajectories.n_curves, trial_random_basis_size),
        dtype=float,
    )

    for participant_index, block in enumerate(blocks):
        y_block = np.asarray(block["response"], dtype=float)
        x_block = np.asarray(block["fixed_exog"], dtype=float)
        z_block = np.asarray(
            block["participant_random_exog"],
            dtype=float,
        )
        curve_indices = np.asarray(block["curve_indices"], dtype=int)
        trial_designs = block["trial_designs"]

        marginal = (
            z_block @ participant_covariance @ z_block.T
            + residual_variance * np.eye(y_block.size, dtype=float)
        )
        for trial_design in trial_designs:
            w = np.asarray(trial_design, dtype=float)
            marginal += w @ trial_covariance @ w.T
        try:
            factor = cho_factor(
                marginal,
                lower=True,
                check_finite=False,
            )
            conditional_score = cho_solve(
                factor,
                y_block - x_block @ fixed_parameters,
                check_finite=False,
            )
        except np.linalg.LinAlgError as exc:
            raise RuntimeError(
                "nested mixed-effects BLUP covariance solve failed"
            ) from exc

        participant_coefficients[participant_index] = (
            participant_covariance
            @ z_block.T
            @ conditional_score
        )
        for within_index, curve_index in enumerate(curve_indices):
            w = np.asarray(trial_designs[within_index], dtype=float)
            trial_coefficients[curve_index] = (
                trial_covariance
                @ w.T
                @ conditional_score
            )

    random_intercept_coefficients = participant_coefficients[
        :, :random_basis_size
    ].copy()
    random_intercept_functions = (
        random_intercept_coefficients @ participant_basis.T
    )
    if has_random_slope:
        random_slope_coefficients = participant_coefficients[
            :, random_basis_size:
        ].copy()
        random_slope_functions = (
            random_slope_coefficients @ participant_basis.T
        )
        random_slope_covariance = participant_covariance[
            random_basis_size:,
            random_basis_size:,
        ].copy()
        random_intercept_slope_covariance = participant_covariance[
            :random_basis_size,
            random_basis_size:,
        ].copy()
        slope_eigenvalues = np.linalg.eigvalsh(random_slope_covariance)
        random_slope_boundary_fit = bool(
            float(np.max(slope_eigenvalues))
            <= 0.10
            * max(
                float(np.max(np.abs(participant_eigenvalues))),
                np.finfo(float).eps,
            )
            or float(np.min(slope_eigenvalues))
            <= 1e-8 * participant_scale
        )
    else:
        random_slope_coefficients = None
        random_slope_functions = None
        random_slope_covariance = None
        random_intercept_slope_covariance = None
        random_slope_boundary_fit = False

    random_intercept_covariance = participant_covariance[
        :random_basis_size,
        :random_basis_size,
    ].copy()
    trial_functions = trial_coefficients @ trial_basis.T
    random_effect_functions = random_intercept_functions.copy()

    participant_lookup = {
        participant_id: index
        for index, participant_id in enumerate(participant_ids)
    }
    fixed_fitted = scalar_design @ coefficient_functions
    fitted_functions = np.empty(
        (trajectories.n_curves, n_time),
        dtype=float,
    )
    for curve_index, participant_id in enumerate(curve_participants):
        participant_index = participant_lookup[participant_id]
        random_contribution = random_intercept_functions[participant_index]
        if random_slope_functions is not None and slope_values is not None:
            random_contribution = (
                random_contribution
                + slope_values[curve_index]
                * random_slope_functions[participant_index]
            )
        fitted_functions[curve_index] = (
            fixed_fitted[curve_index]
            + random_contribution
            + trial_functions[curve_index]
        )

    observed_functions = trajectories.values[:, :, dimension_index].copy()
    residual_functions = observed_functions - fitted_functions
    backend_warnings: tuple[str, ...] = ()

    return FunctionalMixedEffectsResult(
        coefficient_functions=coefficient_functions,
        coefficient_standard_errors=coefficient_standard_errors,
        fixed_basis_coefficients=fixed_basis_coefficients,
        fixed_parameter_covariance=fixed_parameter_covariance,
        fixed_basis=fixed_basis,
        fixed_basis_knots=fixed_knots,
        random_basis=participant_basis,
        random_basis_knots=participant_knots,
        random_intercept_basis=participant_basis.copy(),
        random_slope_basis=(
            None if not has_random_slope else participant_basis.copy()
        ),
        random_effect_design_matrix=participant_random_exog.copy(),
        random_effect_coefficients=participant_coefficients,
        random_effect_functions=random_effect_functions,
        random_intercept_coefficients=random_intercept_coefficients,
        random_slope_coefficients=random_slope_coefficients,
        random_intercept_functions=random_intercept_functions,
        random_slope_functions=random_slope_functions,
        random_effect_covariance=participant_covariance,
        random_intercept_covariance=random_intercept_covariance,
        random_slope_covariance=random_slope_covariance,
        random_intercept_slope_covariance=(
            random_intercept_slope_covariance
        ),
        random_effect_covariance_eigenvalues=participant_eigenvalues.copy(),
        random_effect_covariance_condition_number=(
            participant_condition_number
        ),
        random_effect_dimension=participant_dimension,
        random_effect_covariance_parameter_count=(
            participant_covariance_parameter_count
        ),
        random_effect_complexity_warning=participant_complexity_warning,
        random_effect_singular=participant_singular,
        random_slope_boundary_fit=random_slope_boundary_fit,
        random_slope_predictor=random_slope_predictor,
        residual_variance=residual_variance,
        fitted_functions=fitted_functions,
        residual_functions=residual_functions,
        observed_functions=observed_functions,
        scalar_design_matrix=scalar_design,
        coefficient_names=coefficient_names,
        predictor_names=predictor_names,
        scalar_design_rank=scalar_rank,
        expanded_design_rank=fixed_rank,
        participant_column=participant_column,
        participant_ids=participant_ids,
        curve_participant_ids=tuple(map(str, curve_participants)),
        curves_per_participant=curves_per_participant,
        source_curve_ids=trajectories.curve_ids,
        time=trajectories.time.copy(),
        dimension_name=dimension_name,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        fixed_basis_size=fixed_basis_size,
        random_basis_size=random_basis_size,
        spline_degree=spline_degree,
        reml=reml,
        method=method,
        maxiter=maxiter,
        converged=True,
        boundary_fit=bool(participant_boundary or trial_boundary),
        backend_warnings=backend_warnings,
        log_likelihood=-float(state["negative_log_likelihood"]),
        provenance={
            **dict(trajectories.provenance),
            "functional_mixed_effects_regression": {
                "method": "profiled_gaussian_nested_functional_mixed_model",
                "backend": "eyetrajectoriespy.profiled_gaussian_nested",
                "response_dimension": dimension_name,
                "participant_column": participant_column,
                "trial_column": trial_column,
                "n_source_curves": trajectories.n_curves,
                "n_participants": len(participant_ids),
                "n_trials": n_trials,
                "n_grid_observations": int(
                    trajectories.n_curves * n_time
                ),
                "coefficient_names": list(coefficient_names),
                "predictors": list(predictor_names),
                "design_alignment": aligned_design.attrs[
                    "eyetrajectoriespy_alignment"
                ],
                "fixed_basis": "clamped_bspline",
                "fixed_basis_size": fixed_basis_size,
                "random_intercept_basis": "clamped_bspline",
                "random_slope_basis": (
                    None if not has_random_slope else "clamped_bspline"
                ),
                "random_basis_size": random_basis_size,
                "trial_random_effect": "functional_intercept",
                "trial_random_basis": "clamped_bspline",
                "trial_random_basis_size": trial_random_basis_size,
                "spline_degree": spline_degree,
                "basis_size_selected_automatically": False,
                "trial_basis_size_selected_automatically": False,
                "smoothing_penalty": False,
                "categorical_encoding": False,
                "predictor_centering": False,
                "predictor_scaling": False,
                "interaction_construction": False,
                "automatic_model_selection": False,
                "automatic_random_slope_selection": False,
                "automatic_trial_random_effect_selection": False,
                "participant_random_effect_covariance": "unstructured",
                "trial_random_effect_covariance": "shared_unstructured",
                "participant_trial_cross_covariance": False,
                "participant_random_effect_dimension": participant_dimension,
                "participant_random_effect_covariance_parameter_count": (
                    participant_covariance_parameter_count
                ),
                "trial_random_effect_dimension": trial_random_basis_size,
                "trial_random_effect_covariance_parameter_count": (
                    trial_covariance_parameter_count
                ),
                "n_trials_per_trial_covariance_parameter": float(
                    n_trials / trial_covariance_parameter_count
                ),
                "trial_covariance_complexity_guard": (
                    "require n_nested_trials > "
                    "trial_random_effect_covariance_parameter_count"
                ),
                "minimum_trials_per_participant": 2,
                "participant_covariance_eigenvalues": (
                    participant_eigenvalues.tolist()
                ),
                "trial_covariance_eigenvalues": trial_eigenvalues.tolist(),
                "participant_covariance_condition_number": (
                    participant_condition_number
                ),
                "trial_covariance_condition_number": (
                    trial_condition_number
                ),
                "participant_random_effect_singular": participant_singular,
                "trial_random_effect_singular": trial_singular,
                "trial_random_effect_boundary_fit": trial_boundary,
                "curve_level_functional_random_effect": True,
                "curve_level_random_effect_interpretation": (
                    "nested_trial_functional_intercept"
                ),
                "residual_structure": (
                    "conditionally_iid_gaussian_grid_errors_after_"
                    "participant_and_trial_functional_random_effects"
                ),
                "trial_varying_predictors_supported": True,
                "random_slope_requires_within_participant_variation": (
                    has_random_slope
                ),
                "joint_fit_over_all_time_points": True,
                "pointwise_mixed_models": False,
                "multivariate_cross_dimension_covariance": False,
                "reml": reml,
                "optimizer": "L-BFGS-B",
                "optimizer_requested": method,
                "maxiter": maxiter,
                "converged": True,
                "boundary_fit": bool(
                    participant_boundary or trial_boundary
                ),
                "backend_warnings": [],
            },
        },
        model={
            "backend": "eyetrajectoriespy.profiled_gaussian_nested",
            "optimizer_result": optimized,
        },
        trial_column=trial_column,
        curve_trial_ids=tuple(map(str, source_trial_ids)),
        trial_ids=composite_trial_ids,
        trial_random_effect="functional_intercept",
        trial_random_basis_size=trial_random_basis_size,
        trial_random_basis=trial_basis.copy(),
        trial_random_basis_knots=trial_knots.copy(),
        trial_random_effect_coefficients=trial_coefficients,
        trial_random_effect_functions=trial_functions,
        trial_random_effect_covariance=trial_covariance,
        trial_random_effect_covariance_eigenvalues=trial_eigenvalues.copy(),
        trial_random_effect_covariance_condition_number=(
            trial_condition_number
        ),
        trial_random_effect_covariance_parameter_count=(
            trial_covariance_parameter_count
        ),
        trial_random_effect_complexity_warning=trial_complexity_warning,
        trial_random_effect_boundary_fit=trial_boundary,
        trial_random_effect_singular=trial_singular,
    )


def functional_trial_random_effect_frame(
    result: FunctionalMixedEffectsResult,
) -> pd.DataFrame:
    """Return one row per nested trial and time point for trial BLUPs."""

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if (
        result.trial_random_effect != "functional_intercept"
        or result.trial_random_effect_functions is None
    ):
        raise ValueError(
            "result does not contain a trial functional random intercept"
        )

    rows: list[dict[str, object]] = []
    for curve_index, curve_id in enumerate(result.source_curve_ids):
        participant_id = result.curve_participant_ids[curve_index]
        source_trial_id = result.curve_trial_ids[curve_index]
        trial_id = result.trial_ids[curve_index]
        for time_index, time_value in enumerate(result.time):
            rows.append(
                {
                    "curve_index": curve_index,
                    "curve_id": curve_id,
                    "participant_id": participant_id,
                    "source_trial_id": source_trial_id,
                    "trial_id": trial_id,
                    "time": float(time_value),
                    "effect": "trial_functional_intercept",
                    "value": float(
                        result.trial_random_effect_functions[
                            curve_index,
                            time_index,
                        ]
                    ),
                }
            )
    return pd.DataFrame(rows)


def plot_functional_trial_random_effects(
    result: FunctionalMixedEffectsResult,
    *,
    participant_id: str | None = None,
    max_trials: int = 12,
    ax=None,
):
    """Plot retained trial-level functional BLUPs without hidden averaging."""

    import matplotlib.pyplot as plt

    frame = functional_trial_random_effect_frame(result)
    if isinstance(max_trials, bool) or not isinstance(max_trials, int):
        raise TypeError("max_trials must be an integer")
    if max_trials < 1:
        raise ValueError("max_trials must be positive")

    if participant_id is not None:
        participant_id = str(participant_id)
        frame = frame.loc[
            frame["participant_id"].astype(str) == participant_id
        ]
        if frame.empty:
            raise KeyError(f"Unknown participant_id {participant_id!r}")

    trial_ids = tuple(pd.unique(frame["trial_id"]))
    selected = trial_ids[:max_trials]
    frame = frame.loc[frame["trial_id"].isin(selected)]

    if ax is None:
        _, ax = plt.subplots()
    for trial_id, trial_frame in frame.groupby("trial_id", sort=False):
        ax.plot(
            trial_frame["time"],
            trial_frame["value"],
            label=str(trial_id),
        )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel(f"Time ({result.time_unit})")
    ax.set_ylabel("Trial functional random intercept")
    title = "Trial-level functional random effects"
    if participant_id is not None:
        title += f": {participant_id}"
    ax.set_title(title)
    if len(selected) <= 12:
        ax.legend()
    return ax
