import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    FPCAComponentBandResult,
    TrajectorySet,
    bootstrap_fpca_component_bands,
    fpca_component_band_frame,
    fpca_component_band_reporting_text,
    plot_fpca_component_band,
    simulate_planar_trajectories,
)


def sample():
    return simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=2,
        n_time=31,
        random_state=41,
    )


def near_tie_sample():
    n_curves = 60
    time = np.linspace(0.0, 1.0, 31)
    shape = np.sin(np.pi * time)
    theta = np.linspace(0.0, 2.0 * np.pi, n_curves, endpoint=False)
    a = np.sqrt(2.0) * np.cos(theta)
    b = np.sqrt(2.0) * np.sin(theta)
    values = np.stack([a[:, None] * shape, b[:, None] * shape], axis=2)
    metadata = pd.DataFrame({"participant_id": [f"p{i:03d}" for i in range(n_curves)]})
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=tuple(f"c{i:03d}" for i in range(n_curves)),
        dimension_names=("x", "y"),
        metadata=metadata,
        coordinate_system="normalized",
        time_unit="normalized",
    )


def test_simultaneous_component_bands_are_reproducible_and_ordered():
    gaze = sample()
    first = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        confidence_level=0.95,
        random_state=9,
    )
    second = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=20,
        n_components=2,
        scaling="dimension_sd",
        confidence_level=0.95,
        random_state=9,
    )
    assert isinstance(first, FPCAComponentBandResult)
    assert first.lower.shape == (2, gaze.n_time, gaze.n_dimensions)
    assert first.upper.shape == first.lower.shape
    assert first.pointwise_se.shape == first.lower.shape
    assert first.max_statistics.shape == (20, 2)
    assert first.similarities.shape == (20, 2)
    assert first.critical_values.shape == (2,)
    assert first.n_components == 2
    assert first.n_bootstrap == 20
    assert np.all(first.lower <= first.reference.components[:2])
    assert np.all(first.reference.components[:2] <= first.upper)
    assert np.all(first.pointwise_se >= 0)
    assert np.all(first.critical_values >= 0)
    assert np.all((first.similarities >= 0) & (first.similarities <= 1 + 1e-12))
    assert np.allclose(first.lower, second.lower)
    assert np.allclose(first.upper, second.upper)
    assert first.provenance["fpca_component_band"]["continuous_between_grid_points"] is False


def test_higher_confidence_is_no_narrower_with_identical_bootstrap_draws():
    gaze = sample()
    band90 = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=24, n_components=2, confidence_level=0.90, random_state=4
    )
    band99 = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=24, n_components=2, confidence_level=0.99, random_state=4
    )
    assert np.all((band99.upper - band99.lower) >= (band90.upper - band90.lower) - 1e-12)


def test_family_scope_is_at_least_as_conservative_as_component_scope():
    gaze = sample()
    component = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=24, n_components=2, simultaneous_scope="component", random_state=3
    )
    family = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=24, n_components=2, simultaneous_scope="family", random_state=3
    )
    assert family.critical_values[0] == pytest.approx(family.critical_values[1])
    assert np.all(family.critical_values >= component.critical_values - 1e-12)


def test_participant_resampling_and_long_frame():
    gaze = sample()
    result = bootstrap_fpca_component_bands(
        gaze,
        n_bootstrap=20,
        n_components=1,
        resample_unit="participant",
        participant_column="participant_id",
        random_state=8,
    )
    assert result.resampling_unit == "participant"
    assert result.participant_column == "participant_id"
    frame = fpca_component_band_frame(result)
    assert set(frame.columns) == {
        "component", "time", "dimension", "reference", "pointwise_se", "lower", "upper"
    }
    assert len(frame) == gaze.n_time * gaze.n_dimensions


def test_near_tie_screen_errors_warns_or_records_explicitly():
    gaze = near_tie_sample()
    with pytest.raises(ValueError, match="weakly identified"):
        bootstrap_fpca_component_bands(
            gaze, n_bootstrap=20, n_components=1, relative_gap_threshold=0.05, on_near_tie="error"
        )
    with pytest.warns(RuntimeWarning, match="weakly identified"):
        warned = bootstrap_fpca_component_bands(
            gaze, n_bootstrap=20, n_components=1, relative_gap_threshold=0.05, on_near_tie="warn"
        )
    assert warned.minimum_relative_gaps[0] <= 0.05
    ignored = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=20, n_components=1, relative_gap_threshold=0.05, on_near_tie="ignore"
    )
    assert ignored.provenance["fpca_component_band"]["near_tie_components"] == [1]


def test_band_contract_failures_are_explicit():
    gaze = sample()
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, n_bootstrap=19)
    with pytest.raises(TypeError):
        bootstrap_fpca_component_bands(gaze, n_bootstrap=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, n_components=0)
    with pytest.raises(TypeError):
        bootstrap_fpca_component_bands(gaze, n_components=True)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, confidence_level=1.0)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, simultaneous_scope="point")
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, resample_unit="participant")
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, resample_unit="other")
    with pytest.raises(TypeError):
        bootstrap_fpca_component_bands(gaze, relative_gap_threshold=False)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, relative_gap_threshold=1.0)
    with pytest.raises(ValueError):
        bootstrap_fpca_component_bands(gaze, on_near_tie="guess")


def test_reporting_and_plotting_state_simultaneous_scope_and_limitations():
    gaze = sample()
    result = bootstrap_fpca_component_bands(
        gaze, n_bootstrap=20, n_components=1, simultaneous_scope="component", random_state=6
    )
    text = fpca_component_band_reporting_text(result)
    assert "observed time-by-dimension grid" in text
    assert "does not establish continuous-domain coverage" in text
    assert "component-wise" in text
    assert plot_fpca_component_band(result, component=0, dimension="x") is not None
    with pytest.raises(IndexError):
        plot_fpca_component_band(result, component=4)
    with pytest.raises(KeyError):
        plot_fpca_component_band(result, dimension="missing")
    plt.close("all")
