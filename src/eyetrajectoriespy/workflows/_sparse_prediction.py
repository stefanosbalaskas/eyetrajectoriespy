"""Transparent proper-training/calibration/target sparse prediction workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..sparse_partial_conformal import (
    SparseFPCAPartialConformalBandResult,
    SparseFPCAPartialConformalCalibrationResult,
    calibrate_sparse_fpca_partial_prediction_conformal,
    sparse_fpca_conformal_band_frame,
    sparse_fpca_conformal_band_reporting_text,
    sparse_fpca_conformal_prediction_band,
)
from ..types import IrregularTrajectorySet
from ._core import (
    PreprocessingPlan,
    WORKFLOW_SCHEMA_VERSION,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
)
from ._sparse_fpca import (
    SparseFPCAWorkflowConfig,
    SparseFPCAWorkflowResult,
    run_sparse_fpca_workflow,
)
from ._sparse_shared import (
    normalized_grid,
    require_empty_sparse_preprocessing,
    timed_step,
)


@dataclass(frozen=True)
class SparsePredictionWorkflowConfig:
    """Declared split-conformal future-prediction configuration."""

    training: SparseFPCAWorkflowConfig
    history_cutoff: float
    prediction_grid: tuple[float, ...]
    alpha: float = 0.05
    group_column: str | None = None
    min_history_observations: int = 2
    condition_limit: float | None = None
    history_ridge: float | None = None
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        if not isinstance(self.training, SparseFPCAWorkflowConfig):
            raise TypeError(
                "training must be a SparseFPCAWorkflowConfig"
            )
        cutoff = float(self.history_cutoff)
        if not np.isfinite(cutoff):
            raise ValueError("history_cutoff must be finite")
        object.__setattr__(self, "history_cutoff", cutoff)
        object.__setattr__(
            self,
            "prediction_grid",
            normalized_grid(self.prediction_grid, name="prediction_grid"),
        )
        alpha = float(self.alpha)
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must be finite and strictly within (0, 1)")
        object.__setattr__(self, "alpha", alpha)
        if (
            isinstance(self.min_history_observations, bool)
            or int(self.min_history_observations) < 1
        ):
            raise ValueError(
                "min_history_observations must be a positive integer"
            )
        object.__setattr__(
            self,
            "min_history_observations",
            int(self.min_history_observations),
        )
        if self.condition_limit is not None:
            value = float(self.condition_limit)
            if not np.isfinite(value) or value <= 0:
                raise ValueError(
                    "condition_limit must be finite and positive"
                )
            object.__setattr__(self, "condition_limit", value)
        if self.history_ridge is not None:
            value = float(self.history_ridge)
            if not np.isfinite(value) or value < 0:
                raise ValueError(
                    "history_ridge must be finite and non-negative"
                )
            object.__setattr__(self, "history_ridge", value)


@dataclass(frozen=True)
class SparsePredictionWorkflowResult:
    """Frozen result retaining training, calibration and target prediction."""

    workflow_schema_version: int
    workflow_contract: str
    config: SparsePredictionWorkflowConfig
    training_workflow: SparseFPCAWorkflowResult
    calibration: SparseFPCAPartialConformalCalibrationResult
    band: SparseFPCAPartialConformalBandResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def _prefixed_training_steps(
    result: SparseFPCAWorkflowResult,
) -> list[WorkflowStepRecord]:
    return [
        WorkflowStepRecord(
            name=f"proper_training.{step.name}",
            function=step.function,
            status=step.status,
            parameters=step.parameters,
            elapsed_seconds=step.elapsed_seconds,
            warnings=step.warnings,
        )
        for step in result.steps
    ]


def run_sparse_prediction_workflow(
    proper_training: IrregularTrajectorySet,
    calibration: IrregularTrajectorySet,
    target: IrregularTrajectorySet,
    *,
    config: SparsePredictionWorkflowConfig,
) -> SparsePredictionWorkflowResult:
    """Run explicit proper-training, calibration and target prediction roles."""

    for name, value in (
        ("proper_training", proper_training),
        ("calibration", calibration),
        ("target", target),
    ):
        if not isinstance(value, IrregularTrajectorySet):
            raise TypeError(f"{name} must be an IrregularTrajectorySet")
    if not isinstance(config, SparsePredictionWorkflowConfig):
        raise TypeError(
            "config must be a SparsePredictionWorkflowConfig"
        )
    if target.n_curves != 1:
        raise ValueError("target must contain exactly one target curve")

    contract = "sparse_prediction:v1"
    require_empty_sparse_preprocessing(
        config.preprocessing,
        workflow_contract=contract,
    )
    if config.training.observation_diagnostics is not None:
        raise ValueError(
            "prediction training config must not request observation-process "
            "diagnostics; that diagnostic requires a separately supplied "
            "candidate-sample process and is not inferred from split roles"
        )

    training = run_sparse_fpca_workflow(
        proper_training,
        config=config.training,
    )
    steps = _prefixed_training_steps(training)

    calibration_parameters = {
        "history_cutoff": config.history_cutoff,
        "prediction_grid": config.prediction_grid,
        "alpha": config.alpha,
        "group_column": config.group_column,
        "min_history_observations": config.min_history_observations,
        "condition_limit": config.condition_limit,
        "history_ridge": config.history_ridge,
    }
    calibrated, step = timed_step(
        name="conformal_calibration",
        function="calibrate_sparse_fpca_partial_prediction_conformal",
        parameters=calibration_parameters,
        call=lambda: calibrate_sparse_fpca_partial_prediction_conformal(
            training.fit,
            calibration,
            **{
                **calibration_parameters,
                "prediction_grid": np.asarray(
                    calibration_parameters["prediction_grid"],
                    dtype=float,
                ),
            },
        ),
    )
    steps.append(step)

    band, step = timed_step(
        name="target_prediction",
        function="sparse_fpca_conformal_prediction_band",
        parameters={
            "target_curve_count": target.n_curves,
            "target_curve_ids": tuple(map(str, target.curve_ids)),
        },
        call=lambda: sparse_fpca_conformal_prediction_band(
            calibrated,
            target,
        ),
    )
    steps.append(step)

    decisions: dict[str, WorkflowDecisionRecord] = {
        f"training.{name}": record
        for name, record in training.decisions.items()
    }
    decisions.update(
        {
            "history_cutoff": WorkflowDecisionRecord(
                value=config.history_cutoff,
                source="analyst",
            ),
            "prediction_grid": WorkflowDecisionRecord(
                value=config.prediction_grid,
                source="analyst",
            ),
            "alpha": WorkflowDecisionRecord(
                value=config.alpha,
                source="analyst",
            ),
            "group_column": WorkflowDecisionRecord(
                value=config.group_column,
                source="analyst",
            ),
            "role_assignment": WorkflowDecisionRecord(
                value={
                    "proper_training": tuple(
                        map(str, proper_training.curve_ids)
                    ),
                    "calibration": tuple(map(str, calibration.curve_ids)),
                    "target": tuple(map(str, target.curve_ids)),
                },
                source="analyst",
                criterion="explicit_disjoint_workflow_roles",
            ),
        }
    )

    return SparsePredictionWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        training_workflow=training,
        calibration=calibrated,
        band=band,
        steps=tuple(steps),
        decisions=decisions,
        provenance={
            "raw_interpolation_performed": False,
            "random_role_split_performed": False,
            "proper_training_role_explicit": True,
            "calibration_role_explicit": True,
            "target_role_explicit": True,
            "coverage_scope": (
                "future_observed_measurements_on_declared_finite_grid"
            ),
            "automatic_model_selection_performed": False,
        },
        reports={
            "training_fit": training.reports["fit"],
            "prediction_band": sparse_fpca_conformal_band_reporting_text(band),
        },
        tables={
            "training_scores": training.tables["scores"].copy(),
            "calibration_curve_scores": calibrated.curve_scores.copy(),
            "prediction_band": sparse_fpca_conformal_band_frame(band),
        },
    )
