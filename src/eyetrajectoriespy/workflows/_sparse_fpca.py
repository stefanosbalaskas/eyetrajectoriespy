"""Transparent orchestration for native sparse univariate FPCA."""

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
from ..reporting import sparse_fpca_reporting_text
from ..sparse import SparseFPCAResult, sparse_fpca_score_frame
from ..sparse_bandwidth_selection import (
    SparseFPCABandwidthSelectionResult,
    select_sparse_fpca_bandwidths,
    sparse_fpca_bandwidth_selection_reporting_text,
)
from ..sparse_native import fit_sparse_fpca
from ..sparse_score_uncertainty import (
    SparseFPCAScoreUncertaintyResult,
    sparse_fpca_score_uncertainty,
    sparse_fpca_score_uncertainty_frame,
)
from ..sparse_score_uncertainty_reporting import (
    sparse_fpca_score_uncertainty_reporting_text,
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
class SparseFPCABandwidthSelectionConfig:
    """Explicit audited bandwidth-selection request."""

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
class SparseFPCAWorkflowConfig:
    """Complete declared configuration for the sparse-FPCA workflow."""

    dimension: str
    n_components: int
    evaluation_grid: tuple[float, ...]
    mean_bandwidth: float | None = None
    covariance_bandwidth: float | None = None
    bandwidth_selection: SparseFPCABandwidthSelectionConfig | None = None
    noise_bandwidth: float | None = None
    noise_support: tuple[float, float] | None = None
    analysis_support_action: str = "error"
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
    min_score_samples: int = 2
    score_failure_action: str = "error"
    mean_min_local_points: int = 3
    covariance_min_local_pairs: int = 6
    noise_min_local_points: int = 3
    score_uncertainty: ScoreUncertaintyConfig | None = None
    observation_diagnostics: ObservationDiagnosticConfig | None = None
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        if not str(self.dimension):
            raise ValueError("dimension must be non-empty")
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
class SparseFPCAWorkflowResult:
    """Frozen orchestration result retaining all primitive W2 outputs."""

    workflow_schema_version: int
    workflow_contract: str
    config: SparseFPCAWorkflowConfig
    fit: SparseFPCAResult
    bandwidth_selection: SparseFPCABandwidthSelectionResult | None
    score_uncertainty: SparseFPCAScoreUncertaintyResult | None
    observation_diagnostics: ObservationProcessDiagnosticResult | None
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_sparse_fpca_workflow(
    trajectories: IrregularTrajectorySet,
    *,
    config: SparseFPCAWorkflowConfig,
    observation_process: ObservationProcessData | None = None,
) -> SparseFPCAWorkflowResult:
    """Run explicit sparse FPCA/PACE orchestration without hidden tuning."""

    if not isinstance(trajectories, IrregularTrajectorySet):
        raise TypeError("trajectories must be an IrregularTrajectorySet")
    if not isinstance(config, SparseFPCAWorkflowConfig):
        raise TypeError("config must be a SparseFPCAWorkflowConfig")
    contract = "sparse_fpca:v1"
    require_empty_sparse_preprocessing(
        config.preprocessing,
        workflow_contract=contract,
    )

    steps: list[WorkflowStepRecord] = []
    selection: SparseFPCABandwidthSelectionResult | None = None
    criterion: str | None = None
    bandwidth_source = "analyst"

    if config.bandwidth_selection is not None:
        selector = config.bandwidth_selection
        selection_parameters = {
            "dimension": config.dimension,
            "evaluation_grid": config.evaluation_grid,
            "mean_bandwidths": selector.mean_bandwidths,
            "covariance_bandwidths": selector.covariance_bandwidths,
            "noise_bandwidth": config.noise_bandwidth,
            "noise_support": config.noise_support,
            "analysis_support_action": config.analysis_support_action,
            "noise_variance_method": config.noise_variance_method,
            "measurement_error_variance": config.measurement_error_variance,
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
            "positive_eigen_tolerance": config.positive_eigen_tolerance,
            "mean_smoother": config.mean_smoother,
            "covariance_smoother": config.covariance_smoother,
            "kernel": config.kernel,
            "mean_min_local_points": config.mean_min_local_points,
            "covariance_min_local_pairs": config.covariance_min_local_pairs,
            "noise_min_local_points": config.noise_min_local_points,
        }
        selection, step = timed_step(
            name="bandwidth_selection",
            function="select_sparse_fpca_bandwidths",
            parameters=selection_parameters,
            call=lambda: select_sparse_fpca_bandwidths(
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
                "audited sparse-FPCA bandwidth selection produced no "
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
        "dimension": config.dimension,
        "n_components": config.n_components,
        "evaluation_grid": config.evaluation_grid,
        "mean_bandwidth": mean_bandwidth,
        "covariance_bandwidth": covariance_bandwidth,
        "noise_bandwidth": config.noise_bandwidth,
        "noise_support": config.noise_support,
        "analysis_support_action": config.analysis_support_action,
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
        "min_score_samples": config.min_score_samples,
        "score_failure_action": config.score_failure_action,
        "mean_min_local_points": config.mean_min_local_points,
        "covariance_min_local_pairs": config.covariance_min_local_pairs,
        "noise_min_local_points": config.noise_min_local_points,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_sparse_fpca",
        parameters=fit_parameters,
        call=lambda: fit_sparse_fpca(
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

    uncertainty: SparseFPCAScoreUncertaintyResult | None = None
    if config.score_uncertainty is not None:
        uncertainty_parameters = {
            "condition_limit": config.score_uncertainty.condition_limit,
            "failure_action": config.score_uncertainty.failure_action,
        }
        uncertainty, step = timed_step(
            name="score_uncertainty",
            function="sparse_fpca_score_uncertainty",
            parameters=uncertainty_parameters,
            call=lambda: sparse_fpca_score_uncertainty(
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
        "noise_variance_method": WorkflowDecisionRecord(
            value=config.noise_variance_method,
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

    reports: dict[str, str] = {
        "fit": sparse_fpca_reporting_text(fit),
    }
    tables: dict[str, pd.DataFrame] = {
        "scores": sparse_fpca_score_frame(fit),
    }
    if selection is not None:
        reports["bandwidth_selection"] = (
            sparse_fpca_bandwidth_selection_reporting_text(selection)
        )
        tables["bandwidth_candidates"] = selection.candidate_summary.copy()
        tables["bandwidth_curve_losses"] = selection.curve_losses.copy()
    if uncertainty is not None:
        reports["score_uncertainty"] = (
            sparse_fpca_score_uncertainty_reporting_text(uncertainty)
        )
        tables["score_uncertainty"] = sparse_fpca_score_uncertainty_frame(
            uncertainty
        )
    if observation is not None:
        reports["observation_diagnostics"] = observation_process_reporting_text(
            observation
        )
        tables["observation_global"] = observation.global_summary.copy()
        tables["observation_time"] = observation.time_summary.copy()
        tables["observation_associations"] = observation.associations.copy()

    return SparseFPCAWorkflowResult(
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
            "native_observation_grids_retained": True,
            "bandwidth_mode": (
                "audited_selector" if selection is not None else "fixed"
            ),
            "automatic_model_selection_performed": False,
        },
        reports=reports,
        tables=tables,
    )
