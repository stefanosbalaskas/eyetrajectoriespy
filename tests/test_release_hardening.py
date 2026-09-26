import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_release_version_contract_agrees_for_057():
    module = _load_script("verify_release_version.py")
    assert module.verify_version_contract() == "0.57.0.dev0"


def test_production_release_rejects_dev_version():
    module = _load_script("verify_release_version.py")
    with pytest.raises(RuntimeError, match="development versions"):
        module.verify_version_contract(
            tag="v0.57.0.dev0",
            production=True,
        )


def test_release_governance_happy_path_requires_all_quality_gates(monkeypatch):
    module = _load_script("verify_release_governance.py")
    repository = "stefanosbalaskas/eyetrajectoriespy"
    commit = "a" * 40
    tag_sha = "b" * 40

    def fake_get(url, token):
        assert token == "token"
        if url.endswith("/branches/main"):
            return {
                "protected": True,
                "commit": {"sha": commit},
            }
        if url.endswith("/issues/64"):
            return {"state": "closed"}
        if "/git/ref/tags/" in url:
            return {
                "object": {
                    "type": "tag",
                    "sha": tag_sha,
                }
            }
        if url.endswith(f"/git/tags/{tag_sha}"):
            return {
                "verification": {"verified": True},
                "object": {"sha": commit},
            }
        if "/check-runs?" in url:
            return {
                "check_runs": [
                    {
                        "name": name,
                        "status": "completed",
                        "conclusion": "success",
                    }
                    for name in module.REQUIRED_CHECKS
                ]
            }
        raise AssertionError(url)

    monkeypatch.setattr(module, "_github_json", fake_get)
    module.verify_release_governance(
        repository=repository,
        commit=commit,
        tag="v0.9.0rc1",
        token="token",
    )


def test_release_governance_blocks_unprotected_main(monkeypatch):
    module = _load_script("verify_release_governance.py")

    monkeypatch.setattr(
        module,
        "_github_json",
        lambda url, token: {
            "protected": False,
            "commit": {"sha": "a" * 40},
        },
    )
    with pytest.raises(RuntimeError, match="main is not protected"):
        module.verify_release_governance(
            repository="stefanosbalaskas/eyetrajectoriespy",
            commit="a" * 40,
            tag="v0.9.0rc1",
            token="token",
        )


def test_release_workflow_builds_once_and_reuses_exact_artifact():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert workflow.count("python -m build") == 1
    assert "name: release-build-once" in workflow
    assert workflow.count("name: release-dist") >= 3
    assert "uses: pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "environment: pypi" in workflow
    assert "environment: testpypi" in workflow
    assert "id-token: write" in workflow
    assert "needs:" in workflow
    assert "- publish-pypi" in workflow
    assert "gh release create" in workflow
    assert "--verify-tag" in workflow
    assert "verify-pypi-install" in workflow


def test_production_release_has_no_manual_dispatch_path():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert "publish-pypi:" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "startsWith(github.ref, 'refs/tags/v')" in workflow
    assert "inputs.target == 'testpypi'" in workflow
    assert "production" not in workflow.split("options:", 1)[1].split(
        "concurrency:", 1
    )[0]
