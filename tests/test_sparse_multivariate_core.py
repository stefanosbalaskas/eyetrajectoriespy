import numpy as np
import pytest

from eyetrajectoriespy._sparse_multivariate import (
    audit_repair_planar_covariance,
    weighted_planar_covariance_eigendecomposition,
)
from eyetrajectoriespy._sparse_native import SparseNativeError
from eyetrajectoriespy.fpca import functional_trapezoid_weights


def _weighted_scalar_mode(grid):
    weights = functional_trapezoid_weights(grid)
    candidate = np.sin(np.pi * grid)
    norm = np.sqrt(np.sum(weights * candidate**2))
    return candidate / norm, weights


def test_joint_operator_recovers_known_cross_channel_eigenstructure():
    grid = np.linspace(0.0, 1.0, 41)
    phi, weights = _weighted_scalar_mode(grid)
    base = np.outer(phi, phi)
    rho = 0.6

    operator = audit_repair_planar_covariance(
        base,
        rho * base,
        base,
        grid,
    )
    result = weighted_planar_covariance_eigendecomposition(
        operator.covariance_matrix,
        grid,
        n_components=2,
    )

    assert np.allclose(
        result.eigenvalues,
        np.array([1.0 + rho, 1.0 - rho]),
        rtol=1e-10,
        atol=1e-12,
    )

    expected_plus = np.stack([phi, phi]) / np.sqrt(2.0)
    expected_minus = np.stack([phi, -phi]) / np.sqrt(2.0)
    joint_weights = np.broadcast_to(weights, (2, grid.size))

    similarities = np.array(
        [
            [
                abs(np.sum(joint_weights * fitted * expected))
                for expected in (expected_plus, expected_minus)
            ]
            for fitted in result.eigenfunctions
        ]
    )
    assert similarities[0, 0] == pytest.approx(1.0, abs=1e-10)
    assert similarities[1, 1] == pytest.approx(1.0, abs=1e-10)

    gram = np.einsum(
        "kcg,lcg,cg->kl",
        result.eigenfunctions,
        result.eigenfunctions,
        joint_weights,
    )
    assert np.allclose(gram, np.eye(2), atol=1e-10)


def test_cross_channel_dependence_changes_joint_spectrum_with_fixed_marginals():
    grid = np.linspace(0.0, 1.0, 31)
    phi, _ = _weighted_scalar_mode(grid)
    base = np.outer(phi, phi)

    spectra = []
    for rho in (0.0, 0.3, 0.6, 0.9):
        operator = audit_repair_planar_covariance(
            base,
            rho * base,
            base,
            grid,
        )
        fitted = weighted_planar_covariance_eigendecomposition(
            operator.covariance_matrix,
            grid,
            n_components=2,
        )
        spectra.append(fitted.eigenvalues)

        assert np.allclose(operator.cxx, base)
        assert np.allclose(operator.cyy, base)
        assert np.allclose(operator.cxy, rho * base)
        assert np.allclose(operator.cyx, (rho * base).T)

    spectra = np.asarray(spectra)
    assert np.allclose(
        spectra[:, 0],
        np.array([1.0, 1.3, 1.6, 1.9]),
        atol=1e-10,
    )
    assert np.allclose(
        spectra[:, 1],
        np.array([1.0, 0.7, 0.4, 0.1]),
        atol=1e-10,
    )


def test_joint_psd_can_fail_even_when_both_marginal_blocks_are_psd():
    grid = np.linspace(0.0, 1.0, 9)
    marginal = np.eye(grid.size)
    cross = 1.2 * np.eye(grid.size)

    with pytest.raises(SparseNativeError) as exc:
        audit_repair_planar_covariance(
            marginal,
            cross,
            marginal,
            grid,
            action="error",
            tolerance=1e-12,
        )
    assert exc.value.code == "joint_covariance_psd_failure"

    projected = audit_repair_planar_covariance(
        marginal,
        cross,
        marginal,
        grid,
        action="project",
        tolerance=1e-12,
    )
    assert projected.audit.applied_action == "project"
    assert projected.audit.substantial_negative_eigenvalue_count > 0
    assert projected.audit.operator_correction_frobenius_norm > 0

    weights = np.concatenate(
        [
            functional_trapezoid_weights(grid),
            functional_trapezoid_weights(grid),
        ]
    )
    sqrt_weights = np.sqrt(weights)
    weighted = (
        sqrt_weights[:, None]
        * projected.covariance_matrix
        * sqrt_weights[None, :]
    )
    assert np.min(np.linalg.eigvalsh(weighted)) >= -1e-12


def test_joint_symmetry_violation_fails_closed():
    grid = np.linspace(0.0, 1.0, 7)
    identity = np.eye(grid.size)
    cxy = 0.2 * identity
    cyx = cxy.T.copy()
    cyx[0, 1] = 0.1

    with pytest.raises(SparseNativeError) as exc:
        audit_repair_planar_covariance(
            identity,
            cxy,
            identity,
            grid,
            cyx=cyx,
            symmetry_tolerance=1e-12,
        )
    assert exc.value.code == "joint_covariance_symmetry_failure"


def test_joint_component_shortage_has_joint_specific_status():
    grid = np.linspace(0.0, 1.0, 21)
    phi, _ = _weighted_scalar_mode(grid)
    base = np.outer(phi, phi)
    operator = audit_repair_planar_covariance(
        base,
        np.zeros_like(base),
        np.zeros_like(base),
        grid,
    )

    with pytest.raises(SparseNativeError) as exc:
        weighted_planar_covariance_eigendecomposition(
            operator.covariance_matrix,
            grid,
            n_components=2,
            positive_tolerance=1e-10,
        )
    assert exc.value.code == "insufficient_positive_joint_components"
