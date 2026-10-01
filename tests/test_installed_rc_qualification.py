import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "installed-rc-qualification.yml"
SCRIPT = ROOT / "scripts" / "run_installed_rc_observation.py"


def test_installed_rc_observation_script_parses_and_uses_public_package_only():
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)

    assert "eyetrajectoriespy" in imported
    assert not any(
        name.startswith("eyetrajectoriespy.")
        for name in imported
    )
    assert "src/eyetrajectoriespy" not in source
    assert "scientific_thresholds_added" in source
    assert '"scientific_thresholds_added": False' in source
    assert '"truth_available_to_estimators": False' in source


def test_installed_rc_workflow_installs_exact_production_artifact_without_editable_source():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'RC_VERSION: "0.12.0rc1"' in workflow
    assert 'RC_VERSION: "0.11.0rc1"' not in workflow
    assert '"eyetrajectoriespy==${RC_VERSION}"' in workflow
    assert "--no-cache-dir" in workflow
    assert "pip install -e" not in workflow
    assert "pip install ." not in workflow
    assert 'cd "${RUNNER_TEMP}/rc-work"' in workflow
    assert 'cd "${RUNNER_TEMP}/rc-matrix-work"' in workflow
    assert "package imported from repository checkout" in workflow


def test_installed_rc_workflow_covers_supported_python_and_deep_public_recovery():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'python-version: ["3.11", "3.12", "3.13"]' in workflow
    assert "run_functional_simulation_validation.py" in workflow
    assert "run_functional_simulation_stress.py" in workflow
    assert "run_installed_rc_observation.py" in workflow
    assert "functional-simulation-validation.json" in workflow
    assert "functional-simulation-stress.json" in workflow
    assert "installed-rc-observation.json" in workflow
    assert 'if stress["failure_action"] != "record"' in workflow
    assert "expected_records = 14 * int(stress[" in workflow


def test_installed_rc_workflow_retains_environment_and_immutable_evidence():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in workflow
    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v7" in workflow
    assert "uses: actions/upload-artifact@v7" in workflow
    assert "ImageOS" in workflow
    assert "ImageVersion" in workflow
    assert "pip-freeze.txt" in workflow
    assert "pip-show-eyetrajectoriespy.txt" in workflow
    assert "SHA256SUMS" in workflow
    assert "retention-days: 90" in workflow


def test_installed_rc_observation_covers_decision_relevant_public_surfaces():
    source = SCRIPT.read_text(encoding="utf-8")

    required = (
        "FunctionalSimulationScenario",
        "simulate_functional_scenario",
        "fit_fpca",
        "evaluate_fpca_recovery",
        "fit_functional_mixed_effects_regression",
        "evaluate_functional_mixed_effects_recovery",
        "register_to_landmarks",
        "evaluate_registration_recovery",
        "export_portable_result",
        "load_portable_result",
        "functional_simulation_reporting_text",
        "functional_recovery_reporting_text",
        "plot_functional_simulation_curve",
        "capture_environment",
    )
    for name in required:
        assert f"et.{name}" in source
