"""W4 nonlinear recurrence workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..embedding import delay_embed_trajectory
from ..nonlinear_reporting import rqa_reporting_text
from ..nonlinear_types import DelayEmbeddingResult, RecurrenceResult, RQAResult
from ..recurrence import recurrence_matrix, rqa_metrics
from ..types import TrajectorySet
from ._core import (
    PreprocessingPlan,
    WORKFLOW_SCHEMA_VERSION,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
)
from ._sparse_shared import timed_step


@dataclass(frozen=True)
class RecurrenceWorkflowConfig:
    """Explicit recurrence/RQA specification.

    W4 uses a fixed analyst-declared recurrence radius (epsilon). Parameter
    diagnostics and sensitivity analyses remain separate APIs and are never
    converted into an automatic selection rule by the workflow.
    """

    curve: int | str
    dimensions: tuple[str, ...]
    embedding_dimension: int
    delay: float | int
    radius: float
    delay_units: str = "samples"
    metric: str = "euclidean"
    theiler_window: float | int = 0
    theiler_window_units: str = "samples"
    min_diagonal_length: int = 2
    min_vertical_length: int = 2
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        dimensions = tuple(map(str, self.dimensions))
        if not dimensions:
            raise ValueError("dimensions must contain at least one name")
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("dimensions must not contain duplicates")
        object.__setattr__(self, "dimensions", dimensions)

        if (
            isinstance(self.embedding_dimension, bool)
            or not isinstance(self.embedding_dimension, (int, np.integer))
            or int(self.embedding_dimension) < 1
        ):
            raise ValueError("embedding_dimension must be a positive integer")
        object.__setattr__(
            self,
            "embedding_dimension",
            int(self.embedding_dimension),
        )

        radius = float(self.radius)
        if not np.isfinite(radius) or radius <= 0:
            raise ValueError("radius must be finite and strictly positive")
        object.__setattr__(self, "radius", radius)

        if self.metric not in {"cityblock", "euclidean", "chebyshev"}:
            raise ValueError(
                "metric must be 'cityblock', 'euclidean', or 'chebyshev'"
            )
        if isinstance(self.min_diagonal_length, bool) or int(
            self.min_diagonal_length
        ) < 1:
            raise ValueError("min_diagonal_length must be a positive integer")
        if isinstance(self.min_vertical_length, bool) or int(
            self.min_vertical_length
        ) < 1:
            raise ValueError("min_vertical_length must be a positive integer")
        object.__setattr__(
            self,
            "min_diagonal_length",
            int(self.min_diagonal_length),
        )
        object.__setattr__(
            self,
            "min_vertical_length",
            int(self.min_vertical_length),
        )


@dataclass(frozen=True)
class RecurrenceWorkflowResult:
    """Frozen recurrence workflow result retaining every analysis stage."""

    workflow_schema_version: int
    workflow_contract: str
    config: RecurrenceWorkflowConfig
    embedding: DelayEmbeddingResult
    recurrence: RecurrenceResult
    metrics: RQAResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def _require_empty_preprocessing(
    preprocessing: PreprocessingPlan,
) -> None:
    if not isinstance(preprocessing, PreprocessingPlan):
        raise TypeError("preprocessing must be a PreprocessingPlan")
    if preprocessing.steps:
        raise ValueError(
            "recurrence:v1 requires an empty preprocessing plan; resampling, "
            "smoothing, normalization or coordinate transforms must be "
            "performed explicitly upstream and retained in source provenance"
        )


def _rqa_frame(metrics: RQAResult) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
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
                "min_diagonal_length": metrics.min_diagonal_length,
                "min_vertical_length": metrics.min_vertical_length,
            }
        ]
    )


def run_recurrence_workflow(
    trajectories: TrajectorySet,
    *,
    config: RecurrenceWorkflowConfig,
) -> RecurrenceWorkflowResult:
    """Run explicit delay embedding, fixed-radius recurrence, and RQA."""

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if not isinstance(config, RecurrenceWorkflowConfig):
        raise TypeError("config must be a RecurrenceWorkflowConfig")
    _require_empty_preprocessing(config.preprocessing)

    steps: list[WorkflowStepRecord] = []

    embedding_parameters = {
        "embedding_dimension": config.embedding_dimension,
        "delay": config.delay,
        "delay_units": config.delay_units,
        "dimensions": config.dimensions,
    }
    embedding, step = timed_step(
        name="delay_embedding",
        function="delay_embed_trajectory",
        parameters=embedding_parameters,
        call=lambda: delay_embed_trajectory(
            trajectories,
            **embedding_parameters,
        ),
    )
    steps.append(step)

    recurrence_parameters = {
        "curve": config.curve,
        "radius": config.radius,
        "metric": config.metric,
        "theiler_window": config.theiler_window,
        "theiler_window_units": config.theiler_window_units,
    }
    recurrence, step = timed_step(
        name="recurrence",
        function="recurrence_matrix",
        parameters=recurrence_parameters,
        call=lambda: recurrence_matrix(
            embedding,
            curve=config.curve,
            radius=config.radius,
            metric=config.metric,
            theiler_window=config.theiler_window,
            theiler_window_units=config.theiler_window_units,
        ),
    )
    steps.append(step)

    rqa_parameters = {
        "min_diagonal_length": config.min_diagonal_length,
        "min_vertical_length": config.min_vertical_length,
    }
    metrics, step = timed_step(
        name="rqa",
        function="rqa_metrics",
        parameters=rqa_parameters,
        call=lambda: rqa_metrics(recurrence, **rqa_parameters),
    )
    steps.append(step)

    decisions = {
        "curve": WorkflowDecisionRecord(
            value=config.curve,
            source="analyst",
        ),
        "dimensions": WorkflowDecisionRecord(
            value=config.dimensions,
            source="analyst",
        ),
        "embedding_dimension": WorkflowDecisionRecord(
            value=config.embedding_dimension,
            source="analyst",
        ),
        "delay": WorkflowDecisionRecord(
            value=config.delay,
            source="analyst",
        ),
        "delay_units": WorkflowDecisionRecord(
            value=config.delay_units,
            source="analyst",
        ),
        "radius": WorkflowDecisionRecord(
            value=config.radius,
            source="analyst",
        ),
        "metric": WorkflowDecisionRecord(
            value=config.metric,
            source="analyst",
        ),
        "theiler_window": WorkflowDecisionRecord(
            value=config.theiler_window,
            source="analyst",
        ),
        "theiler_window_units": WorkflowDecisionRecord(
            value=config.theiler_window_units,
            source="analyst",
        ),
        "min_diagonal_length": WorkflowDecisionRecord(
            value=config.min_diagonal_length,
            source="analyst",
        ),
        "min_vertical_length": WorkflowDecisionRecord(
            value=config.min_vertical_length,
            source="analyst",
        ),
        "resolved_delay_samples": WorkflowDecisionRecord(
            value=embedding.delay_samples,
            source="derived",
            criterion=(
                "resolved by delay_embed_trajectory from the declared delay "
                "and source time grid"
            ),
        ),
        "resolved_theiler_window_samples": WorkflowDecisionRecord(
            value=recurrence.theiler_window_samples,
            source="derived",
            criterion=(
                "resolved by recurrence_matrix from the declared Theiler "
                "window and embedded-state time grid"
            ),
        ),
    }

    return RecurrenceWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract="recurrence:v1",
        config=config,
        embedding=embedding,
        recurrence=recurrence,
        metrics=metrics,
        steps=tuple(steps),
        decisions=decisions,
        provenance={
            "input_layout": "complete_common_grid",
            "state_representation": "delay_embedding",
            "preprocessing_executed": False,
            "fixed_radius_policy": True,
            "target_recurrence_rate_selection_performed": False,
            "automatic_embedding_parameter_selection": False,
            "automatic_rqa_parameter_selection": False,
        },
        reports={"rqa": rqa_reporting_text(recurrence, metrics)},
        tables={"rqa_metrics": _rqa_frame(metrics)},
    )
