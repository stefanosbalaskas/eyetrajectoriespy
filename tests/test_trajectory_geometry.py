import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    heading_function,
    signed_curvature_function,
    trajectory_tortuosity,
    turning_rate_function,
)


def _trajectory(time, xy, *, names=("x", "y"), coordinate_system="unknown"):
    values = np.asarray(xy, dtype=float)
    if values.ndim == 2:
        values = values[None, :, :]
    return TrajectorySet(
        time=np.asarray(time, dtype=float),
        values=values,
        curve_ids=tuple(f"c{index}" for index in range(values.shape[0])),
        dimension_names=names,
        time_unit="s",
        coordinate_system=coordinate_system,
    )


def test_straight_line_heading_curvature_and_turning_rate_are_exact():
    time = np.linspace(0.0, 2.0, 101)
    xy = np.column_stack([time, 2.0 * time])
    source = _trajectory(time, xy)

    heading = heading_function(source)
    curvature = signed_curvature_function(source)
    turning = turning_rate_function(source)

    np.testing.assert_allclose(
        heading.values[0, :, 0],
        np.arctan2(2.0, 1.0),
        atol=1e-12,
    )
    np.testing.assert_allclose(curvature.values[0, :, 0], 0.0, atol=1e-10)
    np.testing.assert_allclose(turning.values[0, :, 0], 0.0, atol=1e-10)
    assert curvature.provenance["smoothing"] is False
    assert curvature.provenance["denominator_epsilon"] is None
    assert heading.provenance["angle_unwrapped"] is False


def test_counterclockwise_unit_circle_has_positive_unit_curvature_and_turning_rate():
    time = np.linspace(0.0, 2.0 * np.pi, 401)
    xy = np.column_stack([np.cos(time), np.sin(time)])
    source = _trajectory(time, xy)

    curvature = signed_curvature_function(source)
    turning = turning_rate_function(source)
    interior = slice(5, -5)

    np.testing.assert_allclose(
        curvature.values[0, interior, 0],
        1.0,
        atol=2e-3,
    )
    np.testing.assert_allclose(
        turning.values[0, interior, 0],
        1.0,
        atol=2e-3,
    )
    assert curvature.provenance["orientation_sign"] == (
        "positive_under_the_recorded_x_y_axis_orientation"
    )
    assert turning.provenance["computed_from_wrapped_heading"] is False


def test_clockwise_unit_circle_has_negative_signed_geometry():
    time = np.linspace(0.0, 2.0 * np.pi, 401)
    xy = np.column_stack([np.cos(time), -np.sin(time)])
    source = _trajectory(time, xy)

    curvature = signed_curvature_function(source)
    turning = turning_rate_function(source)
    np.testing.assert_allclose(curvature.values[0, 5:-5, 0], -1.0, atol=2e-3)
    np.testing.assert_allclose(turning.values[0, 5:-5, 0], -1.0, atol=2e-3)


def test_stationary_geometry_is_explicitly_undefined_not_zero_filled():
    time = np.linspace(0.0, 1.0, 21)
    source = _trajectory(time, np.zeros((time.size, 2)))

    for function in (
        heading_function,
        signed_curvature_function,
        turning_rate_function,
    ):
        result = function(source)
        assert np.isnan(result.values).all()
        assert result.provenance["undefined_sample_counts"] == [time.size]
        assert result.provenance["low_speed_rule"] == "speed <= min_speed"

        with pytest.raises(ValueError, match="undefined where speed"):
            function(source, undefined_policy="raise")


def test_low_speed_threshold_is_explicit_and_validated():
    time = np.linspace(0.0, 1.0, 31)
    xy = np.column_stack([1e-6 * time, np.zeros_like(time)])
    source = _trajectory(time, xy)

    result = heading_function(source, min_speed=1e-5)
    assert np.isnan(result.values).all()

    with pytest.raises(ValueError, match="non-negative"):
        heading_function(source, min_speed=-1.0)
    with pytest.raises(TypeError, match="not boolean"):
        heading_function(source, min_speed=True)
    with pytest.raises(ValueError, match="undefined_policy"):
        heading_function(source, undefined_policy="zero")


def test_nonstandard_planar_dimensions_must_be_declared_explicitly():
    time = np.linspace(0.0, 1.0, 31)
    xy = np.column_stack([time, time**2])
    source = _trajectory(time, xy, names=("gaze_x", "gaze_y"))

    with pytest.raises(ValueError, match="supplied explicitly"):
        signed_curvature_function(source)

    result = signed_curvature_function(
        source,
        dimensions=("gaze_x", "gaze_y"),
    )
    assert result.provenance["planar_dimensions"] == ("gaze_x", "gaze_y")

    with pytest.raises(ValueError, match="exactly two"):
        heading_function(source, dimensions=("gaze_x",))
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        heading_function(source, dimensions=("gaze_x", "missing"))


def test_two_point_path_supports_tortuosity_but_not_differential_geometry():
    time = np.array([0.0, 1.0])
    xy = np.asarray([[0.0, 0.0], [1.0, 0.0]])
    source = _trajectory(time, xy)

    result = trajectory_tortuosity(source)
    assert result.loc[0, "tortuosity"] == pytest.approx(1.0)

    with pytest.raises(ValueError, match="at least three time samples"):
        heading_function(source)


def test_tortuosity_is_path_length_over_endpoint_displacement():
    time = np.array([0.0, 1.0, 2.0])
    values = np.asarray(
        [
            [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
            [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]],
        ]
    )
    source = _trajectory(time, values)

    result = trajectory_tortuosity(source)

    assert result.loc[0, "path_length"] == pytest.approx(2.0)
    assert result.loc[0, "endpoint_displacement"] == pytest.approx(2.0)
    assert result.loc[0, "tortuosity"] == pytest.approx(1.0)
    assert result.loc[1, "path_length"] == pytest.approx(2.0)
    assert result.loc[1, "endpoint_displacement"] == pytest.approx(np.sqrt(2.0))
    assert result.loc[1, "tortuosity"] == pytest.approx(np.sqrt(2.0))
    assert result.attrs["provenance"]["denominator_epsilon"] is None


def test_closed_path_tortuosity_is_undefined_or_raises():
    time = np.arange(5, dtype=float)
    xy = np.asarray(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
            [0.0, 0.0],
        ]
    )
    source = _trajectory(time, xy)

    result = trajectory_tortuosity(source)
    assert bool(result.loc[0, "undefined"])
    assert np.isnan(result.loc[0, "tortuosity"])

    with pytest.raises(ValueError, match="endpoint displacement"):
        trajectory_tortuosity(source, undefined_policy="raise")


def test_tortuosity_displacement_threshold_and_policy_are_validated():
    time = np.array([0.0, 1.0, 2.0])
    xy = np.asarray([[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]])
    source = _trajectory(time, xy)

    result = trajectory_tortuosity(source, min_displacement=2.0)
    assert np.isnan(result.loc[0, "tortuosity"])

    with pytest.raises(ValueError, match="non-negative"):
        trajectory_tortuosity(source, min_displacement=-0.1)
    with pytest.raises(ValueError, match="undefined_policy"):
        trajectory_tortuosity(source, undefined_policy="infinite")
