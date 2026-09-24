import numpy as np
import pandas as pd
import pytest
from dataclasses import replace

import eyetrajectoriespy.functional_mixed_effects_full_refit as full_refit_module
from eyetrajectoriespy import (
    FunctionalMixedEffectsFullRefitBootstrapResult,
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    bootstrap_functional_mixed_effects_full_refit,
    compare_functional_mixed_effects_bootstraps,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_bootstrap_identity_frame,
    functional_mixed_effects_simultaneous_bands,
    functional_mixed_effects_variance_bootstrap_frame,
    plot_functional_mixed_effects_bootstrap_comparison,
)


def _reference_fit(seed=460):
    rng = np.random.default_rng(seed)
    n_participants = 8
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 6)
    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile([-0.5, 0.0, 0.5], n_participants)
    beta0 = 0.2 + 0.1 * time
    beta1 = 0.3 + 0.2 * time
    random_intercepts = rng.normal(0.0, 0.10, size=n_participants)
    random_slopes = rng.normal(0.0, 0.07, size=n_participants)

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        for trial_index in range(trials_per_participant):
            row = participant_index * trials_per_participant + trial_index
            values.append(
                (
                    beta0
                    + condition[row] * beta1
                    + random_intercepts[participant_index]
                    + condition[row] * random_slopes[participant_index]
                    + rng.normal(0.0, 0.03, size=time.size)
                )[:, None]
            )
            curve_ids.append(f"C{row:03d}")

    trajectories = TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("metric",),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="unknown",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=1,
        random_slope_predictor="condition",
        spline_degree=0,
        reml=True,
        method="lbfgs",
        maxiter=500,
    )


def test_full_refit_bootstrap_retains_distinct_group_identities(monkeypatch):
    reference = _reference_fit()
    call_index = 0

    def fake_refit(
        trajectories,
        design,
        predictors,
        *,
        participant_column,
        dimension,
        fixed_basis_size,
        random_basis_size,
        random_slope_predictor,
        spline_degree,
        reml,
        method,
        maxiter,
    ):
        nonlocal call_index
        assert participant_column == "_bootstrap_participant_id"
        groups = trajectories.metadata[participant_column].astype(str)
        sources = trajectories.metadata["_source_participant_id"].astype(str)
        assert groups.nunique() == reference.n_participants

        mapping = (
            trajectories.metadata[
                [participant_column, "_source_participant_id"]
            ]
            .drop_duplicates()
            .reset_index(drop=True)
        )
        assert len(mapping) == reference.n_participants
        assert mapping[participant_column].is_unique

        duplicated_sources = mapping["_source_participant_id"].duplicated(
            keep=False
        )
        if duplicated_sources.any():
            duplicate_rows = mapping.loc[duplicated_sources]
            assert duplicate_rows[participant_column].nunique() == len(
                duplicate_rows
            )

        delta = 0.001 * (call_index + 1)
        scale = 1.0 + 0.002 * (call_index + 1)
        call_index += 1
        covariance = reference.random_effect_covariance * scale
        intercept_covariance = covariance[:1, :1]
        slope_covariance = covariance[1:, 1:]
        cross_covariance = covariance[:1, 1:]
        eigenvalues = np.linalg.eigvalsh(covariance)

        return replace(
            reference,
            fixed_basis_coefficients=(
                reference.fixed_basis_coefficients + delta
            ),
            coefficient_functions=(
                reference.coefficient_functions + delta
            ),
            random_effect_covariance=covariance,
            random_intercept_covariance=intercept_covariance,
            random_slope_covariance=slope_covariance,
            random_intercept_slope_covariance=cross_covariance,
            random_effect_covariance_eigenvalues=eigenvalues,
            random_effect_covariance_condition_number=float(
                np.max(eigenvalues) / np.min(eigenvalues)
            ),
            residual_variance=reference.residual_variance * scale,
            log_likelihood=reference.log_likelihood - delta,
            boundary_fit=False,
            random_effect_singular=False,
            random_slope_boundary_fit=False,
            converged=True,
            backend_warnings=(),
        )

    monkeypatch.setattr(
        full_refit_module,
        "fit_functional_mixed_effects_regression",
        fake_refit,
    )

    bootstrap = bootstrap_functional_mixed_effects_full_refit(
        reference,
        n_bootstrap=100,
        random_state=46,
    )

    assert isinstance(
        bootstrap,
        FunctionalMixedEffectsFullRefitBootstrapResult,
    )
    assert bootstrap.n_bootstrap == 100
    assert bootstrap.n_participants == reference.n_participants
    assert bootstrap.bootstrap_random_effect_covariances.shape == (
        100,
        2,
        2,
    )
    assert bootstrap.bootstrap_random_slope_covariances.shape == (
        100,
        1,
        1,
    )
    assert bootstrap.bootstrap_intercept_slope_covariances.shape == (
        100,
        1,
        1,
    )
    assert np.all(bootstrap.bootstrap_converged)
    assert np.std(bootstrap.bootstrap_residual_variances) > 0
    assert bootstrap.failed_replicate_policy == "raise"

    identity = functional_mixed_effects_bootstrap_identity_frame(
        bootstrap
    )
    assert len(identity) == 100 * reference.n_participants
    for _, replicate in identity.groupby("replicate"):
        assert replicate["bootstrap_participant_id"].is_unique

    duplicated = identity.duplicated(
        ["replicate", "source_participant_id"],
        keep=False,
    )
    assert duplicated.any()
    assert (
        identity.loc[duplicated]
        .groupby(["replicate", "source_participant_id"])[
            "bootstrap_participant_id"
        ]
        .nunique()
        .ge(2)
        .any()
    )

    variance = functional_mixed_effects_variance_bootstrap_frame(
        bootstrap
    )
    assert len(variance) == 100
    assert {
        "residual_variance",
        "log_likelihood",
        "covariance_condition_number",
        "boundary_fit",
        "random_effect_singular",
        "random_slope_boundary_fit",
        "covariance_eigenvalue_1",
        "covariance_eigenvalue_2",
    } <= set(variance.columns)

    provenance = bootstrap.provenance[
        "functional_mixed_effects_full_refit_bootstrap"
    ]
    assert provenance["variance_components_refit"] is True
    assert (
        provenance[
            "duplicate_source_participants_receive_distinct_bootstrap_groups"
        ]
        is True
    )
    assert provenance["basis_sizes_refit"] is False
    assert provenance["random_slope_choice_changed"] is False
    assert provenance["failed_replicate_policy"] == "raise"


def test_full_refit_bootstrap_failure_is_not_redrawn(monkeypatch):
    reference = _reference_fit(seed=461)
    calls = 0

    def failing_refit(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("synthetic optimizer failure")

    monkeypatch.setattr(
        full_refit_module,
        "fit_functional_mixed_effects_regression",
        failing_refit,
    )

    with pytest.raises(
        RuntimeError,
        match="replicate 1 failed.*no failed replicate was discarded or redrawn",
    ):
        bootstrap_functional_mixed_effects_full_refit(
            reference,
            n_bootstrap=100,
            random_state=1,
        )
    assert calls == 1


def test_full_refit_bootstrap_comparison_and_band_contract(monkeypatch):
    reference = _reference_fit(seed=462)
    call_index = 0

    def fake_refit(*args, **kwargs):
        nonlocal call_index
        delta = ((call_index % 7) - 3) * 0.004
        scale = 1.0 + ((call_index % 5) - 2) * 0.01
        call_index += 1
        covariance = reference.random_effect_covariance * scale
        eigenvalues = np.linalg.eigvalsh(covariance)
        return replace(
            reference,
            fixed_basis_coefficients=(
                reference.fixed_basis_coefficients + delta
            ),
            coefficient_functions=(
                reference.coefficient_functions + delta
            ),
            random_effect_covariance=covariance,
            random_intercept_covariance=covariance[:1, :1],
            random_slope_covariance=covariance[1:, 1:],
            random_intercept_slope_covariance=covariance[:1, 1:],
            random_effect_covariance_eigenvalues=eigenvalues,
            random_effect_covariance_condition_number=float(
                np.max(eigenvalues) / np.min(eigenvalues)
            ),
            residual_variance=reference.residual_variance * scale,
            log_likelihood=reference.log_likelihood + delta,
            boundary_fit=False,
            random_effect_singular=False,
            random_slope_boundary_fit=False,
            converged=True,
            backend_warnings=(),
        )

    monkeypatch.setattr(
        full_refit_module,
        "fit_functional_mixed_effects_regression",
        fake_refit,
    )

    full = bootstrap_functional_mixed_effects_full_refit(
        reference,
        n_bootstrap=100,
        random_state=3,
    )
    band = functional_mixed_effects_simultaneous_bands(full)
    assert band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]["variance_components_refit"] is True
    assert band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]["bootstrap_type"] == "full_refit"

    fixed = bootstrap_functional_mixed_effects_coefficients(
        reference,
        n_bootstrap=100,
        random_state=3,
    )
    comparison = compare_functional_mixed_effects_bootstraps(
        fixed,
        full,
    )
    assert len(comparison) == (
        reference.n_coefficients * reference.time.size
    )
    assert np.all(
        comparison["fixed_covariance_band_width"] > 0
    )
    assert np.all(comparison["full_refit_band_width"] > 0)
    assert np.all(
        np.isfinite(comparison["full_to_fixed_width_ratio"])
    )

    ax = plot_functional_mixed_effects_bootstrap_comparison(
        comparison,
        coefficient="condition",
    )
    assert "condition" in ax.get_title()
    assert ax.get_ylabel() == (
        "Full-refit / fixed-covariance band width"
    )


@pytest.mark.parametrize(
    "kwargs,error,match",
    [
        ({"n_bootstrap": 99}, ValueError, "at least 100"),
        ({"n_bootstrap": True}, TypeError, "n_bootstrap"),
        ({"random_state": True}, TypeError, "random_state"),
    ],
)
def test_full_refit_argument_contracts_fail_closed(kwargs, error, match):
    reference = _reference_fit(seed=463)
    parameters = {
        "n_bootstrap": 100,
        "random_state": 0,
    }
    parameters.update(kwargs)
    with pytest.raises(error, match=match):
        bootstrap_functional_mixed_effects_full_refit(
            reference,
            **parameters,
        )


def test_full_refit_helpers_require_full_refit_result():
    with pytest.raises(TypeError):
        functional_mixed_effects_variance_bootstrap_frame(object())
    with pytest.raises(TypeError):
        functional_mixed_effects_bootstrap_identity_frame(object())
