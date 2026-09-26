"""Marginal generalized function-on-scalar regression for repeated curves."""

from __future__ import annotations

from collections.abc import Sequence
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .function_on_scalar import _validate_design_alignment
from .functional_mixed_effects import (
    _bspline_basis,
    _fixed_effect_design,
    _validate_dimension,
)
from .types import (
    GeneralizedFunctionOnScalarBandResult,
    GeneralizedFunctionOnScalarBootstrapResult,
    GeneralizedFunctionOnScalarResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _validate_family_response(
    values: np.ndarray,
    *,
    family: str,
) -> tuple[object, str]:
    family_name = str(family).lower().strip()
    if family_name == "binomial":
        if not np.all(np.isin(values, (0.0, 1.0))):
            raise ValueError(
                "family='binomial' requires Bernoulli functional responses "
                "coded exactly as 0/1 in version 0.51; aggregated proportions "
                "or trial denominators are not silently inferred"
            )
        return sm.families.Binomial(), "logit"
    if family_name == "poisson":
        if np.any(values < 0) or not np.allclose(
            values,
            np.round(values),
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                "family='poisson' requires non-negative integer count "
                "functional responses"
            )
        return sm.families.Poisson(), "log"
    raise ValueError(
        "family must be 'binomial' or 'poisson' for the 0.53 contract"
    )


def _validate_poisson_exposure(
    exposure: np.ndarray | Sequence[float] | None,
    *,
    family: str,
    n_curves: int,
    n_time: int,
) -> tuple[np.ndarray | None, np.ndarray | None, bool]:
    """Validate an explicit Poisson exposure array without inferring it."""

    if exposure is None:
        return None, None, False
    family_name = str(family).lower().strip()
    if family_name != "poisson":
        raise ValueError("exposure is supported only for family='poisson'")

    values = np.asarray(exposure, dtype=float)
    expanded_from_curve = False
    if values.shape == (n_curves,):
        values = np.repeat(values[:, None], n_time, axis=1)
        expanded_from_curve = True
    elif values.shape != (n_curves, n_time):
        raise ValueError(
            "exposure must have shape (n_curves, n_time) or (n_curves,); "
            f"got {values.shape}"
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("exposure must contain only finite values")
    if np.any(values <= 0):
        raise ValueError("exposure must be strictly positive everywhere")
    return values.copy(), np.log(values), expanded_from_curve


def _validate_participant_clusters(
    trajectories: TrajectorySet,
    *,
    participant_column: str,
    n_parameters: int,
) -> tuple[np.ndarray, tuple[str, ...], tuple[int, ...]]:
    if not isinstance(participant_column, str) or not participant_column:
        raise TypeError("participant_column must be a non-empty string")
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column "
            f"{participant_column!r}"
        )
    series = trajectories.metadata[participant_column]
    if series.isna().any():
        raise ValueError("participant_column contains missing values")

    curve_participants = series.astype(str).to_numpy()
    participant_ids = tuple(pd.unique(curve_participants))
    if len(participant_ids) <= n_parameters:
        raise ValueError(
            "generalized function-on-scalar robust cluster inference requires "
            "the participant count to exceed the expanded coefficient "
            "parameter count; "
            f"got {len(participant_ids)} participants and {n_parameters} "
            "parameters. This is a minimum structural guard, not evidence "
            "that the sandwich covariance is adequately estimated."
        )
    curves_per_participant = tuple(
        int(np.count_nonzero(curve_participants == participant_id))
        for participant_id in participant_ids
    )
    return curve_participants, participant_ids, curves_per_participant


def _fit_gee_arrays(
    *,
    observed_functions: np.ndarray,
    scalar_design: np.ndarray,
    curve_participants: np.ndarray,
    basis: np.ndarray,
    family: str,
    exposure: np.ndarray | None,
    maxiter: int,
    ctol: float,
) -> dict[str, object]:
    family_object, link_name = _validate_family_response(
        observed_functions,
        family=family,
    )
    expanded_design = _fixed_effect_design(scalar_design, basis)
    expanded_rank = int(np.linalg.matrix_rank(expanded_design))
    if expanded_rank != expanded_design.shape[1]:
        raise ValueError(
            "expanded generalized function-on-scalar design is rank "
            "deficient; change the declared predictors or basis size"
        )

    endog = np.asarray(observed_functions, dtype=float).reshape(-1)
    groups = np.repeat(
        np.asarray(curve_participants, dtype=str),
        observed_functions.shape[1],
    )

    exposure_vector = (
        None
        if exposure is None
        else np.asarray(exposure, dtype=float).reshape(-1)
    )
    model = sm.GEE(
        endog,
        expanded_design,
        groups=groups,
        family=family_object,
        cov_struct=sm.cov_struct.Independence(),
        exposure=exposure_vector,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fitted = model.fit(
            maxiter=maxiter,
            ctol=ctol,
            cov_type="robust",
        )
    warning_messages = tuple(str(item.message) for item in caught)
    converged = bool(getattr(fitted, "converged", True))
    if not converged:
        raise RuntimeError(
            "generalized function-on-scalar GEE did not converge under the "
            "declared working-independence specification"
        )

    parameters = np.asarray(fitted.params, dtype=float)
    covariance = np.asarray(fitted.cov_params(), dtype=float)
    if not np.all(np.isfinite(parameters)):
        raise RuntimeError("GEE coefficient parameters are non-finite")
    if covariance.shape != (parameters.size, parameters.size):
        raise RuntimeError(
            "GEE robust parameter covariance has an unexpected shape"
        )
    if not np.all(np.isfinite(covariance)):
        raise RuntimeError(
            "GEE robust parameter covariance contains non-finite values"
        )
    if not np.allclose(
        covariance,
        covariance.T,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise RuntimeError("GEE robust parameter covariance is not symmetric")

    n_coefficients = scalar_design.shape[1]
    basis_size = basis.shape[1]
    basis_coefficients = parameters.reshape(
        n_coefficients,
        basis_size,
    )
    coefficient_functions = basis_coefficients @ basis.T

    standard_errors = np.empty(
        (n_coefficients, basis.shape[0]),
        dtype=float,
    )
    for coefficient_index in range(n_coefficients):
        start = coefficient_index * basis_size
        stop = start + basis_size
        block = covariance[start:stop, start:stop]
        pointwise_variance = np.einsum(
            "ti,ij,tj->t",
            basis,
            block,
            basis,
            optimize=True,
        )
        standard_errors[coefficient_index] = np.sqrt(
            np.maximum(pointwise_variance, 0.0)
        )

    linear_rate = scalar_design @ coefficient_functions
    if exposure is None:
        linear_count = linear_rate.copy()
        mean_functions = family_object.link.inverse(linear_rate)
        rate_functions = None
        log_exposure = None
    else:
        log_exposure = np.log(np.asarray(exposure, dtype=float))
        linear_count = linear_rate + log_exposure
        rate_functions = np.exp(linear_rate)
        mean_functions = np.exp(linear_count)
    if not np.all(np.isfinite(mean_functions)):
        raise RuntimeError("GEE fitted marginal means are non-finite")
    if rate_functions is not None and not np.all(np.isfinite(rate_functions)):
        raise RuntimeError("GEE fitted marginal rates are non-finite")

    return {
        "model": model,
        "fitted": fitted,
        "coefficient_functions": coefficient_functions,
        "coefficient_standard_errors": standard_errors,
        "basis_coefficients": basis_coefficients,
        "parameter_covariance": covariance,
        "linear_predictor_functions": linear_rate,
        "linear_predictor_rate": (
            linear_rate
            if exposure is not None
            and str(family).lower().strip() == "poisson"
            else None
        ),
        "linear_predictor_count": (
            linear_count
            if str(family).lower().strip() == "poisson"
            else None
        ),
        "mean_functions": np.asarray(mean_functions, dtype=float),
        "rate_functions": (
            None
            if rate_functions is None
            else np.asarray(rate_functions, dtype=float)
        ),
        "log_exposure": log_exposure,
        "expanded_design_rank": expanded_rank,
        "link_name": link_name,
        "warning_messages": warning_messages,
        "scale": float(fitted.scale),
    }


def fit_generalized_function_on_scalar_regression(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    predictors: Sequence[str],
    *,
    participant_column: str,
    dimension: str,
    family: str,
    exposure: np.ndarray | Sequence[float] | None = None,
    exposure_units: str | None = None,
    basis_size: int = 5,
    spline_degree: int = 3,
    working_correlation: str = "independence",
    covariance_type: str = "robust",
    maxiter: int = 100,
    ctol: float = 1e-8,
) -> GeneralizedFunctionOnScalarResult:
    """Fit a marginal generalized function-on-scalar model by clustered GEE.

    Version 0.53 supports Bernoulli/logit and Poisson/log functional outcomes,
    including an explicit positive exposure contract for Poisson rate models.
    Coefficient functions use an explicitly sized clamped B-spline basis.
    Participants are the independent GEE clusters; trial-varying predictors are
    allowed.  The only working correlation in this tranche is independence,
    paired with the robust sandwich covariance.

    No family, link, basis size, working dependence structure, smoothing
    penalty, categorical encoding, predictor scaling, or model is selected
    automatically.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError(
            "generalized function-on-scalar regression requires finite "
            "complete trajectories"
        )
    if trajectories.coordinate_system == "probability_simplex":
        raise ValueError(
            "generalized function-on-scalar regression does not interpret "
            "simplex-valued AOI probabilities as Bernoulli/count observations"
        )
    if working_correlation != "independence":
        raise ValueError(
            "working_correlation must be 'independence' for the 0.53 "
            "marginal GEE contract"
        )
    if covariance_type != "robust":
        raise ValueError(
            "covariance_type must be 'robust'; naive working-correlation "
            "standard errors are not exposed in 0.53"
        )
    if isinstance(maxiter, bool) or not isinstance(maxiter, int):
        raise TypeError("maxiter must be an integer")
    if maxiter < 1:
        raise ValueError("maxiter must be positive")
    if not np.isfinite(ctol) or ctol <= 0:
        raise ValueError("ctol must be finite and positive")

    aligned_design, predictor_names = _validate_design_alignment(
        trajectories,
        design,
        predictors,
    )
    dimension_index, dimension_name = _validate_dimension(
        trajectories,
        dimension,
    )
    observed_functions = trajectories.values[
        :,
        :,
        dimension_index,
    ].copy()
    _, link_name = _validate_family_response(
        observed_functions,
        family=family,
    )
    exposure_array, log_exposure, exposure_expanded = _validate_poisson_exposure(
        exposure,
        family=family,
        n_curves=trajectories.n_curves,
        n_time=trajectories.n_time,
    )
    if exposure_units is not None:
        if not isinstance(exposure_units, str) or not exposure_units.strip():
            raise TypeError("exposure_units must be a non-empty string or None")
        if exposure_array is None:
            raise ValueError("exposure_units requires an explicit exposure array")
        exposure_units = exposure_units.strip()

    basis, basis_knots = _bspline_basis(
        trajectories.time,
        n_basis=basis_size,
        degree=spline_degree,
    )
    if np.linalg.matrix_rank(basis) != basis_size:
        raise ValueError(
            "generalized function-on-scalar coefficient basis is rank "
            "deficient on the observed grid"
        )

    predictor_matrix = aligned_design.loc[
        :,
        list(predictor_names),
    ].to_numpy(dtype=float)
    scalar_design = np.column_stack(
        [
            np.ones(trajectories.n_curves, dtype=float),
            predictor_matrix,
        ]
    )
    scalar_rank = int(np.linalg.matrix_rank(scalar_design))
    if scalar_rank != scalar_design.shape[1]:
        raise ValueError(
            "scalar design matrix is rank deficient; remove redundant "
            "predictors or encode the model explicitly"
        )
    coefficient_names = ("Intercept",) + predictor_names
    n_parameters = len(coefficient_names) * basis_size

    (
        curve_participants,
        participant_ids,
        curves_per_participant,
    ) = _validate_participant_clusters(
        trajectories,
        participant_column=participant_column,
        n_parameters=n_parameters,
    )

    state = _fit_gee_arrays(
        observed_functions=observed_functions,
        scalar_design=scalar_design,
        curve_participants=curve_participants,
        basis=basis,
        family=family,
        exposure=exposure_array,
        maxiter=maxiter,
        ctol=ctol,
    )

    family_name = str(family).lower().strip()
    return GeneralizedFunctionOnScalarResult(
        coefficient_functions=state["coefficient_functions"],
        coefficient_standard_errors=state[
            "coefficient_standard_errors"
        ],
        basis_coefficients=state["basis_coefficients"],
        parameter_covariance=state["parameter_covariance"],
        basis=basis.copy(),
        basis_knots=basis_knots.copy(),
        linear_predictor_functions=state[
            "linear_predictor_functions"
        ],
        mean_functions=state["mean_functions"],
        observed_functions=observed_functions,
        scalar_design_matrix=scalar_design,
        expanded_design_rank=state["expanded_design_rank"],
        coefficient_names=coefficient_names,
        predictor_names=predictor_names,
        participant_column=participant_column,
        participant_ids=participant_ids,
        curve_participant_ids=tuple(map(str, curve_participants)),
        curves_per_participant=curves_per_participant,
        source_curve_ids=trajectories.curve_ids,
        time=trajectories.time.copy(),
        dimension_name=dimension_name,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        family=family_name,
        link=link_name,
        basis_size=basis_size,
        spline_degree=spline_degree,
        working_correlation=working_correlation,
        covariance_type=covariance_type,
        scale=state["scale"],
        maxiter=maxiter,
        ctol=float(ctol),
        converged=True,
        backend_warnings=state["warning_messages"],
        exposure=(
            None if exposure_array is None else exposure_array.copy()
        ),
        log_exposure=(
            None if log_exposure is None else log_exposure.copy()
        ),
        rate_functions=state["rate_functions"],
        linear_predictor_rate=state["linear_predictor_rate"],
        linear_predictor_count=state["linear_predictor_count"],
        exposure_units=exposure_units,
        exposure_expanded_from_curve=exposure_expanded,
        provenance={
            **dict(trajectories.provenance),
            "generalized_function_on_scalar_regression": {
                "method": "marginal_function_on_scalar_gee",
                "backend": "statsmodels.GEE",
                "family": family_name,
                "link": link_name,
                "response_dimension": dimension_name,
                "participant_column": participant_column,
                "n_participants": len(participant_ids),
                "n_source_curves": trajectories.n_curves,
                "n_grid_observations": int(
                    trajectories.n_curves * trajectories.n_time
                ),
                "coefficient_names": list(coefficient_names),
                "predictors": list(predictor_names),
                "design_alignment": aligned_design.attrs[
                    "eyetrajectoriespy_alignment"
                ],
                "coefficient_basis": "clamped_bspline",
                "basis_size": basis_size,
                "spline_degree": spline_degree,
                "basis_size_selected_automatically": False,
                "smoothing_penalty": False,
                "working_correlation": "independence",
                "working_correlation_selected_automatically": False,
                "covariance_type": "robust_sandwich",
                "independent_cluster": "participant",
                "trial_varying_predictors_supported": True,
                "random_effects": False,
                "conditional_effect_interpretation": False,
                "marginal_population_averaged_interpretation": True,
                "categorical_encoding": False,
                "predictor_centering": False,
                "predictor_scaling": False,
                "interaction_construction": False,
                "automatic_family_selection": False,
                "automatic_link_selection": False,
                "automatic_model_selection": False,
                "cluster_count_guard": (
                    "require n_participants > expanded_coefficient_parameter_count"
                ),
                "expanded_coefficient_parameter_count": n_parameters,
                "cluster_count_guard_is_adequacy_theorem": False,
                "aggregated_binomial_proportions_supported": False,
                "generic_offset_supported": False,
                "poisson_exposure_supported": True,
                "exposure_supplied": exposure_array is not None,
                "exposure_shape": (
                    None
                    if exposure_array is None
                    else list(exposure_array.shape)
                ),
                "exposure_units": exposure_units,
                "exposure_expanded_from_curve": exposure_expanded,
                "exposure_inferred_from_time_grid": False,
                "exposure_inferred_from_trial_duration": False,
                "exposure_inferred_from_metadata": False,
                "exposure_observed_and_fixed": exposure_array is not None,
                "exposure_measurement_uncertainty": False,
                "converged": True,
                "backend_warnings": list(state["warning_messages"]),
            },
        },
        model=state["fitted"],
    )


def bootstrap_generalized_function_on_scalar_coefficients(
    result: GeneralizedFunctionOnScalarResult,
    *,
    n_bootstrap: int = 1000,
    random_state: int | None = 0,
    failed_replicate_policy: str = "raise",
) -> GeneralizedFunctionOnScalarBootstrapResult:
    """Whole-participant case bootstrap for generalized FoSR coefficients."""

    if not isinstance(result, GeneralizedFunctionOnScalarResult):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarResult"
        )
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int):
        raise TypeError("n_bootstrap must be an integer")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100")
    if failed_replicate_policy != "raise":
        raise ValueError(
            "failed_replicate_policy must be 'raise'; failed GEE bootstrap "
            "replicates are not silently dropped or redrawn"
        )

    rng = np.random.default_rng(random_state)
    participant_ids = result.participant_ids
    curve_participants = np.asarray(
        result.curve_participant_ids,
        dtype=str,
    )
    n_participants = len(participant_ids)

    participant_curve_indices = [
        np.flatnonzero(curve_participants == participant_id)
        for participant_id in participant_ids
    ]
    sampled_indices = rng.integers(
        0,
        n_participants,
        size=(n_bootstrap, n_participants),
    )
    bootstrap_coefficients = np.empty(
        (
            n_bootstrap,
            result.n_coefficients,
            result.time.size,
        ),
        dtype=float,
    )
    source_id_audit: list[tuple[str, ...]] = []
    bootstrap_id_audit: list[tuple[str, ...]] = []

    for bootstrap_index in range(n_bootstrap):
        curve_indices: list[int] = []
        groups: list[str] = []
        source_ids: list[str] = []
        bootstrap_ids: list[str] = []

        for draw_index, source_index in enumerate(
            sampled_indices[bootstrap_index]
        ):
            source_id = participant_ids[int(source_index)]
            bootstrap_id = (
                f"bootstrap_{bootstrap_index:04d}_participant_"
                f"{draw_index:04d}"
            )
            indices = participant_curve_indices[int(source_index)]
            curve_indices.extend(int(index) for index in indices)
            groups.extend(bootstrap_id for _ in indices)
            source_ids.append(source_id)
            bootstrap_ids.append(bootstrap_id)

        index = np.asarray(curve_indices, dtype=int)
        try:
            state = _fit_gee_arrays(
                observed_functions=result.observed_functions[index],
                scalar_design=result.scalar_design_matrix[index],
                curve_participants=np.asarray(groups, dtype=str),
                basis=result.basis,
                family=result.family,
                exposure=(
                    None
                    if result.exposure is None
                    else result.exposure[index]
                ),
                maxiter=result.maxiter,
                ctol=result.ctol,
            )
        except Exception as exc:
            raise RuntimeError(
                "generalized function-on-scalar participant bootstrap failed "
                f"at replicate {bootstrap_index}; the replicate was retained "
                "as a failure and was not silently dropped or redrawn"
            ) from exc

        bootstrap_coefficients[bootstrap_index] = state[
            "coefficient_functions"
        ]
        source_id_audit.append(tuple(source_ids))
        bootstrap_id_audit.append(tuple(bootstrap_ids))

    return GeneralizedFunctionOnScalarBootstrapResult(
        reference=result,
        bootstrap_coefficient_functions=bootstrap_coefficients,
        sampled_participant_indices=sampled_indices,
        sampled_source_participant_ids=tuple(source_id_audit),
        sampled_bootstrap_participant_ids=tuple(bootstrap_id_audit),
        random_state=random_state,
        failure_policy=failed_replicate_policy,
        provenance={
            **dict(result.provenance),
            "generalized_function_on_scalar_bootstrap": {
                "method": "whole_participant_case_bootstrap_full_gee_refit",
                "n_bootstrap": n_bootstrap,
                "random_state": random_state,
                "resampling_unit": "participant",
                "whole_participant_curve_bundles_resampled": True,
                "duplicate_source_participants_receive_distinct_group_ids": True,
                "family_refit": result.family,
                "link_refit": result.link,
                "working_correlation_refit": "independence",
                "basis_refit": False,
                "basis_selected_automatically": False,
                "failed_replicate_policy": "raise",
                "failed_replicates_redrawn": False,
                "exposure_observed_and_fixed": result.exposure is not None,
                "exposure_resampled_with_response_bundle": (
                    result.exposure is not None
                ),
                "exposure_measurement_uncertainty": False,
            },
        },
    )


def generalized_function_on_scalar_simultaneous_bands(
    bootstrap: GeneralizedFunctionOnScalarBootstrapResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "coefficient",
) -> GeneralizedFunctionOnScalarBandResult:
    """Calibrate observed-grid link-scale simultaneous coefficient bands."""

    if not isinstance(
        bootstrap,
        GeneralizedFunctionOnScalarBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a GeneralizedFunctionOnScalarBootstrapResult"
        )
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"coefficient", "family"}:
        raise ValueError(
            "simultaneous_scope must be 'coefficient' or 'family'"
        )

    reference = bootstrap.reference
    standard_errors = np.asarray(
        reference.coefficient_standard_errors,
        dtype=float,
    )
    positive = standard_errors > np.finfo(float).eps
    deviations = (
        bootstrap.bootstrap_coefficient_functions
        - reference.coefficient_functions[None, :, :]
    )
    standardized = np.zeros_like(deviations)
    np.divide(
        deviations,
        standard_errors[None, :, :],
        out=standardized,
        where=positive[None, :, :],
    )
    absolute = np.abs(standardized)

    if simultaneous_scope == "coefficient":
        max_statistics = np.max(absolute, axis=2)
        critical_values = np.quantile(
            max_statistics,
            confidence_level,
            axis=0,
            method="higher",
        )
    else:
        family_max = np.max(absolute, axis=(1, 2))
        critical = float(
            np.quantile(
                family_max,
                confidence_level,
                method="higher",
            )
        )
        max_statistics = family_max[:, None]
        critical_values = np.full(
            reference.n_coefficients,
            critical,
            dtype=float,
        )

    lower = (
        reference.coefficient_functions
        - critical_values[:, None] * standard_errors
    )
    upper = (
        reference.coefficient_functions
        + critical_values[:, None] * standard_errors
    )
    return GeneralizedFunctionOnScalarBandResult(
        reference=reference,
        lower=lower,
        upper=upper,
        critical_values=critical_values,
        max_statistics=max_statistics,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
        bootstrap=bootstrap,
        provenance={
            **dict(bootstrap.provenance),
            "generalized_function_on_scalar_simultaneous_band": {
                "confidence_level": confidence_level,
                "simultaneous_scope": simultaneous_scope,
                "coefficient_scale": "link",
                "calibration": "participant_bootstrap_max_standardized_deviation",
                "pointwise_standard_error": "gee_robust_sandwich",
                "response_scale_coefficient_band": False,
                "automatic_model_selection": False,
            },
        },
    )


def generalized_function_on_scalar_coefficient_frame(
    result: (
        GeneralizedFunctionOnScalarResult
        | GeneralizedFunctionOnScalarBandResult
    ),
) -> pd.DataFrame:
    """Return one row per coefficient and observed time point."""

    if isinstance(result, GeneralizedFunctionOnScalarBandResult):
        fit = result.reference
        band = result
    elif isinstance(result, GeneralizedFunctionOnScalarResult):
        fit = result
        band = None
    else:
        raise TypeError(
            "result must be a generalized function-on-scalar fit or band"
        )

    rows: list[dict[str, object]] = []
    for coefficient_index, coefficient_name in enumerate(
        fit.coefficient_names
    ):
        for time_index, time_value in enumerate(fit.time):
            row = {
                "coefficient": coefficient_name,
                "time": float(time_value),
                "estimate": float(
                    fit.coefficient_functions[
                        coefficient_index,
                        time_index,
                    ]
                ),
                "standard_error": float(
                    fit.coefficient_standard_errors[
                        coefficient_index,
                        time_index,
                    ]
                ),
                "scale": "link",
                "family": fit.family,
                "link": fit.link,
            }
            if band is not None:
                row["lower"] = float(
                    band.lower[coefficient_index, time_index]
                )
                row["upper"] = float(
                    band.upper[coefficient_index, time_index]
                )
                row["critical_value"] = float(
                    band.critical_values[coefficient_index]
                )
            rows.append(row)
    return pd.DataFrame(rows)


def generalized_function_on_scalar_exposure_frame(
    result: GeneralizedFunctionOnScalarResult,
) -> pd.DataFrame:
    """Return a per-curve audit of an explicitly supplied Poisson exposure."""

    if not isinstance(result, GeneralizedFunctionOnScalarResult):
        raise TypeError("result must be a GeneralizedFunctionOnScalarResult")
    if result.exposure is None:
        raise ValueError("the fitted model does not contain an exposure array")

    exposure = np.asarray(result.exposure, dtype=float)
    rows = []
    for index, curve_id in enumerate(result.source_curve_ids):
        values = exposure[index]
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        rows.append(
            {
                "curve_id": curve_id,
                "minimum_exposure": minimum,
                "maximum_exposure": maximum,
                "exposure_range": maximum - minimum,
                "exposure_ratio": maximum / minimum,
                "varies_over_time": bool(
                    not np.allclose(values, values[0], rtol=0.0, atol=0.0)
                ),
                "exposure_units": result.exposure_units,
            }
        )
    frame = pd.DataFrame(rows)
    global_min = float(np.min(exposure))
    global_max = float(np.max(exposure))
    curve_means = np.mean(exposure, axis=1)
    frame.attrs["exposure_audit"] = {
        "minimum_exposure": global_min,
        "maximum_exposure": global_max,
        "exposure_range": global_max - global_min,
        "extreme_exposure_ratio": global_max / global_min,
        "varies_over_time": bool(np.any(frame["varies_over_time"])),
        "varies_between_curves": bool(
            not np.allclose(curve_means, curve_means[0], rtol=0.0, atol=0.0)
        ),
        "exposure_units": result.exposure_units,
        "exposure_expanded_from_curve": result.exposure_expanded_from_curve,
        "exposure_observed_and_fixed": True,
        "exposure_measurement_uncertainty": False,
    }
    return frame


def plot_generalized_function_on_scalar_coefficients(
    result: (
        GeneralizedFunctionOnScalarResult
        | GeneralizedFunctionOnScalarBandResult
    ),
    *,
    coefficient: str,
    ax=None,
):
    """Plot one generalized FoSR coefficient on the declared link scale."""

    import matplotlib.pyplot as plt

    if isinstance(result, GeneralizedFunctionOnScalarBandResult):
        fit = result.reference
        band = result
    elif isinstance(result, GeneralizedFunctionOnScalarResult):
        fit = result
        band = None
    else:
        raise TypeError(
            "result must be a generalized function-on-scalar fit or band"
        )
    if coefficient not in fit.coefficient_names:
        raise KeyError(f"Unknown coefficient {coefficient!r}")
    coefficient_index = fit.coefficient_names.index(coefficient)

    if ax is None:
        _, ax = plt.subplots()
    estimate = fit.coefficient_functions[coefficient_index]
    ax.plot(fit.time, estimate, label="estimate")
    if band is not None:
        ax.fill_between(
            fit.time,
            band.lower[coefficient_index],
            band.upper[coefficient_index],
            alpha=0.2,
            label=(
                f"{100 * band.confidence_level:.0f}% simultaneous band"
            ),
        )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel(f"Time ({fit.time_unit})")
    ax.set_ylabel(f"{coefficient} coefficient ({fit.link} scale)")
    ax.set_title(
        f"Generalized function-on-scalar coefficient: {coefficient}"
    )
    ax.legend()
    return ax


def generalized_function_on_scalar_reporting_text(
    result: GeneralizedFunctionOnScalarResult,
    *,
    band: GeneralizedFunctionOnScalarBandResult | None = None,
) -> str:
    """Return manuscript-oriented wording for marginal generalized FoSR."""

    if not isinstance(result, GeneralizedFunctionOnScalarResult):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarResult"
        )
    if band is not None:
        if not isinstance(band, GeneralizedFunctionOnScalarBandResult):
            raise TypeError(
                "band must be a GeneralizedFunctionOnScalarBandResult or None"
            )
        if band.reference is not result:
            raise ValueError("band.reference must be the supplied fit object")

    band_text = (
        " No simultaneous coefficient band was requested."
        if band is None
        else (
            f" A {100 * band.confidence_level:.1f}% observed-grid "
            f"{band.simultaneous_scope}-simultaneous coefficient band was "
            "calibrated on the link scale using whole-participant case "
            f"bootstrap refits ({band.bootstrap.n_bootstrap} replicates)."
        )
    )
    exposure_text = ""
    if result.family == "poisson" and result.exposure is not None:
        exposure_text = (
            " A strictly positive observed exposure was included explicitly "
            f"({result.exposure_units or 'units not declared'}); coefficients "
            "therefore describe marginal log rates and exponentiated "
            "coefficients are rate ratios holding exposure fixed. Exposure "
            "was treated as observed and fixed, was not inferred, and "
            "measurement uncertainty in exposure was not modeled."
        )
    elif result.family == "poisson":
        exposure_text = (
            " No exposure was supplied, so Poisson coefficients describe "
            "marginal log expected counts rather than rates."
        )

    return (
        "Marginal generalized function-on-scalar regression modeled "
        f"{result.dimension_name!r} using a {result.family} family with "
        f"{result.link} link and {result.basis_size} clamped B-spline basis "
        "functions per coefficient. Participants were treated as independent "
        "clusters and within-participant observations were fit with working "
        "independence; coefficient uncertainty used the robust GEE sandwich "
        "covariance. Coefficients therefore have a population-averaged "
        "marginal interpretation on the link scale, not a conditional "
        "random-effects interpretation. No working correlation, smoothing "
        "penalty, exposure definition, family, link, or model was selected "
        "automatically."
        + exposure_text
        + band_text
    )
