import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_functional_mixed_effects_coefficients,
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_reporting_text,
    functional_mixed_effects_simultaneous_bands,
    functional_random_effect_frame,
    plot_functional_random_effects,
)


def _random_slope_data(
    *,
    seed=45,
    n_participants=32,
    zero_slope=False,
):
    rng = np.random.default_rng(seed)
    trials_per_participant = 4
    time = np.linspace(0.0, 1.0, 9)
    basis = np.column_stack([1.0 - time, time])
    condition_template = np.array([-0.75, -0.25, 0.25, 0.75])
    condition = np.tile(condition_template, n_participants)
    participants = np.repeat(
        [f"P{i:03d}" for i in range(n_participants)],
        trials_per_participant,
    )

    beta0 = 0.25 + 0.12 * time
    beta1 = 0.18 + 0.30 * time

    if zero_slope:
        intercept_covariance = np.array(
            [[0.030, 0.004], [0.004, 0.022]]
        )
        intercept_coefficients = rng.multivariate_normal(
            np.zeros(2),
            intercept_covariance,
            size=n_participants,
        )
        slope_coefficients = np.zeros((n_participants, 2))
    else:
        covariance = np.array(
            [
                [0.030, 0.004, 0.010, 0.002],
                [0.004, 0.022, 0.002, 0.008],
                [0.010, 0.002, 0.022, 0.003],
                [0.002, 0.008, 0.003, 0.017],
            ]
        )
        coefficients = rng.multivariate_normal(
            np.zeros(4),
            covariance,
            size=n_participants,
        )
        intercept_coefficients = coefficients[:, :2]
        slope_coefficients = coefficients[:, 2:]

    intercept_functions = intercept_coefficients @ basis.T
    slope_functions = slope_coefficients @ basis.T

    values = []
    curve_ids = []
    for participant_index in range(n_participants):
        for trial_index in range(trials_per_participant):
            row = (
                participant_index * trials_per_participant + trial_index
            )
            response = (
                beta0
                + condition[row] * beta1
                + intercept_functions[participant_index]
                + condition[row] * slope_functions[participant_index]
                + rng.normal(0.0, 0.025, size=time.size)
            )
            values.append(response[:, None])
            curve_ids.append(f"C{row:04d}")

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
    return trajectories, design, slope_functions


@pytest.fixture(scope="module")
def heterogeneous_random_slope_fit():
    trajectories, design, true_slope_functions = _random_slope_data()
    fit = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        random_slope_predictor="condition",
        spline_degree=1,
        reml=True,
        method="lbfgs",
        maxiter=1000,
    )
    return fit, true_slope_functions


def test_one_random_functional_slope_retains_full_audit_contract(
    heterogeneous_random_slope_fit,
):
    result, true_slope_functions = heterogeneous_random_slope_fit

    assert result.random_slope_predictor == "condition"
    assert result.random_effect_dimension == 4
    assert result.random_effect_covariance_parameter_count == 10
    assert result.random_effect_complexity_warning is False
    assert result.random_effect_design_matrix.shape == (
        result.n_curves * result.time.size,
        4,
    )
    assert result.random_intercept_basis.shape == (result.time.size, 2)
    assert result.random_slope_basis.shape == (result.time.size, 2)
    assert result.random_intercept_covariance.shape == (2, 2)
    assert result.random_slope_covariance.shape == (2, 2)
    assert result.random_intercept_slope_covariance.shape == (2, 2)
    assert result.random_effect_covariance_eigenvalues.shape == (4,)
    assert np.all(np.isfinite(result.random_effect_covariance_eigenvalues))
    assert result.random_effect_covariance_condition_number > 0
    assert result.random_intercept_functions.shape == (
        result.n_participants,
        result.time.size,
    )
    assert result.random_slope_functions.shape == (
        result.n_participants,
        result.time.size,
    )

    recovery = np.corrcoef(
        result.random_slope_functions.reshape(-1),
        true_slope_functions.reshape(-1),
    )[0, 1]
    assert recovery > 0.55

    # The simulated intercept/slope coefficient covariance is positively
    # associated on both matched basis directions.
    assert np.trace(result.random_intercept_slope_covariance) > 0

    contract = result.provenance["functional_mixed_effects_regression"]
    assert contract["random_slope_predictor"] == "condition"
    assert contract["automatic_random_slope_selection"] is False
    assert contract["random_effect_dimension"] == 4
    assert contract["random_effect_covariance_parameter_count"] == 10
    assert contract["random_basis_covariance"] == "unstructured"


def test_random_slope_frame_plot_and_reporting(
    heterogeneous_random_slope_fit,
):
    result, _ = heterogeneous_random_slope_fit

    frame = functional_random_effect_frame(
        result,
        effect="slope",
    )
    assert len(frame) == result.n_participants * result.time.size
    assert set(frame["effect"]) == {"slope"}
    assert set(frame["random_slope_predictor"]) == {"condition"}
    assert set(frame["participant_id"]) == set(result.participant_ids)

    ax = plot_functional_random_effects(
        result,
        effect="slope",
        max_participants=8,
    )
    assert "condition" in ax.get_title()

    text = functional_mixed_effects_reporting_text(result)
    assert "exactly one functional random slope" in text
    assert "'condition'" in text
    assert "10 free covariance parameters" in text
    assert "random-slope selection" in text


def test_zero_random_slope_truth_is_boundary_or_fail_closed():
    trajectories, design, _ = _random_slope_data(
        seed=451,
        n_participants=36,
        zero_slope=True,
    )
    try:
        result = fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            random_slope_predictor="condition",
            spline_degree=1,
            maxiter=1000,
        )
    except RuntimeError as exc:
        # An exact zero variance component lies on the covariance boundary.
        # If the backend does not converge there, the package must fail closed
        # rather than return a nominally valid heterogeneous-slope fit.
        assert "optimization did not converge" in str(exc)
        return

    slope_scale = float(
        np.max(np.linalg.eigvalsh(result.random_slope_covariance))
    )
    intercept_scale = float(
        np.max(np.linalg.eigvalsh(result.random_intercept_covariance))
    )
    assert slope_scale < 0.20 * intercept_scale
    assert result.random_slope_boundary_fit is True


def test_random_slope_requires_within_participant_predictor_variation():
    trajectories, design, _ = _random_slope_data(
        seed=452,
        n_participants=12,
    )
    participant = trajectories.metadata["participant_id"].to_numpy()
    participant_levels = {
        participant_id: float(index % 2)
        for index, participant_id in enumerate(pd.unique(participant))
    }
    design = design.copy()
    design["condition"] = [
        participant_levels[participant_id]
        for participant_id in participant
    ]

    with pytest.raises(ValueError, match="vary within every participant"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            random_slope_predictor="condition",
            spline_degree=1,
        )


def test_random_slope_covariance_complexity_guard_fails_closed():
    trajectories, design, _ = _random_slope_data(
        seed=453,
        n_participants=10,
    )
    with pytest.raises(ValueError, match="participant count to exceed"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            random_slope_predictor="condition",
            spline_degree=1,
        )


def test_random_slope_must_be_explicit_declared_fixed_predictor():
    trajectories, design, _ = _random_slope_data(
        seed=454,
        n_participants=12,
    )
    design = design.copy()
    design["other"] = np.tile(
        np.array([-1.0, -0.25, 0.25, 1.0]),
        12,
    )

    with pytest.raises(ValueError, match="declared fixed predictors"):
        fit_functional_mixed_effects_regression(
            trajectories,
            design,
            predictors=("condition",),
            participant_column="participant_id",
            dimension="metric",
            fixed_basis_size=2,
            random_basis_size=2,
            random_slope_predictor="other",
            spline_degree=1,
        )


def test_random_slope_none_reproduces_intercept_only_fit():
    trajectories, design, _ = _random_slope_data(
        seed=455,
        n_participants=12,
    )
    base = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        spline_degree=1,
    )
    explicit_none = fit_functional_mixed_effects_regression(
        trajectories,
        design,
        predictors=("condition",),
        participant_column="participant_id",
        dimension="metric",
        fixed_basis_size=2,
        random_basis_size=2,
        random_slope_predictor=None,
        spline_degree=1,
    )

    np.testing.assert_allclose(
        base.coefficient_functions,
        explicit_none.coefficient_functions,
        rtol=1e-10,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        base.random_effect_covariance,
        explicit_none.random_effect_covariance,
        rtol=1e-10,
        atol=1e-12,
    )
    assert base.random_slope_predictor is None
    assert explicit_none.random_slope_functions is None
    assert explicit_none.random_effect_dimension == 2


def test_fixed_covariance_bootstrap_remains_explicit_with_random_slope(
    heterogeneous_random_slope_fit,
):
    result, _ = heterogeneous_random_slope_fit
    bootstrap = bootstrap_functional_mixed_effects_coefficients(
        result,
        n_bootstrap=100,
        random_state=45,
    )
    band = functional_mixed_effects_simultaneous_bands(bootstrap)

    provenance = bootstrap.provenance[
        "functional_mixed_effects_bootstrap"
    ]
    assert provenance["reference_random_slope_predictor"] == "condition"
    assert provenance["reference_random_effect_dimension"] == 4
    assert provenance[
        "random_intercept_slope_covariance_conditioned_on_reference"
    ] is True
    assert provenance["variance_components_refit"] is False
    assert band.provenance[
        "functional_mixed_effects_simultaneous_bands"
    ]["variance_components_refit"] is False
