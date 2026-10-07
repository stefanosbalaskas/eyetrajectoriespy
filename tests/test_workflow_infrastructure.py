from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy.workflows import (
    PreprocessingPlan,
    PreprocessingStepConfig,
    WORKFLOW_BUNDLE_FORMAT,
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


@dataclass(frozen=True)
class DemoConfig:
    n_components: int
    grid: np.ndarray
    preprocessing: PreprocessingPlan


@dataclass(frozen=True)
class DemoResult:
    workflow_schema_version: int
    workflow_contract: str
    config: DemoConfig
    steps: tuple[WorkflowStepRecord, ...]
    decisions: dict[str, WorkflowDecisionRecord]
    provenance: dict[str, object]
    reports: dict[str, str]
    tables: dict[str, pd.DataFrame]


def _result():
    config = DemoConfig(
        n_components=2,
        grid=np.array([0.0, 0.5, 1.0]),
        preprocessing=PreprocessingPlan(
            steps=(
                PreprocessingStepConfig(
                    function="normalize_coordinates",
                    parameters={"method": "screen_fraction"},
                    scientific_effect="changes coordinate scale only",
                ),
            )
        ),
    )
    steps = (
        WorkflowStepRecord(
            name="preprocess",
            function="normalize_coordinates",
            status="completed",
            parameters={"method": "screen_fraction"},
            elapsed_seconds=0.01,
        ),
        WorkflowStepRecord(
            name="fit",
            function="fit_sparse_fpca",
            status="completed",
            parameters={"n_components": 2},
            elapsed_seconds=0.02,
            warnings=("example warning",),
        ),
    )
    decisions = {
        "n_components": WorkflowDecisionRecord(
            value=2,
            source="analyst",
        ),
        "mean_bandwidth": WorkflowDecisionRecord(
            value=0.36,
            source="audited_selector",
            criterion="grouped_cv",
        ),
    }
    return DemoResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract="demo:v1",
        config=config,
        steps=steps,
        decisions=decisions,
        provenance={"raw_interpolation": False},
        reports={"methods": "A transparent demo workflow."},
        tables={"scores": pd.DataFrame({"score": [0.1, -0.2]})},
    )


def test_preprocessing_plan_is_empty_by_default_and_ordered_when_declared():
    empty = PreprocessingPlan()
    assert empty.steps == ()

    first = PreprocessingStepConfig(
        function="smooth_trajectories",
        parameters={"window": 5},
        scientific_effect="changes local signal roughness",
    )
    second = PreprocessingStepConfig(
        function="normalize_coordinates",
        parameters={"method": "screen_fraction"},
        scientific_effect="changes coordinate scale",
    )
    plan = PreprocessingPlan(steps=(first, second))
    assert tuple(step.function for step in plan.steps) == (
        "smooth_trajectories",
        "normalize_coordinates",
    )


def test_audited_selector_decision_requires_criterion():
    with pytest.raises(ValueError, match="criterion"):
        WorkflowDecisionRecord(
            value=0.36,
            source="audited_selector",
        )


def test_step_record_is_fail_closed_on_status_and_time():
    with pytest.raises(ValueError, match="status"):
        WorkflowStepRecord(
            name="fit",
            function="fit_sparse_fpca",
            status="mystery",
            parameters={},
            elapsed_seconds=0.1,
        )
    with pytest.raises(ValueError, match="elapsed_seconds"):
        WorkflowStepRecord(
            name="fit",
            function="fit_sparse_fpca",
            status="completed",
            parameters={},
            elapsed_seconds=-0.1,
        )


def test_config_serialization_is_strict_and_preserves_ordered_plan():
    payload = workflow_config_to_dict(_result().config)

    assert payload["n_components"] == 2
    assert payload["grid"] == [0.0, 0.5, 1.0]
    assert payload["preprocessing"]["steps"][0]["function"] == (
        "normalize_coordinates"
    )


def test_frames_and_reporting_retain_decision_sources():
    result = _result()
    steps = workflow_steps_frame(result.steps)
    decisions = workflow_decisions_frame(result.decisions)
    text = workflow_reporting_text(result)
    summary = workflow_summary_frame(result)

    assert steps["order"].tolist() == [1, 2]
    assert decisions.set_index("name").loc["mean_bandwidth", "source"] == (
        "audited_selector"
    )
    assert "demo:v1" in text
    assert "analyst-declared" in text
    assert "audited selectors" in text
    assert summary.loc[0, "workflow_contract"] == "demo:v1"
    assert summary.loc[0, "step_count"] == 2
    assert summary.loc[0, "warning_count"] == 1
    assert summary.loc[0, "analyst_decisions"] == 1
    assert summary.loc[0, "audited_selector_decisions"] == 1


def test_workflow_bundle_is_complete_and_checksummed(tmp_path):
    destination = export_workflow_bundle(
        _result(),
        tmp_path / "bundle",
    )

    required = {
        "workflow.json",
        "config.json",
        "provenance.json",
        "environment.json",
        "steps.csv",
        "decisions.csv",
        "SHA256SUMS",
        "reports/methods.txt",
        "tables/scores.csv",
        "result/manifest.json",
        "result/arrays.npz",
    }
    files = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    assert required <= files

    manifest = json.loads(
        (destination / "workflow.json").read_text(encoding="utf-8")
    )
    assert manifest["format"] == WORKFLOW_BUNDLE_FORMAT
    assert manifest["workflow_schema_version"] == WORKFLOW_SCHEMA_VERSION
    assert manifest["workflow_contract"] == "demo:v1"
    assert manifest["figure_export_included"] is False

    checksums = (destination / "SHA256SUMS").read_text(encoding="utf-8")
    assert "config.json" in checksums
    assert "result/arrays.npz" in checksums
    assert "SHA256SUMS" not in checksums


def test_bundle_rejects_non_dataclass_result(tmp_path):
    with pytest.raises(TypeError, match="dataclass"):
        export_workflow_bundle(
            {"workflow_contract": "invalid"},
            tmp_path / "bundle",
        )


def test_w1_remains_module_scoped_not_root_exported():
    import eyetrajectoriespy as et

    for name in (
        "WorkflowDecisionRecord",
        "WorkflowStepRecord",
        "PreprocessingPlan",
        "PreprocessingStepConfig",
        "export_workflow_bundle",
        "workflow_summary_frame",
    ):
        assert not hasattr(et, name)
