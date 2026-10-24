"""E5 development boundary guard; does not authorize RC2 publication."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
import inspect
from pathlib import Path
import tomllib

from eyetrajectoriespy import __version__
from eyetrajectoriespy import workflows
from eyetrajectoriespy.workflows import experimental

ROOT = Path(__file__).resolve().parents[1]
DEV = "1.2.0"
HISTORICAL_RC2 = "1.2.0rc2"
RC1 = "1.2.0rc1"
EXPECTED_EXPERIMENTAL = {
    "PreprocessingExecutionResult", "WorkflowPreflightResult",
    "WorkflowReportArtifact", "WorkflowSensitivityResult", "WorkflowSpecification",
    "run_preprocessing_plan", "run_workflow_preprocessed", "workflow_preflight",
    "run_workflow_sensitivity", "plot_workflow_sensitivity", "render_workflow_report",
    "plot_workflow_preflight",
}


def main() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        source_version = tomllib.load(stream)["project"]["version"]
    assert source_version == DEV == __version__
    readiness = json.loads((ROOT / "RELEASE_READINESS.json").read_text())
    frozen = json.loads((ROOT / "WORKFLOW_API_AUDIT.json").read_text())
    rc1 = json.loads((ROOT / "ONE_DOT_TWO_RC_QUALIFICATION.json").read_text())
    development = json.loads((ROOT / "EXPERIMENTAL_WORKFLOW_AUDIT.json").read_text())
    assert readiness["current_development_version"] == DEV
    # The RC2 authorization is archived; it must not arm a distinct final release.
    assert readiness["production_release_ready"] is readiness["github_release_ready"] is False
    approval = json.loads((ROOT / "FINAL_1_2_PUBLICATION_APPROVAL.json").read_text())
    assert approval["approval_state"] == "separately_authorized_stable_publication"
    assert approval["owner_production_publication_approved"] is True
    assert approval["published_final_version"] is True
    assert approval["production_workflow_run_id"] == 40128358042
    assert approval["root_api_promotion"] is False
    assert approval["experimental_helpers_stable_promotion"] is False
    historic_readiness = json.loads((ROOT / "validation/RELEASE_READINESS-1.2.0rc2.json").read_text())
    assert historic_readiness["production_release_ready"] is historic_readiness["github_release_ready"] is True
    if historic_readiness["production_release_ready"]:
        review = json.loads((ROOT / "RC2_PUBLICATION_REVIEW.json").read_text())
        assert review["record_kind"] == "owner_authorized_pending_independent_review"
        assert review["independent_human_release_review_recorded"] is False
        assert review["independent_exact_head_github_review_enforced_in_workflow"] is True
    assert rc1["package_version"] == RC1
    assert rc1["scientific_behavior_changed"] is False
    assert rc1["publication_interlock"]["publication_arming_performed"] is False
    assert frozen["root_exports_promoted"] is False
    assert set(workflows.__all__) == set(frozen["exported_symbols"])
    assert set(experimental.__all__) == EXPECTED_EXPERIMENTAL
    assert set(experimental.__all__).isdisjoint(set(workflows.__all__))
    assert development["source_version"] == HISTORICAL_RC2
    assert development["previous_qualified_candidate"] == RC1
    assert development["candidate_publication_authorized"] is False
    assert development["candidate_scientifically_qualified"] is False
    assert development["candidate_exact_main_qualified"] is False
    assert development["native_bayesian_estimator_added"] is False
    assert development["new_effect_region_inference_added"] is False
    proposed = json.loads((ROOT / "EXPERIMENTAL_WORKFLOW_API_AUDIT.json").read_text())
    assert proposed["branch_version"] == HISTORICAL_RC2
    assert proposed["publication_authorized"] is False
    assert proposed["root_namespace_promoted"] is False
    assert proposed["status"] == "frozen_proposed_api_for_scientific_review"
    assert set(proposed["exported_symbols"]) == EXPECTED_EXPERIMENTAL
    for name, parameters in proposed["callable_parameters"].items():
        fn = getattr(experimental, name)
        assert list(inspect.signature(fn).parameters) == parameters, name
    for name, names in proposed["dataclass_fields"].items():
        cls = getattr(experimental, name)
        assert is_dataclass(cls)
        assert [field.name for field in fields(cls)] == names, name
    print("PASS historical RC2/E1-E4 boundary preserved; stable 1.2.0 published and production flags disarmed")


if __name__ == "__main__":
    main()
