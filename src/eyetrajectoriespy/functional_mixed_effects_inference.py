"""Simultaneous inference for functional mixed-effects coefficient functions."""

from __future__ import annotations

import numpy as np

from .functional_mixed_effects import _fixed_effect_design
from .types import (
    FunctionalMixedEffectsBandResult,
    FunctionalMixedEffectsBootstrapResult,
    FunctionalMixedEffectsFullRefitBootstrapResult,
    FunctionalMixedEffectsResult,
)


def _validate_reference(
    result: FunctionalMixedEffectsResult,
) -> None:
    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if not result.converged:
        raise ValueError("reference mixed-effects fit must have converged")
    if not np.isfinite(result.residual_variance) or result.residual_variance <= 0:
        raise ValueError("reference residual_variance must be finite and positive")
    covariance = np.asarray(result.random_effect_covariance, dtype=float)
    if covariance.shape != (
        result.random_effect_dimension,
        result.random_effect_dimension,
    ):
        raise ValueError(
            "reference random_effect_covariance has an unexpected shape"
        )
    if not np.all(np.isfinite(covariance)):
        raise ValueError(
            "reference random_effect_covariance must contain finite values"
        )
    if not np.allclose(covariance, covariance.T, rtol=1e-10, atol=1e-12):
        raise ValueError(
            "reference random_effect_covariance must be symmetric"
        )


def _participant_gls_contributions(
    result: FunctionalMixedEffectsResult,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _validate_reference(result)

    participant_labels = np.asarray(
        result.curve_participant_ids,
        dtype=object,
    )
    covariance = np.asarray(result.random_effect_covariance, dtype=float)
    n_fixed_parameters = (
        result.n_coefficients * result.fixed_basis_size
    )
    information = np.empty(
        (
            result.n_participants,
            n_fixed_parameters,
            n_fixed_parameters,
        ),
        dtype=float,
    )
    scores = np.empty(
        (result.n_participants, n_fixed_parameters),
        dtype=float,
    )

    for participant_index, participant_id in enumerate(
        result.participant_ids
    ):
        curve_indices = np.flatnonzero(
            participant_labels == participant_id
        )
        if curve_indices.size == 0:
            raise RuntimeError(
                "reference participant has no associated source curves"
            )

        fixed_exog = _fixed_effect_design(
            result.scalar_design_matrix[curve_indices],
            result.fixed_basis,
        )
        response = result.observed_functions[curve_indices].reshape(-1)
        n_time = result.time.size
        row_indices = (
            curve_indices[:, None] * n_time
            + np.arange(n_time, dtype=int)[None, :]
        ).reshape(-1)
        random_exog = np.asarray(
            result.random_effect_design_matrix[row_indices],
            dtype=float,
        )
        marginal_covariance = (
            random_exog
            @ covariance
            @ random_exog.T
            + result.residual_variance
            * np.eye(random_exog.shape[0], dtype=float)
        )
        try:
            covariance_inverse_fixed = np.linalg.solve(
                marginal_covariance,
                fixed_exog,
            )
            covariance_inverse_response = np.linalg.solve(
                marginal_covariance,
                response,
            )
        except np.linalg.LinAlgError as exc:
            raise RuntimeError(
                "reference participant marginal covariance could not be solved"
            ) from exc

        information[participant_index] = (
            fixed_exog.T @ covariance_inverse_fixed
        )
        scores[participant_index] = (
            fixed_exog.T @ covariance_inverse_response
        )

    total_information = np.sum(information, axis=0)
    total_score = np.sum(scores, axis=0)
    try:
        reference_gls = np.linalg.solve(
            total_information,
            total_score,
        )
    except np.linalg.LinAlgError as exc:
        raise RuntimeError(
            "reference fixed-covariance GLS system is singular"
        ) from exc

    backend_fixed = np.asarray(
        result.fixed_basis_coefficients,
        dtype=float,
    ).reshape(-1)
    max_difference = float(
        np.max(np.abs(reference_gls - backend_fixed))
    )
    if not np.allclose(
        reference_gls,
        backend_fixed,
        rtol=2e-4,
        atol=2e-7,
    ):
        raise RuntimeError(
            "fixed-covariance GLS reconstruction does not reproduce the "
            "reference MixedLM fixed coefficients"
        )
    return information, scores, np.asarray([max_difference], dtype=float)


def bootstrap_functional_mixed_effects_coefficients(
    result: FunctionalMixedEffectsResult,
    *,
    n_bootstrap: int = 1000,
    random_state: int | None = 0,
) -> FunctionalMixedEffectsBootstrapResult:
    """Bootstrap mixed-effects coefficient functions by participant clusters.

    Whole participant trial bundles are sampled with replacement. For every
    resample, the fixed B-spline coefficients are re-estimated by GLS while the
    reference random-effect covariance and residual variance are held fixed.

    This targets participant-level sampling variability in the fixed coefficient
    functions conditional on the fitted covariance model and declared bases. It
    is not a full variance-component-refitting bootstrap.
    """

    _validate_reference(result)
    if isinstance(n_bootstrap, bool) or not isinstance(
        n_bootstrap, (int, np.integer)
    ):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100")
    if random_state is not None and (
        isinstance(random_state, bool)
        or not isinstance(random_state, (int, np.integer))
    ):
        raise TypeError("random_state must be an integer or None")

    information, scores, reconstruction_difference = (
        _participant_gls_contributions(result)
    )
    rng = np.random.default_rng(
        None if random_state is None else int(random_state)
    )
    sampled_participant_indices = rng.integers(
        0,
        result.n_participants,
        size=(n_bootstrap, result.n_participants),
    )
    bootstrap_fixed_basis_coefficients = np.empty(
        (
            n_bootstrap,
            result.n_coefficients,
            result.fixed_basis_size,
        ),
        dtype=float,
    )
    bootstrap_coefficient_functions = np.empty(
        (
            n_bootstrap,
            result.n_coefficients,
            result.time.size,
        ),
        dtype=float,
    )

    n_fixed_parameters = (
        result.n_coefficients * result.fixed_basis_size
    )
    for bootstrap_index, participant_sample in enumerate(
        sampled_participant_indices
    ):
        information_star = np.sum(
            information[participant_sample],
            axis=0,
        )
        score_star = np.sum(
            scores[participant_sample],
            axis=0,
        )
        if np.linalg.matrix_rank(information_star) < n_fixed_parameters:
            raise RuntimeError(
                "participant-cluster bootstrap replicate "
                f"{bootstrap_index + 1} produced a rank-deficient fixed-effect "
                "information matrix; no replicate was silently discarded"
            )
        try:
            fixed_star = np.linalg.solve(
                information_star,
                score_star,
            )
        except np.linalg.LinAlgError as exc:
            raise RuntimeError(
                "participant-cluster bootstrap replicate "
                f"{bootstrap_index + 1} could not solve the fixed-effect "
                "GLS system; no replicate was silently discarded"
            ) from exc

        basis_coefficients = fixed_star.reshape(
            result.n_coefficients,
            result.fixed_basis_size,
        )
        bootstrap_fixed_basis_coefficients[
            bootstrap_index
        ] = basis_coefficients
        bootstrap_coefficient_functions[
            bootstrap_index
        ] = basis_coefficients @ result.fixed_basis.T

    bootstrap_mean = np.mean(
        bootstrap_coefficient_functions,
        axis=0,
    )
    bootstrap_standard_errors = np.std(
        bootstrap_coefficient_functions,
        axis=0,
        ddof=1,
    )

    return FunctionalMixedEffectsBootstrapResult(
        reference=result,
        bootstrap_fixed_basis_coefficients=(
            bootstrap_fixed_basis_coefficients
        ),
        bootstrap_coefficient_functions=(
            bootstrap_coefficient_functions
        ),
        sampled_participant_indices=sampled_participant_indices,
        bootstrap_mean=bootstrap_mean,
        bootstrap_standard_errors=bootstrap_standard_errors,
        random_state=(
            None if random_state is None else int(random_state)
        ),
        covariance_conditioning=(
            "reference_random_effect_covariance_and_residual_variance_fixed"
        ),
        provenance={
            **dict(result.provenance),
            "functional_mixed_effects_bootstrap": {
                "method": (
                    "participant_cluster_case_bootstrap_fixed_covariance_gls"
                ),
                "n_bootstrap": n_bootstrap,
                "random_state": (
                    None
                    if random_state is None
                    else int(random_state)
                ),
                "resampling_unit": "participant",
                "whole_trial_bundles_resampled": True,
                "curves_resampled_independently": False,
                "participant_draws_with_replacement": True,
                "fixed_effects_reestimated_each_replicate": True,
                "variance_components_refit": False,
                "random_effect_covariance_conditioned_on_reference": True,
                "residual_variance_conditioned_on_reference": True,
                "fixed_basis_refit": False,
                "random_basis_refit": False,
                "basis_selection_repeated": False,
                "reference_boundary_fit": bool(result.boundary_fit),
                "reference_random_slope_predictor": (
                    result.random_slope_predictor
                ),
                "reference_random_effect_dimension": (
                    result.random_effect_dimension
                ),
                "random_intercept_slope_covariance_conditioned_on_reference": (
                    result.random_slope_predictor is not None
                ),
                "reference_gls_max_abs_difference": float(
                    reconstruction_difference[0]
                ),
                "failed_replicate_policy": "raise",
                "simultaneous_band_calibration": False,
            },
        },
    )


def functional_mixed_effects_simultaneous_bands(
    bootstrap: (
        FunctionalMixedEffectsBootstrapResult
        | FunctionalMixedEffectsFullRefitBootstrapResult
    ),
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "coefficient",
) -> FunctionalMixedEffectsBandResult:
    """Calibrate observed-grid simultaneous mixed-effects coefficient bands."""

    if not isinstance(
        bootstrap,
        (
            FunctionalMixedEffectsBootstrapResult,
            FunctionalMixedEffectsFullRefitBootstrapResult,
        ),
    ):
        raise TypeError(
            "bootstrap must be a FunctionalMixedEffectsBootstrapResult "
            "or FunctionalMixedEffectsFullRefitBootstrapResult"
        )
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"coefficient", "family"}:
        raise ValueError(
            "simultaneous_scope must be 'coefficient' or 'family'"
        )

    reference = bootstrap.reference
    standard_errors = np.asarray(
        bootstrap.bootstrap_standard_errors,
        dtype=float,
    )
    if not np.all(np.isfinite(standard_errors)):
        raise RuntimeError(
            "bootstrap pointwise standard errors contain non-finite values"
        )
    positive = standard_errors > np.finfo(float).eps
    if not np.all(positive):
        raise RuntimeError(
            "bootstrap pointwise standard errors contain zero-width cells; "
            "simultaneous studentization is undefined"
        )

    deviations = (
        bootstrap.bootstrap_coefficient_functions
        - bootstrap.bootstrap_mean[None, :, :]
    )
    standardized = deviations / standard_errors[None, :, :]
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

    return FunctionalMixedEffectsBandResult(
        reference=reference,
        lower=lower,
        upper=upper,
        pointwise_standard_errors=standard_errors.copy(),
        critical_values=np.asarray(
            critical_values,
            dtype=float,
        ),
        max_statistics=np.asarray(
            max_statistics,
            dtype=float,
        ),
        confidence_level=float(confidence_level),
        simultaneous_scope=simultaneous_scope,
        bootstrap=bootstrap,
        provenance={
            **dict(bootstrap.provenance),
            "functional_mixed_effects_simultaneous_bands": {
                "method": (
                    "participant_cluster_bootstrap_studentized_supremum"
                ),
                "confidence_level": float(confidence_level),
                "simultaneous_scope": simultaneous_scope,
                "simultaneous_domain": (
                    "observed_time_grid_per_coefficient"
                    if simultaneous_scope == "coefficient"
                    else "coefficient_by_observed_time_grid"
                ),
                "bootstrap_centering_for_calibration": (
                    "bootstrap_mean"
                ),
                "band_center": "reference_estimate",
                "bias_correction": False,
                "pointwise_scale": "participant_cluster_bootstrap_sd",
                "continuous_between_grid_points": False,
                "variance_components_refit": isinstance(
                    bootstrap,
                    FunctionalMixedEffectsFullRefitBootstrapResult,
                ),
                "bootstrap_type": (
                    "full_refit"
                    if isinstance(
                        bootstrap,
                        FunctionalMixedEffectsFullRefitBootstrapResult,
                    )
                    else "fixed_covariance"
                ),
                "failed_replicate_policy": "raise",
            },
        },
    )
