import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    dynamic_time_warping_distance,
    dynamic_time_warping_reporting_text,
    plot_dynamic_time_warping_alignment,
)


def _audit():
    a = np.array([[0.0], [0.0], [1.0]])
    b = np.array([[0.0], [1.0], [1.0]])
    return dynamic_time_warping_distance(
        a,
        b,
        step_pattern="symmetric2",
        normalize=True,
        return_path=True,
    )


def test_dtw_reporting_text_states_step_pattern_window_and_timing_boundary():
    result = _audit()
    text = dynamic_time_warping_reporting_text(result, digits=4)

    assert "symmetric2" in text
    assert "unconstrained" in text
    assert "normalized distance" in text
    assert "recorded timestamps were not used" in text
    assert "selected automatically" in text


def test_dtw_reporting_text_validates_inputs():
    with pytest.raises(TypeError, match="DynamicTimeWarpingResult"):
        dynamic_time_warping_reporting_text(object())
    with pytest.raises(TypeError, match="digits must be an integer"):
        dynamic_time_warping_reporting_text(_audit(), digits=True)
    with pytest.raises(ValueError, match="non-negative"):
        dynamic_time_warping_reporting_text(_audit(), digits=-1)


def test_dtw_alignment_plot_uses_audited_path():
    result = _audit()
    ax = plot_dynamic_time_warping_alignment(result)

    assert ax.get_xlabel() == "Sequence B sample index"
    assert ax.get_ylabel() == "Sequence A sample index"
    assert "symmetric2" in ax.get_title()
    assert len(ax.lines) == 2
    np.testing.assert_array_equal(
        np.asarray(ax.lines[0].get_xdata(), dtype=int),
        result.path[:, 1],
    )
    np.testing.assert_array_equal(
        np.asarray(ax.lines[0].get_ydata(), dtype=int),
        result.path[:, 0],
    )
    plt.close(ax.figure)


def test_dtw_alignment_plot_rejects_wrong_object():
    with pytest.raises(TypeError, match="DynamicTimeWarpingResult"):
        plot_dynamic_time_warping_alignment(object())
