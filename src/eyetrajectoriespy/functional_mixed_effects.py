"""Gaussian functional mixed-effects regression on a common time grid."""

from __future__ import annotations

from collections.abc import Sequence
import warnings

import numpy as np
import pandas as pd
from scipy.interpolate import BSpline
from statsmodels.regression.mixed_linear_model import MixedLM

from .function_on_scalar import _validate_design_alignment
from .types import (
    FunctionalMixedEffectsBandResult,
    FunctionalMixedEffectsResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _bspline_basis(
    time: np.ndarray,
    *,
    n_basis: int,
    degree: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct a clamped B-spline basis on the observed time domain."""

    if isinstance(n_basis, bool) or not isinstance(n_basis, int):
        raise TypeError("n_basis must be an integer")
    if isinstance(degree, bool) or not isinstance(degree, int):
        raise TypeError("degree must be an integer")
    if degree < 0:
        raise ValueError("degree must be non-negative")
    if n_basis < degree + 1:
        raise ValueError("n_basis must be at least degree + 1")

    start = float(time[0])
    stop = float(time[-1])
    n_interior = n_basis - degree - 1
    if n_interior > 0:
        interior = np.linspace(start, stop, n_interior + 2, dtype=float)[1:-1]
    else:
        interior = np.empty(0, dtype=float)
    knots = np.concatenate(
        [
            np.repeat(start, degree + 1),
            interior,
            np.repeat(stop, degree + 1),
        ]
    )

    coefficients = np.eye(n_basis, dtype=float)
    basis = np.column_stack(
        [
            BSpline(
                knots,
                coefficients[index],
                degree,
                extrapolate=False,
            )(time)
            for index in range(n_basis)
        ]
    )
    if not np.all(np.isfinite(basis)):
        raise RuntimeError("B-spline basis evaluation produced non-finite values")
    return basis, knots


def _validate_dimension(
    trajectories: TrajectorySet,
    dimension: str,
) -> tuple[int, str]:
    if not isinstance(dimension, str):
        raise TypeError("dimension must be a string")
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown trajectory dimension {dimension!r}")
    return trajectories.dimension_names.index(dimension), dimension


def _validate_participants(
    trajectories: TrajectorySet,
    participant_column: str,
    *,
    random_effect_dimension: int,
) -> tuple[np.ndarray, tuple[str, ...], tuple[int, ...]]:
    if not isinstance(participant_column, str):
        raise TypeError("participant_column must be a string")
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column {participant_column!r}"
        )
    participant_series = trajectories.metadata[participant_column]
    if participant_series.isna().any():
        raise ValueError("participant_column contains missing values")

    participants = participant_series.astype(str).to_numpy()
    participant_ids = tuple(pd.unique(participants))
    minimum_participants = max(4, random_effect_dimension + 1)
    if len(participant_ids) < minimum_participants:
        raise ValueError(
            "functional mixed-effects regression requires at least "
            "max(4, random_effect_dimension + 1) participants; "
            f"got {len(participant_ids)} participants for random-effect "
            f"dimension {random_effect_dimension}"
        )
    counts = tuple(
        int(np.count_nonzero(participants == participant_id))
        for participant_id in participant_ids
    )
    return participants, participant_ids, counts


def _validate_random_slope(
    *,
    random_slope_predictor: str | None,
    predictor_names: tuple[str, ...],
    aligned_design: pd.DataFrame,
    curve_participants: np.ndarray,
    participant_ids: tuple[str, ...],
) -> np.ndarray | None:
    """Validate one explicitly declared random-slope predictor."""

    if random_slope_predictor is None:
        return None
    if not isinstance(random_slope_predictor, str) or not random_slope_predictor:
        raise TypeError(
            "random_slope_predictor must be a non-empty string or None"
        )
    if random_slope_predictor not in predictor_names:
        raise ValueError(
            "random_slope_predictor must name one of the declared fixed "
            "predictors"
        )

    slope_values = aligned_design[random_slope_predictor].to_numpy(dtype=float)
    if not np.all(np.isfinite(slope_values)):
        raise ValueError("random_slope_predictor contains non-finite values")

    nonvarying: list[str] = []
    for participant_id in participant_ids:
        participant_values = slope_values[curve_participants == participant_id]
        scale = max(1.0, float(np.max(np.abs(participant_values))))
        if float(np.ptp(participant_values)) <= 1e-12 * scale:
            nonvarying.append(participant_id)
    if nonvarying:
        preview = ", ".join(nonvarying[:5])
        suffix = "" if len(nonvarying) <= 5 else ", ..."
        raise ValueError(
            "random_slope_predictor must vary within every participant under "
            "the guarded 0.45 contract; no within-participant variation for "
            f"{preview}{suffix}"
        )
    return slope_values


def _random_effect_design(
    random_basis: np.ndarray,
    *,
    n_curves: int,
    slope_values: np.ndarray | None,
) -> np.ndarray:
    """Build participant random-intercept plus optional one-slope design."""

    intercept_block = np.tile(random_basis, (n_curves, 1))
    if slope_values is None:
        return intercept_block
    repeated_slope = np.repeat(
        np.asarray(slope_values, dtype=float),
        random_basis.shape[0],
    )[:, None]
    slope_block = repeated_slope * intercept_block
    return np.column_stack([intercept_block, slope_block])


def _fixed_effect_design(
    scalar_design: np.ndarray,
    basis: np.ndarray,
) -> np.ndarray:
    n_curves = scalar_design.shape[0]
    n_time = basis.shape[0]
    repeated_basis = np.tile(basis, (n_curves, 1))
    blocks = [
        np.repeat(
            scalar_design[:, coefficient_index],
            n_time,
        )[:, None]
        * repeated_basis
        for coefficient_index in range(scalar_design.shape[1])
    ]
    return np.column_stack(blocks)


def fit_functional_mixed_effects_regression(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictors: Sequence[str],
    *,
    participant_column: str,
    dimension: str,
    fixed_basis_size: int = 6,
    random_basis_size: int = 4,
    random_slope_predictor: str | None = None,
    trial_column: str | None = None,
    trial_random_effect: str | None = None,
    trial_random_basis_size: int = 3,
    residual_correlation: str = "iid",
    spline_degree: int = 3,
    reml: bool = True,
    method: str = "lbfgs",
    maxiter: int = 500,
) -> FunctionalMixedEffectsResult:
    """Fit one joint Gaussian functional mixed-effects model.

    The base model contains a participant functional random intercept. When
    random_slope_predictor explicitly names one declared fixed predictor, the
    model adds exactly one participant random functional slope for that
    predictor.

    Fixed coefficient functions, the participant functional random intercept,
    and the optional random functional slope use explicitly sized clamped
    B-spline bases. Version 0.45 uses one common random basis size for the
    intercept and the single slope, with one unstructured covariance over the
    stacked random-basis coefficient vector.

    Version 0.48 optionally adds one nested trial-level functional random
    intercept through an explicit profiled Gaussian marginal-likelihood backend.
    Version 0.49 extends that backend with explicit within-trial residual
    correlation: physical-time exponential correlation on arbitrary strictly
    increasing common grids, or index-step AR(1) on equally spaced grids.
    Residual correlation is block diagonal by source curve/trial and is never
    allowed to cross trial boundaries.

    The historical statsmodels MixedLM path is preserved exactly for the
    backward-compatible participant-only `residual_correlation="iid"` model.

    No random-slope predictor, trial random effect, residual-correlation family,
    basis size, interaction, or optimizer fallback is selected automatically.
    """

    if not isinstance(residual_correlation, str) or not residual_correlation:
        raise TypeError("residual_correlation must be a non-empty string")
    normalized_residual_correlation = residual_correlation.lower().strip()

    if (
        trial_random_effect is not None
        or normalized_residual_correlation != "iid"
    ):
        from .functional_mixed_effects_nested import (
            fit_nested_functional_mixed_effects_regression,
        )

        return fit_nested_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors,
            participant_column=participant_column,
            trial_column=trial_column,
            dimension=dimension,
            fixed_basis_size=fixed_basis_size,
            random_basis_size=random_basis_size,
            random_slope_predictor=random_slope_predictor,
            trial_random_effect=trial_random_effect,
            trial_random_basis_size=trial_random_basis_size,
            residual_correlation=normalized_residual_correlation,
            spline_degree=spline_degree,
            reml=reml,
            method=method,
            maxiter=maxiter,
        )
    if trial_column is not None:
        raise ValueError(
            "trial_column is only used when trial_random_effect is explicitly "
            "requested"
        )

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
    if not isinstance(reml, bool):
        raise TypeError("reml must be boolean")
    if not isinstance(method, str) or not method:
        raise TypeError("method must be a non-empty string")
    if isinstance(maxiter, bool) or not isinstance(maxiter, int):
        raise TypeError("maxiter must be an integer")
    if maxiter < 1:
        raise ValueError("maxiter must be positive")
    if random_slope_predictor is not None and (
        not isinstance(random_slope_predictor, str)
        or not random_slope_predictor
    ):
        raise TypeError(
            "random_slope_predictor must be a non-empty string or None"
        )

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
    random_basis, random_knots = _bspline_basis(
        trajectories.time,
        n_basis=random_basis_size,
        degree=spline_degree,
    )

    has_random_slope = random_slope_predictor is not None
    random_effect_dimension = random_basis_size * (2 if has_random_slope else 1)
    (
        curve_participants,
        participant_ids,
        curves_per_participant,
    ) = _validate_participants(
        trajectories,
        participant_column,
        random_effect_dimension=random_effect_dimension,
    )

    slope_values = _validate_random_slope(
        random_slope_predictor=random_slope_predictor,
        predictor_names=predictor_names,
        aligned_design=aligned_design,
        curve_participants=curve_participants,
        participant_ids=participant_ids,
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
    y = trajectories.values[:, :, dimension_index].reshape(-1)
    groups = np.repeat(curve_participants, n_time)
    random_exog = _random_effect_design(
        random_basis,
        n_curves=trajectories.n_curves,
        slope_values=slope_values,
    )
    random_design_rank = int(np.linalg.matrix_rank(random_exog))
    if random_design_rank != random_exog.shape[1]:
        raise ValueError(
            "expanded functional random-effect design is rank deficient"
        )

    covariance_parameter_count = (
        random_effect_dimension * (random_effect_dimension + 1) // 2
    )
    if has_random_slope and len(participant_ids) <= covariance_parameter_count:
        raise ValueError(
            "guarded random-functional-slope model requires the participant "
            "count to exceed the number of free unstructured random-effect "
            "covariance parameters; "
            f"got {len(participant_ids)} participants and "
            f"{covariance_parameter_count} covariance parameters"
        )
    covariance_complexity_warning = bool(
        len(participant_ids) <= covariance_parameter_count
    )

    model = MixedLM(
        endog=y,
        exog=fixed_exog,
        groups=groups,
        exog_re=random_exog,
        use_sqrt=True,
        missing="raise",
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        try:
            fitted_model = model.fit(
                reml=reml,
                method=method,
                maxiter=maxiter,
                disp=False,
            )
        except Exception as exc:
            raise RuntimeError(
                "statsmodels MixedLM failed before producing a valid fit"
            ) from exc

    warning_messages = tuple(dict.fromkeys(str(item.message) for item in captured))
    if not bool(getattr(fitted_model, "converged", False)):
        raise RuntimeError(
            "functional mixed-effects optimization did not converge"
        )

    n_coefficients = len(coefficient_names)
    expected_fixed = n_coefficients * fixed_basis_size
    fixed_parameters = np.asarray(fitted_model.fe_params, dtype=float)
    if fixed_parameters.size != expected_fixed:
        raise RuntimeError(
            "backend returned an unexpected number of fixed-effect parameters"
        )
    fixed_basis_coefficients = fixed_parameters.reshape(
        n_coefficients,
        fixed_basis_size,
    )
    coefficient_functions = fixed_basis_coefficients @ fixed_basis.T

    covariance_all = np.asarray(fitted_model.cov_params(), dtype=float)
    fixed_parameter_covariance = covariance_all[
        :expected_fixed,
        :expected_fixed,
    ]
    coefficient_standard_errors = np.empty(
        (n_coefficients, n_time),
        dtype=float,
    )
    for coefficient_index in range(n_coefficients):
        block_start = coefficient_index * fixed_basis_size
        block_stop = block_start + fixed_basis_size
        block = fixed_parameter_covariance[
            block_start:block_stop,
            block_start:block_stop,
        ]
        variance = np.einsum(
            "ti,ij,tj->t",
            fixed_basis,
            block,
            fixed_basis,
            optimize=True,
        )
        coefficient_standard_errors[coefficient_index] = np.sqrt(
            np.maximum(variance, 0.0)
        )

    random_effect_covariance = np.asarray(
        fitted_model.cov_re,
        dtype=float,
    )
    expected_covariance_shape = (
        random_effect_dimension,
        random_effect_dimension,
    )
    if random_effect_covariance.shape != expected_covariance_shape:
        raise RuntimeError(
            "backend returned an unexpected random-effect covariance shape"
        )
    if not np.all(np.isfinite(random_effect_covariance)):
        raise RuntimeError(
            "backend returned non-finite random-effect covariance values"
        )
    if not np.allclose(
        random_effect_covariance,
        random_effect_covariance.T,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise RuntimeError(
            "backend returned a non-symmetric random-effect covariance"
        )

    covariance_eigenvalues = np.linalg.eigvalsh(random_effect_covariance)
    covariance_scale = max(
        1.0,
        float(np.max(np.abs(random_effect_covariance))),
    )
    negative_tolerance = 1e-10 * covariance_scale
    if float(np.min(covariance_eigenvalues)) < -negative_tolerance:
        raise RuntimeError(
            "fitted random-effect covariance is not positive semidefinite"
        )

    boundary_fit = bool(
        float(np.min(covariance_eigenvalues))
        <= 1e-8 * covariance_scale
    )
    largest_covariance_eigenvalue = float(
        np.max(np.abs(covariance_eigenvalues))
    )
    singular_tolerance = max(
        np.finfo(float).eps * max(1.0, largest_covariance_eigenvalue),
        1e-14,
    )
    random_effect_singular = bool(
        float(np.min(covariance_eigenvalues)) <= singular_tolerance
    )
    if float(np.min(covariance_eigenvalues)) <= 0.0:
        covariance_condition_number = float("inf")
    else:
        covariance_condition_number = float(
            np.max(covariance_eigenvalues)
            / np.min(covariance_eigenvalues)
        )

    random_intercept_covariance = random_effect_covariance[
        :random_basis_size,
        :random_basis_size,
    ].copy()
    if has_random_slope:
        random_slope_covariance = random_effect_covariance[
            random_basis_size:,
            random_basis_size:,
        ].copy()
        random_intercept_slope_covariance = random_effect_covariance[
            :random_basis_size,
            random_basis_size:,
        ].copy()
        slope_eigenvalues = np.linalg.eigvalsh(random_slope_covariance)
        slope_boundary_reference = max(
            largest_covariance_eigenvalue,
            np.finfo(float).eps,
        )
        random_slope_boundary_fit = bool(
            float(np.max(slope_eigenvalues))
            <= 0.10 * slope_boundary_reference
            or float(np.min(slope_eigenvalues))
            <= 1e-8 * covariance_scale
        )
    else:
        random_slope_covariance = None
        random_intercept_slope_covariance = None
        random_slope_boundary_fit = False

    random_effect_coefficients = np.empty(
        (len(participant_ids), random_effect_dimension),
        dtype=float,
    )
    for participant_index, participant_id in enumerate(participant_ids):
        try:
            random_values = np.asarray(
                fitted_model.random_effects[participant_id],
                dtype=float,
            )
        except Exception as exc:
            raise RuntimeError(
                "backend could not recover participant random effects"
            ) from exc
        if random_values.size != random_effect_dimension:
            raise RuntimeError(
                "backend returned an unexpected participant random-effect "
                "dimension"
            )
        random_effect_coefficients[participant_index] = random_values

    random_intercept_coefficients = random_effect_coefficients[
        :, :random_basis_size
    ].copy()
    random_intercept_functions = (
        random_intercept_coefficients @ random_basis.T
    )
    if has_random_slope:
        random_slope_coefficients = random_effect_coefficients[
            :, random_basis_size:
        ].copy()
        random_slope_functions = random_slope_coefficients @ random_basis.T
    else:
        random_slope_coefficients = None
        random_slope_functions = None

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
            fixed_fitted[curve_index] + random_contribution
        )
    observed_functions = trajectories.values[:, :, dimension_index].copy()
    residual_functions = observed_functions - fitted_functions
    residual_variance = float(fitted_model.scale)
    whitened_residual_functions = (
        residual_functions / np.sqrt(residual_variance)
    )
    residual_correlation_matrix = np.eye(n_time, dtype=float)

    return FunctionalMixedEffectsResult(
        coefficient_functions=coefficient_functions,
        coefficient_standard_errors=coefficient_standard_errors,
        fixed_basis_coefficients=fixed_basis_coefficients,
        fixed_parameter_covariance=fixed_parameter_covariance,
        fixed_basis=fixed_basis,
        fixed_basis_knots=fixed_knots,
        random_basis=random_basis,
        random_basis_knots=random_knots,
        random_intercept_basis=random_basis.copy(),
        random_slope_basis=(
            None if not has_random_slope else random_basis.copy()
        ),
        random_effect_design_matrix=random_exog.copy(),
        random_effect_coefficients=random_effect_coefficients,
        random_effect_functions=random_effect_functions,
        random_intercept_coefficients=random_intercept_coefficients,
        random_slope_coefficients=random_slope_coefficients,
        random_intercept_functions=random_intercept_functions,
        random_slope_functions=random_slope_functions,
        random_effect_covariance=random_effect_covariance,
        random_intercept_covariance=random_intercept_covariance,
        random_slope_covariance=random_slope_covariance,
        random_intercept_slope_covariance=random_intercept_slope_covariance,
        random_effect_covariance_eigenvalues=covariance_eigenvalues.copy(),
        random_effect_covariance_condition_number=covariance_condition_number,
        random_effect_dimension=random_effect_dimension,
        random_effect_covariance_parameter_count=covariance_parameter_count,
        random_effect_complexity_warning=covariance_complexity_warning,
        random_effect_singular=random_effect_singular,
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
        curve_participant_ids=tuple(curve_participants),
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
        boundary_fit=boundary_fit,
        backend_warnings=warning_messages,
        log_likelihood=float(fitted_model.llf),
        provenance={
            **dict(trajectories.provenance),
            "functional_mixed_effects_regression": {
                "method": "joint_stacked_gaussian_linear_mixed_model",
                "backend": "statsmodels.MixedLM",
                "response_dimension": dimension_name,
                "participant_column": participant_column,
                "n_source_curves": trajectories.n_curves,
                "n_participants": len(participant_ids),
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
                "spline_degree": spline_degree,
                "basis_size_selected_automatically": False,
                "smoothing_penalty": False,
                "categorical_encoding": False,
                "predictor_centering": False,
                "predictor_scaling": False,
                "interaction_construction": False,
                "automatic_model_selection": False,
                "automatic_random_slope_selection": False,
                "random_effect": (
                    "participant_functional_intercept"
                    if not has_random_slope
                    else "participant_functional_intercept_plus_one_slope"
                ),
                "random_slope_predictor": random_slope_predictor,
                "random_effect_dimension": random_effect_dimension,
                "random_effect_design_rank": random_design_rank,
                "random_basis_covariance": "unstructured",
                "random_effect_covariance_parameter_count": (
                    covariance_parameter_count
                ),
                "participants_per_covariance_parameter": float(
                    len(participant_ids) / covariance_parameter_count
                ),
                "covariance_complexity_warning": (
                    covariance_complexity_warning
                ),
                "covariance_complexity_warning_rule": (
                    "n_participants <= random_effect_covariance_parameter_count"
                ),
                "random_slope_covariance_complexity_guard": (
                    "require n_participants > covariance_parameter_count"
                    if has_random_slope
                    else None
                ),
                "random_slope_boundary_rule": (
                    "max_slope_covariance_eigenvalue <= "
                    "0.10 * max_abs_full_covariance_eigenvalue OR "
                    "min_slope_covariance_eigenvalue <= 1e-8 * covariance_scale"
                    if has_random_slope
                    else None
                ),
                "random_effect_covariance_eigenvalues": (
                    covariance_eigenvalues.tolist()
                ),
                "random_effect_covariance_condition_number": (
                    covariance_condition_number
                ),
                "random_effect_singular": random_effect_singular,
                "random_slope_boundary_fit": random_slope_boundary_fit,
                "random_effect_functions_legacy_alias": (
                    "random_intercept_functions"
                ),
                "curve_level_functional_random_effect": False,
                "residual_structure": (
                    "conditionally_iid_gaussian_grid_errors"
                ),
                "residual_correlation": "iid",
                "automatic_residual_correlation_selection": False,
                "residual_correlation_crosses_trial_boundaries": False,
                "trial_varying_predictors_supported": True,
                "random_slope_requires_within_participant_variation": (
                    has_random_slope
                ),
                "joint_fit_over_all_time_points": True,
                "pointwise_mixed_models": False,
                "multivariate_cross_dimension_covariance": False,
                "reml": reml,
                "optimizer": method,
                "maxiter": maxiter,
                "converged": True,
                "boundary_fit": boundary_fit,
                "backend_warnings": list(warning_messages),
            },
        },
        model=fitted_model,
        residual_correlation="iid",
        residual_correlation_parameter=None,
        residual_correlation_parameter_name=None,
        residual_correlation_parameter_unit=None,
        residual_correlation_matrix=residual_correlation_matrix,
        residual_correlation_eigenvalues=np.ones(n_time, dtype=float),
        residual_correlation_condition_number=1.0,
        residual_correlation_boundary_fit=False,
        residual_correlation_optimizer_bounds=None,
        residual_correlation_grid_regular=bool(
            np.allclose(
                np.diff(trajectories.time),
                np.diff(trajectories.time)[0],
                rtol=1e-8,
                atol=max(
                    1e-12,
                    abs(float(np.diff(trajectories.time)[0])) * 1e-10,
                ),
            )
        ),
        residual_correlation_grid_interval=(
            float(np.diff(trajectories.time)[0])
            if np.allclose(
                np.diff(trajectories.time),
                np.diff(trajectories.time)[0],
                rtol=1e-8,
                atol=max(
                    1e-12,
                    abs(float(np.diff(trajectories.time)[0])) * 1e-10,
                ),
            )
            else None
        ),
        whitened_residual_functions=whitened_residual_functions,
    )


def functional_mixed_effects_coefficient_frame(
    result: FunctionalMixedEffectsResult,
    *,
    band: FunctionalMixedEffectsBandResult | None = None,
) -> pd.DataFrame:
    """Return fixed-effect coefficient functions and optional simultaneous bands."""

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if band is not None:
        if not isinstance(band, FunctionalMixedEffectsBandResult):
            raise TypeError(
                "band must be a FunctionalMixedEffectsBandResult or None"
            )
        if band.reference is not result:
            raise ValueError("band.reference must be the supplied result object")

    rows: list[dict[str, float | str]] = []
    z_value = 1.959963984540054
    for coefficient_index, coefficient_name in enumerate(
        result.coefficient_names
    ):
        for time_index, time_value in enumerate(result.time):
            estimate = float(
                result.coefficient_functions[
                    coefficient_index,
                    time_index,
                ]
            )
            standard_error = float(
                result.coefficient_standard_errors[
                    coefficient_index,
                    time_index,
                ]
            )
            row: dict[str, float | str] = {
                "coefficient": coefficient_name,
                "time": float(time_value),
                "dimension": result.dimension_name,
                "estimate": estimate,
                "standard_error": standard_error,
                "lower_95_wald": estimate - z_value * standard_error,
                "upper_95_wald": estimate + z_value * standard_error,
            }
            if band is not None:
                row.update(
                    {
                        "bootstrap_standard_error": float(
                            band.pointwise_standard_errors[
                                coefficient_index,
                                time_index,
                            ]
                        ),
                        "lower_simultaneous": float(
                            band.lower[
                                coefficient_index,
                                time_index,
                            ]
                        ),
                        "upper_simultaneous": float(
                            band.upper[
                                coefficient_index,
                                time_index,
                            ]
                        ),
                        "simultaneous_critical_value": float(
                            band.critical_values[coefficient_index]
                        ),
                        "simultaneous_scope": band.simultaneous_scope,
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def functional_random_effect_frame(
    result: FunctionalMixedEffectsResult,
    *,
    effect: str = "intercept",
) -> pd.DataFrame:
    """Return participant BLUP functional random effects in long form."""

    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if effect not in {"intercept", "slope"}:
        raise ValueError("effect must be 'intercept' or 'slope'")

    if effect == "intercept":
        functions = result.random_intercept_functions
        predictor = None
    else:
        if result.random_slope_functions is None:
            raise ValueError(
                "result does not contain a participant random functional slope"
            )
        functions = result.random_slope_functions
        predictor = result.random_slope_predictor

    rows: list[dict[str, float | str | None]] = []
    for participant_index, participant_id in enumerate(result.participant_ids):
        for time_index, time_value in enumerate(result.time):
            rows.append(
                {
                    "participant_id": participant_id,
                    "time": float(time_value),
                    "dimension": result.dimension_name,
                    "effect": effect,
                    "random_slope_predictor": predictor,
                    "estimate": float(
                        functions[participant_index, time_index]
                    ),
                }
            )
    return pd.DataFrame(rows)
