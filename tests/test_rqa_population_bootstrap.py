import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    bootstrap_rqa_metric_means,
    plot_rqa_metric_mean_bootstrap,
    rqa_metric_mean_bootstrap_reporting_text,
)


def _repeated_sine_sample():
    time = np.arange(120, dtype=float) * 0.01
    values = []
    participants = []
    for participant_index in range(6):
        for trial_index in range(2):
            phase = 0.12 * participant_index + 0.05 * trial_index
            signal = np.sin(2.0 * np.pi * 2.0 * time + phase)
            values.append(signal[:, None])
            participants.append(f"P{participant_index + 1:02d}")
    return TrajectorySet(
        time=time,
        values=np.asarray(values, dtype=float),
        curve_ids=tuple(f"c{index + 1:02d}" for index in range(len(values))),
        dimension_names=("x",),
        metadata=pd.DataFrame({"participant_id": participants}),
        time_unit="s",
        coordinate_system="normalized",
        provenance={"fixture": "repeated sine"},
    )


def test_curve_level_rqa_bootstrap_is_reproducible_and_ordered():
    data = _repeated_sine_sample()
    first = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("recurrence_rate", "determinism", "laminarity"),
        radius=0.18,
        theiler_window=2,
        n_bootstrap=300,
        random_state=17,
    )
    second = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("recurrence_rate", "determinism", "laminarity"),
        radius=0.18,
        theiler_window=2,
        n_bootstrap=300,
        random_state=17,
    )

    assert first.n_units == data.n_curves
    assert first.unit == "curve"
    assert len(first.observed_table) == data.n_curves
    assert len(first.bootstrap_table) == 300
    assert np.all(first.summary_table["lower"] <= first.summary_table["upper"])
    assert np.all(np.isfinite(first.summary_table["mean"]))
    assert np.all(np.isfinite(first.summary_table["bootstrap_standard_error"]))
    pd.testing.assert_frame_equal(first.bootstrap_table, second.bootstrap_table)
    pd.testing.assert_frame_equal(first.summary_table, second.summary_table)
    assert first.provenance["within_single_trajectory_uncertainty"] is False
    assert first.provenance["curve_level_rqa_recomputed_per_bootstrap_draw"] is False
    assert first.provenance["undefined_metric_policy"] == "raise_entire_analysis"


def test_participant_bootstrap_uses_equal_weight_participant_metric_means():
    time = np.arange(120, dtype=float)
    values = np.stack(
        [
            np.zeros(120),
            np.zeros(120),
            np.zeros(120),
            np.linspace(0.0, 10.0, 120),
        ],
        axis=0,
    )[:, :, None]
    data = TrajectorySet(
        time=time,
        values=values,
        curve_ids=("A1", "A2", "A3", "B1"),
        dimension_names=("x",),
        metadata=pd.DataFrame(
            {"participant_id": ["A", "A", "A", "B"]}
        ),
        time_unit="samples",
        coordinate_system="normalized",
    )

    result = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("recurrence_rate",),
        radius=0.1,
        unit="participant",
        participant_column="participant_id",
        n_bootstrap=200,
        random_state=5,
    )

    assert result.n_units == 2
    assert result.unit_ids == ("A", "B")
    assert list(result.unit_table["n_curves"]) == [3, 1]

    participant_mean = float(result.unit_table["recurrence_rate"].mean())
    curve_mean = float(result.observed_table["recurrence_rate"].mean())
    reported = float(
        result.summary_table.loc[
            result.summary_table["metric"] == "recurrence_rate",
            "mean",
        ].iloc[0]
    )
    assert reported == pytest.approx(participant_mean)
    assert reported != pytest.approx(curve_mean)
    assert (
        result.provenance["estimand"]
        == "equal_weight_mean_of_participant_average_curve_level_rqa_metrics"
    )
    assert result.provenance["within_participant_trial_resampling"] is False


def test_target_rr_rejects_recurrence_rate_as_bootstrap_outcome():
    data = _repeated_sine_sample()
    with pytest.raises(ValueError, match="controlled by target_recurrence_rate"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("recurrence_rate", "determinism"),
            target_recurrence_rate=0.08,
            n_bootstrap=100,
        )


def test_target_rr_bootstrap_retains_resolved_curve_specific_radii():
    data = _repeated_sine_sample()
    result = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("determinism", "laminarity"),
        target_recurrence_rate=0.08,
        theiler_window=2,
        n_bootstrap=120,
        random_state=9,
    )

    assert result.provenance["threshold_policy"] == "target_recurrence_rate"
    assert np.all(np.isfinite(result.observed_table["resolved_radius"]))
    assert np.all(
        np.abs(result.observed_table["achieved_recurrence_rate"] - 0.08) < 0.02
    )


def test_undefined_selected_metric_fails_instead_of_dropping_curve():
    time = np.arange(40, dtype=float)
    values = np.stack(
        [
            np.arange(40, dtype=float),
            np.arange(40, dtype=float) + 100.0,
        ],
        axis=0,
    )[:, :, None]
    data = TrajectorySet(
        time=time,
        values=values,
        curve_ids=("a", "b"),
        dimension_names=("x",),
        time_unit="samples",
        coordinate_system="normalized",
    )

    with pytest.raises(ValueError, match="undefined for curve"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=1e-12,
            n_bootstrap=100,
        )


def test_embedding_contract_is_retained_in_bootstrap_provenance():
    data = _repeated_sine_sample()
    result = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("determinism",),
        radius=0.2,
        embedding_dimension=2,
        delay=2,
        theiler_window=3,
        n_bootstrap=100,
        random_state=3,
    )

    assert result.provenance["state_representation"] == "delay_embedding"
    assert result.provenance["embedding_dimension"] == 2
    assert result.provenance["delay_samples"] == 2
    assert result.provenance["parameter_selection_uncertainty_included"] is False


def test_rqa_bootstrap_control_and_design_errors():
    data = _repeated_sine_sample()

    with pytest.raises(ValueError, match="exactly one"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="exactly one"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            target_recurrence_rate=0.05,
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="confidence_level"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            confidence_level=1.0,
            n_bootstrap=100,
        )
    with pytest.raises(TypeError, match="integer"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            n_bootstrap=True,
        )
    with pytest.raises(ValueError, match="at least 100"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            n_bootstrap=99,
        )
    with pytest.raises(ValueError, match="unit must be"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            unit="trial",
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="participant_column is required"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            unit="participant",
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="must be None"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            unit="curve",
            participant_column="participant_id",
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="delay must be None"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            delay=2,
            n_bootstrap=100,
        )
    with pytest.raises(ValueError, match="delay is required"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            embedding_dimension=2,
            n_bootstrap=100,
        )


def test_participant_metadata_errors_are_explicit():
    data = _repeated_sine_sample()
    with pytest.raises(ValueError, match="does not contain"):
        bootstrap_rqa_metric_means(
            data,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            unit="participant",
            participant_column="missing",
            n_bootstrap=100,
        )

    metadata = data.metadata.reset_index(drop=True).copy()
    metadata.loc[0, "participant_id"] = np.nan
    missing = TrajectorySet(
        time=data.time,
        values=data.values,
        curve_ids=data.curve_ids,
        dimension_names=data.dimension_names,
        metadata=metadata,
        coordinate_system=data.coordinate_system,
        time_unit=data.time_unit,
        provenance=data.provenance,
    )
    with pytest.raises(ValueError, match="missing values"):
        bootstrap_rqa_metric_means(
            missing,
            dimensions=("x",),
            metrics=("determinism",),
            radius=0.2,
            unit="participant",
            participant_column="participant_id",
            n_bootstrap=100,
        )


def test_rqa_bootstrap_plot_and_reporting_are_explicit_about_scope():
    data = _repeated_sine_sample()
    result = bootstrap_rqa_metric_means(
        data,
        dimensions=("x",),
        metrics=("determinism", "laminarity"),
        radius=0.18,
        unit="participant",
        participant_column="participant_id",
        n_bootstrap=150,
        random_state=12,
    )

    ax = plot_rqa_metric_mean_bootstrap(result)
    assert "RQA population mean" in ax.get_title()

    text = rqa_metric_mean_bootstrap_reporting_text(result)
    assert "participant" in text
    assert "percentile bootstrap" in text
    assert "within-single-trajectory" in text
    plt.close("all")
