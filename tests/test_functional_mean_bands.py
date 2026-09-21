import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    functional_mean_band_frame,
    functional_mean_band_reporting_text,
    multiplier_functional_mean_band,
    plot_functional_mean_band,
    simulate_planar_trajectories,
)


def repeated_sample():
    return simulate_planar_trajectories(
        n_participants=10,
        trials_per_participant=3,
        n_time=41,
        random_state=91,
    )


def test_curve_level_band_is_reproducible_and_ordered():
    gaze = repeated_sample()
    first = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.95,
        n_multiplier=300,
        random_state=17,
    )
    second = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.95,
        n_multiplier=300,
        random_state=17,
    )

    assert first.mean.shape == (gaze.n_time, gaze.n_dimensions)
    assert first.max_statistics.shape == (300,)
    assert np.all(first.lower <= first.mean)
    assert np.all(first.mean <= first.upper)
    assert np.allclose(first.lower, second.lower)
    assert np.allclose(first.upper, second.upper)
    assert first.critical_value == pytest.approx(second.critical_value)
    assert first.provenance["functional_mean_band"]["estimand"] == "equal_weight_curve_mean"


def test_higher_confidence_level_is_not_narrower_with_same_multiplier_draws():
    gaze = repeated_sample()
    low = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.90,
        n_multiplier=400,
        random_state=3,
    )
    high = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.99,
        n_multiplier=400,
        random_state=3,
    )
    assert high.critical_value >= low.critical_value
    assert np.all((high.upper - high.lower) >= (low.upper - low.lower) - 1e-15)


def test_participant_level_estimand_is_equal_weight_not_curve_weighted():
    time = np.array([0.0, 1.0, 2.0])
    values = np.array(
        [
            [[0.0], [0.0], [0.0]],
            [[2.0], [2.0], [2.0]],
            [[4.0], [4.0], [4.0]],
            [[10.0], [10.0], [10.0]],
        ]
    )
    gaze = TrajectorySet(
        time=time,
        values=values,
        curve_ids=("A1", "A2", "A3", "B1"),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": ["A", "A", "A", "B"]}),
        coordinate_system="normalized",
        time_unit="s",
    )

    result = multiplier_functional_mean_band(
        gaze,
        n_multiplier=200,
        unit="participant",
        participant_column="participant_id",
        random_state=5,
    )
    assert result.n_units == 2
    assert result.unit_ids == ("A", "B")
    assert np.allclose(result.mean[:, 0], 6.0)
    assert not np.allclose(result.mean[:, 0], values.mean(axis=0)[:, 0])
    band = result.provenance["functional_mean_band"]
    assert band["estimand"] == "equal_weight_mean_of_participant_mean_trajectories"
    assert band["curves_per_unit"] == [3, 1]


def test_zero_variance_grid_points_have_exact_zero_width():
    gaze = repeated_sample()
    values = gaze.values.copy()
    values[:, 0, 0] = 0.25
    modified = gaze.with_values(values)

    result = multiplier_functional_mean_band(
        modified,
        n_multiplier=200,
        random_state=11,
    )
    assert result.pointwise_se[0, 0] == pytest.approx(0.0)
    assert result.lower[0, 0] == pytest.approx(result.mean[0, 0])
    assert result.upper[0, 0] == pytest.approx(result.mean[0, 0])
    assert result.provenance["functional_mean_band"]["zero_variance_grid_points"] >= 1


def test_all_constant_functions_return_zero_critical_value():
    time = np.array([0.0, 1.0, 2.0])
    gaze = TrajectorySet(
        time=time,
        values=np.ones((4, 3, 2)),
        curve_ids=("c1", "c2", "c3", "c4"),
        dimension_names=("x", "y"),
        coordinate_system="normalized",
        time_unit="s",
    )
    result = multiplier_functional_mean_band(
        gaze,
        n_multiplier=100,
        random_state=1,
    )
    assert result.critical_value == pytest.approx(0.0)
    assert np.all(result.max_statistics == 0)
    assert np.allclose(result.lower, result.mean)
    assert np.allclose(result.upper, result.mean)


def test_functional_mean_band_contract_errors():
    gaze = repeated_sample()

    with pytest.raises(ValueError):
        multiplier_functional_mean_band(gaze, confidence_level=1.0)
    with pytest.raises(TypeError):
        multiplier_functional_mean_band(gaze, n_multiplier=True)
    with pytest.raises(ValueError):
        multiplier_functional_mean_band(gaze, n_multiplier=99)
    with pytest.raises(ValueError):
        multiplier_functional_mean_band(gaze, unit="bad")
    with pytest.raises(ValueError):
        multiplier_functional_mean_band(
            gaze,
            unit="curve",
            participant_column="participant_id",
        )
    with pytest.raises(ValueError):
        multiplier_functional_mean_band(
            gaze,
            unit="participant",
        )
    with pytest.raises(ValueError):
        multiplier_functional_mean_band(
            gaze,
            unit="participant",
            participant_column="missing",
        )

    metadata = gaze.metadata.reset_index(drop=True).copy()
    metadata.loc[0, "participant_id"] = np.nan
    missing_group = TrajectorySet(
        gaze.time,
        gaze.values,
        gaze.curve_ids,
        gaze.dimension_names,
        metadata,
        gaze.coordinate_system,
        gaze.time_unit,
        gaze.provenance,
    )
    with pytest.raises(ValueError, match="missing"):
        multiplier_functional_mean_band(
            missing_group,
            unit="participant",
            participant_column="participant_id",
        )


def test_nonfinite_and_probability_simplex_inputs_are_rejected():
    gaze = repeated_sample()
    values = gaze.values.copy()
    values[0, 0, 0] = np.inf
    bad = gaze.with_values(values)
    with pytest.raises(ValueError, match="finite"):
        multiplier_functional_mean_band(bad, n_multiplier=100)

    simplex = TrajectorySet(
        time=np.array([0.0, 1.0, 2.0]),
        values=np.array(
            [
                [[0.2, 0.8], [0.3, 0.7], [0.4, 0.6]],
                [[0.3, 0.7], [0.4, 0.6], [0.5, 0.5]],
                [[0.4, 0.6], [0.5, 0.5], [0.6, 0.4]],
            ]
        ),
        curve_ids=("a", "b", "c"),
        dimension_names=("AOI1", "AOI2"),
        coordinate_system="probability_simplex",
        time_unit="s",
    )
    with pytest.raises(ValueError, match="compositional"):
        multiplier_functional_mean_band(simplex, n_multiplier=100)


def test_frame_plot_and_reporting_contracts():
    gaze = repeated_sample()
    result = multiplier_functional_mean_band(
        gaze,
        n_multiplier=150,
        unit="participant",
        participant_column="participant_id",
        random_state=8,
    )
    frame = functional_mean_band_frame(result)
    assert len(frame) == gaze.n_time * gaze.n_dimensions
    assert set(frame.columns) == {
        "time",
        "dimension",
        "mean",
        "pointwise_se",
        "lower",
        "upper",
    }

    text = functional_mean_band_reporting_text(result)
    assert "simultaneous observed-grid band" in text
    assert "does not claim continuous-domain coverage" in text

    assert plot_functional_mean_band(result, dimension="x") is not None
    with pytest.raises(KeyError):
        plot_functional_mean_band(result, dimension="missing")
    plt.close("all")
