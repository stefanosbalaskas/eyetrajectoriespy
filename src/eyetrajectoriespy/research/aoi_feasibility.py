"""F4 feasibility only: raw-space FPCA with post-reconstruction simplex projection.

This is a deliberately transparent comparator against established ALR-FPCA.
It is NOT the constrained eigenfunction estimator of Kwan et al. (2024).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.fpca import fit_mfpca, reconstruct_fpca
from eyetrajectoriespy.compositional import (
    fit_compositional_fpca, reconstruct_compositional_fpca,
)
from eyetrajectoriespy.validation import validate_simplex


def project_simplex(values: np.ndarray) -> np.ndarray:
    """Exact Euclidean projection of each vector onto probability simplex."""
    arr = np.asarray(values, dtype=float)
    if arr.ndim < 1 or arr.shape[-1] < 2 or not np.isfinite(arr).all():
        raise ValueError("finite array with at least two AOIs required")
    n = arr.shape[-1]
    ordered = np.sort(arr, axis=-1)[..., ::-1]
    cumulative = np.cumsum(ordered, axis=-1) - 1
    ranks = np.arange(1, n + 1)
    positive = ordered - cumulative / ranks > 0
    rho = positive.sum(axis=-1)
    theta = np.take_along_axis(cumulative / ranks, (rho - 1)[..., None], axis=-1)
    projected = np.maximum(arr - theta, 0)
    return projected / projected.sum(axis=-1, keepdims=True)


@dataclass(frozen=True)
class AOIGeometryFeasibility:
    alr_result: Any
    raw_fpca_result: Any
    summary: pd.DataFrame
    projected_reconstruction: np.ndarray
    alr_reconstruction: np.ndarray
    provisional: bool = True


def compare_aoi_functional_geometries(
    trajectories: TrajectorySet,
    *,
    n_components: int = 2,
    reference_dimension: int = -1,
    epsilon: float = 1e-6,
) -> AOIGeometryFeasibility:
    """Compare ALR-FPCA against Euclidean FPCA plus simplex projection.

    This is a reconstruction-sensitivity programme, not a new qualified
    constrained FPCA estimator. Reference choice and zero pseudocounts must
    be explicitly reported. Observed curves must be finite and simplex-valued.
    """
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("F4 requires a common-grid AOI proportion TrajectorySet")
    if not np.isfinite(trajectories.values).all():
        raise ValueError("missing AOI values require an explicit preprocessing plan")
    validate_simplex(trajectories.values)
    if isinstance(n_components, bool) or n_components < 1:
        raise ValueError("n_components must be positive")
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be positive")
    alr = fit_compositional_fpca(
        trajectories, reference_dimension=reference_dimension,
        epsilon=epsilon, n_components=n_components, scaling="none",
    )
    raw = fit_mfpca(trajectories, n_components=n_components, scaling="none")
    a = reconstruct_compositional_fpca(alr)
    b = project_simplex(reconstruct_fpca(raw))
    if a.shape != trajectories.values.shape or b.shape != trajectories.values.shape:
        raise RuntimeError("unexpected reconstruction shape")
    truth = trajectories.values
    summary = pd.DataFrame([
        {"geometry": "existing_ALR_FPCA", "mse": float(np.mean((truth - a) ** 2)),
         "reference_dimension": int(reference_dimension % trajectories.n_dimensions),
         "epsilon": epsilon, "known_zero_count": int((truth == 0).sum()),
         "qualified_as_new_constrained_estimator": False},
        {"geometry": "raw_FPCA_plus_Euclidean_simplex_projection",
         "mse": float(np.mean((truth - b) ** 2)),
         "reference_dimension": np.nan, "epsilon": np.nan,
         "known_zero_count": int((truth == 0).sum()),
         "qualified_as_new_constrained_estimator": False},
    ])
    return AOIGeometryFeasibility(
        alr_result=alr, raw_fpca_result=raw,
        summary=summary, projected_reconstruction=b, alr_reconstruction=a,
    )
