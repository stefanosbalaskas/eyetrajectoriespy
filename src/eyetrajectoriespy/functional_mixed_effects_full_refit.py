"""Full-refit participant bootstrap for functional mixed-effects models."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .functional_mixed_effects import fit_functional_mixed_effects_regression
from .types import (
    FunctionalMixedEffectsBootstrapResult,
    FunctionalMixedEffectsFullRefitBootstrapResult,
    FunctionalMixedEffectsResult,
    TrajectorySet,
)


def _validate_reference(
    result: FunctionalMixedEffectsResult,
) -> None:
    if not isinstance(result, FunctionalMixedEffectsResult):
        raise TypeError("fit must be a FunctionalMixedEffectsResult")
    if not result.converged:
        raise ValueError("reference mixed-effects fit must have converged")
    if result.scalar_design_matrix.shape != (
        result.n_curves,
        result.n_coefficients,
    ):
        raise ValueError(
            "reference scalar_design_matrix has an unexpected shape"
        )
    if result.n_coefficients != len(result.predictor_names) + 1:
        raise ValueError(
            "reference coefficient/predictor contract is inconsistent"
        )
    if not np.allclose(
        result.scalar_design_matrix[:, 0],
        1.0,
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError(
            "reference scalar_design_matrix must retain an intercept column"
        )


def _validate_bootstrap_args(
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
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100")

    if random_state is not None and (
        isinstance(random_state, bool)
        or not isinstance(random_state, (int, np.integer))
    ):
        raise TypeError("random_state must be an integer or None")
    return (
        n_bootstrap,
        None if random_state is None else int(random_state),
    )


def _bootstrap_sample(
    fit: FunctionalMixedEffectsResult,
    *,
    sampled_participant_indices: np.ndarray,
    replicate_index: int,
) -> tuple[
    TrajectorySet,
    pd.DataFrame,
    tuple[str, ...],
    tuple[str, ...],
]:
    participant_labels = np.asarray(
        fit.curve_participant_ids,
        dtype=object,
    )
    predictor_matrix = np.asarray(
        fit.scalar_design_matrix[:, 1:],
        dtype=float,
    )

    values: list[np.ndarray] = []
    curve_ids: list[str] = []
    metadata_rows: list[dict[str, str]] = []
    design_rows: list[dict[str, float | str]] = []
    source_participant_ids: list[str] = []
    bootstrap_participant_ids: list[str] = []

    for draw_position, participant_index in enumerate(
        sampled_participant_indices
    ):
        source_id = str(fit.participant_ids[int(participant_index)])
        bootstrap_id = (
            f"bootstrap_{replicate_index:04d}_"
            f"group_{draw_position:04d}"
        )
        source_participant_ids.append(source_id)
        bootstrap_participant_ids.append(bootstrap_id)

        curve_indices = np.flatnonzero(
            participant_labels == source_id
        )
        if curve_indices.size == 0:
            raise RuntimeError(
                "bootstrap source participant has no associated curves"
            )

        for local_curve_index, curve_index in enumerate(curve_indices):
            source_curve_id = str(
                fit.source_curve_ids[int(curve_index)]
            )
            bootstrap_curve_id = (
                f"{bootstrap_id}::"
                f"curve_{local_curve_index:04d}::"
                f"{source_curve_id}"
            )
            curve_ids.append(bootstrap_curve_id)
            values.append(
                np.asarray(
                    fit.observed_functions[int(curve_index)],
                    dtype=float,
                )[:, None]
            )
            metadata_rows.append(
                {
                    "_bootstrap_participant_id": bootstrap_id,
                    "_source_participant_id": source_id,
                }
            )
            row: dict[str, float | str] = {
                "curve_id": bootstrap_curve_id,
            }
            for predictor_index, predictor_name in enumerate(
                fit.predictor_names
            ):
                row[predictor_name] = float(
                    predictor_matrix[
                        int(curve_index),
                        predictor_index,
                    ]
                )
            design_rows.append(row)

    trajectories = TrajectorySet(
        time=fit.time.copy(),
        values=np.asarray(values, dtype=float),
        curve_ids=tuple(curve_ids),
        dimension_names=(fit.dimension_name,),
        metadata=pd.DataFrame(metadata_rows),
        coordinate_system=fit.coordinate_system,
        time_unit=fit.time_unit,
        provenance={
            **dict(fit.provenance),
            "full_refit_bootstrap_sample": {
                "replicate_index": replicate_index,
                "source_participant_ids": source_participant_ids,
                "bootstrap_participant_ids": bootstrap_participant_ids,
                "duplicate_source_participants_receive_distinct_groups": True,
            },
        },
    )
    design = pd.DataFrame(design_rows)
    return (
        trajectories,
        design,
        tuple(source_participant_ids),
        tuple(bootstrap_participant_ids),
    )


def bootstrap_functional_mixed_effects_full_refit(
    fit: FunctionalMixedEffectsResult,
    *,
    n_bootstrap: int = 1000,
    random_state: int | None = 0,
) -> FunctionalMixedEffectsFullRefitBootstrapResult:
    """Bootstrap whole participants and refit the complete declared mixed model.

    Every bootstrap draw samples participants with replacement. Each occurrence
    of a sampled source participant receives a new bootstrap group identity, so
    duplicated source participants remain independent bootstrap clusters rather
    than being merged by the mixed-model backend.

    Each replicate refits fixed effects, the complete declared random-effect
    covariance, and residual variance. Basis sizes, knot construction, response
    dimension, predictors, random-slope choice, random-effect structure, REML/ML
    choice, optimizer, and preprocessing/model specification remain fixed.

    Any failed replicate raises immediately. No failed draw is discarded or
    silently replaced.
    """

    _validate_reference(fit)
    n_bootstrap, random_state = _validate_bootstrap_args(
        n_bootstrap=n_bootstrap,
        random_state=random_state,
    )

    rng = np.random.default_rng(random_state)
    sampled_participant_indices = rng.integers(
        0,
        fit.n_participants,
        size=(n_bootstrap, fit.n_participants),
    )

    bootstrap_fixed_basis_coefficients = np.empty(
        (
            n_bootstrap,
            fit.n_coefficients,
            fit.fixed_basis_size,
        ),
        dtype=float,
    )
    bootstrap_coefficient_functions = np.empty(
        (
            n_bootstrap,
            fit.n_coefficients,
            fit.time.size,
        ),
        dtype=float,
    )
    bootstrap_random_effect_covariances = np.empty(
        (
            n_bootstrap,
            fit.random_effect_dimension,
            fit.random_effect_dimension,
        ),
        dtype=float,
    )
    bootstrap_random_intercept_covariances = np.empty(
        (
            n_bootstrap,
            fit.random_basis_size,
            fit.random_basis_size,
        ),
        dtype=float,
    )
    if fit.random_slope_predictor is None:
        bootstrap_random_slope_covariances = None
        bootstrap_intercept_slope_covariances = None
    else:
        bootstrap_random_slope_covariances = np.empty(
            (
                n_bootstrap,
                fit.random_basis_size,
                fit.random_basis_size,
            ),
            dtype=float,
        )
        bootstrap_intercept_slope_covariances = np.empty(
            (
                n_bootstrap,
                fit.random_basis_size,
                fit.random_basis_size,
            ),
            dtype=float,
        )

    bootstrap_covariance_eigenvalues = np.empty(
        (n_bootstrap, fit.random_effect_dimension),
        dtype=float,
    )
    bootstrap_covariance_condition_numbers = np.empty(
        n_bootstrap,
        dtype=float,
    )
    bootstrap_residual_variances = np.empty(
        n_bootstrap,
        dtype=float,
    )
    bootstrap_log_likelihoods = np.empty(
        n_bootstrap,
        dtype=float,
    )
    bootstrap_boundary_fit = np.empty(
        n_bootstrap,
        dtype=bool,
    )
    bootstrap_random_effect_singular = np.empty(
        n_bootstrap,
        dtype=bool,
    )
    bootstrap_random_slope_boundary_fit = np.empty(
        n_bootstrap,
        dtype=bool,
    )
    bootstrap_converged = np.empty(
        n_bootstrap,
        dtype=bool,
    )
    backend_warnings: list[tuple[str, ...]] = []
    source_audit: list[tuple[str, ...]] = []
    bootstrap_group_audit: list[tuple[str, ...]] = []

    for bootstrap_index in range(n_bootstrap):
        sample_indices = sampled_participant_indices[
            bootstrap_index
        ]
        (
            trajectories_star,
            design_star,
            source_ids,
            bootstrap_ids,
        ) = _bootstrap_sample(
            fit,
            sampled_participant_indices=sample_indices,
            replicate_index=bootstrap_index,
        )
        source_audit.append(source_ids)
        bootstrap_group_audit.append(bootstrap_ids)

        try:
            fitted_star = fit_functional_mixed_effects_regression(
                trajectories_star,
                design_star,
                predictors=fit.predictor_names,
                participant_column="_bootstrap_participant_id",
                dimension=fit.dimension_name,
                fixed_basis_size=fit.fixed_basis_size,
                random_basis_size=fit.random_basis_size,
                random_slope_predictor=fit.random_slope_predictor,
                spline_degree=fit.spline_degree,
                reml=fit.reml,
                method=fit.method,
                maxiter=fit.maxiter,
            )
        except Exception as exc:
            raise RuntimeError(
                "full-refit participant bootstrap replicate "
                f"{bootstrap_index + 1} failed for source participant draw "
                f"{source_ids}; no failed replicate was discarded or redrawn"
            ) from exc

        if not fitted_star.converged:
            raise RuntimeError(
                "full-refit participant bootstrap replicate "
                f"{bootstrap_index + 1} did not converge; no failed replicate "
                "was discarded or redrawn"
            )

        bootstrap_fixed_basis_coefficients[
            bootstrap_index
        ] = fitted_star.fixed_basis_coefficients
        bootstrap_coefficient_functions[
            bootstrap_index
        ] = fitted_star.coefficient_functions
        bootstrap_random_effect_covariances[
            bootstrap_index
        ] = fitted_star.random_effect_covariance
        bootstrap_random_intercept_covariances[
            bootstrap_index
        ] = fitted_star.random_intercept_covariance

        if (
            bootstrap_random_slope_covariances is not None
            and bootstrap_intercept_slope_covariances is not None
        ):
            if (
                fitted_star.random_slope_covariance is None
                or fitted_star.random_intercept_slope_covariance is None
            ):
                raise RuntimeError(
                    "full-refit bootstrap lost the declared random-slope "
                    "covariance structure"
                )
            bootstrap_random_slope_covariances[
                bootstrap_index
            ] = fitted_star.random_slope_covariance
            bootstrap_intercept_slope_covariances[
                bootstrap_index
            ] = fitted_star.random_intercept_slope_covariance

        bootstrap_covariance_eigenvalues[
            bootstrap_index
        ] = fitted_star.random_effect_covariance_eigenvalues
        bootstrap_covariance_condition_numbers[
            bootstrap_index
        ] = fitted_star.random_effect_covariance_condition_number
        bootstrap_residual_variances[
            bootstrap_index
        ] = fitted_star.residual_variance
        bootstrap_log_likelihoods[
            bootstrap_index
        ] = fitted_star.log_likelihood
        bootstrap_boundary_fit[
            bootstrap_index
        ] = fitted_star.boundary_fit
        bootstrap_random_effect_singular[
            bootstrap_index
        ] = fitted_star.random_effect_singular
        bootstrap_random_slope_boundary_fit[
            bootstrap_index
        ] = fitted_star.random_slope_boundary_fit
        bootstrap_converged[
            bootstrap_index
        ] = fitted_star.converged
        backend_warnings.append(
            tuple(fitted_star.backend_warnings)
        )

    bootstrap_mean = np.mean(
        bootstrap_coefficient_functions,
        axis=0,
    )
    bootstrap_standard_errors = np.std(
        bootstrap_coefficient_functions,
        axis=0,
        ddof=1,
    )

    return FunctionalMixedEffectsFullRefitBootstrapResult(
        reference=fit,
        bootstrap_fixed_basis_coefficients=(
            bootstrap_fixed_basis_coefficients
        ),
        bootstrap_coefficient_functions=(
            bootstrap_coefficient_functions
        ),
        bootstrap_random_effect_covariances=(
            bootstrap_random_effect_covariances
        ),
        bootstrap_random_intercept_covariances=(
            bootstrap_random_intercept_covariances
        ),
        bootstrap_random_slope_covariances=(
            bootstrap_random_slope_covariances
        ),
        bootstrap_intercept_slope_covariances=(
            bootstrap_intercept_slope_covariances
        ),
        bootstrap_covariance_eigenvalues=(
            bootstrap_covariance_eigenvalues
        ),
        bootstrap_covariance_condition_numbers=(
            bootstrap_covariance_condition_numbers
        ),
        bootstrap_residual_variances=(
            bootstrap_residual_variances
        ),
        bootstrap_log_likelihoods=bootstrap_log_likelihoods,
        bootstrap_boundary_fit=bootstrap_boundary_fit,
        bootstrap_random_effect_singular=(
            bootstrap_random_effect_singular
        ),
        bootstrap_random_slope_boundary_fit=(
            bootstrap_random_slope_boundary_fit
        ),
        bootstrap_converged=bootstrap_converged,
        bootstrap_backend_warnings=tuple(backend_warnings),
        sampled_participant_indices=sampled_participant_indices,
        sampled_source_participant_ids=tuple(source_audit),
        bootstrap_participant_ids=tuple(
            bootstrap_group_audit
        ),
        bootstrap_mean=bootstrap_mean,
        bootstrap_standard_errors=bootstrap_standard_errors,
        random_state=random_state,
        failed_replicate_policy="raise",
        refit_contract=(
            "full_mixed_model_refit_conditional_on_declared_model_specification"
        ),
        provenance={
            **dict(fit.provenance),
            "functional_mixed_effects_full_refit_bootstrap": {
                "method": "whole_participant_case_bootstrap_full_refit",
                "n_bootstrap": n_bootstrap,
                "random_state": random_state,
                "resampling_unit": "participant",
                "whole_trial_bundles_resampled": True,
                "participant_draws_with_replacement": True,
                "duplicate_source_participants_receive_distinct_bootstrap_groups": True,
                "source_participant_ids_retained": True,
                "bootstrap_participant_ids_retained": True,
                "fixed_effects_refit": True,
                "random_effect_covariance_refit": True,
                "residual_variance_refit": True,
                "variance_components_refit": True,
                "basis_sizes_refit": False,
                "knot_rule_changed": False,
                "preprocessing_repeated": False,
                "response_dimension_changed": False,
                "predictor_specification_changed": False,
                "random_slope_choice_changed": False,
                "random_effect_structure_changed": False,
                "optimizer_changed": False,
                "reml_choice_changed": False,
                "failed_replicate_policy": "raise",
                "automatic_redraw_after_failure": False,
                "random_slope_predictor": fit.random_slope_predictor,
            },
        },
    )


def functional_mixed_effects_variance_bootstrap_frame(
    bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
) -> pd.DataFrame:
    """Return tidy replicate-level variance-component stability diagnostics."""

    if not isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a "
            "FunctionalMixedEffectsFullRefitBootstrapResult"
        )

    rows: list[dict[str, object]] = []
    for replicate in range(bootstrap.n_bootstrap):
        row: dict[str, object] = {
            "replicate": replicate,
            "residual_variance": float(
                bootstrap.bootstrap_residual_variances[replicate]
            ),
            "log_likelihood": float(
                bootstrap.bootstrap_log_likelihoods[replicate]
            ),
            "covariance_condition_number": float(
                bootstrap.bootstrap_covariance_condition_numbers[
                    replicate
                ]
            ),
            "boundary_fit": bool(
                bootstrap.bootstrap_boundary_fit[replicate]
            ),
            "random_effect_singular": bool(
                bootstrap.bootstrap_random_effect_singular[
                    replicate
                ]
            ),
            "random_slope_boundary_fit": bool(
                bootstrap.bootstrap_random_slope_boundary_fit[
                    replicate
                ]
            ),
            "converged": bool(
                bootstrap.bootstrap_converged[replicate]
            ),
            "backend_warning_count": len(
                bootstrap.bootstrap_backend_warnings[replicate]
            ),
        }
        for eigen_index, eigenvalue in enumerate(
            bootstrap.bootstrap_covariance_eigenvalues[replicate]
        ):
            row[f"covariance_eigenvalue_{eigen_index + 1}"] = float(
                eigenvalue
            )
        rows.append(row)
    return pd.DataFrame(rows)


def functional_mixed_effects_bootstrap_identity_frame(
    bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
) -> pd.DataFrame:
    """Return source and distinct bootstrap group identities for every draw."""

    if not isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a "
            "FunctionalMixedEffectsFullRefitBootstrapResult"
        )

    rows = []
    for replicate, (
        source_ids,
        bootstrap_ids,
    ) in enumerate(
        zip(
            bootstrap.sampled_source_participant_ids,
            bootstrap.bootstrap_participant_ids,
            strict=True,
        )
    ):
        for draw_position, (
            source_id,
            bootstrap_id,
        ) in enumerate(
            zip(
                source_ids,
                bootstrap_ids,
                strict=True,
            )
        ):
            rows.append(
                {
                    "replicate": replicate,
                    "draw_position": draw_position,
                    "source_participant_id": source_id,
                    "bootstrap_participant_id": bootstrap_id,
                }
            )
    return pd.DataFrame(rows)


def compare_functional_mixed_effects_bootstraps(
    fixed_covariance_bootstrap: FunctionalMixedEffectsBootstrapResult,
    full_refit_bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
    *,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "coefficient",
) -> pd.DataFrame:
    """Compare fixed-covariance and full-refit simultaneous band widths."""

    from .functional_mixed_effects_inference import (
        functional_mixed_effects_simultaneous_bands,
    )

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
    if (
        fixed_covariance_bootstrap.reference
        is not full_refit_bootstrap.reference
    ):
        raise ValueError(
            "both bootstrap objects must reference the same fitted model "
            "object"
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

    reference = fixed_covariance_bootstrap.reference
    rows = []
    for coefficient_index, coefficient_name in enumerate(
        reference.coefficient_names
    ):
        fixed_width = (
            fixed_band.upper[coefficient_index]
            - fixed_band.lower[coefficient_index]
        )
        full_width = (
            full_band.upper[coefficient_index]
            - full_band.lower[coefficient_index]
        )
        ratio = np.divide(
            full_width,
            fixed_width,
            out=np.full_like(full_width, np.nan),
            where=fixed_width > np.finfo(float).eps,
        )
        for time_index, time_value in enumerate(reference.time):
            rows.append(
                {
                    "coefficient": coefficient_name,
                    "time": float(time_value),
                    "fixed_covariance_band_width": float(
                        fixed_width[time_index]
                    ),
                    "full_refit_band_width": float(
                        full_width[time_index]
                    ),
                    "full_to_fixed_width_ratio": float(
                        ratio[time_index]
                    ),
                    "confidence_level": float(confidence_level),
                    "simultaneous_scope": simultaneous_scope,
                }
            )
    return pd.DataFrame(rows)


def functional_mixed_effects_full_refit_reporting_text(
    bootstrap: FunctionalMixedEffectsFullRefitBootstrapResult,
) -> str:
    """Return compact reporting text for the full-refit participant bootstrap."""

    if not isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    ):
        raise TypeError(
            "bootstrap must be a "
            "FunctionalMixedEffectsFullRefitBootstrapResult"
        )

    boundary_fraction = float(
        np.mean(bootstrap.bootstrap_boundary_fit)
    )
    singular_fraction = float(
        np.mean(bootstrap.bootstrap_random_effect_singular)
    )
    warning_fraction = float(
        np.mean(
            np.asarray(
                [
                    len(messages) > 0
                    for messages in bootstrap.bootstrap_backend_warnings
                ],
                dtype=float,
            )
        )
    )
    residual = np.asarray(
        bootstrap.bootstrap_residual_variances,
        dtype=float,
    )
    return (
        "A whole-participant case bootstrap with full mixed-model refitting "
        f"used {bootstrap.n_bootstrap} replicates. Every sampled participant "
        "occurrence received a distinct bootstrap group identity, including "
        "duplicate source participants. Fixed effects, the complete declared "
        "random-effect covariance, and residual variance were re-estimated in "
        "every replicate, while preprocessing, predictors, random-slope "
        "choice, random-effect structure, basis specification, REML/ML choice, "
        "and optimizer were held fixed. "
        f"The fitted random-effect covariance was boundary-flagged in "
        f"{boundary_fraction:.3f} of replicates and singular-flagged in "
        f"{singular_fraction:.3f}; backend warnings occurred in "
        f"{warning_fraction:.3f}. Residual variance across replicates had "
        f"median {np.median(residual):.6g} and range "
        f"[{np.min(residual):.6g}, {np.max(residual):.6g}]. "
        "These empirical variance-component distributions are stability "
        "diagnostics rather than automatically calibrated confidence "
        "intervals. Any failed replicate would terminate the bootstrap rather "
        "than being discarded or redrawn."
    )
