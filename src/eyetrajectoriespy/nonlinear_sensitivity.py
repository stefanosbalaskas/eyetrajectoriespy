"""Declared-parameter sensitivity analyses for nonlinear trajectory methods."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

from .embedding import delay_embed_trajectory
from .nonlinear_dynamics import (
    estimate_largest_lyapunov_kantz,
    estimate_largest_lyapunov_rosenstein,
    kantz_divergence_curve,
    local_divergence_curve,
)
from .nonlinear_types import (
    KantzParameterSensitivityResult,
    LyapunovParameterSensitivityResult,
    RQAParameterSensitivityResult,
)
from .recurrence import recurrence_matrix, rqa_metrics
from .types import TrajectorySet


_RQA_METRICS = (
    "recurrence_rate",
    "determinism",
    "mean_diagonal_length",
    "max_diagonal_length",
    "diagonal_entropy",
    "laminarity",
    "trapping_time",
    "max_vertical_length",
    "center_of_recurrence_mass",
)

_LLE_SUMMARY_METRICS = (
    "exponent",
    "r_squared",
    "standard_error",
    "n_fit_points",
)

_KANTZ_LLE_SUMMARY_METRICS = (
    "exponent",
    "r_squared",
    "standard_error",
    "n_fit_points",
    "minimum_reference_count_in_fit",
    "minimum_pair_count_in_fit",
    "initial_supported_reference_fraction",
)


def _as_tuple(values: Sequence[Any], *, name: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a non-string sequence")
    out = tuple(values)
    if not out:
        raise ValueError(f"{name} must contain at least one value")
    return out


def _finite_numeric_grid(
    values: Sequence[float | int],
    *,
    name: str,
    positive: bool,
    allow_zero: bool = False,
) -> tuple[float | int, ...]:
    out = _as_tuple(values, name=name)
    normalized: list[float] = []
    for value in out:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value,
            (int, float, np.integer, np.floating),
        ):
            raise TypeError(f"{name} values must be numeric")
        numeric = float(value)
        if not np.isfinite(numeric):
            raise ValueError(f"{name} values must be finite")
        if positive and numeric <= 0:
            raise ValueError(f"{name} values must be positive")
        if allow_zero and numeric < 0:
            raise ValueError(f"{name} values must be non-negative")
        normalized.append(numeric)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicate numeric values")
    return out


def _positive_integer_grid(
    values: Sequence[int],
    *,
    name: str,
    minimum: int = 1,
) -> tuple[int, ...]:
    out = _as_tuple(values, name=name)
    normalized: list[int] = []
    for value in out:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise TypeError(f"{name} values must be integers")
        integer = int(value)
        if integer < minimum:
            raise ValueError(f"{name} values must be >= {minimum}")
        normalized.append(integer)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicate values")
    return tuple(normalized)


def _validate_dimensions(
    trajectories: TrajectorySet,
    dimensions: Sequence[str],
) -> tuple[str, ...]:
    names = _as_tuple(dimensions, name="dimensions")
    normalized = tuple(str(name) for name in names)
    if len(set(normalized)) != len(normalized):
        raise ValueError("dimensions must be unique")
    missing = [name for name in normalized if name not in trajectories.dimension_names]
    if missing:
        raise KeyError(f"Unknown trajectory dimensions: {missing}")
    return normalized


def _curve_id(trajectories: TrajectorySet, curve: int | str) -> str:
    if isinstance(curve, str):
        if curve not in trajectories.curve_ids:
            raise KeyError(f"Unknown curve_id {curve!r}")
        return curve
    if isinstance(curve, (bool, np.bool_)) or not isinstance(
        curve, (int, np.integer)
    ):
        raise TypeError("curve must be an integer index or curve_id string")
    index = int(curve)
    if index < 0 or index >= trajectories.n_curves:
        raise IndexError("curve index is out of range")
    return trajectories.curve_ids[index]


def _variation_summary(
    table: pd.DataFrame,
    metric_columns: Sequence[str],
    *,
    exponent_sign: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for metric in metric_columns:
        values = pd.to_numeric(table[metric], errors="coerce").to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        row: dict[str, float | int | str] = {
            "metric": metric,
            "n_specifications": int(values.size),
            "n_finite": int(finite.size),
            "finite_fraction": float(finite.size / values.size),
            "minimum": float(np.min(finite)) if finite.size else float("nan"),
            "q25": float(np.quantile(finite, 0.25)) if finite.size else float("nan"),
            "median": float(np.median(finite)) if finite.size else float("nan"),
            "q75": float(np.quantile(finite, 0.75)) if finite.size else float("nan"),
            "maximum": float(np.max(finite)) if finite.size else float("nan"),
            "range": (
                float(np.max(finite) - np.min(finite))
                if finite.size
                else float("nan")
            ),
            "standard_deviation": (
                float(np.std(finite, ddof=1))
                if finite.size > 1
                else float("nan")
            ),
        }
        if exponent_sign and metric == "exponent":
            positive = int(np.sum(finite > 0))
            negative = int(np.sum(finite < 0))
            zero = int(np.sum(finite == 0))
            row.update(
                {
                    "n_positive": positive,
                    "n_negative": negative,
                    "n_exact_zero": zero,
                    "positive_specification_fraction": (
                        float(positive / finite.size)
                        if finite.size
                        else float("nan")
                    ),
                    "negative_specification_fraction": (
                        float(negative / finite.size)
                        if finite.size
                        else float("nan")
                    ),
                }
            )
        else:
            row.update(
                {
                    "n_positive": 0,
                    "n_negative": 0,
                    "n_exact_zero": 0,
                    "positive_specification_fraction": float("nan"),
                    "negative_specification_fraction": float("nan"),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def rqa_parameter_sensitivity(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    embedding_dimensions: Sequence[int],
    delays: Sequence[float | int],
    theiler_windows: Sequence[float | int],
    min_diagonal_lengths: Sequence[int],
    min_vertical_lengths: Sequence[int],
    radii: Sequence[float] | None = None,
    target_recurrence_rates: Sequence[float] | None = None,
    delay_units: str = "samples",
    theiler_window_units: str = "samples",
    distance_metric: str = "euclidean",
) -> RQAParameterSensitivityResult:
    """Evaluate a predeclared RQA parameter multiverse without selecting a winner.

    Exactly one recurrence-threshold grid must be supplied: radii or
    target_recurrence_rates. Every Cartesian-product specification is
    evaluated. Invalid specifications fail the whole analysis with the
    offending combination identified; no failed row is silently discarded.

    The returned summaries are descriptive variation across the declared
    analysis choices. They are not sampling distributions, posterior
    probabilities, or automatic tuning criteria.
    """

    dimension_names = _validate_dimensions(trajectories, dimensions)
    curve_name = _curve_id(trajectories, curve)
    embedding_grid = _positive_integer_grid(
        embedding_dimensions,
        name="embedding_dimensions",
        minimum=2,
    )
    delay_grid = _finite_numeric_grid(
        delays,
        name="delays",
        positive=True,
    )
    theiler_grid = _finite_numeric_grid(
        theiler_windows,
        name="theiler_windows",
        positive=False,
        allow_zero=True,
    )
    diagonal_grid = _positive_integer_grid(
        min_diagonal_lengths,
        name="min_diagonal_lengths",
    )
    vertical_grid = _positive_integer_grid(
        min_vertical_lengths,
        name="min_vertical_lengths",
    )

    if (radii is None) == (target_recurrence_rates is None):
        raise ValueError(
            "supply exactly one sensitivity threshold grid: radii or "
            "target_recurrence_rates"
        )
    if radii is not None:
        threshold_grid = _finite_numeric_grid(
            radii,
            name="radii",
            positive=True,
        )
        threshold_policy = "fixed_radius"
    else:
        target_grid = _finite_numeric_grid(
            (
                target_recurrence_rates
                if target_recurrence_rates is not None
                else ()
            ),
            name="target_recurrence_rates",
            positive=True,
        )
        if any(float(value) >= 1 for value in target_grid):
            raise ValueError(
                "target_recurrence_rates must be strictly between 0 and 1"
            )
        threshold_grid = target_grid
        threshold_policy = "target_recurrence_rate"

    rows: list[dict[str, Any]] = []
    resolved_embedding_keys: set[tuple[int, int]] = set()
    resolved_specification_keys: set[tuple[Any, ...]] = set()

    for embedding_dimension, delay in product(embedding_grid, delay_grid):
        try:
            embedding = delay_embed_trajectory(
                trajectories,
                embedding_dimension=embedding_dimension,
                delay=delay,
                delay_units=delay_units,
                dimensions=dimension_names,
            )
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                "RQA sensitivity embedding failed for "
                f"embedding_dimension={embedding_dimension}, delay={delay!r} "
                f"{delay_units}: {exc}"
            ) from exc

        embedding_key = (embedding_dimension, embedding.delay_samples)
        if embedding_key in resolved_embedding_keys:
            raise ValueError(
                "two declared embedding specifications resolve to the same "
                f"(embedding_dimension, delay_samples)={embedding_key}; "
                "remove duplicate resolved specifications"
            )
        resolved_embedding_keys.add(embedding_key)

        for threshold, theiler_window in product(
            threshold_grid,
            theiler_grid,
        ):
            recurrence_kwargs: dict[str, Any] = {
                "curve": curve,
                "metric": distance_metric,
                "theiler_window": theiler_window,
                "theiler_window_units": theiler_window_units,
            }
            if threshold_policy == "fixed_radius":
                recurrence_kwargs["radius"] = float(threshold)
            else:
                recurrence_kwargs["target_recurrence_rate"] = float(threshold)

            try:
                recurrence = recurrence_matrix(
                    embedding,
                    **recurrence_kwargs,
                )
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                raise ValueError(
                    "RQA sensitivity recurrence failed for "
                    f"embedding_dimension={embedding_dimension}, "
                    f"delay={delay!r} {delay_units}, "
                    f"{threshold_policy}={float(threshold):.12g}, "
                    f"theiler_window={theiler_window!r} "
                    f"{theiler_window_units}: {exc}"
                ) from exc

            for min_diagonal_length, min_vertical_length in product(
                diagonal_grid,
                vertical_grid,
            ):
                specification_key = (
                    embedding_dimension,
                    embedding.delay_samples,
                    threshold_policy,
                    float(threshold),
                    recurrence.theiler_window_samples,
                    min_diagonal_length,
                    min_vertical_length,
                )
                if specification_key in resolved_specification_keys:
                    raise ValueError(
                        "two declared RQA specifications resolve to the same "
                        "sample-level analysis contract; remove duplicate "
                        "resolved specifications"
                    )
                resolved_specification_keys.add(specification_key)
                try:
                    metrics = rqa_metrics(
                        recurrence,
                        min_diagonal_length=min_diagonal_length,
                        min_vertical_length=min_vertical_length,
                    )
                except (TypeError, ValueError, KeyError, IndexError) as exc:
                    raise ValueError(
                        "RQA sensitivity metric calculation failed for "
                        f"embedding_dimension={embedding_dimension}, "
                        f"delay_samples={embedding.delay_samples}, "
                        f"{threshold_policy}={float(threshold):.12g}, "
                        f"theiler_window_samples="
                        f"{recurrence.theiler_window_samples}, "
                        f"min_diagonal_length={min_diagonal_length}, "
                        f"min_vertical_length={min_vertical_length}: {exc}"
                    ) from exc

                rows.append(
                    {
                        "embedding_dimension": embedding_dimension,
                        "requested_delay": float(delay),
                        "delay_units": delay_units,
                        "delay_samples": embedding.delay_samples,
                        "delay_time": embedding.delay_time,
                        "threshold_policy": threshold_policy,
                        "requested_radius": (
                            float(threshold)
                            if threshold_policy == "fixed_radius"
                            else float("nan")
                        ),
                        "requested_target_recurrence_rate": (
                            float(threshold)
                            if threshold_policy == "target_recurrence_rate"
                            else float("nan")
                        ),
                        "resolved_radius": recurrence.radius,
                        "achieved_recurrence_rate": recurrence.achieved_recurrence_rate,
                        "requested_theiler_window": float(theiler_window),
                        "theiler_window_units": theiler_window_units,
                        "theiler_window_samples": recurrence.theiler_window_samples,
                        "min_diagonal_length": min_diagonal_length,
                        "min_vertical_length": min_vertical_length,
                        "distance_metric": distance_metric,
                        "recurrence_rate": metrics.recurrence_rate,
                        "determinism": metrics.determinism,
                        "mean_diagonal_length": metrics.mean_diagonal_length,
                        "max_diagonal_length": metrics.max_diagonal_length,
                        "diagonal_entropy": metrics.diagonal_entropy,
                        "laminarity": metrics.laminarity,
                        "trapping_time": metrics.trapping_time,
                        "max_vertical_length": metrics.max_vertical_length,
                        "center_of_recurrence_mass": metrics.center_of_recurrence_mass,
                        "n_recurrence_points": metrics.n_recurrence_points,
                        "n_diagonal_lines": metrics.n_diagonal_lines,
                        "n_vertical_lines": metrics.n_vertical_lines,
                    }
                )

    table = pd.DataFrame(rows)
    table.insert(
        0,
        "specification_id",
        [f"spec_{index + 1}" for index in range(len(table))],
    )
    parameter_columns = (
        "embedding_dimension",
        "requested_delay",
        "delay_samples",
        "threshold_policy",
        "requested_radius",
        "requested_target_recurrence_rate",
        "resolved_radius",
        "requested_theiler_window",
        "theiler_window_samples",
        "min_diagonal_length",
        "min_vertical_length",
    )
    summary = _variation_summary(table, _RQA_METRICS)

    return RQAParameterSensitivityResult(
        table=table,
        summary_table=summary,
        parameter_columns=parameter_columns,
        metric_columns=_RQA_METRICS,
        curve_id=curve_name,
        provenance={
            "operation": "rqa_parameter_sensitivity",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": curve_name,
            "dimensions": dimension_names,
            "threshold_policy": threshold_policy,
            "delay_units": delay_units,
            "theiler_window_units": theiler_window_units,
            "distance_metric": distance_metric,
            "cartesian_product_evaluated": True,
            "n_specifications": len(table),
            "automatic_parameter_selection": False,
            "failed_specification_policy": "raise_entire_analysis",
            "summary_interpretation": (
                "descriptive variation over the analyst-declared parameter "
                "multiverse; not a sampling distribution"
            ),
            "controlled_metric_caution": (
                "under target-recurrence-rate sensitivity, recurrence_rate is "
                "controlled by design and should not be interpreted as an "
                "independent robustness outcome"
            ),
            "matrices_retained": False,
            "memory_contract": (
                "sensitivity retains tidy metrics/provenance rather than one "
                "sparse recurrence matrix per specification"
            ),
        },
    )


def _validate_fit_intervals(
    fit_intervals: Sequence[tuple[float | int, float | int]],
) -> tuple[tuple[float | int, float | int], ...]:
    intervals = _as_tuple(fit_intervals, name="fit_intervals")
    normalized: list[tuple[float | int, float | int]] = []
    numeric_pairs: list[tuple[float, float]] = []
    for index, interval in enumerate(intervals):
        if (
            not isinstance(interval, Sequence)
            or isinstance(interval, (str, bytes))
            or len(interval) != 2
        ):
            raise ValueError(
                f"fit_intervals[{index}] must contain exactly (start, end)"
            )
        start, end = interval
        values = _finite_numeric_grid(
            (start, end),
            name=f"fit_intervals[{index}]",
            positive=False,
            allow_zero=True,
        )
        if float(values[1]) <= float(values[0]):
            raise ValueError(
                f"fit_intervals[{index}] end must be greater than start"
            )
        pair = (float(values[0]), float(values[1]))
        if pair in numeric_pairs:
            raise ValueError("fit_intervals must not contain duplicates")
        numeric_pairs.append(pair)
        normalized.append((start, end))
    return tuple(normalized)



def kantz_parameter_sensitivity(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    embedding_dimensions: Sequence[int],
    delays: Sequence[float | int],
    radii: Sequence[float],
    min_neighbors: Sequence[int],
    theiler_windows: Sequence[float | int],
    fit_intervals: Sequence[tuple[float | int, float | int]],
    max_horizon: float | int,
    delay_units: str = "samples",
    theiler_window_units: str = "samples",
    fit_units: str = "samples",
    max_horizon_units: str = "samples",
) -> KantzParameterSensitivityResult:
    """Evaluate a declared Kantz-LLE parameter multiverse without tuning.

    Every Cartesian-product specification is evaluated. Divergence curves are
    reused across fit intervals for the same resolved embedding, radius,
    minimum-neighbor, and Theiler contract. Invalid specifications fail the
    whole analysis and identify the offending combination.

    Variation across specifications is descriptive sensitivity, not a sampling
    distribution and not a probability of deterministic chaos.
    """

    dimension_names = _validate_dimensions(trajectories, dimensions)
    curve_name = _curve_id(trajectories, curve)
    embedding_grid = _positive_integer_grid(
        embedding_dimensions,
        name="embedding_dimensions",
        minimum=2,
    )
    delay_grid = _finite_numeric_grid(
        delays,
        name="delays",
        positive=True,
    )
    radius_grid = _finite_numeric_grid(
        radii,
        name="radii",
        positive=True,
    )
    min_neighbor_grid = _positive_integer_grid(
        min_neighbors,
        name="min_neighbors",
        minimum=1,
    )
    theiler_grid = _finite_numeric_grid(
        theiler_windows,
        name="theiler_windows",
        positive=False,
        allow_zero=True,
    )
    intervals = _validate_fit_intervals(fit_intervals)
    if isinstance(max_horizon, (bool, np.bool_)) or not isinstance(
        max_horizon,
        (int, float, np.integer, np.floating),
    ):
        raise TypeError("max_horizon must be numeric")
    if not np.isfinite(float(max_horizon)) or float(max_horizon) <= 0:
        raise ValueError("max_horizon must be positive and finite")

    rows: list[dict[str, Any]] = []
    resolved_embedding_keys: set[tuple[int, int]] = set()
    resolved_specification_keys: set[tuple[Any, ...]] = set()
    exponent_unit: str | None = None

    for embedding_dimension, delay in product(embedding_grid, delay_grid):
        try:
            embedding = delay_embed_trajectory(
                trajectories,
                embedding_dimension=embedding_dimension,
                delay=delay,
                delay_units=delay_units,
                dimensions=dimension_names,
            )
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                "Kantz sensitivity embedding failed for "
                f"embedding_dimension={embedding_dimension}, delay={delay!r} "
                f"{delay_units}: {exc}"
            ) from exc

        embedding_key = (embedding_dimension, embedding.delay_samples)
        if embedding_key in resolved_embedding_keys:
            raise ValueError(
                "two declared embedding specifications resolve to the same "
                f"(embedding_dimension, delay_samples)={embedding_key}; "
                "remove duplicate resolved specifications"
            )
        resolved_embedding_keys.add(embedding_key)

        for radius, minimum_neighbors, theiler_window in product(
            radius_grid,
            min_neighbor_grid,
            theiler_grid,
        ):
            try:
                divergence = kantz_divergence_curve(
                    embedding,
                    curve=curve,
                    radius=float(radius),
                    min_neighbors=minimum_neighbors,
                    theiler_window=theiler_window,
                    theiler_window_units=theiler_window_units,
                    max_horizon=max_horizon,
                    max_horizon_units=max_horizon_units,
                )
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                raise ValueError(
                    "Kantz sensitivity divergence failed for "
                    f"embedding_dimension={embedding_dimension}, "
                    f"delay_samples={embedding.delay_samples}, "
                    f"radius={float(radius):.12g}, "
                    f"min_neighbors={minimum_neighbors}, "
                    f"theiler_window={theiler_window!r} "
                    f"{theiler_window_units}: {exc}"
                ) from exc

            initial_supported_fraction = float(
                np.mean(divergence.initial_neighbor_counts >= minimum_neighbors)
            )

            for fit_start, fit_end in intervals:
                try:
                    estimate = estimate_largest_lyapunov_kantz(
                        divergence,
                        fit_start=fit_start,
                        fit_end=fit_end,
                        fit_units=fit_units,
                    )
                except (TypeError, ValueError, KeyError, IndexError) as exc:
                    raise ValueError(
                        "Kantz sensitivity fit failed for "
                        f"embedding_dimension={embedding_dimension}, "
                        f"delay_samples={embedding.delay_samples}, "
                        f"radius={float(radius):.12g}, "
                        f"min_neighbors={minimum_neighbors}, "
                        f"theiler_window_samples="
                        f"{divergence.theiler_window_samples}, "
                        f"fit_interval=({fit_start!r}, {fit_end!r}) "
                        f"{fit_units}: {exc}"
                    ) from exc

                fit_start_samples = int(estimate.provenance["fit_start_samples"])
                fit_end_samples = int(estimate.provenance["fit_end_samples"])
                specification_key = (
                    embedding_dimension,
                    embedding.delay_samples,
                    float(radius),
                    int(minimum_neighbors),
                    divergence.theiler_window_samples,
                    fit_start_samples,
                    fit_end_samples,
                )
                if specification_key in resolved_specification_keys:
                    raise ValueError(
                        "two declared Kantz specifications resolve to the same "
                        "sample-level reconstruction/neighborhood/fit contract; "
                        "remove duplicate resolved specifications"
                    )
                resolved_specification_keys.add(specification_key)

                if exponent_unit is None:
                    exponent_unit = estimate.exponent_unit
                elif exponent_unit != estimate.exponent_unit:
                    raise RuntimeError(
                        "Kantz sensitivity produced inconsistent exponent units"
                    )

                fit_mask = (
                    (divergence.horizons >= fit_start_samples)
                    & (divergence.horizons <= fit_end_samples)
                )
                fit_reference_counts = divergence.reference_counts[fit_mask]
                fit_pair_counts = divergence.pair_counts[fit_mask]
                fit_zero_counts = divergence.zero_mean_neighborhood_counts[fit_mask]

                rows.append(
                    {
                        "embedding_dimension": embedding_dimension,
                        "requested_delay": float(delay),
                        "delay_units": delay_units,
                        "delay_samples": embedding.delay_samples,
                        "delay_time": embedding.delay_time,
                        "radius": float(radius),
                        "min_neighbors": int(minimum_neighbors),
                        "requested_theiler_window": float(theiler_window),
                        "theiler_window_units": theiler_window_units,
                        "theiler_window_samples": divergence.theiler_window_samples,
                        "requested_fit_start": float(fit_start),
                        "requested_fit_end": float(fit_end),
                        "fit_units": fit_units,
                        "fit_start_samples": fit_start_samples,
                        "fit_end_samples": fit_end_samples,
                        "resolved_fit_start_time": estimate.fit_start,
                        "resolved_fit_end_time": estimate.fit_end,
                        "requested_max_horizon": float(max_horizon),
                        "max_horizon_units": max_horizon_units,
                        "max_horizon_samples": divergence.max_horizon_samples,
                        "exponent": estimate.exponent,
                        "exponent_unit": estimate.exponent_unit,
                        "r_squared": estimate.r_squared,
                        "standard_error": estimate.standard_error,
                        "intercept": estimate.intercept,
                        "n_fit_points": estimate.n_fit_points,
                        "initial_supported_reference_fraction": (
                            initial_supported_fraction
                        ),
                        "minimum_reference_count_in_fit": (
                            int(np.min(fit_reference_counts))
                            if fit_reference_counts.size
                            else 0
                        ),
                        "minimum_pair_count_in_fit": (
                            int(np.min(fit_pair_counts))
                            if fit_pair_counts.size
                            else 0
                        ),
                        "total_zero_mean_neighborhood_count_in_fit": int(
                            np.sum(fit_zero_counts)
                        ),
                    }
                )

    table = pd.DataFrame(rows)
    table.insert(
        0,
        "specification_id",
        [f"spec_{index + 1}" for index in range(len(table))],
    )
    parameter_columns = (
        "embedding_dimension",
        "requested_delay",
        "delay_samples",
        "radius",
        "min_neighbors",
        "requested_theiler_window",
        "theiler_window_samples",
        "requested_fit_start",
        "requested_fit_end",
        "fit_start_samples",
        "fit_end_samples",
    )
    summary = _variation_summary(
        table,
        _KANTZ_LLE_SUMMARY_METRICS,
        exponent_sign=True,
    )
    if exponent_unit is None:
        raise RuntimeError(
            "Kantz sensitivity unexpectedly produced no specifications"
        )

    return KantzParameterSensitivityResult(
        table=table,
        summary_table=summary,
        parameter_columns=parameter_columns,
        curve_id=curve_name,
        exponent_unit=exponent_unit,
        provenance={
            "operation": "kantz_parameter_sensitivity",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": curve_name,
            "dimensions": dimension_names,
            "delay_units": delay_units,
            "theiler_window_units": theiler_window_units,
            "fit_units": fit_units,
            "max_horizon_units": max_horizon_units,
            "cartesian_product_evaluated": True,
            "n_specifications": len(table),
            "automatic_parameter_selection": False,
            "automatic_radius_selection": False,
            "automatic_fit_interval_selection": False,
            "failed_specification_policy": "raise_entire_analysis",
            "divergence_reuse": (
                "one Kantz divergence curve per resolved embedding/radius/"
                "min-neighbors/Theiler specification, reused across declared "
                "fit intervals"
            ),
            "positive_fraction_interpretation": (
                "descriptive fraction of the analyst-declared sensitivity grid "
                "with exponent > 0; not a probability of deterministic chaos"
            ),
            "support_fraction_interpretation": (
                "fraction of reconstructed reference states satisfying the "
                "declared minimum-neighbor rule at horizon zero; descriptive "
                "support diagnostic, not an inferential weight"
            ),
            "summary_interpretation": (
                "descriptive variation over the analyst-declared parameter "
                "multiverse; not a sampling distribution"
            ),
        },
    )


def lyapunov_parameter_sensitivity(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    embedding_dimensions: Sequence[int],
    delays: Sequence[float | int],
    theiler_windows: Sequence[float | int],
    fit_intervals: Sequence[tuple[float | int, float | int]],
    max_horizon: float | int,
    delay_units: str = "samples",
    theiler_window_units: str = "samples",
    fit_units: str = "samples",
    max_horizon_units: str = "samples",
) -> LyapunovParameterSensitivityResult:
    """Evaluate declared Rosenstein-LLE reconstruction and fit choices.

    Divergence curves are reused across fit intervals for the same embedding
    and Theiler specification. No fit interval, embedding dimension, delay, or
    Theiler window is selected automatically.

    The fraction of declared specifications with positive exponents is a
    descriptive property of the analyst-specified grid. It is not a
    probability that the system is chaotic.
    """

    dimension_names = _validate_dimensions(trajectories, dimensions)
    curve_name = _curve_id(trajectories, curve)
    embedding_grid = _positive_integer_grid(
        embedding_dimensions,
        name="embedding_dimensions",
        minimum=2,
    )
    delay_grid = _finite_numeric_grid(
        delays,
        name="delays",
        positive=True,
    )
    theiler_grid = _finite_numeric_grid(
        theiler_windows,
        name="theiler_windows",
        positive=False,
        allow_zero=True,
    )
    intervals = _validate_fit_intervals(fit_intervals)
    if isinstance(max_horizon, (bool, np.bool_)) or not isinstance(
        max_horizon,
        (int, float, np.integer, np.floating),
    ):
        raise TypeError("max_horizon must be numeric")
    if not np.isfinite(float(max_horizon)) or float(max_horizon) <= 0:
        raise ValueError("max_horizon must be positive and finite")

    rows: list[dict[str, Any]] = []
    resolved_embedding_keys: set[tuple[int, int]] = set()
    resolved_specification_keys: set[tuple[Any, ...]] = set()
    exponent_unit: str | None = None

    for embedding_dimension, delay in product(embedding_grid, delay_grid):
        try:
            embedding = delay_embed_trajectory(
                trajectories,
                embedding_dimension=embedding_dimension,
                delay=delay,
                delay_units=delay_units,
                dimensions=dimension_names,
            )
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                "LLE sensitivity embedding failed for "
                f"embedding_dimension={embedding_dimension}, delay={delay!r} "
                f"{delay_units}: {exc}"
            ) from exc

        embedding_key = (embedding_dimension, embedding.delay_samples)
        if embedding_key in resolved_embedding_keys:
            raise ValueError(
                "two declared embedding specifications resolve to the same "
                f"(embedding_dimension, delay_samples)={embedding_key}; "
                "remove duplicate resolved specifications"
            )
        resolved_embedding_keys.add(embedding_key)

        for theiler_window in theiler_grid:
            try:
                divergence = local_divergence_curve(
                    embedding,
                    curve=curve,
                    theiler_window=theiler_window,
                    theiler_window_units=theiler_window_units,
                    max_horizon=max_horizon,
                    max_horizon_units=max_horizon_units,
                )
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                raise ValueError(
                    "LLE sensitivity divergence failed for "
                    f"embedding_dimension={embedding_dimension}, "
                    f"delay_samples={embedding.delay_samples}, "
                    f"theiler_window={theiler_window!r} "
                    f"{theiler_window_units}: {exc}"
                ) from exc

            for fit_start, fit_end in intervals:
                try:
                    estimate = estimate_largest_lyapunov_rosenstein(
                        divergence,
                        fit_start=fit_start,
                        fit_end=fit_end,
                        fit_units=fit_units,
                    )
                except (TypeError, ValueError, KeyError, IndexError) as exc:
                    raise ValueError(
                        "LLE sensitivity fit failed for "
                        f"embedding_dimension={embedding_dimension}, "
                        f"delay_samples={embedding.delay_samples}, "
                        f"theiler_window_samples={divergence.theiler_window_samples}, "
                        f"fit_interval=({fit_start!r}, {fit_end!r}) "
                        f"{fit_units}: {exc}"
                    ) from exc

                fit_start_samples = int(estimate.provenance["fit_start_samples"])
                fit_end_samples = int(estimate.provenance["fit_end_samples"])
                specification_key = (
                    embedding_dimension,
                    embedding.delay_samples,
                    divergence.theiler_window_samples,
                    fit_start_samples,
                    fit_end_samples,
                )
                if specification_key in resolved_specification_keys:
                    raise ValueError(
                        "two declared LLE specifications resolve to the same "
                        "sample-level reconstruction/fit contract; remove "
                        "duplicate resolved specifications"
                    )
                resolved_specification_keys.add(specification_key)

                if exponent_unit is None:
                    exponent_unit = estimate.exponent_unit
                elif exponent_unit != estimate.exponent_unit:
                    raise RuntimeError(
                        "LLE sensitivity produced inconsistent exponent units"
                    )

                fit_mask = (
                    (divergence.horizons >= fit_start_samples)
                    & (divergence.horizons <= fit_end_samples)
                )
                fit_pair_counts = divergence.pair_counts[fit_mask]
                fit_zero_counts = divergence.zero_distance_counts[fit_mask]
                rows.append(
                    {
                        "embedding_dimension": embedding_dimension,
                        "requested_delay": float(delay),
                        "delay_units": delay_units,
                        "delay_samples": embedding.delay_samples,
                        "delay_time": embedding.delay_time,
                        "requested_theiler_window": float(theiler_window),
                        "theiler_window_units": theiler_window_units,
                        "theiler_window_samples": divergence.theiler_window_samples,
                        "requested_fit_start": float(fit_start),
                        "requested_fit_end": float(fit_end),
                        "fit_units": fit_units,
                        "fit_start_samples": fit_start_samples,
                        "fit_end_samples": fit_end_samples,
                        "resolved_fit_start_time": estimate.fit_start,
                        "resolved_fit_end_time": estimate.fit_end,
                        "requested_max_horizon": float(max_horizon),
                        "max_horizon_units": max_horizon_units,
                        "max_horizon_samples": divergence.max_horizon_samples,
                        "exponent": estimate.exponent,
                        "exponent_unit": estimate.exponent_unit,
                        "r_squared": estimate.r_squared,
                        "standard_error": estimate.standard_error,
                        "intercept": estimate.intercept,
                        "n_fit_points": estimate.n_fit_points,
                        "minimum_pair_count_in_fit": (
                            int(np.min(fit_pair_counts))
                            if fit_pair_counts.size
                            else 0
                        ),
                        "total_zero_distance_count_in_fit": int(
                            np.sum(fit_zero_counts)
                        ),
                    }
                )

    table = pd.DataFrame(rows)
    table.insert(
        0,
        "specification_id",
        [f"spec_{index + 1}" for index in range(len(table))],
    )
    parameter_columns = (
        "embedding_dimension",
        "requested_delay",
        "delay_samples",
        "requested_theiler_window",
        "theiler_window_samples",
        "requested_fit_start",
        "requested_fit_end",
        "fit_start_samples",
        "fit_end_samples",
    )
    summary = _variation_summary(
        table,
        _LLE_SUMMARY_METRICS,
        exponent_sign=True,
    )
    if exponent_unit is None:
        raise RuntimeError("LLE sensitivity unexpectedly produced no specifications")

    return LyapunovParameterSensitivityResult(
        table=table,
        summary_table=summary,
        parameter_columns=parameter_columns,
        curve_id=curve_name,
        exponent_unit=exponent_unit,
        provenance={
            "operation": "lyapunov_parameter_sensitivity",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": curve_name,
            "dimensions": dimension_names,
            "delay_units": delay_units,
            "theiler_window_units": theiler_window_units,
            "fit_units": fit_units,
            "max_horizon_units": max_horizon_units,
            "cartesian_product_evaluated": True,
            "n_specifications": len(table),
            "automatic_parameter_selection": False,
            "automatic_fit_interval_selection": False,
            "failed_specification_policy": "raise_entire_analysis",
            "divergence_reuse": (
                "one divergence curve per resolved embedding/Theiler "
                "specification, reused across declared fit intervals"
            ),
            "positive_fraction_interpretation": (
                "descriptive fraction of the analyst-declared sensitivity grid "
                "with exponent > 0; not a probability of deterministic chaos"
            ),
            "summary_interpretation": (
                "descriptive variation over the analyst-declared parameter "
                "multiverse; not a sampling distribution"
            ),
        },
    )


def kantz_parameter_sensitivity(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    embedding_dimensions: Sequence[int],
    delays: Sequence[float | int],
    radii: Sequence[float],
    min_neighbors: Sequence[int],
    theiler_windows: Sequence[float | int],
    fit_intervals: Sequence[tuple[float | int, float | int]],
    max_horizon: float | int,
    delay_units: str = "samples",
    theiler_window_units: str = "samples",
    fit_units: str = "samples",
    max_horizon_units: str = "samples",
) -> KantzParameterSensitivityResult:
    """Evaluate a declared Kantz-LLE parameter multiverse without tuning.

    Every Cartesian-product specification is evaluated. Divergence curves are
    reused across fit intervals for the same resolved embedding, radius,
    minimum-neighbor, and Theiler contract. Invalid specifications fail the
    complete analysis rather than being silently removed.

    The resulting ranges and sign fractions describe sensitivity across the
    analyst-declared grid. They are not confidence intervals, posterior
    probabilities, or probabilities that the source dynamics are chaotic.
    """

    dimension_names = _validate_dimensions(trajectories, dimensions)
    curve_name = _curve_id(trajectories, curve)
    embedding_grid = _positive_integer_grid(
        embedding_dimensions,
        name="embedding_dimensions",
        minimum=2,
    )
    delay_grid = _finite_numeric_grid(
        delays,
        name="delays",
        positive=True,
    )
    radius_grid = _finite_numeric_grid(
        radii,
        name="radii",
        positive=True,
    )
    neighbor_grid = _positive_integer_grid(
        min_neighbors,
        name="min_neighbors",
        minimum=1,
    )
    theiler_grid = _finite_numeric_grid(
        theiler_windows,
        name="theiler_windows",
        positive=False,
        allow_zero=True,
    )
    intervals = _validate_fit_intervals(fit_intervals)

    if isinstance(max_horizon, (bool, np.bool_)) or not isinstance(
        max_horizon,
        (int, float, np.integer, np.floating),
    ):
        raise TypeError("max_horizon must be numeric")
    if not np.isfinite(float(max_horizon)) or float(max_horizon) <= 0:
        raise ValueError("max_horizon must be positive and finite")

    rows: list[dict[str, Any]] = []
    resolved_embedding_keys: set[tuple[int, int]] = set()
    resolved_divergence_keys: set[tuple[Any, ...]] = set()
    resolved_specification_keys: set[tuple[Any, ...]] = set()
    exponent_unit: str | None = None

    for embedding_dimension, delay in product(embedding_grid, delay_grid):
        try:
            embedding = delay_embed_trajectory(
                trajectories,
                embedding_dimension=embedding_dimension,
                delay=delay,
                delay_units=delay_units,
                dimensions=dimension_names,
            )
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                "Kantz sensitivity embedding failed for "
                f"embedding_dimension={embedding_dimension}, delay={delay!r} "
                f"{delay_units}: {exc}"
            ) from exc

        embedding_key = (embedding_dimension, embedding.delay_samples)
        if embedding_key in resolved_embedding_keys:
            raise ValueError(
                "two declared embedding specifications resolve to the same "
                f"(embedding_dimension, delay_samples)={embedding_key}; "
                "remove duplicate resolved specifications"
            )
        resolved_embedding_keys.add(embedding_key)

        for radius, minimum_neighbors, theiler_window in product(
            radius_grid,
            neighbor_grid,
            theiler_grid,
        ):
            try:
                divergence = kantz_divergence_curve(
                    embedding,
                    curve=curve,
                    radius=float(radius),
                    min_neighbors=minimum_neighbors,
                    theiler_window=theiler_window,
                    theiler_window_units=theiler_window_units,
                    max_horizon=max_horizon,
                    max_horizon_units=max_horizon_units,
                )
            except (TypeError, ValueError, KeyError, IndexError) as exc:
                raise ValueError(
                    "Kantz sensitivity divergence failed for "
                    f"embedding_dimension={embedding_dimension}, "
                    f"delay_samples={embedding.delay_samples}, "
                    f"radius={float(radius):.12g}, "
                    f"min_neighbors={minimum_neighbors}, "
                    f"theiler_window={theiler_window!r} "
                    f"{theiler_window_units}: {exc}"
                ) from exc

            divergence_key = (
                embedding_dimension,
                embedding.delay_samples,
                float(radius),
                minimum_neighbors,
                divergence.theiler_window_samples,
            )
            if divergence_key in resolved_divergence_keys:
                raise ValueError(
                    "two declared Kantz divergence specifications resolve to "
                    "the same sample-level neighborhood contract; remove "
                    "duplicate resolved specifications"
                )
            resolved_divergence_keys.add(divergence_key)

            initial_counts = divergence.initial_neighbor_counts.astype(float)
            supported_initial = divergence.initial_neighbor_counts >= minimum_neighbors
            initial_supported_fraction = float(np.mean(supported_initial))

            for fit_start, fit_end in intervals:
                try:
                    estimate = estimate_largest_lyapunov_kantz(
                        divergence,
                        fit_start=fit_start,
                        fit_end=fit_end,
                        fit_units=fit_units,
                    )
                except (TypeError, ValueError, KeyError, IndexError) as exc:
                    raise ValueError(
                        "Kantz sensitivity fit failed for "
                        f"embedding_dimension={embedding_dimension}, "
                        f"delay_samples={embedding.delay_samples}, "
                        f"radius={float(radius):.12g}, "
                        f"min_neighbors={minimum_neighbors}, "
                        f"theiler_window_samples="
                        f"{divergence.theiler_window_samples}, "
                        f"fit_interval=({fit_start!r}, {fit_end!r}) "
                        f"{fit_units}: {exc}"
                    ) from exc

                fit_start_samples = int(estimate.provenance["fit_start_samples"])
                fit_end_samples = int(estimate.provenance["fit_end_samples"])
                specification_key = (
                    *divergence_key,
                    fit_start_samples,
                    fit_end_samples,
                )
                if specification_key in resolved_specification_keys:
                    raise ValueError(
                        "two declared Kantz LLE specifications resolve to the "
                        "same sample-level neighborhood/fit contract; remove "
                        "duplicate resolved specifications"
                    )
                resolved_specification_keys.add(specification_key)

                if exponent_unit is None:
                    exponent_unit = estimate.exponent_unit
                elif exponent_unit != estimate.exponent_unit:
                    raise RuntimeError(
                        "Kantz sensitivity produced inconsistent exponent units"
                    )

                fit_mask = (
                    (divergence.horizons >= fit_start_samples)
                    & (divergence.horizons <= fit_end_samples)
                )
                fit_reference_counts = divergence.reference_counts[fit_mask]
                fit_pair_counts = divergence.pair_counts[fit_mask]
                fit_zero_counts = divergence.zero_mean_neighborhood_counts[fit_mask]

                rows.append(
                    {
                        "embedding_dimension": embedding_dimension,
                        "requested_delay": float(delay),
                        "delay_units": delay_units,
                        "delay_samples": embedding.delay_samples,
                        "delay_time": embedding.delay_time,
                        "requested_radius": float(radius),
                        "resolved_radius": divergence.radius,
                        "min_neighbors": minimum_neighbors,
                        "requested_theiler_window": float(theiler_window),
                        "theiler_window_units": theiler_window_units,
                        "theiler_window_samples": divergence.theiler_window_samples,
                        "requested_fit_start": float(fit_start),
                        "requested_fit_end": float(fit_end),
                        "fit_units": fit_units,
                        "fit_start_samples": fit_start_samples,
                        "fit_end_samples": fit_end_samples,
                        "resolved_fit_start_time": estimate.fit_start,
                        "resolved_fit_end_time": estimate.fit_end,
                        "requested_max_horizon": float(max_horizon),
                        "max_horizon_units": max_horizon_units,
                        "max_horizon_samples": divergence.max_horizon_samples,
                        "exponent": estimate.exponent,
                        "exponent_unit": estimate.exponent_unit,
                        "r_squared": estimate.r_squared,
                        "standard_error": estimate.standard_error,
                        "intercept": estimate.intercept,
                        "n_fit_points": estimate.n_fit_points,
                        "minimum_reference_count_in_fit": (
                            int(np.min(fit_reference_counts))
                            if fit_reference_counts.size
                            else 0
                        ),
                        "minimum_pair_count_in_fit": (
                            int(np.min(fit_pair_counts))
                            if fit_pair_counts.size
                            else 0
                        ),
                        "total_zero_mean_neighborhood_count_in_fit": int(
                            np.sum(fit_zero_counts)
                        ),
                        "initial_neighbor_count_minimum": float(
                            np.min(initial_counts)
                        ),
                        "initial_neighbor_count_median": float(
                            np.median(initial_counts)
                        ),
                        "initial_neighbor_count_maximum": float(
                            np.max(initial_counts)
                        ),
                        "initial_supported_reference_fraction": (
                            initial_supported_fraction
                        ),
                    }
                )

    table = pd.DataFrame(rows)
    table.insert(
        0,
        "specification_id",
        [f"spec_{index + 1}" for index in range(len(table))],
    )
    parameter_columns = (
        "embedding_dimension",
        "requested_delay",
        "delay_samples",
        "requested_radius",
        "resolved_radius",
        "min_neighbors",
        "requested_theiler_window",
        "theiler_window_samples",
        "requested_fit_start",
        "requested_fit_end",
        "fit_start_samples",
        "fit_end_samples",
    )
    summary = _variation_summary(
        table,
        _KANTZ_LLE_SUMMARY_METRICS,
        exponent_sign=True,
    )
    if exponent_unit is None:
        raise RuntimeError(
            "Kantz sensitivity unexpectedly produced no specifications"
        )

    return KantzParameterSensitivityResult(
        table=table,
        summary_table=summary,
        parameter_columns=parameter_columns,
        curve_id=curve_name,
        exponent_unit=exponent_unit,
        provenance={
            "operation": "kantz_parameter_sensitivity",
            "estimator_family": "Kantz fixed-radius neighborhood divergence",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": curve_name,
            "dimensions": dimension_names,
            "delay_units": delay_units,
            "theiler_window_units": theiler_window_units,
            "fit_units": fit_units,
            "max_horizon_units": max_horizon_units,
            "cartesian_product_evaluated": True,
            "n_specifications": len(table),
            "automatic_parameter_selection": False,
            "automatic_radius_selection": False,
            "automatic_fit_interval_selection": False,
            "adaptive_radius_expansion": False,
            "failed_specification_policy": "raise_entire_analysis",
            "divergence_reuse": (
                "one Kantz divergence curve per resolved embedding/radius/"
                "minimum-neighbor/Theiler specification, reused across "
                "declared fit intervals"
            ),
            "positive_fraction_interpretation": (
                "descriptive fraction of the analyst-declared sensitivity grid "
                "with exponent > 0; not a probability of deterministic chaos"
            ),
            "summary_interpretation": (
                "descriptive variation over the analyst-declared parameter "
                "multiverse; not a sampling distribution"
            ),
            "support_diagnostics": (
                "reference/pair support and zero-mean-neighborhood counts are "
                "retained for each specification rather than converted into "
                "an automatic quality threshold"
            ),
        },
    )
