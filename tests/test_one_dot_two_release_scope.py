"""R1.2 proposed scope: machine-readable, unapproved, no feature promotion."""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts import validate_one_dot_two_release_scope as policy


def _inputs():
    return {
        "scope":policy.load_json("RELEASE_SCOPE_1_2_PROPOSAL.json"),
        "readiness":policy.load_json("RELEASE_READINESS.json"),
        "audit":policy.load_json("WORKFLOW_API_AUDIT.json"),
        "frozen":policy.load_json("ONE_DOT_ZERO_API_STABILITY.json"),
    }


def test_draft_scope_matches_previous_audited_stable_and_candidate_boundaries():
    result=policy.validate_scope(**_inputs())
    assert result=={
        "proposal_status":"unapproved",
        "source_version":"1.2.0rc2.dev0",
        "published_stable_baseline":"1.1.0",
        "candidate_workflow_count":10,
        "frozen_root_exports":458,
        "scientific_blockers_open":[289,296],
        "release_authorized":False,
    }
    scope=_inputs()["scope"]
    assert scope["frozen_root_compatibility"]["stable_exports"]==455
    assert scope["frozen_root_compatibility"]["experimental_exports"]==3
    assert len({r["contract"] for r in scope["candidate_workflows"]})==10
    assert all(r["interpretation_limit"] for r in scope["candidate_workflows"])


@pytest.mark.parametrize("name",(
    "production_release_ready",
    "github_release_ready",
    "testpypi_publication_ready",
    "merge_authorized",
    "tag_authorized",
    "pypi_publication_authorized",
    "literal_rc2_exact_version_qualified",
))
def test_no_governance_flag_can_be_armed_as_a_scope_proposal(name):
    data=_inputs()
    data["scope"]["governance"][name]=True
    with pytest.raises(RuntimeError,match="governance"):
        policy.validate_scope(**data)


def test_no_candidate_workflow_may_be_added_removed_or_relabeled():
    data=_inputs()
    data["scope"]["candidate_workflows"].pop()
    with pytest.raises(RuntimeError,match="ten"):
        policy.validate_scope(**data)
    data=_inputs()
    data["scope"]["candidate_workflows"][0]["contract"]="unreviewed:v2"
    with pytest.raises(RuntimeError,match="drifted"):
        policy.validate_scope(**data)
    data=_inputs()
    data["scope"]["candidate_workflows"][0]["engineering_status"]="published"
    with pytest.raises(RuntimeError,match="limitation"):
        policy.validate_scope(**data)


@pytest.mark.parametrize("hold",sorted(policy.REQUIRED_CLAIM_HOLDS))
def test_scientific_negative_results_cannot_be_silently_promoted(hold):
    data=_inputs()
    data["scope"]["disallowed_new_claims"].remove(hold)
    with pytest.raises(RuntimeError,match="holds"):
        policy.validate_scope(**data)


@pytest.mark.parametrize("issue",[289,296])
def test_scientific_blocker_cannot_be_omitted(issue):
    data=_inputs()
    data["scope"]["scientific_blockers_open"].remove(issue)
    with pytest.raises(RuntimeError,match="blockers"):
        policy.validate_scope(**data)


def test_literal_rc_evidence_must_not_be_credited_to_dev_source():
    data=_inputs()
    data["scope"]["source_version"]="1.2.0rc2"
    with pytest.raises(RuntimeError,match="identity"):
        policy.validate_scope(**data)
    data=_inputs()
    data["scope"]["governance"]["literal_rc2_exact_version_qualified"]=True
    with pytest.raises(RuntimeError,match="governance"):
        policy.validate_scope(**data)


def test_old_1_0_root_experimental_exports_cannot_be_reclassified():
    data=_inputs()
    data["scope"]["frozen_root_compatibility"]["experimental_exports"]=0
    with pytest.raises(RuntimeError,match="counts"):
        policy.validate_scope(**data)
    data=_inputs()
    data["scope"]["frozen_root_compatibility"]["root_promotion_authorized"]=True
    with pytest.raises(RuntimeError,match="promotion"):
        policy.validate_scope(**data)


def test_testpypi_or_production_armed_readiness_is_not_a_draft():
    data=_inputs()
    data["readiness"]["testpypi_publication_ready"]=True
    with pytest.raises(RuntimeError,match="TestPyPI"):
        policy.validate_scope(**data)
    data=_inputs()
    data["readiness"]["production_release_ready"]=True
    with pytest.raises(RuntimeError,match="armed"):
        policy.validate_scope(**data)


def test_source_audit_historical_evidence_cannot_be_fabricated():
    data=_inputs()
    data["scope"]["last_completed_evidence"]["exact_head_workflows_successful"]=28
    with pytest.raises(RuntimeError,match="evidence"):
        policy.validate_scope(**data)
