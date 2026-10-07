import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_b2_b3_scenario_matrix_separates_requested_regimes():
    runner = _load(
        ROOT / "scripts" / "run_bayesian_fpca_replication.py",
        "run_bayesian_fpca_replication",
    )

    names = {scenario.name for scenario in runner.SCENARIOS}
    assert names == {
        "harmonic_moderate",
        "harmonic_extreme_sparse",
        "harmonic_low_n",
        "harmonic_near_tied",
        "localized_moderate",
        "harmonic_informative_observation",
        "planar_paired",
        "planar_async",
    }
    assert runner.DEFAULT_REPLICATES == 5
    assert runner.K_SENSITIVITY == (5, 7, 9)

    low_n = next(x for x in runner.SCENARIOS if x.name == "harmonic_low_n")
    near_tied = next(
        x for x in runner.SCENARIOS if x.name == "harmonic_near_tied"
    )
    assert low_n.n_curves < near_tied.n_curves
    assert low_n.eigenvalues != near_tied.eigenvalues

    localized = next(
        x for x in runner.SCENARIOS if x.name == "localized_moderate"
    )
    assert localized.truth_family == "localized"

    informative = next(
        x
        for x in runner.SCENARIOS
        if x.name == "harmonic_informative_observation"
    )
    assert informative.observation_mechanism != "independent_irregular"


def test_localized_basis_is_finite_and_nearly_orthonormal():
    runner = _load(
        ROOT / "scripts" / "run_bayesian_fpca_replication.py",
        "run_bayesian_fpca_replication_localized",
    )
    scenario = next(
        x for x in runner.SCENARIOS if x.name == "localized_moderate"
    )
    functions = runner._modes(runner.GRID, scenario)
    weights = runner._trap_weights(runner.GRID)
    gram = np.einsum(
        "kgd,lgd,g->kl",
        functions,
        functions,
        weights,
        optimize=True,
    )
    assert np.all(np.isfinite(functions))
    np.testing.assert_allclose(gram, np.eye(2), atol=0.04)


def test_b2_b3_contract_forbids_premature_b4_and_truth_tuning(tmp_path):
    evaluator = _load(
        ROOT / "scripts" / "evaluate_bayesian_fpca_replication.py",
        "evaluate_bayesian_fpca_replication",
    )

    manifest = {
        "b1_evidence_immutable": True,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
        "automatic_promotion_decision": False,
        "b4_decision_recorded": True,
    }
    (tmp_path / "replication_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    (tmp_path / "replication_manifest.csv").write_text(
        "scenario,replicate,seed,design,truth_family,observation_mechanism,"
        "n_curves,n_dimensions,n_components,primary_spline_basis_size,"
        "k_sensitivity,relative_path\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="b4_decision_recorded"):
        evaluator.evaluate(tmp_path)


def test_locked_r_environment_is_exact_not_latest_cran():
    lock = (
        ROOT
        / "validation"
        / "bayesian_fpca"
        / "install_locked_r_environment.R"
    ).read_text(encoding="utf-8")
    workflow = (
        ROOT / ".github" / "workflows" / "bayesian-fpca-b2-b3.yml"
    ).read_text(encoding="utf-8")

    for token in (
        'ellipse = list(version = "0.5.0"',
        'magic = list(version = "1.6.1.1"',
        'matrixcalc = list(version = "1.0.6"',
        'pracma = list(version = "2.4.6"',
    ):
        assert token in lock

    assert 'r-version: "4.6.1"' in workflow
    assert "run_sparse_score_uncertainty_validation.py" in workflow
    assert "--n-curves 200" in workflow
    assert "--replicates 5" in workflow
    assert "bayesfpca_k_sensitivity" in workflow
    assert "direct_covariance_magnitude_comparison_performed" in workflow


def test_async_secondary_native_tuning_is_not_silently_invented():
    runner_source = (
        ROOT / "scripts" / "run_bayesian_fpca_replication.py"
    ).read_text(encoding="utf-8")
    assert 'elif scenario.design == "planar_paired":' in runner_source
    assert "return None, None" in runner_source
    assert '"available_for_async_planar": False' in runner_source
