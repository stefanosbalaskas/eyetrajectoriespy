"""Review-only RC2 publication ledger: detect any premature release authorization.

This validator is intentionally not an action to authorize or publish anything.
A later separate governance PR must implement and test the actual transition.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MAIN = "9891feee6e5daa638a9de5cada295482a5fa4884"
EXCLUDED = {
    "universal_nominal_90_pct_simultaneous_coverage",
    "identified_MNAR_gaze_loss_correction",
}


def _load(path: str) -> dict:
    raw=json.loads((ROOT/path).read_text(encoding="utf-8"))
    if not isinstance(raw,dict):
        raise RuntimeError(f"Invalid release review object: {path}")
    return raw


def audit_pending_authorization(review: dict, readiness: dict, scope: dict) -> dict:
    armed = readiness.get("production_release_ready") is True and readiness.get("github_release_ready") is True
    kind = "owner_authorized_pending_independent_review" if armed else "release_authorization_review_pending"
    if (review.get("schema_version") != 1
        or review.get("record_kind") != kind
        or review.get("candidate_version") != readiness.get("current_development_version")
        or review.get("candidate_version") != scope.get("source_version")
        or review.get("candidate_version") != "1.2.0rc2"):
        raise RuntimeError("RC2 publication review source identity mismatch")
    if (review.get("published_stable_version") != "1.1.0"
        or review.get("exact_candidate_merge_commit") != EXPECTED_MAIN
        or review.get("source_qualification_pr") != 471
        or review.get("source_pr_exact_head_qualified") is not True
        or review.get("source_pr_successful_workflows") != 33):
        raise RuntimeError("RC2 candidate PR/merge/provenance identity drifted")
    if (review.get("protected_main_qualification_complete") is not True
        or review.get("protected_main_workflows_all_successful") is not True
        or review.get("protected_main_expected_workflow_runs") != 30
        or review.get("protected_main_successful_workflow_runs") != 30
        or review.get("protected_main_failed_workflow_runs") != 0
        or review.get("protected_main_evidence_url") != "https://github.com/stefanosbalaskas/eyetrajectoriespy/actions"):
        raise RuntimeError("Verified exact-main qualification evidence missing or drifted")
    for field in ("independent_human_release_review_recorded",
                  "testpypi_authorized", "manual_workflow_dispatch_performed"):
        if review.get(field) is not False:
            raise RuntimeError(f"Premature production publication approval: {field}")
    owner_fields = ("narrow_scope_approved_for_release", "github_release_authorized",
                    "production_pypi_authorized", "tag_creation_authorized")
    for field in owner_fields:
        if review.get(field) is not armed:
            raise RuntimeError(f"Owner publication approval state inconsistent: {field}")
    if readiness.get("testpypi_publication_ready") is not False:
        raise RuntimeError("Unreviewed publication gate armed: testpypi_publication_ready")
    if armed:
        if (scope.get("document_type") != "owner_approved_release_scope_pending_independent_review"
            or scope.get("governance", {}).get("proposal_approved") is not True
            or review.get("authorization_pr_number") != 475
            or review.get("independent_exact_head_github_review_enforced_in_workflow") is not True
            or review.get("owner_manual_dispatch_fallback_authorized") is not True
            or "Authenticated stefanosbalaskas manual workflow_dispatch" not in review.get("owner_manual_dispatch_policy", "")):
            raise RuntimeError("Independent review enforcement or owner scope approval missing")
    else:
        if (readiness.get("github_release_ready") is not False
            or readiness.get("production_release_ready") is not False
            or scope.get("document_type") != "unapproved_release_scope_proposal"
            or scope.get("governance",{}).get("proposal_approved") is not False):
            raise RuntimeError("Narrow release scope approval differs from reviewed proposal")
    if (review.get("release_workflow")!=".github/workflows/release.yml"
        or review.get("release_target")!="production"
        or review.get("pypi_environment_review_required") is not True
        or review.get("source_version_wheel_sdist_qualified") is not True
        or review.get("ten_workflow_qualification_passed") is not True
        or review.get("experimental_E1_E4_helpers_retained_as_unqualified") is not True):
        raise RuntimeError("Release or experimental package-content boundary changed")
    if set(review.get("scientific_issues_open",())) != {289,296}:
        raise RuntimeError("Scientific inference/MNAR blockers missing")
    if not EXCLUDED <= set(review.get("excluded_claims",())):
        raise RuntimeError("Unsupported nominal coverage or MNAR claim escaped")
    if not isinstance(review.get("publication_gates"),list) or len(review["publication_gates"])<7:
        raise RuntimeError("Required external review and publishing gates omitted")
    prov=review.get("rc2_performance_provenance",{})
    if (prov.get("workflow_run")!=39945467014
        or prov.get("artifact_id")!=12497727453
        or prov.get("original_source_commit")!="46d2dd74c5ab71d0bb5bd24c356d221f4915b903"
        or prov.get("artifact_member_sha256")!="8da44ff291614aac2b9e01ae8819bcda67f98e0c33cb7b43dfdfb3b9adbcd3d5"):
        raise RuntimeError("Original measured RC2 performance artifact provenance changed")
    return {"version":"1.2.0rc2",
            "status":"owner_authorized_independent_review_pending" if armed else "review_pending",
            "source_qualified":True,"production_authorized":armed,
            "exact_main_qualified":True,"scope_approved":armed}


def main() -> None:
    report=audit_pending_authorization(
        _load("RC2_PUBLICATION_REVIEW.json"),
        _load("RELEASE_READINESS.json"),
        _load("RELEASE_SCOPE_1_2_PROPOSAL.json"),
    )
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
