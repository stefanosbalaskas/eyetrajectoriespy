import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    GeneralizedFunctionOnScalarBandResult,
    GeneralizedFunctionOnScalarBootstrapResult,
    GeneralizedFunctionOnScalarResult,
    TrajectorySet,
    bootstrap_generalized_function_on_scalar_coefficients,
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_coefficient_frame,
    generalized_function_on_scalar_reporting_text,
    generalized_function_on_scalar_simultaneous_bands,
    plot_generalized_function_on_scalar_coefficients,
)


def _binary_data(seed=510, n_participants=60):
    rng = np.random.default_rng(seed)
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 7)
    condition_template = np.array([-0.7, 0.0, 0.7])
    condition = np.tile(condition_template, n_participants)
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )

    beta0 = -0.45 + 0.50 * time
    beta1 = 0.90 - 0.35 * time
    eta = beta0[None, :] + condition[:, None] * beta1[None, :]
    probability = 1.0 / (1.0 + np.exp(-eta))
    response = rng.binomial(1, probability).astype(float)

    trajectories = TrajectorySet(
        time=time,
        values=response[:, :, None],
        curve_ids=tuple(f"C{i:04d}" for i in range(response.shape[0])),
        dimension_names=("target_aoi",),
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
    return trajectories, design, beta0, beta1


def _poisson_data(seed=511, n_participants=50):
    rng = np.random.default_rng(seed)
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 7)
    condition_template = np.array([-0.5, 0.0, 0.5])
    condition = np.tile(condition_template, n_participants)
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )

    beta0 = 0.30 + 0.20 * time
    beta1 = 0.45 - 0.15 * time
    eta = beta0[None, :] + condition[:, None] * beta1[None, :]
    mean = np.exp(eta)
    response = rng.poisson(mean).astype(float)

    trajectories = TrajectorySet(
        time=time,
        values=response[:, :, None],
        curve_ids=tuple(f"C{i:04d}" for i in range(response.shape[0])),
        dimension_names=("count",),
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
    return trajectories, design, beta0, beta1


def test_binomial_generalized_fosr_recovers_link_scale_coefficients():
    trajectories, design, beta0, beta1 = _binary_data()
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="target_aoi",
        family="binomial",
        basis_size=2,
        spline_degree=1,
    )

    assert isinstance(fit, GeneralizedFunctionOnScalarResult)
    assert fit.family == "binomial"
    assert fit.link == "logit"
    assert fit.working_correlation == "independence"
    assert fit.covariance_type == "robust"
    assert fit.n_participants == 60
    assert fit.n_curves == 180
    assert fit.coefficient_names == ("Intercept", "condition")
    assert fit.coefficient_functions.shape == (2, trajectories.n_time)
    assert fit.coefficient_standard_errors.shape == (2, trajectories.n_time)
    assert np.all(fit.coefficient_standard_errors >= 0)
    assert np.all((fit.mean_functions > 0) & (fit.mean_functions < 1))

    np.testing.assert_allclose(
        fit.coefficient_functions[0],
        beta0,
        atol=0.35,
    )
    np.testing.assert_allclose(
        fit.coefficient_functions[1],
        beta1,
        atol=0.40,
    )

    contract = fit.provenance["generalized_function_on_scalar_regression"]
    assert contract["marginal_population_averaged_interpretation"] is True
    assert contract["conditional_effect_interpretation"] is False
    assert contract["trial_varying_predictors_supported"] is True
    assert contract["working_correlation_selected_automatically"] is False
    assert contract["automatic_family_selection"] is False
    assert contract["automatic_link_selection"] is False


def test_poisson_generalized_fosr_recovers_log_scale_coefficients():
    trajectories, design, beta0, beta1 = _poisson_data()
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        basis_size=2,
        spline_degree=1,
    )

    assert fit.family == "poisson"
    assert fit.link == "log"
    assert np.all(fit.mean_functions > 0)
    np.testing.assert_allclose(
        fit.coefficient_functions[0],
        beta0,
        atol=0.25,
    )
    np.testing.assert_allclose(
        fit.coefficient_functions[1],
        beta1,
        atol=0.30,
    )


def test_whole_participant_bootstrap_and_simultaneous_bands_are_seeded():
    trajectories, design, _, _ = _binary_data(
        seed=512,
        n_participants=16,
    )
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="target_aoi",
        family="binomial",
        basis_size=2,
        spline_degree=1,
    )

    first = bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=51,
    )
    second = bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=51,
    )

    assert isinstance(first, GeneralizedFunctionOnScalarBootstrapResult)
    assert first.n_bootstrap == 100
    np.testing.assert_array_equal(
        first.sampled_participant_indices,
        second.sampled_participant_indices,
    )
    np.testing.assert_allclose(
        first.bootstrap_coefficient_functions,
        second.bootstrap_coefficient_functions,
    )
    assert first.sampled_source_participant_ids == (
        second.sampled_source_participant_ids
    )
    assert first.sampled_bootstrap_participant_ids == (
        second.sampled_bootstrap_participant_ids
    )
    assert all(
        len(set(ids)) == len(ids)
        for ids in first.sampled_bootstrap_participant_ids
    )
    assert any(
        len(set(ids)) < len(ids)
        for ids in first.sampled_source_participant_ids
    )

    band = generalized_function_on_scalar_simultaneous_bands(
        first,
        confidence_level=0.95,
        simultaneous_scope="coefficient",
    )
    family_band = generalized_function_on_scalar_simultaneous_bands(
        first,
        confidence_level=0.95,
        simultaneous_scope="family",
    )

    assert isinstance(band, GeneralizedFunctionOnScalarBandResult)
    assert band.lower.shape == fit.coefficient_functions.shape
    assert band.upper.shape == fit.coefficient_functions.shape
    assert np.all(band.lower <= fit.coefficient_functions)
    assert np.all(fit.coefficient_functions <= band.upper)
    assert band.provenance[
        "generalized_function_on_scalar_simultaneous_band"
    ]["coefficient_scale"] == "link"
    np.testing.assert_allclose(
        family_band.critical_values,
        family_band.critical_values[0],
    )


def test_frames_plot_and_reporting_preserve_marginal_interpretation():
    trajectories, design, _, _ = _poisson_data(
        seed=513,
        n_participants=20,
    )
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        basis_size=2,
        spline_degree=1,
    )
    bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=513,
    )
    band = generalized_function_on_scalar_simultaneous_bands(
        bootstrap
    )

    frame = generalized_function_on_scalar_coefficient_frame(band)
    assert set(
        (
            "coefficient",
            "time",
            "estimate",
            "standard_error",
            "scale",
            "family",
            "link",
            "lower",
            "upper",
        )
    ) <= set(frame.columns)
    assert set(frame["scale"]) == {"link"}

    ax = plot_generalized_function_on_scalar_coefficients(
        band,
        coefficient="condition",
    )
    assert "condition" in ax.get_title()
    assert "log scale" in ax.get_ylabel()

    text = generalized_function_on_scalar_reporting_text(
        fit,
        band=band,
    )
    assert "population-averaged marginal interpretation" in text
    assert "working independence" in text
    assert "robust GEE sandwich" in text
    assert "selected automatically" in text


def test_response_and_model_contracts_fail_closed():
    trajectories, design, _, _ = _binary_data(
        seed=514,
        n_participants=12,
    )

    bad_values = trajectories.values.copy()
    bad_values[0, 0, 0] = 0.5
    bad_binomial = TrajectorySet(
        time=trajectories.time,
        values=bad_values,
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=trajectories.metadata,
        time_unit=trajectories.time_unit,
    )
    with pytest.raises(ValueError, match="coded exactly as 0/1"):
        fit_generalized_function_on_scalar_regression(
            bad_binomial,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            basis_size=2,
            spline_degree=1,
        )

    with pytest.raises(ValueError, match="working_correlation"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            basis_size=2,
            spline_degree=1,
            working_correlation="exchangeable",
        )

    with pytest.raises(ValueError, match="covariance_type"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            basis_size=2,
            spline_degree=1,
            covariance_type="naive",
        )

    with pytest.raises(ValueError, match="family must be"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="negative_binomial",
            basis_size=2,
            spline_degree=1,
        )


def test_poisson_rejects_negative_or_fractional_counts():
    trajectories, design, _, _ = _poisson_data(
        seed=515,
        n_participants=12,
    )
    for bad_value in (-1.0, 0.5):
        values = trajectories.values.copy()
        values[0, 0, 0] = bad_value
        bad = TrajectorySet(
            time=trajectories.time,
            values=values,
            curve_ids=trajectories.curve_ids,
            dimension_names=trajectories.dimension_names,
            metadata=trajectories.metadata,
            time_unit=trajectories.time_unit,
        )
        with pytest.raises(ValueError, match="non-negative integer"):
            fit_generalized_function_on_scalar_regression(
                bad,
                design,
                predictors=("condition",),
                participant_column="participant_id",
                dimension="count",
                family="poisson",
                basis_size=2,
                spline_degree=1,
            )


def test_cluster_count_guard_is_explicit():
    trajectories, design, _, _ = _binary_data(
        seed=516,
        n_participants=4,
    )
    with pytest.raises(ValueError, match="participant count to exceed"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            basis_size=2,
            spline_degree=1,
        )


def test_bootstrap_and_band_invalid_contracts_fail_closed():
    trajectories, design, _, _ = _binary_data(
        seed=517,
        n_participants=12,
    )
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="target_aoi",
        family="binomial",
        basis_size=2,
        spline_degree=1,
    )

    with pytest.raises(ValueError, match="at least 100"):
        bootstrap_generalized_function_on_scalar_coefficients(
            fit,
            n_bootstrap=99,
        )
    with pytest.raises(ValueError, match="must be 'raise'"):
        bootstrap_generalized_function_on_scalar_coefficients(
            fit,
            n_bootstrap=100,
            failed_replicate_policy="drop",
        )

    bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=517,
    )
    with pytest.raises(ValueError, match="simultaneous_scope"):
        generalized_function_on_scalar_simultaneous_bands(
            bootstrap,
            simultaneous_scope="pointwise",
        )
