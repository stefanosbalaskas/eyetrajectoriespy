import importlib.util
from pathlib import Path

import numpy as np
import pytest

from eyetrajectoriespy import (
    FunctionalSimulationScenario,
    simulate_functional_scenario,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    path = ROOT / "scripts" / "run_sparse_mfpca_recovery_validation.py"
    spec = importlib.util.spec_from_file_location(
        "run_sparse_mfpca_recovery_validation",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _truth_cxy(truth):
    functions = np.asarray(truth.eigenfunctions, dtype=float)
    return np.einsum(
        "k,ks,kt->st",
        np.asarray(truth.eigenvalues, dtype=float),
        functions[:, :, 0],
        functions[:, :, 1],
        optimize=True,
    )


def test_rho_design_supports_negative_coupling_and_preserves_positive_spectrum():
    runner = _load_runner()
    negative_values, negative_modes = runner.planar_rho_design(-0.6)
    positive_values, positive_modes = runner.planar_rho_design(0.6)

    assert len(negative_values) == len(negative_modes) == 4
    assert len(positive_values) == len(positive_modes) == 4
    assert all(value > 0 for value in negative_values)
    assert list(negative_values) == sorted(negative_values, reverse=True)

    grid = np.linspace(0.0, 1.0, 31)
    neg_scenario = FunctionalSimulationScenario(
        name="neg",
        truth_grid=grid,
        eigenvalues=negative_values,
        n_participants=4,
        dimension_names=("x", "y"),
        observation_design="irregular",
        samples_per_curve=8,
        measurement_noise_sd=(0.0, 0.0),
        replicates=1,
        seed_start=7,
    )
    pos_scenario = FunctionalSimulationScenario(
        name="pos",
        truth_grid=grid,
        eigenvalues=positive_values,
        n_participants=4,
        dimension_names=("x", "y"),
        observation_design="irregular",
        samples_per_curve=8,
        measurement_noise_sd=(0.0, 0.0),
        replicates=1,
        seed_start=7,
    )
    negative = simulate_functional_scenario(
        neg_scenario,
        mean=runner._mean_planar,
        eigenfunctions=negative_modes,
    )
    positive = simulate_functional_scenario(
        pos_scenario,
        mean=runner._mean_planar,
        eigenfunctions=positive_modes,
    )

    neg_cxy = _truth_cxy(negative.truth)
    pos_cxy = _truth_cxy(positive.truth)
    np.testing.assert_allclose(neg_cxy, -pos_cxy, atol=1e-12)

    neg_xx = np.einsum(
        "k,ks,kt->st",
        negative.truth.eigenvalues,
        negative.truth.eigenfunctions[:, :, 0],
        negative.truth.eigenfunctions[:, :, 0],
    )
    pos_xx = np.einsum(
        "k,ks,kt->st",
        positive.truth.eigenvalues,
        positive.truth.eigenfunctions[:, :, 0],
        positive.truth.eigenfunctions[:, :, 0],
    )
    np.testing.assert_allclose(neg_xx, pos_xx, atol=1e-12)


@pytest.mark.parametrize("rho", [-1.0, 1.0, np.nan])
def test_rho_design_fails_closed_outside_open_unit_interval(rho):
    runner = _load_runner()
    with pytest.raises(ValueError, match="rho_xy"):
        runner.planar_rho_design(rho)


def test_asymmetric_design_is_genuinely_directional_not_implementation_only():
    runner = _load_runner()
    eigenvalues, eigenfunctions = runner.asymmetric_cross_covariance_design()
    scenario = FunctionalSimulationScenario(
        name="asymmetric",
        truth_grid=np.linspace(0.0, 1.0, 31),
        eigenvalues=eigenvalues,
        n_participants=4,
        dimension_names=("x", "y"),
        observation_design="irregular",
        samples_per_curve=8,
        measurement_noise_sd=(0.0, 0.0),
        replicates=1,
        seed_start=11,
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=runner._mean_planar,
        eigenfunctions=eigenfunctions,
    )
    cxy = _truth_cxy(simulation.truth)
    functions = simulation.truth.eigenfunctions
    cyx = np.einsum(
        "k,ks,kt->st",
        simulation.truth.eigenvalues,
        functions[:, :, 1],
        functions[:, :, 0],
    )

    assert not np.allclose(cxy, cxy.T)
    np.testing.assert_allclose(cyx, cxy.T, atol=1e-12)


def test_mean_guard_uses_analytic_finite_sample_scale_not_absolute_ise():
    runner = _load_runner()
    assert "mean_ise_max" not in runner.QUALIFICATION_GUARDS
    assert runner.QUALIFICATION_GUARDS[
        "mean_ise_sampling_reference_ratio_max"
    ] == pytest.approx(2.0)

    eigenvalues, _ = runner.planar_rho_design(0.6)
    expected = sum(eigenvalues) / 36
    assert expected == pytest.approx(2.9 / 36)


def test_sensitivity_contract_never_selects_a_tuning_value():
    runner = _load_runner()
    assert runner.GRID_SIZES == (31, 51, 81)
    assert runner.RIDGES == (0.0, 1e-8, 1e-6, 1e-4)
    source = (
        ROOT
        / "scripts"
        / "run_sparse_mfpca_recovery_validation.py"
    ).read_text(encoding="utf-8")
    assert '"selection_performed": False' in source
    assert "mGSFPCA" not in source
