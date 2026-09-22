import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    embedding_delay_diagnostics,
    embedding_dimension_diagnostics,
)


def _planar_set(n=120):
    time = np.arange(n, dtype=float) * 0.01
    x = np.sin(2 * np.pi * 2 * time)
    y = np.cos(2 * np.pi * 2 * time)
    values = np.stack([x, y], axis=1)[None, :, :]
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=("c1",),
        dimension_names=("x", "y"),
        time_unit="s",
        coordinate_system="normalized",
    )


def _logistic_set(n=500):
    x = np.empty(n, dtype=float)
    x[0] = 0.231
    for i in range(n - 1):
        x[i + 1] = 4.0 * x[i] * (1.0 - x[i])
    return TrajectorySet(
        time=np.arange(n, dtype=float) * 0.01,
        values=x[None, :, None],
        curve_ids=("logistic",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
    )


def test_delay_embedding_multivariate_exact_order():
    gaze = _planar_set(20)
    result = delay_embed_trajectory(
        gaze,
        embedding_dimension=3,
        delay=1,
        delay_units="samples",
        dimensions=("x", "y"),
    )

    assert result.values.shape == (1, 18, 6)
    np.testing.assert_allclose(
        result.values[0, 0],
        np.concatenate([gaze.values[0, 2], gaze.values[0, 1], gaze.values[0, 0]]),
    )
    assert result.state_names == (
        "x[t-0*delay]",
        "y[t-0*delay]",
        "x[t-1*delay]",
        "y[t-1*delay]",
        "x[t-2*delay]",
        "y[t-2*delay]",
    )
    assert result.provenance["automatic_parameter_selection"] is False


def test_delay_embedding_time_units_resolve_to_samples():
    gaze = _planar_set(40)
    result = delay_embed_trajectory(
        gaze,
        embedding_dimension=2,
        delay=0.02,
        delay_units="seconds",
        dimensions=("x",),
    )
    assert result.delay_samples == 2
    assert result.delay_time == pytest.approx(0.02)


def test_delay_embedding_rejects_missing_samples():
    gaze = _planar_set(20)
    values = gaze.values.copy()
    values[0, 4, 0] = np.nan
    broken = gaze.with_values(values)
    with pytest.raises(ValueError, match="missing values"):
        delay_embed_trajectory(
            broken,
            embedding_dimension=2,
            delay=1,
            dimensions=("x",),
        )


def test_delay_diagnostics_are_diagnostic_not_selector():
    gaze = _logistic_set(300)
    result = embedding_delay_diagnostics(
        gaze,
        curve="logistic",
        dimension="x",
        max_lag=20,
        bins=12,
    )
    assert len(result.table) == 20
    assert result.table["first_ami_local_minimum"].sum() <= 1
    assert np.isfinite(result.table["average_mutual_information"]).all()
    assert result.provenance["automatic_delay_selection"] is False
    assert result.provenance["histogram_edges_fixed_across_lags"] is True


def test_false_nearest_neighbor_diagnostics_return_bounded_fractions():
    gaze = _logistic_set(450)
    result = embedding_dimension_diagnostics(
        gaze,
        curve=0,
        dimension="x",
        delay=1,
        max_dimension=4,
        theiler_window=5,
    )
    assert list(result.table["embedding_dimension"]) == [1, 2, 3, 4]
    assert result.table["false_neighbor_fraction"].between(0, 1).all()
    assert result.provenance["automatic_dimension_selection"] is False


def test_time_based_parameters_require_regular_grid():
    gaze = _planar_set(20)
    irregular_time = gaze.time.copy()
    irregular_time[5:] += 0.001
    irregular = TrajectorySet(
        time=irregular_time,
        values=gaze.values,
        curve_ids=gaze.curve_ids,
        dimension_names=gaze.dimension_names,
        time_unit="s",
    )
    with pytest.raises(ValueError, match="regular grid"):
        delay_embed_trajectory(
            irregular,
            embedding_dimension=2,
            delay=0.01,
            delay_units="seconds",
            dimensions=("x",),
        )


def test_delay_embedding_requires_explicit_state_dimensions():
    gaze = _planar_set(30)
    with pytest.raises(ValueError, match="dimensions must be supplied explicitly"):
        delay_embed_trajectory(
            gaze,
            embedding_dimension=2,
            delay=1,
        )


def test_sample_lag_on_irregular_common_grid_records_no_constant_delay_time():
    gaze = _planar_set(30)
    time = gaze.time.copy()
    time[10:] += np.linspace(0.0, 0.02, time.size - 10)
    irregular = TrajectorySet(
        time=time,
        values=gaze.values,
        curve_ids=gaze.curve_ids,
        dimension_names=gaze.dimension_names,
        time_unit="s",
    )
    result = delay_embed_trajectory(
        irregular,
        embedding_dimension=2,
        delay=1,
        delay_units="samples",
        dimensions=("x",),
    )
    assert np.isnan(result.delay_time)
    assert result.provenance["constant_delay_time"] is False
