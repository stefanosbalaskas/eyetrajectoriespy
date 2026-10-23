"""RC2 release-review checkpoint: pending approval and negative scientific gates."""
from __future__ import annotations

from copy import deepcopy
import pytest

from scripts import validate_rc2_publication_review as contract


def inputs():
    return [
        contract._load("RC2_PUBLICATION_REVIEW.json"),
        contract._load("RELEASE_READINESS.json"),
        contract._load("RELEASE_SCOPE_1_2_PROPOSAL.json"),
    ]


def test_review_is_exact_candidate_based_but_explicitly_unapproved():
    result=contract.audit_pending_authorization(*inputs())
    assert result=={
        "version":"1.2.0rc2","status":"review_pending",
        "source_qualified":True,"production_authorized":False,
        "exact_main_qualified":True,"scope_approved":False,
    }


@pytest.mark.parametrize("field",[
    "independent_human_release_review_recorded",
    "narrow_scope_approved_for_release",
    "github_release_authorized",
    "production_pypi_authorized",
    "testpypi_authorized",
    "tag_creation_authorized",
    "manual_workflow_dispatch_performed",
])
def test_pending_review_cannot_claim_any_approval(field):
    review,readiness,scope=inputs()
    review[field]=True
    with pytest.raises(RuntimeError,match="Premature production"):
        contract.audit_pending_authorization(review,readiness,scope)


@pytest.mark.parametrize("field",[
    "github_release_ready","production_release_ready","testpypi_publication_ready",
])
def test_pending_review_refuses_disarmed_flag_mutation(field):
    review,readiness,scope=inputs()
    readiness[field]=True
    with pytest.raises(RuntimeError,match="Unreviewed publication"):
        contract.audit_pending_authorization(review,readiness,scope)


def test_open_scientific_blockers_and_claim_exclusions_are_immutable():
    for issue in (289,296):
        review,readiness,scope=inputs()
        review["scientific_issues_open"].remove(issue)
        with pytest.raises(RuntimeError,match="blockers"):
            contract.audit_pending_authorization(review,readiness,scope)
    for claim in contract.EXCLUDED:
        review,readiness,scope=inputs()
        review["excluded_claims"].remove(claim)
        with pytest.raises(RuntimeError,match="Unsupported"):
            contract.audit_pending_authorization(review,readiness,scope)


@pytest.mark.parametrize("field,value",[
    ("protected_main_qualification_complete",False),
    ("protected_main_workflows_all_successful",False),
    ("protected_main_expected_workflow_runs",29),
    ("protected_main_successful_workflow_runs",29),
    ("protected_main_failed_workflow_runs",1),
    ("protected_main_evidence_url","https://example.invalid"),
])
def test_main_ci_verified_record_cannot_drift(field,value):
    review,readiness,scope=inputs()
    review[field]=value
    with pytest.raises(RuntimeError,match="Verified exact-main"):
        contract.audit_pending_authorization(review,readiness,scope)


def test_source_artifact_sha_and_exact_version_cannot_be_rewritten():
    review,readiness,scope=inputs()
    review["rc2_performance_provenance"]["artifact_member_sha256"]="0"*64
    with pytest.raises(RuntimeError,match="artifact provenance"):
        contract.audit_pending_authorization(review,readiness,scope)
    review,readiness,scope=inputs()
    review["candidate_version"]="1.2.0rc1"
    with pytest.raises(RuntimeError,match="identity"):
        contract.audit_pending_authorization(review,readiness,scope)
