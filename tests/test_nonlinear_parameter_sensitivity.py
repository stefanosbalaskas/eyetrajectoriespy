import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    kantz_parameter_sensitivity,
    kantz_parameter_sensitivity_reporting_text,
    lyapunov_parameter_sensitivity,
    plot_kantz_sensitivity,
    plot_lyapunov_sensitivity,
    plot_rqa_sensitivity,
    rqa_parameter_sensitivity,
)


def _logistic_set(n=420):
    x = np.empty(n, dtype=float)
    x[0] = 0.217
    for i in range(n - 1):
        x[i + 1] = 4.0 * x[i] * (1.0 - x[i])
    return TrajectorySet(
        time=np.arange(n, dtype=float) * 0.01,
        values=x[None, :, None],
        curve_ids=("logistic",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
        provenance={"source": "logistic-map"},
    )


def test_rqa_parameter_sensitivity_evaluates_declared_cartesian_grid():
    data = _logistic_set()
    result = rqa_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2, 3),
        delays=(1,),
        radii=(0.05, 0.10),
        theiler_windows=(1, 4),
        min_diagonal_lengths=(2, 3),
        min_vertical_lengths=(2,),
    )

    assert result.n_specifications == 16
    assert result.curve_id == "logistic"
    assert result.table["specification_id"].is_unique
    assert set(result.table["embedding_dimension"]) == {2, 3}
    assert set(result.table["requested_radius"]) == {0.05, 0.10}
    assert set(result.table["theiler_window_samples"]) == {1, 4}
    assert set(result.table["min_diagonal_length"]) == {2, 3}
    assert result.provenance["automatic_parameter_selection"] is False
    assert result.provenance["failed_specification_policy"] == "raise_entire_analysis"
    assert result.provenance["matrices_retained"] is False

    summary = result.summary_table.set_index("metric")
    assert summary.loc["determinism", "n_specifications"] == 16
    assert 0 < summary.loc["determinism", "finite_fraction"] <= 1
    assert summary.loc["recurrence_rate", "maximum"] >= summary.loc[
        "recurrence_rate", "minimum"
    ]


def test_rqa_target_rate_sensitivity_records_controlled_metric_boundary():
    data = _logistic_set()
    result = rqa_parameter_sensitivity(
        data,
        curve="logistic",
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        target_recurrence_rates=(0.04, 0.08),
        theiler_windows=(2,),
        min_diagonal_lengths=(2,),
        min_vertical_lengths=(2,),
    )

    assert result.n_specifications == 2
    assert set(result.table["threshold_policy"]) == {"target_recurrence_rate"}
    assert result.table["requested_radius"].isna().all()
    assert np.all(np.isfinite(result.table["resolved_radius"]))
    assert "controlled by design" in result.provenance["controlled_metric_caution"]


def test_rqa_sensitivity_requires_exactly_one_threshold_grid():
    data = _logistic_set()
    common = dict(
        trajectories=data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        theiler_windows=(2,),
        min_diagonal_lengths=(2,),
        min_vertical_lengths=(2,),
    )
    with pytest.raises(ValueError, match="exactly one"):
        rqa_parameter_sensitivity(**common)
    with pytest.raises(ValueError, match="exactly one"):
        rqa_parameter_sensitivity(
            **common,
            radii=(0.1,),
            target_recurrence_rates=(0.05,),
        )


def test_rqa_sensitivity_rejects_embedding_dimension_one_for_delay_multiverse():
    data = _logistic_set()
    with pytest.raises(ValueError, match=">= 2"):
        rqa_parameter_sensitivity(
            data,
            curve=0,
            dimensions=("x",),
            embedding_dimensions=(1, 2),
            delays=(1,),
            radii=(0.1,),
            theiler_windows=(2,),
            min_diagonal_lengths=(2,),
            min_vertical_lengths=(2,),
        )


def test_lyapunov_parameter_sensitivity_retains_fit_quality_and_sign_summary():
    data = _logistic_set(520)
    result = lyapunov_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2, 3),
        delays=(1,),
        theiler_windows=(6, 10),
        fit_intervals=((1, 4), (2, 5)),
        max_horizon=8,
    )

    assert result.n_specifications == 8
    assert result.exponent_unit == "1/s"
    assert np.all(np.isfinite(result.table["exponent"]))
    assert np.all(np.isfinite(result.table["r_squared"]))
    assert np.all(result.table["n_fit_points"] >= 3)
    assert result.provenance["automatic_parameter_selection"] is False
    assert result.provenance["automatic_fit_interval_selection"] is False
    assert "not a probability" in result.provenance["positive_fraction_interpretation"]

    exponent = result.summary_table.set_index("metric").loc["exponent"]
    assert exponent["n_specifications"] == 8
    assert 0 <= exponent["positive_specification_fraction"] <= 1

    report = kantz_parameter_sensitivity_reporting_text(result)
    assert "Kantz local-divergence sensitivity" in report
    assert "not sampling uncertainty or a probability of deterministic chaos" in report
    assert "No radius" in report
    assert (
        exponent["n_positive"]
        + exponent["n_negative"]
        + exponent["n_exact_zero"]
        == exponent["n_finite"]
    )


def test_lyapunov_sensitivity_fails_entire_grid_for_invalid_fit_interval():
    data = _logistic_set(300)
    with pytest.raises(ValueError, match="LLE sensitivity fit failed"):
        lyapunov_parameter_sensitivity(
            data,
            curve=0,
            dimensions=("x",),
            embedding_dimensions=(2,),
            delays=(1,),
            theiler_windows=(5,),
            fit_intervals=((1, 2),),
            max_horizon=6,
        )


def test_sensitivity_plots_require_explicit_one_parameter_slice():
    data = _logistic_set(460)
    rqa = rqa_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2, 3),
        delays=(1,),
        radii=(0.05, 0.10),
        theiler_windows=(2,),
        min_diagonal_lengths=(2,),
        min_vertical_lengths=(2,),
    )
    with pytest.raises(ValueError, match="No averaging"):
        plot_rqa_sensitivity(
            rqa,
            parameter="requested_radius",
            metric="determinism",
        )
    ax = plot_rqa_sensitivity(
        rqa,
        parameter="requested_radius",
        metric="determinism",
        filters={
            "embedding_dimension": 2,
            "requested_delay": 1.0,
            "requested_theiler_window": 2.0,
            "min_diagonal_length": 2,
            "min_vertical_length": 2,
        },
    )
    assert "RQA parameter sensitivity" in ax.get_title()

    lle = lyapunov_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2, 3),
        delays=(1,),
        theiler_windows=(6,),
        fit_intervals=((1, 4),),
        max_horizon=7,
    )
    ax2 = plot_lyapunov_sensitivity(
        lle,
        parameter="embedding_dimension",
        filters={
            "requested_delay": 1.0,
            "requested_theiler_window": 6.0,
            "requested_fit_start": 1.0,
            "requested_fit_end": 4.0,
        },
    )
    assert "Rosenstein sensitivity" in ax2.get_title()
    plt.close("all")


def test_kantz_parameter_sensitivity_evaluates_declared_cartesian_grid():
    data = _logistic_set(560)
    result = kantz_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        radii=(0.05, 0.08),
        min_neighbors=(1, 2),
        theiler_windows=(6,),
        fit_intervals=((1, 4), (2, 5)),
        max_horizon=8,
    )

    assert result.n_specifications == 8
    assert result.exponent_unit == "1/s"
    assert result.table["specification_id"].is_unique
    assert set(result.table["requested_radius"]) == {0.05, 0.08}
    assert set(result.table["min_neighbors"]) == {1, 2}
    assert np.all(np.isfinite(result.table["exponent"]))
    assert np.all(result.table["minimum_reference_count_in_fit"] > 0)
    assert np.all(result.table["minimum_pair_count_in_fit"] > 0)
    assert np.all(
        (result.table["initial_supported_reference_fraction"] > 0)
        & (result.table["initial_supported_reference_fraction"] <= 1)
    )
    assert result.provenance["automatic_parameter_selection"] is False
    assert result.provenance["automatic_radius_selection"] is False
    assert result.provenance["automatic_fit_interval_selection"] is False
    assert result.provenance["failed_specification_policy"] == "raise_entire_analysis"
    assert "not a probability" in result.provenance["positive_fraction_interpretation"]

    exponent = result.summary_table.set_index("metric").loc["exponent"]
    assert exponent["n_specifications"] == 8
    assert 0 <= exponent["positive_specification_fraction"] <= 1


def test_kantz_sensitivity_fails_entire_grid_for_unsupported_neighborhood():
    data = _logistic_set(360)
    with pytest.raises(ValueError, match="Kantz sensitivity divergence failed"):
        kantz_parameter_sensitivity(
            data,
            curve=0,
            dimensions=("x",),
            embedding_dimensions=(2,),
            delays=(1,),
            radii=(1e-12,),
            min_neighbors=(5,),
            theiler_windows=(6,),
            fit_intervals=((1, 4),),
            max_horizon=7,
        )


def test_kantz_sensitivity_rejects_duplicate_radius_and_min_neighbor_grids():
    data = _logistic_set(360)
    common = dict(
        trajectories=data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        theiler_windows=(6,),
        fit_intervals=((1, 4),),
        max_horizon=7,
    )
    with pytest.raises(ValueError, match="radii must not contain duplicate"):
        kantz_parameter_sensitivity(
            **common,
            radii=(0.05, 0.05),
            min_neighbors=(2,),
        )
    with pytest.raises(ValueError, match="min_neighbors must not contain duplicate"):
        kantz_parameter_sensitivity(
            **common,
            radii=(0.05,),
            min_neighbors=(2, 2),
        )


def test_kantz_sensitivity_plot_requires_explicit_one_parameter_slice():
    data = _logistic_set(520)
    result = kantz_parameter_sensitivity(
        data,
        curve=0,
        dimensions=("x",),
        embedding_dimensions=(2,),
        delays=(1,),
        radii=(0.05, 0.08),
        min_neighbors=(1, 2),
        theiler_windows=(6,),
        fit_intervals=((1, 4),),
        max_horizon=7,
    )
    with pytest.raises(ValueError, match="No averaging"):
        plot_kantz_sensitivity(
            result,
            parameter="requested_radius",
        )
    ax = plot_kantz_sensitivity(
        result,
        parameter="radius",
        filters={
            "embedding_dimension": 2,
            "requested_delay": 1.0,
            "min_neighbors": 2,
            "requested_theiler_window": 6.0,
            "requested_fit_start": 1.0,
            "requested_fit_end": 4.0,
        },
    )
    assert "Kantz sensitivity" in ax.get_title()
    plt.close(ax.figure)


def test_sensitivity_grid_validation_rejects_duplicates_and_unknown_dimensions():
    data = _logistic_set()
    with pytest.raises(ValueError, match="duplicate"):
        rqa_parameter_sensitivity(
            data,
            curve=0,
            dimensions=("x",),
            embedding_dimensions=(2,),
            delays=(1, 1.0),
            radii=(0.1,),
            theiler_windows=(2,),
            min_diagonal_lengths=(2,),
            min_vertical_lengths=(2,),
        )
    with pytest.raises(KeyError, match="Unknown trajectory dimensions"):
        lyapunov_parameter_sensitivity(
            data,
            curve=0,
            dimensions=("y",),
            embedding_dimensions=(2,),
            delays=(1,),
            theiler_windows=(5,),
            fit_intervals=((1, 4),),
            max_horizon=6,
        )
