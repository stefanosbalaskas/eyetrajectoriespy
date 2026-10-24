"""1.2 release qualification: strict manual-target and exact-main failure gates.

No test sends a network request, uploads distributions, or arms readiness.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name, ROOT/"scripts"/f"{name}.py")
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def current():
    return json.loads((ROOT/"RELEASE_READINESS.json").read_text(encoding="utf-8"))


def fully_armed():
    return {"testpypi_publication_ready":True,
            "production_release_ready":True,
            "github_release_ready":True,
            "gates":{
                "testpypi_trusted_publishing_configured":True,
                "pypi_trusted_publishing_configured":True,
                "pypi_environment_required_reviewer":True,
                "exact_main_ci_required":True,
            }}


def test_current_1_2_release_owner_arm_requires_live_approval_or_authenticated_owner_dispatch():
    policy=load("verify_release_publication_gate")
    readiness=current()
    assert readiness["current_development_version"]=="1.2.0rc2"
    assert readiness["production_release_ready"] is True
    assert readiness["github_release_ready"] is True
    assert readiness["testpypi_publication_ready"] is False
    assert policy.verify_publication_policy(readiness,"build-only")=="build-only"
    assert policy.verify_publication_policy(readiness,"production")=="production"
    assert policy.verify_publication_policy(readiness,"resume-production")=="resume-production"
    with pytest.raises(RuntimeError,match="blocked"):
        policy.verify_publication_policy(readiness,"testpypi")
    workflow=(ROOT/".github/workflows/release.yml").read_text()
    assert "verify_rc2_independent_pr_approval.py" in workflow
    assert workflow.index("verify_rc2_independent_pr_approval.py") < workflow.index("python -m build")
    assert "RELEASE_TARGET: ${{ inputs.target }}" in workflow


@pytest.mark.parametrize("target",("testpypi","production","resume-production"))
def test_no_publication_target_passes_with_unset_flags(target):
    policy=load("verify_release_publication_gate")
    readiness=fully_armed()
    readiness["testpypi_publication_ready"]=False
    readiness["github_release_ready"]=False
    readiness["production_release_ready"]=False
    with pytest.raises(RuntimeError,match="blocked"):
        policy.verify_publication_policy(readiness,target)


@pytest.mark.parametrize("target",("production","resume-production"))
def test_production_and_resume_require_two_distinct_approval_flags(target):
    policy=load("verify_release_publication_gate")
    for key in ("production_release_ready","github_release_ready"):
        ready=fully_armed()
        ready[key]=False
        with pytest.raises(RuntimeError,match="BOTH"):
            policy.verify_publication_policy(ready,target)


def test_testpypi_requires_separate_approval_and_trusted_environment():
    policy=load("verify_release_publication_gate")
    ready=fully_armed()
    for key in ("testpypi_publication_ready","testpypi_trusted_publishing_configured"):
        trial=fully_armed()
        if key in trial:trial[key]=False
        else:trial["gates"][key]=False
        with pytest.raises(RuntimeError,match="TestPyPI publishing blocked"):
            policy.verify_publication_policy(trial,"testpypi")
    assert policy.verify_publication_policy(ready,"testpypi")=="testpypi"


def test_production_requires_trusted_publishing_review_and_exact_main():
    policy=load("verify_release_publication_gate")
    for key in ("pypi_trusted_publishing_configured",
                "pypi_environment_required_reviewer","exact_main_ci_required"):
        ready=fully_armed()
        ready["gates"][key]=False
        with pytest.raises(RuntimeError,match=key):
            policy.verify_publication_policy(ready,"production")
    for target in ("production","resume-production"):
        assert policy.verify_publication_policy(fully_armed(),target)==target


def test_unknown_target_is_refused():
    policy=load("verify_release_publication_gate")
    with pytest.raises(ValueError,match="Unrecognized"):
        policy.verify_publication_policy(fully_armed(),"unsafe-target")


def test_release_workflow_always_checks_publication_policy_before_build():
    source=(ROOT/".github/workflows/release.yml").read_text()
    assert "python scripts/verify_release_publication_gate.py --target" in source
    assert source.index("verify_release_publication_gate.py") < source.index("python -m build")
    assert "workflow_dispatch:" in source
    assert "publish-testpypi" in source and "publish-pypi" in source
    assert "resume-pypi" in source
    assert "testpypi" in source and "build-only" in source


def test_production_governance_requires_both_approval_flags():
    governance=load("verify_release_governance")
    governance._verify_declared_github_release_readiness()
    # A hypothetically arming GitHub release alone is insufficient.
    original=governance._release_readiness
    try:
        governance._release_readiness=lambda:{
            "github_release_ready":True,
            "production_release_ready":False,
            "gates":{n:True for n in governance._GITHUB_RELEASE_DECLARATIONS},
        }
        with pytest.raises(RuntimeError,match="production_release_ready"):
            governance._verify_declared_github_release_readiness()
    finally:
        governance._release_readiness=original


def test_required_checks_reject_skipped_neutral_and_incomplete(monkeypatch):
    governance=load("verify_release_governance")
    repo="stefanosbalaskas/eyetrajectoriespy"
    commit="f"*40
    good="test (ubuntu-latest, 3.12)"
    def fake(url,token):
        assert token=="fake"
        assert f"/commits/{commit}/check-runs" in url
        return {"check_runs":[
            {"name":good,"status":"completed","conclusion":"success"},
            {"name":"docs-build","status":"completed","conclusion":"skipped"},
            {"name":"release-readiness","status":"completed","conclusion":"neutral"},
            {"name":"installed-product","status":"in_progress","conclusion":None},
        ]}
    monkeypatch.setattr(governance,"_github_json",fake)
    assert governance._passed_checks(repo,commit,"fake")=={good}


def test_literal_candidate_needs_new_exact_version_evidence_but_no_publication():
    version=load("verify_release_version")
    assert version.verify_version_contract()=="1.2.0rc2"
    assert set(version.qualified_evidence_contract().values())=={"1.2.0rc2"}
    assert version.verify_version_contract(production=True)=="1.2.0rc2"
    assert current()["production_release_ready"] is True
    assert current()["github_release_ready"] is True


def test_future_arming_documentation_rejects_stale_1_1_main_provenance():
    """Do not import a heavy docs validator in the installed-wheel smoke tests."""
    import ast

    source = ast.parse(
        (ROOT / "scripts" / "validate_docs_contracts.py").read_text(
            encoding="utf-8"
        )
    )
    assignments = [
        node.value.value
        for node in source.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "QUALIFIED_RELEASE_MAIN"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
    ]
    assert assignments == ["9891feee6e5daa638a9de5cada295482a5fa4884"]
    notes = "\n".join(current()["notes"])
    assert assignments[0] in notes
    assert "30/30 workflow groups successfully" in notes
    assert current()["current_development_version"] == "1.2.0rc2"
    assert current()["production_release_ready"] is True
    assert current()["github_release_ready"] is True
    assert current()["testpypi_publication_ready"] is False
    release_yaml = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    assert "verify_rc2_independent_pr_approval.py" in release_yaml
