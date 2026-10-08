"""Transparent orchestration for asynchronous sparse planar MFPCA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticResult,
)
from ..sparse_multivariate_async import (
    SparseAsyncMFPCAResult,
    fit_sparse_mfpca_async,
    sparse_mfpca_async_reporting_text,
    sparse_mfpca_async_score_frame,
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
class SparseMFPCAAsyncWorkflowConfig:
    """Declared configuration for asynchronous sparse planar MFPCA."""

    n_components: int
    evaluation_grid: tuple[float, ...]
    mean_bandwidth: float
    covariance_bandwidth: float
    measurement_error: str
    dimensions: tuple[str, str] = ("x", "y")
    measurement_error_variance: tuple[float, float] | None = None
    measurement_error_covariance: np.ndarray | None = None
    analysis_support_action: str = "error"
    same_time_tolerance: float = 0.0
    psd_action: str = "error"
    psd_tolerance: float = 1e-8
    positive_eigen_tolerance: float = 1e-10
    score_ridge: float = 0.0
    score_condition_limit: float = 1e12
    min_score_observations: int = 2
    score_failure_action: str = "error"
    mean_min_local_points: int = 3
    covariance_min_local_pairs: int = 6
    observation_diagnostics: ObservationDiagnosticConfig | None = None
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        dimensions = tuple(map(str, self.dimensions))
        if len(dimensions) != 2 or dimensions[0] == dimensions[1]:
            raise ValueError("dimensions must contain two distinct names")
        object.__setattr__(self, "dimensions", dimensions)
        if isinstance(self.n_components, bool) or int(self.n_components) < 1:
            raise ValueError("n_components must be a positive integer")
        object.__setattr__(self, "n_components", int(self.n_components))
        object.__setattr__(
            self,
            "evaluation_grid",
            normalized_grid(self.evaluation_grid, name="evaluation_grid"),
        )
        for name in ("mean_bandwidth", "covariance_bandwidth"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
            object.__setattr__(self, name, value)
        tolerance = float(self.same_time_tolerance)
        if not np.isfinite(tolerance) or tolerance < 0:
            raise ValueError(
                "same_time_tolerance must be finite and non-negative"
            )
        object.__setattr__(self, "same_time_tolerance", tolerance)


@dataclass(frozen=True)
class SparseMFPCAAsyncWorkflowResult:
    """Frozen asynchronous sparse-MFPCA workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: SparseMFPCAAsyncWorkflowConfig
    fit: SparseAsyncMFPCAResult
    observation_diagnostics: ObservationProcessDiagnosticResult | None
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_sparse_mfpca_async_workflow(
    trajectories: IrregularTrajectorySet,
    *,
    config: SparseMFPCAAsyncWorkflowConfig,
    observation_process: ObservationProcessData | None = None,
) -> SparseMFPCAAsyncWorkflowResult:
    """Run asynchronous sparse planar MFPCA with fixed explicit bandwidths."""

    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if not isinstance(config, SparseMFPCAAsyncWorkflowConfig):
        raise TypeError(
            "config must be a SparseMFPCAAsyncWorkflowConfig"
        )
    contract = "sparse_mfpca_async:v1"
    require_empty_sparse_preprocessing(
        config.preprocessing,
        workflow_contract=contract,
    )

    fit_parameters = {
        "dimensions": config.dimensions,
        "n_components": config.n_components,
        "evaluation_grid": config.evaluation_grid,
        "mean_bandwidth": config.mean_bandwidth,
        "covariance_bandwidth": config.covariance_bandwidth,
        "measurement_error": config.measurement_error,
        "measurement_error_variance": config.measurement_error_variance,
        "measurement_error_covariance": config.measurement_error_covariance,
        "analysis_support_action": config.analysis_support_action,
        "same_time_tolerance": config.same_time_tolerance,
        "psd_action": config.psd_action,
        "psd_tolerance": config.psd_tolerance,
        "positive_eigen_tolerance": config.positive_eigen_tolerance,
        "score_ridge": config.score_ridge,
        "score_condition_limit": config.score_condition_limit,
        "min_score_observations": config.min_score_observations,
        "score_failure_action": config.score_failure_action,
        "mean_min_local_points": config.mean_min_local_points,
        "covariance_min_local_pairs": config.covariance_min_local_pairs,
    }
    fit, fit_step = timed_step(
        name="fit",
        function="fit_sparse_mfpca_async",
        parameters=fit_parameters,
        call=lambda: fit_sparse_mfpca_async(
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

    reports = {"fit": sparse_mfpca_async_reporting_text(fit)}
    tables: dict[str, pd.DataFrame] = {
        "scores": sparse_mfpca_async_score_frame(fit),
    }
    if observation is not None:
        tables["observation_global"] = observation.global_summary.copy()
        tables["observation_time"] = observation.time_summary.copy()
        tables["observation_associations"] = observation.associations.copy()

    return SparseMFPCAAsyncWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        observation_diagnostics=observation,
        steps=tuple(steps),
        decisions={
            "n_components": WorkflowDecisionRecord(
                value=config.n_components,
                source="analyst",
            ),
            "mean_bandwidth": WorkflowDecisionRecord(
                value=config.mean_bandwidth,
                source="analyst",
            ),
            "covariance_bandwidth": WorkflowDecisionRecord(
                value=config.covariance_bandwidth,
                source="analyst",
            ),
            "measurement_error": WorkflowDecisionRecord(
                value=config.measurement_error,
                source="analyst",
            ),
            "same_time_tolerance": WorkflowDecisionRecord(
                value=config.same_time_tolerance,
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
            "raw_synchronization_performed": False,
            "time_binning_performed": False,
            "coordinate_specific_native_grids_retained": True,
            "bandwidth_mode": "fixed",
            "paired_bandwidth_selector_reused": False,
            "automatic_model_selection_performed": False,
        },
        reports=reports,
        tables=tables,
    )
