import importlib.util
import urllib.error
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


def test_release_version_contract_agrees_for_development_line():
    module = _load_script("verify_release_version.py")
    assert module.verify_version_contract() == "0.12.0.dev0"


def test_current_development_line_is_not_production_eligible():
    module = _load_script("verify_release_version.py")
    with pytest.raises(RuntimeError, match="development versions"):
        module.verify_version_contract(
            tag="v0.12.0.dev0",
            production=True,
        )


def test_production_release_rejects_development_line(monkeypatch):
    module = _load_script("verify_release_version.py")
    monkeypatch.setattr(
        module,
        "version_contract",
        lambda: {
            "pyproject.toml": "0.10.1.dev0",
            "package __version__": "0.10.1.dev0",
            "CITATION.cff": "0.10.1.dev0",
        },
    )
    with pytest.raises(RuntimeError, match="development versions"):
        module.verify_version_contract(production=True)


def test_production_release_rejects_development_tag(monkeypatch):
    module = _load_script("verify_release_version.py")
    monkeypatch.setattr(
        module,
        "version_contract",
        lambda: {
            "pyproject.toml": "0.10.1.dev0",
            "package __version__": "0.10.1.dev0",
            "CITATION.cff": "0.10.1.dev0",
        },
    )
    with pytest.raises(RuntimeError, match="development versions"):
        module.verify_version_contract(
            tag="v0.10.1.dev0",
            production=True,
        )


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


def test_release_governance_requires_exact_main_simulation_evidence():
    module = _load_script("verify_release_governance.py")
    assert "recovery" in module.REQUIRED_CHECKS
    assert "stress-evidence" in module.REQUIRED_CHECKS
    assert "sparse-performance" in module.REQUIRED_CHECKS
    assert "stress-recovery" in module.REQUIRED_CHECKS
    assert "noise-variance-recovery" in module.REQUIRED_CHECKS
    assert "known-truth-recovery" in module.REQUIRED_CHECKS
    assert "resource-envelope" in module.REQUIRED_CHECKS
    assert "frozen-fixture-sensitivity" in module.REQUIRED_CHECKS
    assert (
        "functional_simulation_qualification_qualified"
        in module._GITHUB_RELEASE_DECLARATIONS
    )
    assert (
        "functional_simulation_stress_recorded"
        in module._GITHUB_RELEASE_DECLARATIONS
    )
    assert (
        "sparse_native_validation_qualified"
        in module._GITHUB_RELEASE_DECLARATIONS
    )
    assert (
        "sparse_multivariate_validation_qualified"
        in module._GITHUB_RELEASE_DECLARATIONS
    )
    assert (
        "sparse_multivariate_external_sensitivity_recorded"
        in module._GITHUB_RELEASE_DECLARATIONS
    )
    assert (
        "sparse_multivariate_performance_recorded"
        in module._GITHUB_RELEASE_DECLARATIONS
    )

    validation_workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "functional-simulation-validation.yml"
    ).read_text(encoding="utf-8")
    stress_workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "functional-simulation-stress.yml"
    ).read_text(encoding="utf-8")
    sparse_workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "sparse-native-validation.yml"
    ).read_text(encoding="utf-8")
    assert "- main" in validation_workflow
    assert "- main" in stress_workflow
    assert "- main" in sparse_workflow
    assert "- release/0.11-native-simulation" in sparse_workflow


def test_release_workflow_builds_once_and_reuses_exact_artifact():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert workflow.count("python -m build") == 1
    assert "name: release-build-once" in workflow
    assert workflow.count("name: release-dist") >= 2
    assert "uses: pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "environment: testpypi" in workflow
    production_block = workflow.split("  publish-pypi:", 1)[1].split(
        "  resume-pypi:", 1
    )[0]
    resume_block = workflow.split("  resume-pypi:", 1)[1].split(
        "  verify-pypi:", 1
    )[0]
    assert "environment: pypi" in production_block
    assert "environment: pypi" in resume_block
    assert "PYPI_TRUSTED_PUBLISHING_CONFIGURED" in production_block
    assert "PYPI_REQUIRED_REVIEWER_CONFIGURED" in production_block
    assert "skip-existing: true" not in production_block
    assert "skip-existing: true" in resume_block
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


def test_release_workflow_pins_runner_and_uses_node24_actions():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert "runs-on: ubuntu-latest" not in workflow
    assert "runs-on: ubuntu-24.04" in workflow
    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v7" in workflow
    assert "uses: actions/upload-artifact@v7" in workflow
    assert "uses: actions/download-artifact@v8" in workflow
    assert "actions/checkout@v4" not in workflow
    assert "actions/setup-python@v5" not in workflow
    assert "actions/upload-artifact@v4" not in workflow
    assert "actions/download-artifact@v4" not in workflow


def test_release_install_verification_tolerates_index_propagation():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    testpypi_block = workflow.split(
        "  verify-testpypi:", 1
    )[1].split("  production-governance:", 1)[0]
    production_block = workflow.split(
        "  verify-pypi:", 1
    )[1].split("  verify-resume-pypi:", 1)[0]
    resume_block = workflow.split("  verify-resume-pypi:", 1)[1]

    assert "seq 1 20" in testpypi_block
    assert "--no-cache-dir" in testpypi_block
    assert "sleep 20" in testpypi_block

    for block in (production_block, resume_block):
        assert "seq 1 30" in block
        assert "--no-cache-dir" in block
        assert "sleep 20" in block
        assert "bounded propagation window" in block


def test_production_release_requires_explicit_manual_target():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    assert "publish-pypi:" in workflow
    trigger_block = workflow.split("on:", 1)[1].split("jobs:", 1)[0]
    assert "push:" not in trigger_block
    assert "workflow_dispatch:" in trigger_block
    options = workflow.split("options:", 1)[1].split("concurrency:", 1)[0]
    assert "- build-only" in options
    assert "- testpypi" in options
    assert "- production" in options
    assert "- resume-production" in options
    assert "inputs.target == 'production'" in workflow
    assert "inputs.target == 'resume-production'" in workflow
    assert "production-new-version-preflight" in workflow
    assert "verify_pypi_version_unpublished.py" in workflow

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

def test_production_path_fails_on_preexisting_release_or_version():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    production_preflight = workflow.split(
        "  production-preflight:", 1
    )[1].split("  github-release:", 1)[0]
    assert 'gh release view "${TAG}"' in production_preflight
    assert 'git ls-remote --exit-code --tags origin "refs/tags/${TAG}"' in (
        production_preflight
    )
    assert "verify_pypi_version_unpublished.py" in production_preflight

    github_release = workflow.split("  github-release:", 1)[1].split(
        "  resume-release-preflight:", 1
    )[0]
    assert "already exists; retaining it" not in github_release
    assert "gh release create" in github_release


def test_resume_production_requires_existing_matching_release():
    workflow = (
        ROOT / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")

    resume_preflight = workflow.split(
        "  resume-release-preflight:", 1
    )[1].split("  publish-pypi:", 1)[0]
    assert 'gh release view "${TAG}"' in resume_preflight
    assert 'TARGET="$(git rev-list -n 1 "${TAG}")"' in resume_preflight
    assert 'test "${TARGET}" = "${GITHUB_SHA}"' in resume_preflight


def test_pypi_version_preflight_accepts_404(monkeypatch):
    module = _load_script("verify_pypi_version_unpublished.py")

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    module.verify_version_unpublished("eyetrajectoriespy", "0.9.2")


def test_pypi_version_preflight_rejects_existing_version(monkeypatch):
    module = _load_script("verify_pypi_version_unpublished.py")

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda request, timeout: Response(),
    )
    with pytest.raises(RuntimeError, match="already exists on PyPI"):
        module.verify_version_unpublished("eyetrajectoriespy", "0.9.0")


def test_pypi_version_preflight_fails_closed_on_index_error(monkeypatch):
    module = _load_script("verify_pypi_version_unpublished.py")

    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            503,
            "Unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="preflight failed"):
        module.verify_version_unpublished("eyetrajectoriespy", "0.9.2")

