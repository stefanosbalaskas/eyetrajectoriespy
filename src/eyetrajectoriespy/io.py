"""Input adapters for continuous gaze trajectories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from .types import TrajectorySet


def from_long_dataframe(
    data: pd.DataFrame,
    *,
    curve_columns: Sequence[str],
    time_column: str,
    value_columns: Sequence[str] = ("x", "y"),
    metadata_columns: Sequence[str] | None = None,
    coordinate_system: str = "unknown",
    time_unit: str = "unknown",
    require_common_grid: bool = True,
    provenance: dict[str, Any] | None = None,
) -> TrajectorySet:
    """Create a :class:`TrajectorySet` from long-format gaze samples.

    The function does not interpolate, smooth, impute, average duplicate time
    points, or normalize time. Such operations must be requested explicitly.

    Parameters
    ----------
    data:
        Long-format dataframe containing one row per gaze sample.
    curve_columns:
        Columns identifying a trajectory, typically ``("participant_id",
        "trial_id")``.
    time_column:
        Sample-time column.
    value_columns:
        Functional channels. For continuous planar gaze this is usually
        ``("x", "y")``.
    metadata_columns:
        Curve-constant columns to preserve. If a requested metadata column
        varies within a curve, an error is raised.
    require_common_grid:
        If ``True``, all trajectories must contain the same time grid. If
        ``False``, use :func:`eyetrajectoriespy.resample_to_grid` after
        constructing curve-specific data with another adapter; the canonical
        :class:`TrajectorySet` itself always uses a common grid.
    """

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    curve_columns = tuple(curve_columns)
    value_columns = tuple(value_columns)
    metadata_columns = tuple(metadata_columns or ())
    required = set(curve_columns) | {time_column} | set(value_columns) | set(metadata_columns)
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not curve_columns:
        raise ValueError("curve_columns must contain at least one identifier")
    if not value_columns:
        raise ValueError("value_columns must contain at least one functional dimension")

    work = data.loc[:, list(required)].copy()
    if work[list(curve_columns) + [time_column]].isna().any().any():
        raise ValueError("curve identifiers and time values cannot be missing")

    grouped = work.groupby(list(curve_columns), sort=False, dropna=False)
    curves: list[np.ndarray] = []
    ids: list[str] = []
    grids: list[np.ndarray] = []
    metadata_rows: list[dict[str, Any]] = []

    for key, frame in grouped:
        frame = frame.sort_values(time_column, kind="stable")
        times = frame[time_column].to_numpy(dtype=float)
        if len(np.unique(times)) != len(times):
            raise ValueError(f"Duplicate time points within curve {key!r}; resolve them explicitly")
        if not np.all(np.diff(times) > 0):
            raise ValueError(f"Time must be strictly increasing within curve {key!r}")
        grid = times
        values = frame[list(value_columns)].to_numpy(dtype=float)
        grids.append(grid)
        curves.append(values)
        key_tuple = key if isinstance(key, tuple) else (key,)
        ids.append("|".join(str(part) for part in key_tuple))

        row = dict(zip(curve_columns, key_tuple, strict=True))
        for column in metadata_columns:
            unique = frame[column].drop_duplicates()
            if len(unique) > 1:
                raise ValueError(f"Metadata column {column!r} varies within curve {key!r}")
            row[column] = unique.iloc[0] if len(unique) else np.nan
        metadata_rows.append(row)

    if not curves:
        raise ValueError("No trajectories were found")
    reference = grids[0]
    common = all(np.array_equal(reference, grid) for grid in grids[1:])
    if not common:
        if require_common_grid:
            raise ValueError(
                "Trajectories do not share a common time grid. Resample explicitly before creating a TrajectorySet."
            )
        raise ValueError(
            "TrajectorySet requires a common grid; use from_irregular_long_dataframe() to resample explicitly."
        )

    return TrajectorySet(
        time=reference,
        values=np.stack(curves, axis=0),
        curve_ids=tuple(ids),
        dimension_names=tuple(value_columns),
        metadata=pd.DataFrame(metadata_rows),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
        provenance={
            "source": "long_dataframe",
            "curve_columns": list(curve_columns),
            "time_column": time_column,
            "value_columns": list(value_columns),
            **(provenance or {}),
        },
    )


def from_irregular_long_dataframe(
    data: pd.DataFrame,
    *,
    curve_columns: Sequence[str],
    time_column: str,
    value_columns: Sequence[str] = ("x", "y"),
    grid: np.ndarray,
    metadata_columns: Sequence[str] | None = None,
    method: str = "linear",
    max_gap: float | None = None,
    coordinate_system: str = "unknown",
    time_unit: str = "unknown",
) -> TrajectorySet:
    """Create a common-grid trajectory set from irregular long-format samples.

    Resampling is explicit and gap-limited. Values outside each curve's
    observed domain remain missing rather than being extrapolated.
    """

    from .preprocessing import _resample_single_curve

    grid = np.asarray(grid, dtype=float)
    if grid.ndim != 1 or len(grid) < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("grid must be a strictly increasing one-dimensional array")

    curve_columns = tuple(curve_columns)
    value_columns = tuple(value_columns)
    metadata_columns = tuple(metadata_columns or ())
    required = set(curve_columns) | {time_column} | set(value_columns) | set(metadata_columns)
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    curves: list[np.ndarray] = []
    ids: list[str] = []
    metadata_rows: list[dict[str, Any]] = []
    grouped = data.groupby(list(curve_columns), sort=False, dropna=False)
    for key, frame in grouped:
        frame = frame.sort_values(time_column, kind="stable")
        times = frame[time_column].to_numpy(dtype=float)
        if len(np.unique(times)) != len(times):
            raise ValueError(f"Duplicate time points within curve {key!r}; resolve them explicitly")
        values = frame[list(value_columns)].to_numpy(dtype=float)
        resampled = _resample_single_curve(times, values, grid, method=method, max_gap=max_gap)
        curves.append(resampled)
        key_tuple = key if isinstance(key, tuple) else (key,)
        ids.append("|".join(str(part) for part in key_tuple))
        row = dict(zip(curve_columns, key_tuple, strict=True))
        for column in metadata_columns:
            unique = frame[column].drop_duplicates()
            if len(unique) > 1:
                raise ValueError(f"Metadata column {column!r} varies within curve {key!r}")
            row[column] = unique.iloc[0] if len(unique) else np.nan
        metadata_rows.append(row)

    return TrajectorySet(
        time=grid,
        values=np.stack(curves),
        curve_ids=tuple(ids),
        dimension_names=value_columns,
        metadata=pd.DataFrame(metadata_rows),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
        provenance={
            "source": "irregular_long_dataframe",
            "resampling_method": method,
            "max_gap": max_gap,
        },
    )
