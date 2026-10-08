"""Transparent W3 orchestration for dense FPCA and functional regression.

W3 composes already-qualified common-grid estimators. It does not add model
selection, response-family inference, preprocessing defaults, or estimator
fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

from ..fpca import fit_fpca, fpca_score_frame
from ..function_on_scalar import (
    fit_function_on_scalar_regression,
    function_on_scalar_coefficient_frame,
)
from ..functional_mixed_effects import (
    fit_functional_mixed_effects_regression,
    functional_mixed_effects_coefficient_frame,
)
from ..generalized_function_on_scalar import (
    fit_generalized_function_on_scalar_regression,
    generalized_function_on_scalar_coefficient_frame,
    generalized_function_on_scalar_reporting_text,
)
from ..reporting import (
    fpca_reporting_text,
    function_on_scalar_reporting_text,
    functional_mixed_effects_reporting_text,
    summarise_fpca,
)
from ..types import (
    FPCAResult,
    FunctionOnScalarResult,
    FunctionalMixedEffectsResult,
    GeneralizedFunctionOnScalarResult,
    TrajectorySet,
)
from ._core import (
    PreprocessingPlan,
    WORKFLOW_SCHEMA_VERSION,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
)
from ._sparse_shared import timed_step


def _predictors(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    predictors = tuple(map(str, values))
    if not predictors:
        raise ValueError("predictors must contain at least one name")
    if len(set(predictors)) != len(predictors):
        raise ValueError("predictors must not contain duplicates")
    return predictors


def _require_empty_preprocessing(
    preprocessing: PreprocessingPlan,
    *,
    workflow_contract: str,
) -> None:
    if not isinstance(preprocessing, PreprocessingPlan):
        raise TypeError("preprocessing must be a PreprocessingPlan")
    if preprocessing.steps:
        raise ValueError(
            f"{workflow_contract} currently requires an empty preprocessing "
            "plan; W3 composes complete common-grid inputs exactly as supplied "
            "and no in-workflow transformation executor has been qualified"
        )


def _optional_array(
    value: np.ndarray | tuple[float, ...] | tuple[tuple[float, ...], ...] | None,
    *,
    name: str,
) -> np.ndarray | None:
    if value is None:
        return None
    array = np.asarray(value, dtype=float).copy()
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class FPCAWorkflowConfig:
    """Declared common-grid FPCA configuration."""

    n_components: int | float = 0.95
    scaling: str = "none"
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        if isinstance(self.n_components, bool):
            raise TypeError("n_components must be an integer count or variance proportion")
        if isinstance(self.n_components, (int, np.integer)):
            value = int(self.n_components)
            if value < 1:
                raise ValueError("integer n_components must be positive")
            object.__setattr__(self, "n_components", value)
        else:
            value = float(self.n_components)
            if not np.isfinite(value) or not 0.0 < value <= 1.0:
                raise ValueError(
                    "floating n_components must be a finite variance proportion within (0, 1]"
                )
            object.__setattr__(self, "n_components", value)
        if self.scaling not in {"none", "dimension_sd"}:
            raise ValueError("scaling must be 'none' or 'dimension_sd'")


@dataclass(frozen=True)
class FPCAWorkflowResult:
    """Frozen dense FPCA workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: FPCAWorkflowConfig
    fit: FPCAResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_fpca_workflow(
    trajectories: TrajectorySet,
    *,
    config: FPCAWorkflowConfig,
) -> FPCAWorkflowResult:
    """Run common-grid FPCA without hidden preprocessing or component tuning."""

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if not isinstance(config, FPCAWorkflowConfig):
        raise TypeError("config must be an FPCAWorkflowConfig")
    contract = "fpca:v1"
    _require_empty_preprocessing(config.preprocessing, workflow_contract=contract)

    parameters = {
        "n_components": config.n_components,
        "scaling": config.scaling,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_fpca",
        parameters=parameters,
        call=lambda: fit_fpca(trajectories, **parameters),
    )
    return FPCAWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        steps=(step,),
        decisions={
            "requested_n_components": WorkflowDecisionRecord(
                value=config.n_components,
                source="analyst",
            ),
            "retained_n_components": WorkflowDecisionRecord(
                value=fit.n_components,
                source="derived",
                criterion=(
                    "resolved by fit_fpca from the analyst-declared component "
                    "count or variance-retention threshold"
                ),
            ),
            "scaling": WorkflowDecisionRecord(
                value=config.scaling,
                source="analyst",
            ),
        },
        provenance={
            "input_layout": "complete_common_grid",
            "preprocessing_executed": False,
            "automatic_model_selection_performed": False,
            "component_resolution_rule_changed": False,
        },
        reports={"fit": fpca_reporting_text(fit)},
        tables={
            "scores": fpca_score_frame(fit),
            "explained_variance": summarise_fpca(fit),
        },
    )


@dataclass(frozen=True)
class FunctionOnScalarWorkflowConfig:
    """Declared observed-grid function-on-scalar regression configuration."""

    predictors: tuple[str, ...]
    dimensions: tuple[str, ...] | None = None
    participant_column: str | None = None
    unit: str = "curve"
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        object.__setattr__(self, "predictors", _predictors(self.predictors))
        if self.dimensions is not None:
            dimensions = tuple(map(str, self.dimensions))
            if not dimensions or len(set(dimensions)) != len(dimensions):
                raise ValueError("dimensions must be non-empty and unique")
            object.__setattr__(self, "dimensions", dimensions)
        if self.unit not in {"curve", "participant"}:
            raise ValueError("unit must be 'curve' or 'participant'")
        if self.unit == "curve" and self.participant_column is not None:
            raise ValueError("participant_column must be None when unit='curve'")
        if self.unit == "participant" and not self.participant_column:
            raise ValueError("participant unit requires participant_column")


@dataclass(frozen=True)
class FunctionOnScalarWorkflowResult:
    """Frozen function-on-scalar workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: FunctionOnScalarWorkflowConfig
    fit: FunctionOnScalarResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_function_on_scalar_workflow(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    *,
    config: FunctionOnScalarWorkflowConfig,
) -> FunctionOnScalarWorkflowResult:
    """Run explicit observed-grid function-on-scalar regression."""

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if not isinstance(design, pd.DataFrame):
        raise TypeError("design must be a pandas DataFrame")
    if not isinstance(config, FunctionOnScalarWorkflowConfig):
        raise TypeError("config must be a FunctionOnScalarWorkflowConfig")
    contract = "function_on_scalar:v1"
    _require_empty_preprocessing(config.preprocessing, workflow_contract=contract)

    parameters = {
        "predictors": config.predictors,
        "dimensions": config.dimensions,
        "participant_column": config.participant_column,
        "unit": config.unit,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_function_on_scalar_regression",
        parameters=parameters,
        call=lambda: fit_function_on_scalar_regression(
            trajectories,
            design,
            config.predictors,
            dimensions=config.dimensions,
            participant_column=config.participant_column,
            unit=config.unit,
        ),
    )
    return FunctionOnScalarWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        steps=(step,),
        decisions={
            "predictors": WorkflowDecisionRecord(
                value=config.predictors,
                source="analyst",
            ),
            "dimensions": WorkflowDecisionRecord(
                value=config.dimensions,
                source="analyst",
            ),
            "unit": WorkflowDecisionRecord(value=config.unit, source="analyst"),
            "participant_column": WorkflowDecisionRecord(
                value=config.participant_column,
                source="analyst",
            ),
        },
        provenance={
            "input_layout": "complete_common_grid",
            "preprocessing_executed": False,
            "automatic_predictor_encoding": False,
            "automatic_model_selection_performed": False,
            "functional_mixed_effects_inferred": False,
        },
        reports={"fit": function_on_scalar_reporting_text(fit)},
        tables={"coefficients": function_on_scalar_coefficient_frame(fit)},
    )


@dataclass(frozen=True)
class FunctionalMixedEffectsWorkflowConfig:
    """Declared Gaussian functional mixed-effects configuration."""

    predictors: tuple[str, ...]
    participant_column: str
    dimension: str
    fixed_basis_size: int = 6
    random_basis_size: int = 4
    random_slope_predictor: str | None = None
    trial_column: str | None = None
    trial_random_effect: str | None = None
    trial_random_basis_size: int = 3
    residual_correlation: str = "iid"
    spline_degree: int = 3
    reml: bool = True
    method: str = "lbfgs"
    maxiter: int = 500
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        object.__setattr__(self, "predictors", _predictors(self.predictors))
        if not self.participant_column:
            raise ValueError("participant_column must be non-empty")
        if not self.dimension:
            raise ValueError("dimension must be non-empty")


@dataclass(frozen=True)
class FunctionalMixedEffectsWorkflowResult:
    """Frozen Gaussian functional mixed-effects workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: FunctionalMixedEffectsWorkflowConfig
    fit: FunctionalMixedEffectsResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_functional_mixed_effects_workflow(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    *,
    config: FunctionalMixedEffectsWorkflowConfig,
) -> FunctionalMixedEffectsWorkflowResult:
    """Run an explicitly specified Gaussian functional mixed-effects model."""

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if not isinstance(design, pd.DataFrame):
        raise TypeError("design must be a pandas DataFrame")
    if not isinstance(config, FunctionalMixedEffectsWorkflowConfig):
        raise TypeError("config must be a FunctionalMixedEffectsWorkflowConfig")
    contract = "functional_mixed_effects:v1"
    _require_empty_preprocessing(config.preprocessing, workflow_contract=contract)

    parameters = {
        "predictors": config.predictors,
        "participant_column": config.participant_column,
        "dimension": config.dimension,
        "fixed_basis_size": config.fixed_basis_size,
        "random_basis_size": config.random_basis_size,
        "random_slope_predictor": config.random_slope_predictor,
        "trial_column": config.trial_column,
        "trial_random_effect": config.trial_random_effect,
        "trial_random_basis_size": config.trial_random_basis_size,
        "residual_correlation": config.residual_correlation,
        "spline_degree": config.spline_degree,
        "reml": config.reml,
        "method": config.method,
        "maxiter": config.maxiter,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_functional_mixed_effects_regression",
        parameters=parameters,
        call=lambda: fit_functional_mixed_effects_regression(
            trajectories,
            design,
            config.predictors,
            participant_column=config.participant_column,
            dimension=config.dimension,
            fixed_basis_size=config.fixed_basis_size,
            random_basis_size=config.random_basis_size,
            random_slope_predictor=config.random_slope_predictor,
            trial_column=config.trial_column,
            trial_random_effect=config.trial_random_effect,
            trial_random_basis_size=config.trial_random_basis_size,
            residual_correlation=config.residual_correlation,
            spline_degree=config.spline_degree,
            reml=config.reml,
            method=config.method,
            maxiter=config.maxiter,
        ),
    )
    decisions = {
        name: WorkflowDecisionRecord(value=value, source="analyst")
        for name, value in parameters.items()
    }
    return FunctionalMixedEffectsWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        steps=(step,),
        decisions=decisions,
        provenance={
            "input_layout": "complete_common_grid",
            "preprocessing_executed": False,
            "automatic_random_effect_selection": False,
            "automatic_residual_correlation_selection": False,
            "automatic_optimizer_fallback": False,
            "automatic_model_selection_performed": False,
        },
        reports={"fit": functional_mixed_effects_reporting_text(fit)},
        tables={
            "coefficients": functional_mixed_effects_coefficient_frame(fit),
        },
    )


@dataclass(frozen=True)
class GeneralizedFunctionalWorkflowConfig:
    """Declared marginal generalized function-on-scalar configuration."""

    predictors: tuple[str, ...]
    participant_column: str
    dimension: str
    family: str
    binomial_denominator: np.ndarray | tuple[float, ...] | tuple[tuple[float, ...], ...] | None = None
    exposure: np.ndarray | tuple[float, ...] | tuple[tuple[float, ...], ...] | None = None
    exposure_units: str | None = None
    basis_size: int = 5
    spline_degree: int = 3
    working_correlation: str = "independence"
    covariance_type: str = "robust"
    maxiter: int = 100
    ctol: float = 1e-8
    preprocessing: PreprocessingPlan = field(default_factory=PreprocessingPlan)

    def __post_init__(self) -> None:
        object.__setattr__(self, "predictors", _predictors(self.predictors))
        if not self.participant_column:
            raise ValueError("participant_column must be non-empty")
        if not self.dimension:
            raise ValueError("dimension must be non-empty")
        family = str(self.family).lower().strip()
        if family not in {"binomial", "poisson"}:
            raise ValueError("family must be explicitly 'binomial' or 'poisson'")
        object.__setattr__(self, "family", family)
        object.__setattr__(
            self,
            "binomial_denominator",
            _optional_array(
                self.binomial_denominator,
                name="binomial_denominator",
            ),
        )
        object.__setattr__(
            self,
            "exposure",
            _optional_array(self.exposure, name="exposure"),
        )


@dataclass(frozen=True)
class GeneralizedFunctionalWorkflowResult:
    """Frozen marginal generalized functional workflow result."""

    workflow_schema_version: int
    workflow_contract: str
    config: GeneralizedFunctionalWorkflowConfig
    fit: GeneralizedFunctionOnScalarResult
    steps: tuple[WorkflowStepRecord, ...]
    decisions: Mapping[str, WorkflowDecisionRecord]
    provenance: Mapping[str, object]
    reports: Mapping[str, str]
    tables: Mapping[str, pd.DataFrame]


def run_generalized_functional_workflow(
    trajectories: TrajectorySet,
    design: pd.DataFrame,
    *,
    config: GeneralizedFunctionalWorkflowConfig,
) -> GeneralizedFunctionalWorkflowResult:
    """Run a marginal generalized functional model with explicit semantics."""

    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("trajectories must be a TrajectorySet")
    if not isinstance(design, pd.DataFrame):
        raise TypeError("design must be a pandas DataFrame")
    if not isinstance(config, GeneralizedFunctionalWorkflowConfig):
        raise TypeError("config must be a GeneralizedFunctionalWorkflowConfig")
    contract = "generalized_functional:v1"
    _require_empty_preprocessing(config.preprocessing, workflow_contract=contract)

    parameters = {
        "predictors": config.predictors,
        "participant_column": config.participant_column,
        "dimension": config.dimension,
        "family": config.family,
        "binomial_denominator": config.binomial_denominator,
        "exposure": config.exposure,
        "exposure_units": config.exposure_units,
        "basis_size": config.basis_size,
        "spline_degree": config.spline_degree,
        "working_correlation": config.working_correlation,
        "covariance_type": config.covariance_type,
        "maxiter": config.maxiter,
        "ctol": config.ctol,
    }
    fit, step = timed_step(
        name="fit",
        function="fit_generalized_function_on_scalar_regression",
        parameters=parameters,
        call=lambda: fit_generalized_function_on_scalar_regression(
            trajectories,
            design,
            config.predictors,
            participant_column=config.participant_column,
            dimension=config.dimension,
            family=config.family,
            binomial_denominator=config.binomial_denominator,
            exposure=config.exposure,
            exposure_units=config.exposure_units,
            basis_size=config.basis_size,
            spline_degree=config.spline_degree,
            working_correlation=config.working_correlation,
            covariance_type=config.covariance_type,
            maxiter=config.maxiter,
            ctol=config.ctol,
        ),
    )
    decisions = {
        "predictors": WorkflowDecisionRecord(
            value=config.predictors,
            source="analyst",
        ),
        "participant_column": WorkflowDecisionRecord(
            value=config.participant_column,
            source="analyst",
        ),
        "dimension": WorkflowDecisionRecord(
            value=config.dimension,
            source="analyst",
        ),
        "family": WorkflowDecisionRecord(
            value=config.family,
            source="analyst",
        ),
        "binomial_denominator_supplied": WorkflowDecisionRecord(
            value=config.binomial_denominator is not None,
            source="analyst",
        ),
        "exposure_supplied": WorkflowDecisionRecord(
            value=config.exposure is not None,
            source="analyst",
        ),
        "exposure_units": WorkflowDecisionRecord(
            value=config.exposure_units,
            source="analyst",
        ),
        "basis_size": WorkflowDecisionRecord(
            value=config.basis_size,
            source="analyst",
        ),
        "spline_degree": WorkflowDecisionRecord(
            value=config.spline_degree,
            source="analyst",
        ),
        "working_correlation": WorkflowDecisionRecord(
            value=config.working_correlation,
            source="analyst",
        ),
        "covariance_type": WorkflowDecisionRecord(
            value=config.covariance_type,
            source="analyst",
        ),
    }
    return GeneralizedFunctionalWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract=contract,
        config=config,
        fit=fit,
        steps=(step,),
        decisions=decisions,
        provenance={
            "input_layout": "complete_common_grid",
            "preprocessing_executed": False,
            "automatic_family_selection": False,
            "binomial_denominator_inferred": False,
            "poisson_exposure_inferred": False,
            "automatic_working_correlation_selection": False,
            "automatic_model_selection_performed": False,
        },
        reports={"fit": generalized_function_on_scalar_reporting_text(fit)},
        tables={
            "coefficients": generalized_function_on_scalar_coefficient_frame(fit),
        },
    )
