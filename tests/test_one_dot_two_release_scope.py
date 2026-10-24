"""RC2 owner publication scope: exact installed routes, pending external review."""
from __future__ import annotations
import pytest
from scripts import validate_one_dot_two_release_scope as policy


def inputs():
    return {
        "scope": policy.load_json("RELEASE_SCOPE_1_2_PROPOSAL.json"),
        "readiness": policy.load_json("RELEASE_READINESS.json"),
        "audit": policy.load_json("WORKFLOW_API_AUDIT.json"),
        "frozen": policy.load_json("ONE_DOT_ZERO_API_STABILITY.json"),
    }


def test_owner_scope_arms_only_narrow_rc2_prerelease():
    data = inputs()
    result = policy.validate_scope(**data)
    assert result == {
        "proposal_status": "owner_authorized_pending_independent_review",
        "source_version": "1.2.0rc2",
        "published_stable_baseline": "1.1.0",
        "candidate_workflow_count": 10,
        "frozen_root_exports": 458,
        "scientific_blockers_open": [289, 296],
        "release_authorized": True,
    }
    assert data["scope"]["frozen_root_compatibility"]["stable_exports"] == 455
    assert data["scope"]["frozen_root_compatibility"]["experimental_exports"] == 3


@pytest.mark.parametrize("field", [
    "production_release_ready", "github_release_ready", "proposal_approved",
    "literal_rc2_exact_version_qualified", "tag_authorized",
    "pypi_publication_authorized",
])
def test_owner_scope_flag_cannot_be_partly_disarmed(field):
    data = inputs()
    data["scope"]["governance"][field] = False
    with pytest.raises(RuntimeError, match="governance"):
        policy.validate_scope(**data)


def test_merge_permission_not_preapproved_without_external_review():
    data = inputs()
    data["scope"]["governance"]["merge_authorized"] = True
    with pytest.raises(RuntimeError, match="governance"):
        policy.validate_scope(**data)


def test_version_and_api_drift_still_refused():
    data = inputs()
    data["scope"]["source_version"] = "1.2.0rc1"
    with pytest.raises(RuntimeError, match="identity"):
        policy.validate_scope(**data)
    data = inputs()
    data["scope"]["candidate_workflows"].pop()
    with pytest.raises(RuntimeError, match="ten"):
        policy.validate_scope(**data)
    data = inputs()
    data["scope"]["candidate_workflows"][0]["contract"] = "untested:v2"
    with pytest.raises(RuntimeError, match="drifted"):
        policy.validate_scope(**data)
    data = inputs()
    data["scope"]["frozen_root_compatibility"]["experimental_exports"] = 0
    with pytest.raises(RuntimeError, match="counts"):
        policy.validate_scope(**data)


@pytest.mark.parametrize("hold", sorted(policy.REQUIRED_CLAIM_HOLDS))
def test_unsupported_inference_never_promoted(hold):
    data = inputs()
    data["scope"]["disallowed_new_claims"].remove(hold)
    with pytest.raises(RuntimeError, match="holds"):
        policy.validate_scope(**data)


@pytest.mark.parametrize("issue", [289, 296])
def test_scientific_blockers_still_visible(issue):
    data = inputs()
    data["scope"]["scientific_blockers_open"].remove(issue)
    with pytest.raises(RuntimeError, match="blockers"):
        policy.validate_scope(**data)


def test_experimental_helpers_not_stable_routes():
    data = inputs()
    module = data["scope"]["bundled_unqualified_experimental_module"]
    assert len(module["named_experimental_helpers"]) == 12
    assert module["public_contract_frozen"] is False
    assert module["supported_in_proposed_ten_workflow_api"] is False
    assert set(module["named_experimental_helpers"]).isdisjoint(
        data["audit"]["workflow_entry_points"])
    data["scope"]["bundled_unqualified_experimental_module"]["public_contract_frozen"] = True
    with pytest.raises(RuntimeError, match="promoted"):
        policy.validate_scope(**data)


def test_testpypi_remains_disarmed():
    data = inputs()
    data["readiness"]["testpypi_publication_ready"] = True
    with pytest.raises(RuntimeError, match="TestPyPI"):
        policy.validate_scope(**data)


def test_no_partial_readiness_or_fake_historical_evidence():
    data = inputs()
    data["readiness"]["production_release_ready"] = False
    with pytest.raises(RuntimeError):
        policy.validate_scope(**data)
    data = inputs()
    data["scope"]["last_completed_evidence"]["exact_head_workflows_successful"] = 28
    with pytest.raises(RuntimeError, match="evidence"):
        policy.validate_scope(**data)
