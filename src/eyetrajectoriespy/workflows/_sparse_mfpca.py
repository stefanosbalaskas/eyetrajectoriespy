"""Transparent orchestration for native paired sparse planar MFPCA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..observation_process import (
    ObservationProcessData,
    ObservationProcessDiagnosticResult,
    observation_process_reporting_text,
)
from ..sparse_multivariate import (
    SparseMFPCAResult,
    fit_sparse_mfpca,
    sparse_mfpca_reporting_text,
    sparse_mfpca_score_frame,
)
from ..sparse_multivariate_bandwidth_selection import (
    SparseMFPCABandwidthSelectionResult,
    select_sparse_mfpca_bandwidths,
    sparse_mfpca_bandwidth_selection_reporting_text,
)
from ..sparse_multivariate_score_uncertainty import (
    SparseMFPCAScoreUncertaintyResult,
    sparse_mfpca_score_uncertainty,
    sparse_mfpca_score_uncertainty_frame,
    sparse_mfpca_score_uncertainty_reporting_text,
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
    ScoreUncertaintyConfig,
    normalized_grid,
    positive_candidates,
    require_empty_sparse_preprocessing,
    run_observation_diagnostics,
    timed_step,
)


@dataclass(frozen=True)
class SparseMFPCABandwidthSelectionConfig:
    """Explicit audited paired-planar bandwidth-selection request."""

    mean_bandwidths: tuple[float, ...]
    covariance_bandwidths: tuple[float, ...]
    n_splits: int = 5
    resampling_unit: str = "curve"
    group_column: str | None = None
    shuffle: bool = True
    random_state: int | None = 0
    min_valid_folds: int | None = None
    failure_action: str = "retain"
    predictive_condition_limit: float = 1e12

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mean_bandwidths",
            positive_candidates(self.mean_bandwidths, name="mean_bandwidths"),
        )
        object.__setattr__(
            self,
            "covariance_bandwidths",
            positive_candidates(
                self.covariance_bandwidths,
                name="covariance_bandwidths",
            ),
        )
        if isinstance(self.n_splits, bool) or int(self.n_splits) < 2:
            raise ValueError("n_splits must be an integer >= 2")
        object.__setattr__(self, "n_splits", int(self.n_splits))


@dataclass(frozen=True)
class SparseMFPCAWorkflowConfig:
    """Declared configuration for paired sparse planar MFPCA."""

    n_components: int
    evaluation_grid: tuple[float, ...]
    measurement_error: str
    dimensions: tuple[str, str] = ("x", "y")
    mean_bandwidth: float | None = None
    covariance_bandwidth: float | None = None
    bandwidth_selection: SparseMFPCABandwidthSelectionConfig | None = None
    measurement_error_variance: tuple[float, float] | None = None
    measurement_error_covariance: np.ndarray | None = None
    analysis_support_action: str = "error"
    psd_action: str = "error"
    psd_tolerance: float = 1e-8
    positive_eigen_tolerance: float = 1e-10
    score_ridge: float = 0.0
    score_condition_limit: float = 1e12
    min_score_time_points: int = 2
    score_failure_action: str = "error"
    mean_min_local_points: int = 3
    covariance_min_local_pairs: int = 6
    score_uncertainty: ScoreUncertaintyConfig | None = None
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
        fixed_any = (
            self.mean_bandwidth is not None
            or self.covariance_bandwidth is not None
        )
        fixed_complete = (
            self.mean_bandwidth is not None
            and self.covariance_bandwidth is not None
        )
        selected = self.bandwidth_selection is not None
        if fixed_any and not fixed_complete:
            raise ValueError(
                "fixed bandwidth mode requires both mean_bandwidth and "
                "covariance_bandwidth"
            )
        if fixed_complete == selected:
            raise ValueError(
                "declare exactly one bandwidth mode: fixed values or "
                "bandwidth_selection"
            )
        if fixed_complete:
            for name, value in (
                ("mean_bandwidth", self.mean_bandwidth),
                ("covariance_bandwidth", self.covariance_bandwidth),
            ):
                number = float(value)
                if not np.isfinite(number) or number <= 0:
                    raise ValueError(f"{name} must be finite and positive")
                object.__setattr__(self, name, number)


@dataclass(frozen=True)
class SparseMFPCAWorkflowResult:
    """Frozen paired sparse-MFPCA workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: SparseMFPCAWorkflowConfig
    fit: SparseMFPCAResult
    bandwidth_selection: SparseMFPCABandwidthSelectionResult | None
    score_uncertainty: SparseMFPCAScoreUncertaintyResult | None
    observation_diagnostics: ObservationProcessDiagnosticResult | None
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_sparse_mfpca_workflow(
    trajectories: IrregularTrajectorySet,
    *,
    config: SparseMFPCAWorkflowConfig,
    observation_process: ObservationProcessData | None = None,
) -> SparseMFPCAWorkflowResult:
    """Run explicit paired sparse planar MFPCA orchestration."""

    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if not isinstance(config, SparseMFPCAWorkflowConfig):
        raise TypeError("config must be a SparseMFPCAWorkflowConfig")
    contract = "sparse_mfpca:v1"
    require_empty_sparse_preprocessing(
        config.preprocessing,
        workflow_contract=contract,
    )
    steps: list[WorkflowStepRecord] = []
    selection: SparseMFPCABandwidthSelectionResult | None = None
    criterion: str | None = None
    bandwidth_source = "analyst"

    if config.bandwidth_selection is not None:
        selector = config.bandwidth_selection
        selection_parameters = {
            "dimensions": config.dimensions,
            "evaluation_grid": config.evaluation_grid,
            "mean_bandwidths": selector.mean_bandwidths,
            "covariance_bandwidths": selector.covariance_bandwidths,
            "measurement_error": config.measurement_error,
            "measurement_error_variance": config.measurement_error_variance,
            "measurement_error_covariance": config.measurement_error_covariance,
            "analysis_support_action": config.analysis_support_action,
            "n_splits": selector.n_splits,
            "resampling_unit": selector.resampling_unit,
            "group_column": selector.group_column,
            "shuffle": selector.shuffle,
            "random_state": selector.random_state,
            "min_valid_folds": selector.min_valid_folds,
            "failure_action": selector.failure_action,
            "predictive_condition_limit": selector.predictive_condition_limit,
            "psd_action": config.psd_action,
            "psd_tolerance": config.psd_tolerance,
            "mean_min_local_points": config.mean_min_local_points,
            "covariance_min_local_pairs": config.covariance_min_local_pairs,
        }
        selection, step = timed_step(
            name="bandwidth_selection",
            function="select_sparse_mfpca_bandwidths",
            parameters=selection_parameters,
            call=lambda: select_sparse_mfpca_bandwidths(
                trajectories,
                **{
                    **selection_parameters,
                    "evaluation_grid": np.asarray(
                        selection_parameters["evaluation_grid"],
                        dtype=float,
                    ),
                },
            ),
        )
        steps.append(step)
        if selection.selected_bandwidths is None:
            raise RuntimeError(
                "audited sparse-MFPCA bandwidth selection produced no "
                "eligible candidate"
            )
        mean_bandwidth = float(
            selection.selected_bandwidths["mean_bandwidth"]
        )
        covariance_bandwidth = float(
            selection.selected_bandwidths["covariance_bandwidth"]
        )
        bandwidth_source = "audited_selector"
        criterion = selection.criterion
    else:
        assert config.mean_bandwidth is not None
        assert config.covariance_bandwidth is not None
        mean_bandwidth = float(config.mean_bandwidth)
        covariance_bandwidth = float(config.covariance_bandwidth)

    fit_parameters = {
        "dimensions": config.dimensions,
        "n_components": config.n_components,
        "evaluation_grid": config.evaluation_grid,
        "mean_bandwidth": mean_bandwidth,
        "covariance_bandwidth": covariance_bandwidth,
        "measurement_error": config.measurement_error,
        "measurement_error_variance": config.measurement_error_variance,
        "measurement_error_covariance": config.measurement_error_covariance,
        "analysis_support_action": config.analysis_support_action,
        "psd_action": config.psd_action,
        "psd_tolerance": config.psd_tolerance,
        "positive_eigen_tolerance": config.positive_eigen_tolerance,
        "score_ridge": config.score_ridge,
        "score_condition_limit": config.score_condition_limit,
        "min_score_time_points": config.min_score_time_points,
        "score_failure_action": config.score_failure_action,
        "mean_min_local_points": config.mean_min_local_points,
        "covariance_min_local_pairs": config.covariance_min_local_pairs,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_sparse_mfpca",
        parameters=fit_parameters,
        call=lambda: fit_sparse_mfpca(
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
    steps.append(step)

    uncertainty: SparseMFPCAScoreUncertaintyResult | None = None
    if config.score_uncertainty is not None:
        uncertainty_parameters = {
            "condition_limit": config.score_uncertainty.condition_limit,
            "failure_action": config.score_uncertainty.failure_action,
        }
        uncertainty, step = timed_step(
            name="score_uncertainty",
            function="sparse_mfpca_score_uncertainty",
            parameters=uncertainty_parameters,
            call=lambda: sparse_mfpca_score_uncertainty(
                fit,
                trajectories,
                **uncertainty_parameters,
            ),
        )
        steps.append(step)

    observation, observation_step = run_observation_diagnostics(
        process=observation_process,
        config=config.observation_diagnostics,
    )
    if observation_step is not None:
        steps.append(observation_step)

    decisions = {
        "n_components": WorkflowDecisionRecord(
            value=config.n_components,
            source="analyst",
        ),
        "mean_bandwidth": WorkflowDecisionRecord(
            value=mean_bandwidth,
            source=bandwidth_source,
            criterion=criterion,
        ),
        "covariance_bandwidth": WorkflowDecisionRecord(
            value=covariance_bandwidth,
            source=bandwidth_source,
            criterion=criterion,
        ),
        "measurement_error": WorkflowDecisionRecord(
            value=config.measurement_error,
            source="analyst",
        ),
        "psd_action": WorkflowDecisionRecord(
            value=config.psd_action,
            source="analyst",
        ),
        "score_uncertainty_requested": WorkflowDecisionRecord(
            value=config.score_uncertainty is not None,
            source="analyst",
        ),
        "observation_diagnostics_requested": WorkflowDecisionRecord(
            value=config.observation_diagnostics is not None,
            source="analyst",
        ),
    }
    reports: dict[str, str] = {"fit": sparse_mfpca_reporting_text(fit)}
    tables: dict[str, pd.DataFrame] = {
        "scores": sparse_mfpca_score_frame(fit),
    }
    if selection is not None:
        reports["bandwidth_selection"] = (
            sparse_mfpca_bandwidth_selection_reporting_text(selection)
        )
        tables["bandwidth_candidates"] = selection.candidate_summary.copy()
        tables["bandwidth_curve_losses"] = selection.curve_losses.copy()
    if uncertainty is not None:
        reports["score_uncertainty"] = (
            sparse_mfpca_score_uncertainty_reporting_text(uncertainty)
        )
        tables["score_uncertainty"] = sparse_mfpca_score_uncertainty_frame(
            uncertainty
        )
    if observation is not None:
        reports["observation_diagnostics"] = observation_process_reporting_text(
            observation
        )
        tables["observation_global"] = observation.global_summary.copy()
        tables["observation_time"] = observation.time_summary.copy()
        tables["observation_associations"] = observation.associations.copy()

    return SparseMFPCAWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        bandwidth_selection=selection,
        score_uncertainty=uncertainty,
        observation_diagnostics=observation,
        steps=tuple(steps),
        decisions=decisions,
        provenance={
            "raw_interpolation_performed": False,
            "native_paired_observation_grids_retained": True,
            "bandwidth_mode": (
                "audited_selector" if selection is not None else "fixed"
            ),
            "automatic_model_selection_performed": False,
        },
        reports=reports,
        tables=tables,
    )
