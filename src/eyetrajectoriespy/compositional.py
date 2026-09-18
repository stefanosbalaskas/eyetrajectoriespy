"""Constraint-aware FPCA for AOI probability trajectories."""

from __future__ import annotations

import numpy as np

from .fpca import fit_mfpca, reconstruct_fpca
from .types import CompositionalFPCAResult, TrajectorySet
from .validation import validate_simplex


def alr_transform(
    values: np.ndarray,
    *,
    reference_dimension: int = -1,
    epsilon: float = 1e-8,
) -> np.ndarray:
    """Additive log-ratio transform for simplex-valued functional data.

    Exact zeros are clipped to ``epsilon`` and the complete composition is
    renormalized before transformation. The chosen epsilon is part of the
    scientific specification and should be reported.
    """

    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    arr = np.asarray(values, dtype=float)
    validate_simplex(arr)
    k = arr.shape[2]
    ref = reference_dimension % k
    clipped = np.maximum(arr, epsilon)
    clipped = clipped / clipped.sum(axis=2, keepdims=True)
    indices = [i for i in range(k) if i != ref]
    return np.log(clipped[:, :, indices] / clipped[:, :, [ref]])


def inverse_alr(
    transformed: np.ndarray,
    *,
    reference_dimension: int,
    n_dimensions: int,
) -> np.ndarray:
    """Inverse additive log-ratio transform back to the probability simplex."""

    z = np.asarray(transformed, dtype=float)
    if z.ndim != 3 or z.shape[2] != n_dimensions - 1:
        raise ValueError("transformed data have incompatible dimensions")
    ref = reference_dimension % n_dimensions
    exponentiated = np.exp(z)
    out = np.ones((z.shape[0], z.shape[1], n_dimensions), dtype=float)
    indices = [i for i in range(n_dimensions) if i != ref]
    out[:, :, indices] = exponentiated
    return out / out.sum(axis=2, keepdims=True)


def fit_compositional_fpca(
    trajectories: TrajectorySet,
    *,
    reference_dimension: int = -1,
    epsilon: float = 1e-8,
    n_components: int | float = 0.95,
    scaling: str = "none",
) -> CompositionalFPCAResult:
    """Fit FPCA to AOI probability functions while respecting the simplex.

    The implementation applies an additive log-ratio transform before MFPCA.
    Reconstructed trajectories can be mapped back exactly to the simplex with
    :func:`reconstruct_compositional_fpca`.
    """

    validate_simplex(trajectories.values)
    k = trajectories.n_dimensions
    ref = reference_dimension % k
    z = alr_transform(
        trajectories.values,
        reference_dimension=ref,
        epsilon=epsilon,
    )
    names = tuple(f"log({name}/{trajectories.dimension_names[ref]})" for i, name in enumerate(trajectories.dimension_names) if i != ref)
    transformed = TrajectorySet(
        time=trajectories.time,
        values=z,
        curve_ids=trajectories.curve_ids,
        dimension_names=names,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system="simplex_logratio",
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "compositional_transform": {
                "method": "additive_log_ratio",
                "reference_dimension": ref,
                "epsilon": epsilon,
            },
        },
    )
    fpca = fit_mfpca(transformed, n_components=n_components, scaling=scaling)
    return CompositionalFPCAResult(
        fpca=fpca,
        reference_dimension=ref,
        original_dimension_names=trajectories.dimension_names,
        epsilon=epsilon,
        provenance={
            "method": "ALR + quadrature-weighted MFPCA",
            "simplex_preserved_on_inverse": True,
        },
    )


def reconstruct_compositional_fpca(
    result: CompositionalFPCAResult,
    *,
    scores: np.ndarray | None = None,
    n_components: int | None = None,
) -> np.ndarray:
    """Reconstruct AOI probability trajectories that sum to one."""

    z = reconstruct_fpca(result.fpca, scores=scores, n_components=n_components)
    return inverse_alr(
        z,
        reference_dimension=result.reference_dimension,
        n_dimensions=len(result.original_dimension_names),
    )
