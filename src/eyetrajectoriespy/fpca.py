"""Grid-based univariate and multivariate functional PCA.

The implementation uses quadrature-weighted PCA on a common observation grid.
It is deliberately transparent and dependency-light. For elastic SRVF analysis
use :mod:`eyetrajectoriespy.elastic`; for optional third-party FDA backends see
:mod:`eyetrajectoriespy.backends`.
"""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from .types import FPCAResult, TrajectorySet
from .validation import validate_trajectory_set


def functional_trapezoid_weights(time: np.ndarray, *, normalize: bool = False) -> np.ndarray:
    """Return trapezoidal quadrature weights for a strictly increasing grid."""

    time = np.asarray(time, dtype=float)
    if time.ndim != 1 or len(time) < 2 or not np.all(np.diff(time) > 0):
        raise ValueError("time must be a strictly increasing one-dimensional array")
    dt = np.diff(time)
    weights = np.empty_like(time)
    weights[0] = dt[0] / 2.0
    weights[-1] = dt[-1] / 2.0
    if len(time) > 2:
        weights[1:-1] = (dt[:-1] + dt[1:]) / 2.0
    if normalize:
        weights = weights / weights.sum()
    return weights


def _dimension_scales(
    trajectories: TrajectorySet,
    *,
    scaling: str,
    weights: np.ndarray,
) -> np.ndarray:
    if scaling == "none":
        return np.ones(trajectories.n_dimensions, dtype=float)
    if scaling != "dimension_sd":
        raise ValueError("scaling must be 'none' or 'dimension_sd'")
    centered = trajectories.values - trajectories.values.mean(axis=0, keepdims=True)
    # Mean integrated variance for each functional dimension.
    variances = np.mean(centered**2, axis=0)
    integrated = np.sum(variances * weights[:, None], axis=0)
    scale = np.sqrt(integrated)
    if np.any(scale <= np.finfo(float).eps):
        bad = np.flatnonzero(scale <= np.finfo(float).eps)
        raise ValueError(f"Cannot standardize constant functional dimensions: {bad.tolist()}")
    return scale


def _resolve_n_components(n_components: int | float, max_components: int) -> int | float:
    if isinstance(n_components, bool):
        raise TypeError("n_components must be an integer or variance proportion")
    if isinstance(n_components, int):
        if n_components < 1 or n_components > max_components:
            raise ValueError(f"n_components must be in [1, {max_components}]")
        return n_components
    value = float(n_components)
    if not 0 < value < 1:
        raise ValueError("float n_components must be a variance proportion in (0, 1)")
    return value


def fit_fpca(
    trajectories: TrajectorySet,
    *,
    n_components: int | float = 0.95,
    scaling: str = "none",
) -> FPCAResult:
    """Fit quadrature-weighted functional PCA on one or more channels.

    Parameters
    ----------
    trajectories:
        Complete trajectories on a common grid. Missing values are rejected;
        users must make interpolation/exclusion decisions explicitly upstream.
    n_components:
        Integer component count or a proportion of variance to retain.
    scaling:
        ``"none"`` preserves original relative channel scales. Use
        ``"dimension_sd"`` to equalize integrated variance across dimensions.
        Scaling is explicit because x/y, pupil, velocity, or other channels may
        have scientifically different units.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    x = trajectories.values
    n_curves, n_time, n_dim = x.shape
    if n_curves < 2:
        raise ValueError("At least two trajectories are required for FPCA")
    weights = functional_trapezoid_weights(trajectories.time)
    mean = x.mean(axis=0)
    scales = _dimension_scales(trajectories, scaling=scaling, weights=weights)
    centered = (x - mean[None, :, :]) / scales[None, None, :]
    weighted = centered * np.sqrt(weights)[None, :, None]
    matrix = weighted.reshape(n_curves, n_time * n_dim)
    max_components = min(n_curves, n_time * n_dim)
    resolved = _resolve_n_components(n_components, max_components)
    pca = PCA(n_components=resolved, svd_solver="full")
    scores = pca.fit_transform(matrix)

    basis = pca.components_.reshape(pca.n_components_, n_time, n_dim)
    components = basis / np.sqrt(weights)[None, :, None] * scales[None, None, :]
    return FPCAResult(
        mean=mean,
        components=components,
        scores=scores,
        explained_variance=pca.explained_variance_.copy(),
        explained_variance_ratio=pca.explained_variance_ratio_.copy(),
        time=trajectories.time.copy(),
        dimension_names=trajectories.dimension_names,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        curve_ids=trajectories.curve_ids,
        weights=weights,
        scale=scales,
        provenance={
            **dict(trajectories.provenance),
            "fpca": {
                "method": "quadrature_weighted_grid_pca",
                "n_components": int(pca.n_components_),
                "requested_n_components": n_components,
                "scaling": scaling,
            },
        },
        model=pca,
    )


def fit_mfpca(
    trajectories: TrajectorySet,
    *,
    n_components: int | float = 0.95,
    scaling: str = "none",
) -> FPCAResult:
    """Fit multivariate FPCA to two or more functional dimensions.

    This is a semantic wrapper around :func:`fit_fpca` that enforces a
    multivariate input and makes intent explicit in analysis scripts.
    """

    if trajectories.n_dimensions < 2:
        raise ValueError("fit_mfpca requires at least two functional dimensions")
    result = fit_fpca(trajectories, n_components=n_components, scaling=scaling)
    provenance = dict(result.provenance)
    provenance["fpca"] = {**provenance["fpca"], "multivariate": True}
    return FPCAResult(**{**result.__dict__, "provenance": provenance})


def transform_fpca(result: FPCAResult, trajectories: TrajectorySet) -> np.ndarray:
    """Project compatible trajectories into an existing FPCA basis."""

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.array_equal(trajectories.time, result.time):
        raise ValueError("Trajectory grid must match the fitted FPCA grid exactly")
    if trajectories.dimension_names != result.dimension_names:
        raise ValueError("Functional dimension names/order must match the fitted FPCA model")
    centered = (trajectories.values - result.mean[None, :, :]) / result.scale[None, None, :]
    weighted = centered * np.sqrt(result.weights)[None, :, None]
    matrix = weighted.reshape(trajectories.n_curves, -1)
    basis = result.components / result.scale[None, None, :] * np.sqrt(result.weights)[None, :, None]
    flat_basis = basis.reshape(result.n_components, -1)
    return matrix @ flat_basis.T


def reconstruct_fpca(
    result: FPCAResult,
    *,
    scores: np.ndarray | None = None,
    n_components: int | None = None,
) -> np.ndarray:
    """Reconstruct trajectories from functional principal component scores."""

    if scores is None:
        scores = result.scores
    scores = np.asarray(scores, dtype=float)
    if scores.ndim == 1:
        scores = scores[None, :]
    if scores.ndim != 2:
        raise ValueError("scores must be a one- or two-dimensional array")
    if n_components is None:
        n_components = min(scores.shape[1], result.n_components)
    if n_components < 1 or n_components > result.n_components:
        raise ValueError("n_components is outside the fitted range")
    if scores.shape[1] < n_components:
        raise ValueError("scores contain fewer columns than requested components")
    return result.mean[None, :, :] + np.einsum(
        "nk,ktd->ntd", scores[:, :n_components], result.components[:n_components]
    )


def component_trajectories(
    result: FPCAResult,
    component: int,
    *,
    sd_multipliers: tuple[float, ...] = (-2.0, -1.0, 0.0, 1.0, 2.0),
) -> np.ndarray:
    """Return mean ± score-SD trajectories for interpreting one component."""

    if component < 0 or component >= result.n_components:
        raise IndexError("component is outside the fitted range")
    sd = float(np.sqrt(result.explained_variance[component]))
    multipliers = np.asarray(sd_multipliers, dtype=float)
    return result.mean[None, :, :] + multipliers[:, None, None] * sd * result.components[component]


def select_n_components(result: FPCAResult, *, threshold: float = 0.95) -> int:
    """Smallest number of components reaching a cumulative variance threshold."""

    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    cumulative = np.cumsum(result.explained_variance_ratio)
    return int(np.searchsorted(cumulative, threshold, side="left") + 1)


def fpca_score_frame(result: FPCAResult, *, prefix: str = "FPC"):
    """Return component scores as a tidy pandas DataFrame."""

    import pandas as pd

    columns = [f"{prefix}{i + 1}" for i in range(result.n_components)]
    frame = pd.DataFrame(result.scores, columns=columns)
    frame.insert(0, "curve_id", result.curve_ids)
    return frame
