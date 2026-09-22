import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    plot_windowed_rqa_trajectories,
    windowed_rqa_functional_reporting_text,
    windowed_rqa_trajectory_set,
)


def _multi_curve(n=120):
    time = np.arange(n, dtype=float) * 0.01
    curves = []
    for phase in (0.0, 0.35, 0.7):
        curves.append(np.sin(2 * np.pi * 2 * time + phase))
    values = np.asarray(curves, dtype=float)[:, :, None]
    return TrajectorySet(
        time=time,
        values=values,
        curve_ids=("p1", "p2", "p3"),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="normalized",
        provenance={"source": "synthetic"},
    )


def test_windowed_rqa_functional_bridge_preserves_curve_identity_and_overlap():
    gaze = _multi_curve()
    result = windowed_rqa_trajectory_set(
        gaze,
        metrics=("recurrence_rate", "determinism", "laminarity"),
        window=40,
        step=20,
        radius=0.35,
        theiler_window=2,
        dimensions=("x",),
        undefined_policy="keep",
    )
    assert result.trajectories.curve_ids == gaze.curve_ids
    assert result.trajectories.dimension_names == (
        "recurrence_rate",
        "determinism",
        "laminarity",
    )
    assert result.trajectories.values.shape[0] == 3
    assert result.n_windows == 5
    assert result.overlap_samples == 20
    assert result.overlap_fraction == pytest.approx(0.5)
    assert result.trajectories.provenance["window_rows_are_independent"] is False
    assert len(result.window_results) == gaze.n_curves
    np.testing.assert_allclose(
        result.trajectories.time,
        result.window_results[0].table["center_time"],
    )


def test_target_rr_cannot_be_repackaged_as_rr_outcome():
    gaze = _multi_curve()
    with pytest.raises(ValueError, match="controlled by design"):
        windowed_rqa_trajectory_set(
            gaze,
            metrics=("recurrence_rate", "determinism"),
            window=40,
            step=20,
            target_recurrence_rate=0.05,
            theiler_window=2,
            dimensions=("x",),
        )


def test_undefined_metric_policy_is_fail_closed_or_explicit_keep():
    gaze = _multi_curve()
    with pytest.raises(ValueError, match="metric is undefined"):
        windowed_rqa_trajectory_set(
            gaze,
            metrics=("diagonal_entropy",),
            window=30,
            step=15,
            radius=1e-12,
            dimensions=("x",),
        )
    kept = windowed_rqa_trajectory_set(
        gaze,
        metrics=("diagonal_entropy",),
        window=30,
        step=15,
        radius=1e-12,
        dimensions=("x",),
        undefined_policy="keep",
    )
    assert np.isnan(kept.trajectories.values).any()
    assert kept.trajectories.provenance["undefined_value_count"] > 0


def test_functional_rqa_plot_and_reporting_expose_dependence_contract():
    gaze = _multi_curve()
    result = windowed_rqa_trajectory_set(
        gaze,
        metrics=("recurrence_rate",),
        window=40,
        step=20,
        radius=0.35,
        dimensions=("x",),
    )
    ax = plot_windowed_rqa_trajectories(
        result,
        metric="recurrence_rate",
        show_mean=True,
    )
    assert "Functional windowed RQA" in ax.get_title()
    text = windowed_rqa_functional_reporting_text(result)
    assert "50.0% sample overlap" in text
    assert "not treated as independent observations" in text
