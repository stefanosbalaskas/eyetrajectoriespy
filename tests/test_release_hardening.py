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


def test_release_version_contract_agrees_for_rc1():
    module = _load_script("verify_release_version.py")
    assert module.verify_version_contract() == "0.9.0rc1"


def test_production_release_accepts_rc_on_exact_main_before_tag_creation():
    module = _load_script("verify_release_version.py")
    assert module.verify_version_contract(
        production=True,
    ) == "0.9.0rc1"


def test_production_release_accepts_matching_rc_tag():
    module = _load_script("verify_release_version.py")
    assert module.verify_version_contract(
        tag="v0.9.0rc1",
        production=True,
    ) == "0.9.0rc1"


def test_release_governance_happy_path_requires_all_quality_gates(monkeypatch):
    module = _load_script("verify_release_governance.py")
    repository = "stefanosbalaskas/eyetrajectoriespy"
    commit = "a" * 40
    def fake_get(url, token):
        assert token == "token"
        if url.endswith("/branches/main"):
            return {
                "protected": True,
                "commit": {"sha": commit},
            }
        if url.endswith("/issues/64"):
            return {"state": "closed"}
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
    monkeypatch.setattr(
        module,
        "_release_readiness",
        lambda: {
            "github_release_ready": True,
            "gates": {
                name: True
                for name in module._GITHUB_RELEASE_DECLARATIONS
            },
        },
    )
    module.verify_release_governance(
        repository=repository,
        commit=commit,
        token="token",
    )


def test_release_governance_blocks_unprotected_main(monkeypatch):
    module = _load_script("verify_release_governance.py")

    monkeypatch.setattr(
        module,
        "_release_readiness",
        lambda: {
            "github_release_ready": True,
            "gates": {
                name: True
                for name in module._GITHUB_RELEASE_DECLARATIONS
            },
        },
    )
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
    assert "environment: testpypi" in workflow
    assert 'gh release download "v${VERSION}"' in workflow
    assert '--pattern "*.whl"' in workflow
    assert '--pattern "*.tar.gz"' in workflow
    assert "sha256sum -c dist/SHA256SUMS" in workflow
    assert "rm dist/SHA256SUMS" in workflow
    assert "id-token: write" in workflow
    assert "needs:" in workflow
    assert "- github-release" in workflow
    assert "gh release create" in workflow
    assert workflow.index("gh release create") < workflow.index(
        "uses: pypa/gh-action-pypi-publish@release/v1",
        workflow.index("publish-pypi:"),
    )
    assert "--verify-tag" in workflow
    assert "verify-pypi-install" in workflow
    verify_block = workflow.split("  verify-pypi:", 1)[1]
    assert "- publish-pypi" in verify_block


def test_production_release_has_no_manual_dispatch_path():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert "publish-pypi:" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "inputs.target == 'testpypi'" in workflow
    assert "production" not in workflow.split("options:", 1)[1].split(
        "concurrency:", 1
    )[0]

def test_release_governance_blocks_unarmed_readiness_manifest(monkeypatch):
    module = _load_script("verify_release_governance.py")
    monkeypatch.setattr(
        module,
        "_release_readiness",
        lambda: {
            "github_release_ready": False,
            "gates": {},
        },
    )

    with pytest.raises(RuntimeError, match="is not armed"):
        module.verify_release_governance(
            repository="stefanosbalaskas/eyetrajectoriespy",
            commit="a" * 40,
            token="token",
        )

