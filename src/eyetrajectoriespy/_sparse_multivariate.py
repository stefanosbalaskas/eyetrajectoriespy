"""Joint block-covariance primitives for native sparse planar FPCA.

This module is intentionally estimator-agnostic. It provides the weighted
operator algebra required by the 0.12 design contract before sparse smoothing
or conditional score recovery is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ._sparse_native import SparseNativeError
from .fpca import functional_trapezoid_weights


@dataclass(frozen=True)
class PlanarCovarianceAudit:
    """Diagnostics for symmetry and PSD handling of a planar covariance."""

    requested_action: str
    applied_action: str
    tolerance: float
    symmetry_tolerance: float
    pre_enforcement_symmetry_error: float
    pre_repair_operator_eigenvalues: np.ndarray
    negative_eigenvalue_count: int
    substantial_negative_eigenvalue_count: int
    most_negative_eigenvalue: float
    correction_frobenius_norm: float
    relative_correction_frobenius_norm: float
    operator_correction_frobenius_norm: float
    relative_operator_correction_frobenius_norm: float


@dataclass(frozen=True)
class PlanarCovarianceOperatorResult:
    """A symmetry-enforced, optionally PSD-repaired planar covariance."""

    cxx: np.ndarray
    cxy: np.ndarray
    cyx: np.ndarray
    cyy: np.ndarray
    covariance_matrix: np.ndarray
    quadrature_weights: np.ndarray
    audit: PlanarCovarianceAudit


@dataclass(frozen=True)
class PlanarWeightedEigendecomposition:
    """Quadrature-weighted joint eigendecomposition."""

    eigenvalues: np.ndarray
    eigenfunctions: np.ndarray
    quadrature_weights: np.ndarray


def _validate_grid(evaluation_grid: np.ndarray) -> np.ndarray:
    grid = np.asarray(evaluation_grid, dtype=float)
    if (
        grid.ndim != 1
        or grid.size < 3
        or not np.all(np.isfinite(grid))
        or not np.all(np.diff(grid) > 0)
    ):
        raise ValueError(
            "evaluation_grid must be a finite, strictly increasing "
            "one-dimensional array with at least three points"
        )
    return grid


def _validate_block(
    block: np.ndarray,
    *,
    grid_size: int,
    name: str,
) -> np.ndarray:
    matrix = np.asarray(block, dtype=float)
    if matrix.shape != (grid_size, grid_size):
        raise ValueError(
            f"{name} must have shape ({grid_size}, {grid_size})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must contain only finite values")
    return matrix


def _relative_frobenius(delta: np.ndarray, baseline: np.ndarray) -> float:
    numerator = float(np.linalg.norm(delta, ord="fro"))
    denominator = float(np.linalg.norm(baseline, ord="fro"))
    return 0.0 if denominator == 0.0 else numerator / denominator


def audit_repair_planar_covariance(
    cxx: np.ndarray,
    cxy: np.ndarray,
    cyy: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    cyx: np.ndarray | None = None,
    action: str = "error",
    tolerance: float = 1e-8,
    symmetry_tolerance: float = 1e-10,
) -> PlanarCovarianceOperatorResult:
    """Audit and optionally project a full planar covariance operator to PSD.

    Blocks use channel-major ordering in the assembled operator:
    x(grid) followed by y(grid). Symmetry is assessed jointly, including
    Cyx(s,t) = Cxy(t,s). Tiny numerical asymmetry within the declared
    tolerance is enforced explicitly; material asymmetry fails closed.
    """

    grid = _validate_grid(evaluation_grid)
    if action not in {"error", "project"}:
        raise ValueError("action must be 'error' or 'project'")
    tolerance = float(tolerance)
    symmetry_tolerance = float(symmetry_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")
    if not np.isfinite(symmetry_tolerance) or symmetry_tolerance < 0:
        raise ValueError(
            "symmetry_tolerance must be finite and non-negative"
        )

    size = grid.size
    raw_xx = _validate_block(cxx, grid_size=size, name="cxx")
    raw_xy = _validate_block(cxy, grid_size=size, name="cxy")
    raw_yy = _validate_block(cyy, grid_size=size, name="cyy")
    raw_yx = (
        raw_xy.T.copy()
        if cyx is None
        else _validate_block(cyx, grid_size=size, name="cyx")
    )

    symmetry_error = max(
        float(np.max(np.abs(raw_xx - raw_xx.T))),
        float(np.max(np.abs(raw_yy - raw_yy.T))),
        float(np.max(np.abs(raw_yx - raw_xy.T))),
    )
    if symmetry_error > symmetry_tolerance:
        raise SparseNativeError(
            "joint_covariance_symmetry_failure",
            "planar covariance blocks violate joint symmetry tolerance",
            details={
                "maximum_symmetry_error": symmetry_error,
                "symmetry_tolerance": symmetry_tolerance,
            },
        )

    sym_xx = 0.5 * (raw_xx + raw_xx.T)
    sym_yy = 0.5 * (raw_yy + raw_yy.T)
    sym_xy = 0.5 * (raw_xy + raw_yx.T)
    sym_yx = sym_xy.T
    matrix = np.block([[sym_xx, sym_xy], [sym_yx, sym_yy]])

    weights = functional_trapezoid_weights(grid)
    joint_weights = np.concatenate([weights, weights])
    sqrt_weights = np.sqrt(joint_weights)
    weighted_operator = (
        sqrt_weights[:, None] * matrix * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    negative = eigenvalues < 0.0
    substantial = eigenvalues < -tolerance
    negative_count = int(np.count_nonzero(negative))
    substantial_count = int(np.count_nonzero(substantial))
    most_negative = float(np.min(eigenvalues))

    if action == "error" and substantial_count:
        raise SparseNativeError(
            "joint_covariance_psd_failure",
            "planar covariance operator has eigenvalues below the PSD tolerance",
            details={
                "most_negative_eigenvalue": most_negative,
                "negative_eigenvalue_count": negative_count,
                "substantial_negative_eigenvalue_count": substantial_count,
                "tolerance": tolerance,
            },
        )

    clipped = eigenvalues.copy()
    applied_action = "none"
    if action == "project" and negative_count:
        clipped[negative] = 0.0
        applied_action = "project"
    elif action == "error" and negative_count:
        clipped[negative] = 0.0
        applied_action = "numerical_clip_within_tolerance"

    if applied_action == "none":
        repaired = matrix.copy()
    else:
        repaired_weighted = (
            (eigenvectors * clipped[None, :]) @ eigenvectors.T
        )
        repaired = (
            repaired_weighted
            / sqrt_weights[:, None]
            / sqrt_weights[None, :]
        )
        repaired = 0.5 * (repaired + repaired.T)

    correction = repaired - matrix
    operator_correction = (
        sqrt_weights[:, None] * correction * sqrt_weights[None, :]
    )
    correction_norm = float(np.linalg.norm(correction, ord="fro"))
    operator_correction_norm = float(
        np.linalg.norm(operator_correction, ord="fro")
    )
    operator_baseline_norm = float(
        np.linalg.norm(weighted_operator, ord="fro")
    )
    relative_operator_norm = (
        0.0
        if operator_baseline_norm == 0.0
        else operator_correction_norm / operator_baseline_norm
    )

    repaired_xx = repaired[:size, :size].copy()
    repaired_xy = repaired[:size, size:].copy()
    repaired_yx = repaired[size:, :size].copy()
    repaired_yy = repaired[size:, size:].copy()
    audit = PlanarCovarianceAudit(
        requested_action=action,
        applied_action=applied_action,
        tolerance=tolerance,
        symmetry_tolerance=symmetry_tolerance,
        pre_enforcement_symmetry_error=symmetry_error,
        pre_repair_operator_eigenvalues=eigenvalues.copy(),
        negative_eigenvalue_count=negative_count,
        substantial_negative_eigenvalue_count=substantial_count,
        most_negative_eigenvalue=most_negative,
        correction_frobenius_norm=correction_norm,
        relative_correction_frobenius_norm=_relative_frobenius(
            correction, matrix
        ),
        operator_correction_frobenius_norm=operator_correction_norm,
        relative_operator_correction_frobenius_norm=relative_operator_norm,
    )
    return PlanarCovarianceOperatorResult(
        cxx=repaired_xx,
        cxy=repaired_xy,
        cyx=repaired_yx,
        cyy=repaired_yy,
        covariance_matrix=repaired,
        quadrature_weights=weights,
        audit=audit,
    )


def weighted_planar_covariance_eigendecomposition(
    covariance_matrix: np.ndarray,
    evaluation_grid: np.ndarray,
    *,
    n_components: int,
    positive_tolerance: float = 1e-10,
) -> PlanarWeightedEigendecomposition:
    """Solve the quadrature-weighted bivariate covariance eigenproblem."""

    grid = _validate_grid(evaluation_grid)
    matrix = np.asarray(covariance_matrix, dtype=float)
    size = grid.size
    if matrix.shape != (2 * size, 2 * size):
        raise ValueError(
            "covariance_matrix must have shape "
            f"({2 * size}, {2 * size})"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError("covariance_matrix must contain only finite values")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    positive_tolerance = float(positive_tolerance)
    if not np.isfinite(positive_tolerance) or positive_tolerance < 0:
        raise ValueError(
            "positive_tolerance must be finite and non-negative"
        )

    weights = functional_trapezoid_weights(grid)
    joint_weights = np.concatenate([weights, weights])
    sqrt_weights = np.sqrt(joint_weights)
    symmetric = 0.5 * (matrix + matrix.T)
    weighted_operator = (
        sqrt_weights[:, None] * symmetric * sqrt_weights[None, :]
    )
    eigenvalues, eigenvectors = np.linalg.eigh(weighted_operator)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    positive = eigenvalues > positive_tolerance
    n_positive = int(np.count_nonzero(positive))
    if n_components > n_positive:
        raise SparseNativeError(
            "insufficient_positive_joint_components",
            "joint covariance has fewer positive components than requested",
            details={
                "requested_components": n_components,
                "positive_components": n_positive,
                "positive_tolerance": positive_tolerance,
            },
        )

    selected_values = eigenvalues[:n_components].copy()
    selected_vectors = eigenvectors[:, :n_components].copy()
    flat_functions = (
        selected_vectors / sqrt_weights[:, None]
    ).T

    for component in range(n_components):
        pivot = int(np.argmax(np.abs(flat_functions[component])))
        if flat_functions[component, pivot] < 0:
            flat_functions[component] *= -1.0

    eigenfunctions = flat_functions.reshape(n_components, 2, size)
    return PlanarWeightedEigendecomposition(
        eigenvalues=selected_values,
        eigenfunctions=eigenfunctions,
        quadrature_weights=weights,
    )
