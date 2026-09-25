import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    bootstrap_functional_mixed_effects_full_refit,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_full_refit_trial_audit_frame,
    functional_mixed_effects_residual_diagnostics,
    functional_trial_random_effect_frame,
    plot_functional_trial_random_effects,
)


def _trial_random_effect_data(
    *,
    seed=480,
    n_participants=12,
    trials_per_participant=3,
    zero_trial_variance=False,
):
    rng = np.random.default_rng(seed)
    time = np.linspace(0.0, 1.0, 7)
    basis = np.column_stack([1.0 - time, time])
    participant_ids = np.repeat(
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

    beta0 = 0.25 + 0.10 * time
    beta1 = 0.18 + 0.28 * time

    participant_covariance = np.array(
        [[0.030, 0.005], [0.005, 0.022]]
    )
    trial_covariance = np.array(
        [[0.022, 0.006], [0.006, 0.017]]
    )
    participant_coefficients = rng.multivariate_normal(
        np.zeros(2),
        participant_covariance,
        size=n_participants,
    )
    true_participant_functions = participant_coefficients @ basis.T
    if zero_trial_variance:
        trial_coefficients = np.zeros(
            (n_participants * trials_per_participant, 2),
            dtype=float,
        )
    else:
        trial_coefficients = rng.multivariate_normal(
            np.zeros(2),
            trial_covariance,
            size=n_participants * trials_per_participant,
        )

    values = []
    curve_ids = []
    true_trial_functions = []
    for participant_index in range(n_participants):
        participant_function = true_participant_functions[
            participant_index
        ]
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            trial_function = trial_coefficients[curve_index] @ basis.T
            true_trial_functions.append(trial_function)
            response = (
                beta0
                + condition[curve_index] * beta1
                + participant_function
                + trial_function
                + rng.normal(0.0, 0.020, size=time.size)
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
    return (
        trajectories,
        design,
        beta0,
        beta1,
        true_participant_functions,
        np.asarray(true_trial_functions),
    )


@pytest.fixture(scope="module")
def nested_trial_fit():
    (
        trajectories,
        design,
        beta0,
        beta1,
        true_participant_functions,
        true_trial_functions,
    ) = _trial_random_effect_data()
    fit = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        trial_random_effect="functional_intercept",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=1000,
    )
    return (
        fit,
        beta0,
        beta1,
        true_participant_functions,
        true_trial_functions,
    )


def test_trial_functional_random_effect_recovers_hierarchy(nested_trial_fit):
    (
        fit,
        beta0,
        beta1,
        true_participant_functions,
        true_trial_functions,
    ) = nested_trial_fit

    assert fit.trial_random_effect == "functional_intercept"
    assert fit.trial_column == "trial_id"
    assert fit.n_trials == fit.n_curves == 36
    assert fit.trial_random_basis_size == 2
    assert fit.trial_random_effect_covariance.shape == (2, 2)
    assert fit.trial_random_effect_covariance_parameter_count == 3
    assert fit.trial_random_effect_coefficients.shape == (36, 2)
    assert fit.trial_random_effect_functions.shape == (
        36,
        fit.time.size,
    )
    assert len(set(fit.trial_ids)) == fit.n_trials
    assert set(fit.curve_trial_ids) == {"T00", "T01", "T02"}

    np.testing.assert_allclose(
        fit.coefficient_functions[0],
        beta0,
        atol=0.10,
    )
    np.testing.assert_allclose(
        fit.coefficient_functions[1],
        beta1,
        atol=0.10,
    )

    participant_recovery = np.corrcoef(
        fit.random_intercept_functions.reshape(-1),
        true_participant_functions.reshape(-1),
    )[0, 1]
    trial_recovery = np.corrcoef(
        fit.trial_random_effect_functions.reshape(-1),
        true_trial_functions.reshape(-1),
    )[0, 1]
    assert participant_recovery > 0.70
    assert trial_recovery > 0.55

    # Both independently generated hierarchy levels must be recoverable from
    # their own BLUP layer; the trial process is not folded into the retained
    # participant random-intercept functions.
    expanded_participant_truth = np.repeat(
        true_participant_functions,
        3,
        axis=0,
    )
    participant_to_trial_truth = abs(
        np.corrcoef(
            fit.random_intercept_functions.repeat(3, axis=0).reshape(-1),
            true_trial_functions.reshape(-1),
        )[0, 1]
    )
    trial_to_participant_truth = abs(
        np.corrcoef(
            fit.trial_random_effect_functions.reshape(-1),
            expanded_participant_truth.reshape(-1),
        )[0, 1]
    )
    assert participant_to_trial_truth < participant_recovery
    assert trial_to_participant_truth < trial_recovery

    contract = fit.provenance["functional_mixed_effects_regression"]
    assert contract["backend"] == "eyetrajectoriespy.profiled_gaussian_nested"
    assert contract["trial_random_effect_covariance"] == "shared_unstructured"
    assert contract["participant_trial_cross_covariance"] is False
    assert contract["automatic_trial_random_effect_selection"] is False
    assert contract["minimum_trials_per_participant"] == 2


def test_trial_random_effect_frame_plot_and_identity(nested_trial_fit):
    fit, _, _, _, _ = nested_trial_fit
    frame = functional_trial_random_effect_frame(fit)

    assert len(frame) == fit.n_trials * fit.time.size
    assert set(frame["effect"]) == {"trial_functional_intercept"}
    assert set(frame["curve_id"]) == set(fit.source_curve_ids)
    assert set(frame["participant_id"]) == set(fit.participant_ids)
    assert set(frame["source_trial_id"]) == {"T00", "T01", "T02"}

    ax = plot_functional_trial_random_effects(
        fit,
        participant_id=fit.participant_ids[0],
        max_trials=3,
    )
    assert fit.participant_ids[0] in ax.get_title()
    assert ax.get_ylabel() == "Trial functional random intercept"


def test_trial_effect_reduces_smooth_residual_dependence():
    trajectories, design, _, _, _, _ = _trial_random_effect_data(seed=481)

    participant_only = fit_functional_mixed_effects_regression(
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
        maxiter=1000,
    )
    nested = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        trial_random_effect="functional_intercept",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=1000,
    )

    before = functional_mixed_effects_residual_diagnostics(
        participant_only,
        max_lag=3,
    ).overall_diagnostics
    after = functional_mixed_effects_residual_diagnostics(
        nested,
        max_lag=3,
    ).overall_diagnostics

    before_lag1 = float(
        before.loc[before["lag_index"] == 1, "autocorrelation"].iloc[0]
    )
    after_lag1 = float(
        after.loc[after["lag_index"] == 1, "autocorrelation"].iloc[0]
    )
    assert before_lag1 > 0.20
    assert abs(after_lag1) < abs(before_lag1)

    before_positive = before.loc[
        before["lag_index"] > 0,
        "semivariance",
    ].to_numpy(dtype=float)
    after_positive = after.loc[
        after["lag_index"] > 0,
        "semivariance",
    ].to_numpy(dtype=float)
    before_variogram_range = float(np.ptp(before_positive))
    after_variogram_range = float(np.ptp(after_positive))
    assert after_variogram_range < before_variogram_range


def test_zero_trial_variance_is_boundary_or_fails_closed():
    trajectories, design, _, _, _, _ = _trial_random_effect_data(
        seed=482,
        n_participants=10,
        zero_trial_variance=True,
    )
    try:
        fit = fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            trial_random_effect="functional_intercept",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            trial_random_basis_size=2,
            spline_degree=1,
            reml=True,
            method="lbfgs",
            maxiter=1000,
        )
    except RuntimeError as exc:
        assert "optimization did not converge" in str(exc)
        return

    assert fit.trial_random_effect_boundary_fit is True


def test_trial_identifiability_guards_fail_closed():
    trajectories, design, _, _, _, _ = _trial_random_effect_data(
        seed=483,
        n_participants=6,
        trials_per_participant=2,
    )

    duplicate = trajectories.metadata.copy()
    duplicate.loc[
        duplicate["participant_id"] == duplicate["participant_id"].iloc[0],
        "trial_id",
    ] = "same"
    duplicated_trajectories = TrajectorySet(
        time=trajectories.time,
        values=trajectories.values,
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=duplicate.reset_index(drop=True),
        time_unit=trajectories.time_unit,
    )
    with pytest.raises(ValueError, match="unique within participant"):
        fit_functional_mixed_effects_regression(
            duplicated_trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            trial_random_effect="functional_intercept",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            trial_random_basis_size=2,
            spline_degree=1,
        )

    single = trajectories.subset(
        np.arange(0, trajectories.n_curves, 2)
    )
    single_design = design.iloc[
        np.arange(0, trajectories.n_curves, 2)
    ].reset_index(drop=True)
    with pytest.raises(ValueError, match="at least two observed trials"):
        fit_functional_mixed_effects_regression(
            single,
            single_design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            trial_random_effect="functional_intercept",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            trial_random_basis_size=2,
            spline_degree=1,
        )

    small_trajectories, small_design, _, _, _, _ = (
        _trial_random_effect_data(
            seed=4831,
            n_participants=4,
            trials_per_participant=2,
        )
    )
    with pytest.raises(ValueError, match="number of observed nested trials"):
        fit_functional_mixed_effects_regression(
            small_trajectories,
            small_design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            trial_random_effect="functional_intercept",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            trial_random_basis_size=4,
            spline_degree=1,
        )


def test_fixed_covariance_bootstrap_conditions_on_trial_covariance(
    nested_trial_fit,
):
    fit, _, _, _, _ = nested_trial_fit
    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        fit,
        n_bootstrap=100,
        random_state=48,
    )
    contract = bootstrap.provenance["functional_mixed_effects_bootstrap"]
    assert contract[
        "trial_random_effect_covariance_conditioned_on_reference"
    ] is True
    assert contract["reference_trial_random_effect"] == "functional_intercept"
    assert bootstrap.covariance_conditioning.startswith(
        "reference_participant_and_trial"
    )


def test_full_refit_bootstrap_preserves_nested_trial_identity():
    trajectories, design, _, _, _, _ = _trial_random_effect_data(
        seed=484,
        n_participants=6,
        trials_per_participant=2,
    )
    fit = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        trial_random_effect="functional_intercept",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=False,
        method="lbfgs",
        maxiter=600,
    )
    bootstrap = bootstrap_functional_mixed_effects_full_refit(
        fit,
        n_bootstrap=20,
        random_state=480,
    )

    assert bootstrap.trial_random_effect_covariances.shape == (20, 2, 2)
    assert bootstrap.trial_random_effect_covariance_eigenvalues.shape == (
        20,
        2,
    )
    audit = functional_mixed_effects_full_refit_trial_audit_frame(bootstrap)
    assert len(audit) == 20 * fit.n_trials
    assert {
        "source_participant_id",
        "bootstrap_participant_id",
        "source_trial_id",
        "bootstrap_trial_id",
    } <= set(audit.columns)

    duplicate_sources = audit[
        audit.duplicated(
            [
                "bootstrap_replicate",
                "source_participant_id",
                "source_trial_id",
            ],
            keep=False,
        )
    ]
    assert not duplicate_sources.empty
    grouped = duplicate_sources.groupby(
        [
            "bootstrap_replicate",
            "source_participant_id",
            "source_trial_id",
        ]
    )
    assert all(
        group["bootstrap_trial_id"].nunique() == len(group)
        for _, group in grouped
    )
    contract = bootstrap.provenance[
        "functional_mixed_effects_full_refit_bootstrap"
    ]
    assert contract["resampling_unit"] == "participant"
    assert contract["whole_trial_bundles_resampled"] is True
    assert contract["trial_random_effect_covariance_refit"] is True
    assert contract[
        "duplicate_source_trials_receive_distinct_bootstrap_trial_ids"
    ] is True


def test_trial_effect_requires_explicit_contract():
    trajectories, design, _, _, _, _ = _trial_random_effect_data(seed=485)

    with pytest.raises(ValueError, match="trial_column is required"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_random_effect="functional_intercept",
            dimension="metric",
        )

    with pytest.raises(ValueError, match="only used when"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            dimension="metric",
        )

    with pytest.raises(ValueError, match="must be 'functional_intercept'"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            trial_column="trial_id",
            trial_random_effect="automatic",
            dimension="metric",
        )


def test_trial_effect_coexists_with_participant_random_slope():
    rng = np.random.default_rng(486)
    n_participants = 14
    trials_per_participant = 4
    time = np.linspace(0.0, 1.0, 7)
    basis = np.column_stack([1.0 - time, time])
    condition_template = np.array([-0.75, -0.25, 0.25, 0.75])
    condition = np.tile(condition_template, n_participants)
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )
    trials = np.tile(
        [f"T{j:02d}" for j in range(trials_per_participant)],
        n_participants,
    )

    beta0 = 0.20 + 0.12 * time
    beta1 = 0.16 + 0.24 * time
    participant_covariance = np.array(
        [
            [0.030, 0.004, 0.009, 0.002],
            [0.004, 0.022, 0.002, 0.007],
            [0.009, 0.002, 0.020, 0.003],
            [0.002, 0.007, 0.003, 0.016],
        ]
    )
    trial_covariance = np.array(
        [[0.016, 0.004], [0.004, 0.013]]
    )
    participant_coefficients = rng.multivariate_normal(
        np.zeros(4),
        participant_covariance,
        size=n_participants,
    )
    trial_coefficients = rng.multivariate_normal(
        np.zeros(2),
        trial_covariance,
        size=n_participants * trials_per_participant,
    )
    true_slope_functions = participant_coefficients[:, 2:] @ basis.T
    true_trial_functions = trial_coefficients @ basis.T

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        intercept_function = (
            participant_coefficients[participant_index, :2] @ basis.T
        )
        slope_function = true_slope_functions[participant_index]
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            response = (
                beta0
                + condition[curve_index] * beta1
                + intercept_function
                + condition[curve_index] * slope_function
                + true_trial_functions[curve_index]
                + rng.normal(0.0, 0.018, size=time.size)
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
                "trial_id": trials,
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
    fit = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        trial_column="trial_id",
        random_slope_predictor="condition",
        trial_random_effect="functional_intercept",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        trial_random_basis_size=2,
        spline_degree=1,
        reml=False,
        method="lbfgs",
        maxiter=1200,
    )

    assert fit.random_slope_predictor == "condition"
    assert fit.random_effect_dimension == 4
    assert fit.random_slope_functions is not None
    assert fit.random_slope_covariance is not None
    assert fit.random_intercept_slope_covariance is not None
    assert fit.trial_random_effect_functions is not None
    assert fit.trial_random_effect_covariance.shape == (2, 2)

    slope_recovery = np.corrcoef(
        fit.random_slope_functions.reshape(-1),
        true_slope_functions.reshape(-1),
    )[0, 1]
    trial_recovery = np.corrcoef(
        fit.trial_random_effect_functions.reshape(-1),
        true_trial_functions.reshape(-1),
    )[0, 1]
    assert slope_recovery > 0.45
    assert trial_recovery > 0.45

    contract = fit.provenance["functional_mixed_effects_regression"]
    assert contract["random_slope_requires_within_participant_variation"] is True
    assert contract["participant_random_effect_covariance"] == "unstructured"
    assert contract["trial_random_effect_covariance"] == "shared_unstructured"
