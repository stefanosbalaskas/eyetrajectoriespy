import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    GeneralizedFunctionOnScalarBandResult,
    GeneralizedFunctionOnScalarBootstrapResult,
    GeneralizedFunctionOnScalarMeanDifferenceResult,
    GeneralizedFunctionOnScalarPredictionBandResult,
    GeneralizedFunctionOnScalarPredictionBootstrapResult,
    GeneralizedFunctionOnScalarPredictionResult,
    GeneralizedFunctionOnScalarResult,
    TrajectorySet,
    bootstrap_generalized_function_on_scalar_coefficients,
    bootstrap_generalized_function_on_scalar_predictions,
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_coefficient_frame,
    generalized_function_on_scalar_mean_difference_band,
    generalized_function_on_scalar_mean_difference_frame,
    generalized_function_on_scalar_mean_difference_reporting_text,
    generalized_function_on_scalar_predict,
    generalized_function_on_scalar_prediction_bands,
    generalized_function_on_scalar_prediction_frame,
    generalized_function_on_scalar_prediction_reporting_text,
    generalized_function_on_scalar_reporting_text,
    generalized_function_on_scalar_simultaneous_bands,
    plot_generalized_function_on_scalar_coefficients,
    plot_generalized_function_on_scalar_mean_difference,
    plot_generalized_function_on_scalar_predictions,
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

@pytest.fixture(scope="module")
def _binary_prediction_bundle():
    trajectories, design, _, _ = _binary_data(
        seed=520,
        n_participants=18,
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
    coefficient_bootstrap = (
        bootstrap_generalized_function_on_scalar_coefficients(
            fit,
            n_bootstrap=100,
            random_state=520,
        )
    )
    profiles = pd.DataFrame(
        {
            "profile_id": ("low", "high", "extrapolated"),
            "condition": (-0.7, 0.7, 1.5),
        }
    )
    prediction_bootstrap = (
        bootstrap_generalized_function_on_scalar_predictions(
            coefficient_bootstrap,
            profiles,
        )
    )
    return (
        trajectories,
        design,
        fit,
        coefficient_bootstrap,
        profiles,
        prediction_bootstrap,
    )


def test_fixed_profile_prediction_matches_fitted_mean_for_observed_profile(
    _binary_prediction_bundle,
):
    trajectories, design, fit, _, profiles, prediction_bootstrap = (
        _binary_prediction_bundle
    )
    prediction = prediction_bootstrap.prediction

    assert isinstance(
        prediction,
        GeneralizedFunctionOnScalarPredictionResult,
    )
    assert prediction.profile_ids == (
        "low",
        "high",
        "extrapolated",
    )
    assert prediction.n_profiles == 3
    assert prediction.extrapolation_flags.tolist() == [
        False,
        False,
        True,
    ]

    low_curve = int(
        np.flatnonzero(
            design["condition"].to_numpy(dtype=float) == -0.7
        )[0]
    )
    np.testing.assert_allclose(
        prediction.linear_predictor_functions[0],
        fit.linear_predictor_functions[low_curve],
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        prediction.mean_functions[0],
        fit.mean_functions[low_curve],
        rtol=1e-12,
        atol=1e-12,
    )
    assert np.all(
        (prediction.mean_functions > 0.0)
        & (prediction.mean_functions < 1.0)
    )
    assert np.all(
        prediction.linear_predictor_standard_errors >= 0.0
    )
    assert np.all(prediction.mean_standard_errors >= 0.0)

    contract = prediction.provenance[
        "generalized_function_on_scalar_prediction"
    ]
    assert contract["profile_values_fixed"] is True
    assert contract["profile_values_resampled"] is False
    assert contract["extrapolated_profiles_retained"] is True
    assert contract["automatic_profile_selection"] is False


def test_profile_prediction_bootstrap_reuses_participant_draws(
    _binary_prediction_bundle,
):
    _, _, _, coefficient_bootstrap, _, prediction_bootstrap = (
        _binary_prediction_bundle
    )

    assert isinstance(
        prediction_bootstrap,
        GeneralizedFunctionOnScalarPredictionBootstrapResult,
    )
    assert prediction_bootstrap.n_bootstrap == 100
    assert (
        prediction_bootstrap.coefficient_bootstrap
        is coefficient_bootstrap
    )
    assert prediction_bootstrap.bootstrap_linear_predictor_functions.shape == (
        100,
        3,
        prediction_bootstrap.prediction.reference.time.size,
    )
    assert prediction_bootstrap.bootstrap_mean_functions.shape == (
        100,
        3,
        prediction_bootstrap.prediction.reference.time.size,
    )

    contract = prediction_bootstrap.provenance[
        "generalized_function_on_scalar_prediction_bootstrap"
    ]
    assert contract[
        "same_participant_draws_as_coefficient_bootstrap"
    ] is True
    assert contract["profile_values_fixed_across_bootstrap"] is True


def test_prediction_bands_transform_to_valid_probability_scale(
    _binary_prediction_bundle,
):
    _, _, _, _, _, prediction_bootstrap = _binary_prediction_bundle

    profile_band = generalized_function_on_scalar_prediction_bands(
        prediction_bootstrap,
        confidence_level=0.95,
        simultaneous_scope="profile",
    )
    family_band = generalized_function_on_scalar_prediction_bands(
        prediction_bootstrap,
        confidence_level=0.95,
        simultaneous_scope="family",
    )

    assert isinstance(
        profile_band,
        GeneralizedFunctionOnScalarPredictionBandResult,
    )
    assert np.all(
        profile_band.linear_lower
        <= profile_band.prediction.linear_predictor_functions
    )
    assert np.all(
        profile_band.prediction.linear_predictor_functions
        <= profile_band.linear_upper
    )
    assert np.all(
        (profile_band.mean_lower > 0.0)
        & (profile_band.mean_upper < 1.0)
    )
    assert np.all(
        profile_band.mean_lower
        <= profile_band.prediction.mean_functions
    )
    assert np.all(
        profile_band.prediction.mean_functions
        <= profile_band.mean_upper
    )
    np.testing.assert_allclose(
        family_band.critical_values,
        family_band.critical_values[0],
    )

    contract = profile_band.provenance[
        "generalized_function_on_scalar_prediction_band"
    ]
    assert contract["calibration_scale"] == "linear_predictor"
    assert contract[
        "mean_band_transformation"
    ] == "strictly_monotone_inverse_link_endpoints"
    assert contract["between_grid_coverage_claim"] is False


def test_response_scale_mean_difference_uses_paired_profile_bootstrap(
    _binary_prediction_bundle,
):
    _, _, _, _, _, prediction_bootstrap = _binary_prediction_bundle

    contrast = generalized_function_on_scalar_mean_difference_band(
        prediction_bootstrap,
        profile_a="high",
        profile_b="low",
        confidence_level=0.95,
    )

    assert isinstance(
        contrast,
        GeneralizedFunctionOnScalarMeanDifferenceResult,
    )
    np.testing.assert_allclose(
        contrast.estimate,
        (
            prediction_bootstrap.prediction.mean_functions[1]
            - prediction_bootstrap.prediction.mean_functions[0]
        ),
    )
    np.testing.assert_allclose(
        contrast.bootstrap_estimates,
        (
            prediction_bootstrap.bootstrap_mean_functions[:, 1, :]
            - prediction_bootstrap.bootstrap_mean_functions[:, 0, :]
        ),
    )
    assert np.all(contrast.standard_error > 0)
    assert np.all(contrast.lower <= contrast.estimate)
    assert np.all(contrast.estimate <= contrast.upper)
    assert contrast.physical_lower_bound == -1.0
    assert contrast.physical_upper_bound == 1.0
    assert contrast.provenance[
        "generalized_function_on_scalar_mean_difference_band"
    ]["multiple_contrast_family_adjustment"] is False


def test_prediction_frames_plots_and_reporting(
    _binary_prediction_bundle,
):
    _, _, _, _, _, prediction_bootstrap = _binary_prediction_bundle
    band = generalized_function_on_scalar_prediction_bands(
        prediction_bootstrap
    )
    contrast = generalized_function_on_scalar_mean_difference_band(
        prediction_bootstrap,
        profile_a="high",
        profile_b="low",
    )

    prediction_frame = generalized_function_on_scalar_prediction_frame(
        band
    )
    contrast_frame = generalized_function_on_scalar_mean_difference_frame(
        contrast
    )
    assert set(
        (
            "profile_id",
            "time",
            "linear_predictor",
            "mean",
            "mean_lower",
            "mean_upper",
            "extrapolation",
        )
    ) <= set(prediction_frame.columns)
    assert len(prediction_frame) == (
        band.n_profiles * band.prediction.reference.time.size
    )
    assert len(contrast_frame) == (
        contrast.prediction_bootstrap.prediction.reference.time.size
    )

    ax_prediction = plot_generalized_function_on_scalar_predictions(
        band
    )
    ax_contrast = plot_generalized_function_on_scalar_mean_difference(
        contrast
    )
    assert "fixed-profile" in ax_prediction.get_title()
    assert "high - low" in ax_contrast.get_title()

    prediction_text = (
        generalized_function_on_scalar_prediction_reporting_text(
            band
        )
    )
    contrast_text = (
        generalized_function_on_scalar_mean_difference_reporting_text(
            contrast
        )
    )
    assert "fixed scientific targets" in prediction_text
    assert "extrapolations" in prediction_text
    assert "predeclared" in contrast_text
    assert "no multiple-contrast family adjustment" in contrast_text


def test_poisson_profile_prediction_is_positive_and_transform_exact():
    trajectories, design, _, _ = _poisson_data(
        seed=521,
        n_participants=18,
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
    profiles = pd.DataFrame(
        {
            "profile_id": ("low", "high"),
            "condition": (-0.5, 0.5),
        }
    )
    prediction = generalized_function_on_scalar_predict(
        fit,
        profiles,
    )

    assert np.all(prediction.mean_functions > 0.0)
    np.testing.assert_allclose(
        prediction.mean_functions,
        np.exp(prediction.linear_predictor_functions),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        prediction.mean_standard_errors,
        (
            prediction.mean_functions
            * prediction.linear_predictor_standard_errors
        ),
        rtol=1e-12,
        atol=1e-12,
    )


def test_profile_contracts_fail_closed(_binary_prediction_bundle):
    _, _, fit, coefficient_bootstrap, _, prediction_bootstrap = (
        _binary_prediction_bundle
    )

    with pytest.raises(ValueError, match="exactly the profile id"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": (0.0,),
                    "extra": (1.0,),
                }
            ),
        )

    with pytest.raises(ValueError, match="identifiers must be unique"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a", "a"),
                    "condition": (-0.5, 0.5),
                }
            ),
        )

    with pytest.raises(ValueError, match="profile.*family"):
        generalized_function_on_scalar_prediction_bands(
            prediction_bootstrap,
            simultaneous_scope="bad",
        )

    with pytest.raises(ValueError, match="must be different"):
        generalized_function_on_scalar_mean_difference_band(
            prediction_bootstrap,
            profile_a="low",
            profile_b="low",
        )

    with pytest.raises(KeyError, match="Unknown profile"):
        generalized_function_on_scalar_mean_difference_band(
            prediction_bootstrap,
            profile_a="high",
            profile_b="missing",
        )

    with pytest.raises(TypeError):
        bootstrap_generalized_function_on_scalar_predictions(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": (0.0,),
                }
            ),
        )

