"""Nonpublishing validator for a REVIEW-ONLY 1.2 candidate engineering scope.

This script cannot qualify statistical methods, authorize publication, change
package version declarations, or approve an actual release. It fails closed on
promotions, undeclared workflows, disarmed-flag drift and missing claim holds.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CLAIM_HOLDS = {
    "nominal_90_percent_simultaneous_functional_band_coverage",
    "validated_CR2_fitted_covariance_random_slope_inference",
    "MNAR_gaze_loss_identification_from_observed_data",
    "automatic_reconstruction_of_unreturned_gaze",
    "algorithmic_recovery_of_missing_outcomes_by_random_audit_assignment_alone",
}
REQUIRED_OPEN_BLOCKERS = {289,296}
EXPECTED_SOURCE_VERSION = "1.2.0rc2.dev0"


def load_json(name: str) -> dict:
    data=json.loads((ROOT/name).read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise RuntimeError(f"Invalid source JSON object: {name}")
    return data


def validate_scope(*, scope: dict, readiness: dict, audit: dict, frozen: dict) -> dict:
    if scope.get("schema_version") != 1 or scope.get("document_type") != "unapproved_release_scope_proposal":
        raise RuntimeError("release scope must remain an unapproved draft proposal")
    if (scope.get("source_version") != EXPECTED_SOURCE_VERSION
        or readiness.get("current_development_version") != EXPECTED_SOURCE_VERSION):
        raise RuntimeError("release scope/source identity differs from frozen development source")
    if scope.get("published_stable_baseline") != "1.1.0":
        raise RuntimeError("1.1 published stable baseline cannot be relabelled")
    frozen_counts=frozen.get("counts",{})
    boundary=scope.get("frozen_root_compatibility",{})
    for source_field,target_field in (
        ("public_exports","original_public_exports"),
        ("stable_exports","stable_exports"),
        ("experimental_exports","experimental_exports"),
    ):
        if boundary.get(target_field)!=frozen_counts.get(source_field):
            raise RuntimeError("frozen 1.0 public root API counts were relabelled")
    if boundary.get("root_promotion_authorized") is not False or boundary.get("removals_authorized") is not False:
        raise RuntimeError("release scope attempted root promotion or breaking removal")
    if (audit.get("boundary_state")!="module_scoped_stable_candidate"
        or audit.get("root_exports_promoted") is not False
        or scope.get("workflow_namespace")!=audit.get("public_module")):
        raise RuntimeError("module-scoped workflow API contract changed")
    if scope.get("workflow_status")!="module_scoped_stable_candidate_unpublished":
        raise RuntimeError("candidate scientific workflows were improperly promoted")
    routes=scope.get("candidate_workflows")
    if not isinstance(routes,list) or len(routes)!=10:
        raise RuntimeError("release scope must declare exactly ten current workflow candidates")
    names=[r.get("entry_point") for r in routes]
    contracts=[r.get("contract") for r in routes]
    if names != audit.get("workflow_entry_points") or contracts != audit.get("workflow_contracts"):
        raise RuntimeError("candidate workflow names/contracts drifted from frozen public audit")
    for record in routes:
        if (record.get("engineering_status")!="installed_candidate_passed"
            or not isinstance(record.get("description"),str)
            or not record["description"].strip()
            or not isinstance(record.get("interpretation_limit"),str)
            or not record["interpretation_limit"].strip()):
            raise RuntimeError("candidate route missing engineering or scientific limitation")
    if set(scope.get("scientific_blockers_open",()))!=REQUIRED_OPEN_BLOCKERS:
        raise RuntimeError("scientific blockers #289/#296 must remain visible and open")
    if not REQUIRED_CLAIM_HOLDS<=set(scope.get("disallowed_new_claims",())):
        raise RuntimeError("scientific inferential/MNAR claim holds missing")
    experimental=scope.get("bundled_unqualified_experimental_module")
    if not isinstance(experimental,dict):
        raise RuntimeError("1.2 release scope ignores bundled experimental E1-E4 module")
    if (experimental.get("module")!="eyetrajectoriespy.workflows.experimental"
        or experimental.get("source_file")!="src/eyetrajectoriespy/workflows/experimental.py"
        or experimental.get("published_in_current_stable_1_1") is not False
        or experimental.get("bundled_in_dev_wheel") is not True
        or experimental.get("supported_in_proposed_ten_workflow_api") is not False
        or experimental.get("public_contract_frozen") is not False
        or experimental.get("eligible_for_literal_1_2_release_without_separate_e5_review") is not False):
        raise RuntimeError("bundled experimental E1-E4 release-content boundary was promoted")
    import ast
    source_path=ROOT/experimental["source_file"]
    tree=ast.parse(source_path.read_text(encoding="utf-8"))
    module_exports=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="__all__" for t in node.targets
        ):
            module_exports=ast.literal_eval(node.value)
            break
    if module_exports is None or list(module_exports)!=experimental.get("named_experimental_helpers"):
        raise RuntimeError("importable experimental helper surface differs from frozen draft manifest")
    if not isinstance(experimental.get("required_decision"),str) or len(experimental["required_decision"])<35:
        raise RuntimeError("bundled experimental module requires an explicit release-content decision")
    if scope.get("scope_decision")!="engineering_candidate_only_not_release_authorization":
        raise RuntimeError("candidate scope claimed release authorization")
    evidence=scope.get("last_completed_evidence",{})
    if (evidence.get("qualification_pr")!=467
        or evidence.get("exact_head_workflows_successful")!=27
        or evidence.get("installed_python_versions")!=["3.11","3.12","3.13"]
        or evidence.get("candidate_installed_routes")!=10):
        raise RuntimeError("verified engineering qualification evidence changed")
    if readiness.get("production_release_ready") is not False or readiness.get("github_release_ready") is not False:
        raise RuntimeError("source readiness is unexpectedly armed")
    if readiness.get("testpypi_publication_ready") is not False:
        raise RuntimeError("TestPyPI readiness is unexpectedly armed")
    governance=scope.get("governance")
    if not isinstance(governance,dict) or any(flag is not False for flag in governance.values()):
        raise RuntimeError("draft release scope must have every governance flag set false")
    if len(scope.get("future_required_gates",()))<4:
        raise RuntimeError("literal candidate/governance qualification gates omitted")
    return {
        "proposal_status":"unapproved",
        "source_version":EXPECTED_SOURCE_VERSION,
        "published_stable_baseline":"1.1.0",
        "candidate_workflow_count":len(routes),
        "frozen_root_exports":frozen_counts.get("public_exports"),
        "scientific_blockers_open":sorted(REQUIRED_OPEN_BLOCKERS),
        "release_authorized":False,
    }


def main():
    result=validate_scope(
        scope=load_json("RELEASE_SCOPE_1_2_PROPOSAL.json"),
        readiness=load_json("RELEASE_READINESS.json"),
        audit=load_json("WORKFLOW_API_AUDIT.json"),
        frozen=load_json("ONE_DOT_ZERO_API_STABILITY.json"),
    )
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
