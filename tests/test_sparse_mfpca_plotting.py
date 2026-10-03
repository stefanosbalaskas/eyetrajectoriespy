from __future__ import annotations

from dataclasses import replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et


@pytest.fixture(scope="module")
def sparse_mfpca_fit():
    rng = np.random.default_rng(12101)
    times = []
    values = []
    curve_ids = []
    participants = []

    for index in range(24):
        t = np.sort(np.r_[0.0, rng.uniform(0.03, 0.97, 8), 1.0])
        z1, z2 = rng.normal(size=2)
        x = (
            0.30
            + 0.35 * t
            + 0.42 * z1 * np.sin(np.pi * t)
            + 0.08 * z2 * np.sin(2.0 * np.pi * t)
        )
        y = (
            0.55
            - 0.20 * t
            + 0.24 * z1 * np.cos(np.pi * t)
            - 0.18 * z2 * np.sin(2.0 * np.pi * t)
        )
        xy = np.column_stack([x, y]) + rng.normal(0.0, 0.05, size=(t.size, 2))
        times.append(t)
        values.append(xy)
        curve_ids.append(f"P{index + 1:02d}|1")
        participants.append(f"P{index + 1:02d}")

    irregular = et.IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(curve_ids),
        dimension_names=("x", "y"),
        metadata=pd.DataFrame({"participant_id": participants}),
        coordinate_system="normalized",
        time_unit="s",
    )
    return et.fit_sparse_mfpca(
        irregular,
        dimensions=("x", "y"),
        n_components=2,
        evaluation_grid=np.linspace(0.0, 1.0, 41),
        mean_bandwidth=0.20,
        covariance_bandwidth=0.30,
        measurement_error="diagonal",
        measurement_error_variance=(0.0025, 0.0025),
        psd_action="project",
        score_ridge=0.0,
        score_failure_action="retain_nan",
    )


def test_sparse_mfpca_public_plots_render_retained_result(sparse_mfpca_fit):
    component_axes = et.plot_sparse_mfpca_component(
        sparse_mfpca_fit,
        component=0,
        sd_multiplier=1.0,
    )
    assert np.asarray(component_axes).size == 2
    assert all(len(ax.lines) == 3 for ax in component_axes)

    covariance_axes = et.plot_sparse_mfpca_covariance_blocks(
        sparse_mfpca_fit,
        stage="used",
    )
    assert np.asarray(covariance_axes).shape == (2, 2)

    cross_axes = et.plot_sparse_mfpca_cross_covariance(
        sparse_mfpca_fit,
        stage="used",
    )
    assert np.asarray(cross_axes).size == 2

    diagnostic_ax = et.plot_sparse_mfpca_score_diagnostics(sparse_mfpca_fit)
    assert diagnostic_ax.get_xlabel() == "paired native observations"
    assert "condition number" in diagnostic_ax.get_ylabel()

    for figure in {
        component_axes[0].figure,
        covariance_axes[0, 0].figure,
        cross_axes[0].figure,
        diagnostic_ax.figure,
    }:
        plt.close(figure)


def test_sparse_mfpca_default_colorbars_stay_outside_heatmaps(sparse_mfpca_fit):
    for plotting_function in (
        et.plot_sparse_mfpca_covariance_blocks,
        et.plot_sparse_mfpca_cross_covariance,
    ):
        axes = np.asarray(plotting_function(sparse_mfpca_fit), dtype=object).reshape(-1)
        figure = axes[0].figure
        assert figure.get_layout_engine() is not None

        figure.canvas.draw()
        colorbar_axes = [ax for ax in figure.axes if ax not in axes.tolist()]
        assert len(colorbar_axes) == 1
        right_edge = max(ax.get_position().x1 for ax in axes)
        assert colorbar_axes[0].get_position().x0 > right_edge
        plt.close(figure)


def test_sparse_mfpca_covariance_plots_support_smoothed_stage(sparse_mfpca_fit):
    covariance_axes = et.plot_sparse_mfpca_covariance_blocks(
        sparse_mfpca_fit,
        stage="smoothed",
    )
    cross_axes = et.plot_sparse_mfpca_cross_covariance(
        sparse_mfpca_fit,
        stage="smoothed",
    )

    assert "smoothed" in covariance_axes[0, 0].figure._suptitle.get_text()
    assert "smoothed" in cross_axes[0].figure._suptitle.get_text()

    plt.close(covariance_axes[0, 0].figure)
    plt.close(cross_axes[0].figure)


def test_sparse_mfpca_plot_component_validates_arguments(sparse_mfpca_fit):
    with pytest.raises(TypeError, match="component must be an integer"):
        et.plot_sparse_mfpca_component(sparse_mfpca_fit, component=True)
    with pytest.raises(IndexError, match="outside the retained"):
        et.plot_sparse_mfpca_component(
            sparse_mfpca_fit,
            component=sparse_mfpca_fit.n_components,
        )
    with pytest.raises(TypeError, match="sd_multiplier must be a real scalar"):
        et.plot_sparse_mfpca_component(sparse_mfpca_fit, sd_multiplier=True)
    with pytest.raises(ValueError, match="finite and > 0"):
        et.plot_sparse_mfpca_component(sparse_mfpca_fit, sd_multiplier=0.0)


def test_sparse_mfpca_covariance_plots_validate_stage(sparse_mfpca_fit):
    with pytest.raises(ValueError, match="stage must be 'used' or 'smoothed'"):
        et.plot_sparse_mfpca_covariance_blocks(sparse_mfpca_fit, stage="raw")
    with pytest.raises(ValueError, match="stage must be 'used' or 'smoothed'"):
        et.plot_sparse_mfpca_cross_covariance(sparse_mfpca_fit, stage="raw")


def test_sparse_mfpca_plots_require_result_type():
    with pytest.raises(TypeError, match="SparseMFPCAResult"):
        et.plot_sparse_mfpca_component(object())
    with pytest.raises(TypeError, match="SparseMFPCAResult"):
        et.plot_sparse_mfpca_covariance_blocks(object())
    with pytest.raises(TypeError, match="SparseMFPCAResult"):
        et.plot_sparse_mfpca_cross_covariance(object())
    with pytest.raises(TypeError, match="SparseMFPCAResult"):
        et.plot_sparse_mfpca_score_diagnostics(object())


def test_sparse_mfpca_score_plot_fails_closed_on_malformed_diagnostics(
    sparse_mfpca_fit,
):
    malformed = replace(
        sparse_mfpca_fit,
        score_diagnostics=sparse_mfpca_fit.score_diagnostics.drop(
            columns=["condition_number"]
        ),
    )
    with pytest.raises(ValueError, match="condition_number"):
        et.plot_sparse_mfpca_score_diagnostics(malformed)
