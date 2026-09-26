"""Fixed-profile prediction and response-scale contrasts for generalized FoSR."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import expit

from .functional_mixed_effects import _fixed_effect_design
from .types import (
    GeneralizedFunctionOnScalarBootstrapResult,
    GeneralizedFunctionOnScalarMeanDifferenceResult,
    GeneralizedFunctionOnScalarPredictionBandResult,
    GeneralizedFunctionOnScalarPredictionBootstrapResult,
    GeneralizedFunctionOnScalarPredictionResult,
    GeneralizedFunctionOnScalarResult,
)


def _inverse_link(
    family: str,
    linear_predictor: np.ndarray,
) -> np.ndarray:
    eta = np.asarray(linear_predictor, dtype=float)
    if family == "binomial":
        return expit(eta)
    if family == "poisson":
        with np.errstate(over="raise", invalid="raise"):
            try:
                return np.exp(eta)
            except FloatingPointError as exc:
                raise RuntimeError(
                    "Poisson marginal mean prediction overflowed on the "
                    "declared profile(s)"
                ) from exc
    raise ValueError(f"Unsupported generalized FoSR family {family!r}")


def _inverse_link_derivative(
    family: str,
    mean: np.ndarray,
) -> np.ndarray:
    mu = np.asarray(mean, dtype=float)
    if family == "binomial":
        return mu * (1.0 - mu)
    if family == "poisson":
        return mu
    raise ValueError(f"Unsupported generalized FoSR family {family!r}")


def _validate_profiles(
    result: GeneralizedFunctionOnScalarResult,
    profiles: pd.DataFrame,
    *,
    profile_id_column: str,
) -> tuple[pd.DataFrame, tuple[str, ...], np.ndarray]:
    if not isinstance(result, GeneralizedFunctionOnScalarResult):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarResult"
        )
    if not isinstance(profiles, pd.DataFrame):
        raise TypeError("profiles must be a pandas DataFrame")
    if profiles.empty:
        raise ValueError("profiles must contain at least one row")
    if not isinstance(profile_id_column, str) or not profile_id_column:
        raise TypeError("profile_id_column must be a non-empty string")
    if profile_id_column in result.predictor_names:
        raise ValueError(
            "profile_id_column must not reuse a declared predictor name"
        )

    expected = {profile_id_column, *result.predictor_names}
    observed = set(profiles.columns)
    if observed != expected:
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        raise ValueError(
            "profiles must contain exactly the profile id plus declared "
            f"predictors; missing={missing}, unexpected={unexpected}"
        )
    if profiles[profile_id_column].isna().any():
        raise ValueError("profile identifiers must not be missing")

    profile_ids = tuple(profiles[profile_id_column].astype(str))
    if any(not value for value in profile_ids):
        raise ValueError("profile identifiers must be non-empty")
    if len(set(profile_ids)) != len(profile_ids):
        raise ValueError("profile identifiers must be unique")

    aligned = profiles.copy()
    predictor_values = np.empty(
        (len(aligned), len(result.predictor_names)),
        dtype=float,
    )
    for index, name in enumerate(result.predictor_names):
        try:
            values = pd.to_numeric(
                aligned[name],
                errors="raise",
            ).to_numpy(dtype=float)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"profile predictor {name!r} must be numeric"
            ) from exc
        if not np.all(np.isfinite(values)):
            raise ValueError(
                f"profile predictor {name!r} contains non-finite values"
            )
        predictor_values[:, index] = values
        aligned[name] = values

    return aligned, profile_ids, predictor_values


def generalized_function_on_scalar_predict(
    result: GeneralizedFunctionOnScalarResult,
    profiles: pd.DataFrame,
    *,
    profile_id_column: str = "profile_id",
) -> GeneralizedFunctionOnScalarPredictionResult:
    """Predict fixed marginal response profiles under a generalized FoSR fit.

    Profiles are fixed analyst-declared targets.  Their predictor values are
    never estimated, averaged, resampled, centered, scaled, or encoded by this
    function.  Targets outside the observed scalar predictor ranges are retained
    and explicitly flagged as extrapolations.
    """

    _, profile_ids, predictor_values = _validate_profiles(
        result,
        profiles,
        profile_id_column=profile_id_column,
    )
    scalar_design = np.column_stack(
        [
            np.ones(len(profile_ids), dtype=float),
            predictor_values,
        ]
    )
    expanded_design = _fixed_effect_design(
        scalar_design,
        result.basis,
    )
    parameter_vector = np.asarray(
        result.basis_coefficients,
        dtype=float,
    ).reshape(-1)
    linear = (
        expanded_design @ parameter_vector
    ).reshape(len(profile_ids), result.time.size)

    covariance = np.asarray(
        result.parameter_covariance,
        dtype=float,
    )
    linear_variance = np.einsum(
        "ij,jk,ik->i",
        expanded_design,
        covariance,
        expanded_design,
        optimize=True,
    ).reshape(len(profile_ids), result.time.size)
    linear_se = np.sqrt(np.maximum(linear_variance, 0.0))

    mean = _inverse_link(result.family, linear)
    derivative = _inverse_link_derivative(result.family, mean)
    mean_se = derivative * linear_se

    observed_predictors = np.asarray(
        result.scalar_design_matrix[:, 1:],
        dtype=float,
    )
    minima = np.min(observed_predictors, axis=0)
    maxima = np.max(observed_predictors, axis=0)
    scale = np.maximum(
        1.0,
        np.maximum(np.abs(minima), np.abs(maxima)),
    )
    tolerance = 1e-12 * scale
    extrapolation = np.any(
        (predictor_values < minima[None, :] - tolerance[None, :])
        | (predictor_values > maxima[None, :] + tolerance[None, :]),
        axis=1,
    )

    return GeneralizedFunctionOnScalarPredictionResult(
        reference=result,
        profile_ids=profile_ids,
        profile_design_matrix=scalar_design,
        predictor_values=predictor_values,
        linear_predictor_functions=linear,
        linear_predictor_standard_errors=linear_se,
        mean_functions=mean,
        mean_standard_errors=mean_se,
        extrapolation_flags=extrapolation,
        predictor_minima=minima,
        predictor_maxima=maxima,
        provenance={
            **dict(result.provenance),
            "generalized_function_on_scalar_prediction": {
                "method": "fixed_profile_marginal_prediction",
                "profile_id_column": profile_id_column,
                "profile_ids": list(profile_ids),
                "n_profiles": len(profile_ids),
                "predictors": list(result.predictor_names),
                "profile_values_fixed": True,
                "profile_values_resampled": False,
                "categorical_encoding": False,
                "predictor_centering": False,
                "predictor_scaling": False,
                "marginal_population_averaged_interpretation": True,
                "linear_predictor_scale": result.link,
                "mean_scale": (
                    "probability"
                    if result.family == "binomial"
                    else "expected_count"
                ),
                "pointwise_linear_predictor_standard_error": (
                    "delta_from_gee_robust_parameter_covariance"
                ),
                "pointwise_mean_standard_error": (
                    "inverse_link_delta_method"
                ),
                "predictor_minima": minima.tolist(),
                "predictor_maxima": maxima.tolist(),
                "extrapolation_flags": extrapolation.tolist(),
                "extrapolated_profiles_retained": True,
                "automatic_profile_selection": False,
                "simultaneous_inference": False,
            },
        },
    )


def bootstrap_generalized_function_on_scalar_predictions(
    bootstrap: GeneralizedFunctionOnScalarBootstrapResult,
    profiles: pd.DataFrame,
    *,
    profile_id_column: str = "profile_id",
) -> GeneralizedFunctionOnScalarPredictionBootstrapResult:
    """Project participant-bootstrap coefficient functions to fixed profiles."""

    if not isinstance(
        bootstrap,
        GeneralizedFunctionOnScalarBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a GeneralizedFunctionOnScalarBootstrapResult"
        )
    prediction = generalized_function_on_scalar_predict(
        bootstrap.reference,
        profiles,
        profile_id_column=profile_id_column,
    )
    design = np.asarray(
        prediction.profile_design_matrix,
        dtype=float,
    )
    coefficient_draws = np.asarray(
        bootstrap.bootstrap_coefficient_functions,
        dtype=float,
    )
    linear_draws = np.einsum(
        "pc,bct->bpt",
        design,
        coefficient_draws,
        optimize=True,
    )
    mean_draws = _inverse_link(
        bootstrap.reference.family,
        linear_draws,
    )
    if not np.all(np.isfinite(linear_draws)):
        raise RuntimeError(
            "bootstrap fixed-profile linear predictors contain non-finite values"
        )
    if not np.all(np.isfinite(mean_draws)):
        raise RuntimeError(
            "bootstrap fixed-profile marginal means contain non-finite values"
        )

    return GeneralizedFunctionOnScalarPredictionBootstrapResult(
        prediction=prediction,
        coefficient_bootstrap=bootstrap,
        bootstrap_linear_predictor_functions=linear_draws,
        bootstrap_mean_functions=mean_draws,
        provenance={
            **dict(bootstrap.provenance),
            "generalized_function_on_scalar_prediction_bootstrap": {
                "method": (
                    "fixed_profile_projection_of_whole_participant_"
                    "coefficient_bootstrap"
                ),
                "n_bootstrap": bootstrap.n_bootstrap,
                "profile_ids": list(prediction.profile_ids),
                "profile_values_fixed_across_bootstrap": True,
                "profile_values_resampled": False,
                "same_participant_draws_as_coefficient_bootstrap": True,
                "response_transformation": (
                    "inverse_logit"
                    if bootstrap.reference.family == "binomial"
                    else "exponential"
                ),
                "automatic_profile_selection": False,
            },
        },
    )


def generalized_function_on_scalar_prediction_bands(
    bootstrap: GeneralizedFunctionOnScalarPredictionBootstrapResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "profile",
) -> GeneralizedFunctionOnScalarPredictionBandResult:
    """Calibrate simultaneous fixed-profile marginal mean bands.

    Calibration is performed on the linear-predictor scale.  Because the logit
    and log inverse links are strictly monotone, transforming both endpoints
    produces simultaneous marginal probability/mean bands with the same
    bootstrap event on the observed grid.
    """

    if not isinstance(
        bootstrap,
        GeneralizedFunctionOnScalarPredictionBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a "
            "GeneralizedFunctionOnScalarPredictionBootstrapResult"
        )
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"profile", "family"}:
        raise ValueError(
            "simultaneous_scope must be 'profile' or 'family'"
        )

    prediction = bootstrap.prediction
    se = np.asarray(
        prediction.linear_predictor_standard_errors,
        dtype=float,
    )
    if np.any(~np.isfinite(se)) or np.any(se <= np.finfo(float).eps):
        raise ValueError(
            "prediction simultaneous bands require strictly positive finite "
            "linear-predictor standard errors at every profile/time point"
        )

    deviations = (
        bootstrap.bootstrap_linear_predictor_functions
        - prediction.linear_predictor_functions[None, :, :]
    )
    standardized = np.abs(deviations / se[None, :, :])

    if simultaneous_scope == "profile":
        max_statistics = np.max(standardized, axis=2)
        critical_values = np.quantile(
            max_statistics,
            confidence_level,
            axis=0,
            method="higher",
        )
    else:
        family_max = np.max(standardized, axis=(1, 2))
        critical = float(
            np.quantile(
                family_max,
                confidence_level,
                method="higher",
            )
        )
        max_statistics = family_max[:, None]
        critical_values = np.full(
            prediction.n_profiles,
            critical,
            dtype=float,
        )

    linear_lower = (
        prediction.linear_predictor_functions
        - critical_values[:, None] * se
    )
    linear_upper = (
        prediction.linear_predictor_functions
        + critical_values[:, None] * se
    )
    mean_lower = _inverse_link(
        prediction.reference.family,
        linear_lower,
    )
    mean_upper = _inverse_link(
        prediction.reference.family,
        linear_upper,
    )

    return GeneralizedFunctionOnScalarPredictionBandResult(
        prediction=prediction,
        linear_lower=linear_lower,
        linear_upper=linear_upper,
        mean_lower=mean_lower,
        mean_upper=mean_upper,
        critical_values=critical_values,
        max_statistics=max_statistics,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
        bootstrap=bootstrap,
        provenance={
            **dict(bootstrap.provenance),
            "generalized_function_on_scalar_prediction_band": {
                "confidence_level": confidence_level,
                "simultaneous_scope": simultaneous_scope,
                "calibration_scale": "linear_predictor",
                "calibration": (
                    "whole_participant_bootstrap_max_standardized_deviation"
                ),
                "linear_predictor_standard_error": (
                    "gee_robust_delta_method"
                ),
                "mean_band_transformation": (
                    "strictly_monotone_inverse_link_endpoints"
                ),
                "observed_grid_only": True,
                "between_grid_coverage_claim": False,
                "profiles_fixed": True,
                "extrapolated_profiles_retained": True,
                "automatic_profile_selection": False,
            },
        },
    )


def generalized_function_on_scalar_mean_difference_band(
    bootstrap: GeneralizedFunctionOnScalarPredictionBootstrapResult,
    *,
    profile_a: str,
    profile_b: str,
    confidence_level: float = 0.95,
) -> GeneralizedFunctionOnScalarMeanDifferenceResult:
    """Construct one predeclared simultaneous marginal mean-difference band.

    The contrast is mean(profile_a) - mean(profile_b) on the response scale.
    For Bernoulli outcomes this is a marginal probability/risk difference; for
    Poisson outcomes it is an expected-count difference under the no-offset
    0.51/0.52 contract.
    """

    if not isinstance(
        bootstrap,
        GeneralizedFunctionOnScalarPredictionBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a "
            "GeneralizedFunctionOnScalarPredictionBootstrapResult"
        )
    if not isinstance(profile_a, str) or not profile_a:
        raise TypeError("profile_a must be a non-empty string")
    if not isinstance(profile_b, str) or not profile_b:
        raise TypeError("profile_b must be a non-empty string")
    if profile_a == profile_b:
        raise ValueError("profile_a and profile_b must be different")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")

    prediction = bootstrap.prediction
    lookup = {
        profile_id: index
        for index, profile_id in enumerate(prediction.profile_ids)
    }
    missing = [
        value
        for value in (profile_a, profile_b)
        if value not in lookup
    ]
    if missing:
        raise KeyError(f"Unknown profile identifier(s): {missing}")

    a = lookup[profile_a]
    b = lookup[profile_b]
    estimate = (
        prediction.mean_functions[a]
        - prediction.mean_functions[b]
    )
    bootstrap_estimates = (
        bootstrap.bootstrap_mean_functions[:, a, :]
        - bootstrap.bootstrap_mean_functions[:, b, :]
    )
    standard_error = np.std(
        bootstrap_estimates,
        axis=0,
        ddof=1,
    )
    if (
        np.any(~np.isfinite(standard_error))
        or np.any(standard_error <= np.finfo(float).eps)
    ):
        raise ValueError(
            "mean-difference simultaneous band requires strictly positive "
            "finite bootstrap standard errors at every observed time point"
        )

    standardized = np.abs(
        (bootstrap_estimates - estimate[None, :])
        / standard_error[None, :]
    )
    max_statistics = np.max(standardized, axis=1)
    critical_value = float(
        np.quantile(
            max_statistics,
            confidence_level,
            method="higher",
        )
    )
    lower = estimate - critical_value * standard_error
    upper = estimate + critical_value * standard_error

    if prediction.reference.family == "binomial":
        physical_lower: float | None = -1.0
        physical_upper: float | None = 1.0
        exceeds = bool(
            np.any(lower < physical_lower)
            or np.any(upper > physical_upper)
        )
    else:
        physical_lower = None
        physical_upper = None
        exceeds = False

    extrapolated = bool(
        prediction.extrapolation_flags[a]
        or prediction.extrapolation_flags[b]
    )
    return GeneralizedFunctionOnScalarMeanDifferenceResult(
        prediction_bootstrap=bootstrap,
        profile_a=profile_a,
        profile_b=profile_b,
        estimate=estimate,
        standard_error=standard_error,
        lower=lower,
        upper=upper,
        bootstrap_estimates=bootstrap_estimates,
        max_statistics=max_statistics,
        critical_value=critical_value,
        confidence_level=confidence_level,
        physical_lower_bound=physical_lower,
        physical_upper_bound=physical_upper,
        interval_exceeds_physical_bounds=exceeds,
        provenance={
            **dict(bootstrap.provenance),
            "generalized_function_on_scalar_mean_difference_band": {
                "contrast": f"{profile_a} - {profile_b}",
                "response_scale": (
                    "probability_difference"
                    if prediction.reference.family == "binomial"
                    else "expected_count_difference"
                ),
                "profiles_fixed": True,
                "profile_pair_predeclared": True,
                "profile_pair_extrapolated": extrapolated,
                "standard_error": "participant_bootstrap_standard_deviation",
                "calibration": (
                    "observed_grid_max_standardized_bootstrap_deviation"
                ),
                "confidence_level": confidence_level,
                "physical_bounds_clipped": False,
                "interval_exceeds_physical_bounds": exceeds,
                "multiple_contrast_family_adjustment": False,
                "automatic_contrast_selection": False,
            },
        },
    )


def generalized_function_on_scalar_prediction_frame(
    result: (
        GeneralizedFunctionOnScalarPredictionResult
        | GeneralizedFunctionOnScalarPredictionBandResult
    ),
) -> pd.DataFrame:
    """Return one row per fixed profile and observed time point."""

    if isinstance(result, GeneralizedFunctionOnScalarPredictionBandResult):
        prediction = result.prediction
        band = result
    elif isinstance(result, GeneralizedFunctionOnScalarPredictionResult):
        prediction = result
        band = None
    else:
        raise TypeError(
            "result must be a generalized FoSR prediction or prediction band"
        )

    rows: list[dict[str, object]] = []
    for profile_index, profile_id in enumerate(prediction.profile_ids):
        for time_index, time_value in enumerate(
            prediction.reference.time
        ):
            row: dict[str, object] = {
                "profile_id": profile_id,
                "time": float(time_value),
                "linear_predictor": float(
                    prediction.linear_predictor_functions[
                        profile_index,
                        time_index,
                    ]
                ),
                "linear_predictor_standard_error": float(
                    prediction.linear_predictor_standard_errors[
                        profile_index,
                        time_index,
                    ]
                ),
                "mean": float(
                    prediction.mean_functions[
                        profile_index,
                        time_index,
                    ]
                ),
                "mean_standard_error": float(
                    prediction.mean_standard_errors[
                        profile_index,
                        time_index,
                    ]
                ),
                "family": prediction.reference.family,
                "link": prediction.reference.link,
                "extrapolation": bool(
                    prediction.extrapolation_flags[profile_index]
                ),
            }
            if band is not None:
                row.update(
                    {
                        "linear_lower": float(
                            band.linear_lower[
                                profile_index,
                                time_index,
                            ]
                        ),
                        "linear_upper": float(
                            band.linear_upper[
                                profile_index,
                                time_index,
                            ]
                        ),
                        "mean_lower": float(
                            band.mean_lower[
                                profile_index,
                                time_index,
                            ]
                        ),
                        "mean_upper": float(
                            band.mean_upper[
                                profile_index,
                                time_index,
                            ]
                        ),
                        "critical_value": float(
                            band.critical_values[profile_index]
                        ),
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def generalized_function_on_scalar_mean_difference_frame(
    result: GeneralizedFunctionOnScalarMeanDifferenceResult,
) -> pd.DataFrame:
    """Return the observed-grid response-scale mean-difference band."""

    if not isinstance(
        result,
        GeneralizedFunctionOnScalarMeanDifferenceResult,
    ):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarMeanDifferenceResult"
        )
    time = result.prediction_bootstrap.prediction.reference.time
    return pd.DataFrame(
        {
            "time": np.asarray(time, dtype=float),
            "estimate": result.estimate,
            "standard_error": result.standard_error,
            "lower": result.lower,
            "upper": result.upper,
            "profile_a": result.profile_a,
            "profile_b": result.profile_b,
            "critical_value": result.critical_value,
            "interval_exceeds_physical_bounds": (
                result.interval_exceeds_physical_bounds
            ),
        }
    )


def plot_generalized_function_on_scalar_predictions(
    result: (
        GeneralizedFunctionOnScalarPredictionResult
        | GeneralizedFunctionOnScalarPredictionBandResult
    ),
    *,
    ax=None,
):
    """Plot fixed-profile marginal mean functions and optional bands."""

    import matplotlib.pyplot as plt

    if isinstance(result, GeneralizedFunctionOnScalarPredictionBandResult):
        prediction = result.prediction
        band = result
    elif isinstance(result, GeneralizedFunctionOnScalarPredictionResult):
        prediction = result
        band = None
    else:
        raise TypeError(
            "result must be a generalized FoSR prediction or prediction band"
        )

    if ax is None:
        _, ax = plt.subplots()
    for index, profile_id in enumerate(prediction.profile_ids):
        label = (
            f"{profile_id} (extrapolation)"
            if prediction.extrapolation_flags[index]
            else profile_id
        )
        ax.plot(
            prediction.reference.time,
            prediction.mean_functions[index],
            label=label,
        )
        if band is not None:
            ax.fill_between(
                prediction.reference.time,
                band.mean_lower[index],
                band.mean_upper[index],
                alpha=0.2,
            )
    ax.set_xlabel(
        f"Time ({prediction.reference.time_unit})"
    )
    ax.set_ylabel(
        "Marginal probability"
        if prediction.reference.family == "binomial"
        else "Marginal expected count"
    )
    ax.set_title("Generalized FoSR fixed-profile marginal predictions")
    ax.legend()
    return ax


def plot_generalized_function_on_scalar_mean_difference(
    result: GeneralizedFunctionOnScalarMeanDifferenceResult,
    *,
    ax=None,
):
    """Plot one predeclared response-scale mean-difference band."""

    import matplotlib.pyplot as plt

    if not isinstance(
        result,
        GeneralizedFunctionOnScalarMeanDifferenceResult,
    ):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarMeanDifferenceResult"
        )
    if ax is None:
        _, ax = plt.subplots()
    time = result.prediction_bootstrap.prediction.reference.time
    ax.plot(time, result.estimate, label="estimate")
    ax.fill_between(
        time,
        result.lower,
        result.upper,
        alpha=0.2,
        label=(
            f"{100 * result.confidence_level:.0f}% simultaneous band"
        ),
    )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel(
        "Time "
        f"({result.prediction_bootstrap.prediction.reference.time_unit})"
    )
    ylabel = (
        "Marginal probability difference"
        if result.prediction_bootstrap.prediction.reference.family
        == "binomial"
        else "Marginal expected-count difference"
    )
    ax.set_ylabel(ylabel)
    ax.set_title(
        f"Generalized FoSR mean difference: "
        f"{result.profile_a} - {result.profile_b}"
    )
    ax.legend()
    return ax


def generalized_function_on_scalar_prediction_reporting_text(
    result: GeneralizedFunctionOnScalarPredictionBandResult,
) -> str:
    """Return manuscript-oriented wording for fixed-profile prediction."""

    if not isinstance(
        result,
        GeneralizedFunctionOnScalarPredictionBandResult,
    ):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarPredictionBandResult"
        )
    prediction = result.prediction
    extrapolated = [
        profile_id
        for profile_id, flag in zip(
            prediction.profile_ids,
            prediction.extrapolation_flags,
            strict=True,
        )
        if flag
    ]
    extrapolation_text = (
        " No declared profile lay outside the observed scalar predictor "
        "ranges."
        if not extrapolated
        else (
            " The following fixed profiles were retained but flagged as "
            "scalar-predictor extrapolations: "
            + ", ".join(extrapolated)
            + "."
        )
    )
    scale = (
        "marginal probability"
        if prediction.reference.family == "binomial"
        else "marginal expected count"
    )
    return (
        f"Fixed-profile {scale} functions were derived from the fitted "
        f"{prediction.reference.family}/{prediction.reference.link} marginal "
        "generalized function-on-scalar model. Profile values were treated as "
        "fixed scientific targets and were not resampled. Simultaneous bands "
        "were calibrated on the linear-predictor scale using the retained "
        "whole-participant coefficient bootstrap and then transformed through "
        "the strictly monotone inverse link. The simultaneous scope was "
        f"{result.simultaneous_scope!r} over the observed grid; no "
        "between-grid coverage is claimed and no profile was selected "
        "automatically."
        + extrapolation_text
    )


def generalized_function_on_scalar_mean_difference_reporting_text(
    result: GeneralizedFunctionOnScalarMeanDifferenceResult,
) -> str:
    """Return manuscript wording for one predeclared mean-difference band."""

    if not isinstance(
        result,
        GeneralizedFunctionOnScalarMeanDifferenceResult,
    ):
        raise TypeError(
            "result must be a GeneralizedFunctionOnScalarMeanDifferenceResult"
        )
    family = (
        result.prediction_bootstrap.prediction.reference.family
    )
    measure = (
        "marginal probability difference"
        if family == "binomial"
        else "marginal expected-count difference"
    )
    bounds_text = ""
    if result.interval_exceeds_physical_bounds:
        bounds_text = (
            " The untrimmed simultaneous band extended beyond the logical "
            "[-1, 1] range of a probability difference; bounds were retained "
            "rather than silently clipped."
        )
    return (
        f"One predeclared {measure} function was evaluated as "
        f"{result.profile_a!r} minus {result.profile_b!r}. The paired "
        "whole-participant bootstrap coefficient draws were propagated through "
        "both fixed profiles, preserving their dependence, and an observed-grid "
        "maximum standardized-deviation band was calibrated at "
        f"{100 * result.confidence_level:.1f}%. The profile pair was not "
        "selected from the bootstrap results and no multiple-contrast family "
        "adjustment is claimed."
        + bounds_text
    )
