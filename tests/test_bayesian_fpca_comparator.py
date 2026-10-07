import importlib.util
import json
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
        ROOT / "scripts" / "run_bayesian_fpca_comparator.py",
        "run_bayesian_fpca_comparator",
    )


def _evaluator():
    return _load(
        ROOT / "scripts" / "evaluate_bayesian_fpca_comparator.py",
        "evaluate_bayesian_fpca_comparator",
    )


def test_b1_scenario_matrix_and_external_only_contract():
    runner = _runner()

    names = {scenario.name for scenario in runner.SCENARIOS}
    assert names == {
        "univariate_moderate",
        "univariate_extreme_sparse",
        "univariate_low_n_near_tied",
        "planar_paired",
        "planar_async",
    }
    assert runner.BAYESFPCA_COMMIT == (
        "f05b0615632cffe5c63838858d9a956af6588a73"
    )
    source = (
        ROOT / "scripts" / "run_bayesian_fpca_comparator.py"
    ).read_text(encoding="utf-8")
    assert "source_code_ported" in source
    assert '"external_runtime_backend": False' in source
    assert '"equivalence_claim": False' in source
    assert '"architecture_winner_selected": False' in source


def _write_method(
    root: Path,
    prefix: str,
    grid: np.ndarray,
    functions: np.ndarray,
    scores: np.ndarray,
    eigenvalues: np.ndarray,
    ids: list[str],
):
    pd.DataFrame({"time": grid, "x": np.zeros_like(grid)}).to_csv(
        root / f"{prefix}_mean.csv",
        index=False,
    )
    rows = []
    for component in range(functions.shape[0]):
        for time_value, value in zip(
            grid,
            functions[component, :, 0],
            strict=True,
        ):
            rows.append(
                {
                    "component": component + 1,
                    "dimension": "x",
                    "time": time_value,
                    "value": value,
                }
            )
    pd.DataFrame(rows).to_csv(
        root / f"{prefix}_eigenfunctions.csv",
        index=False,
    )
    score_frame = pd.DataFrame(
        scores,
        columns=["PC1", "PC2"],
    )
    score_frame.insert(0, "curve_id", ids)
    score_frame.to_csv(root / f"{prefix}_scores.csv", index=False)
    pd.DataFrame(
        {
            "component": [1, 2],
            "eigenvalue": eigenvalues,
        }
    ).to_csv(root / f"{prefix}_eigenvalues.csv", index=False)


def _identity_fixture(tmp_path: Path) -> Path:
    scenario_dir = tmp_path / "scenarios" / "identity"
    scenario_dir.mkdir(parents=True)

    grid = np.array([0.0, 0.5, 1.0])
    functions = np.array(
        [
            [[2.0], [0.0], [0.0]],
            [[0.0], [np.sqrt(2.0)], [0.0]],
        ]
    )
    scores = np.array(
        [
            [1.0, -0.5],
            [-1.0, 0.5],
            [0.5, 1.0],
            [-0.5, -1.0],
        ]
    )
    ids = ["a", "b", "c", "d"]
    eigenvalues = np.array([1.0, 0.5])
    mean = np.zeros((grid.size, 1))
    latent = mean[None, :, :] + np.einsum(
        "nk,kgd->ngd",
        scores,
        functions,
    )
    truth = {
        "scenario": "identity",
        "design": "univariate",
        "truth_grid": grid.tolist(),
        "dimension_names": ["x"],
        "curve_ids": ids,
        "eigenvalues": eigenvalues.tolist(),
        "eigenfunctions": functions.tolist(),
        "scores": scores.tolist(),
        "mean": mean.tolist(),
        "latent_on_truth_grid": latent.tolist(),
        "contract": {
            "equivalence_claim": False,
            "architecture_winner_selected": False,
            "external_runtime_backend": False,
        },
    }
    (scenario_dir / "truth.json").write_text(
        json.dumps(truth),
        encoding="utf-8",
    )
    _write_method(
        scenario_dir,
        "native",
        grid,
        functions,
        scores,
        eigenvalues,
        ids,
    )
    _write_method(
        scenario_dir,
        "bayesfpca",
        grid,
        functions,
        scores,
        eigenvalues,
        ids,
    )
    pd.DataFrame(
        {
            "scenario": ["identity"],
            "algorithm": ["run_mfvb_fpca"],
            "package_version": ["0.1.0"],
            "remote_sha": [
                "f05b0615632cffe5c63838858d9a956af6588a73"
            ],
            "elapsed_seconds": [1.0],
            "n_iter": [10],
            "final_elbo": [-100.0],
            "fixed_score_variance": [True],
        }
    ).to_csv(scenario_dir / "bayesfpca_metadata.csv", index=False)
    covariance_rows = []
    for curve_id in ids:
        for a in (1, 2):
            for b in (1, 2):
                covariance_rows.append(
                    {
                        "curve_id": curve_id,
                        "component_i": a,
                        "component_j": b,
                        "covariance": 0.1 if a == b else 0.0,
                    }
                )
    pd.DataFrame(covariance_rows).to_csv(
        scenario_dir / "bayesfpca_score_covariance.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "scenario": ["identity"],
            "design": ["univariate"],
            "n_curves": [4],
            "n_dimensions": [1],
            "n_components": [2],
            "spline_basis_size": [7],
        }
    ).to_csv(tmp_path / "manifest.csv", index=False)
    manifest = {
        "external_comparator_version": "0.1.0",
        "external_comparator_commit": (
            "f05b0615632cffe5c63838858d9a956af6588a73"
        ),
        "external_comparator_license": "GPL-3.0-or-later",
        "external_runtime_backend": False,
        "source_code_ported": False,
        "equivalence_claim": False,
        "architecture_winner_selected": False,
    }
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return tmp_path


def test_evaluator_uses_invariant_subspaces_and_no_winner(tmp_path):
    evaluator = _evaluator()
    root = _identity_fixture(tmp_path)

    payload = evaluator.evaluate(root)
    result = payload["scenarios"][0]

    assert payload["equivalence_claim"] is False
    assert payload["architecture_winner_selected"] is False
    assert payload["external_runtime_backend"] is False
    assert payload["source_code_ported"] is False
    assert result["native"]["mean_ise"] == pytest.approx(0.0)
    assert result["bayesfpca"]["mean_ise"] == pytest.approx(0.0)
    assert result["native"]["reconstruction_ise"] == pytest.approx(0.0)
    assert result["bayesfpca"]["reconstruction_ise"] == pytest.approx(0.0)
    np.testing.assert_allclose(
        result["native"]["truth_functional_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["bayesfpca"]["truth_functional_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result["native_bayesfpca_score_subspace_principal_cosines"],
        1.0,
        atol=1e-12,
    )
    assert (
        result["uncertainty_contract"][
            "direct_uncertainty_superiority_claim"
        ]
        is False
    )


def test_evaluator_rejects_equivalence_claim(tmp_path):
    evaluator = _evaluator()
    root = _identity_fixture(tmp_path)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["equivalence_claim"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="forbid equivalence"):
        evaluator.evaluate(root)
