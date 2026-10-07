import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _runner():
    return _load(
        ROOT
        / "scripts"
        / "run_bayesian_fpca_replication.py",
        "run_bayesian_fpca_replication",
    )


def _evaluator():
    return _load(
        ROOT
        / "scripts"
        / "evaluate_bayesian_fpca_replication.py",
        "evaluate_bayesian_fpca_replication",
    )


def test_b2_design_is_frozen_before_execution():
    runner = _runner()

    assert runner.PRIMARY_REPLICATES == 16
    assert runner.FAIRNESS_REPLICATES == 4
    assert runner.K_CANDIDATES == (
        5,
        6,
        7,
        8,
        9,
    )
    assert runner.BANDWIDTH_FACTORS == (
        0.75,
        1.0,
        1.25,
    )
    assert {
        scenario.name
        for scenario in runner.SCENARIOS
    } == {
        "univariate_moderate",
        "univariate_extreme_sparse",
        "univariate_low_n",
        "univariate_near_tied",
        "univariate_localized",
        "univariate_informative_time",
        "planar_paired",
        "planar_async",
    }
    assert runner.FAIRNESS_SCENARIOS == {
        "univariate_extreme_sparse",
        "univariate_low_n",
        "univariate_near_tied",
        "univariate_localized",
        "planar_paired",
    }

    by_name = {
        scenario.name: scenario
        for scenario in runner.SCENARIOS
    }
    assert (
        by_name["univariate_low_n"].n_curves
        == 14
    )
    assert (
        by_name[
            "univariate_low_n"
        ].eigenvalues
        == (1.0, 0.4)
    )
    assert (
        by_name[
            "univariate_near_tied"
        ].n_curves
        == 32
    )
    assert (
        by_name[
            "univariate_near_tied"
        ].eigenvalues
        == (1.0, 0.9)
    )
    assert (
        by_name[
            "univariate_localized"
        ].truth_family
        == "localized_triangular"
    )
    assert (
        by_name[
            "univariate_informative_time"
        ].observation_mechanism
        == "logistic_candidate_time"
    )


def test_localized_truth_is_nonharmonic_and_disjoint():
    runner = _runner()
    grid = np.linspace(
        0.02,
        0.98,
        1001,
    )
    functions = runner._localized_modes(grid)

    assert functions.shape == (
        2,
        grid.size,
        1,
    )
    first = functions[0, :, 0]
    second = functions[1, :, 0]
    assert np.all(first >= 0)
    assert np.all(second >= 0)
    assert np.max(first * second) == pytest.approx(
        0.0
    )
    assert np.trapz(
        first**2,
        grid,
    ) == pytest.approx(
        1.0,
        rel=2e-3,
    )
    assert np.trapz(
        second**2,
        grid,
    ) == pytest.approx(
        1.0,
        rel=2e-3,
    )


def test_replicated_aggregation_is_descriptive_only():
    evaluator = _evaluator()
    records = [
        {
            "native": {
                "status": "ok",
                "mean_ise": 2.0,
                "reconstruction_ise": 4.0,
                "functional_subspace_min_cosine": 0.90,
                "score_subspace_min_cosine": 0.91,
                "spectrum_pve_l1_error": 0.20,
                "score_failure_rate": 0.0,
            },
            "bayes": {
                "status": "ok",
                "mean_ise": 1.0,
                "reconstruction_ise": 2.0,
                "functional_subspace_min_cosine": 0.95,
                "score_subspace_min_cosine": 0.96,
                "spectrum_pve_l1_error": 0.10,
                "score_failure_rate": 0.0,
            },
        },
        {
            "native": {
                "status": "failed",
                "error": "fixture stress",
            },
            "bayes": {
                "status": "ok",
                "mean_ise": 1.5,
                "reconstruction_ise": 2.5,
                "functional_subspace_min_cosine": 0.94,
                "score_subspace_min_cosine": 0.95,
                "spectrum_pve_l1_error": 0.12,
                "score_failure_rate": 0.0,
            },
        },
    ]

    native = evaluator._aggregate(
        records,
        "native",
    )
    bayes = evaluator._aggregate(
        records,
        "bayes",
    )
    paired = evaluator._paired(
        records,
        "native",
        "bayes",
    )

    assert native["n_replicates"] == 2
    assert native["n_success"] == 1
    assert native["fit_failure_rate"] == pytest.approx(
        0.5
    )
    assert bayes["n_success"] == 2
    assert paired["n_paired"] == 1
    assert paired["descriptive_only"] is True
    assert (
        paired["reconstruction_ise"][
            "fraction_right_in_favorable_direction"
        ]
        == pytest.approx(1.0)
    )
    assert (
        paired[
            "functional_subspace_min_cosine"
        ][
            "fraction_right_in_favorable_direction"
        ]
        == pytest.approx(1.0)
    )


def test_b2_workflow_retains_predeclared_contract_and_r_provenance():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "bayesian-fpca-replication.yml"
    ).read_text(encoding="utf-8")

    for token in (
        "--replicates 16",
        "--fairness-replicates 4",
        "BAYESFPCA_COMMIT",
        "f05b0615632cffe5c63838858d9a956af6588a73",
        "r-package-versions.csv",
        "r-session-info.txt",
        "r-runtime-details.txt",
        "sessionInfo()",
        "extSoftVersion()",
        "b4_decision",
        "p_values_computed",
        "qualification_thresholds_introduced",
    ):
        assert token in workflow

    assert (
        'test "$(git -C external-bayesFPCA rev-parse HEAD)" = "$BAYESFPCA_COMMIT"'
        in workflow
    )
