"""Sparse recurrence and cross-recurrence analysis."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix, triu
from scipy.spatial import cKDTree

from .embedding import (
    _curve_index,
    _dimension_indices,
    _require_finite,
    _resolve_samples,
)
from .nonlinear_types import (
    DelayEmbeddingResult,
    RecurrenceResult,
    RQAResult,
    WindowedRQAFunctionalResult,
    WindowedRQAResult,
)
from .types import TrajectorySet


_METRIC_P = {"cityblock": 1.0, "euclidean": 2.0, "chebyshev": np.inf}


def _state_from_source(
    source: TrajectorySet | DelayEmbeddingResult,
    *,
    curve: int | str,
    dimensions: Sequence[str] | None,
) -> tuple[np.ndarray, np.ndarray, str, str, dict]:
    if isinstance(source, TrajectorySet):
        if dimensions is None:
            raise ValueError(
                "dimensions must be supplied explicitly for TrajectorySet recurrence analysis"
            )
        index = _curve_index(source, curve)
        dim_indices = _dimension_indices(source, dimensions)
        states = source.values[index][:, dim_indices]
        names = tuple(source.dimension_names[i] for i in dim_indices)
        _require_finite(states, context="recurrence analysis")
        return (
            np.asarray(states, dtype=float),
            source.time.copy(),
            source.curve_ids[index],
            source.time_unit,
            {
                "source_kind": "TrajectorySet",
                "dimensions": names,
                "state_names": names,
                "coordinate_system": source.coordinate_system,
                "source_provenance": dict(source.provenance),
            },
        )
    if isinstance(source, DelayEmbeddingResult):
        if dimensions is not None:
            raise ValueError("dimensions cannot be supplied for an already embedded state space")
        if isinstance(curve, str):
            try:
                index = source.curve_ids.index(curve)
            except ValueError as exc:
                raise KeyError(f"Unknown curve_id {curve!r}") from exc
        else:
            index = int(curve)
            if index < 0 or index >= source.n_curves:
                raise IndexError("curve index is out of range")
        states = source.values[index]
        _require_finite(states, context="recurrence analysis")
        return (
            np.asarray(states, dtype=float),
            source.time.copy(),
            source.curve_ids[index],
            source.time_unit,
            {
                "source_kind": "DelayEmbeddingResult",
                "embedding_dimension": source.embedding_dimension,
                "delay_samples": source.delay_samples,
                "delay_time": source.delay_time,
                "state_names": source.state_names,
                "coordinate_system": source.coordinate_system,
                "source_provenance": dict(source.provenance),
            },
        )
    raise TypeError("source must be a TrajectorySet or DelayEmbeddingResult")


def _eligible_auto_pairs(n: int, theiler: int) -> int:
    remaining = n - theiler - 1
    return 0 if remaining <= 0 else remaining * (remaining + 1) // 2


def _filter_auto_pairs(pairs: set[tuple[int, int]], theiler: int) -> list[tuple[int, int]]:
    return sorted((i, j) for i, j in pairs if abs(j - i) > theiler)


def _count_auto_pairs(states: np.ndarray, radius: float, p: float, theiler: int) -> int:
    pairs = cKDTree(states).query_pairs(radius, p=p, output_type="set")
    return sum(abs(j - i) > theiler for i, j in pairs)


def _auto_radius_for_target(
    states: np.ndarray,
    target: float,
    *,
    p: float,
    theiler: int,
    iterations: int = 48,
) -> float:
    eligible = _eligible_auto_pairs(states.shape[0], theiler)
    if eligible <= 0:
        raise ValueError("Theiler window leaves no eligible recurrence pairs")
    spread = np.ptp(states, axis=0)
    if p == np.inf:
        high = float(np.max(spread))
    else:
        high = float(np.linalg.norm(spread, ord=p))
    if high <= 0:
        raise ValueError("recurrence analysis requires non-constant state vectors")
    low = 0.0
    for _ in range(iterations):
        mid = (low + high) / 2.0
        rr = _count_auto_pairs(states, mid, p, theiler) / eligible
        if rr < target:
            low = mid
        else:
            high = mid
    return high


def _cross_radius_for_target(
    a: np.ndarray,
    b: np.ndarray,
    target: float,
    *,
    p: float,
    iterations: int = 48,
) -> float:
    total = a.shape[0] * b.shape[0]
    if total <= 0:
        raise ValueError("cross recurrence requires non-empty state spaces")
    combined_min = np.minimum(a.min(axis=0), b.min(axis=0))
    combined_max = np.maximum(a.max(axis=0), b.max(axis=0))
    spread = combined_max - combined_min
    if p == np.inf:
        high = float(np.max(spread))
    else:
        high = float(np.linalg.norm(spread, ord=p))
    if high <= 0:
        raise ValueError("cross recurrence requires non-constant state vectors")
    tree_a = cKDTree(a)
    tree_b = cKDTree(b)
    low = 0.0
    for _ in range(iterations):
        mid = (low + high) / 2.0
        count = int(tree_a.count_neighbors(tree_b, mid, p=p))
        rr = count / total
        if rr < target:
            low = mid
        else:
            high = mid
    return high


def _validate_radius_policy(
    radius: float | None,
    target_recurrence_rate: float | None,
) -> None:
    if (radius is None) == (target_recurrence_rate is None):
        raise ValueError("supply exactly one of radius or target_recurrence_rate")
    if radius is not None and (not np.isfinite(radius) or radius <= 0):
        raise ValueError("radius must be a positive finite value")
    if target_recurrence_rate is not None and not (
        np.isfinite(target_recurrence_rate) and 0 < target_recurrence_rate < 1
    ):
        raise ValueError("target_recurrence_rate must be strictly between 0 and 1")


def recurrence_matrix(
    source: TrajectorySet | DelayEmbeddingResult,
    *,
    curve: int | str,
    radius: float | None = None,
    target_recurrence_rate: float | None = None,
    metric: str = "euclidean",
    theiler_window: float | int = 0,
    theiler_window_units: str = "samples",
    dimensions: Sequence[str] | None = None,
) -> RecurrenceResult:
    """Construct a sparse symmetric recurrence matrix for one trajectory.

    Exactly one radius policy must be declared.  The main diagonal and all
    pairs within the explicit Theiler window are excluded.
    """

    _validate_radius_policy(radius, target_recurrence_rate)
    if metric not in _METRIC_P:
        raise ValueError(f"metric must be one of {sorted(_METRIC_P)}")
    states, time, curve_id, time_unit, source_info = _state_from_source(
        source, curve=curve, dimensions=dimensions
    )
    theiler = _resolve_samples(
        time,
        theiler_window,
        units=theiler_window_units,
        time_unit=time_unit,
        name="theiler_window",
        allow_zero=True,
    )
    eligible = _eligible_auto_pairs(states.shape[0], theiler)
    if eligible <= 0:
        raise ValueError("Theiler window leaves no eligible recurrence pairs")
    p = _METRIC_P[metric]
    chosen_radius = (
        float(radius)
        if radius is not None
        else _auto_radius_for_target(
            states, float(target_recurrence_rate), p=p, theiler=theiler
        )
    )
    pairs = _filter_auto_pairs(
        cKDTree(states).query_pairs(chosen_radius, p=p, output_type="set"),
        theiler,
    )
    if pairs:
        upper_i = np.asarray([i for i, _ in pairs], dtype=int)
        upper_j = np.asarray([j for _, j in pairs], dtype=int)
        rows = np.concatenate([upper_i, upper_j])
        cols = np.concatenate([upper_j, upper_i])
        data = np.ones(rows.size, dtype=bool)
        matrix = coo_matrix((data, (rows, cols)), shape=(states.shape[0], states.shape[0])).tocsr()
    else:
        matrix = csr_matrix((states.shape[0], states.shape[0]), dtype=bool)
    achieved = len(pairs) / eligible
    return RecurrenceResult(
        matrix=matrix,
        time_a=time,
        time_b=time,
        source_curve_ids=(curve_id,),
        radius=chosen_radius,
        target_recurrence_rate=(
            None if target_recurrence_rate is None else float(target_recurrence_rate)
        ),
        achieved_recurrence_rate=float(achieved),
        metric=metric,
        theiler_window_samples=theiler,
        kind="auto",
        state_dimension=states.shape[1],
        provenance={
            "operation": "recurrence_matrix",
            **source_info,
            "radius_policy": "fixed" if radius is not None else "target_recurrence_rate",
            "target_recurrence_rate": target_recurrence_rate,
            "achieved_recurrence_rate": float(achieved),
            "metric": metric,
            "theiler_window_samples": theiler,
            "sparse": True,
            "diagonal_included": False,
        },
    )


def cross_recurrence_matrix(
    source_a: TrajectorySet | DelayEmbeddingResult,
    source_b: TrajectorySet | DelayEmbeddingResult,
    *,
    curve_a: int | str,
    curve_b: int | str,
    radius: float | None = None,
    target_recurrence_rate: float | None = None,
    metric: str = "euclidean",
    dimensions_a: Sequence[str] | None = None,
    dimensions_b: Sequence[str] | None = None,
) -> RecurrenceResult:
    """Construct a sparse cross-recurrence matrix between two trajectories."""

    _validate_radius_policy(radius, target_recurrence_rate)
    if metric not in _METRIC_P:
        raise ValueError(f"metric must be one of {sorted(_METRIC_P)}")
    a, time_a, id_a, unit_a, info_a = _state_from_source(
        source_a, curve=curve_a, dimensions=dimensions_a
    )
    b, time_b, id_b, unit_b, info_b = _state_from_source(
        source_b, curve=curve_b, dimensions=dimensions_b
    )
    if a.shape[1] != b.shape[1]:
        raise ValueError("cross-recurrence state spaces must have the same dimension")
    if info_a.get("state_names") != info_b.get("state_names"):
        raise ValueError(
            "cross-recurrence state spaces must use the same named state variables "
            "in the same order"
        )
    if info_a.get("coordinate_system") != info_b.get("coordinate_system"):
        raise ValueError(
            "cross-recurrence state spaces must use the same coordinate_system"
        )
    if unit_a != unit_b:
        raise ValueError("cross-recurrence trajectories must use the same time_unit")
    if info_a.get("source_kind") == info_b.get("source_kind") == "DelayEmbeddingResult":
        if info_a.get("embedding_dimension") != info_b.get("embedding_dimension"):
            raise ValueError("cross-recurrence embeddings must use the same embedding_dimension")
        if info_a.get("delay_samples") != info_b.get("delay_samples"):
            raise ValueError("cross-recurrence embeddings must use the same delay_samples")
        delay_a = info_a.get("delay_time")
        delay_b = info_b.get("delay_time")
        if np.isfinite(delay_a) != np.isfinite(delay_b):
            raise ValueError("cross-recurrence embeddings have incompatible delay-time semantics")
        if np.isfinite(delay_a) and not np.isclose(delay_a, delay_b):
            raise ValueError("cross-recurrence embeddings must use the same physical delay")
    p = _METRIC_P[metric]
    chosen_radius = (
        float(radius)
        if radius is not None
        else _cross_radius_for_target(a, b, float(target_recurrence_rate), p=p)
    )
    neighbors = cKDTree(a).query_ball_tree(cKDTree(b), chosen_radius, p=p)
    rows = []
    cols = []
    for i, js in enumerate(neighbors):
        rows.extend([i] * len(js))
        cols.extend(js)
    matrix = coo_matrix(
        (np.ones(len(rows), dtype=bool), (rows, cols)),
        shape=(a.shape[0], b.shape[0]),
    ).tocsr()
    achieved = matrix.nnz / (a.shape[0] * b.shape[0])
    return RecurrenceResult(
        matrix=matrix,
        time_a=time_a,
        time_b=time_b,
        source_curve_ids=(id_a, id_b),
        radius=chosen_radius,
        target_recurrence_rate=(
            None if target_recurrence_rate is None else float(target_recurrence_rate)
        ),
        achieved_recurrence_rate=float(achieved),
        metric=metric,
        theiler_window_samples=0,
        kind="cross",
        state_dimension=a.shape[1],
        provenance={
            "operation": "cross_recurrence_matrix",
            "source_a": info_a,
            "source_b": info_b,
            "radius_policy": "fixed" if radius is not None else "target_recurrence_rate",
            "target_recurrence_rate": target_recurrence_rate,
            "achieved_recurrence_rate": float(achieved),
            "metric": metric,
            "sparse": True,
        },
    )


def _run_lengths(sorted_values: np.ndarray) -> list[int]:
    if sorted_values.size == 0:
        return []
    gaps = np.where(np.diff(sorted_values) != 1)[0] + 1
    return [len(part) for part in np.split(sorted_values, gaps)]


def _diagonal_lengths(matrix: csr_matrix, *, upper_only: bool) -> list[int]:
    working = triu(matrix, k=1).tocoo() if upper_only else matrix.tocoo()
    groups: dict[int, list[int]] = {}
    for i, j in zip(working.row, working.col, strict=True):
        groups.setdefault(int(j - i), []).append(int(i))
    lengths = []
    for values in groups.values():
        lengths.extend(_run_lengths(np.sort(np.asarray(values, dtype=int))))
    return lengths


def _vertical_lengths(matrix: csr_matrix) -> list[int]:
    coo = matrix.tocoo()
    groups: dict[int, list[int]] = {}
    for i, j in zip(coo.row, coo.col, strict=True):
        groups.setdefault(int(j), []).append(int(i))
    lengths = []
    for values in groups.values():
        lengths.extend(_run_lengths(np.sort(np.asarray(values, dtype=int))))
    return lengths


def _line_entropy(lengths: list[int]) -> float:
    if not lengths:
        return float("nan")
    counts = np.asarray(list(Counter(lengths).values()), dtype=float)
    probabilities = counts / counts.sum()
    return float(-np.sum(probabilities * np.log(probabilities)))


def rqa_metrics(
    recurrence: RecurrenceResult,
    *,
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
) -> RQAResult:
    """Compute standard line-based recurrence-quantification metrics."""

    if min_diagonal_length < 1 or min_vertical_length < 1:
        raise ValueError("minimum line lengths must be positive integers")
    matrix = recurrence.matrix.astype(bool).tocsr()
    if recurrence.kind == "auto":
        upper = triu(matrix, k=1).tocsr()
        denominator_points = int(upper.nnz)
        diagonal_lengths_all = _diagonal_lengths(matrix, upper_only=True)
        if denominator_points:
            coo = upper.tocoo()
            weighted_lag = float(np.sum(coo.col - coo.row))
            corm = 100.0 * weighted_lag / (
                max(matrix.shape[0] - 1, 1) * denominator_points
            )
        else:
            corm = float("nan")
    elif recurrence.kind == "cross":
        denominator_points = int(matrix.nnz)
        diagonal_lengths_all = _diagonal_lengths(matrix, upper_only=False)
        corm = float("nan")
    else:
        raise ValueError(f"Unknown recurrence kind {recurrence.kind!r}")

    diagonal_lengths = [x for x in diagonal_lengths_all if x >= min_diagonal_length]
    vertical_lengths_all = _vertical_lengths(matrix)
    vertical_lengths = [x for x in vertical_lengths_all if x >= min_vertical_length]

    diagonal_points = int(sum(diagonal_lengths))
    vertical_points = int(sum(vertical_lengths))
    denominator_vertical = int(matrix.nnz)

    det = (
        diagonal_points / denominator_points
        if denominator_points
        else float("nan")
    )
    lam = (
        vertical_points / denominator_vertical
        if denominator_vertical
        else float("nan")
    )
    return RQAResult(
        recurrence_rate=float(recurrence.achieved_recurrence_rate),
        determinism=float(det),
        mean_diagonal_length=(
            float(np.mean(diagonal_lengths)) if diagonal_lengths else float("nan")
        ),
        max_diagonal_length=max(diagonal_lengths, default=0),
        diagonal_entropy=_line_entropy(diagonal_lengths),
        laminarity=float(lam),
        trapping_time=(
            float(np.mean(vertical_lengths)) if vertical_lengths else float("nan")
        ),
        max_vertical_length=max(vertical_lengths, default=0),
        center_of_recurrence_mass=float(corm),
        n_recurrence_points=denominator_points,
        n_diagonal_lines=len(diagonal_lengths),
        n_vertical_lines=len(vertical_lengths),
        min_diagonal_length=int(min_diagonal_length),
        min_vertical_length=int(min_vertical_length),
        provenance={
            "operation": "rqa_metrics",
            "recurrence_provenance": dict(recurrence.provenance),
            "min_diagonal_length": int(min_diagonal_length),
            "min_vertical_length": int(min_vertical_length),
            "corm_definition": (
                "100 * mean upper-triangle recurrence lag / (n-1)"
                if recurrence.kind == "auto"
                else "not_defined_for_cross_recurrence"
            ),
        },
    )


def cross_rqa_metrics(
    recurrence: RecurrenceResult,
    *,
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
) -> RQAResult:
    """Compute line-based metrics for a cross-recurrence result."""

    if recurrence.kind != "cross":
        raise ValueError("cross_rqa_metrics requires a cross-recurrence result")
    return rqa_metrics(
        recurrence,
        min_diagonal_length=min_diagonal_length,
        min_vertical_length=min_vertical_length,
    )


def windowed_rqa(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    window: float | int,
    step: float | int,
    window_units: str = "samples",
    step_units: str = "samples",
    radius: float | None = None,
    target_recurrence_rate: float | None = None,
    metric: str = "euclidean",
    theiler_window: float | int = 0,
    theiler_window_units: str = "samples",
    dimensions: Sequence[str] | None = None,
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
) -> WindowedRQAResult:
    """Compute RQA in full sliding windows while reporting any trailing tail."""

    window_samples = _resolve_samples(
        trajectories.time,
        window,
        units=window_units,
        time_unit=trajectories.time_unit,
        name="window",
    )
    step_samples = _resolve_samples(
        trajectories.time,
        step,
        units=step_units,
        time_unit=trajectories.time_unit,
        name="step",
    )
    if window_samples < 3:
        raise ValueError("window must contain at least three samples")
    if step_samples > window_samples:
        raise ValueError(
            "step cannot exceed window because that would leave internal samples "
            "unanalyzed; use step <= window"
        )
    index = _curve_index(trajectories, curve)
    starts = np.arange(0, trajectories.n_time - window_samples + 1, step_samples)
    if starts.size == 0:
        raise ValueError("window is longer than the available trajectory")

    rows = []
    for start in starts:
        stop = int(start + window_samples)
        subset = TrajectorySet(
            time=trajectories.time[start:stop],
            values=trajectories.values[index : index + 1, start:stop, :],
            curve_ids=(trajectories.curve_ids[index],),
            dimension_names=trajectories.dimension_names,
            metadata=trajectories.metadata.iloc[[index]].reset_index(drop=True),
            coordinate_system=trajectories.coordinate_system,
            time_unit=trajectories.time_unit,
            provenance={
                **dict(trajectories.provenance),
                "window_start_index": int(start),
                "window_stop_index": stop,
            },
        )
        rec = recurrence_matrix(
            subset,
            curve=0,
            radius=radius,
            target_recurrence_rate=target_recurrence_rate,
            metric=metric,
            theiler_window=theiler_window,
            theiler_window_units=theiler_window_units,
            dimensions=dimensions,
        )
        metrics = rqa_metrics(
            rec,
            min_diagonal_length=min_diagonal_length,
            min_vertical_length=min_vertical_length,
        )
        rows.append(
            {
                "start_index": int(start),
                "stop_index": stop,
                "start_time": float(trajectories.time[start]),
                "end_time": float(trajectories.time[stop - 1]),
                "center_time": float(
                    0.5 * (trajectories.time[start] + trajectories.time[stop - 1])
                ),
                "radius": rec.radius,
                "recurrence_rate": metrics.recurrence_rate,
                "determinism": metrics.determinism,
                "mean_diagonal_length": metrics.mean_diagonal_length,
                "max_diagonal_length": metrics.max_diagonal_length,
                "diagonal_entropy": metrics.diagonal_entropy,
                "laminarity": metrics.laminarity,
                "trapping_time": metrics.trapping_time,
                "max_vertical_length": metrics.max_vertical_length,
                "center_of_recurrence_mass": metrics.center_of_recurrence_mass,
            }
        )
    last_stop = int(starts[-1] + window_samples)
    dropped_tail = trajectories.n_time - last_stop
    return WindowedRQAResult(
        table=pd.DataFrame(rows),
        window_samples=window_samples,
        step_samples=step_samples,
        dropped_tail_samples=int(dropped_tail),
        time_unit=trajectories.time_unit,
        provenance={
            "operation": "windowed_rqa",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": trajectories.curve_ids[index],
            "window_samples": window_samples,
            "step_samples": step_samples,
            "dropped_tail_samples": int(dropped_tail),
            "tail_policy": "full_windows_only_with_explicit_tail_count",
            "radius_policy": "fixed" if radius is not None else "target_recurrence_rate",
        },
    )

_WINDOWED_RQA_FUNCTIONAL_METRIC_UNITS = {
    "recurrence_rate": "proportion",
    "determinism": "proportion",
    "mean_diagonal_length": "state_steps",
    "max_diagonal_length": "state_steps",
    "diagonal_entropy": "nats",
    "laminarity": "proportion",
    "trapping_time": "state_steps",
    "max_vertical_length": "state_steps",
    "center_of_recurrence_mass": "percent_of_sequence_length",
}


def windowed_rqa_trajectory_set(
    trajectories: TrajectorySet,
    *,
    metrics: Sequence[str],
    window: float | int,
    step: float | int,
    window_units: str = "samples",
    step_units: str = "samples",
    radius: float | None = None,
    target_recurrence_rate: float | None = None,
    metric: str = "euclidean",
    theiler_window: float | int = 0,
    theiler_window_units: str = "samples",
    dimensions: Sequence[str] | None = None,
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
    undefined_policy: str = "raise",
) -> WindowedRQAFunctionalResult:
    """Convert per-curve sliding-window RQA into functional trajectories.

    Every input curve is analyzed with the same declared recurrence contract.
    Window-center times become the common functional grid and selected RQA
    metrics become functional dimensions. The complete per-curve
    WindowedRQAResult objects are retained so solved radii and window-level
    diagnostics are never discarded.

    undefined_policy='raise' rejects any undefined selected metric.
    undefined_policy='keep' retains undefined values as NaN. No imputation is
    performed.

    Overlapping windows deterministically reuse source samples. The result
    records this overlap and never describes window rows as independent
    observations. If target_recurrence_rate is used, recurrence_rate cannot be
    selected as a functional outcome because its density is controlled by
    construction.
    """

    if trajectories.n_curves < 1:
        raise ValueError("functional windowed RQA requires at least one source curve")
    metric_names = tuple(str(name) for name in metrics)
    if not metric_names:
        raise ValueError("metrics must contain at least one RQA metric")
    if len(set(metric_names)) != len(metric_names):
        raise ValueError("metrics must be unique")
    unknown = [
        name
        for name in metric_names
        if name not in _WINDOWED_RQA_FUNCTIONAL_METRIC_UNITS
    ]
    if unknown:
        raise KeyError(f"Unknown functional RQA metrics: {unknown}")
    if undefined_policy not in {"raise", "keep"}:
        raise ValueError("undefined_policy must be 'raise' or 'keep'")
    if target_recurrence_rate is not None and "recurrence_rate" in metric_names:
        raise ValueError(
            "recurrence_rate cannot be a functional outcome when "
            "target_recurrence_rate controls recurrence density by design; "
            "use a fixed radius or omit recurrence_rate"
        )

    per_curve = tuple(
        windowed_rqa(
            trajectories,
            curve=curve_index,
            window=window,
            step=step,
            window_units=window_units,
            step_units=step_units,
            radius=radius,
            target_recurrence_rate=target_recurrence_rate,
            metric=metric,
            theiler_window=theiler_window,
            theiler_window_units=theiler_window_units,
            dimensions=dimensions,
            min_diagonal_length=min_diagonal_length,
            min_vertical_length=min_vertical_length,
        )
        for curve_index in range(trajectories.n_curves)
    )

    first = per_curve[0]
    center_time = first.table["center_time"].to_numpy(dtype=float)
    if center_time.size < 2:
        raise ValueError(
            "functional windowed RQA requires at least two complete windows; "
            "reduce window, reduce step, or provide a longer trajectory"
        )
    for result in per_curve[1:]:
        candidate_time = result.table["center_time"].to_numpy(dtype=float)
        if candidate_time.shape != center_time.shape or not np.array_equal(
            candidate_time,
            center_time,
        ):
            raise RuntimeError(
                "common-grid input produced inconsistent window-center grids"
            )
        if result.window_samples != first.window_samples:
            raise RuntimeError("window sample counts differ across curves")
        if result.step_samples != first.step_samples:
            raise RuntimeError("step sample counts differ across curves")
        if result.dropped_tail_samples != first.dropped_tail_samples:
            raise RuntimeError("tail accounting differs across curves")

    values = np.stack(
        [
            result.table.loc[:, list(metric_names)].to_numpy(dtype=float)
            for result in per_curve
        ],
        axis=0,
    )
    nonfinite = ~np.isfinite(values)
    if np.any(nonfinite) and undefined_policy == "raise":
        curve_index, window_index, metric_index = np.argwhere(nonfinite)[0]
        raise ValueError(
            "selected windowed RQA metric is undefined: "
            f"curve={trajectories.curve_ids[int(curve_index)]!r}, "
            f"window_index={int(window_index)}, "
            f"metric={metric_names[int(metric_index)]!r}; "
            "change the recurrence/line-threshold contract or set "
            "undefined_policy='keep' to retain NaN explicitly"
        )

    overlap_samples = max(first.window_samples - first.step_samples, 0)
    overlap_fraction = overlap_samples / first.window_samples
    functional = TrajectorySet(
        time=center_time,
        values=values,
        curve_ids=trajectories.curve_ids,
        dimension_names=metric_names,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system="rqa_metrics",
        time_unit=trajectories.time_unit,
        provenance={
            "operation": "windowed_rqa_trajectory_set",
            "source_provenance": dict(trajectories.provenance),
            "source_coordinate_system": trajectories.coordinate_system,
            "source_dimension_names": (
                tuple(dimensions) if dimensions is not None else None
            ),
            "metrics": metric_names,
            "metric_units": {
                name: _WINDOWED_RQA_FUNCTIONAL_METRIC_UNITS[name]
                for name in metric_names
            },
            "window_samples": first.window_samples,
            "step_samples": first.step_samples,
            "overlap_samples": overlap_samples,
            "overlap_fraction": float(overlap_fraction),
            "overlapping_windows": bool(overlap_samples > 0),
            "window_rows_are_independent": False,
            "window_center_definition": (
                "midpoint_of_first_and_last_observed_sample"
            ),
            "source_time_support": (
                float(trajectories.time[0]),
                float(trajectories.time[-1]),
            ),
            "functional_time_support": (
                float(center_time[0]),
                float(center_time[-1]),
            ),
            "leading_edge_span": float(center_time[0] - trajectories.time[0]),
            "trailing_edge_span": float(trajectories.time[-1] - center_time[-1]),
            "edge_policy": "full_window_centers_only",
            "dropped_tail_samples": first.dropped_tail_samples,
            "tail_policy": "full_windows_only_with_explicit_tail_count",
            "radius_policy": (
                "fixed" if radius is not None else "target_recurrence_rate"
            ),
            "fixed_radius": None if radius is None else float(radius),
            "target_recurrence_rate": (
                None
                if target_recurrence_rate is None
                else float(target_recurrence_rate)
            ),
            "recurrence_rate_controlled_by_design": bool(
                target_recurrence_rate is not None
            ),
            "distance_metric": metric,
            "theiler_window": theiler_window,
            "theiler_window_units": theiler_window_units,
            "min_diagonal_length": int(min_diagonal_length),
            "min_vertical_length": int(min_vertical_length),
            "undefined_policy": undefined_policy,
            "undefined_value_count": int(np.sum(nonfinite)),
            "downstream_note": (
                "Windowed metrics are functional summaries, not independent "
                "window-level observations; preserve the curve/participant "
                "sampling unit in downstream inference."
            ),
        },
    )
    return WindowedRQAFunctionalResult(
        trajectories=functional,
        window_results=per_curve,
        metrics=metric_names,
        window_samples=first.window_samples,
        step_samples=first.step_samples,
        overlap_samples=overlap_samples,
        overlap_fraction=float(overlap_fraction),
        dropped_tail_samples=first.dropped_tail_samples,
        time_unit=trajectories.time_unit,
        undefined_policy=undefined_policy,
        provenance={
            "operation": "windowed_rqa_trajectory_set",
            "functional_trajectory_provenance": dict(functional.provenance),
        },
    )

