import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    cross_recurrence_matrix,
    cross_rqa_metrics,
    recurrence_matrix,
    rqa_metrics,
    windowed_rqa,
)


def _scalar(values, *, curve_id="c1"):
    values = np.asarray(values, dtype=float)
    return TrajectorySet(
        time=np.arange(values.size, dtype=float),
        values=values[None, :, None],
        curve_ids=(curve_id,),
        dimension_names=("x",),
        time_unit="samples",
        coordinate_system="arbitrary",
    )


def test_sparse_recurrence_matrix_matches_hand_count():
    data = _scalar([0.0, 0.1, 1.0, 0.05])
    result = recurrence_matrix(data, curve=0, radius=0.15, dimensions=("x",))

    assert result.matrix.shape == (4, 4)
    assert result.matrix.nnz == 6
    assert result.achieved_recurrence_rate == pytest.approx(3 / 6)
    assert result.provenance["sparse"] is True
    assert not result.matrix.diagonal().any()


def test_recurrence_requires_exactly_one_radius_policy():
    data = _scalar([0, 1, 0, 1, 0])
    with pytest.raises(ValueError, match="exactly one"):
        recurrence_matrix(data, curve=0, dimensions=("x",))
    with pytest.raises(ValueError, match="exactly one"):
        recurrence_matrix(
            data,
            curve=0,
            radius=0.1,
            target_recurrence_rate=0.2,
            dimensions=("x",),
        )


def test_target_recurrence_rate_policy_is_explicit_and_sparse():
    data = _scalar(np.sin(np.linspace(0, 8 * np.pi, 200)))
    result = recurrence_matrix(
        data,
        curve=0,
        target_recurrence_rate=0.08,
        theiler_window=2,
        dimensions=("x",),
    )
    assert result.target_recurrence_rate == pytest.approx(0.08)
    assert 0.05 <= result.achieved_recurrence_rate <= 0.11
    assert result.radius > 0


def test_rqa_detects_repeated_diagonal_structure():
    data = _scalar([0, 1, 0, 1, 0])
    recurrence = recurrence_matrix(data, curve=0, radius=1e-8, dimensions=("x",))
    result = rqa_metrics(
        recurrence,
        min_diagonal_length=2,
        min_vertical_length=2,
    )

    assert result.recurrence_rate > 0
    assert result.determinism > 0
    assert result.max_diagonal_length >= 3
    assert 0 <= result.center_of_recurrence_mass <= 100


def test_cross_recurrence_and_cross_rqa():
    a = _scalar([0, 1, 0, 1, 0], curve_id="a")
    b = _scalar([1, 0, 1, 0, 1], curve_id="b")
    recurrence = cross_recurrence_matrix(
        a,
        b,
        curve_a=0,
        curve_b=0,
        radius=1e-8,
        dimensions_a=("x",),
        dimensions_b=("x",),
    )
    metrics = cross_rqa_metrics(recurrence)
    assert recurrence.kind == "cross"
    assert recurrence.matrix.shape == (5, 5)
    assert metrics.recurrence_rate > 0
    assert np.isnan(metrics.center_of_recurrence_mass)


def test_windowed_rqa_reports_tail_instead_of_silently_dropping_it():
    data = _scalar(np.sin(np.linspace(0, 8 * np.pi, 23)))
    result = windowed_rqa(
        data,
        curve=0,
        window=10,
        step=6,
        radius=0.5,
        min_diagonal_length=2,
        min_vertical_length=2,
        dimensions=("x",),
    )
    assert len(result.table) == 3
    assert result.dropped_tail_samples == 1
    assert result.provenance["tail_policy"].startswith("full_windows_only")


def test_theiler_window_can_remove_all_pairs_explicitly():
    data = _scalar([0, 1, 2, 3])
    with pytest.raises(ValueError, match="no eligible recurrence pairs"):
        recurrence_matrix(data, curve=0, radius=1.0, theiler_window=3, dimensions=("x",))


def test_raw_recurrence_requires_explicit_dimensions():
    data = _scalar([0, 1, 0, 1, 0])
    with pytest.raises(ValueError, match="dimensions must be supplied explicitly"):
        recurrence_matrix(data, curve=0, radius=0.2)


def test_windowed_rqa_rejects_internal_gaps_between_windows():
    data = _scalar(np.sin(np.linspace(0, 6 * np.pi, 50)))
    with pytest.raises(ValueError, match="step cannot exceed window"):
        windowed_rqa(
            data,
            curve=0,
            window=10,
            step=11,
            radius=0.5,
            dimensions=("x",),
        )


def test_cross_recurrence_rejects_coordinate_semantic_mismatch():
    a = _scalar([0, 1, 0, 1, 0], curve_id="a")
    b = TrajectorySet(
        time=a.time,
        values=a.values.copy(),
        curve_ids=("b",),
        dimension_names=("x",),
        time_unit="samples",
        coordinate_system="different",
    )
    with pytest.raises(ValueError, match="coordinate_system"):
        cross_recurrence_matrix(
            a,
            b,
            curve_a=0,
            curve_b=0,
            radius=0.1,
            dimensions_a=("x",),
            dimensions_b=("x",),
        )


def test_cross_recurrence_rejects_different_named_state_variables():
    time = np.arange(5, dtype=float)
    a = TrajectorySet(
        time=time,
        values=np.arange(5, dtype=float)[None, :, None],
        curve_ids=("a",),
        dimension_names=("x",),
        time_unit="samples",
        coordinate_system="normalized",
    )
    b = TrajectorySet(
        time=time,
        values=np.arange(5, dtype=float)[None, :, None],
        curve_ids=("b",),
        dimension_names=("pupil",),
        time_unit="samples",
        coordinate_system="normalized",
    )
    with pytest.raises(ValueError, match="same named state variables"):
        cross_recurrence_matrix(
            a,
            b,
            curve_a=0,
            curve_b=0,
            radius=0.1,
            dimensions_a=("x",),
            dimensions_b=("pupil",),
        )

def test_spatial_recurrence_allows_irregular_grid_but_line_rqa_fails_closed():
    time = np.array([0.0, 1.0, 2.2, 3.1, 4.7])
    values = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    data = TrajectorySet(
        time=time,
        values=values[None, :, None],
        curve_ids=("irregular",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
    )

    recurrence = recurrence_matrix(
        data,
        curve=0,
        radius=1e-8,
        dimensions=("x",),
    )
    assert recurrence.achieved_recurrence_rate > 0

    with pytest.raises(ValueError, match="regular first time/index grid"):
        rqa_metrics(recurrence)


def test_cross_rqa_requires_matching_regular_sampling_steps():
    values_a = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    values_b = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
    a = TrajectorySet(
        time=np.arange(5, dtype=float),
        values=values_a[None, :, None],
        curve_ids=("a",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
    )
    b = TrajectorySet(
        time=np.arange(5, dtype=float) * 2.0,
        values=values_b[None, :, None],
        curve_ids=("b",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="arbitrary",
    )

    recurrence = cross_recurrence_matrix(
        a,
        b,
        curve_a=0,
        curve_b=0,
        radius=1e-8,
        dimensions_a=("x",),
        dimensions_b=("x",),
    )
    assert recurrence.matrix.nnz > 0

    with pytest.raises(ValueError, match="matching sampling steps"):
        cross_rqa_metrics(recurrence)

