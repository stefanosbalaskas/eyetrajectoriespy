import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionalMixedEffectsBandResult,
    FunctionalMixedEffectsBootstrapResult,
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_coefficient_frame,
    functional_mixed_effects_reporting_text,
    functional_mixed_effects_simultaneous_bands,
    plot_functional_mixed_effects_coefficient,
)


def _mixed_data(seed=2026):
    rng = np.random.default_rng(seed)
    n_participants = 12
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 9)
    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile([0.0, 1.0, 0.5], n_participants)

    intercept = 0.20 + 0.15 * time
    condition_effect = 0.15 + 0.40 * time
    basis = np.column_stack([1.0 - time, time])
    random_coefficients = rng.multivariate_normal(
        [0.0, 0.0],
        [[0.030, 0.004], [0.004, 0.020]],
        size=n_participants,
    )

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        random_function = random_coefficients[participant_index] @ basis.T
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            values.append(
                (
                    intercept
                    + condition[curve_index] * condition_effect
                    + random_function
                    + rng.normal(0.0, 0.04, size=time.size)
                )[:, None]
            )
            curve_ids.append(f"C{curve_index:03d}")

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
    return trajectories, design


def _fit(seed=2026):
    trajectories, design = _mixed_data(seed)
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=500,
    )


def test_participant_cluster_bootstrap_is_deterministic_and_hierarchical():
    result = _fit()
    first = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=120,
        random_state=44,
    )
    second = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=120,
        random_state=44,
    )

    assert isinstance(first, FunctionalMixedEffectsBootstrapResult)
    assert first.n_bootstrap == 120
    assert first.n_participants == result.n_participants
    assert first.bootstrap_fixed_basis_coefficients.shape == (
        120,
        result.n_coefficients,
        result.fixed_basis_size,
    )
    assert first.bootstrap_coefficient_functions.shape == (
        120,
        result.n_coefficients,
        result.time.size,
    )
    assert first.bootstrap_standard_errors.shape == (
        result.n_coefficients,
        result.time.size,
    )
    assert np.all(np.isfinite(first.bootstrap_standard_errors))
    assert np.all(first.bootstrap_standard_errors > 0)

    np.testing.assert_array_equal(
        first.sampled_participant_indices,
        second.sampled_participant_indices,
    )
    np.testing.assert_allclose(
        first.bootstrap_coefficient_functions,
        second.bootstrap_coefficient_functions,
    )

    provenance = first.provenance[
        "functional_mixed_effects_bootstrap"
    ]
    assert provenance["resampling_unit"] == "participant"
    assert provenance["whole_trial_bundles_resampled"] is True
    assert provenance["curves_resampled_independently"] is False
    assert provenance["variance_components_refit"] is False
    assert provenance["fixed_effects_reestimated_each_replicate"] is True
    assert provenance["failed_replicate_policy"] == "raise"
    assert provenance["reference_gls_max_abs_difference"] < 1e-8


def test_simultaneous_bands_support_coefficient_and_family_scope():
    result = _fit(seed=14)
    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=150,
        random_state=9,
    )
    coefficient_band = functional_mixed_effects_simultaneous_bands(
        bootstrap,
        confidence_level=0.95,
        simultaneous_scope="coefficient",
    )
    family_band = functional_mixed_effects_simultaneous_bands(
        bootstrap,
        confidence_level=0.95,
        simultaneous_scope="family",
    )

    assert isinstance(
        coefficient_band,
        FunctionalMixedEffectsBandResult,
    )
    assert coefficient_band.lower.shape == (
        result.n_coefficients,
        result.time.size,
    )
    assert coefficient_band.max_statistics.shape == (
        150,
        result.n_coefficients,
    )
    assert family_band.max_statistics.shape == (150, 1)
    assert np.all(
        family_band.critical_values
        >= coefficient_band.critical_values
    )
    np.testing.assert_allclose(
        family_band.critical_values,
        family_band.critical_values[0],
    )
    assert np.all(
        coefficient_band.lower
        < result.coefficient_functions
    )
    assert np.all(
        result.coefficient_functions
        < coefficient_band.upper
    )

    contract = coefficient_band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]
    assert contract["simultaneous_domain"] == (
        "observed_time_grid_per_coefficient"
    )
    assert contract["continuous_between_grid_points"] is False
    assert contract["variance_components_refit"] is False
    assert contract["bias_correction"] is False


def test_band_frame_plot_and_reporting_are_explicit_about_scope():
    result = _fit(seed=31)
    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=120,
        random_state=5,
    )
    band = functional_mixed_effects_simultaneous_bands(bootstrap)

    frame = functional_mixed_effects_coefficient_frame(
        result,
        band=band,
    )
    assert {
        "bootstrap_standard_error",
        "lower_simultaneous",
        "upper_simultaneous",
        "simultaneous_critical_value",
        "simultaneous_scope",
    } <= set(frame.columns)
    assert set(frame["simultaneous_scope"]) == {"coefficient"}

    ax = plot_functional_mixed_effects_coefficient(
        band,
        coefficient="condition",
    )
    assert "condition" in ax.get_title()
    assert "simultaneous band" in ax.get_legend().get_texts()[0].get_text()

    text = functional_mixed_effects_reporting_text(
        result,
        band=band,
    )
    assert "Participant-cluster bootstrap" in text
    assert "whole-participant resamples" in text
    assert "held fixed" in text
    assert "variance-component" in text
    assert "unsampled grid points" in text


def test_simultaneous_inference_contracts_fail_closed():
    result = _fit(seed=42)

    with pytest.raises(ValueError, match="at least 100"):
        bootstrap_functional_mixed_effects_coefficients(
            result,
            n_bootstrap=99,
        )
    with pytest.raises(TypeError, match="n_bootstrap"):
        bootstrap_functional_mixed_effects_coefficients(
            result,
            n_bootstrap=True,
        )
    with pytest.raises(TypeError, match="random_state"):
        bootstrap_functional_mixed_effects_coefficients(
            result,
            n_bootstrap=100,
            random_state=True,
        )

    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=100,
        random_state=1,
    )
    with pytest.raises(ValueError, match="confidence_level"):
        functional_mixed_effects_simultaneous_bands(
            bootstrap,
            confidence_level=1.0,
        )
    with pytest.raises(ValueError, match="simultaneous_scope"):
        functional_mixed_effects_simultaneous_bands(
            bootstrap,
            simultaneous_scope="bad",
        )
    with pytest.raises(TypeError):
        functional_mixed_effects_simultaneous_bands(object())
    with pytest.raises(TypeError, match="band must be"):
        functional_mixed_effects_coefficient_frame(
            result,
            band=object(),
        )
    with pytest.raises(TypeError):
        plot_functional_mixed_effects_coefficient(
            object(),
            coefficient="condition",
        )
