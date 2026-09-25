import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    bootstrap_functional_mixed_effects_full_refit,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_residual_diagnostics,
    functional_mixed_effects_variance_bootstrap_frame,
    functional_mixed_effects_whitened_residuals,
)
from eyetrajectoriespy.functional_mixed_effects_nested import (
    _block_residual_covariance,
)


def _correlation_matrix(time, family, parameter):
    time = np.asarray(time, dtype=float)
    if family == "exponential":
        distance = np.abs(np.subtract.outer(time, time))
        return np.exp(-distance / float(parameter))
    if family == "ar1":
        order = np.abs(
            np.subtract.outer(
                np.arange(time.size, dtype=int),
                np.arange(time.size, dtype=int),
            )
        )
        return np.power(float(parameter), order)
    if family == "iid":
        return np.eye(time.size, dtype=float)
    raise ValueError(family)


def _serial_data(
    *,
    family,
    parameter,
    time,
    seed=490,
    n_participants=14,
    trials_per_participant=3,
    trial_effect=False,
    random_slope=False,
    residual_sd=0.08,
):
    rng = np.random.default_rng(seed)
    time = np.asarray(time, dtype=float)
    basis = np.column_stack([1.0 - time / time[-1], time / time[-1]])
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )
    trial_ids = np.tile(
        [f"T{j:02d}" for j in range(trials_per_participant)],
        n_participants,
    )
    condition_template = np.linspace(
        -0.75,
        0.75,
        trials_per_participant,
    )
    condition = np.tile(condition_template, n_participants)

    beta0 = 0.25 + 0.12 * (time / time[-1])
    beta1 = 0.16 + 0.25 * (time / time[-1])

    participant_dimension = 4 if random_slope else 2
    if random_slope:
        participant_covariance = np.array(
            [
                [0.025, 0.004, 0.006, 0.001],
                [0.004, 0.020, 0.001, 0.005],
                [0.006, 0.001, 0.015, 0.002],
                [0.001, 0.005, 0.002, 0.013],
            ]
        )
    else:
        participant_covariance = np.array(
            [[0.025, 0.004], [0.004, 0.020]]
        )
    participant_coefficients = rng.multivariate_normal(
        np.zeros(participant_dimension),
        participant_covariance,
        size=n_participants,
    )

    if trial_effect:
        trial_covariance = np.array(
            [[0.014, 0.003], [0.003, 0.011]]
        )
        trial_coefficients = rng.multivariate_normal(
            np.zeros(2),
            trial_covariance,
            size=n_participants * trials_per_participant,
        )
    else:
        trial_coefficients = np.zeros(
            (n_participants * trials_per_participant, 2),
            dtype=float,
        )

    residual_correlation = _correlation_matrix(
        time,
        family,
        parameter,
    )
    residual_covariance = residual_sd**2 * residual_correlation
    residual_chol = np.linalg.cholesky(residual_covariance)

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        intercept_function = (
            participant_coefficients[participant_index, :2] @ basis.T
        )
        slope_function = (
            participant_coefficients[participant_index, 2:] @ basis.T
            if random_slope
            else np.zeros(time.size)
        )
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            trial_function = trial_coefficients[curve_index] @ basis.T
            residual = residual_chol @ rng.normal(size=time.size)
            response = (
                beta0
                + condition[curve_index] * beta1
                + intercept_function
                + condition[curve_index] * slope_function
                + trial_function
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
                "participant_id": participants,
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
    return trajectories, design, beta0, beta1


def _fit_serial(
    trajectories,
    design,
    *,
    residual_correlation,
    trial_effect=False,
    random_slope=False,
    reml=False,
    maxiter=1200,
):
    return fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id" if trial_effect else None,
        trial_random_effect=(
            "functional_intercept" if trial_effect else None
        ),
        random_slope_predictor="condition" if random_slope else None,
        residual_correlation=residual_correlation,
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=reml,
        method="lbfgs",
        maxiter=maxiter,
    )


def test_exponential_irregular_grid_recovers_range_and_whitens():
    time = np.array([0.0, 0.04, 0.13, 0.27, 0.48, 0.73, 1.0])
    true_phi = 0.18
    trajectories, design, beta0, beta1 = _serial_data(
        family="exponential",
        parameter=true_phi,
        time=time,
        seed=491,
        n_participants=18,
        trials_per_participant=3,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="exponential",
    )

    assert fit.residual_correlation == "exponential"
    assert fit.residual_correlation_parameter_name == "phi"
    assert fit.residual_correlation_parameter_unit == "s"
    assert fit.residual_correlation_grid_regular is False
    assert fit.residual_correlation_grid_interval is None
    assert fit.residual_correlation_parameter > 0
    assert 0.35 * true_phi < fit.residual_correlation_parameter < 2.5 * true_phi
    assert fit.residual_correlation_matrix.shape == (time.size, time.size)
    assert fit.residual_correlation_condition_number > 1.0

    np.testing.assert_allclose(
        fit.coefficient_functions[0],
        beta0,
        atol=0.12,
    )
    np.testing.assert_allclose(
        fit.coefficient_functions[1],
        beta1,
        atol=0.12,
    )

    raw = functional_mixed_effects_residual_diagnostics(
        fit,
        max_lag=3,
        residual_scale="raw",
    )
    white = functional_mixed_effects_residual_diagnostics(
        fit,
        max_lag=3,
        residual_scale="whitened",
    )
    raw_lag1 = float(
        raw.overall_diagnostics.loc[
            raw.overall_diagnostics["lag_index"] == 1,
            "autocorrelation",
        ].iloc[0]
    )
    white_lag1 = float(
        white.overall_diagnostics.loc[
            white.overall_diagnostics["lag_index"] == 1,
            "autocorrelation",
        ].iloc[0]
    )
    assert raw_lag1 > 0.20
    assert abs(white_lag1) < abs(raw_lag1)
    assert white.residual_scale == "whitened"

    whitened = functional_mixed_effects_whitened_residuals(fit)
    np.testing.assert_allclose(
        whitened,
        fit.whitened_residual_functions,
    )


@pytest.mark.parametrize(
    ("true_rho", "seed"),
    [(0.62, 492), (-0.55, 493)],
)
def test_ar1_regular_grid_recovers_positive_and_negative_rho(
    true_rho,
    seed,
):
    time = np.linspace(0.0, 1.0, 8)
    trajectories, design, _, _ = _serial_data(
        family="ar1",
        parameter=true_rho,
        time=time,
        seed=seed,
        n_participants=18,
        trials_per_participant=3,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="ar1",
    )

    assert fit.residual_correlation == "ar1"
    assert fit.residual_correlation_parameter_name == "rho"
    assert fit.residual_correlation_parameter_unit == "dimensionless"
    assert fit.residual_correlation_grid_regular is True
    assert fit.residual_correlation_grid_interval == pytest.approx(1.0 / 7.0)
    assert np.sign(fit.residual_correlation_parameter) == np.sign(true_rho)
    assert abs(fit.residual_correlation_parameter - true_rho) < 0.30

    if true_rho < 0:
        assert fit.residual_correlation_matrix[0, 1] < 0
        assert fit.residual_correlation_matrix[0, 2] > 0


def test_ar1_rejects_irregular_grid():
    time = np.array([0.0, 0.05, 0.16, 0.33, 0.58, 1.0])
    trajectories, design, _, _ = _serial_data(
        family="iid",
        parameter=0.0,
        time=time,
        seed=494,
        n_participants=8,
        trials_per_participant=3,
    )
    with pytest.raises(ValueError, match="equally spaced"):
        _fit_serial(
            trajectories,
            design,
            residual_correlation="ar1",
        )


def test_residual_covariance_never_crosses_trial_boundaries():
    correlation = _correlation_matrix(
        np.linspace(0.0, 1.0, 5),
        "ar1",
        0.7,
    )
    covariance = _block_residual_covariance(
        n_curves=3,
        residual_variance=0.04,
        correlation=correlation,
    )
    n_time = correlation.shape[0]

    np.testing.assert_allclose(
        covariance[:n_time, n_time : 2 * n_time],
        0.0,
    )
    np.testing.assert_allclose(
        covariance[n_time : 2 * n_time, 2 * n_time :],
        0.0,
    )
    np.testing.assert_allclose(
        covariance[:n_time, :n_time],
        0.04 * correlation,
    )


def test_exponential_combines_with_random_slope_and_trial_effect():
    time = np.array([0.0, 0.06, 0.15, 0.31, 0.53, 0.76, 1.0])
    trajectories, design, beta0, beta1 = _serial_data(
        family="exponential",
        parameter=0.14,
        time=time,
        seed=495,
        n_participants=14,
        trials_per_participant=4,
        trial_effect=True,
        random_slope=True,
        residual_sd=0.055,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="exponential",
        trial_effect=True,
        random_slope=True,
        maxiter=1600,
    )

    assert fit.random_slope_predictor == "condition"
    assert fit.random_slope_functions is not None
    assert fit.trial_random_effect == "functional_intercept"
    assert fit.trial_random_effect_covariance is not None
    assert fit.residual_correlation == "exponential"
    assert fit.residual_correlation_parameter > 0
    np.testing.assert_allclose(
        fit.coefficient_functions[0],
        beta0,
        atol=0.14,
    )
    np.testing.assert_allclose(
        fit.coefficient_functions[1],
        beta1,
        atol=0.14,
    )

    contract = fit.provenance["functional_mixed_effects_regression"]
    assert contract["participant_trial_cross_covariance"] is False
    assert contract["residual_correlation_crosses_trial_boundaries"] is False
    assert contract["automatic_residual_correlation_selection"] is False
    assert contract["residual_correlation_parameter_estimated_jointly"] is True


def test_iid_truth_exponential_reaches_independence_boundary_or_tiny_range():
    time = np.linspace(0.0, 1.0, 7)
    trajectories, design, _, _ = _serial_data(
        family="iid",
        parameter=0.0,
        time=time,
        seed=496,
        n_participants=18,
        trials_per_participant=4,
        residual_sd=0.07,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="exponential",
    )

    lower = fit.residual_correlation_optimizer_bounds[0]
    assert (
        fit.residual_correlation_boundary_fit
        or fit.residual_correlation_parameter <= 20.0 * lower
        or fit.residual_correlation_parameter < 0.05 * np.diff(time)[0]
    )


def test_fixed_covariance_bootstrap_conditions_on_serial_parameter():
    time = np.linspace(0.0, 1.0, 7)
    trajectories, design, _, _ = _serial_data(
        family="ar1",
        parameter=0.55,
        time=time,
        seed=497,
        n_participants=14,
        trials_per_participant=3,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="ar1",
    )
    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        fit,
        n_bootstrap=100,
        random_state=49,
    )
    contract = bootstrap.provenance["functional_mixed_effects_bootstrap"]

    assert contract["residual_correlation_conditioned_on_reference"] is True
    assert contract["reference_residual_correlation"] == "ar1"
    assert contract["reference_residual_correlation_parameter"] == pytest.approx(
        fit.residual_correlation_parameter
    )


def test_full_refit_bootstrap_reestimates_exponential_parameter_and_covariances():
    time = np.array([0.0, 0.10, 0.25, 0.48, 0.72, 1.0])
    trajectories, design, _, _ = _serial_data(
        family="exponential",
        parameter=0.16,
        time=time,
        seed=498,
        n_participants=7,
        trials_per_participant=2,
        trial_effect=True,
        residual_sd=0.05,
    )
    fit = _fit_serial(
        trajectories,
        design,
        residual_correlation="exponential",
        trial_effect=True,
        maxiter=900,
    )
    bootstrap = bootstrap_functional_mixed_effects_full_refit(
        fit,
        n_bootstrap=20,
        random_state=490,
    )

    assert bootstrap.residual_correlation_parameters.shape == (20,)
    assert bootstrap.residual_correlation_boundary_flags.shape == (20,)
    assert bootstrap.residual_correlation_condition_numbers.shape == (20,)
    assert np.all(np.isfinite(bootstrap.residual_correlation_parameters))
    assert np.all(bootstrap.residual_correlation_parameters > 0)
    assert bootstrap.trial_random_effect_covariances.shape == (20, 2, 2)
    assert bootstrap.random_effect_covariances.shape == (20, 2, 2)
    assert bootstrap.residual_variances.shape == (20,)

    frame = functional_mixed_effects_variance_bootstrap_frame(bootstrap)
    assert "residual_correlation_parameter" in frame.columns
    assert "residual_correlation_condition_number" in frame.columns
    assert "residual_correlation_boundary_fit" in frame.columns

    contract = bootstrap.provenance[
        "functional_mixed_effects_full_refit_bootstrap"
    ]
    assert contract["residual_correlation_refit"] is True
    assert contract["residual_correlation_family_reselected"] is False
    assert contract["reference_residual_correlation"] == "exponential"
