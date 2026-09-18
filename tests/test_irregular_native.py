import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import (
    IrregularTrajectorySet,
    common_overlap_interval,
    from_irregular_long_dataframe_native,
    irregular_sampling_summary,
    make_common_grid,
    resample_irregular_to_common_grid,
    resample_irregular_to_grid,
)


def irregular_frame():
    return pd.DataFrame(
        {
            "participant_id": ["P1"] * 3 + ["P2"] * 4,
            "trial_id": [1] * 7,
            "time": [0.0, 0.2, 0.8, 0.1, 0.3, 0.7, 0.9],
            "x": [0.1, 0.2, 0.7, 0.2, 0.3, 0.6, 0.8],
            "y": [0.5, 0.45, 0.2, 0.55, 0.5, 0.25, 0.2],
            "condition": ["A"] * 3 + ["B"] * 4,
        }
    )


def test_native_irregular_representation_preserves_grids():
    x = from_irregular_long_dataframe_native(
        irregular_frame(),
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
        metadata_columns=["condition"],
        coordinate_system="normalized",
        time_unit="s",
    )
    assert isinstance(x, IrregularTrajectorySet)
    assert x.n_curves == 2
    assert x.n_dimensions == 2
    assert np.array_equal(x.sample_counts, [3, 4])
    assert np.array_equal(x.time[0], [0.0, 0.2, 0.8])
    assert np.array_equal(x.time[1], [0.1, 0.3, 0.7, 0.9])
    assert list(x.metadata["condition"]) == ["A", "B"]
    assert len(x.dimension("x")) == 2
    assert x.subset([1]).curve_ids == ("P2|1",)


def test_sampling_summary_and_overlap():
    x = from_irregular_long_dataframe_native(
        irregular_frame(),
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
    )
    summary = irregular_sampling_summary(x)
    assert list(summary["n_samples"]) == [3, 4]
    assert common_overlap_interval(x) == pytest.approx((0.1, 0.8))
    grid = make_common_grid(x, n_time=8, domain="overlap")
    assert grid[0] == pytest.approx(0.1)
    assert grid[-1] == pytest.approx(0.8)


def test_union_grid_keeps_edge_missingness():
    x = from_irregular_long_dataframe_native(
        irregular_frame(),
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
    )
    grid = make_common_grid(x, n_time=10, domain="union")
    projected = resample_irregular_to_grid(x, grid)
    assert np.isnan(projected.values[0, -1]).all()
    assert np.isnan(projected.values[1, 0]).all()


def test_overlap_projection_is_explicit_and_complete_for_dense_examples():
    x = from_irregular_long_dataframe_native(
        irregular_frame(),
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
    )
    projected = resample_irregular_to_common_grid(
        x,
        n_time=9,
        domain="overlap",
        method="linear",
    )
    assert projected.values.shape == (2, 9, 2)
    assert np.isfinite(projected.values).all()
    assert projected.provenance["irregular_to_grid"]["n_time"] == 9


def test_max_gap_retains_unobserved_interval():
    frame = irregular_frame()
    x = from_irregular_long_dataframe_native(
        frame,
        curve_columns=["participant_id", "trial_id"],
        time_column="time",
    )
    grid = np.linspace(0.1, 0.8, 15)
    projected = resample_irregular_to_grid(x, grid, max_gap=0.25)
    assert np.isnan(projected.values[0]).any()


def test_native_irregular_input_contracts():
    frame = irregular_frame()
    duplicate = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate time"):
        from_irregular_long_dataframe_native(
            duplicate,
            curve_columns=["participant_id", "trial_id"],
            time_column="time",
        )
    with pytest.raises(ValueError):
        from_irregular_long_dataframe_native(
            frame,
            curve_columns=[],
            time_column="time",
        )
    with pytest.raises(ValueError):
        make_common_grid(
            from_irregular_long_dataframe_native(
                frame,
                curve_columns=["participant_id", "trial_id"],
                time_column="time",
            ),
            n_time=1,
        )
    with pytest.raises(ValueError):
        make_common_grid(
            from_irregular_long_dataframe_native(
                frame,
                curve_columns=["participant_id", "trial_id"],
                time_column="time",
            ),
            n_time=5,
            domain="bad",
        )


def test_irregular_type_rejects_mismatched_shapes_and_nonoverlap():
    with pytest.raises(ValueError):
        IrregularTrajectorySet(
            time=(np.array([0.0, 1.0]),),
            values=(np.zeros((3, 2)),),
            curve_ids=("a",),
            dimension_names=("x", "y"),
        )
    no_overlap = IrregularTrajectorySet(
        time=(np.array([0.0, 0.5]), np.array([0.6, 1.0])),
        values=(np.zeros((2, 1)), np.zeros((2, 1))),
        curve_ids=("a", "b"),
        dimension_names=("x",),
    )
    with pytest.raises(ValueError, match="common time interval"):
        common_overlap_interval(no_overlap)
