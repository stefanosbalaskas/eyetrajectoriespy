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
        "univariate_moderate",
        "univariate_extreme_sparse",
        "univariate_low_n",
        "univariate_near_tied",
        "univariate_localized",
        "univariate_informative_time",
        "planar_paired",
        "planar_async",
    }
    assert runner.DEFAULT_REPLICATES == 16
    assert runner.K_SENSITIVITY == (5, 6, 7, 8, 9)
    assert runner.FAIRNESS_REPLICATES == 4
    assert runner.FAIRNESS_SCENARIOS == {
        "univariate_extreme_sparse",
        "univariate_low_n",
        "univariate_near_tied",
        "univariate_localized",
        "planar_paired",
    }

    low_n = next(x for x in runner.SCENARIOS if x.name == "univariate_low_n")
    near_tied = next(
        x for x in runner.SCENARIOS if x.name == "univariate_near_tied"
    )
    assert low_n.n_curves == 14
    assert (low_n.samples_min, low_n.samples_max) == (12, 18)
    assert (low_n.mean_bandwidth, low_n.covariance_bandwidth) == (0.22, 0.32)
    assert near_tied.n_curves == 32
    assert (near_tied.samples_min, near_tied.samples_max) == (12, 18)
    assert (near_tied.mean_bandwidth, near_tied.covariance_bandwidth) == (
        0.20,
        0.30,
    )
    assert low_n.eigenvalues != near_tied.eigenvalues

    localized = next(
        x for x in runner.SCENARIOS if x.name == "univariate_localized"
    )
    assert localized.truth_family == "localized"
    assert (localized.mean_bandwidth, localized.covariance_bandwidth) == (
        0.18,
        0.28,
    )

    informative = next(
        x
        for x in runner.SCENARIOS
        if x.name == "univariate_informative_time"
    )
    assert informative.observation_mechanism != "independent_irregular"
    assert (informative.mean_bandwidth, informative.covariance_bandwidth) == (
        0.20,
        0.30,
    )


def test_localized_basis_is_finite_and_nearly_orthonormal():
    runner = _load(
        ROOT / "scripts" / "run_bayesian_fpca_replication.py",
        "run_bayesian_fpca_replication_localized",
    )
    scenario = next(
        x for x in runner.SCENARIOS if x.name == "univariate_localized"
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
        'abind = list(version = "1.4.8"',
        'ellipse = list(version = "0.5.0"',
        'magic = list(version = "1.6.1.1"',
        'matrixcalc = list(version = "1.0.6"',
        'pracma = list(version = "2.4.6"',
    ):
        assert token in lock

    assert 'r-version: "4.6.1"' in workflow
    assert "run_sparse_score_uncertainty_validation.py" in workflow
    assert "--n-curves 500" in workflow
    assert "--replicates 16" in workflow
    assert "bayesfpca_k_sensitivity" in workflow
    assert "[5, 6, 7, 8, 9]" in workflow
    assert "[0.75, 1.0, 1.25]" in workflow
    assert "direct_covariance_magnitude_comparison_performed" in workflow


def test_async_secondary_native_tuning_is_not_silently_invented():
    runner_source = (
        ROOT / "scripts" / "run_bayesian_fpca_replication.py"
    ).read_text(encoding="utf-8")
    assert 'elif scenario.design == "planar_paired":' in runner_source
    assert "return None, None" in runner_source
    assert '"available_for_async_planar": False' in runner_source

def test_definitive_fairness_selection_is_predeclared_and_elbo_based():
    runner_source = (
        ROOT / "scripts" / "run_bayesian_fpca_replication.py"
    ).read_text(encoding="utf-8")
    r_source = (
        ROOT / "validation" / "bayesian_fpca" / "run_bayesfpca_replication.R"
    ).read_text(encoding="utf-8")

    assert "multipliers = (0.75, 1.00, 1.25)" in runner_source
    assert "replicate > FAIRNESS_REPLICATES" in runner_source
    assert "scenario.name not in FAIRNESS_SCENARIOS" in runner_source
    assert "K_values <- if (fairness) 5L:9L else 7L" in r_source
    assert 'criterion = "maximum_final_elbo"' in r_source

