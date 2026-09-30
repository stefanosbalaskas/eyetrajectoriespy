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


def _stress():
    return _load(
        ROOT / "scripts" / "run_sparse_mfpca_observation_stress.py",
        "run_sparse_mfpca_observation_stress",
    )


def _performance():
    return _load(
        ROOT / "scripts" / "run_sparse_mfpca_performance.py",
        "run_sparse_mfpca_performance",
    )


def test_observation_stress_declares_descriptive_no_selection_contract():
    module = _stress()

    assert module.RHO_XY == pytest.approx(0.6)
    assert module.REPLICATES == 3
    assert module.MECHANISMS == (
        "none",
        "mcar",
        "signal_dependent_x_loss",
        "signal_dependent_y_loss",
        "eccentricity_dependent_loss",
        "velocity_dependent_loss",
        "phase_dependent_loss",
    )

    source = (
        ROOT / "scripts" / "run_sparse_mfpca_observation_stress.py"
    ).read_text(encoding="utf-8")
    assert '"threshold_gate_applied": False' in source
    assert '"parameter_selection_performed": False' in source
    assert "paired x/y coordinates retained on the same native timestamps" in source


def test_observation_stress_summary_is_descriptive_and_mechanism_scoped():
    module = _stress()
    frame = pd.DataFrame(
        {
            "mechanism": ["mcar", "mcar", "signal_dependent_x_loss"],
            "status": ["ok", "fit_or_assessment_failed", "ok"],
            "actual_loss_fraction": [0.2, 0.21, 0.19],
            "mean_ise": [0.1, np.nan, 0.2],
            "joint_covariance_ise": [0.3, np.nan, 0.4],
            "cxy_ise": [0.05, np.nan, 0.06],
            "minimum_subspace_principal_cosine": [0.9, np.nan, 0.8],
            "median_score_correlation": [0.85, np.nan, 0.75],
            "reconstruction_ise": [0.2, np.nan, 0.3],
            "score_failure_rate": [0.0, np.nan, 0.1],
            "score_condition_number_q95": [100.0, np.nan, 200.0],
            "psd_relative_operator_correction": [0.01, np.nan, 0.02],
        }
    )

    summary = module._summary(frame)

    assert set(summary["mechanism"]) == {
        "mcar",
        "signal_dependent_x_loss",
    }
    mcar = summary.loc[summary["mechanism"] == "mcar"].iloc[0]
    assert mcar["mean_ise"] == pytest.approx(0.1)


def test_sparse_mfpca_performance_cases_are_planar_and_noncomparative():
    module = _performance()

    assert set(module.CASES) == {
        "very_sparse_planar",
        "moderate_planar",
        "irregular_rich_planar",
    }
    eigenvalues, eigenfunctions = module._design()
    assert len(eigenvalues) == len(eigenfunctions) == 4
    assert all(value > 0 for value in eigenvalues)
    assert list(eigenvalues) == sorted(eigenvalues, reverse=True)

    source = (
        ROOT / "scripts" / "run_sparse_mfpca_performance.py"
    ).read_text(encoding="utf-8")
    assert '"comparative_benchmark": False' in source
    assert '"speed_threshold_applied": False' in source
    assert "No cross-package" in source


def test_sparse_mfpca_performance_requires_three_repeats(tmp_path):
    module = _performance()

    with pytest.raises(ValueError, match="at least three repeats"):
        module._run_parent(
            2,
            tmp_path / "performance.json",
        )
