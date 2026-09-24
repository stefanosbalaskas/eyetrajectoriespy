"""Joint recurrence analysis for synchronized recurrence systems."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, triu

from .nonlinear_types import (
    JointRecurrenceResult,
    RecurrenceResult,
    RQAResult,
)
from .recurrence import rqa_metrics


def _eligible_auto_pairs(n: int, theiler: int) -> int:
    remaining = n - theiler - 1
    return 0 if remaining <= 0 else remaining * (remaining + 1) // 2


def _validate_labels(
    labels: Sequence[str] | None,
    n_components: int,
) -> tuple[str, ...]:
    if labels is None:
        return tuple(
            f"component_{index + 1}"
            for index in range(n_components)
        )
    if isinstance(labels, (str, bytes)):
        raise TypeError("labels must be a non-string sequence or None")
    resolved = tuple(labels)
    if len(resolved) != n_components:
        raise ValueError(
            "labels must contain exactly one value per recurrence component"
        )
    if not all(isinstance(label, str) and label.strip() for label in resolved):
        raise ValueError("labels must contain non-empty strings")
    if len(set(resolved)) != len(resolved):
        raise ValueError("labels must be unique")
    return resolved


def joint_recurrence_matrix(
    recurrences: Sequence[RecurrenceResult],
    *,
    labels: Sequence[str] | None = None,
) -> JointRecurrenceResult:
    """Intersect synchronized auto-recurrence matrices.

    A joint recurrence is present at (i, j) only when every supplied subsystem
    is recurrent at the same pair of time indices. Each subsystem may use its
    own state dimension, distance metric, and radius policy.

    Version 0.39 requires all component recurrence matrices to be auto
    recurrence results on the exact same time grid with the same Theiler
    exclusion. No resampling, lag shifting, synchronization, threshold
    harmonization, or target-rate re-estimation is performed.
    """

    if isinstance(recurrences, (str, bytes)):
        raise TypeError("recurrences must be a non-string sequence")
    components = tuple(recurrences)
    if len(components) < 2:
        raise ValueError(
            "joint recurrence requires at least two recurrence components"
        )
    for index, recurrence in enumerate(components):
        if not isinstance(recurrence, RecurrenceResult):
            raise TypeError(
                f"recurrence component {index} must be a RecurrenceResult"
            )
        if recurrence.kind != "auto":
            raise ValueError(
                "joint recurrence components must be auto-recurrence results"
            )
        if recurrence.matrix.shape[0] != recurrence.matrix.shape[1]:
            raise ValueError(
                "joint recurrence requires square auto-recurrence matrices"
            )
        if recurrence.time_a.shape != recurrence.time_b.shape or not np.array_equal(
            recurrence.time_a,
            recurrence.time_b,
        ):
            raise ValueError(
                "each auto-recurrence component must use one identical "
                "time grid on both axes"
            )

    first = components[0]
    n_states = first.matrix.shape[0]
    time = np.asarray(first.time_a, dtype=float)
    theiler = int(first.theiler_window_samples)

    if time.shape != (n_states,):
        raise ValueError(
            "recurrence time grid length must match matrix dimensions"
        )
    if theiler < 0:
        raise ValueError("theiler_window_samples must be non-negative")

    for recurrence in components[1:]:
        if recurrence.matrix.shape != first.matrix.shape:
            raise ValueError(
                "joint recurrence components must have identical matrix shapes"
            )
        if not np.array_equal(
            np.asarray(recurrence.time_a, dtype=float),
            time,
        ):
            raise ValueError(
                "joint recurrence components must use the exact same time grid; "
                "align or resample upstream explicitly"
            )
        if recurrence.theiler_window_samples != theiler:
            raise ValueError(
                "joint recurrence components must use the same Theiler window"
            )

    eligible = _eligible_auto_pairs(n_states, theiler)
    if eligible <= 0:
        raise ValueError(
            "Theiler window leaves no eligible joint recurrence pairs"
        )

    resolved_labels = _validate_labels(labels, len(components))

    joint: csr_matrix = components[0].matrix.astype(bool).tocsr().copy()
    for recurrence in components[1:]:
        joint = joint.multiply(
            recurrence.matrix.astype(bool)
        ).tocsr()
    joint.eliminate_zeros()

    upper = triu(joint, k=1).tocsr()
    n_joint_pairs = int(upper.nnz)
    joint_rate = float(n_joint_pairs / eligible)

    return JointRecurrenceResult(
        matrix=joint,
        time=time.copy(),
        component_recurrences=components,
        component_labels=resolved_labels,
        joint_recurrence_rate=joint_rate,
        n_joint_recurrent_pairs=n_joint_pairs,
        eligible_pair_count=int(eligible),
        theiler_window_samples=theiler,
        provenance={
            "operation": "joint_recurrence_matrix",
            "definition": (
                "elementwise_logical_and_of_synchronized_auto_recurrence_matrices"
            ),
            "component_labels": list(resolved_labels),
            "component_count": len(components),
            "component_provenance": [
                dict(recurrence.provenance)
                for recurrence in components
            ],
            "component_metrics": [
                recurrence.metric
                for recurrence in components
            ],
            "component_radii": [
                float(recurrence.radius)
                for recurrence in components
            ],
            "component_target_recurrence_rates": [
                recurrence.target_recurrence_rate
                for recurrence in components
            ],
            "component_achieved_recurrence_rates": [
                float(recurrence.achieved_recurrence_rate)
                for recurrence in components
            ],
            "component_state_dimensions": [
                int(recurrence.state_dimension)
                for recurrence in components
            ],
            "theiler_window_samples": theiler,
            "eligible_pair_count": int(eligible),
            "n_joint_recurrent_pairs": n_joint_pairs,
            "joint_recurrence_rate": joint_rate,
            "recurrence_rate_scale": "0_to_1",
            "recurrence_rate_denominator": (
                "eligible_off_diagonal_pairs_outside_shared_theiler_window"
            ),
            "time_alignment": "exact_grid_match_required",
            "resampling": False,
            "lag_shift": False,
            "threshold_harmonization": False,
            "automatic_threshold_selection": False,
            "interpretation_boundary": (
                "joint recurrence means simultaneous recurrence within every "
                "component system under its own declared recurrence contract; "
                "it is distinct from cross recurrence between states"
            ),
        },
    )


def joint_recurrence_component_frame(
    result: JointRecurrenceResult,
) -> pd.DataFrame:
    """Return one row per component recurrence contract."""

    if not isinstance(result, JointRecurrenceResult):
        raise TypeError("result must be a JointRecurrenceResult")

    rows: list[dict[str, object]] = []
    for label, recurrence in zip(
        result.component_labels,
        result.component_recurrences,
        strict=True,
    ):
        rows.append(
            {
                "label": label,
                "source_curve_ids": recurrence.source_curve_ids,
                "metric": recurrence.metric,
                "radius": float(recurrence.radius),
                "target_recurrence_rate": recurrence.target_recurrence_rate,
                "achieved_recurrence_rate": float(
                    recurrence.achieved_recurrence_rate
                ),
                "state_dimension": int(recurrence.state_dimension),
                "theiler_window_samples": int(
                    recurrence.theiler_window_samples
                ),
            }
        )
    return pd.DataFrame(rows)


def _as_recurrence_result(
    result: JointRecurrenceResult,
) -> RecurrenceResult:
    return RecurrenceResult(
        matrix=result.matrix,
        time_a=result.time.copy(),
        time_b=result.time.copy(),
        source_curve_ids=result.component_labels,
        radius=float("nan"),
        target_recurrence_rate=None,
        achieved_recurrence_rate=result.joint_recurrence_rate,
        metric="joint",
        theiler_window_samples=result.theiler_window_samples,
        kind="auto",
        state_dimension=sum(
            recurrence.state_dimension
            for recurrence in result.component_recurrences
        ),
        provenance={
            **dict(result.provenance),
            "operation": "joint_recurrence_adapter_for_rqa",
            "recurrence_rate_denominator": (
                "eligible_off_diagonal_pairs_outside_shared_theiler_window"
            ),
            "joint_recurrence": True,
        },
    )


def joint_rqa_metrics(
    result: JointRecurrenceResult,
    *,
    min_diagonal_length: int = 2,
    min_vertical_length: int = 2,
) -> RQAResult:
    """Compute standard line-based RQA metrics on a joint recurrence plot."""

    if not isinstance(result, JointRecurrenceResult):
        raise TypeError("result must be a JointRecurrenceResult")
    metrics = rqa_metrics(
        _as_recurrence_result(result),
        min_diagonal_length=min_diagonal_length,
        min_vertical_length=min_vertical_length,
    )
    return RQAResult(
        recurrence_rate=metrics.recurrence_rate,
        determinism=metrics.determinism,
        mean_diagonal_length=metrics.mean_diagonal_length,
        max_diagonal_length=metrics.max_diagonal_length,
        diagonal_entropy=metrics.diagonal_entropy,
        laminarity=metrics.laminarity,
        trapping_time=metrics.trapping_time,
        max_vertical_length=metrics.max_vertical_length,
        center_of_recurrence_mass=metrics.center_of_recurrence_mass,
        n_recurrence_points=metrics.n_recurrence_points,
        n_diagonal_lines=metrics.n_diagonal_lines,
        n_vertical_lines=metrics.n_vertical_lines,
        min_diagonal_length=metrics.min_diagonal_length,
        min_vertical_length=metrics.min_vertical_length,
        provenance={
            **dict(metrics.provenance),
            "operation": "joint_rqa_metrics",
            "joint_recurrence_provenance": dict(result.provenance),
            "interpretation_boundary": (
                "line statistics summarize coincident recurrence structure "
                "across the declared component systems; they are not "
                "cross-RQA between two state trajectories"
            ),
        },
    )
