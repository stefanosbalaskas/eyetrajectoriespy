import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FunctionOnScalarBandResult,
    FunctionOnScalarBootstrapResult,
    FunctionOnScalarResult,
    TrajectorySet,
    bootstrap_function_on_scalar_coefficients,
    fit_function_on_scalar_regression,
    function_on_scalar_coefficient_frame,
    function_on_scalar_reporting_text,
    function_on_scalar_simultaneous_bands,
    plot_function_on_scalar_coefficients,
)


def _independent_data(noise_scale=0.02):
    rng = np.random.default_rng(42)
    n = 24
    time = np.linspace(0.0, 1.0, 31)
    x = np.linspace(-1.0, 1.0, n)
    beta0 = np.sin(np.pi * time)
    beta1 = 0.5 + time
    noise = rng.normal(0.0, noise_scale, size=(n, time.size))
    y = beta0[None, :] + x[:, None] * beta1[None, :] + noise
    values = np.stack([y, 2.0 * y], axis=2)
    trajectories = TrajectorySet(
        time=time,
        values=values,
        curve_ids=tuple(f"C{i:02d}" for i in range(n)),
        dimension_names=("signal", "double"),
        coordinate_system="unknown",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": x,
        }
    )
    return trajectories, design, beta0, beta1


def test_function_on_scalar_recovers_known_coefficient_curves():
    trajectories, design, beta0, beta1 = _independent_data(noise_scale=0.0)

    result = fit_function_on_scalar_regression(
        trajectories,
        design,
        ("condition",),
        dimensions=("signal",),
    )

    assert isinstance(result, FunctionOnScalarResult)
    assert result.coefficient_names == ("Intercept", "condition")
    assert result.predictor_names == ("condition",)
    assert result.n_units == trajectories.n_curves
    assert result.design_rank == 2
    assert result.residual_degrees_of_freedom == trajectories.n_curves - 2
    np.testing.assert_allclose(result.coefficients[0, :, 0], beta0, atol=1e-12)
    np.testing.assert_allclose(result.coefficients[1, :, 0], beta1, atol=1e-12)
    np.testing.assert_allclose(result.fitted_functions, result.observed_functions)
    assert result.provenance["function_on_scalar_regression"]["smoothing"] is False
    assert (
        result.provenance["function_on_scalar_regression"][
            "functional_mixed_effects_model"
        ]
        is False
    )


def test_function_on_scalar_wild_bootstrap_and_bands_are_seeded():
    trajectories, design, _, _ = _independent_data()
    result = fit_function_on_scalar_regression(
        trajectories,
        design,
        ("condition",),
        dimensions=("signal",),
    )

    first = bootstrap_function_on_scalar_coefficients(
        result,
        n_bootstrap=120,
        multiplier="rademacher",
        random_state=7,
    )
    second = bootstrap_function_on_scalar_coefficients(
        result,
        n_bootstrap=120,
        multiplier="rademacher",
        random_state=7,
    )

    assert isinstance(first, FunctionOnScalarBootstrapResult)
    assert first.n_bootstrap == 120
    np.testing.assert_allclose(
        first.bootstrap_coefficients,
        second.bootstrap_coefficients,
    )
    np.testing.assert_allclose(first.multipliers, second.multipliers)

    band = function_on_scalar_simultaneous_bands(
        first,
        confidence_level=0.95,
        simultaneous_scope="coefficient",
    )
    family = function_on_scalar_simultaneous_bands(
        first,
        confidence_level=0.95,
        simultaneous_scope="family",
    )

    assert isinstance(band, FunctionOnScalarBandResult)
    assert band.lower.shape == result.coefficients.shape
    assert band.upper.shape == result.coefficients.shape
    assert band.critical_values.shape == (result.n_coefficients,)
    assert np.all(band.lower <= result.coefficients)
    assert np.all(result.coefficients <= band.upper)
    assert family.critical_values.shape == (result.n_coefficients,)
    np.testing.assert_allclose(
        family.critical_values,
        family.critical_values[0],
    )
    assert np.all(family.critical_values >= 0)


def test_participant_unit_aggregates_equal_weight_participant_means():
    time = np.linspace(0.0, 1.0, 11)
    participants = ("P1", "P1", "P2", "P2", "P2", "P3", "P3", "P4", "P4")
    condition_by_participant = {"P1": 0.0, "P2": 0.0, "P3": 1.0, "P4": 1.0}
    values = []
    condition = []
    for row, participant in enumerate(participants):
        x = condition_by_participant[participant]
        condition.append(x)
        values.append((1.0 + 2.0 * x + 0.01 * row + time)[:, None])
    trajectories = TrajectorySet(
        time=time,
        values=np.asarray(values),
        curve_ids=tuple(f"T{i}" for i in range(len(values))),
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

    result = fit_function_on_scalar_regression(
        trajectories,
        design,
        ("condition",),
        unit="participant",
        participant_column="participant_id",
    )

    assert result.unit == "participant"
    assert result.unit_ids == ("P1", "P2", "P3", "P4")
    assert result.curves_per_unit == (2, 3, 2, 2)
    assert result.observed_functions.shape[0] == 4
    assert result.participant_column == "participant_id"
    assert (
        "participant_mean_function"
        in result.provenance["function_on_scalar_regression"]["estimand"]
    )


def test_participant_unit_rejects_trial_varying_predictors():
    time = np.linspace(0.0, 1.0, 5)
    trajectories = TrajectorySet(
        time=time,
        values=np.zeros((4, 5, 1)),
        curve_ids=("a", "b", "c", "d"),
        dimension_names=("metric",),
        metadata=pd.DataFrame(
            {"participant_id": ("P1", "P1", "P2", "P2")}
        ),
        coordinate_system="unknown",
        time_unit="s",
    )
    design = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "condition": (0.0, 1.0, 0.0, 1.0),
        }
    )

    with pytest.raises(ValueError, match="constant within participant"):
        fit_function_on_scalar_regression(
            trajectories,
            design,
            ("condition",),
            unit="participant",
            participant_column="participant_id",
        )


def test_design_and_model_contracts_fail_closed():
    trajectories, design, _, _ = _independent_data()

    with pytest.raises(TypeError, match="pandas DataFrame"):
        fit_function_on_scalar_regression(
            trajectories,
            {"condition": np.ones(trajectories.n_curves)},
            ("condition",),
        )
    with pytest.raises(ValueError, match="one row per source trajectory"):
        fit_function_on_scalar_regression(
            trajectories,
            design.iloc[:-1].copy(),
            ("condition",),
        )

    wrong_ids = design.copy()
    wrong_ids.loc[0, "curve_id"] = "wrong"
    with pytest.raises(ValueError, match="must match trajectories.curve_ids"):
        fit_function_on_scalar_regression(
            trajectories,
            wrong_ids,
            ("condition",),
        )

    nonnumeric = design.copy()
    nonnumeric["condition"] = "A"
    with pytest.raises(TypeError, match="must be numeric"):
        fit_function_on_scalar_regression(
            trajectories,
            nonnumeric,
            ("condition",),
        )

    rank_deficient = design.copy()
    rank_deficient["duplicate"] = rank_deficient["condition"]
    with pytest.raises(ValueError, match="rank deficient"):
        fit_function_on_scalar_regression(
            trajectories,
            rank_deficient,
            ("condition", "duplicate"),
        )

    with pytest.raises(ValueError, match="participant_column must be None"):
        fit_function_on_scalar_regression(
            trajectories,
            design,
            ("condition",),
            unit="curve",
            participant_column="participant_id",
        )

    with pytest.raises(ValueError, match="unit must be"):
        fit_function_on_scalar_regression(
            trajectories,
            design,
            ("condition",),
            unit="bad",
        )


def test_bootstrap_band_frame_plot_and_reporting_contracts():
    trajectories, design, _, _ = _independent_data()
    result = fit_function_on_scalar_regression(
        trajectories,
        design,
        ("condition",),
        dimensions=("signal",),
    )
    bootstrap = bootstrap_function_on_scalar_coefficients(
        result,
        n_bootstrap=100,
        random_state=11,
    )
    band = function_on_scalar_simultaneous_bands(bootstrap)

    frame = function_on_scalar_coefficient_frame(result, band=band)
    assert set(
        (
            "coefficient",
            "time",
            "dimension",
            "estimate",
            "standard_error",
            "lower",
            "upper",
            "critical_value",
        )
    ) <= set(frame.columns)
    assert len(frame) == result.n_coefficients * result.time.size

    ax = plot_function_on_scalar_coefficients(
        band,
        coefficient="condition",
        dimension="signal",
    )
    assert "condition" in ax.get_title()
    assert len(ax.collections) == 1

    text = function_on_scalar_reporting_text(result, band=band)
    assert "Function-on-scalar regression" in text
    assert "HC1 sandwich" in text
    assert "not a functional mixed-effects model" in text

    with pytest.raises(ValueError, match="simultaneous_scope"):
        function_on_scalar_simultaneous_bands(
            bootstrap,
            simultaneous_scope="bad",
        )
    with pytest.raises(ValueError, match="at least 100"):
        bootstrap_function_on_scalar_coefficients(
            result,
            n_bootstrap=99,
        )
    with pytest.raises(ValueError, match="rademacher.*normal"):
        bootstrap_function_on_scalar_coefficients(
            result,
            n_bootstrap=100,
            multiplier="bad",
        )
