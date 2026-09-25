from dataclasses import replace

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionalMixedEffectsCovarianceSensitivityResult,
    FunctionalMixedEffectsCovarianceSpecification,
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_covariance_sensitivity,
    functional_mixed_effects_covariance_sensitivity_reporting_text,
    functional_mixed_effects_simultaneous_bands,
    functional_mixed_effects_variance_decomposition,
    plot_covariance_sensitivity_band_widths,
    plot_covariance_sensitivity_coefficients,
    plot_functional_variance_decomposition,
)


def _data(seed=500):
    rng = np.random.default_rng(seed)
    n_participants = 14
    trials_per_participant = 3
    time = np.array([0.0, 0.06, 0.17, 0.34, 0.61, 1.0])
    scaled = time / time[-1]
    basis = np.column_stack([1.0 - scaled, scaled])

    participant_ids = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )
    trial_ids = np.tile(
        [f"T{j:02d}" for j in range(trials_per_participant)],
        n_participants,
    )
    condition = np.tile(
        np.array([-0.6, 0.0, 0.6]),
        n_participants,
    )

    beta0 = 0.24 + 0.10 * scaled
    beta1 = 0.14 + 0.24 * scaled

    participant_covariance = np.array(
        [
            [0.024, 0.004, 0.006, 0.001],
            [0.004, 0.019, 0.001, 0.004],
            [0.006, 0.001, 0.014, 0.002],
            [0.001, 0.004, 0.002, 0.012],
        ]
    )
    participant_coefficients = rng.multivariate_normal(
        np.zeros(4),
        participant_covariance,
        size=n_participants,
    )
    trial_covariance = np.array(
        [[0.010, 0.002], [0.002, 0.008]]
    )
    trial_coefficients = rng.multivariate_normal(
        np.zeros(2),
        trial_covariance,
        size=n_participants * trials_per_participant,
    )

    phi = 0.13
    distance = np.abs(np.subtract.outer(time, time))
    residual_correlation = np.exp(-distance / phi)
    residual_chol = np.linalg.cholesky(
        0.045**2 * residual_correlation
    )

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        intercept = (
            participant_coefficients[participant_index, :2] @ basis.T
        )
        slope = (
            participant_coefficients[participant_index, 2:] @ basis.T
        )
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            trial = trial_coefficients[curve_index] @ basis.T
            residual = residual_chol @ rng.normal(size=time.size)
            response = (
                beta0
                + condition[curve_index] * beta1
                + intercept
                + condition[curve_index] * slope
                + trial
                + residual
            )
            values.append(response[:, None])
            curve_ids.append(f"C{curve_index:04d}")

    trajectories = TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("metric",),
        metadata=pd.DataFrame(
            {
                "participant_id": participant_ids,
                "trial_id": trial_ids,
            }
        ),
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": condition,
        }
    )
    return trajectories, design


def _fit(
    trajectories,
    design,
    *,
    trial=False,
    serial="iid",
):
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id" if trial else None,
        trial_random_effect=(
            "functional_intercept" if trial else None
        ),
        random_slope_predictor="condition",
        residual_correlation=serial,
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=False,
        method="lbfgs",
        maxiter=1400,
    )


@pytest.fixture(scope="module")
def covariance_models():
    trajectories, design = _data()
    fits = {
        "M1": _fit(trajectories, design, trial=False, serial="iid"),
        "M2": _fit(trajectories, design, trial=True, serial="iid"),
        "M3": _fit(
            trajectories,
            design,
            trial=False,
            serial="exponential",
        ),
        "M4": _fit(
            trajectories,
            design,
            trial=True,
            serial="exponential",
        ),
    }
    specifications = (
        FunctionalMixedEffectsCovarianceSpecification(
            name="M1",
            random_slope_predictor="condition",
            trial_random_effect=None,
            residual_correlation="iid",
        ),
        FunctionalMixedEffectsCovarianceSpecification(
            name="M2",
            random_slope_predictor="condition",
            trial_random_effect="functional_intercept",
            residual_correlation="iid",
        ),
        FunctionalMixedEffectsCovarianceSpecification(
            name="M3",
            random_slope_predictor="condition",
            trial_random_effect=None,
            residual_correlation="exponential",
        ),
        FunctionalMixedEffectsCovarianceSpecification(
            name="M4",
            random_slope_predictor="condition",
            trial_random_effect="functional_intercept",
            residual_correlation="exponential",
        ),
        FunctionalMixedEffectsCovarianceSpecification(
            name="M5_failed_ar1",
            random_slope_predictor="condition",
            trial_random_effect="functional_intercept",
            residual_correlation="ar1",
        ),
    )
    return fits, specifications


def _sensitivity(covariance_models, *, bands=None):
    fits, specifications = covariance_models
    return functional_mixed_effects_covariance_sensitivity(
        fits,
        reference="M1",
        max_lag=2,
        specifications=specifications,
        failures={
            "M5_failed_ar1": (
                "AR(1) was predeclared but rejected because the common "
                "time grid is irregular."
            )
        },
        bands=bands,
    )


def test_covariance_sensitivity_retains_declared_order_and_failure(
    covariance_models,
):
    result = _sensitivity(covariance_models)

    assert isinstance(
        result,
        FunctionalMixedEffectsCovarianceSensitivityResult,
    )
    assert result.n_models == 5
    assert result.n_successful == 4
    assert result.n_failed == 1
    assert result.reference_label == "M1"
    assert list(result.model_summary["model"]) == [
        "M1",
        "M2",
        "M3",
        "M4",
        "M5_failed_ar1",
    ]
    failed = result.model_summary.loc[
        result.model_summary["model"] == "M5_failed_ar1"
    ].iloc[0]
    assert failed["status"] == "failed"
    assert failed["converged"] == False
    assert "irregular" in failed["failure_reason"]
    assert np.isnan(failed["aic"])
    assert np.isnan(failed["bic"])

    contract = result.provenance[
        "functional_mixed_effects_covariance_sensitivity"
    ]
    assert contract["automatic_model_fitting"] is False
    assert contract["automatic_model_selection"] is False
    assert contract["automatic_model_ranking"] is False
    assert contract["likelihood_ratio_tests"] is False
    assert contract["failed_models_retained"] is True


def test_information_criteria_are_auditable_and_reference_based(
    covariance_models,
):
    result = _sensitivity(covariance_models)
    summary = result.model_summary.set_index("model")
    reference = summary.loc["M1"]

    assert reference["reml"] == False
    assert reference["n_observations"] == (
        result.fits["M1"].n_curves * result.fits["M1"].time.size
    )
    assert reference["n_parameters"] == (
        reference["n_fixed_parameters"]
        + reference["n_covariance_parameters"]
    )
    assert reference["information_criterion_parameter_count"] == (
        reference["n_parameters"]
    )
    assert reference["aic"] == pytest.approx(
        -2.0 * reference["log_likelihood"]
        + 2.0 * reference["information_criterion_parameter_count"]
    )
    assert reference["bic"] == pytest.approx(
        -2.0 * reference["log_likelihood"]
        + np.log(reference["n_observations"])
        * reference["information_criterion_parameter_count"]
    )
    assert reference["delta_log_likelihood"] == pytest.approx(0.0)
    assert reference["delta_aic"] == pytest.approx(0.0)
    assert reference["delta_bic"] == pytest.approx(0.0)


def test_coefficient_differences_and_variance_decomposition(
    covariance_models,
):
    result = _sensitivity(covariance_models)

    reference_rows = result.coefficient_summary.loc[
        result.coefficient_summary["model"] == "M1"
    ]
    assert np.allclose(
        reference_rows["sup_abs_difference_from_reference"],
        0.0,
    )
    assert np.allclose(
        reference_rows["l2_difference_from_reference"],
        0.0,
    )

    m4_components = set(
        result.variance_decomposition.loc[
            result.variance_decomposition["model"] == "M4",
            "component",
        ]
    )
    assert {
        "participant_intercept_variance",
        "participant_slope_variance",
        "participant_intercept_slope_cross_covariance",
        "trial_variance",
        "residual_variance",
    } <= m4_components

    standalone = functional_mixed_effects_variance_decomposition(
        result.fits["M4"],
        model_label="M4",
    )
    assert set(standalone["component"]) == m4_components


def test_raw_and_whitened_residual_summaries_are_side_by_side(
    covariance_models,
):
    result = _sensitivity(covariance_models)
    diagnostics = result.residual_diagnostics

    assert set(diagnostics["residual_scale"]) == {"raw", "whitened"}
    assert set(diagnostics["model"]) == {"M1", "M2", "M3", "M4"}
    assert diagnostics["n_pairs"].gt(0).all()

    summary = result.model_summary.set_index("model")
    for label in ("M1", "M2", "M3", "M4"):
        assert np.isfinite(
            summary.loc[label, "raw_max_abs_acf_positive_lags"]
        )
        assert np.isfinite(
            summary.loc[label, "whitened_max_abs_acf_positive_lags"]
        )
        assert np.isfinite(
            summary.loc[label, "raw_acf_energy_positive_lags"]
        )
        assert np.isfinite(
            summary.loc[label, "whitened_acf_energy_positive_lags"]
        )


def test_band_width_sensitivity_requires_paired_bootstrap_draws(
    covariance_models,
):
    fits, _ = covariance_models
    bands = {}
    for label in ("M1", "M3"):
        bootstrap = bootstrap_functional_mixed_effects_coefficients(
            fits[label],
            n_bootstrap=100,
            random_state=500,
        )
        bands[label] = functional_mixed_effects_simultaneous_bands(
            bootstrap,
            confidence_level=0.95,
            simultaneous_scope="coefficient",
        )

    result = _sensitivity(covariance_models, bands=bands)
    reference = result.band_width_frame.loc[
        result.band_width_frame["model"] == "M1"
    ]
    assert np.allclose(
        reference["band_width_ratio_to_reference"],
        1.0,
    )
    assert set(result.band_width_frame["model"]) == {"M1", "M3"}

    ax1 = plot_covariance_sensitivity_coefficients(
        result,
        coefficient="condition",
    )
    ax2 = plot_covariance_sensitivity_band_widths(
        result,
        coefficient="condition",
    )
    ax3 = plot_functional_variance_decomposition(
        result,
        model="M4",
    )
    assert "condition" in ax1.get_title()
    assert "condition" in ax2.get_title()
    assert "M4" in ax3.get_title()


def test_comparability_contract_refuses_non_covariance_changes(
    covariance_models,
):
    fits, _ = covariance_models
    altered_reml = replace(fits["M2"], reml=True)
    with pytest.raises(ValueError, match="ML-versus-REML"):
        functional_mixed_effects_covariance_sensitivity(
            {"M1": fits["M1"], "M2": altered_reml},
            reference="M1",
            max_lag=2,
        )

    altered_response = replace(
        fits["M2"],
        observed_functions=fits["M2"].observed_functions.copy(),
    )
    altered_response.observed_functions[0, 0] += 0.001
    with pytest.raises(ValueError, match="observed response functions"):
        functional_mixed_effects_covariance_sensitivity(
            {"M1": fits["M1"], "M2": altered_response},
            reference="M1",
            max_lag=2,
        )


def test_failed_models_require_explicit_specifications(
    covariance_models,
):
    fits, _ = covariance_models
    with pytest.raises(ValueError, match="specifications are required"):
        functional_mixed_effects_covariance_sensitivity(
            fits,
            reference="M1",
            max_lag=2,
            failures={"M5": "did not converge"},
        )


def test_reporting_text_states_descriptive_no_selection(
    covariance_models,
):
    result = _sensitivity(covariance_models)
    text = functional_mixed_effects_covariance_sensitivity_reporting_text(
        result
    )

    assert "predeclared sensitivity analysis" in text
    assert "No covariance structure was ranked or automatically selected" in text
    assert "no likelihood-ratio p-values" in text
    assert "failed structure(s)" in text
