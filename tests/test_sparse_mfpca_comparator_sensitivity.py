import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _runner():
    return _load(
        ROOT / "scripts" / "run_sparse_mfpca_comparator_sensitivity.py",
        "run_sparse_mfpca_comparator_sensitivity",
    )


def _evaluator():
    return _load(
        ROOT / "scripts" / "evaluate_sparse_mfpca_mgsfpca.py",
        "evaluate_sparse_mfpca_mgsfpca",
    )


def test_two_stage_benchmark_uses_declared_marginal_ranks_without_selection():
    runner = _runner()
    simulation = runner._simulate(seed=16100, n_participants=12)

    rank_one = runner.two_stage_benchmark(simulation, 1)
    rank_two = runner.two_stage_benchmark(simulation, 2)

    assert rank_one["marginal_rank"] == 1
    assert rank_two["marginal_rank"] == 2
    assert rank_one["eigenfunctions"].shape[2] == 2
    assert rank_two["eigenfunctions"].shape[2] == 2
    assert rank_one["scores"].shape[0] == 12
    assert rank_two["scores"].shape[0] == 12
    assert rank_one["eigenvalues"].size <= 2
    assert rank_two["eigenvalues"].size <= 4
    assert rank_one["provenance"]["automatic_rank_selection"] is False
    assert rank_two["provenance"]["automatic_rank_selection"] is False
    assert rank_one["provenance"]["architecture_winner_selected"] is False
    assert rank_two["provenance"]["architecture_winner_selected"] is False

    np.testing.assert_allclose(
        rank_one["covariance_blocks"]["cyx"],
        rank_one["covariance_blocks"]["cxy"].T,
    )
    np.testing.assert_allclose(
        rank_two["covariance_blocks"]["cyx"],
        rank_two["covariance_blocks"]["cxy"].T,
    )


@pytest.mark.parametrize("rank", [0, 3])
def test_two_stage_benchmark_rejects_undeclared_marginal_rank(rank):
    runner = _runner()
    simulation = runner._simulate(seed=16101, n_participants=8)
    with pytest.raises(ValueError, match="marginal_rank"):
        runner.two_stage_benchmark(simulation, rank)


def test_comparator_runner_declares_descriptive_no_winner_contract():
    runner = _runner()

    assert runner.MARGINAL_RANKS == (1, 2)
    assert runner.RHO_XY == pytest.approx(0.6)
    source = (
        ROOT / "scripts" / "run_sparse_mfpca_comparator_sensitivity.py"
    ).read_text(encoding="utf-8")
    assert '"architecture_winner_selected": False' in source
    assert '"automatic_rank_selection": False' in source
    assert "mGSFPCA" in source


def _write_matrix(path: Path, values: np.ndarray) -> None:
    pd.DataFrame(values).to_csv(path, index=False)


def test_external_evaluator_uses_invariant_subspaces_and_never_claims_equivalence(
    tmp_path,
):
    evaluator = _evaluator()
    grid = np.array([0.0, 0.5, 1.0])
    weights = np.array([0.25, 0.5, 0.25])
    mode_x = np.array([0.0, np.sqrt(2.0), 0.0])
    mode_y = np.array([0.0, 0.0, np.sqrt(2.0)])
    functions = np.array(
        [
            np.column_stack([mode_x, np.zeros_like(mode_x)]),
            np.column_stack([np.zeros_like(mode_y), mode_y]),
        ]
    )
    scores = np.array(
        [
            [1.0, -1.0],
            [-1.0, 1.0],
            [0.5, 0.25],
            [-0.5, -0.25],
        ]
    )
    ids = ["a", "b", "c", "d"]
    payload = {
        "contract": {
            "equivalence_claim": False,
            "automatic_model_selection": False,
            "architecture_winner_selected": False,
        },
        "rho_xy": 0.6,
        "truth_grid": grid.tolist(),
        "eigenvalues": [1.0, 0.5],
        "eigenfunctions": functions.tolist(),
        "scores": scores.tolist(),
        "curve_ids": ids,
    }
    (tmp_path / "external_fixture_truth.json").write_text(
        __import__("json").dumps(payload),
        encoding="utf-8",
    )

    x = functions[:, :, 0].T
    y = functions[:, :, 1].T
    _write_matrix(tmp_path / "native_eigenfunctions_x.csv", x)
    _write_matrix(tmp_path / "native_eigenfunctions_y.csv", y)
    _write_matrix(tmp_path / "mgsfpca_eigenfunctions_x.csv", x)
    _write_matrix(tmp_path / "mgsfpca_eigenfunctions_y.csv", y)

    score_frame = pd.DataFrame(
        {"ID": ids[::-1], "s1": scores[::-1, 0], "s2": scores[::-1, 1]}
    )
    score_frame.to_csv(tmp_path / "native_scores.csv", index=False)
    score_frame.to_csv(tmp_path / "mgsfpca_scores.csv", index=False)
    pd.DataFrame(
        {"component": [1, 2], "eigenvalue": [1.0, 0.5]}
    ).to_csv(tmp_path / "native_eigenvalues.csv", index=False)
    pd.DataFrame(
        {"component": [1, 2], "eigenvalue": [1.0, 0.5]}
    ).to_csv(tmp_path / "mgsfpca_eigenvalues.csv", index=False)

    result = evaluator.evaluate(tmp_path)

    assert result["equivalence_claim"] is False
    assert result["architecture_winner_selected"] is False
    assert result["comparator_version"] == "0.2.2"
    np.testing.assert_allclose(
        result["native_truth_functional_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["mgsfpca_native_functional_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["mgsfpca_native_score_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )


def test_external_evaluator_rejects_equivalence_fixture_contract(tmp_path):
    evaluator = _evaluator()
    payload = {
        "contract": {"equivalence_claim": True},
        "rho_xy": 0.6,
        "truth_grid": [0.0, 1.0],
        "eigenvalues": [1.0],
        "eigenfunctions": [[[1.0, 0.0], [1.0, 0.0]]],
        "scores": [[1.0], [-1.0], [0.5]],
        "curve_ids": ["a", "b", "c"],
    }
    (tmp_path / "external_fixture_truth.json").write_text(
        __import__("json").dumps(payload),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="forbid exact equivalence"):
        evaluator.evaluate(tmp_path)
