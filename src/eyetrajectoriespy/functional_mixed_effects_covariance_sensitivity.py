"""Descriptive covariance-structure sensitivity for functional mixed models.

Version 0.50 compares predeclared, already fitted covariance structures against
one analyst-declared reference.  It deliberately does not fit covariance
combinations, rank models, select a winner, or attach likelihood-ratio p-values.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from .functional_mixed_effects_diagnostics import (
    functional_mixed_effects_residual_diagnostics,
)
from .functional_mixed_effects_nested import (
    functional_mixed_effects_whitened_residuals,
)
from .types import (
    FunctionalMixedEffectsBandResult,
    FunctionalMixedEffectsCovarianceSensitivityResult,
    FunctionalMixedEffectsCovarianceSpecification,
    FunctionalMixedEffectsFullRefitBootstrapResult,
    FunctionalMixedEffectsResult,
)


def _validate_specification(
    specification: FunctionalMixedEffectsCovarianceSpecification,
) -> None:
    if not isinstance(
        specification,
        FunctionalMixedEffectsCovarianceSpecification,
    ):
        raise TypeError(
            "specifications must contain "
            "FunctionalMixedEffectsCovarianceSpecification objects"
        )
    if not isinstance(specification.name, str) or not specification.name:
        raise ValueError("covariance specification name must be non-empty")
    if specification.random_slope_predictor is not None and (
        not isinstance(specification.random_slope_predictor, str)
        or not specification.random_slope_predictor
    ):
        raise ValueError(
            "random_slope_predictor must be None or a non-empty string"
        )
    if specification.trial_random_effect not in {
        None,
        "functional_intercept",
    }:
        raise ValueError(
            "trial_random_effect must be None or 'functional_intercept'"
        )
    if specification.residual_correlation not in {
        "iid",
        "exponential",
        "ar1",
    }:
        raise ValueError(
            "residual_correlation must be 'iid', 'exponential', or 'ar1'"
        )


def _specification_from_fit(
    name: str,
    fit: FunctionalMixedEffectsResult,
) -> FunctionalMixedEffectsCovarianceSpecification:
    return FunctionalMixedEffectsCovarianceSpecification(
        name=name,
        random_slope_predictor=fit.random_slope_predictor,
        trial_random_effect=fit.trial_random_effect,
        residual_correlation=fit.residual_correlation,
    )


def _validate_fit_matches_specification(
    fit: FunctionalMixedEffectsResult,
    specification: FunctionalMixedEffectsCovarianceSpecification,
) -> None:
    observed = (
        fit.random_slope_predictor,
        fit.trial_random_effect,
        fit.residual_correlation,
    )
    declared = (
        specification.random_slope_predictor,
        specification.trial_random_effect,
        specification.residual_correlation,
    )
    if observed != declared:
        raise ValueError(
            f"fit {specification.name!r} does not match its declared "
            "covariance specification"
        )


def _exact_array_match(
    left: np.ndarray,
    right: np.ndarray,
    *,
    field: str,
) -> None:
    left = np.asarray(left)
    right = np.asarray(right)
    if left.shape != right.shape or not np.array_equal(left, right):
        raise ValueError(
            "covariance sensitivity requires identical "
            f"{field} across successful fits"
        )


def _validate_comparability(
    reference: FunctionalMixedEffectsResult,
    candidate: FunctionalMixedEffectsResult,
    *,
    label: str,
) -> None:
    if not isinstance(candidate, FunctionalMixedEffectsResult):
        raise TypeError(
            f"fit {label!r} must be a FunctionalMixedEffectsResult"
        )
    if not candidate.converged:
        raise ValueError(
            f"fit {label!r} is not converged; retain it in failures instead"
        )

    if tuple(candidate.source_curve_ids) != tuple(reference.source_curve_ids):
        raise ValueError(
            "covariance sensitivity requires identical source curves in the "
            f"same order; fit {label!r} differs"
        )
    _exact_array_match(
        candidate.observed_functions,
        reference.observed_functions,
        field="observed response functions",
    )
    _exact_array_match(
        candidate.scalar_design_matrix,
        reference.scalar_design_matrix,
        field="fixed-effect scalar design matrices",
    )
    _exact_array_match(
        candidate.fixed_basis,
        reference.fixed_basis,
        field="fixed-effect basis evaluations",
    )
    _exact_array_match(
        candidate.fixed_basis_knots,
        reference.fixed_basis_knots,
        field="fixed-effect basis knots",
    )
    _exact_array_match(
        candidate.random_basis,
        reference.random_basis,
        field="participant random-effect basis evaluations",
    )
    _exact_array_match(
        candidate.random_basis_knots,
        reference.random_basis_knots,
        field="participant random-effect basis knots",
    )
    _exact_array_match(
        candidate.time,
        reference.time,
        field="observed time grid",
    )

    if candidate.coefficient_names != reference.coefficient_names:
        raise ValueError(
            "covariance sensitivity requires identical fixed coefficient names"
        )
    if candidate.predictor_names != reference.predictor_names:
        raise ValueError(
            "covariance sensitivity requires identical fixed predictors"
        )
    if candidate.fixed_basis_size != reference.fixed_basis_size:
        raise ValueError(
            "covariance sensitivity requires the same fixed basis size"
        )
    if candidate.random_basis_size != reference.random_basis_size:
        raise ValueError(
            "covariance sensitivity requires the same participant random basis "
            "size; basis sensitivity is a different analysis"
        )
    if candidate.spline_degree != reference.spline_degree:
        raise ValueError(
            "covariance sensitivity requires the same spline degree"
        )
    if candidate.participant_column != reference.participant_column:
        raise ValueError(
            "covariance sensitivity requires the same participant column"
        )
    if tuple(candidate.participant_ids) != tuple(reference.participant_ids):
        raise ValueError(
            "covariance sensitivity requires the same participant identities"
        )
    if tuple(candidate.curve_participant_ids) != tuple(
        reference.curve_participant_ids
    ):
        raise ValueError(
            "covariance sensitivity requires the same curve-to-participant "
            "mapping"
        )
    if candidate.dimension_name != reference.dimension_name:
        raise ValueError(
            "covariance sensitivity requires the same response dimension"
        )
    if candidate.coordinate_system != reference.coordinate_system:
        raise ValueError(
            "covariance sensitivity requires the same coordinate system"
        )
    if candidate.time_unit != reference.time_unit:
        raise ValueError(
            "covariance sensitivity requires the same time unit"
        )
    if candidate.reml != reference.reml:
        raise ValueError(
            "covariance sensitivity refuses ML-versus-REML likelihood "
            "comparison; all successful fits must use the same likelihood mode"
        )

    if (
        candidate.trial_random_effect is not None
        and reference.trial_random_effect is not None
    ):
        if tuple(candidate.curve_trial_ids) != tuple(reference.curve_trial_ids):
            raise ValueError(
                "successful fits that both contain trial random effects must "
                "use the same source trial identities"
            )
        _exact_array_match(
            candidate.trial_random_basis,
            reference.trial_random_basis,
            field="trial random-effect basis evaluations",
        )
        _exact_array_match(
            candidate.trial_random_basis_knots,
            reference.trial_random_basis_knots,
            field="trial random-effect basis knots",
        )


def _parameter_counts(
    fit: FunctionalMixedEffectsResult,
) -> tuple[int, int, int]:
    fixed = fit.n_coefficients * fit.fixed_basis_size
    covariance = (
        fit.random_effect_covariance_parameter_count
        + fit.trial_random_effect_covariance_parameter_count
        + 1
        + int(fit.residual_correlation != "iid")
    )
    total = fixed + covariance
    criterion = covariance if fit.reml else total
    return fixed, covariance, criterion


def _l2_grid_norm(values: np.ndarray, time: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    time = np.asarray(time, dtype=float)
    if values.size < 2:
        return 0.0
    squared = values * values
    delta = np.diff(time)
    integral = np.sum(
        0.5 * (squared[:-1] + squared[1:]) * delta
    )
    return float(np.sqrt(max(float(integral), 0.0)))


def functional_mixed_effects_variance_decomposition(
    fit: FunctionalMixedEffectsResult,
    *,
    model_label: str | None = None,
) -> pd.DataFrame:
    """Return participant/trial/residual variance functions on the time grid.

    Participant random-intercept variance, random-slope variance, and
    intercept/slope cross-covariance are kept separate.  The function does not
    collapse them into a percentage or a preferred covariance decomposition.
    """

    if not isinstance(fit, FunctionalMixedEffectsResult):
        raise TypeError("fit must be a FunctionalMixedEffectsResult")
    label = "model" if model_label is None else str(model_label)
    if not label:
        raise ValueError("model_label must be non-empty when supplied")

    time = np.asarray(fit.time, dtype=float)
    basis = np.asarray(fit.random_basis, dtype=float)
    rows: list[dict[str, object]] = []

    def add_component(
        component: str,
        values: np.ndarray,
        component_type: str,
    ) -> None:
        for index, value in enumerate(np.asarray(values, dtype=float)):
            rows.append(
                {
                    "model": label,
                    "component": component,
                    "component_type": component_type,
                    "time": float(time[index]),
                    "value": float(value),
                }
            )

    intercept_variance = np.einsum(
        "ti,ij,tj->t",
        basis,
        np.asarray(fit.random_intercept_covariance, dtype=float),
        basis,
        optimize=True,
    )
    add_component(
        "participant_intercept_variance",
        intercept_variance,
        "variance",
    )

    if fit.random_slope_covariance is not None:
        slope_variance = np.einsum(
            "ti,ij,tj->t",
            basis,
            np.asarray(fit.random_slope_covariance, dtype=float),
            basis,
            optimize=True,
        )
        add_component(
            "participant_slope_variance",
            slope_variance,
            "variance",
        )
        if fit.random_intercept_slope_covariance is None:
            raise ValueError(
                "random slope covariance is present without intercept/slope "
                "cross-covariance"
            )
        cross_covariance = np.einsum(
            "ti,ij,tj->t",
            basis,
            np.asarray(
                fit.random_intercept_slope_covariance,
                dtype=float,
            ),
            basis,
            optimize=True,
        )
        add_component(
            "participant_intercept_slope_cross_covariance",
            cross_covariance,
            "covariance",
        )

    if fit.trial_random_effect == "functional_intercept":
        if (
            fit.trial_random_basis is None
            or fit.trial_random_effect_covariance is None
        ):
            raise ValueError(
                "trial random-effect result is missing its basis/covariance"
            )
        trial_basis = np.asarray(
            fit.trial_random_basis,
            dtype=float,
        )
        trial_variance = np.einsum(
            "ti,ij,tj->t",
            trial_basis,
            np.asarray(
                fit.trial_random_effect_covariance,
                dtype=float,
            ),
            trial_basis,
            optimize=True,
        )
        add_component(
            "trial_variance",
            trial_variance,
            "variance",
        )

    add_component(
        "residual_variance",
        np.full(time.size, fit.residual_variance, dtype=float),
        "variance",
    )
    return pd.DataFrame(rows)


def _diagnostic_tables(
    label: str,
    fit: FunctionalMixedEffectsResult,
    *,
    max_lag: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    frames: list[pd.DataFrame] = []
    summary: dict[str, float] = {}
    for scale in ("raw", "whitened"):
        diagnostics = functional_mixed_effects_residual_diagnostics(
            fit,
            max_lag=max_lag,
            residual_scale=scale,
        )
        frame = diagnostics.overall_diagnostics.copy()
        frame.insert(0, "model", label)
        frame.insert(1, "residual_scale", scale)
        residuals = (
            np.asarray(fit.residual_functions, dtype=float)
            if scale == "raw"
            else functional_mixed_effects_whitened_residuals(fit)
        )
        rms = float(np.sqrt(np.mean(residuals * residuals)))
        frame["residual_rms_global"] = rms

        positive = frame.loc[
            frame["lag_index"] > 0,
            "autocorrelation",
        ].to_numpy(dtype=float)
        finite = positive[np.isfinite(positive)]
        max_abs = (
            float(np.max(np.abs(finite)))
            if finite.size
            else float("nan")
        )
        acf_energy = (
            float(np.sum(finite * finite))
            if finite.size
            else float("nan")
        )
        pair_count = int(
            frame.loc[frame["lag_index"] > 0, "n_pairs"].sum()
        )
        summary[f"{scale}_residual_rms"] = rms
        summary[f"{scale}_max_abs_acf_positive_lags"] = max_abs
        summary[f"{scale}_acf_energy_positive_lags"] = acf_energy
        summary[f"{scale}_positive_lag_pair_count"] = float(pair_count)
        frames.append(frame)

    return pd.concat(frames, ignore_index=True), summary


def _validate_bands(
    fits: Mapping[str, FunctionalMixedEffectsResult],
    bands: Mapping[str, FunctionalMixedEffectsBandResult],
    *,
    reference: str,
) -> None:
    unknown = set(bands) - set(fits)
    if unknown:
        raise ValueError(
            "bands contain labels without successful fits: "
            f"{sorted(unknown)}"
        )
    if not bands:
        return
    if reference not in bands:
        raise ValueError(
            "band-width sensitivity requires a band for the declared reference"
        )

    reference_band = bands[reference]
    for label, band in bands.items():
        if not isinstance(band, FunctionalMixedEffectsBandResult):
            raise TypeError(
                f"band {label!r} must be a FunctionalMixedEffectsBandResult"
            )
        if band.reference is not fits[label]:
            raise ValueError(
                f"band {label!r} does not reference the supplied fit object"
            )
        if band.confidence_level != reference_band.confidence_level:
            raise ValueError(
                "all supplied sensitivity bands must use the same confidence "
                "level"
            )
        if band.simultaneous_scope != reference_band.simultaneous_scope:
            raise ValueError(
                "all supplied sensitivity bands must use the same simultaneous "
                "scope"
            )
        if type(band.bootstrap) is not type(reference_band.bootstrap):
            raise ValueError(
                "all supplied sensitivity bands must use the same bootstrap "
                "contract"
            )
        if band.bootstrap.n_bootstrap != reference_band.bootstrap.n_bootstrap:
            raise ValueError(
                "all supplied sensitivity bands must use the same number of "
                "bootstrap replicates"
            )
        if not np.array_equal(
            band.bootstrap.sampled_participant_indices,
            reference_band.bootstrap.sampled_participant_indices,
        ):
            raise ValueError(
                "band-width sensitivity requires identical participant "
                "bootstrap draws across supplied models"
            )


def _band_width_frame(
    fits: Mapping[str, FunctionalMixedEffectsResult],
    bands: Mapping[str, FunctionalMixedEffectsBandResult],
    *,
    reference: str,
) -> pd.DataFrame:
    if not bands:
        return pd.DataFrame(
            columns=[
                "model",
                "coefficient",
                "time",
                "band_width",
                "reference_band_width",
                "band_width_ratio_to_reference",
            ]
        )

    reference_band = bands[reference]
    reference_width = reference_band.upper - reference_band.lower
    rows: list[dict[str, object]] = []
    for label in fits:
        if label not in bands:
            continue
        band = bands[label]
        width = band.upper - band.lower
        for coefficient_index, coefficient_name in enumerate(
            band.reference.coefficient_names
        ):
            for time_index, time_value in enumerate(band.reference.time):
                denominator = float(
                    reference_width[coefficient_index, time_index]
                )
                numerator = float(width[coefficient_index, time_index])
                rows.append(
                    {
                        "model": label,
                        "coefficient": coefficient_name,
                        "time": float(time_value),
                        "band_width": numerator,
                        "reference_band_width": denominator,
                        "band_width_ratio_to_reference": (
                            float(numerator / denominator)
                            if denominator > 0
                            else float("nan")
                        ),
                    }
                )
    return pd.DataFrame(rows)


def functional_mixed_effects_covariance_sensitivity(
    fits: Mapping[str, FunctionalMixedEffectsResult],
    *,
    reference: str,
    max_lag: int,
    specifications: Sequence[
        FunctionalMixedEffectsCovarianceSpecification
    ]
    | None = None,
    failures: Mapping[str, str] | None = None,
    bands: Mapping[str, FunctionalMixedEffectsBandResult] | None = None,
) -> FunctionalMixedEffectsCovarianceSensitivityResult:
    """Compare already fitted, predeclared covariance structures descriptively.

    The routine never fits a model, ranks structures, returns a best model,
    performs a likelihood-ratio test, or selects a covariance family.
    """

    if not isinstance(fits, Mapping):
        raise TypeError("fits must be a mapping from label to fitted result")
    if not fits:
        raise ValueError("fits must contain at least one successful model")
    if not isinstance(reference, str) or not reference:
        raise TypeError("reference must be a non-empty model label")
    if reference not in fits:
        raise ValueError(
            "reference must identify a successful supplied fit"
        )
    if isinstance(max_lag, bool) or not isinstance(
        max_lag,
        (int, np.integer),
    ):
        raise TypeError("max_lag must be an integer")
    max_lag = int(max_lag)
    if max_lag < 1:
        raise ValueError("max_lag must be at least 1")

    fit_map = dict(fits)
    for label, fit in fit_map.items():
        if not isinstance(label, str) or not label:
            raise ValueError("fit labels must be non-empty strings")
        if not isinstance(fit, FunctionalMixedEffectsResult):
            raise TypeError(
                f"fit {label!r} must be a FunctionalMixedEffectsResult"
            )

    failure_map = {} if failures is None else dict(failures)
    overlap = set(fit_map) & set(failure_map)
    if overlap:
        raise ValueError(
            "a declared model cannot be both successful and failed: "
            f"{sorted(overlap)}"
        )
    for label, reason in failure_map.items():
        if not isinstance(label, str) or not label:
            raise ValueError("failure labels must be non-empty strings")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"failure reason for {label!r} must be a non-empty string"
            )

    if specifications is None:
        if failure_map:
            raise ValueError(
                "specifications are required when failed declared models are "
                "retained, so their intended covariance structures remain "
                "auditable"
            )
        specification_tuple = tuple(
            _specification_from_fit(label, fit)
            for label, fit in fit_map.items()
        )
    else:
        specification_tuple = tuple(specifications)
        if not specification_tuple:
            raise ValueError("specifications must not be empty")
        for specification in specification_tuple:
            _validate_specification(specification)
        names = [item.name for item in specification_tuple]
        if len(set(names)) != len(names):
            raise ValueError("covariance specification names must be unique")
        declared = set(names)
        supplied = set(fit_map) | set(failure_map)
        if declared != supplied:
            raise ValueError(
                "specification names must match the union of successful fits "
                "and retained failures exactly"
            )

    specification_by_name = {
        specification.name: specification
        for specification in specification_tuple
    }
    for label, fit in fit_map.items():
        _validate_fit_matches_specification(
            fit,
            specification_by_name[label],
        )

    reference_fit = fit_map[reference]
    if not reference_fit.converged:
        raise ValueError("reference fit must be converged")
    if max_lag >= reference_fit.time.size:
        raise ValueError(
            "max_lag must be smaller than the number of observed time points"
        )

    for label, fit in fit_map.items():
        _validate_comparability(
            reference_fit,
            fit,
            label=label,
        )

    band_map = {} if bands is None else dict(bands)
    _validate_bands(fit_map, band_map, reference=reference)

    reference_fixed, reference_covariance, reference_ic = (
        _parameter_counts(reference_fit)
    )
    reference_ll = float(reference_fit.log_likelihood)
    n_observations = reference_fit.n_curves * reference_fit.time.size
    reference_aic = -2.0 * reference_ll + 2.0 * reference_ic
    reference_bic = (
        -2.0 * reference_ll
        + np.log(float(n_observations)) * reference_ic
    )

    model_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    coefficient_summary_rows: list[dict[str, object]] = []
    variance_frames: list[pd.DataFrame] = []
    diagnostic_frames: list[pd.DataFrame] = []

    for specification in specification_tuple:
        label = specification.name
        if label in failure_map:
            model_rows.append(
                {
                    "model": label,
                    "status": "failed",
                    "converged": False,
                    "failure_reason": failure_map[label],
                    "is_reference": False,
                    "random_slope_predictor": (
                        specification.random_slope_predictor
                    ),
                    "trial_random_effect": specification.trial_random_effect,
                    "residual_correlation": (
                        specification.residual_correlation
                    ),
                    "reml": reference_fit.reml,
                    "log_likelihood": float("nan"),
                    "n_parameters": float("nan"),
                    "information_criterion_parameter_count": float("nan"),
                    "n_observations": n_observations,
                    "aic": float("nan"),
                    "bic": float("nan"),
                    "delta_log_likelihood": float("nan"),
                    "delta_aic": float("nan"),
                    "delta_bic": float("nan"),
                    "band_available": False,
                }
            )
            continue

        fit = fit_map[label]
        fixed_count, covariance_count, criterion_count = _parameter_counts(
            fit
        )
        total_parameters = fixed_count + covariance_count
        log_likelihood = float(fit.log_likelihood)
        aic = -2.0 * log_likelihood + 2.0 * criterion_count
        bic = (
            -2.0 * log_likelihood
            + np.log(float(n_observations)) * criterion_count
        )
        diagnostics_frame, diagnostic_summary = _diagnostic_tables(
            label,
            fit,
            max_lag=max_lag,
        )
        diagnostic_frames.append(diagnostics_frame)

        variance = functional_mixed_effects_variance_decomposition(
            fit,
            model_label=label,
        )
        variance_frames.append(variance)

        trial_trace = (
            float(np.trace(fit.trial_random_effect_covariance))
            if fit.trial_random_effect_covariance is not None
            else float("nan")
        )
        participant_trace = float(
            np.trace(fit.random_intercept_covariance)
        )
        slope_trace = (
            float(np.trace(fit.random_slope_covariance))
            if fit.random_slope_covariance is not None
            else float("nan")
        )

        model_rows.append(
            {
                "model": label,
                "status": "success",
                "converged": bool(fit.converged),
                "failure_reason": None,
                "is_reference": label == reference,
                "random_slope_predictor": fit.random_slope_predictor,
                "trial_random_effect": fit.trial_random_effect,
                "residual_correlation": fit.residual_correlation,
                "residual_correlation_parameter": (
                    fit.residual_correlation_parameter
                ),
                "residual_correlation_parameter_name": (
                    fit.residual_correlation_parameter_name
                ),
                "residual_correlation_parameter_unit": (
                    fit.residual_correlation_parameter_unit
                ),
                "residual_variance": float(fit.residual_variance),
                "participant_intercept_covariance_trace": participant_trace,
                "participant_slope_covariance_trace": slope_trace,
                "trial_covariance_trace": trial_trace,
                "participant_covariance_condition_number": (
                    fit.random_effect_covariance_condition_number
                ),
                "trial_covariance_condition_number": (
                    fit.trial_random_effect_covariance_condition_number
                ),
                "residual_correlation_condition_number": (
                    fit.residual_correlation_condition_number
                ),
                "participant_covariance_boundary_or_singular": bool(
                    fit.boundary_fit or fit.random_effect_singular
                ),
                "trial_covariance_boundary_or_singular": bool(
                    fit.trial_random_effect_boundary_fit
                    or fit.trial_random_effect_singular
                ),
                "residual_correlation_boundary_fit": bool(
                    fit.residual_correlation_boundary_fit
                ),
                "residual_correlation_independence_limit_fit": bool(
                    fit.residual_correlation_independence_limit_fit
                ),
                "reml": bool(fit.reml),
                "log_likelihood": log_likelihood,
                "n_fixed_parameters": fixed_count,
                "n_covariance_parameters": covariance_count,
                "n_parameters": total_parameters,
                "information_criterion_parameter_count": criterion_count,
                "n_observations": n_observations,
                "aic": float(aic),
                "bic": float(bic),
                "delta_log_likelihood": float(
                    log_likelihood - reference_ll
                ),
                "delta_aic": float(aic - reference_aic),
                "delta_bic": float(bic - reference_bic),
                "band_available": label in band_map,
                **diagnostic_summary,
            }
        )

        difference = (
            np.asarray(fit.coefficient_functions, dtype=float)
            - np.asarray(reference_fit.coefficient_functions, dtype=float)
        )
        for coefficient_index, coefficient_name in enumerate(
            fit.coefficient_names
        ):
            values = difference[coefficient_index]
            coefficient_summary_rows.append(
                {
                    "model": label,
                    "coefficient": coefficient_name,
                    "sup_abs_difference_from_reference": float(
                        np.max(np.abs(values))
                    ),
                    "l2_difference_from_reference": _l2_grid_norm(
                        values,
                        fit.time,
                    ),
                }
            )
            for time_index, time_value in enumerate(fit.time):
                coefficient_rows.append(
                    {
                        "model": label,
                        "coefficient": coefficient_name,
                        "time": float(time_value),
                        "estimate": float(
                            fit.coefficient_functions[
                                coefficient_index,
                                time_index,
                            ]
                        ),
                        "reference_estimate": float(
                            reference_fit.coefficient_functions[
                                coefficient_index,
                                time_index,
                            ]
                        ),
                        "difference_from_reference": float(
                            values[time_index]
                        ),
                    }
                )

    model_summary = pd.DataFrame(model_rows)
    coefficient_frame = pd.DataFrame(coefficient_rows)
    coefficient_summary = pd.DataFrame(coefficient_summary_rows)
    variance_decomposition = (
        pd.concat(variance_frames, ignore_index=True)
        if variance_frames
        else pd.DataFrame()
    )
    residual_diagnostics = (
        pd.concat(diagnostic_frames, ignore_index=True)
        if diagnostic_frames
        else pd.DataFrame()
    )
    band_width_frame = _band_width_frame(
        fit_map,
        band_map,
        reference=reference,
    )

    information_criterion_mode = (
        "restricted_likelihood_covariance_parameter_count"
        if reference_fit.reml
        else "maximum_likelihood_total_parameter_count"
    )

    return FunctionalMixedEffectsCovarianceSensitivityResult(
        specifications=specification_tuple,
        reference_label=reference,
        fits=fit_map,
        failures=failure_map,
        model_summary=model_summary,
        coefficient_frame=coefficient_frame,
        coefficient_summary=coefficient_summary,
        band_width_frame=band_width_frame,
        variance_decomposition=variance_decomposition,
        residual_diagnostics=residual_diagnostics,
        max_lag=max_lag,
        provenance={
            "functional_mixed_effects_covariance_sensitivity": {
                "method": (
                    "predeclared_already_fitted_covariance_sensitivity"
                ),
                "reference": reference,
                "declared_model_order": [
                    specification.name
                    for specification in specification_tuple
                ],
                "automatic_model_fitting": False,
                "automatic_model_selection": False,
                "automatic_model_ranking": False,
                "automatic_covariance_selection": False,
                "likelihood_ratio_tests": False,
                "failed_models_retained": True,
                "failed_models_excluded_from_numerical_comparisons": True,
                "comparability_contract": {
                    "same_source_curves_and_order": True,
                    "same_observed_response": True,
                    "same_fixed_design": True,
                    "same_fixed_basis": True,
                    "same_participant_random_basis": True,
                    "same_participant_mapping": True,
                    "same_time_grid": True,
                    "same_response_dimension": True,
                    "same_time_unit": True,
                    "same_ml_reml_choice": True,
                    "explicit_trial_ids_checked_when_both_models_have_trial_effects": True,
                },
                "information_criterion_mode": information_criterion_mode,
                "bic_sample_size_definition": (
                    "n_curves_times_n_observed_time_points"
                ),
                "n_observations_for_bic": n_observations,
                "reml": bool(reference_fit.reml),
                "coefficient_difference_reference": reference,
                "l2_difference_integration": (
                    "trapezoidal_integral_over_observed_time_grid"
                ),
                "residual_diagnostic_max_lag": max_lag,
                "residual_scales": ["raw", "whitened"],
                "whitened_acf_summary_is_descriptive_not_selection_criterion": True,
                "band_comparison_requires_identical_participant_bootstrap_draws": True,
                "trial_serial_competition_is_diagnostic_not_selection_evidence": True,
            }
        },
    )


def plot_covariance_sensitivity_coefficients(
    result: FunctionalMixedEffectsCovarianceSensitivityResult,
    *,
    coefficient: str,
    ax=None,
):
    """Plot coefficient-function differences from the declared reference."""

    import matplotlib.pyplot as plt

    if not isinstance(
        result,
        FunctionalMixedEffectsCovarianceSensitivityResult,
    ):
        raise TypeError(
            "result must be a FunctionalMixedEffectsCovarianceSensitivityResult"
        )
    if coefficient not in set(result.coefficient_frame["coefficient"]):
        raise KeyError(f"Unknown coefficient {coefficient!r}")

    frame = result.coefficient_frame.loc[
        result.coefficient_frame["coefficient"] == coefficient
    ]
    if ax is None:
        _, ax = plt.subplots()
    for label in [
        specification.name for specification in result.specifications
    ]:
        model = frame.loc[frame["model"] == label]
        if model.empty:
            continue
        ax.plot(
            model["time"],
            model["difference_from_reference"],
            label=label,
        )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel(
        f"Time ({result.fits[result.reference_label].time_unit})"
    )
    ax.set_ylabel("Coefficient difference from reference")
    ax.set_title(
        f"Covariance sensitivity: {coefficient}"
    )
    ax.legend()
    return ax


def plot_covariance_sensitivity_band_widths(
    result: FunctionalMixedEffectsCovarianceSensitivityResult,
    *,
    coefficient: str,
    ax=None,
):
    """Plot simultaneous-band width ratios against the declared reference."""

    import matplotlib.pyplot as plt

    if not isinstance(
        result,
        FunctionalMixedEffectsCovarianceSensitivityResult,
    ):
        raise TypeError(
            "result must be a FunctionalMixedEffectsCovarianceSensitivityResult"
        )
    if result.band_width_frame.empty:
        raise ValueError(
            "result does not contain simultaneous-band sensitivity information"
        )
    if coefficient not in set(result.band_width_frame["coefficient"]):
        raise KeyError(f"Unknown coefficient {coefficient!r}")

    frame = result.band_width_frame.loc[
        result.band_width_frame["coefficient"] == coefficient
    ]
    if ax is None:
        _, ax = plt.subplots()
    for label in [
        specification.name for specification in result.specifications
    ]:
        model = frame.loc[frame["model"] == label]
        if model.empty:
            continue
        ax.plot(
            model["time"],
            model["band_width_ratio_to_reference"],
            label=label,
        )
    ax.axhline(1.0, linewidth=1.0)
    ax.set_xlabel(
        f"Time ({result.fits[result.reference_label].time_unit})"
    )
    ax.set_ylabel("Band-width ratio to reference")
    ax.set_title(
        f"Covariance sensitivity of band width: {coefficient}"
    )
    ax.legend()
    return ax


def plot_functional_variance_decomposition(
    result: (
        FunctionalMixedEffectsResult
        | FunctionalMixedEffectsCovarianceSensitivityResult
    ),
    *,
    model: str | None = None,
    ax=None,
):
    """Plot functional variance/cross-covariance components for one fit."""

    import matplotlib.pyplot as plt

    if isinstance(result, FunctionalMixedEffectsResult):
        if model is not None:
            raise ValueError(
                "model is only accepted for a covariance sensitivity result"
            )
        frame = functional_mixed_effects_variance_decomposition(result)
        time_unit = result.time_unit
        title_label = "model"
    elif isinstance(
        result,
        FunctionalMixedEffectsCovarianceSensitivityResult,
    ):
        if model is None:
            raise ValueError(
                "model must be declared when plotting a sensitivity result"
            )
        if model not in result.fits:
            if model in result.failures:
                raise ValueError(
                    f"model {model!r} failed and has no variance decomposition"
                )
            raise KeyError(f"Unknown model {model!r}")
        frame = result.variance_decomposition.loc[
            result.variance_decomposition["model"] == model
        ]
        time_unit = result.fits[model].time_unit
        title_label = model
    else:
        raise TypeError(
            "result must be a FunctionalMixedEffectsResult or "
            "FunctionalMixedEffectsCovarianceSensitivityResult"
        )

    if ax is None:
        _, ax = plt.subplots()
    for component, component_frame in frame.groupby(
        "component",
        sort=False,
    ):
        ax.plot(
            component_frame["time"],
            component_frame["value"],
            label=str(component),
        )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel(f"Time ({time_unit})")
    ax.set_ylabel("Variance / cross-covariance")
    ax.set_title(f"Functional variance decomposition: {title_label}")
    ax.legend()
    return ax


def functional_mixed_effects_covariance_sensitivity_reporting_text(
    result: FunctionalMixedEffectsCovarianceSensitivityResult,
) -> str:
    """Return manuscript-oriented wording without selecting a covariance model."""

    if not isinstance(
        result,
        FunctionalMixedEffectsCovarianceSensitivityResult,
    ):
        raise TypeError(
            "result must be a FunctionalMixedEffectsCovarianceSensitivityResult"
        )
    failed = result.n_failed
    mode = result.provenance[
        "functional_mixed_effects_covariance_sensitivity"
    ]["information_criterion_mode"]
    return (
        "Covariance structures were compared as a predeclared sensitivity "
        f"analysis against reference {result.reference_label!r}. "
        f"{result.n_successful} declared structure(s) converged and {failed} "
        "failed structure(s) were retained explicitly rather than omitted. "
        "Successful fits used identical observations, fixed-effect design and "
        "basis, participant mapping, response dimension, time grid, and "
        "ML/REML mode. Fixed coefficient-function changes, simultaneous-band "
        "widths where supplied, functional participant/trial/residual variance "
        "decomposition, raw and whitened residual dependence, covariance "
        "diagnostics, log likelihood, AIC, and BIC were reported "
        "descriptively. No covariance structure was ranked or automatically "
        "selected and no likelihood-ratio p-values were computed. "
        f"Information criteria used the recorded convention {mode!r}; BIC "
        "used the explicit observation count n_curves × n_time."
    )
