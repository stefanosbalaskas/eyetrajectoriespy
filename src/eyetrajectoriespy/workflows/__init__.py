"""Transparent, module-scoped analysis workflow infrastructure.

Workflow APIs intentionally live under :mod:`eyetrajectoriespy.workflows`
instead of expanding the frozen package-root 1.x compatibility boundary.
"""

from ._bundle import (
    WORKFLOW_BUNDLE_FORMAT,
    WORKFLOW_BUNDLE_SCHEMA_VERSION,
    WorkflowBundleSnapshot,
    export_workflow_bundle,
    load_workflow_bundle,
)
from ._core import (
    WORKFLOW_SCHEMA_VERSION,
    PreprocessingPlan,
    PreprocessingStepConfig,
    WorkflowContract,
    WorkflowDecision,
    WorkflowDiagnosticConfig,
    WorkflowDiagnosticsPlan,
    WorkflowResultBase,
    WorkflowStepRecord,
    workflow_config_dict,
    workflow_provenance_dict,
    workflow_steps_frame,
)


__all__ = [
    "WORKFLOW_SCHEMA_VERSION",
    "WORKFLOW_BUNDLE_SCHEMA_VERSION",
    "WORKFLOW_BUNDLE_FORMAT",
    "WorkflowContract",
    "WorkflowDecision",
    "WorkflowDiagnosticConfig",
    "WorkflowDiagnosticsPlan",
    "WorkflowStepRecord",
    "WorkflowResultBase",
    "PreprocessingStepConfig",
    "PreprocessingPlan",
    "WorkflowBundleSnapshot",
    "workflow_config_dict",
    "workflow_provenance_dict",
    "workflow_steps_frame",
    "export_workflow_bundle",
    "load_workflow_bundle",
]
