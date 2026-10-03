from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]


def _load_governance():
    path = ROOT / "scripts" / "verify_release_governance.py"
    spec = importlib.util.spec_from_file_location("verify_release_governance", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_1_0_release_governance_requires_frozen_api_boundary():
    module = _load_governance()
    assert "one_dot_zero_api_stability_frozen" in module._GITHUB_RELEASE_DECLARATIONS
    assert "frozen-api-boundary" in module.REQUIRED_CHECKS


def test_1_0_api_boundary_workflow_runs_on_main():
    workflow = (ROOT / ".github" / "workflows" / "one-dot-zero-api-stability.yml").read_text(encoding="utf-8")
    assert "branches: [main]" in workflow
    assert "name: frozen-api-boundary" in workflow
