import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "installed-rc-qualification.yml"
SCRIPT = ROOT / "scripts" / "run_installed_rc_observation.py"
SPARSE_SCRIPT = ROOT / "scripts" / "run_installed_sparse_mfpca_observation.py"
PRODUCT_SCRIPT = ROOT / "scripts" / "run_one_dot_one_product_analyses.py"


def _imported_modules(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return imported


def test_installed_rc_observation_script_parses_and_uses_public_package_only():
    source = SCRIPT.read_text(encoding="utf-8")
    imported = _imported_modules(SCRIPT)

    assert "eyetrajectoriespy" in imported
    assert not any(name.startswith("eyetrajectoriespy.") for name in imported)
    assert "src/eyetrajectoriespy" not in source
    assert "scientific_thresholds_added" in source
    assert '"scientific_thresholds_added": False' in source
    assert '"truth_available_to_estimators": False' in source


def test_installed_sparse_mfpca_script_is_public_observation_only():
    source = SPARSE_SCRIPT.read_text(encoding="utf-8")
    imported = _imported_modules(SPARSE_SCRIPT)

    assert "eyetrajectoriespy" in imported
    assert not any(name.startswith("eyetrajectoriespy.") for name in imported)
    assert "src/eyetrajectoriespy" not in source
    assert "RHO_XY = 0.6" in source
    assert '"scientific_thresholds_added": False' in source
    assert '"recovery_thresholds_applied": False' in source
    assert '"automatic_tuning_performed": False' in source
    assert '"truth_available_to_estimator": False' in source

    required = (
        "FunctionalSimulationScenario",
        "simulate_functional_scenario",
        "fit_sparse_mfpca",
        "evaluate_sparse_mfpca_recovery",
        "functional_recovery_assessment_frame",
        "sparse_mfpca_score_frame",
        "sparse_mfpca_reporting_text",
        "export_portable_result",
        "load_portable_result",
    )
    for name in required:
        assert f"et.{name}" in source

    contract_text = (
        "full_fitted_joint_covariance_plus_measurement_error",
        "cross_covariance_self_symmetrized",
        "yx_estimated_independently",
        "nonportable_fields",
        "source_checkout_imported",
    )
    for text in contract_text:
        assert text in source


def test_installed_rc_workflow_installs_exact_production_artifact_without_editable_source():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'RC_VERSION: "1.1.0rc1"' in workflow
    assert 'RC_VERSION: "1.0.0rc1"' not in workflow
    assert 'RC_VERSION: "0.12.0rc1"' not in workflow
    assert 'RC_VERSION: "0.11.0rc1"' not in workflow
    assert '"eyetrajectoriespy==${RC_VERSION}"' in workflow
    assert "--no-cache-dir" in workflow
    assert "pip install -e" not in workflow
    assert "pip install ." not in workflow
    assert 'cd "${RUNNER_TEMP}/rc-work"' in workflow
    assert 'cd "${RUNNER_TEMP}/rc-matrix-work"' in workflow
    assert "package imported from repository checkout" in workflow
    assert "deep observation imported package from repository checkout" in workflow


def test_installed_rc_workflow_covers_supported_python_and_deep_public_recovery():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'python-version: ["3.11", "3.12", "3.13"]' in workflow
    assert "run_functional_simulation_validation.py" in workflow
    assert "run_functional_simulation_stress.py" in workflow
    assert "run_installed_rc_observation.py" in workflow
    assert "run_installed_sparse_mfpca_observation.py" in workflow
    assert "functional-simulation-validation.json" in workflow
    assert "functional-simulation-stress.json" in workflow
    assert "installed-rc-observation.json" in workflow
    assert "installed-sparse-mfpca-observation.json" in workflow
    assert 'if stress["failure_action"] != "record"' in workflow
    assert "expected_records = 14 * int(stress[" in workflow
    assert "sparse-MFPCA/joint-PACE and complete 1.1 product observation passed" in workflow
    assert 'set(sparse["joint_score_status_counts"]) != {"ok"}' in workflow
    assert "full_fitted_joint_covariance_plus_measurement_error" in workflow
    assert 'portable["nonportable_fields"] != []' in workflow


def test_installed_rc_workflow_runs_complete_one_dot_one_product_observation():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    product_source = PRODUCT_SCRIPT.read_text(encoding="utf-8")

    assert "scripts/run_one_dot_one_product_analyses.py" in workflow
    assert "one-dot-one-product-analyses" in workflow
    assert "1.1-r3-canonical-end-to-end-product-analyses" in workflow
    assert 'product["package_version"] != os.environ["RC_VERSION"]' in workflow
    assert 'product["public_supported_api_only"] is not True' in workflow
    assert 'product["known_truth_qualification_simulator_used"] is not False' in workflow
    assert 'product["release_blocking_friction_count"] != 0' in workflow
    assert 'uni["bandwidth_eligible_candidates"] < 1' in workflow
    assert 'uni["conditional_uncertainty_failures"] != 0' in workflow
    assert 'uni["conformal_calibration_units"] != 10' in workflow
    assert 'planar["paired_uncertainty_failures"] != 0' in workflow
    assert 'planar["asynchronous_score_failures"] != 0' in workflow
    assert 'planar["nearest_neighbour_synchronization_performed"] is not False' in workflow
    assert 'multi["repeated_participants"] != 12' in workflow
    assert 'multi["blup_failures"] != 0' in workflow

    required_module_surfaces = (
        "select_sparse_fpca_bandwidths",
        "sparse_fpca_score_uncertainty",
        "diagnose_observation_process",
        "select_sparse_mfpca_bandwidths",
        "sparse_mfpca_score_uncertainty",
        "fit_sparse_mfpca_async",
        "fit_sparse_multilevel_fpca",
        "sparse_fpca_partial_trajectory_prediction",
        "calibrate_sparse_fpca_partial_prediction_conformal",
        "sparse_fpca_conformal_prediction_band",
    )
    for name in required_module_surfaces:
        assert name in product_source


def test_installed_rc_workflow_retains_environment_and_immutable_evidence():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in workflow
    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v7" in workflow
    assert "uses: actions/upload-artifact@v7" in workflow
    assert "ImageOS" in workflow
    assert "ImageVersion" in workflow
    assert "deep-import-environment.json" in workflow
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
