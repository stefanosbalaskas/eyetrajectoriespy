"""Require a real independent GitHub sign-off; reject self, stale and forged reviews."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_rc2_independent_pr_approval.py"
SPEC = importlib.util.spec_from_file_location("rc2_pr_gate", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def fixture():
    sha = "a" * 40
    pr = {
        "number": 475, "merged": True, "merged_at": "2026-10-24T08:00:00Z",
        "base": {"ref": "main"}, "head": {"sha": sha},
        "user": {"login": "stefanosbalaskas"},
    }
    return pr, sha


def approval(login, sha, state="APPROVED", type="User"):
    return {"user": {"login": login, "type": type},
            "state": state, "commit_id": sha}


def test_independent_exact_head_review_passes():
    pr, sha = fixture()
    assert gate.validate_external_review(
        pr, [approval("outside_reviewer", sha)]
    ) == "outside_reviewer"


@pytest.mark.parametrize("modifier", [
    lambda p: p.update({"merged": False}),
    lambda p: p.update({"number": 474}),
    lambda p: p["base"].update({"ref": "release"}),
    lambda p: p["head"].update({"sha": "short"}),
])
def test_nonmerged_or_wrong_pr_refused(modifier):
    pr, sha = fixture()
    modifier(pr)
    with pytest.raises(RuntimeError):
        gate.validate_external_review(pr, [approval("outside_reviewer", sha)])


@pytest.mark.parametrize("bad", [
    lambda sha: approval("stefanosbalaskas", sha),
    lambda sha: approval("outside_reviewer", "b" * 40),
    lambda sha: approval("outside_reviewer", sha, "COMMENTED"),
    lambda sha: approval("outside_reviewer", sha, type="Bot"),
])
def test_no_self_stale_comment_only_or_bot_review(bad):
    pr, sha = fixture()
    with pytest.raises(RuntimeError, match="independent human"):
        gate.validate_external_review(pr, [bad(sha)])


def test_latest_changed_or_rejected_review_overrides_approval():
    pr, sha = fixture()
    with pytest.raises(RuntimeError, match="independent human"):
        gate.validate_external_review(
            pr, [approval("outside_reviewer", sha),
                 approval("outside_reviewer", sha, "CHANGES_REQUESTED")]
        )


def test_no_review_does_not_publish():
    pr, _ = fixture()
    with pytest.raises(RuntimeError, match="independent human"):
        gate.validate_external_review(pr, [])


def test_authenticated_owner_dispatch_is_explicitly_allowed_without_fake_review():
    pr, _ = fixture()
    pr["head"]["sha"] = gate.EXPECTED_AUTHORIZATION_HEAD
    ledger = {
        "candidate_version": "1.2.0rc2",
        "authorization_pr_number": 475,
        "owner_manual_dispatch_fallback_authorized": True,
        "independent_human_release_review_recorded": False,
        "narrow_scope_approved_for_release": True,
        "pypi_environment_review_required": True,
    }
    assert gate.validate_owner_manual_dispatch(
        pr, ledger, actor="stefanosbalaskas",
        event_name="workflow_dispatch",
        repository="stefanosbalaskas/eyetrajectoriespy",
        git_ref="refs/heads/main", target="production",
    ) == "stefanosbalaskas"


@pytest.mark.parametrize("override", [
    {"actor": "outside_reviewer"},
    {"event_name": "push"},
    {"git_ref": "refs/heads/release"},
    {"repository": "outside/eyetrajectoriespy"},
    {"target": "testpypi"},
    {"target": "build-only"},
])
def test_owner_path_refuses_other_actors_or_contexts(override):
    pr, _ = fixture()
    pr["head"]["sha"] = gate.EXPECTED_AUTHORIZATION_HEAD
    ledger = {
        "candidate_version": "1.2.0rc2",
        "authorization_pr_number": 475,
        "owner_manual_dispatch_fallback_authorized": True,
        "independent_human_release_review_recorded": False,
        "narrow_scope_approved_for_release": True,
        "pypi_environment_review_required": True,
    }
    params = dict(
        actor="stefanosbalaskas", event_name="workflow_dispatch",
        repository="stefanosbalaskas/eyetrajectoriespy",
        git_ref="refs/heads/main", target="production",
    )
    params.update(override)
    with pytest.raises(RuntimeError, match="authenticated manual"):
        gate.validate_owner_manual_dispatch(pr, ledger, **params)


@pytest.mark.parametrize("bad_field,bad_value", [
    ("owner_manual_dispatch_fallback_authorized", False),
    ("independent_human_release_review_recorded", True),
    ("pypi_environment_review_required", False),
    ("authorization_pr_number", 474),
])
def test_owner_path_rejects_invalid_documentary_authorization(bad_field, bad_value):
    pr, _ = fixture()
    pr["head"]["sha"] = gate.EXPECTED_AUTHORIZATION_HEAD
    ledger = {
        "candidate_version": "1.2.0rc2",
        "authorization_pr_number": 475,
        "owner_manual_dispatch_fallback_authorized": True,
        "independent_human_release_review_recorded": False,
        "narrow_scope_approved_for_release": True,
        "pypi_environment_review_required": True,
    }
    ledger[bad_field] = bad_value
    with pytest.raises(RuntimeError, match="recorded recovery"):
        gate.validate_owner_manual_dispatch(
            pr, ledger, actor="stefanosbalaskas",
            event_name="workflow_dispatch",
            repository="stefanosbalaskas/eyetrajectoriespy",
            git_ref="refs/heads/main", target="production",
        )


def test_owner_path_rejects_wrong_original_pr_sha_even_when_authorized():
    pr, _ = fixture()
    ledger = {
        "candidate_version": "1.2.0rc2",
        "authorization_pr_number": 475,
        "owner_manual_dispatch_fallback_authorized": True,
        "independent_human_release_review_recorded": False,
        "narrow_scope_approved_for_release": True,
        "pypi_environment_review_required": True,
    }
    with pytest.raises(RuntimeError, match="immutable RC2"):
        gate.validate_owner_manual_dispatch(
            pr, ledger, actor="stefanosbalaskas",
            event_name="workflow_dispatch",
            repository="stefanosbalaskas/eyetrajectoriespy",
            git_ref="refs/heads/main", target="production",
        )
