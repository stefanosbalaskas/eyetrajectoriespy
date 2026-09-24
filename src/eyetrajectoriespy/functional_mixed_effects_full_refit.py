"""Full-refit participant bootstrap for functional mixed-effects models."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .functional_mixed_effects import fit_functional_mixed_effects_regression
from .functional_mixed_effects_inference import (
    functional_mixed_effects_simultaneous_bands,
)
from .types import (
    FunctionalMixedEffectsBootstrapResult,
    FunctionalMixedEffectsFullRefitBootstrapResult,
    FunctionalMixedEffectsResult,
    TrajectorySet,
)


def _validate_full_refit_reference(
    result: FunctionalMixedEffectsResult,
) -> None:
    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("result must be a FunctionalMixedEffectsResult")
    if not result.converged:
        raise ValueError("reference mixed-effects fit must have converged")
    if not np.all(np.isfinite(result.observed_functions)):
        raise ValueError("reference observed functions must be finite")
    if len(result.curve_participant_ids) != result.n_curves:
        raise ValueError(
            "reference curve_participant_ids must align with source curves"
        )
    if result.scalar_design_matrix.shape != (
        result.n_curves,
        result.n_coefficients,
    ):
        raise ValueError(
            "reference scalar_design_matrix has an unexpected shape"
        )


def _validate_bootstrap_controls(
    *,
    n_bootstrap: int,
    random_state: int | None,
) -> tuple[int, int | None]:
    if isinstance(n_bootstrap, bool) or not isinstance(
        n_bootstrap,
        (int, np.integer),
    ):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 20:
        raise ValueError(
            "n_bootstrap must be at least 20 for full-refit diagnostics"
        )
    if random_state is not None and (
        isinstance(random_state, bool)
        or not isinstance(random_state, (int, np.integer))
    ):
        raise TypeError("random_state must be an integer or None")
    return (
        n_bootstrap,
        None if random_state is None else int(random_state),
    )


def _reference_design_frame(
    result: FunctionalMixedEffectsResult,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            predictor: result.scalar_design_matrix[
                :,
                predictor_index + 1,
            ]
            for predictor_index, predictor in enumerate(
                result.predictor_names
            )
        }
    )
    frame.insert(0, "curve_id", list(result.source_curve_ids))
    return frame


def _bootstrap_dataset(
    result: FunctionalMixedEffectsResult,
    *,
    participant_sample: np.ndarray,
    bootstrap_index: int,
) -> tuple[
    TrajectorySet,
    pd.DataFrame,
    tuple[str, ...],
    tuple[str, ...],
]:
    participant_labels = np.asarray(
        result.curve_participant_ids,
        dtype=object,
    )
    reference_design = _reference_design_frame(result)

    values: list[np.ndarray] = []
    curve_ids: list[str] = []
    bootstrap_groups: list[str] = []
    source_groups: list[str] = []
    design_rows: list[pd.Series] = []

    sampled_source_ids: list[str] = []
    sampled_bootstrap_ids: list[str] = []

    for draw_index, participant_index in enumerate(
        np.asarray(participant_sample, dtype=int)
    ):
        source_participant_id = str(
            result.participant_ids[int(participant_index)]
        )
        bootstrap_participant_id = (
            f"bootstrap_{bootstrap_index:04d}_draw_{draw_index:04d}"
        )
        sampled_source_ids.append(source_participant_id)
        sampled_bootstrap_ids.append(bootstrap_participant_id)

        original_curve_indices = np.flatnonzero(
            participant_labels == source_participant_id
        )
        if original_curve_indices.size == 0:
            raise RuntimeError(
                "sampled source participant has no reference curves"
            )

        for within_draw_index, curve_index in enumerate(
            original_curve_indices
        ):
            curve_id = (
                f"b{bootstrap_index:04d}_d{draw_index:04d}_"
                f"c{within_draw_index:04d}"
            )
            values.append(
                result.observed_functions[curve_index, :, None].copy()
            )
            curve_ids.append(curve_id)
            bootstrap_groups.append(bootstrap_participant_id)
            source_groups.append(source_participant_id)

            row = reference_design.iloc[int(curve_index)].copy()
            row["curve_id"] = curve_id
            design_rows.append(row)

    metadata = pd.DataFrame(
        {
            result.participant_column: bootstrap_groups,
            "source_participant_id": source_groups,
        }
    )
    trajectories = TrajectorySet(
        time=result.time.copy(),
        values=np.asarray(values, dtype=float),
        curve_ids=tuple(curve_ids),
        dimension_names=(result.dimension_name,),
        metadata=metadata,
        coordinate_system=result.coordinate_system,
        time_unit=result.time_unit,
        provenance={
            **dict(result.provenance),
            "functional_mixed_effects_full_refit_bootstrap_dataset": {
                "bootstrap_index": int(bootstrap_index),
                "source_participant_ids": sampled_source_ids,
                "bootstrap_participant_ids": sampled_bootstrap_ids,
                "duplicate_source_draws_receive_distinct_group_ids": True,
            },
        },
    )
    design = pd.DataFrame(design_rows).reset_index(drop=True)
    return (
        trajectories,
        design,
        tuple(sampled_source_ids),
        tuple(sampled_bootstrap_ids),
    )


def bootstrap_functional_mixed_effects_full_refit(
    result: FunctionalMixedEffectsResult,
    *,
    n_bootstrap: int = 1000,
    random_state: int | None = 0,
) -> FunctionalMixedEffectsFullRefitBootstrapResult:
    """Bootstrap whole participants and refit all mixed-model parameters.

    Each sampled participant occurrence receives a distinct bootstrap group
    identity, even when the same source participant is drawn multiple times.
    Every bootstrap replicate refits fixed coefficients, the random-effect
    covariance, and residual variance under the original declared model
    specification.

    Basis sizes, knots implied by the unchanged common grid, preprocessing,
    response dimension, predictors, random-slope structure, optimizer, REML/ML
    choice, and convergence policy are held fixed.
    """

    _validate_full_refit_reference(result)
    n_bootstrap, random_state = _validate_bootstrap_controls(
        n_bootstrap=n_bootstrap,
        random_state=random_state,
    )
    rng = np.random.default_rng(random_state)
    sampled_participant_indices = rng.integers(
        0,
        result.n_participants,
        size=(n_bootstrap, result.n_participants),
    )

    coefficient_functions = np.empty(
        (
            n_bootstrap,
            result.n_coefficients,
            result.time.size,
        ),
        dtype=float,
    )
    fixed_basis_coefficients = np.empty(
        (
            n_bootstrap,
            result.n_coefficients,
            result.fixed_basis_size,
        ),
        dtype=float,
    )
    random_covariances = np.empty(
        (
            n_bootstrap,
            result.random_effect_dimension,
            result.random_effect_dimension,
        ),
        dtype=float,
    )
    intercept_covariances = np.empty(
        (
            n_bootstrap,
            result.random_basis_size,
            result.random_basis_size,
        ),
        dtype=float,
    )
    if result.random_slope_predictor is None:
        slope_covariances = None
        cross_covariances = None
    else:
        slope_covariances = np.empty_like(intercept_covariances)
        cross_covariances = np.empty_like(intercept_covariances)

    covariance_eigenvalues = np.empty(
        (n_bootstrap, result.random_effect_dimension),
        dtype=float,
    )
    covariance_condition_numbers = np.empty(n_bootstrap, dtype=float)
    boundary_flags = np.empty(n_bootstrap, dtype=bool)
    singular_flags = np.empty(n_bootstrap, dtype=bool)
    slope_boundary_flags = np.empty(n_bootstrap, dtype=bool)
    residual_variances = np.empty(n_bootstrap, dtype=float)
    log_likelihoods = np.empty(n_bootstrap, dtype=float)
    convergence_flags = np.empty(n_bootstrap, dtype=bool)
    warning_records: list[tuple[str, ...]] = []
    sampled_source_ids: list[tuple[str, ...]] = []
    sampled_bootstrap_ids: list[tuple[str, ...]] = []

    for bootstrap_index, participant_sample in enumerate(
        sampled_participant_indices
    ):
        (
            trajectories_star,
            design_star,
            source_ids,
            bootstrap_ids,
        ) = _bootstrap_dataset(
            result,
            participant_sample=participant_sample,
            bootstrap_index=bootstrap_index,
        )
        sampled_source_ids.append(source_ids)
        sampled_bootstrap_ids.append(bootstrap_ids)

        try:
            fit_star = fit_functional_mixed_effects_regression(
                trajectories_star,
                design_star,
                predictors=result.predictor_names,
                participant_column=result.participant_column,
                dimension=result.dimension_name,
                fixed_basis_size=result.fixed_basis_size,
                random_basis_size=result.random_basis_size,
                random_slope_predictor=result.random_slope_predictor,
                spline_degree=result.spline_degree,
                reml=result.reml,
                method=result.method,
                maxiter=result.maxiter,
            )
        except Exception as exc:
            raise RuntimeError(
                "full-refit participant bootstrap replicate "
                f"{bootstrap_index + 1} failed; no replicate was silently "
                "discarded or redrawn"
            ) from exc

        coefficient_functions[bootstrap_index] = (
            fit_star.coefficient_functions
        )
        fixed_basis_coefficients[bootstrap_index] = (
            fit_star.fixed_basis_coefficients
        )
        random_covariances[bootstrap_index] = (
            fit_star.random_effect_covariance
        )
        intercept_covariances[bootstrap_index] = (
            fit_star.random_intercept_covariance
        )
        if slope_covariances is not None:
            if (
                fit_star.random_slope_covariance is None
                or fit_star.random_intercept_slope_covariance is None
            ):
                raise RuntimeError(
                    "full-refit bootstrap lost the declared random-slope "
                    "covariance structure"
                )
            slope_covariances[bootstrap_index] = (
                fit_star.random_slope_covariance
            )
            cross_covariances[bootstrap_index] = (
                fit_star.random_intercept_slope_covariance
            )

        covariance_eigenvalues[bootstrap_index] = (
            fit_star.random_effect_covariance_eigenvalues
        )
        covariance_condition_numbers[bootstrap_index] = (
            fit_star.random_effect_covariance_condition_number
        )
        boundary_flags[bootstrap_index] = fit_star.boundary_fit
        singular_flags[bootstrap_index] = fit_star.random_effect_singular
        slope_boundary_flags[bootstrap_index] = (
            fit_star.random_slope_boundary_fit
        )
        residual_variances[bootstrap_index] = fit_star.residual_variance
        log_likelihoods[bootstrap_index] = fit_star.log_likelihood
        convergence_flags[bootstrap_index] = fit_star.converged
        warning_records.append(tuple(fit_star.backend_warnings))

    bootstrap_mean = np.mean(coefficient_functions, axis=0)
    bootstrap_standard_errors = np.std(
        coefficient_functions,
        axis=0,
        ddof=1,
    )

    return FunctionalMixedEffectsFullRefitBootstrapResult(
        reference=result,
        bootstrap_fixed_basis_coefficients=fixed_basis_coefficients,
        bootstrap_coefficient_functions=coefficient_functions,
        sampled_participant_indices=sampled_participant_indices,
        sampled_source_participant_ids=tuple(sampled_source_ids),
        bootstrap_participant_ids=tuple(sampled_bootstrap_ids),
        bootstrap_mean=bootstrap_mean,
        bootstrap_standard_errors=bootstrap_standard_errors,
        random_effect_covariances=random_covariances,
        random_intercept_covariances=intercept_covariances,
        random_slope_covariances=slope_covariances,
        random_intercept_slope_covariances=cross_covariances,
        random_effect_covariance_eigenvalues=covariance_eigenvalues,
        random_effect_covariance_condition_numbers=(
            covariance_condition_numbers
        ),
        random_effect_boundary_flags=boundary_flags,
        random_effect_singular_flags=singular_flags,
        random_slope_boundary_flags=slope_boundary_flags,
        residual_variances=residual_variances,
        log_likelihoods=log_likelihoods,
        convergence_flags=convergence_flags,
        backend_warnings=tuple(warning_records),
        random_state=random_state,
        provenance={
            **dict(result.provenance),
            "functional_mixed_effects_full_refit_bootstrap": {
                "method": "whole_participant_case_bootstrap_full_mixedlm_refit",
                "n_bootstrap": n_bootstrap,
                "random_state": random_state,
                "resampling_unit": "participant",
                "participant_draws_with_replacement": True,
                "whole_trial_bundles_resampled": True,
                "duplicate_source_draws_receive_distinct_group_ids": True,
                "source_participant_id_retained": True,
                "bootstrap_participant_id_retained": True,
                "fixed_effects_refit": True,
                "random_effect_covariance_refit": True,
                "residual_variance_refit": True,
                "variance_components_refit": True,
                "fixed_basis_size_reselected": False,
                "random_basis_size_reselected": False,
                "knots_reselected_from_data": False,
                "preprocessing_repeated": False,
                "response_dimension_reselected": False,
                "predictors_reselected": False,
                "random_slope_structure_reselected": False,
                "optimizer_reselected": False,
                "reml_ml_choice_reselected": False,
                "failed_replicate_policy": "raise",
                "successful_replicates_conditioned_on": False,
            },
        },
    )


def functional_mixed_effects_full_refit_audit_frame(
    bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
) -> pd.DataFrame:
    """Return one row per bootstrap participant draw with source/group IDs."""

    if not isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a FunctionalMixedEffectsFullRefitBootstrapResult"
        )
    rows: list[dict[str, int | str]] = []
    for bootstrap_index in range(bootstrap.n_bootstrap):
        for draw_index in range(bootstrap.n_participants):
            rows.append(
                {
                    "bootstrap_replicate": bootstrap_index,
                    "draw_index": draw_index,
                    "source_participant_index": int(
                        bootstrap.sampled_participant_indices[
                            bootstrap_index,
                            draw_index,
                        ]
                    ),
                    "source_participant_id": (
                        bootstrap.sampled_source_participant_ids[
                            bootstrap_index
                        ][draw_index]
                    ),
                    "bootstrap_participant_id": (
                        bootstrap.bootstrap_participant_ids[
                            bootstrap_index
                        ][draw_index]
                    ),
                }
            )
    return pd.DataFrame(rows)


def functional_mixed_effects_variance_bootstrap_frame(
    bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
) -> pd.DataFrame:
    """Summarize refitted variance-component diagnostics by replicate."""

    if not isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a FunctionalMixedEffectsFullRefitBootstrapResult"
        )

    rows: list[dict[str, float | int | bool]] = []
    for bootstrap_index in range(bootstrap.n_bootstrap):
        eigenvalues = bootstrap.random_effect_covariance_eigenvalues[
            bootstrap_index
        ]
        row: dict[str, float | int | bool] = {
            "bootstrap_replicate": bootstrap_index,
            "residual_variance": float(
                bootstrap.residual_variances[bootstrap_index]
            ),
            "log_likelihood": float(
                bootstrap.log_likelihoods[bootstrap_index]
            ),
            "covariance_min_eigenvalue": float(np.min(eigenvalues)),
            "covariance_max_eigenvalue": float(np.max(eigenvalues)),
            "covariance_trace": float(
                np.trace(
                    bootstrap.random_effect_covariances[
                        bootstrap_index
                    ]
                )
            ),
            "covariance_condition_number": float(
                bootstrap.random_effect_covariance_condition_numbers[
                    bootstrap_index
                ]
            ),
            "boundary_fit": bool(
                bootstrap.random_effect_boundary_flags[
                    bootstrap_index
                ]
            ),
            "singular_fit": bool(
                bootstrap.random_effect_singular_flags[
                    bootstrap_index
                ]
            ),
            "random_slope_boundary_fit": bool(
                bootstrap.random_slope_boundary_flags[
                    bootstrap_index
                ]
            ),
            "converged": bool(
                bootstrap.convergence_flags[bootstrap_index]
            ),
            "backend_warning_count": len(
                bootstrap.backend_warnings[bootstrap_index]
            ),
            "random_intercept_covariance_trace": float(
                np.trace(
                    bootstrap.random_intercept_covariances[
                        bootstrap_index
                    ]
                )
            ),
        }
        if bootstrap.random_slope_covariances is not None:
            row["random_slope_covariance_trace"] = float(
                np.trace(
                    bootstrap.random_slope_covariances[
                        bootstrap_index
                    ]
                )
            )
            row["intercept_slope_cross_covariance_frobenius"] = float(
                np.linalg.norm(
                    bootstrap.random_intercept_slope_covariances[
                        bootstrap_index
                    ],
                    ord="fro",
                )
            )
        rows.append(row)
    return pd.DataFrame(rows)


def compare_functional_mixed_effects_bootstraps(
    fixed_covariance_bootstrap: FunctionalMixedEffectsBootstrapResult,
    full_refit_bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "coefficient",
) -> pd.DataFrame:
    """Compare simultaneous band widths from conditional and full-refit bootstraps."""

    if not isinstance(
        fixed_covariance_bootstrap,
        FunctionalMixedEffectsBootstrapResult,
    ):
        raise TypeError(
            "fixed_covariance_bootstrap must be a "
            "FunctionalMixedEffectsBootstrapResult"
        )
    if not isinstance(
        full_refit_bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "full_refit_bootstrap must be a "
            "FunctionalMixedEffectsFullRefitBootstrapResult"
        )
    if fixed_covariance_bootstrap.reference is not full_refit_bootstrap.reference:
        raise ValueError(
            "both bootstrap objects must share the exact reference fit"
        )

    fixed_band = functional_mixed_effects_simultaneous_bands(
        fixed_covariance_bootstrap,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
    )
    full_band = functional_mixed_effects_simultaneous_bands(
        full_refit_bootstrap,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
    )
    fixed_width = fixed_band.upper - fixed_band.lower
    full_width = full_band.upper - full_band.lower

    rows: list[dict[str, float | str]] = []
    reference = fixed_covariance_bootstrap.reference
    for coefficient_index, coefficient_name in enumerate(
        reference.coefficient_names
    ):
        for time_index, time_value in enumerate(reference.time):
            conditional_width = float(
                fixed_width[coefficient_index, time_index]
            )
            refit_width = float(
                full_width[coefficient_index, time_index]
            )
            rows.append(
                {
                    "coefficient": coefficient_name,
                    "time": float(time_value),
                    "fixed_covariance_band_width": conditional_width,
                    "full_refit_band_width": refit_width,
                    "full_refit_to_fixed_covariance_width_ratio": (
                        float(refit_width / conditional_width)
                        if conditional_width > 0
                        else float("inf")
                    ),
                    "confidence_level": float(confidence_level),
                    "simultaneous_scope": simultaneous_scope,
                }
            )
    return pd.DataFrame(rows)
