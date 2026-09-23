import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    embedding_delay_diagnostics,
    embedding_dimension_diagnostics,
    estimate_largest_lyapunov_kantz,
    estimate_largest_lyapunov_rosenstein,
    fit_local_return_map,
    kantz_divergence_curve,
    local_divergence_curve,
    plot_embedding_delay_diagnostics,
    plot_embedding_dimension_diagnostics,
    plot_local_divergence,
    plot_poincare_return_map,
    plot_recurrence,
    plot_windowed_rqa,
    poincare_crossings,
    recurrence_matrix,
    windowed_rqa,
)


def _logistic():
    x = np.empty(300, dtype=float)
    x[0] = 0.217
    for i in range(x.size - 1):
        x[i + 1] = 4.0 * x[i] * (1.0 - x[i])
    return TrajectorySet(
        time=np.arange(x.size, dtype=float) * 0.01,
        values=x[None, :, None],
        curve_ids=("x",),
        dimension_names=("x",),
        time_unit="s",
    )


def _cycle():
    time = np.linspace(0, 18 * np.pi, 1801)
    amp = np.exp(-0.02 * time)
    values = np.stack([amp * np.sin(time), amp * np.cos(time)], axis=1)
    return TrajectorySet(
        time=time,
        values=values[None, :, :],
        curve_ids=("cycle",),
        dimension_names=("x", "y"),
        time_unit="s",
    )


def test_nonlinear_plot_helpers_return_axes():
    data = _logistic()
    delay = embedding_delay_diagnostics(
        data, curve=0, dimension="x", max_lag=12, bins=10
    )
    dimension = embedding_dimension_diagnostics(
        data,
        curve=0,
        dimension="x",
        delay=1,
        max_dimension=3,
        theiler_window=5,
    )
    embedded = delay_embed_trajectory(
        data, embedding_dimension=2, delay=1, dimensions=("x",)
    )
    recurrence = recurrence_matrix(
        embedded, curve=0, target_recurrence_rate=0.05, theiler_window=5
    )
    dynamic = windowed_rqa(
        data,
        curve=0,
        window=100,
        step=50,
        radius=0.05,
        theiler_window=5,
        dimensions=("x",),
    )
    divergence = local_divergence_curve(
        embedded, curve=0, theiler_window=5, max_horizon=6
    )
    lle = estimate_largest_lyapunov_rosenstein(
        divergence, fit_start=1, fit_end=4
    )

    kantz_divergence = kantz_divergence_curve(
        embedded,
        curve=0,
        radius=0.08,
        theiler_window=5,
        max_horizon=6,
        min_neighbors=2,
    )
    kantz_lle = estimate_largest_lyapunov_kantz(
        kantz_divergence,
        fit_start=1,
        fit_end=4,
    )

    for ax in (
        plot_embedding_delay_diagnostics(delay),
        plot_embedding_dimension_diagnostics(dimension),
        plot_recurrence(recurrence),
        plot_windowed_rqa(dynamic),
        plot_local_divergence(lle),
        plot_local_divergence(kantz_lle),
    ):
        assert hasattr(ax, "plot") or hasattr(ax, "scatter")
        plt.close(ax.figure)


def test_recurrence_plot_refuses_silent_subsampling():
    data = _logistic()
    recurrence = recurrence_matrix(
        data,
        curve=0,
        radius=0.2,
        dimensions=("x",),
    )
    with pytest.raises(ValueError, match="max_points"):
        plot_recurrence(recurrence, max_points=1)


def test_return_map_plot_requires_explicit_one_dimensional_state():
    cycle = _cycle()
    one_dim = poincare_crossings(
        cycle,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y",),
    )
    fit = fit_local_return_map(one_dim, reference="mean", n_neighbors=7)
    ax = plot_poincare_return_map(one_dim, fit=fit)
    assert hasattr(ax, "scatter")
    plt.close(ax.figure)

    two_dim_source = TrajectorySet(
        time=cycle.time,
        values=np.concatenate(
            [cycle.values, (cycle.values[:, :, :1] ** 2)], axis=2
        ),
        curve_ids=cycle.curve_ids,
        dimension_names=("x", "y", "x2"),
        time_unit="s",
    )
    two_dim = poincare_crossings(
        two_dim_source,
        curve=0,
        section_dimension="x",
        section_value=0.0,
        direction="positive",
        state_dimensions=("y", "x2"),
    )
    with pytest.raises(ValueError, match="one returned state dimension"):
        plot_poincare_return_map(two_dim)
