"""Population-level uncertainty for per-curve recurrence quantification."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from .embedding import delay_embed_trajectory
from .nonlinear_types import RQAMeanBootstrapResult
from .recurrence import recurrence_matrix, rqa_metrics
from .types import TrajectorySet
from .validation import validate_trajectory_set


_ALLOWED_RQA_METRICS = (
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


def _validate_metrics(
    metrics: Sequence[str],
    *,
    target_recurrence_rate: float | None,
) -> tuple[str, ...]:
    if isinstance(metrics, (str, bytes)):
        raise TypeError("metrics must be a non-string sequence")
    names = tuple(str(metric) for metric in metrics)
    if not names:
        raise ValueError("metrics must contain at least one RQA metric")
    if len(set(names)) != len(names):
        raise ValueError("metrics must not contain duplicates")
    unknown = [metric for metric in names if metric not in _ALLOWED_RQA_METRICS]
    if unknown:
        raise KeyError(f"Unknown RQA metrics: {unknown}")
    if target_recurrence_rate is not None and "recurrence_rate" in names:
        raise ValueError(
            "recurrence_rate is controlled by target_recurrence_rate and "
            "cannot be treated as an independent bootstrap outcome"
        )
    return names


def _validate_bootstrap_controls(
    *,
    confidence_level: float,
    n_bootstrap: int,
) -> None:
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if isinstance(n_bootstrap, (bool, np.bool_)) or not isinstance(
        n_bootstrap, (int, np.integer)
    ):
        raise TypeError("n_bootstrap must be an integer")
    if int(n_bootstrap) < 100:
        raise ValueError("n_bootstrap must be at least 100")


def _compute_curve_rqa_table(
    trajectories: TrajectorySet,
    *,
    dimensions: tuple[str, ...],
    metrics: tuple[str, ...],
    radius: float | None,
    target_recurrence_rate: float | None,
    distance_metric: str,
    theiler_window: float | int,
    theiler_window_units: str,
    min_diagonal_length: int,
    min_vertical_length: int,
    embedding_dimension: int | None,
    delay: float | int | None,
    delay_units: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if (radius is None) == (target_recurrence_rate is None):
        raise ValueError("supply exactly one of radius or target_recurrence_rate")

    if embedding_dimension is None:
        if delay is not None:
            raise ValueError(
                "delay must be None when embedding_dimension is None"
            )
        recurrence_source = trajectories
        recurrence_dimensions: tuple[str, ...] | None = dimensions
        state_provenance: dict[str, Any] = {
            "state_representation": "observed",
            "dimensions": dimensions,
        }
    else:
        if isinstance(embedding_dimension, (bool, np.bool_)) or not isinstance(
            embedding_dimension, (int, np.integer)
        ):
            raise TypeError("embedding_dimension must be an integer or None")
        if int(embedding_dimension) < 2:
            raise ValueError("embedding_dimension must be at least 2")
        if delay is None:
            raise ValueError(
                "delay is required when embedding_dimension is supplied"
            )
        recurrence_source = delay_embed_trajectory(
            trajectories,
            embedding_dimension=int(embedding_dimension),
            delay=delay,
            delay_units=delay_units,
            dimensions=dimensions,
        )
        recurrence_dimensions = None
        state_provenance = {
            "state_representation": "delay_embedding",
            "dimensions": dimensions,
            "embedding_dimension": int(embedding_dimension),
            "delay_requested": delay,
            "delay_units": delay_units,
            "delay_samples": recurrence_source.delay_samples,
            "delay_time": recurrence_source.delay_time,
        }

    rows: list[dict[str, Any]] = []
    for curve_id in trajectories.curve_ids:
        recurrence = recurrence_matrix(
            recurrence_source,
            curve=curve_id,
            radius=radius,
            target_recurrence_rate=target_recurrence_rate,
            metric=distance_metric,
            theiler_window=theiler_window,
            theiler_window_units=theiler_window_units,
            dimensions=recurrence_dimensions,
        )
        result = rqa_metrics(
            recurrence,
            min_diagonal_length=min_diagonal_length,
            min_vertical_length=min_vertical_length,
        )

        row: dict[str, Any] = {
            "curve_id": curve_id,
            "resolved_radius": recurrence.radius,
            "achieved_recurrence_rate": recurrence.achieved_recurrence_rate,
            "theiler_window_samples": recurrence.theiler_window_samples,
        }
        for metric in metrics:
            value = float(getattr(result, metric))
            if not np.isfinite(value):
                raise ValueError(
                    f"RQA metric {metric!r} is undefined for curve "
                    f"{curve_id!r}; bootstrap inference does not drop, impute, "
                    "or replace undefined unit-level outcomes"
                )
            row[metric] = value
        rows.append(row)

    table = pd.DataFrame(rows)
    return table, state_provenance


def _unit_table(
    trajectories: TrajectorySet,
    observed_table: pd.DataFrame,
    *,
    metrics: tuple[str, ...],
    unit: str,
    participant_column: str | None,
) -> tuple[pd.DataFrame, tuple[str, ...], dict[str, Any]]:
    if unit not in {"curve", "participant"}:
        raise ValueError("unit must be 'curve' or 'participant'")

    if unit == "curve":
        if participant_column is not None:
            raise ValueError(
                "participant_column must be None when unit='curve'; use "
                "unit='participant' for equal-weight participant inference"
            )
        table = observed_table[["curve_id", *metrics]].copy()
        table = table.rename(columns={"curve_id": "unit_id"})
        ids = tuple(table["unit_id"].astype(str))
        return (
            table,
            ids,
            {
                "estimand": "equal_weight_mean_of_curve_level_rqa_metrics",
                "curves_per_unit": [1] * len(ids),
                "within_participant_trial_resampling": False,
            },
        )

    if participant_column is None:
        raise ValueError("participant_column is required when unit='participant'")
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(
            f"metadata does not contain participant column "
            f"{participant_column!r}"
        )
    if trajectories.metadata[participant_column].isna().any():
        raise ValueError("participant_column contains missing values")

    participant = trajectories.metadata[participant_column].astype(str).to_numpy()
    unit_ids = tuple(pd.unique(participant))
    if len(unit_ids) < 2:
        raise ValueError("At least two unique participants are required")

    rows: list[dict[str, Any]] = []
    counts: list[int] = []
    curve_index = {curve_id: index for index, curve_id in enumerate(trajectories.curve_ids)}
    for participant_id in unit_ids:
        indices = np.flatnonzero(participant == participant_id)
        counts.append(int(indices.size))
        curve_ids = [trajectories.curve_ids[index] for index in indices]
        subset = observed_table.loc[
            observed_table["curve_id"].isin(curve_ids),
            ["curve_id", *metrics],
        ]
        if len(subset) != len(curve_ids):
            raise RuntimeError(
                "participant aggregation lost one or more curve-level RQA rows"
            )
        row: dict[str, Any] = {
            "unit_id": participant_id,
            "n_curves": int(len(curve_ids)),
        }
        for metric in metrics:
            row[metric] = float(subset[metric].mean())
        rows.append(row)

    # Retain this audit to catch accidental metadata/curve-order divergence.
    if len(curve_index) != trajectories.n_curves:
        raise RuntimeError("curve identifiers are not unique")

    return (
        pd.DataFrame(rows),
        unit_ids,
        {
            "estimand": (
                "equal_weight_mean_of_participant_average_curve_level_rqa_metrics"
            ),
            "curves_per_unit": counts,
            "within_participant_trial_aggregation": "arithmetic_mean_of_curve_metrics",
            "within_participant_trial_resampling": False,
        },
    )


def bootstrap_rqa_metric_means(
    trajectories: TrajectorySet,
    *,
    dimensions: Sequence[str],
    metrics: Sequence[str],
    radius: float | None = None,
    target_recurrence_rate: float | None = None,
    distance_metric: str = "euclidean",
    theiler_window: float | int = 0,
    theiler_window_units: str = "samples",
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
    embedding_dimension: int | None = None,
    delay: float | int | None = None,
    delay_units: str = "samples",
    unit: str = "curve",
    participant_column: str | None = None,
    confidence_level: float = 0.95,
    n_bootstrap: int = 2000,
    random_state: int | None = 0,
) -> RQAMeanBootstrapResult:
    """Bootstrap population-average per-curve RQA metrics.

    RQA metrics are first computed once for every observed source curve under
    one fixed, fully declared recurrence contract. Bootstrap resampling then
    operates on the independent analysis units: curves, or equal-weight
    participant averages when repeated trials are present.

    This is a population-sampling bootstrap for the mean of curve-level RQA
    summaries. It does not estimate within-single-trajectory recurrence
    uncertainty, does not resample recurrence lines, and does not implement a
    moving/block bootstrap for one time series.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError(
            "RQA bootstrap requires complete finite trajectory values"
        )
    if isinstance(dimensions, (str, bytes)):
        raise TypeError("dimensions must be a non-string sequence")
    dimension_names = tuple(str(name) for name in dimensions)
    if not dimension_names:
        raise ValueError("dimensions must contain at least one name")
    if len(set(dimension_names)) != len(dimension_names):
        raise ValueError("dimensions must be unique")
    missing = [
        name for name in dimension_names if name not in trajectories.dimension_names
    ]
    if missing:
        raise KeyError(f"Unknown trajectory dimensions: {missing}")

    metric_names = _validate_metrics(
        metrics,
        target_recurrence_rate=target_recurrence_rate,
    )
    _validate_bootstrap_controls(
        confidence_level=confidence_level,
        n_bootstrap=n_bootstrap,
    )

    observed_table, state_provenance = _compute_curve_rqa_table(
        trajectories,
        dimensions=dimension_names,
        metrics=metric_names,
        radius=radius,
        target_recurrence_rate=target_recurrence_rate,
        distance_metric=distance_metric,
        theiler_window=theiler_window,
        theiler_window_units=theiler_window_units,
        min_diagonal_length=min_diagonal_length,
        min_vertical_length=min_vertical_length,
        embedding_dimension=embedding_dimension,
        delay=delay,
        delay_units=delay_units,
    )
    unit_table, unit_ids, unit_provenance = _unit_table(
        trajectories,
        observed_table,
        metrics=metric_names,
        unit=unit,
        participant_column=participant_column,
    )
    n_units = len(unit_ids)
    if n_units < 2:
        raise ValueError("At least two independent bootstrap units are required")

    unit_values = unit_table.loc[:, list(metric_names)].to_numpy(dtype=float)
    observed_mean = np.mean(unit_values, axis=0)

    rng = np.random.default_rng(random_state)
    bootstrap_values = np.empty((int(n_bootstrap), len(metric_names)), dtype=float)
    batch_size = min(512, int(n_bootstrap))
    for start in range(0, int(n_bootstrap), batch_size):
        stop = min(start + batch_size, int(n_bootstrap))
        indices = rng.integers(
            0,
            n_units,
            size=(stop - start, n_units),
        )
        bootstrap_values[start:stop] = np.mean(
            unit_values[indices],
            axis=1,
        )

    alpha = 1.0 - float(confidence_level)
    lower_q = alpha / 2.0
    upper_q = 1.0 - alpha / 2.0
    lower = np.quantile(
        bootstrap_values,
        lower_q,
        axis=0,
        method="linear",
    )
    upper = np.quantile(
        bootstrap_values,
        upper_q,
        axis=0,
        method="linear",
    )
    bootstrap_mean = np.mean(bootstrap_values, axis=0)
    bootstrap_se = np.std(bootstrap_values, axis=0, ddof=1)

    bootstrap_table = pd.DataFrame(
        bootstrap_values,
        columns=metric_names,
    )
    bootstrap_table.insert(
        0,
        "bootstrap_id",
        np.arange(1, int(n_bootstrap) + 1, dtype=int),
    )

    summary_table = pd.DataFrame(
        {
            "metric": metric_names,
            "mean": observed_mean,
            "bootstrap_mean": bootstrap_mean,
            "bootstrap_bias": bootstrap_mean - observed_mean,
            "bootstrap_standard_error": bootstrap_se,
            "lower": lower,
            "upper": upper,
        }
    )

    threshold_policy = (
        "fixed_radius" if radius is not None else "target_recurrence_rate"
    )
    return RQAMeanBootstrapResult(
        observed_table=observed_table,
        unit_table=unit_table,
        bootstrap_table=bootstrap_table,
        summary_table=summary_table,
        metrics=metric_names,
        unit=unit,
        unit_ids=unit_ids,
        participant_column=(
            participant_column if unit == "participant" else None
        ),
        confidence_level=float(confidence_level),
        n_bootstrap=int(n_bootstrap),
        provenance={
            "operation": "bootstrap_rqa_metric_means",
            "source_provenance": dict(trajectories.provenance),
            "dimensions": dimension_names,
            **state_provenance,
            "threshold_policy": threshold_policy,
            "requested_radius": radius,
            "requested_target_recurrence_rate": target_recurrence_rate,
            "distance_metric": distance_metric,
            "theiler_window_requested": theiler_window,
            "theiler_window_units": theiler_window_units,
            "min_diagonal_length": min_diagonal_length,
            "min_vertical_length": min_vertical_length,
            "metrics": metric_names,
            "unit": unit,
            "participant_column": (
                participant_column if unit == "participant" else None
            ),
            "n_units": n_units,
            "n_bootstrap": int(n_bootstrap),
            "confidence_level": float(confidence_level),
            "interval_method": "percentile_bootstrap",
            "random_state": random_state,
            "curve_level_rqa_recomputed_per_bootstrap_draw": False,
            "curve_level_rqa_reason": (
                "each observed curve has one deterministic RQA summary under "
                "the fixed declared recurrence contract; the bootstrap targets "
                "between-unit population sampling uncertainty"
            ),
            "within_single_trajectory_uncertainty": False,
            "recurrence_line_resampling": False,
            "moving_or_block_bootstrap": False,
            "automatic_parameter_selection": False,
            "parameter_selection_uncertainty_included": False,
            "undefined_metric_policy": "raise_entire_analysis",
            **unit_provenance,
        },
    )
