"""Fail-closed technical review of the E1-E4 bundle; never authorizes publication."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RC2_COMMIT = "9891feee6e5daa638a9de5cada295482a5fa4884"
HELD = {
    "nominal_90_percent_simultaneous_functional_band_coverage",
    "validated_CR2_fitted_covariance_random_slope_inference",
    "MNAR_gaze_loss_identification_from_observed_data",
}
PENDING = (
    "independent_human_package_content_approval",
    "separate_publication_authorization_review_completed",
    "production_release_authorized",
    "github_release_authorized",
    "tag_authorized",
    "testpypi_authorized",
    "release_workflow_dispatched",
    "implementation_change_in_this_pr",
)


def read(name: str) -> dict:
    obj = json.loads((ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"Not a JSON object: {name}")
    return obj


def validate_content_review(
    proposal: dict, scope: dict, release: dict, readiness: dict, e5: dict,
) -> dict:
    if (proposal.get("schema_version") != 1
        or proposal.get("document_type") != "rc2_experimental_distribution_content_review"
        or proposal.get("version") != "1.2.0rc2"
        or scope.get("source_version") != proposal["version"]
        or release.get("candidate_version") != proposal["version"]
        or readiness.get("current_development_version") != proposal["version"]
        or e5.get("source_version") != proposal["version"]):
        raise RuntimeError("Literal RC2 source/version identity drift")
    evidence = proposal.get("e5_evidence", {})
    if (proposal.get("exact_rc2_candidate_commit") != RC2_COMMIT
        or proposal.get("source_qualification_pr") != 471
        or proposal.get("protected_main_ci_successful") != 30
        or proposal.get("protected_main_ci_failed") != 0
        or evidence.get("workflow") != "experimental-workflow-expansion"
        or evidence.get("run_id") != 40002802440
        or evidence.get("source_commit") != RC2_COMMIT
        or evidence.get("python_versions") != ["3.11", "3.12", "3.13"]
        or evidence.get("qualified_jobs") != 3
        or len(evidence.get("checks", [])) != 4
        or release.get("protected_main_workflows_all_successful") is not True):
        raise RuntimeError("E5 evidence or exact-main qualification changed")
    experimental = scope.get("bundled_unqualified_experimental_module", {})
    if (proposal.get("package_module") != experimental.get("module")
        or proposal.get("package_module") != "eyetrajectoriespy.workflows.experimental"
        or proposal.get("imported_helper_names") != experimental.get("named_experimental_helpers")
        or len(proposal.get("imported_helper_names", [])) != 12
        or proposal.get("proposed_decision") !=
          "include_twelve_importable_E1_E4_helpers_as_explicitly_experimental_prerelease_only"
        or experimental.get("supported_in_proposed_ten_workflow_api") is not False
        or experimental.get("public_contract_frozen") is not False):
        raise RuntimeError("Experimental E1-E4 package-content boundary drift")
    if (proposal.get("primary_workflow_routes_supported") != 10
        or len(scope.get("candidate_workflows", [])) != 10
        or proposal.get("stable_root_exports") != 455
        or proposal.get("frozen_experimental_root_exports") != 3
        or proposal.get("stable_root_promotions") != 0):
        raise RuntimeError("Ten-route or root API compatibility boundary changed")
    if (set(proposal.get("unresolved_inference_claims", [])) != HELD
        or set(proposal.get("open_scientific_issues", [])) != {289, 296}
        or set(scope.get("scientific_blockers_open", [])) != {289, 296}):
        raise RuntimeError("Scientific inference hold or blocker missing")
    armed = readiness.get("production_release_ready") is True and readiness.get("github_release_ready") is True
    if (proposal.get("independent_human_package_content_approval") is not False
        or proposal.get("separate_publication_authorization_review_completed") is not False
        or proposal.get("testpypi_authorized") is not False
        or proposal.get("release_workflow_dispatched") is not False
        or proposal.get("implementation_change_in_this_pr") is not False
        or readiness.get("testpypi_publication_ready") is not False
        or release.get("independent_human_release_review_recorded") is not False):
        raise RuntimeError("Human approval/publication cannot be asserted by this review")
    for flag in ("production_release_authorized", "github_release_authorized", "tag_authorized"):
        if proposal.get(flag) is not armed:
            raise RuntimeError("Owner authorization/E5 review state inconsistent")
    if armed:
        if (proposal.get("authorization_pr_number") != 475
            or release.get("authorization_pr_number") != 475
            or scope.get("governance", {}).get("proposal_approved") is not True):
            raise RuntimeError("Independent review enforcement/E5 owner authorization missing")
    elif (scope.get("governance", {}).get("proposal_approved") is not False
          or readiness.get("production_release_ready") is not False
          or readiness.get("github_release_ready") is not False):
        raise RuntimeError("Human approval/publication cannot be asserted by this review")
    if (not isinstance(proposal.get("reviewer_decision_required"), str)
        or len(proposal["reviewer_decision_required"]) < 60
        or not isinstance(proposal.get("reviewer_guidance"), str)
        or len(proposal["reviewer_guidance"]) < 100):
        raise RuntimeError("Required E5 content decision or reviewer instructions missing")
    return {"version": "1.2.0rc2", "E5_source_technical_jobs": 3,
            "status": "owner_authorized_independent_review_pending" if armed else "independent_review_pending",
            "experimental_helpers": 12, "stable_root_promotions": 0,
            "publication_authorized": armed}


def main() -> None:
    print(json.dumps(validate_content_review(
        read("E5_RC2_CONTENT_REVIEW.json"),
        read("RELEASE_SCOPE_1_2_PROPOSAL.json"),
        read("RC2_PUBLICATION_REVIEW.json"),
        read("RELEASE_READINESS.json"),
        read("EXPERIMENTAL_WORKFLOW_AUDIT.json"),
    ), sort_keys=True))


if __name__ == "__main__":
    main()
