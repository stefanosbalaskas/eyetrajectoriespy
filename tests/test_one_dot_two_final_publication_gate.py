"""Verify final stable publication cannot reuse an RC2 authorization."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "verify_final_one_dot_two_release_policy.py"
SPEC = importlib.util.spec_from_file_location("final_approval", PATH)
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def inputs():
    p = json.loads((ROOT / "FINAL_1_2_PUBLICATION_APPROVAL.json").read_text())
    r = json.loads((ROOT / "RELEASE_READINESS.json").read_text())
    opts = {
        "actor": "stefanosbalaskas",
        "repository": "stefanosbalaskas/eyetrajectoriespy",
        "git_ref": "refs/heads/main",
        "event_name": "workflow_dispatch",
        "target": "production",
    }
    return p,r,opts

def test_final_requires_distinct_authorization_not_rc2_success():
    p,r,opts=inputs()
    assert p["release_version"] == "1.2.0"
    assert p["owner_production_publication_approved"] is True
    assert p["qualification_main_commit"] == "2d9fe5886ea0c36e619a302d6a6237ce446a18e2"
    assert p["published_final_version"] is True
    assert r["production_release_ready"] is False
    assert r["github_release_ready"] is False
    with pytest.raises(RuntimeError, match="already published"):
        policy.verify_final_release_authorization(p,r,**opts)
    # A previously published final cannot be reopened by toggling flags.
    r["production_release_ready"] = True
    r["github_release_ready"] = True
    with pytest.raises(RuntimeError, match="already published"):
        policy.verify_final_release_authorization(p,r,**opts)

@pytest.mark.parametrize("override",[
    {"actor":"other"},
    {"event_name":"push"},
    {"repository":"other/repo"},
    {"git_ref":"refs/heads/rc2"},
    {"target":"testpypi"},
])
def test_wrong_actor_event_branch_target_are_rejected(override):
    p,r,opts=inputs()
    opts.update(override)
    with pytest.raises(RuntimeError,match="manual release"):
        policy.verify_final_release_authorization(p,r,**opts)

def test_only_separate_final_approval_and_armed_gate_can_pass():
    p,r,opts=inputs()
    p.update(approval_state="separately_authorized_stable_publication",
      final_version_evidence_complete=True, protected_main_exact_ci_qualified=True,
      owner_production_publication_approved=True, published_final_version=False,
      qualification_main_commit="a"*40)
    r.update(production_release_ready=True,github_release_ready=True)
    assert policy.verify_final_release_authorization(p,r,**opts)=="a"*40
    p["scientific_issues_open"]=[]
    with pytest.raises(RuntimeError,match="FINAL approval"):
        policy.verify_final_release_authorization(p,r,**opts)
