"""Experimental E1–E4 development surface: not in frozen RC1 public export audit.

These APIs are candidate research utilities, not 1.1 stable features or
qualified 1.2.0rc1 interfaces. Separate RC2 evidence must precede promotion.
"""

from ._exp_preprocessing import PreprocessingExecutionResult, run_preprocessing_plan, run_workflow_preprocessed
from ._exp_preflight import WorkflowPreflightResult, workflow_preflight, plot_workflow_preflight
from ._exp_reporting import WorkflowReportArtifact, render_workflow_report
from ._exp_sensitivity import (
    WorkflowSensitivityResult, WorkflowSpecification,
    run_workflow_sensitivity, plot_workflow_sensitivity,
)

__all__ = [
    "PreprocessingExecutionResult", "WorkflowPreflightResult", "WorkflowReportArtifact", "render_workflow_report",
    "WorkflowSensitivityResult", "WorkflowSpecification",
    "run_preprocessing_plan", "run_workflow_preprocessed",
    "workflow_preflight", "plot_workflow_preflight", "run_workflow_sensitivity", "plot_workflow_sensitivity",
]
