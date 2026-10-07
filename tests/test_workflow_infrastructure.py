from dataclasses import dataclass
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import eyetrajectoriespy as et
from eyetrajectoriespy.workflows import (
    WORKFLOW_BUNDLE_FORMAT,
    WORKFLOW_BUNDLE_SCHEMA_VERSION,
    WORKFLOW_SCHEMA_VERSION,
    PreprocessingPlan,
    PreprocessingStepConfig,
    WorkflowContract,
    WorkflowDecision,
    WorkflowStepRecord,
    export_workflow_bundle,
    load_workflow_bundle,
    workflow_config_dict,
    workflow_provenance_dict,
    workflow_steps_frame,
)


@dataclass(frozen=True)
class _DummyConfig:
    evaluation_grid: np.ndarray
    n_components: int
    preprocessing: PreprocessingPlan


@dataclass(frozen=True)
class _DummyWorkflowResult:
    workflow_schema_version: int
    workflow_contract: str
    config: _DummyConfig
    steps: tuple[WorkflowStepRecord, ...]
    provenance: dict[str, object]
    values: np.ndarray


def _dummy_result() -> _DummyWorkflowResult:
    return _DummyWorkflowResult(
        workflow_schema_version=WORKFLOW_SCHEMA_VERSION,
        workflow_contract="dummy:v1",
        config=_DummyConfig(
            evaluation_grid=np.linspace(0.0, 1.0, 5),
            n_components=2,
            preprocessing=PreprocessingPlan(
                steps=(
                    PreprocessingStepConfig(
                        operation="normalize_coordinates",
                        parameters={"mode": "unit_square"},
                    ),
                )
            ),
        ),
        steps=(
            WorkflowStepRecord(
                name="validate representation",
                function="validate_trajectory_set",
                status="ok",
                parameters={"require_complete": True},
                elapsed_seconds=0.01,
            ),
            WorkflowStepRecord(
                name="fit",
                function="fit_fpca",
                status="ok",
                parameters={"n_components": 2},
                elapsed_seconds=0.05,
                warnings=("synthetic test warning",),
            ),
        ),
        provenance={
            "decisions": {
                "n_components": WorkflowDecision(
                    value=2,
                    source="analyst",
                ),
                "mean_bandwidth": WorkflowDecision(
                    value=0.3,
                    source="select_sparse_fpca_bandwidths",
                    criterion="grouped_cv",
                ),
            },
            "automatic_method_selection": False,
        },
        values=np.array([1.0, 2.0]),
    )


def test_workflow_contract_has_versioned_identifier():
    contract = WorkflowContract(
        name="sparse_fpca",
        version=1,
        scientific_scope="Sparse FPCA composition",
        prohibitions=("no hidden bandwidth selection",),
    )

    assert contract.identifier == "sparse_fpca:v1"
    assert contract.version == 1
    assert contract.prohibitions == ("no hidden bandwidth selection",)


@pytest.mark.parametrize(
    ("name", "version"),
    [
        ("SparseFPCA", 1),
        ("sparse-fpca", 1),
        ("", 1),
        ("sparse_fpca", 0),
        ("sparse_fpca", True),
    ],
)
def test_workflow_contract_rejects_invalid_identity(name, version):
    error = TypeError if isinstance(version, bool) else ValueError
    with pytest.raises(error):
        WorkflowContract(name=name, version=version)


def test_decision_provenance_retains_value_source_and_criterion():
    decision = WorkflowDecision(
        value=0.36,
        source="select_sparse_fpca_bandwidths",
        criterion="participant_grouped_cv",
        details={"candidate_id": "candidate_0003"},
    )

    assert decision.value == pytest.approx(0.36)
    assert decision.source == "select_sparse_fpca_bandwidths"
    assert decision.criterion == "participant_grouped_cv"
    assert decision.details["candidate_id"] == "candidate_0003"
    with pytest.raises(TypeError):
        decision.details["candidate_id"] = "changed"


def test_preprocessing_plan_is_explicit_and_ordered():
    plan = PreprocessingPlan(
        steps=(
            PreprocessingStepConfig(
                "smooth_trajectories",
                {"window": 5},
            ),
            PreprocessingStepConfig(
                "normalize_coordinates",
                {"mode": "unit_square"},
            ),
        )
    )

    assert tuple(step.operation for step in plan.steps) == (
        "smooth_trajectories",
        "normalize_coordinates",
    )
    assert PreprocessingPlan().steps == ()


def test_workflow_step_record_validates_status_and_elapsed_time():
    with pytest.raises(ValueError, match="status"):
        WorkflowStepRecord(
            name="fit",
            function="fit_fpca",
            status="running",
        )
    with pytest.raises(ValueError, match="elapsed_seconds"):
        WorkflowStepRecord(
            name="fit",
            function="fit_fpca",
            status="ok",
            elapsed_seconds=-1.0,
        )


def test_config_and_provenance_serialization_are_json_safe():
    result = _dummy_result()

    config = workflow_config_dict(result.config)
    provenance = workflow_provenance_dict(result.provenance)

    assert config["evaluation_grid"] == pytest.approx(
        np.linspace(0.0, 1.0, 5).tolist()
    )
    assert config["preprocessing"]["steps"][0]["operation"] == (
        "normalize_coordinates"
    )
    assert provenance["decisions"]["n_components"]["source"] == "analyst"
    assert provenance["decisions"]["mean_bandwidth"]["criterion"] == (
        "grouped_cv"
    )
    json.dumps(config, allow_nan=False)
    json.dumps(provenance, allow_nan=False)


def test_config_serialization_rejects_nonfinite_or_opaque_values():
    @dataclass(frozen=True)
    class BadFloat:
        value: float

    @dataclass(frozen=True)
    class BadObject:
        value: object

    with pytest.raises(ValueError, match="non-finite"):
        workflow_config_dict(BadFloat(float("nan")))
    with pytest.raises(TypeError, match="unsupported"):
        workflow_config_dict(BadObject(object()))


def test_workflow_steps_frame_preserves_declared_order():
    result = _dummy_result()

    frame = workflow_steps_frame(result.steps)

    assert frame["step_index"].tolist() == [1, 2]
    assert frame["function"].tolist() == [
        "validate_trajectory_set",
        "fit_fpca",
    ]
    assert frame["n_warnings"].tolist() == [0, 1]


def test_workflow_api_is_module_scoped_not_root_exported():
    for name in (
        "WorkflowContract",
        "WorkflowDecision",
        "WorkflowStepRecord",
        "PreprocessingPlan",
        "export_workflow_bundle",
        "load_workflow_bundle",
    ):
        assert name not in et.__all__
        assert not hasattr(et, name)


def test_export_and_load_workflow_bundle_round_trip(tmp_path):
    result = _dummy_result()
    figure, axis = plt.subplots()
    axis.plot([0.0, 1.0], [0.0, 1.0])

    destination = tmp_path / "workflow-bundle"
    try:
        exported = export_workflow_bundle(
            result,
            destination,
            tables={
                "scores": pd.DataFrame(
                    {"curve_id": ["a", "b"], "score": [0.2, -0.2]}
                )
            },
            reports={"methods": "Explicit synthetic workflow."},
            figures={"overview": axis},
        )
    finally:
        plt.close(figure)

    assert exported == destination
    for relative in (
        "workflow.json",
        "config.json",
        "provenance.json",
        "steps.json",
        "environment.json",
        "results/workflow-result/manifest.json",
        "results/workflow-result/arrays.npz",
        "tables/scores.csv",
        "reports/methods.txt",
        "figures/overview.png",
        "SHA256SUMS",
    ):
        assert (destination / relative).is_file()

    snapshot = load_workflow_bundle(destination)
    assert snapshot.workflow_schema_version == WORKFLOW_SCHEMA_VERSION
    assert snapshot.workflow_contract == "dummy:v1"
    assert snapshot.manifest["format"] == WORKFLOW_BUNDLE_FORMAT
    assert (
        snapshot.manifest["schema_version"]
        == WORKFLOW_BUNDLE_SCHEMA_VERSION
    )
    assert snapshot.config["n_components"] == 2
    assert snapshot.provenance["automatic_method_selection"] is False
    assert len(snapshot.steps) == 2
    assert snapshot.environment is not None
    assert snapshot.result.result_type.endswith("._DummyWorkflowResult")
    assert snapshot.tables == ("scores.csv",)
    assert snapshot.reports == ("methods.txt",)
    assert snapshot.figures == ("overview.png",)


def test_workflow_bundle_can_omit_environment(tmp_path):
    destination = export_workflow_bundle(
        _dummy_result(),
        tmp_path / "without-environment",
        include_environment=False,
    )

    assert not (destination / "environment.json").exists()
    snapshot = load_workflow_bundle(destination)
    assert snapshot.environment is None


def test_workflow_bundle_detects_tampering(tmp_path):
    destination = export_workflow_bundle(
        _dummy_result(),
        tmp_path / "tampered",
        reports={"results": "original"},
    )
    (destination / "reports" / "results.txt").write_text(
        "tampered",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_workflow_bundle(destination)


def test_workflow_bundle_rejects_unsafe_export_names(tmp_path):
    with pytest.raises(ValueError, match="table names"):
        export_workflow_bundle(
            _dummy_result(),
            tmp_path / "unsafe",
            tables={"../scores": pd.DataFrame({"x": [1]})},
        )


def test_workflow_bundle_rejects_nonstring_export_names_before_sorting(tmp_path):
    with pytest.raises(ValueError, match="report names"):
        export_workflow_bundle(
            _dummy_result(),
            tmp_path / "bad-report-name",
            reports={1: "not allowed"},
        )


def test_workflow_bundle_rejects_checksum_path_traversal(tmp_path):
    destination = export_workflow_bundle(
        _dummy_result(),
        tmp_path / "path-traversal",
    )
    checksum = destination / "SHA256SUMS"
    checksum.write_text(
        checksum.read_text(encoding="utf-8")
        + ("0" * 64)
        + "  ../outside.txt\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsafe workflow bundle checksum path"):
        load_workflow_bundle(destination)


def test_workflow_bundle_rejects_nonempty_destination(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not empty"):
        export_workflow_bundle(_dummy_result(), destination)


def test_workflow_bundle_requires_explicit_workflow_result_contract(tmp_path):
    @dataclass(frozen=True)
    class NotAWorkflow:
        value: int

    with pytest.raises(
        (TypeError, ValueError),
        match="workflow",
    ):
        export_workflow_bundle(
            NotAWorkflow(1),
            tmp_path / "not-workflow",
        )
