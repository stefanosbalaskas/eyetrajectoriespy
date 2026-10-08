"""Experimental F6: declared channel-weighted functional L2 geometry.

The weighted isometry maps x_j(t) to sqrt(w_j) * x_j(t). Ordinary quadrature
FPCA is fitted in that transformed space. Inversion restores original units.
Not a new sparse estimator, nor an automatic channel weighting algorithm.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
from eyetrajectoriespy.types import TrajectorySet
from eyetrajectoriespy.fpca import fit_mfpca, reconstruct_fpca


@dataclass(frozen=True)
class WeightedMFPCAResult:
    fitted_transformed: Any
    weights: np.ndarray
    dimensions: tuple[str, ...]
    method: str = "declared_diagonal_weighted_L2_isometry"


def fit_weighted_mfpca(
    trajectories: TrajectorySet,
    *,
    weights: tuple[float, ...] | np.ndarray,
    n_components: int | float = 0.95,
) -> WeightedMFPCAResult:
    """Only positive finite scientific weights; no inferred optimal weights."""
    if not isinstance(trajectories, TrajectorySet):
        raise TypeError("weighted geometry currently supports common-grid data only")
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1 or len(w) != trajectories.n_dimensions or (
        not np.isfinite(w).all()
    ) or (w <= 0).any():
        raise ValueError("one positive finite weight per channel required")
    if not np.isfinite(trajectories.values).all():
        raise ValueError("F6 requires observed common-grid samples; no hidden interpolation")
    transformed = TrajectorySet(
        time=trajectories.time,
        values=trajectories.values * np.sqrt(w)[None, None, :],
        curve_ids=trajectories.curve_ids,
        dimension_names=trajectories.dimension_names,
        metadata=trajectories.metadata.reset_index(drop=True),
        coordinate_system="unknown",
        time_unit=trajectories.time_unit,
        provenance={**trajectories.provenance, "geometry": "weighted L2",
                    "weights": w.tolist(), "weight_choice": "analyst_declared"},
    )
    fit = fit_mfpca(transformed, n_components=n_components, scaling="none")
    return WeightedMFPCAResult(
        fitted_transformed=fit, weights=w,
        dimensions=trajectories.dimension_names,
    )


def reconstruct_weighted_mfpca(
    fitted: WeightedMFPCAResult,
    *,
    scores: np.ndarray | None = None,
    n_components: int | None = None,
) -> np.ndarray:
    """Invert declared isometry and return reconstructed original coordinate units."""
    prediction = reconstruct_fpca(
        fitted.fitted_transformed, scores=scores, n_components=n_components
    )
    return prediction / np.sqrt(fitted.weights)[None, None, :]


def weighted_component_geometry(fitted: WeightedMFPCAResult) -> np.ndarray:
    """Return component trajectories back in original coordinate units."""
    return fitted.fitted_transformed.components / np.sqrt(fitted.weights)[None, None, :]
