"""RC2 owner authorization has live-review gate, not fabricated independent approval."""
from __future__ import annotations
import pytest
from scripts import validate_rc2_publication_review as policy


def inputs():
    return [
        policy._load("RC2_PUBLICATION_REVIEW.json"),
        policy._load("RELEASE_READINESS.json"),
        policy._load("RELEASE_SCOPE_1_2_PROPOSAL.json"),
    ]


def test_owner_authorization_pending_real_independent_review():
    assert policy.audit_pending_authorization(*inputs()) == {
        "version": "1.2.0rc2",
        "status": "owner_authorized_independent_review_pending",
        "source_qualified": True, "production_authorized": True,
        "exact_main_qualified": True, "scope_approved": True,
    }


@pytest.mark.parametrize("field", [
    "independent_human_release_review_recorded",
    "testpypi_authorized", "manual_workflow_dispatch_performed",
])
def test_no_false_independent_review_or_execution_record(field):
    review, readiness, scope = inputs()
    review[field] = True
    with pytest.raises(RuntimeError, match="Premature"):
        policy.audit_pending_authorization(review, readiness, scope)


@pytest.mark.parametrize("field", [
    "narrow_scope_approved_for_release", "github_release_authorized",
    "production_pypi_authorized", "tag_creation_authorized",
])
def test_no_partial_owner_approval(field):
    review, readiness, scope = inputs()
    review[field] = False
    with pytest.raises(RuntimeError, match="Owner"):
        policy.audit_pending_authorization(review, readiness, scope)


def test_exact_review_pr_and_external_gate_required():
    review, readiness, scope = inputs()
    review["authorization_pr_number"] = 999
    with pytest.raises(RuntimeError, match="Independent"):
        policy.audit_pending_authorization(review, readiness, scope)
    review, readiness, scope = inputs()
    review["independent_exact_head_github_review_enforced_in_workflow"] = False
    with pytest.raises(RuntimeError, match="Independent"):
        policy.audit_pending_authorization(review, readiness, scope)


@pytest.mark.parametrize("issue", [289, 296])
def test_scientific_blocks_preserved(issue):
    review, readiness, scope = inputs()
    review["scientific_issues_open"].remove(issue)
    with pytest.raises(RuntimeError, match="blockers"):
        policy.audit_pending_authorization(review, readiness, scope)


@pytest.mark.parametrize("field,value", [
    ("protected_main_qualification_complete", False),
    ("protected_main_workflows_all_successful", False),
    ("protected_main_expected_workflow_runs", 29),
    ("protected_main_successful_workflow_runs", 29),
    ("protected_main_failed_workflow_runs", 1),
])
def test_historical_main_ci_unchanged(field, value):
    review, readiness, scope = inputs()
    review[field] = value
    with pytest.raises(RuntimeError, match="Verified exact-main"):
        policy.audit_pending_authorization(review, readiness, scope)


def test_provenance_and_exclusions_cannot_be_erased():
    review, readiness, scope = inputs()
    review["rc2_performance_provenance"]["artifact_member_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="artifact provenance"):
        policy.audit_pending_authorization(review, readiness, scope)
    review, readiness, scope = inputs()
    review["excluded_claims"] = []
    with pytest.raises(RuntimeError, match="Unsupported"):
        policy.audit_pending_authorization(review, readiness, scope)


def test_explicit_owner_dispatch_policy_cannot_be_silently_removed():
    review, readiness, scope = inputs()
    review["owner_manual_dispatch_fallback_authorized"] = False
    with pytest.raises(RuntimeError, match="Independent review enforcement"):
        policy.audit_pending_authorization(review, readiness, scope)
