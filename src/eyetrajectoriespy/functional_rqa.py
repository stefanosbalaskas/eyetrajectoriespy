"""Sensitivity and dependence-aware functional recurrence analysis."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .inference import multiplier_functional_mean_band
from .nonlinear_types import (
    WindowedRQAMeanBandResult,
    WindowedRQASensitivityResult,
)
from .recurrence import windowed_rqa_trajectory_set
from .types import TrajectorySet


def _validated_window_step_pairs(
    window_step_pairs: Sequence[tuple[float | int, float | int]],
) -> tuple[tuple[float | int, float | int], ...]:
    if isinstance(window_step_pairs, (str, bytes)):
        raise TypeError("window_step_pairs must be a sequence of (window, step) pairs")
    pairs = tuple(window_step_pairs)
    if not pairs:
        raise ValueError("window_step_pairs must contain at least one specification")

    validated: list[tuple[float | int, float | int]] = []
    for index, pair in enumerate(pairs):
        if not isinstance(pair, Sequence) or isinstance(pair, (str, bytes)) or len(pair) != 2:
            raise ValueError(
                f"window_step_pairs[{index}] must contain exactly (window, step)"
            )
        window, step = pair
        for name, value in (("window", window), ("step", step)):
            if isinstance(value, (bool, np.bool_)) or not isinstance(
                value, (int, float, np.integer, np.floating)
            ):
                raise TypeError(
                    f"{name} in window_step_pairs[{index}] must be numeric"
                )
            if not np.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(
                    f"{name} in window_step_pairs[{index}] must be positive and finite"
                )
        validated.append((window, step))
    return tuple(validated)


def _window_reuse_diagnostics(
    n_time: int,
    *,
    starts: np.ndarray,
    window_samples: int,
) -> dict[str, float | int]:
    coverage = np.zeros(n_time, dtype=int)
    for start in starts:
        coverage[int(start) : int(start) + window_samples] += 1
    analyzed = coverage > 0
    reused = coverage > 1
    if not np.any(analyzed):
        raise RuntimeError("window sensitivity analysis produced no analyzed samples")
    analyzed_count = int(np.sum(analyzed))
    return {
        "n_analyzed_source_samples": analyzed_count,
        "analyzed_source_fraction": float(analyzed_count / n_time),
        "fraction_analyzed_samples_reused": float(
            np.sum(reused) / analyzed_count
        ),
        "mean_window_memberships_per_analyzed_sample": float(
            np.mean(coverage[analyzed])
        ),
        "max_window_memberships": int(np.max(coverage)),
    }


def _descriptive_summary(
    analyses,
    specification_ids: tuple[str, ...],
    metrics: tuple[str, ...],
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for specification_id, analysis in zip(
        specification_ids, analyses, strict=True
    ):
        for curve_index, curve_id in enumerate(analysis.trajectories.curve_ids):
            for metric_index, metric_name in enumerate(metrics):
                values = analysis.trajectories.values[
                    curve_index, :, metric_index
                ]
                finite = values[np.isfinite(values)]
                n_finite = int(finite.size)
                rows.append(
                    {
                        "specification_id": specification_id,
                        "curve_id": curve_id,
                        "metric": metric_name,
                        "n_windows": int(values.size),
                        "n_finite_windows": n_finite,
                        "mean": (
                            float(np.mean(finite)) if n_finite else float("nan")
                        ),
                        "standard_deviation": (
                            float(np.std(finite, ddof=1))
                            if n_finite > 1
                            else float("nan")
                        ),
                        "minimum": (
                            float(np.min(finite)) if n_finite else float("nan")
                        ),
                        "maximum": (
                            float(np.max(finite)) if n_finite else float("nan")
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _pairwise_exact_center_comparison(
    analyses,
    specification_ids: tuple[str, ...],
    metrics: tuple[str, ...],
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for left_index in range(len(analyses)):
        for right_index in range(left_index + 1, len(analyses)):
            left = analyses[left_index].trajectories
            right = analyses[right_index].trajectories
            common = np.intersect1d(left.time, right.time)
            if common.size:
                left_positions = np.searchsorted(left.time, common)
                right_positions = np.searchsorted(right.time, common)
            else:
                left_positions = np.empty(0, dtype=int)
                right_positions = np.empty(0, dtype=int)

            for curve_index, curve_id in enumerate(left.curve_ids):
                for metric_index, metric_name in enumerate(metrics):
                    x = left.values[
                        curve_index, left_positions, metric_index
                    ]
                    y = right.values[
                        curve_index, right_positions, metric_index
                    ]
                    finite = np.isfinite(x) & np.isfinite(y)
                    x_finite = x[finite]
                    y_finite = y[finite]
                    n_common = int(x_finite.size)
                    if n_common:
                        difference = x_finite - y_finite
                        rmse = float(np.sqrt(np.mean(difference**2)))
                        mad = float(np.mean(np.abs(difference)))
                        maximum = float(np.max(np.abs(difference)))
                    else:
                        rmse = mad = maximum = float("nan")

                    correlation = float("nan")
                    if (
                        n_common >= 2
                        and np.std(x_finite, ddof=0) > np.finfo(float).eps
                        and np.std(y_finite, ddof=0) > np.finfo(float).eps
                    ):
                        correlation = float(np.corrcoef(x_finite, y_finite)[0, 1])

                    rows.append(
                        {
                            "specification_a": specification_ids[left_index],
                            "specification_b": specification_ids[right_index],
                            "curve_id": curve_id,
                            "metric": metric_name,
                            "n_common_centers": n_common,
                            "rmse": rmse,
                            "mean_absolute_difference": mad,
                            "max_absolute_difference": maximum,
                            "correlation": correlation,
                        }
                    )
    return pd.DataFrame(rows)


def windowed_rqa_sensitivity(
    trajectories: TrajectorySet,
    *,
    metrics: Sequence[str],
    window_step_pairs: Sequence[tuple[float | int, float | int]],
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
) -> WindowedRQASensitivityResult:
    """Evaluate declared window/step specifications without selecting one.

    Every specification is run through windowed_rqa_trajectory_set under the
    same recurrence contract. No interpolation is used to compare profiles
    from different specifications. Pairwise shape diagnostics use exact shared
    window-center times only.

    The design table quantifies deterministic sample reuse caused by overlap.
    Its profile-grid spacing is the temporal spacing of the derived RQA
    function, not an estimate of independent-information resolution.
    """

    pairs = _validated_window_step_pairs(window_step_pairs)
    metric_names = tuple(str(name) for name in metrics)
    analyses = tuple(
        windowed_rqa_trajectory_set(
            trajectories,
            metrics=metric_names,
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
            undefined_policy=undefined_policy,
        )
        for window, step in pairs
    )

    resolved_pairs = tuple(
        (analysis.window_samples, analysis.step_samples)
        for analysis in analyses
    )
    if len(set(resolved_pairs)) != len(resolved_pairs):
        raise ValueError(
            "two or more requested window/step specifications resolve to the "
            "same sample counts; remove duplicate resolved specifications"
        )

    specification_ids = tuple(
        f"spec_{index + 1}" for index in range(len(analyses))
    )
    design_rows: list[dict[str, float | int | str]] = []
    for specification_id, requested, analysis in zip(
        specification_ids, pairs, analyses, strict=True
    ):
        first_window = analysis.window_results[0]
        table = first_window.table
        starts = table["start_index"].to_numpy(dtype=int)
        centers = analysis.trajectories.time
        profile_grid_spacing = (
            float(np.median(np.diff(centers)))
            if centers.size > 1
            else float("nan")
        )
        window_span = float(
            table["end_time"].iloc[0] - table["start_time"].iloc[0]
        )
        reuse = _window_reuse_diagnostics(
            trajectories.n_time,
            starts=starts,
            window_samples=analysis.window_samples,
        )
        design_rows.append(
            {
                "specification_id": specification_id,
                "requested_window": float(requested[0]),
                "requested_step": float(requested[1]),
                "window_units": window_units,
                "step_units": step_units,
                "window_samples": int(analysis.window_samples),
                "step_samples": int(analysis.step_samples),
                "window_span_time": window_span,
                "profile_grid_spacing_time": profile_grid_spacing,
                "profile_time_unit": trajectories.time_unit,
                "n_windows": int(analysis.n_windows),
                "overlap_samples": int(analysis.overlap_samples),
                "overlap_fraction": float(analysis.overlap_fraction),
                "functional_support_start": float(centers[0]),
                "functional_support_end": float(centers[-1]),
                "dropped_tail_samples": int(
                    analysis.dropped_tail_samples
                ),
                **reuse,
            }
        )

    design_table = pd.DataFrame(design_rows)
    summary_table = _descriptive_summary(
        analyses,
        specification_ids,
        metric_names,
    )
    pairwise_table = _pairwise_exact_center_comparison(
        analyses,
        specification_ids,
        metric_names,
    )

    return WindowedRQASensitivityResult(
        analyses=analyses,
        design_table=design_table,
        summary_table=summary_table,
        pairwise_table=pairwise_table,
        metrics=metric_names,
        provenance={
            "operation": "windowed_rqa_sensitivity",
            "source_provenance": dict(trajectories.provenance),
            "specification_ids": specification_ids,
            "requested_window_step_pairs": tuple(
                (float(window), float(step)) for window, step in pairs
            ),
            "resolved_window_step_samples": resolved_pairs,
            "no_automatic_specification_selection": True,
            "pairwise_time_alignment": "exact_shared_window_centers_only",
            "interpolation_used_for_sensitivity_comparison": False,
            "summary_statistics_are_descriptive_not_inferential": True,
            "profile_grid_spacing_interpretation": (
                "derived-function temporal grid spacing; not an estimate of "
                "independent-information resolution"
            ),
            "window_dependence_interpretation": (
                "sample-reuse diagnostics quantify deterministic overlap only; "
                "serial dependence can remain even when overlap_fraction is zero"
            ),
        },
    )


def windowed_rqa_functional_mean_band(
    trajectories: TrajectorySet,
    *,
    metrics: Sequence[str],
    window: float | int,
    step: float | int,
    unit: str,
    participant_column: str | None = None,
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
    confidence_level: float = 0.95,
    n_multiplier: int = 2000,
    random_state: int | None = 0,
) -> WindowedRQAMeanBandResult:
    """Estimate a unit-level simultaneous mean band for functional RQA.

    Windowed RQA is first computed once per source curve with undefined
    selected metrics rejected. The existing functional-mean multiplier band is
    then applied to complete derived functions, never to window rows.

    unit="participant" averages repeated trial curves within participant before
    inference and requires participant_column. unit="curve" treats each source
    curve as an independent unit and therefore should only be used when that
    independence is scientifically justified.
    """

    functional_rqa = windowed_rqa_trajectory_set(
        trajectories,
        metrics=metrics,
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
        undefined_policy="raise",
    )
    band = multiplier_functional_mean_band(
        functional_rqa.trajectories,
        confidence_level=confidence_level,
        n_multiplier=n_multiplier,
        unit=unit,
        participant_column=participant_column,
        random_state=random_state,
    )
    return WindowedRQAMeanBandResult(
        functional_rqa=functional_rqa,
        band=band,
        unit=unit,
        participant_column=participant_column,
        provenance={
            "operation": "windowed_rqa_functional_mean_band",
            "functional_rqa_provenance": dict(functional_rqa.provenance),
            "functional_mean_band_provenance": dict(band.provenance),
            "resampling_unit": unit,
            "participant_column": participant_column,
            "window_rows_resampled_as_independent": False,
            "whole_function_resampling_contract": True,
            "within_function_temporal_dependence_preserved": True,
            "within_source_curve_block_bootstrap": False,
            "inference_scope": (
                "simultaneous observed-grid mean band for independent "
                "curve/participant functional units"
            ),
        },
    )
