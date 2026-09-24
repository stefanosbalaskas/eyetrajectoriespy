from dataclasses import replace

from scipy.sparse import triu

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    JointRecurrenceResult,
    TrajectorySet,
    cross_recurrence_matrix,
    joint_recurrence_component_frame,
    joint_recurrence_matrix,
    joint_recurrence_reporting_text,
    joint_rqa_metrics,
    plot_joint_recurrence,
    recurrence_matrix,
)


def _synchronized_recurrences():
    time = np.arange(80, dtype=float) * 0.02
    phase = 2.0 * np.pi * time / 0.40

    position = TrajectorySet(
        time=time,
        values=np.sin(phase)[None, :, None],
        curve_ids=("trial",),
        dimension_names=("x",),
        coordinate_system="unknown",
        time_unit="s",
    )
    physiology = TrajectorySet(
        time=time,
        values=np.stack(
            [
                np.cos(phase),
                0.6 * np.cos(phase) + 0.2 * np.sin(2.0 * phase),
            ],
            axis=1,
        )[None, :, :],
        curve_ids=("trial",),
        dimension_names=("eda", "pupil"),
        coordinate_system="unknown",
        time_unit="s",
    )

    position_rec = recurrence_matrix(
        position,
        curve=0,
        target_recurrence_rate=0.20,
        metric="euclidean",
        theiler_window=2,
        dimensions=("x",),
    )
    physiology_rec = recurrence_matrix(
        physiology,
        curve=0,
        target_recurrence_rate=0.25,
        metric="chebyshev",
        theiler_window=2,
        dimensions=("eda", "pupil"),
    )
    return position_rec, physiology_rec


def test_joint_recurrence_is_exact_sparse_intersection():
    position_rec, physiology_rec = _synchronized_recurrences()

    result = joint_recurrence_matrix(
        (position_rec, physiology_rec),
        labels=("position", "physiology"),
    )

    assert isinstance(result, JointRecurrenceResult)
    assert result.n_components == 2
    assert result.component_labels == ("position", "physiology")
    assert result.shape == position_rec.shape
    assert result.theiler_window_samples == 2

    expected = position_rec.matrix.multiply(
        physiology_rec.matrix
    ).astype(bool).tocsr()
    expected.eliminate_zeros()
    difference = result.matrix != expected
    assert difference.nnz == 0

    upper_pairs = int(triu(result.matrix, k=1).nnz)
    assert result.n_joint_recurrent_pairs == upper_pairs
    assert result.joint_recurrence_rate == pytest.approx(
        upper_pairs / result.eligible_pair_count
    )
    assert result.joint_recurrence_rate <= (
        position_rec.achieved_recurrence_rate + 1e-12
    )
    assert result.joint_recurrence_rate <= (
        physiology_rec.achieved_recurrence_rate + 1e-12
    )

    provenance = result.provenance
    assert provenance["resampling"] is False
    assert provenance["lag_shift"] is False
    assert provenance["threshold_harmonization"] is False
    assert provenance["automatic_threshold_selection"] is False
    assert provenance["component_state_dimensions"] == [1, 2]


def test_joint_recurrence_component_frame_and_rqa_contract():
    position_rec, physiology_rec = _synchronized_recurrences()
    result = joint_recurrence_matrix(
        (position_rec, physiology_rec),
        labels=("position", "physiology"),
    )

    frame = joint_recurrence_component_frame(result)
    assert list(frame["label"]) == ["position", "physiology"]
    assert list(frame["metric"]) == ["euclidean", "chebyshev"]
    assert list(frame["state_dimension"]) == [1, 2]
    assert np.all(frame["theiler_window_samples"] == 2)

    metrics = joint_rqa_metrics(
        result,
        min_diagonal_length=2,
        min_vertical_length=2,
    )
    assert metrics.recurrence_rate == pytest.approx(
        result.joint_recurrence_rate
    )
    assert metrics.provenance["operation"] == "joint_rqa_metrics"
    assert np.isfinite(metrics.determinism)
    assert 0.0 <= metrics.determinism <= 1.0

    text = joint_recurrence_reporting_text(result, metrics)
    assert "logical intersection" in text
    assert "not as cross-recurrence" in text
    assert "No resampling" in text


def test_joint_recurrence_plot_is_sparse_and_auditable():
    position_rec, physiology_rec = _synchronized_recurrences()
    result = joint_recurrence_matrix(
        (position_rec, physiology_rec),
        labels=("position", "physiology"),
    )
    ax = plot_joint_recurrence(result)
    assert "Joint recurrence" in ax.get_title()
    assert len(ax.collections) == 1
    plt.close(ax.figure)

    with pytest.raises(ValueError, match="exceeds max_points"):
        plot_joint_recurrence(
            result,
            max_points=max(1, result.matrix.nnz - 1),
        )


def test_joint_recurrence_rejects_cross_recurrence_and_misalignment():
    position_rec, physiology_rec = _synchronized_recurrences()

    with pytest.raises(ValueError, match="at least two"):
        joint_recurrence_matrix((position_rec,))

    cross = cross_recurrence_matrix(
        TrajectorySet(
            time=position_rec.time_a,
            values=np.sin(
                2.0 * np.pi * position_rec.time_a / 0.40
            )[None, :, None],
            curve_ids=("a",),
            dimension_names=("x",),
            coordinate_system="unknown",
            time_unit="s",
        ),
        TrajectorySet(
            time=position_rec.time_a,
            values=np.cos(
                2.0 * np.pi * position_rec.time_a / 0.40
            )[None, :, None],
            curve_ids=("b",),
            dimension_names=("x",),
            coordinate_system="unknown",
            time_unit="s",
        ),
        curve_a=0,
        curve_b=0,
        radius=0.4,
        dimensions_a=("x",),
        dimensions_b=("x",),
    )
    with pytest.raises(ValueError, match="auto-recurrence"):
        joint_recurrence_matrix((position_rec, cross))

    shifted = replace(
        physiology_rec,
        time_a=physiology_rec.time_a + 0.001,
        time_b=physiology_rec.time_b + 0.001,
    )
    with pytest.raises(ValueError, match="exact same time grid"):
        joint_recurrence_matrix((position_rec, shifted))

    filtered = physiology_rec.matrix.tolil(copy=True)
    for index in range(physiology_rec.matrix.shape[0] - 3):
        filtered[index, index + 3] = False
        filtered[index + 3, index] = False
    filtered = filtered.tocsr()
    filtered.eliminate_zeros()
    different_theiler = replace(
        physiology_rec,
        matrix=filtered,
        theiler_window_samples=3,
    )
    with pytest.raises(ValueError, match="same Theiler window"):
        joint_recurrence_matrix((position_rec, different_theiler))


    different_unit = replace(
        physiology_rec,
        time_unit="ms",
    )
    with pytest.raises(ValueError, match="same time_unit"):
        joint_recurrence_matrix((position_rec, different_unit))

    bad_diagonal = replace(
        physiology_rec,
        matrix=physiology_rec.matrix.copy(),
    )
    bad_diagonal.matrix[0, 0] = True
    with pytest.raises(ValueError, match="exclude the main diagonal"):
        joint_recurrence_matrix((position_rec, bad_diagonal))


def test_joint_recurrence_label_and_type_contracts_fail_closed():
    position_rec, physiology_rec = _synchronized_recurrences()

    with pytest.raises(TypeError, match="RecurrenceResult"):
        joint_recurrence_matrix((position_rec, object()))

    with pytest.raises(ValueError, match="exactly one"):
        joint_recurrence_matrix(
            (position_rec, physiology_rec),
            labels=("only_one",),
        )

    with pytest.raises(ValueError, match="unique"):
        joint_recurrence_matrix(
            (position_rec, physiology_rec),
            labels=("same", "same"),
        )

    with pytest.raises(TypeError, match="JointRecurrenceResult"):
        joint_recurrence_component_frame(object())
    with pytest.raises(TypeError, match="JointRecurrenceResult"):
        joint_rqa_metrics(object())
    with pytest.raises(TypeError, match="JointRecurrenceResult"):
        plot_joint_recurrence(object())
    with pytest.raises(TypeError, match="JointRecurrenceResult"):
        joint_recurrence_reporting_text(object())


def test_joint_rqa_preserves_regular_grid_requirement():
    position_rec, physiology_rec = _synchronized_recurrences()
    irregular_time = position_rec.time_a.copy()
    irregular_time[20:] += 0.003

    irregular_a = replace(
        position_rec,
        time_a=irregular_time,
        time_b=irregular_time,
    )
    irregular_b = replace(
        physiology_rec,
        time_a=irregular_time,
        time_b=irregular_time,
    )
    result = joint_recurrence_matrix(
        (irregular_a, irregular_b),
        labels=("position", "physiology"),
    )

    with pytest.raises(ValueError, match="approximately regular"):
        joint_rqa_metrics(result)
