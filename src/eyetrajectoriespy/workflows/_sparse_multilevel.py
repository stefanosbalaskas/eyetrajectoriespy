"""Transparent orchestration for native sparse multilevel FPCA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticResult,
)
from ..sparse_multilevel import (
    SparseMultilevelFPCAResult,
    fit_sparse_multilevel_fpca,
    sparse_multilevel_fpca_reporting_text,
)
from ..types import IrregularTrajectorySet
from ._core import (
    PreprocessingPlan,
    WORKFLOW_SCHEMA_VERSION,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
)
from ._sparse_shared import (
    ObservationDiagnosticConfig,
    normalized_grid,
    require_empty_sparse_preprocessing,
    run_observation_diagnostics,
    timed_step,
)


@dataclass(frozen=True)
class SparseMultilevelWorkflowConfig:
    """Declared fixed-bandwidth sparse participant/trial decomposition."""

    dimension: str
    participant_column: str
    participant_components: int
    trial_components: int
    evaluation_grid: tuple[float, ...]
    mean_bandwidth: float
    total_covariance_bandwidth: float
    between_covariance_bandwidth: float
    noise_bandwidth: float | None = None
    noise_support: tuple[float, float] | None = None
    analysis_support_action: str = "error"
    weighting: str = "observation"
    mean_smoother: str = "local_linear"
    covariance_smoother: str = "local_linear"
    kernel: str = "epanechnikov"
    noise_variance_method: str = "diagonal_difference"
    measurement_error_variance: float | None = None
    psd_action: str = "error"
    psd_tolerance: float = 1e-8
    positive_eigen_tolerance: float = 1e-10
    score_ridge: float = 0.0
    score_condition_limit: float = 1e12
    min_participant_score_samples: int = 2
    score_failure_action: str = "error"
    mean_min_local_points: int = 3
    total_covariance_min_local_pairs: int = 6
    between_covariance_min_local_pairs: int = 6
    noise_min_local_points: int = 3
    observation_diagnostics: ObservationDiagnosticConfig | None = None
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        if not str(self.dimension):
            raise ValueError("dimension must be non-empty")
        if not str(self.participant_column):
            raise ValueError("participant_column must be non-empty")
        for name in ("participant_components", "trial_components"):
            value = getattr(self, name)
            if isinstance(value, bool) or int(value) < 1:
                raise ValueError(f"{name} must be a positive integer")
            object.__setattr__(self, name, int(value))
        object.__setattr__(
            self,
            "evaluation_grid",
            normalized_grid(self.evaluation_grid, name="evaluation_grid"),
        )
        for name in (
            "mean_bandwidth",
            "total_covariance_bandwidth",
            "between_covariance_bandwidth",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
            object.__setattr__(self, name, value)
        if self.noise_bandwidth is not None:
            value = float(self.noise_bandwidth)
            if not np.isfinite(value) or value <= 0:
                raise ValueError(
                    "noise_bandwidth must be finite and positive"
                )
            object.__setattr__(self, "noise_bandwidth", value)
        if self.noise_support is not None:
            support = tuple(map(float, self.noise_support))
            if (
                len(support) != 2
                or not np.all(np.isfinite(support))
                or support[0] >= support[1]
            ):
                raise ValueError(
                    "noise_support must be a finite increasing pair"
                )
            object.__setattr__(self, "noise_support", support)


@dataclass(frozen=True)
class SparseMultilevelWorkflowResult:
    """Frozen sparse multilevel workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: SparseMultilevelWorkflowConfig
    fit: SparseMultilevelFPCAResult
    observation_diagnostics: ObservationProcessDiagnosticResult | None
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_sparse_multilevel_workflow(
    trajectories: IrregularTrajectorySet,
    *,
    config: SparseMultilevelWorkflowConfig,
    observation_process: ObservationProcessData | None = None,
) -> SparseMultilevelWorkflowResult:
    """Run sparse participant/trial FPCA with fixed explicit bandwidths."""

    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if not isinstance(config, SparseMultilevelWorkflowConfig):
        raise TypeError(
            "config must be a SparseMultilevelWorkflowConfig"
        )
    contract = "sparse_multilevel:v1"
    require_empty_sparse_preprocessing(
        config.preprocessing,
        workflow_contract=contract,
    )

    fit_parameters = {
        "dimension": config.dimension,
        "participant_column": config.participant_column,
        "participant_components": config.participant_components,
        "trial_components": config.trial_components,
        "evaluation_grid": config.evaluation_grid,
        "mean_bandwidth": config.mean_bandwidth,
        "total_covariance_bandwidth": config.total_covariance_bandwidth,
        "between_covariance_bandwidth": config.between_covariance_bandwidth,
        "noise_bandwidth": config.noise_bandwidth,
        "noise_support": config.noise_support,
        "analysis_support_action": config.analysis_support_action,
        "weighting": config.weighting,
        "mean_smoother": config.mean_smoother,
        "covariance_smoother": config.covariance_smoother,
        "kernel": config.kernel,
        "noise_variance_method": config.noise_variance_method,
        "measurement_error_variance": config.measurement_error_variance,
        "psd_action": config.psd_action,
        "psd_tolerance": config.psd_tolerance,
        "positive_eigen_tolerance": config.positive_eigen_tolerance,
        "score_ridge": config.score_ridge,
        "score_condition_limit": config.score_condition_limit,
        "min_participant_score_samples": config.min_participant_score_samples,
        "score_failure_action": config.score_failure_action,
        "mean_min_local_points": config.mean_min_local_points,
        "total_covariance_min_local_pairs": (
            config.total_covariance_min_local_pairs
        ),
        "between_covariance_min_local_pairs": (
            config.between_covariance_min_local_pairs
        ),
        "noise_min_local_points": config.noise_min_local_points,
    }
    fit, fit_step = timed_step(
        name="fit",
        function="fit_sparse_multilevel_fpca",
        parameters=fit_parameters,
        call=lambda: fit_sparse_multilevel_fpca(
            trajectories,
            **{
                **fit_parameters,
                "evaluation_grid": np.asarray(
                    fit_parameters["evaluation_grid"],
                    dtype=float,
                ),
            },
        ),
    )
    steps = [fit_step]

    observation, observation_step = run_observation_diagnostics(
        process=observation_process,
        config=config.observation_diagnostics,
    )
    if observation_step is not None:
        steps.append(observation_step)

    tables: dict[str, pd.DataFrame] = {
        "participant_scores": fit.participant_scores.copy(),
        "trial_scores": fit.trial_scores.copy(),
        "score_diagnostics": fit.score_diagnostics.copy(),
    }
    if observation is not None:
        tables["observation_global"] = observation.global_summary.copy()
        tables["observation_time"] = observation.time_summary.copy()
        tables["observation_associations"] = observation.associations.copy()

    return SparseMultilevelWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        observation_diagnostics=observation,
        steps=tuple(steps),
        decisions={
            "participant_components": WorkflowDecisionRecord(
                value=config.participant_components,
                source="analyst",
            ),
            "trial_components": WorkflowDecisionRecord(
                value=config.trial_components,
                source="analyst",
            ),
            "mean_bandwidth": WorkflowDecisionRecord(
                value=config.mean_bandwidth,
                source="analyst",
            ),
            "total_covariance_bandwidth": WorkflowDecisionRecord(
                value=config.total_covariance_bandwidth,
                source="analyst",
            ),
            "between_covariance_bandwidth": WorkflowDecisionRecord(
                value=config.between_covariance_bandwidth,
                source="analyst",
            ),
            "weighting": WorkflowDecisionRecord(
                value=config.weighting,
                source="analyst",
            ),
            "psd_action": WorkflowDecisionRecord(
                value=config.psd_action,
                source="analyst",
            ),
            "observation_diagnostics_requested": WorkflowDecisionRecord(
                value=config.observation_diagnostics is not None,
                source="analyst",
            ),
        },
        provenance={
            "raw_interpolation_performed": False,
            "native_observation_grids_retained": True,
            "bandwidth_mode": "fixed",
            "bandwidth_selector_available": False,
            "automatic_model_selection_performed": False,
        },
        reports={"fit": sparse_multilevel_fpca_reporting_text(fit)},
        tables=tables,
    )
