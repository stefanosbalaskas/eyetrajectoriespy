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
