"""E5 development boundary guard; does not authorize RC2 promotion."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib

from eyetrajectoriespy import __version__
from eyetrajectoriespy import workflows
from eyetrajectoriespy.workflows import experimental

ROOT = Path(__file__).resolve().parents[1]
DEV = "1.2.0rc2.dev0"
RC1 = "1.2.0rc1"
EXPECTED_EXPERIMENTAL = {
    "PreprocessingExecutionResult", "WorkflowPreflightResult",
    "WorkflowReportArtifact", "WorkflowSensitivityResult", "WorkflowSpecification",
    "run_preprocessing_plan", "run_workflow_preprocessed", "workflow_preflight",
    "run_workflow_sensitivity", "plot_workflow_sensitivity", "render_workflow_report",
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
    assert not readiness["production_release_ready"] and not readiness["github_release_ready"]
    assert rc1["package_version"] == RC1
    assert rc1["scientific_behavior_changed"] is False
    assert rc1["publication_interlock"]["publication_arming_performed"] is False
    assert frozen["root_exports_promoted"] is False
    assert len(frozen["exported_symbols"]) == 49
    assert set(workflows.__all__) == set(frozen["exported_symbols"])
    assert set(experimental.__all__) == EXPECTED_EXPERIMENTAL
    assert set(experimental.__all__).isdisjoint(set(workflows.__all__))
    assert development["source_version"] == DEV
    assert development["previous_qualified_candidate"] == RC1
    assert development["candidate_publication_authorized"] is False
    assert development["candidate_scientifically_qualified"] is False
    assert development["candidate_exact_main_qualified"] is False
    assert development["native_bayesian_estimator_added"] is False
    assert development["new_effect_region_inference_added"] is False
    print("PASS E5 development boundaries: RC1 immutable, 11 experimental exports, RC2 not qualified")


if __name__ == "__main__":
    main()
