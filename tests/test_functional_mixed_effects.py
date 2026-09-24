import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionalMixedEffectsResult,
    TrajectorySet,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_coefficient_frame,
    functional_mixed_effects_reporting_text,
    plot_functional_mixed_effects_coefficient,
)


def _repeated_functional_data(seed=2026):
    rng = np.random.default_rng(seed)
    n_participants = 12
    trials_per_participant = 3
    time = np.linspace(0.0, 1.0, 9)
    n_time = time.size

    participants = np.repeat(
        [f"P{i:02d}" for i in range(n_participants)],
        trials_per_participant,
    )
    condition = np.tile(
        np.array([0.0, 1.0, 0.5]),
        n_participants,
    )

    # With two degree-1 B-spline functions, these coefficient functions are
    # represented exactly by the fitted fixed-effect basis.
    intercept = 0.20 + 0.15 * time
    condition_effect = 0.15 + 0.40 * time

    # Participant functional random intercepts have a full-rank covariance
    # in the same two-function linear B-spline basis.
    covariance = np.array(
        [
            [0.030, 0.004],
            [0.004, 0.020],
        ]
    )
    random_basis_coefficients = rng.multivariate_normal(
        np.zeros(2),
        covariance,
        size=n_participants,
    )
    linear_basis = np.column_stack([1.0 - time, time])

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        random_function = (
            random_basis_coefficients[participant_index] @ linear_basis.T
        )
        for trial_index in range(trials_per_participant):
            curve_index = (
                participant_index * trials_per_participant + trial_index
            )
            curve_ids.append(f"C{curve_index:03d}")
            response = (
                intercept
                + condition[curve_index] * condition_effect
                + random_function
                + rng.normal(0.0, 0.04, size=n_time)
            )
            values.append(response[:, None])

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
    return trajectories, design, intercept, condition_effect


def test_joint_functional_mixed_effects_recovers_trial_varying_condition():
    trajectories, design, intercept, condition_effect = (
        _repeated_functional_data()
    )

    result = fit_functional_mixed_effects_regression(
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

    assert isinstance(result, FunctionalMixedEffectsResult)
    assert result.converged is True
    assert result.n_participants == 12
    assert result.n_curves == 36
    assert result.coefficient_names == ("Intercept", "condition")
    assert result.curves_per_participant == tuple([3] * 12)
    assert result.fixed_basis.shape == (trajectories.n_time, 2)
    assert result.random_basis.shape == (trajectories.n_time, 2)
    assert result.random_effect_functions.shape == (12, trajectories.n_time)
    assert result.fitted_functions.shape == (36, trajectories.n_time)
    assert result.residual_functions.shape == (36, trajectories.n_time)
    assert result.random_effect_covariance.shape == (2, 2)
    assert result.residual_variance > 0

    # The within-participant condition changes on every participant, which is
    # precisely the design that 0.35 participant aggregation refused.
    for participant_id in result.participant_ids:
        idx = (
            trajectories.metadata["participant_id"].astype(str).to_numpy()
            == participant_id
        )
        assert np.unique(design.loc[idx, "condition"]).size == 3

    np.testing.assert_allclose(
        result.coefficient_functions[0],
        intercept,
        atol=0.12,
    )
    np.testing.assert_allclose(
        result.coefficient_functions[1],
        condition_effect,
        atol=0.08,
    )

    contract = result.provenance["functional_mixed_effects_regression"]
    assert contract["joint_fit_over_all_time_points"] is True
    assert contract["pointwise_mixed_models"] is False
    assert contract["trial_varying_predictors_supported"] is True
    assert contract["residual_structure"] == (
        "conditionally_iid_gaussian_grid_errors"
    )


def test_functional_mixed_effects_frame_plot_and_reporting():
    trajectories, design, _, _ = _repeated_functional_data(seed=14)
    result = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
    )

    frame = functional_mixed_effects_coefficient_frame(result)
    assert set(
        [
            "coefficient",
            "time",
            "dimension",
            "estimate",
            "standard_error",
            "lower_95_wald",
            "upper_95_wald",
        ]
    ) <= set(frame.columns)
    assert len(frame) == result.n_coefficients * trajectories.n_time
    assert np.all(frame["lower_95_wald"] <= frame["estimate"])
    assert np.all(frame["estimate"] <= frame["upper_95_wald"])

    ax = plot_functional_mixed_effects_coefficient(
        result,
        coefficient="condition",
    )
    assert "condition" in ax.get_title()
    assert len(ax.collections) == 1

    text = functional_mixed_effects_reporting_text(result)
    assert "Gaussian functional mixed-effects regression" in text
    assert "jointly" in text
    assert "conditionally iid Gaussian" in text
    assert "pointwise Wald intervals" in text


def test_functional_mixed_effects_contracts_fail_closed():
    trajectories, design, _, _ = _repeated_functional_data()

    rank_deficient = design.copy()
    rank_deficient["duplicate"] = rank_deficient["condition"]
    with pytest.raises(ValueError, match="rank deficient"):
        fit_functional_mixed_effects_regression(
            trajectories,
            rank_deficient,
            predictors=("condition", "duplicate"),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
        )

    with pytest.raises(KeyError, match="Unknown trajectory dimension"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="missing",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
        )

    with pytest.raises(ValueError, match="metadata does not contain"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="missing",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
        )

    with pytest.raises(ValueError, match="n_basis must be at least"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=1,
            random_basis_size=2,
            spline_degree=1,
        )

    with pytest.raises(ValueError, match="maxiter must be positive"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
            maxiter=0,
        )


def test_functional_mixed_effects_rejects_too_few_participants():
    trajectories, design, _, _ = _repeated_functional_data()
    keep = np.arange(9)
    subset = trajectories.subset(keep)
    subset_design = design.iloc[keep].reset_index(drop=True)
    subset_design["curve_id"] = subset.curve_ids

    with pytest.raises(ValueError, match="at least max"):
        fit_functional_mixed_effects_regression(
            subset,
            subset_design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            spline_degree=1,
        )


def test_functional_mixed_effects_helpers_validate_result_type():
    with pytest.raises(TypeError, match="FunctionalMixedEffectsResult"):
        functional_mixed_effects_coefficient_frame(object())
    with pytest.raises(TypeError, match="FunctionalMixedEffectsResult"):
        plot_functional_mixed_effects_coefficient(
            object(),
            coefficient="condition",
        )
    with pytest.raises(TypeError, match="FunctionalMixedEffectsResult"):
        functional_mixed_effects_reporting_text(object())
