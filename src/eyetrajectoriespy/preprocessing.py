"""Conservative preprocessing for functional gaze trajectories."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from .types import TrajectorySet
from .validation import validate_trajectory_set


def _interpolate_valid_segments(
    times: np.ndarray,
    values: np.ndarray,
    grid: np.ndarray,
    *,
    method: str,
) -> np.ndarray:
    out = np.full(grid.shape, np.nan, dtype=float)
    valid = np.isfinite(times) & np.isfinite(values)
    if valid.sum() < 2:
        return out
    x = times[valid]
    y = values[valid]
    inside = (grid >= x[0]) & (grid <= x[-1])
    if method == "linear":
        out[inside] = np.interp(grid[inside], x, y)
    elif method == "pchip":
        out[inside] = PchipInterpolator(x, y, extrapolate=False)(grid[inside])
    else:
        raise ValueError("method must be 'linear' or 'pchip'")
    return out


def _mask_large_gaps(
    times: np.ndarray,
    grid: np.ndarray,
    out: np.ndarray,
    *,
    max_gap: float | None,
) -> np.ndarray:
    if max_gap is None:
        return out
    if max_gap <= 0:
        raise ValueError("max_gap must be positive")
    diffs = np.diff(times)
    for left, right, gap in zip(times[:-1], times[1:], diffs, strict=True):
        if gap > max_gap:
            out[(grid > left) & (grid < right)] = np.nan
    return out


def _resample_single_curve(
    times: np.ndarray,
    values: np.ndarray,
    grid: np.ndarray,
    *,
    method: str,
    max_gap: float | None,
) -> np.ndarray:
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)
    if times.ndim != 1 or values.ndim != 2 or values.shape[0] != times.size:
        raise ValueError("times must be 1-D and values must have shape (n_time, n_dimensions)")
    valid_time = np.isfinite(times)
    times = times[valid_time]
    values = values[valid_time]
    if len(times) and not np.all(np.diff(times) > 0):
        raise ValueError("times must be strictly increasing")
    result = np.full((len(grid), values.shape[1]), np.nan, dtype=float)
    for dim in range(values.shape[1]):
        valid = np.isfinite(values[:, dim])
        if valid.sum() < 2:
            continue
        x = times[valid]
        y = values[valid, dim]
        interpolated = _interpolate_valid_segments(x, y, grid, method=method)
        result[:, dim] = _mask_large_gaps(x, grid, interpolated, max_gap=max_gap)
    return result


def resample_to_grid(
    trajectories: TrajectorySet,
    grid: np.ndarray,
    *,
    method: str = "linear",
    max_gap: float | None = None,
) -> TrajectorySet:
    """Resample common-grid trajectories to a new grid without extrapolation.

    Missing observations are interpolated only when bounded by observed values.
    If ``max_gap`` is supplied, intervals larger than that threshold remain
    missing after resampling.
    """

    validate_trajectory_set(trajectories)
    grid = np.asarray(grid, dtype=float)
    if grid.ndim != 1 or len(grid) < 2 or not np.all(np.diff(grid) > 0):
        raise ValueError("grid must be a strictly increasing one-dimensional array")
    values = np.empty((trajectories.n_curves, len(grid), trajectories.n_dimensions), dtype=float)
    for i in range(trajectories.n_curves):
        values[i] = _resample_single_curve(
            trajectories.time,
            trajectories.values[i],
            grid,
            method=method,
            max_gap=max_gap,
        )
    return trajectories.with_values(
        values,
        time=grid,
        provenance_update={
            "resampling": {"method": method, "max_gap": max_gap, "n_grid": len(grid)}
        },
    )


def interpolate_short_gaps(
    trajectories: TrajectorySet,
    *,
    max_gap: float,
    method: str = "pchip",
) -> TrajectorySet:
    """Interpolate only missing runs whose bounding samples are sufficiently close.

    This function exists to make interpolation explicit. It never fills leading
    or trailing missing values and never bridges a gap longer than ``max_gap``.
    """

    if max_gap <= 0:
        raise ValueError("max_gap must be positive")
    result = trajectories.values.copy()
    time = trajectories.time
    for c in range(trajectories.n_curves):
        for d in range(trajectories.n_dimensions):
            y = result[c, :, d]
            valid_idx = np.flatnonzero(np.isfinite(y))
            if valid_idx.size < 2:
                continue
            for left_idx, right_idx in zip(valid_idx[:-1], valid_idx[1:], strict=True):
                if right_idx - left_idx <= 1:
                    continue
                gap_duration = time[right_idx] - time[left_idx]
                if gap_duration > max_gap:
                    continue
                target_idx = np.arange(left_idx + 1, right_idx)
                if method == "linear":
                    y[target_idx] = np.interp(
                        time[target_idx],
                        time[[left_idx, right_idx]],
                        y[[left_idx, right_idx]],
                    )
                elif method == "pchip":
                    y[target_idx] = PchipInterpolator(
                        time[[left_idx, right_idx]], y[[left_idx, right_idx]]
                    )(time[target_idx])
                else:
                    raise ValueError("method must be 'linear' or 'pchip'")
            result[c, :, d] = y
    return trajectories.with_values(
        result,
        provenance_update={"gap_interpolation": {"method": method, "max_gap": max_gap}},
    )


def smooth_trajectories(
    trajectories: TrajectorySet,
    *,
    method: str,
    window: int | None = None,
    polyorder: int = 2,
    sigma: float | None = None,
) -> TrajectorySet:
    """Smooth functional channels while preserving missing observations.

    Smoothing is intentionally opt-in because genuine saccadic transitions are
    abrupt. The function emits a methodological warning whenever called.
    """

    warnings.warn(
        "Smoothing can attenuate genuine saccadic transitions. Report the method and parameters, "
        "and compare against unsmoothed trajectories when timing/shape is scientifically important.",
        UserWarning,
        stacklevel=2,
    )
    result = trajectories.values.copy()
    for c in range(trajectories.n_curves):
        for d in range(trajectories.n_dimensions):
            y = result[c, :, d]
            valid = np.isfinite(y)
            if valid.sum() < 3:
                continue
            # Do not bridge missing runs during smoothing. Smooth each contiguous valid run.
            padded = np.r_[False, valid, False]
            changes = np.diff(padded.astype(int))
            starts = np.flatnonzero(changes == 1)
            ends = np.flatnonzero(changes == -1)
            for start, end in zip(starts, ends, strict=True):
                segment = y[start:end]
                if method == "savgol":
                    if window is None:
                        raise ValueError("window is required for Savitzky-Golay smoothing")
                    if window % 2 == 0 or window < 3:
                        raise ValueError("window must be an odd integer >= 3")
                    if window > len(segment):
                        continue
                    if polyorder >= window:
                        raise ValueError("polyorder must be smaller than window")
                    y[start:end] = savgol_filter(segment, window_length=window, polyorder=polyorder)
                elif method == "gaussian":
                    if sigma is None or sigma <= 0:
                        raise ValueError("positive sigma is required for Gaussian smoothing")
                    y[start:end] = gaussian_filter1d(segment, sigma=sigma, mode="nearest")
                else:
                    raise ValueError("method must be 'savgol' or 'gaussian'")
            result[c, :, d] = y
    params = {"method": method, "window": window, "polyorder": polyorder, "sigma": sigma}
    return trajectories.with_values(result, provenance_update={"smoothing": params})


def normalize_time(
    trajectories: TrajectorySet,
    *,
    start: float = 0.0,
    end: float = 1.0,
) -> TrajectorySet:
    """Linearly normalize the common time domain to an explicit interval.

    This removes absolute time units. The original time domain is retained in
    provenance so the transformation is auditable.
    """

    if end <= start:
        raise ValueError("end must be greater than start")
    old = trajectories.time
    scaled = start + (old - old[0]) / (old[-1] - old[0]) * (end - start)
    return trajectories.with_values(
        trajectories.values.copy(),
        time=scaled,
        time_unit="normalized",
        provenance_update={
            "time_normalization": {
                "original_start": float(old[0]),
                "original_end": float(old[-1]),
                "original_unit": trajectories.time_unit,
                "new_start": start,
                "new_end": end,
            }
        },
    )


def normalize_coordinates(
    trajectories: TrajectorySet,
    *,
    width: float,
    height: float,
) -> TrajectorySet:
    """Convert planar pixel coordinates to ``[0, 1]`` normalized coordinates."""

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if trajectories.n_dimensions < 2:
        raise ValueError("At least two dimensions are required for planar coordinate normalization")
    values = trajectories.values.copy()
    values[:, :, 0] = values[:, :, 0] / width
    values[:, :, 1] = values[:, :, 1] / height
    return trajectories.with_values(
        values,
        coordinate_system="normalized",
        provenance_update={"coordinate_normalization": {"width": width, "height": height}},
    )


def center_on_landmark(
    trajectories: TrajectorySet,
    *,
    landmark_x: float | np.ndarray,
    landmark_y: float | np.ndarray,
) -> TrajectorySet:
    """Express planar gaze relative to a stimulus landmark.

    ``landmark_x`` and ``landmark_y`` may be scalars or one value per curve.
    """

    if trajectories.n_dimensions < 2:
        raise ValueError("At least two dimensions are required")
    lx = np.asarray(landmark_x, dtype=float)
    ly = np.asarray(landmark_y, dtype=float)
    if lx.ndim == 0:
        lx = np.repeat(lx, trajectories.n_curves)
    if ly.ndim == 0:
        ly = np.repeat(ly, trajectories.n_curves)
    if lx.shape != (trajectories.n_curves,) or ly.shape != (trajectories.n_curves,):
        raise ValueError("landmark coordinates must be scalars or one value per curve")
    values = trajectories.values.copy()
    values[:, :, 0] -= lx[:, None]
    values[:, :, 1] -= ly[:, None]
    return trajectories.with_values(
        values,
        coordinate_system="landmark_relative",
        provenance_update={"landmark_centering": {"per_curve": True}},
    )
