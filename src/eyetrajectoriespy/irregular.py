"""Native irregularly sampled gaze trajectories and explicit common-grid projection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from .preprocessing import _resample_single_curve
from .types import IrregularTrajectorySet, TrajectorySet


def from_irregular_long_dataframe_native(
    data: pd.DataFrame,
    *,
    curve_columns: Sequence[str],
    time_column: str,
    value_columns: Sequence[str] = ("x", "y"),
    metadata_columns: Sequence[str] | None = None,
    coordinate_system: str = "unknown",
    time_unit: str = "unknown",
    provenance: dict[str, Any] | None = None,
) -> IrregularTrajectorySet:
    """Create an irregular trajectory set without resampling.

    Duplicate time points are rejected because their interpretation is
    experiment-specific. Functional values may contain missing observations;
    those remain missing and are not converted to zeros or interpolated.
    """

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    curve_columns = tuple(curve_columns)
    value_columns = tuple(value_columns)
    metadata_columns = tuple(metadata_columns or ())
    if not curve_columns:
        raise ValueError("curve_columns must contain at least one identifier")
    if not value_columns:
        raise ValueError("value_columns must contain at least one functional dimension")
    required = set(curve_columns) | {time_column} | set(value_columns) | set(metadata_columns)
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data[list(curve_columns) + [time_column]].isna().any().any():
        raise ValueError("curve identifiers and time values cannot be missing")

    times: list[np.ndarray] = []
    values: list[np.ndarray] = []
    ids: list[str] = []
    metadata_rows: list[dict[str, Any]] = []

    grouped = data.groupby(list(curve_columns), sort=False, dropna=False)
    for key, frame in grouped:
        frame = frame.sort_values(time_column, kind="stable")
        time = frame[time_column].to_numpy(dtype=float)
        if len(time) < 2:
            raise ValueError(f"Curve {key!r} contains fewer than two samples")
        if len(np.unique(time)) != len(time):
            raise ValueError(f"Duplicate time points within curve {key!r}; resolve them explicitly")
        if not np.all(np.diff(time) > 0):
            raise ValueError(f"Time must be strictly increasing within curve {key!r}")

        value = frame[list(value_columns)].to_numpy(dtype=float)
        key_tuple = key if isinstance(key, tuple) else (key,)
        ids.append("|".join(str(part) for part in key_tuple))
        times.append(time)
        values.append(value)

        row = dict(zip(curve_columns, key_tuple, strict=True))
        for column in metadata_columns:
            unique = frame[column].drop_duplicates()
            if len(unique) > 1:
                raise ValueError(f"Metadata column {column!r} varies within curve {key!r}")
            row[column] = unique.iloc[0] if len(unique) else np.nan
        metadata_rows.append(row)

    if not times:
        raise ValueError("No trajectories were found")

    return IrregularTrajectorySet(
        time=tuple(times),
        values=tuple(values),
        curve_ids=tuple(ids),
        dimension_names=tuple(value_columns),
        metadata=pd.DataFrame(metadata_rows),
        coordinate_system=coordinate_system,
        time_unit=time_unit,
        provenance={
            "source": "irregular_long_dataframe_native",
            "curve_columns": list(curve_columns),
            "time_column": time_column,
            "value_columns": list(value_columns),
            **(provenance or {}),
        },
    )


def common_overlap_interval(trajectories: IrregularTrajectorySet) -> tuple[float, float]:
    """Return the time interval observed by every curve."""

    start = max(float(time[0]) for time in trajectories.time)
    end = min(float(time[-1]) for time in trajectories.time)
    if end <= start:
        raise ValueError("Irregular trajectories do not share a positive common time interval")
    return start, end


def make_common_grid(
    trajectories: IrregularTrajectorySet,
    *,
    n_time: int,
    domain: str = "overlap",
    start: float | None = None,
    end: float | None = None,
) -> np.ndarray:
    """Construct an explicit common grid without modifying trajectory values.

    The 'overlap' domain uses only time observed by every curve. The 'union'
    domain spans the full observed range and can create edge missingness after
    resampling for curves with shorter domains.
    """

    if n_time < 2:
        raise ValueError("n_time must be at least 2")
    if (start is None) ^ (end is None):
        raise ValueError("start and end must be supplied together")
    if start is not None:
        lo, hi = float(start), float(end)
    elif domain == "overlap":
        lo, hi = common_overlap_interval(trajectories)
    elif domain == "union":
        lo = min(float(time[0]) for time in trajectories.time)
        hi = max(float(time[-1]) for time in trajectories.time)
    else:
        raise ValueError("domain must be 'overlap' or 'union'")
    if hi <= lo:
        raise ValueError("Common-grid end must be greater than start")
    return np.linspace(lo, hi, n_time)


def resample_irregular_to_grid(
    trajectories: IrregularTrajectorySet,
    grid: np.ndarray,
    *,
    method: str = "linear",
    max_gap: float | None = None,
) -> TrajectorySet:
    """Project native irregular trajectories onto an explicit common grid.

    No extrapolation is performed. Long intervals remain missing when
    max_gap is supplied.
    """

    grid = np.asarray(grid, dtype=float)
    if grid.ndim != 1 or len(grid) < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("grid must be a strictly increasing one-dimensional array")
    projected = np.empty(
        (trajectories.n_curves, len(grid), trajectories.n_dimensions),
        dtype=float,
    )
    for i, (time, values) in enumerate(zip(trajectories.time, trajectories.values, strict=True)):
        projected[i] = _resample_single_curve(
            time,
            values,
            grid,
            method=method,
            max_gap=max_gap,
        )
    return TrajectorySet(
        time=grid,
        values=projected,
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "irregular_to_grid": {
                "method": method,
                "max_gap": max_gap,
                "n_time": len(grid),
                "grid_start": float(grid[0]),
                "grid_end": float(grid[-1]),
            },
        },
    )


def resample_irregular_to_common_grid(
    trajectories: IrregularTrajectorySet,
    *,
    n_time: int,
    domain: str = "overlap",
    method: str = "linear",
    max_gap: float | None = None,
) -> TrajectorySet:
    """Create and apply a common grid in one explicit step."""

    grid = make_common_grid(trajectories, n_time=n_time, domain=domain)
    return resample_irregular_to_grid(
        trajectories,
        grid,
        method=method,
        max_gap=max_gap,
    )


def irregular_sampling_summary(trajectories: IrregularTrajectorySet) -> pd.DataFrame:
    """Return per-curve sampling and missingness diagnostics."""

    rows = []
    for curve_id, time, values in zip(
        trajectories.curve_ids,
        trajectories.time,
        trajectories.values,
        strict=True,
    ):
        intervals = np.diff(time)
        rows.append(
            {
                "curve_id": curve_id,
                "n_samples": len(time),
                "time_start": float(time[0]),
                "time_end": float(time[-1]),
                "median_interval": float(np.median(intervals)),
                "max_interval": float(np.max(intervals)),
                "missing_fraction": float(np.isnan(values).mean()),
            }
        )
    return pd.DataFrame(rows)
