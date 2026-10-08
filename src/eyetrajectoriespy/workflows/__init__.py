"""Transparent workflow orchestration namespace.

The 1.2 workflow layer remains module-scoped during qualification.
W1 provides the shared contracts; W2-W4 compose already-qualified scientific APIs.
"""

from ._core import (
    PreprocessingPlan,
    PreprocessingStepConfig,
    WORKFLOW_BUNDLE_FORMAT,
    WORKFLOW_BUNDLE_SCHEMA_VERSION,
    WORKFLOW_SCHEMA_VERSION,
    WorkflowDecisionRecord,
    WorkflowStepRecord,
    export_workflow_bundle,
    workflow_config_to_dict,
    workflow_decisions_frame,
    workflow_reporting_text,
    workflow_steps_frame,
    workflow_summary_frame,
)
from ._sparse_shared import (
    ObservationDiagnosticConfig,
    ScoreUncertaintyConfig,
)
from ._sparse_fpca import (
    SparseFPCABandwidthSelectionConfig,
    SparseFPCAWorkflowConfig,
    SparseFPCAWorkflowResult,
    run_sparse_fpca_workflow,
)
from ._sparse_mfpca import (
    SparseMFPCABandwidthSelectionConfig,
    SparseMFPCAWorkflowConfig,
    SparseMFPCAWorkflowResult,
    run_sparse_mfpca_workflow,
)
from ._sparse_async import (
    SparseMFPCAAsyncWorkflowConfig,
    SparseMFPCAAsyncWorkflowResult,
    run_sparse_mfpca_async_workflow,
)
from ._sparse_multilevel import (
    SparseMultilevelWorkflowConfig,
    SparseMultilevelWorkflowResult,
    run_sparse_multilevel_workflow,
)
from ._sparse_prediction import (
    SparsePredictionWorkflowConfig,
    SparsePredictionWorkflowResult,
    run_sparse_prediction_workflow,
)
from ._dense_regression import (
    FPCAWorkflowConfig,
    FPCAWorkflowResult,
    FunctionOnScalarWorkflowConfig,
    FunctionOnScalarWorkflowResult,
    FunctionalMixedEffectsWorkflowConfig,
    FunctionalMixedEffectsWorkflowResult,
    GeneralizedFunctionalWorkflowConfig,
    GeneralizedFunctionalWorkflowResult,
    run_fpca_workflow,
    run_function_on_scalar_workflow,
    run_functional_mixed_effects_workflow,
    run_generalized_functional_workflow,
)
from ._recurrence import (
    RecurrenceWorkflowConfig,
    RecurrenceWorkflowResult,
    run_recurrence_workflow,
)
from ._plotting import (
    SUPPORTED_WORKFLOW_PLOTS,
    plot_workflow_result,
    save_workflow_figure,
)

__all__ = [
    "FPCAWorkflowConfig",
    "FPCAWorkflowResult",
    "FunctionOnScalarWorkflowConfig",
    "FunctionOnScalarWorkflowResult",
    "FunctionalMixedEffectsWorkflowConfig",
    "FunctionalMixedEffectsWorkflowResult",
    "GeneralizedFunctionalWorkflowConfig",
    "GeneralizedFunctionalWorkflowResult",
    "RecurrenceWorkflowConfig",
    "RecurrenceWorkflowResult",
    "SUPPORTED_WORKFLOW_PLOTS",
    "ObservationDiagnosticConfig",
    "PreprocessingPlan",
    "PreprocessingStepConfig",
    "ScoreUncertaintyConfig",
    "SparseFPCABandwidthSelectionConfig",
    "SparseFPCAWorkflowConfig",
    "SparseFPCAWorkflowResult",
    "SparseMFPCABandwidthSelectionConfig",
    "SparseMFPCAAsyncWorkflowConfig",
    "SparseMFPCAAsyncWorkflowResult",
    "SparseMFPCAWorkflowConfig",
    "SparseMFPCAWorkflowResult",
    "SparseMultilevelWorkflowConfig",
    "SparseMultilevelWorkflowResult",
    "SparsePredictionWorkflowConfig",
    "SparsePredictionWorkflowResult",
    "WORKFLOW_BUNDLE_FORMAT",
    "WORKFLOW_BUNDLE_SCHEMA_VERSION",
    "WORKFLOW_SCHEMA_VERSION",
    "WorkflowDecisionRecord",
    "WorkflowStepRecord",
    "export_workflow_bundle",
    "run_fpca_workflow",
    "run_function_on_scalar_workflow",
    "run_functional_mixed_effects_workflow",
    "run_generalized_functional_workflow",
    "run_recurrence_workflow",
    "plot_workflow_result",
    "save_workflow_figure",
    "run_sparse_fpca_workflow",
    "run_sparse_mfpca_async_workflow",
    "run_sparse_mfpca_workflow",
    "run_sparse_multilevel_workflow",
    "run_sparse_prediction_workflow",
    "workflow_config_to_dict",
    "workflow_decisions_frame",
    "workflow_reporting_text",
    "workflow_steps_frame",
    "workflow_summary_frame",
]
