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
    generalized_function_on_scalar_exposure_frame,
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


def _poisson_exposure_data(seed=530, n_participants=40):
    rng = np.random.default_rng(seed)
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 7)
    condition_template = np.array([-0.5, 0.0, 0.5])
    condition = np.tile(condition_template, n_participants)
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )

    beta0 = 0.10 + 0.20 * time
    beta1 = 0.35 - 0.10 * time
    eta_rate = beta0[None, :] + condition[:, None] * beta1[None, :]
    curve_scale = 0.75 + 0.50 * (
        np.arange(condition.size, dtype=float) % 5
    ) / 4.0
    exposure = curve_scale[:, None] * (0.80 + 0.40 * time[None, :])
    mean_count = exposure * np.exp(eta_rate)
    response = rng.poisson(mean_count).astype(float)

    trajectories = TrajectorySet(
        time=time,
        values=response[:, :, None],
        curve_ids=tuple(f"E{i:04d}" for i in range(response.shape[0])),
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
    return trajectories, design, exposure, beta0, beta1


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


def test_profile_input_validation_closes_edge_contracts(
    _binary_prediction_bundle,
):
    _, _, fit, _, _, _ = _binary_prediction_bundle

    with pytest.raises(TypeError, match="GeneralizedFunctionOnScalarResult"):
        generalized_function_on_scalar_predict(
            "not-a-fit",
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": (0.0,),
                }
            ),
        )

    with pytest.raises(TypeError, match="pandas DataFrame"):
        generalized_function_on_scalar_predict(
            fit,
            {"profile_id": ["a"], "condition": [0.0]},
        )

    with pytest.raises(ValueError, match="at least one row"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(columns=["profile_id", "condition"]),
        )

    with pytest.raises(TypeError, match="profile_id_column"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": (0.0,),
                }
            ),
            profile_id_column="",
        )

    with pytest.raises(ValueError, match="must not reuse"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame({"condition": (0.0,)}),
            profile_id_column="condition",
        )

    with pytest.raises(ValueError, match="must not be missing"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": (None,),
                    "condition": (0.0,),
                }
            ),
        )

    with pytest.raises(ValueError, match="must be non-empty"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("",),
                    "condition": (0.0,),
                }
            ),
        )

    with pytest.raises(TypeError, match="must be numeric"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": ("bad",),
                }
            ),
        )

    with pytest.raises(ValueError, match="non-finite"):
        generalized_function_on_scalar_predict(
            fit,
            pd.DataFrame(
                {
                    "profile_id": ("a",),
                    "condition": (np.nan,),
                }
            ),
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

    with pytest.raises(ValueError, match="simultaneous_scope"):
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

def test_poisson_exposure_retains_rate_and_expected_count_semantics():
    trajectories, design, exposure, beta0, beta1 = _poisson_exposure_data()
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=exposure,
        exposure_units="seconds",
        basis_size=2,
        spline_degree=1,
    )

    np.testing.assert_allclose(fit.exposure, exposure)
    np.testing.assert_allclose(fit.log_exposure, np.log(exposure))
    np.testing.assert_allclose(
        fit.linear_predictor_count,
        fit.linear_predictor_rate + np.log(exposure),
    )
    np.testing.assert_allclose(
        fit.mean_functions,
        exposure * fit.rate_functions,
        rtol=1e-12,
        atol=1e-12,
    )
    assert fit.exposure_units == "seconds"
    assert fit.exposure_expanded_from_curve is False
    np.testing.assert_allclose(fit.coefficient_functions[0], beta0, atol=0.35)
    np.testing.assert_allclose(fit.coefficient_functions[1], beta1, atol=0.40)

    contract = fit.provenance["generalized_function_on_scalar_regression"]
    assert contract["generic_offset_supported"] is False
    assert contract["poisson_exposure_supported"] is True
    assert contract["exposure_inferred_from_time_grid"] is False
    assert contract["exposure_inferred_from_trial_duration"] is False
    assert contract["exposure_inferred_from_metadata"] is False
    assert contract["exposure_observed_and_fixed"] is True
    assert contract["exposure_measurement_uncertainty"] is False

    audit = generalized_function_on_scalar_exposure_frame(fit)
    assert len(audit) == trajectories.n_curves
    assert np.all(audit["minimum_exposure"] > 0)
    assert audit.attrs["exposure_audit"]["varies_over_time"] is True
    assert audit.attrs["exposure_audit"]["varies_between_curves"] is True
    assert audit.attrs["exposure_audit"]["exposure_units"] == "seconds"


def test_poisson_exposure_validation_and_curve_expansion_fail_closed():
    trajectories, design, exposure, _, _ = _poisson_exposure_data(
        seed=531,
        n_participants=12,
    )

    zero = exposure.copy()
    zero[0, 0] = 0.0
    negative = exposure.copy()
    negative[0, 0] = -1.0
    nonfinite = exposure.copy()
    nonfinite[0, 0] = np.nan
    for bad in (zero, negative, nonfinite):
        with pytest.raises(ValueError, match="exposure"):
            fit_generalized_function_on_scalar_regression(
                trajectories,
                design,
                predictors=("condition",),
                participant_column="participant_id",
                dimension="count",
                family="poisson",
                exposure=bad,
                basis_size=2,
                spline_degree=1,
            )

    with pytest.raises(ValueError, match="shape"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="count",
            family="poisson",
            exposure=np.ones((trajectories.n_curves, 2)),
            basis_size=2,
            spline_degree=1,
        )

    per_curve = np.linspace(0.5, 1.5, trajectories.n_curves)
    expanded = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=per_curve,
        basis_size=2,
        spline_degree=1,
    )
    np.testing.assert_allclose(
        expanded.exposure,
        np.repeat(per_curve[:, None], trajectories.n_time, axis=1),
    )
    assert expanded.exposure_expanded_from_curve is True

    with pytest.raises(ValueError, match="exposure_units"):
        fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="count",
            family="poisson",
            exposure_units="seconds",
            basis_size=2,
            spline_degree=1,
        )

    binary, binary_design, _, _ = _binary_data(seed=532, n_participants=12)
    with pytest.raises(ValueError, match="only for family='poisson'"):
        fit_generalized_function_on_scalar_regression(
            binary,
            binary_design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="target_aoi",
            family="binomial",
            exposure=np.ones((binary.n_curves, binary.n_time)),
            basis_size=2,
            spline_degree=1,
        )


def test_exposure_adjusted_prediction_requires_target_exposure_for_counts():
    trajectories, design, exposure, _, _ = _poisson_exposure_data(
        seed=533,
        n_participants=18,
    )
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=exposure,
        exposure_units="seconds",
        basis_size=2,
        spline_degree=1,
    )
    profiles = pd.DataFrame(
        {"profile_id": ("low", "high"), "condition": (-0.5, 0.5)}
    )

    rate = generalized_function_on_scalar_predict(fit, profiles)
    assert rate.prediction_scale == "rate"
    assert rate.exposure_profiles is None
    assert rate.expected_count_functions is None
    np.testing.assert_allclose(rate.mean_functions, rate.rate_functions)
    np.testing.assert_allclose(
        rate.rate_functions,
        np.exp(rate.linear_predictor_rate),
    )

    with pytest.raises(ValueError, match="requires explicit exposure_profiles"):
        generalized_function_on_scalar_predict(
            fit,
            profiles,
            prediction_scale="expected_count",
        )

    target_exposure = np.array([1.5, 2.0])
    count = generalized_function_on_scalar_predict(
        fit,
        profiles,
        exposure_profiles=target_exposure,
        prediction_scale="expected_count",
    )
    expected_exposure = np.repeat(
        target_exposure[:, None], trajectories.n_time, axis=1
    )
    np.testing.assert_allclose(count.exposure_profiles, expected_exposure)
    np.testing.assert_allclose(
        count.linear_predictor_count,
        count.linear_predictor_rate + np.log(expected_exposure),
    )
    np.testing.assert_allclose(
        count.expected_count_functions,
        expected_exposure * count.rate_functions,
    )
    np.testing.assert_allclose(
        count.mean_functions,
        count.expected_count_functions,
    )

    with pytest.raises(ValueError, match="must be omitted for rate"):
        generalized_function_on_scalar_predict(
            fit,
            profiles,
            exposure_profiles=target_exposure,
            prediction_scale="rate",
        )


def test_exposure_bootstrap_rate_contrasts_and_log_rate_ratio_band():
    trajectories, design, exposure, _, _ = _poisson_exposure_data(
        seed=534,
        n_participants=16,
    )
    fit = fit_generalized_function_on_scalar_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="count",
        family="poisson",
        exposure=exposure,
        basis_size=2,
        spline_degree=1,
    )
    coefficient_bootstrap = bootstrap_generalized_function_on_scalar_coefficients(
        fit,
        n_bootstrap=100,
        random_state=534,
    )
    contract = coefficient_bootstrap.provenance[
        "generalized_function_on_scalar_bootstrap"
    ]
    assert contract["exposure_observed_and_fixed"] is True
    assert contract["exposure_resampled_with_response_bundle"] is True
    assert contract["exposure_measurement_uncertainty"] is False

    profiles = pd.DataFrame(
        {"profile_id": ("low", "high"), "condition": (-0.5, 0.5)}
    )
    rate_bootstrap = bootstrap_generalized_function_on_scalar_predictions(
        coefficient_bootstrap,
        profiles,
        prediction_scale="rate",
    )

    difference = generalized_function_on_scalar_mean_difference_band(
        rate_bootstrap,
        profile_a="high",
        profile_b="low",
        contrast_scale="rate_difference",
    )
    assert difference.contrast_scale == "rate_difference"

    ratio = generalized_function_on_scalar_mean_difference_band(
        rate_bootstrap,
        profile_a="high",
        profile_b="low",
        contrast_scale="rate_ratio",
    )
    assert ratio.contrast_scale == "rate_ratio"
    assert ratio.inference_scale == "log_rate_ratio"
    assert np.all(ratio.estimate > 0)
    assert np.all(ratio.lower > 0)
    assert np.all(ratio.upper > 0)
    np.testing.assert_allclose(
        ratio.estimate,
        (
            rate_bootstrap.prediction.rate_functions[1]
            / rate_bootstrap.prediction.rate_functions[0]
        ),
    )
    assert ratio.provenance[
        "generalized_function_on_scalar_mean_difference_band"
    ]["rate_ratio_band_calibrated_on_log_scale"] is True

    fit_report = generalized_function_on_scalar_reporting_text(fit)
    assert "log rates" in fit_report
    assert "observed and fixed" in fit_report

    rate_band = generalized_function_on_scalar_prediction_bands(
        rate_bootstrap,
        confidence_level=0.95,
    )
    prediction_report = (
        generalized_function_on_scalar_prediction_reporting_text(rate_band)
    )
    assert "exposure-adjusted rate" in prediction_report
    prediction_ax = plot_generalized_function_on_scalar_predictions(rate_band)
    assert "exposure-adjusted rate" in prediction_ax.get_ylabel().lower()

    ratio_report = (
        generalized_function_on_scalar_mean_difference_reporting_text(ratio)
    )
    assert "log-rate-ratio" in ratio_report
    ratio_ax = plot_generalized_function_on_scalar_mean_difference(ratio)
    assert "high - low" in ratio_ax.get_title()
    assert "rate ratio" in ratio_ax.get_ylabel().lower()
    assert ratio_ax.lines[-1].get_ydata()[0] == pytest.approx(1.0)

    count_bootstrap = bootstrap_generalized_function_on_scalar_predictions(
        coefficient_bootstrap,
        profiles,
        exposure_profiles=np.array([1.0, 1.5]),
        prediction_scale="expected_count",
    )
    count_difference = generalized_function_on_scalar_mean_difference_band(
        count_bootstrap,
        profile_a="high",
        profile_b="low",
        contrast_scale="expected_count_difference",
    )
    assert count_difference.contrast_scale == "expected_count_difference"
    assert np.all(np.isfinite(count_difference.estimate))


def test_exposure_audit_rejects_non_exposure_fit():
    trajectories, design, _, _ = _poisson_data(seed=535, n_participants=12)
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
    with pytest.raises(ValueError, match="does not contain an exposure"):
        generalized_function_on_scalar_exposure_frame(fit)

