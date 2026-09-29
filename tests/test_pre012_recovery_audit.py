from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from eyetrajectoriespy import simulate_functional_scenario


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_pre012_recovery_audit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "run_pre012_recovery_audit",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load pre-0.12 audit script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_planar_truth_keeps_marginals_fixed_while_cross_block_changes():
    audit = _load_module()
    marginal_covariances = []
    cross_fractions = []

    for rho in audit.RHO_LEVELS:
        scenario, design = audit._planar_scenario(
            rho,
            name=f"test-rho-{rho}",
            seed_start=100,
            replicates=1,
            n_participants=6,
            samples_per_curve=(10, 12),
        )
        simulation = simulate_functional_scenario(
            scenario,
            mean=audit._mean_planar,
            eigenfunctions=design.eigenfunctions,
        )
        truth = simulation.truth
        marginal_covariances.append(
            (
                audit._truth_covariance(truth, 0, 0),
                audit._truth_covariance(truth, 1, 1),
            )
        )
        cross_fractions.append(
            audit._joint_truth_metrics(truth)[
                "truth_cross_block_energy_fraction"
            ]
        )

    reference_x, reference_y = marginal_covariances[0]
    for covariance_x, covariance_y in marginal_covariances[1:]:
        np.testing.assert_allclose(
            covariance_x,
            reference_x,
            rtol=1e-12,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            covariance_y,
            reference_y,
            rtol=1e-12,
            atol=1e-12,
        )
    assert cross_fractions[0] == pytest.approx(0.0, abs=1e-14)
    assert np.all(np.diff(cross_fractions) > 0)


def test_signal_dependent_loss_is_seeded_and_retains_sparse_native_geometry():
    audit = _load_module()
    scenario, design = audit._planar_scenario(
        0.6,
        name="loss-test",
        seed_start=321,
        replicates=1,
        n_participants=8,
        samples_per_curve=(12, 16),
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=audit._mean_planar,
        eigenfunctions=design.eigenfunctions,
    )

    first, first_metrics = audit._apply_loss(
        simulation,
        "velocity_dependent_loss",
        seed=888,
    )
    second, second_metrics = audit._apply_loss(
        simulation,
        "velocity_dependent_loss",
        seed=888,
    )

    assert first.dimension_names == ("x", "y")
    assert first.curve_ids == simulation.observations.curve_ids
    assert first_metrics == second_metrics
    for time_first, time_second, value_first, value_second in zip(
        first.time,
        second.time,
        first.values,
        second.values,
        strict=True,
    ):
        np.testing.assert_array_equal(time_first, time_second)
        np.testing.assert_array_equal(value_first, value_second)
    assert 0.0 < first_metrics["actual_loss_fraction"] < 0.5
    assert first_metrics["minimum_retained_samples"] >= 4


@pytest.mark.parametrize("mechanism", [
    "signal_dependent_x_loss",
    "signal_dependent_y_loss",
    "eccentricity_dependent_loss",
    "velocity_dependent_loss",
    "phase_dependent_loss",
])
def test_loss_predictors_are_finite_and_shape_preserving(mechanism):
    audit = _load_module()
    scenario, design = audit._planar_scenario(
        0.3,
        name="predictor-test",
        seed_start=456,
        replicates=1,
        n_participants=6,
        samples_per_curve=(10, 14),
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=audit._mean_planar,
        eigenfunctions=design.eigenfunctions,
    )
    predictors = audit._loss_predictors(simulation.truth, mechanism)
    assert predictors is not None
    assert len(predictors) == simulation.observations.n_curves
    for predictor, time in zip(
        predictors,
        simulation.truth.pre_missing_observation_times,
        strict=True,
    ):
        assert predictor.shape == np.asarray(time).shape
        assert np.all(np.isfinite(predictor))


def test_sparse_hierarchy_audit_does_not_silently_interpolate():
    audit = _load_module()
    frame = audit._sparse_hierarchy_audit()

    assert len(frame) == 3
    assert set(frame["status"]) == {"boundary_confirmed"}
    assert not frame["native_irregular_input_supported"].any()
    assert np.all(
        frame["observed_samples_min"]
        < frame["observed_samples_max"]
    )


def test_external_fixture_is_long_format_and_records_joint_truth(tmp_path):
    audit = _load_module()
    truth = audit._external_fixture(tmp_path)

    x = np.genfromtxt(
        tmp_path / "external_fixture_x.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    y = np.genfromtxt(
        tmp_path / "external_fixture_y.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    assert x.dtype.names == ("ID", "time", "value")
    assert y.dtype.names == ("ID", "time", "value")
    assert truth["rho_xy"] == pytest.approx(0.6)
    assert (
        truth["joint_truth_metrics"][
            "truth_cross_block_energy_fraction"
        ]
        > 0
    )


def test_invalid_rho_and_unknown_loss_mechanism_fail_closed():
    audit = _load_module()
    with pytest.raises(ValueError, match="rho_xy"):
        audit._planar_design(1.0)

    scenario, design = audit._planar_scenario(
        0.0,
        name="invalid-loss",
        seed_start=7,
        replicates=1,
        n_participants=4,
        samples_per_curve=(8, 10),
    )
    simulation = simulate_functional_scenario(
        scenario,
        mean=audit._mean_planar,
        eigenfunctions=design.eigenfunctions,
    )
    with pytest.raises(ValueError, match="unknown loss mechanism"):
        audit._loss_predictors(simulation.truth, "not-a-mechanism")
