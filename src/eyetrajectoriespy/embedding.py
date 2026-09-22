"""Delay-coordinate reconstruction and embedding diagnostics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .nonlinear_types import (
    DelayEmbeddingResult,
    EmbeddingDelayDiagnosticResult,
    EmbeddingDimensionDiagnosticResult,
)
from .types import TrajectorySet


_TIME_TO_SECONDS = {
    "s": 1.0,
    "sec": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 1e-3,
    "millisecond": 1e-3,
    "milliseconds": 1e-3,
}


def _curve_index(trajectories: TrajectorySet, curve: int | str) -> int:
    if isinstance(curve, str):
        try:
            return trajectories.curve_ids.index(curve)
        except ValueError as exc:
            raise KeyError(f"Unknown curve_id {curve!r}") from exc
    if not isinstance(curve, (int, np.integer)):
        raise TypeError("curve must be an integer index or curve_id string")
    index = int(curve)
    if index < 0 or index >= trajectories.n_curves:
        raise IndexError("curve index is out of range")
    return index


def _dimension_indices(
    trajectories: TrajectorySet,
    dimensions: Sequence[str] | None,
) -> tuple[int, ...]:
    if dimensions is None:
        raise ValueError("dimensions must be supplied explicitly")
    names = tuple(dimensions)
    if not names:
        raise ValueError("at least one dimension must be selected")
    if len(set(names)) != len(names):
        raise ValueError("dimensions must be unique")
    indices = []
    for name in names:
        try:
            indices.append(trajectories.dimension_names.index(name))
        except ValueError as exc:
            raise KeyError(f"Unknown dimension {name!r}") from exc
    return tuple(indices)


def _regular_step(time: np.ndarray) -> float:
    delta = np.diff(time)
    step = float(np.median(delta))
    if not np.allclose(delta, step, rtol=1e-6, atol=max(1e-12, abs(step) * 1e-9)):
        raise ValueError(
            "time-based nonlinear dynamics parameters require an approximately regular grid; "
            "resample explicitly before analysis or use sample units where scientifically justified"
        )
    return step


def _resolve_samples(
    time: np.ndarray,
    value: float | int,
    *,
    units: str,
    time_unit: str,
    name: str,
    allow_zero: bool = False,
) -> int:
    minimum = 0 if allow_zero else 1
    if units == "samples":
        if isinstance(value, (bool, np.bool_)) or float(value) != int(value):
            raise ValueError(f"{name} must be an integer when units='samples'")
        samples = int(value)
    else:
        step = _regular_step(time)
        normalized_units = units.lower()
        normalized_time_unit = time_unit.lower()
        if normalized_units in _TIME_TO_SECONDS and normalized_time_unit in _TIME_TO_SECONDS:
            value_in_time_units = (
                float(value)
                * _TIME_TO_SECONDS[normalized_units]
                / _TIME_TO_SECONDS[normalized_time_unit]
            )
        elif normalized_units == normalized_time_unit:
            value_in_time_units = float(value)
        else:
            raise ValueError(
                f"{name}_units={units!r} cannot be converted to trajectory time_unit={time_unit!r}"
            )
        raw = value_in_time_units / step
        samples = int(round(raw))
        if not np.isclose(raw, samples, rtol=1e-6, atol=1e-8):
            raise ValueError(
                f"{name}={value!r} {units} is not an integer multiple of the observed grid step"
            )
    if samples < minimum:
        comparator = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must resolve to a {comparator} sample count")
    return samples


def _require_finite(values: np.ndarray, *, context: str) -> None:
    if not np.all(np.isfinite(values)):
        raise ValueError(
            f"{context} requires complete finite samples; missing values are never dropped or imputed silently"
        )


def _embed_scalar(signal: np.ndarray, embedding_dimension: int, delay_samples: int) -> np.ndarray:
    n = signal.size - (embedding_dimension - 1) * delay_samples
    if n < 2:
        raise ValueError("embedding leaves fewer than two reconstructed states")
    end = np.arange((embedding_dimension - 1) * delay_samples, signal.size)
    return np.column_stack(
        [signal[end - lag * delay_samples] for lag in range(embedding_dimension)]
    )


def delay_embed_trajectory(
    trajectories: TrajectorySet,
    *,
    embedding_dimension: int,
    delay: float | int,
    delay_units: str = "samples",
    dimensions: Sequence[str] | None = None,
) -> DelayEmbeddingResult:
    """Reconstruct a multivariate delay-coordinate state space.

    No smoothing, interpolation, scaling, or parameter selection is performed.
    Time-based delays require a regular common grid and must map to an integer
    number of observed samples.
    """

    if not isinstance(embedding_dimension, (int, np.integer)) or embedding_dimension < 1:
        raise ValueError("embedding_dimension must be a positive integer")
    indices = _dimension_indices(trajectories, dimensions)
    source_names = tuple(trajectories.dimension_names[i] for i in indices)
    selected = trajectories.values[:, :, indices]
    _require_finite(selected, context="delay embedding")
    delay_samples = _resolve_samples(
        trajectories.time,
        delay,
        units=delay_units,
        time_unit=trajectories.time_unit,
        name="delay",
    )
    first = (embedding_dimension - 1) * delay_samples
    if first >= trajectories.n_time - 1:
        raise ValueError("embedding_dimension and delay leave fewer than two reconstructed states")

    endpoints = np.arange(first, trajectories.n_time)
    blocks = [
        selected[:, endpoints - lag * delay_samples, :]
        for lag in range(embedding_dimension)
    ]
    values = np.concatenate(blocks, axis=2)
    state_names = tuple(
        f"{name}[t-{lag}*delay]"
        for lag in range(embedding_dimension)
        for name in source_names
    )
    try:
        step = _regular_step(trajectories.time)
        delay_time = delay_samples * step
        constant_delay_time = True
    except ValueError:
        if delay_units != "samples":
            raise
        delay_time = float("nan")
        constant_delay_time = False
    return DelayEmbeddingResult(
        values=values,
        time=trajectories.time[endpoints].copy(),
        curve_ids=trajectories.curve_ids,
        source_dimension_names=source_names,
        state_names=state_names,
        embedding_dimension=int(embedding_dimension),
        delay_samples=delay_samples,
        delay_time=delay_time,
        time_unit=trajectories.time_unit,
        provenance={
            "operation": "delay_embed_trajectory",
            "source_provenance": dict(trajectories.provenance),
            "dimensions": source_names,
            "embedding_dimension": int(embedding_dimension),
            "delay_samples": delay_samples,
            "delay_time": delay_time,
            "constant_delay_time": constant_delay_time,
            "delay_units_requested": delay_units,
            "automatic_parameter_selection": False,
            "missing_policy": "error",
            "scaling": "none",
        },
    )


def _average_mutual_information(
    x: np.ndarray,
    y: np.ndarray,
    edges: np.ndarray,
) -> float:
    joint, _, _ = np.histogram2d(x, y, bins=(edges, edges))
    total = float(joint.sum())
    if total <= 0:
        raise ValueError("cannot estimate mutual information from an empty histogram")
    pxy = joint / total
    px = pxy.sum(axis=1)
    py = pxy.sum(axis=0)
    expected = px[:, None] * py[None, :]
    mask = pxy > 0
    return float(np.sum(pxy[mask] * np.log(pxy[mask] / expected[mask])))


def embedding_delay_diagnostics(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimension: str,
    max_lag: float | int,
    max_lag_units: str = "samples",
    bins: int = 16,
) -> EmbeddingDelayDiagnosticResult:
    """Compute autocorrelation and average-mutual-information delay diagnostics.

    The function marks the first interior AMI local minimum when one exists but
    does not select or return an analysis delay automatically.
    """

    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if not isinstance(bins, (int, np.integer)) or bins < 2:
        raise ValueError("bins must be an integer >= 2")
    curve_index = _curve_index(trajectories, curve)
    signal = trajectories.dimension(dimension)[curve_index].astype(float, copy=False)
    _require_finite(signal, context="embedding delay diagnostics")
    if np.std(signal, ddof=0) <= 0:
        raise ValueError("embedding delay diagnostics require a non-constant signal")
    max_lag_samples = _resolve_samples(
        trajectories.time,
        max_lag,
        units=max_lag_units,
        time_unit=trajectories.time_unit,
        name="max_lag",
    )
    if max_lag_samples >= signal.size - 1:
        raise ValueError("max_lag must leave at least two paired observations")

    centered = signal - signal.mean()
    denominator = float(np.dot(centered, centered))
    edges = np.histogram_bin_edges(signal, bins=int(bins))
    if np.unique(edges).size < 3:
        raise ValueError("AMI histogram requires at least two non-degenerate bins")
    rows = []
    for lag in range(1, max_lag_samples + 1):
        x = signal[:-lag]
        y = signal[lag:]
        acf = float(np.dot(centered[:-lag], centered[lag:]) / denominator)
        ami = _average_mutual_information(x, y, edges)
        rows.append((lag, trajectories.time[lag] - trajectories.time[0], acf, ami))
    table = pd.DataFrame(
        rows,
        columns=["lag_samples", "lag_time", "autocorrelation", "average_mutual_information"],
    )
    local_min = np.zeros(len(table), dtype=bool)
    ami = table["average_mutual_information"].to_numpy()
    candidates = np.where((ami[1:-1] < ami[:-2]) & (ami[1:-1] <= ami[2:]))[0]
    if candidates.size:
        local_min[candidates[0] + 1] = True
    table["first_ami_local_minimum"] = local_min

    return EmbeddingDelayDiagnosticResult(
        table=table,
        curve_id=trajectories.curve_ids[curve_index],
        dimension=dimension,
        bins=int(bins),
        max_lag_samples=max_lag_samples,
        time_unit=trajectories.time_unit,
        provenance={
            "operation": "embedding_delay_diagnostics",
            "source_provenance": dict(trajectories.provenance),
            "criterion": "Fraser-Swinney average mutual information diagnostic",
            "automatic_delay_selection": False,
            "bins": int(bins),
            "histogram_edges_fixed_across_lags": True,
        },
    )


def _nearest_temporally_separated(
    states: np.ndarray,
    *,
    theiler_window_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    n = states.shape[0]
    tree = cKDTree(states)
    k = min(n, 16)
    while True:
        distances, indices = tree.query(states, k=k)
        if k == 1:
            distances = distances[:, None]
            indices = indices[:, None]
        chosen_index = np.full(n, -1, dtype=int)
        chosen_distance = np.full(n, np.nan, dtype=float)
        for i in range(n):
            for distance, candidate in zip(distances[i], indices[i], strict=True):
                candidate = int(candidate)
                if (
                    candidate != i
                    and abs(candidate - i) > theiler_window_samples
                    and np.isfinite(distance)
                    and distance > 0
                ):
                    chosen_index[i] = candidate
                    chosen_distance[i] = float(distance)
                    break
        if np.all(chosen_index >= 0):
            return chosen_index, chosen_distance
        if k == n:
            missing = int(np.sum(chosen_index < 0))
            raise ValueError(
                f"no positive-distance temporally separated nearest neighbor for {missing} states"
            )
        k = min(n, max(k + 1, 2 * k))


def embedding_dimension_diagnostics(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimension: str,
    delay: float | int,
    delay_units: str = "samples",
    max_dimension: int = 10,
    theiler_window: float | int = 0,
    theiler_window_units: str = "samples",
    rtol: float = 10.0,
    atol: float = 2.0,
) -> EmbeddingDimensionDiagnosticResult:
    """Compute Kennel-style false-nearest-neighbor fractions across dimensions.

    The diagnostic curve is returned without silently choosing an embedding
    dimension.
    """

    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")
    if not isinstance(max_dimension, (int, np.integer)) or max_dimension < 1:
        raise ValueError("max_dimension must be a positive integer")
    if not np.isfinite(rtol) or rtol <= 0 or not np.isfinite(atol) or atol <= 0:
        raise ValueError("rtol and atol must be positive finite values")

    curve_index = _curve_index(trajectories, curve)
    signal = trajectories.dimension(dimension)[curve_index].astype(float, copy=False)
    _require_finite(signal, context="embedding dimension diagnostics")
    scale = float(np.std(signal, ddof=0))
    if scale <= 0:
        raise ValueError("false-nearest-neighbor diagnostics require a non-constant signal")
    delay_samples = _resolve_samples(
        trajectories.time,
        delay,
        units=delay_units,
        time_unit=trajectories.time_unit,
        name="delay",
    )
    theiler_samples = _resolve_samples(
        trajectories.time,
        theiler_window,
        units=theiler_window_units,
        time_unit=trajectories.time_unit,
        name="theiler_window",
        allow_zero=True,
    )

    rows = []
    for dimension_value in range(1, int(max_dimension) + 1):
        start = dimension_value * delay_samples
        if start >= signal.size - 1:
            break
        endpoints = np.arange(start, signal.size)
        states = np.column_stack(
            [
                signal[endpoints - lag * delay_samples]
                for lag in range(dimension_value)
            ]
        )
        added = signal[endpoints - dimension_value * delay_samples]
        neighbor_index, distance_m = _nearest_temporally_separated(
            states,
            theiler_window_samples=theiler_samples,
        )
        added_difference = np.abs(added - added[neighbor_index])
        distance_next = np.sqrt(distance_m**2 + added_difference**2)
        false = (added_difference / distance_m > float(rtol)) | (
            distance_next / scale > float(atol)
        )
        rows.append(
            {
                "embedding_dimension": dimension_value,
                "false_neighbor_fraction": float(np.mean(false)),
                "n_reference_states": int(states.shape[0]),
                "rtol": float(rtol),
                "atol": float(atol),
            }
        )
    if not rows:
        raise ValueError("no embedding dimensions are supported by the available series length")

    return EmbeddingDimensionDiagnosticResult(
        table=pd.DataFrame(rows),
        curve_id=trajectories.curve_ids[curve_index],
        dimension=dimension,
        delay_samples=delay_samples,
        theiler_window_samples=theiler_samples,
        rtol=float(rtol),
        atol=float(atol),
        provenance={
            "operation": "embedding_dimension_diagnostics",
            "source_provenance": dict(trajectories.provenance),
            "criterion": "Kennel-Brown-Abarbanel false nearest neighbors",
            "automatic_dimension_selection": False,
            "missing_policy": "error",
        },
    )
