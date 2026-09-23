"""Downstream analyses built on functional representations and FPCA scores."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances

from .fpca import functional_trapezoid_weights
from .types import ClusterResult, FPCAResult, FunctionalRegressionResult, TrajectorySet
from .validation import validate_trajectory_set


def functional_l2_distance(
    a: np.ndarray,
    b: np.ndarray,
    *,
    time: np.ndarray,
    dimension_weights: np.ndarray | None = None,
) -> float:
    """Integrated L2 distance between two complete multivariate functions."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape or a.ndim != 2:
        raise ValueError("a and b must have the same shape (n_time, n_dimensions)")
    if np.isnan(a).any() or np.isnan(b).any():
        raise ValueError("functional_l2_distance requires complete trajectories")
    weights = functional_trapezoid_weights(time)
    if dimension_weights is None:
        dw = np.ones(a.shape[1])
    else:
        dw = np.asarray(dimension_weights, dtype=float)
        if dw.shape != (a.shape[1],) or np.any(dw < 0):
            raise ValueError("dimension_weights must be non-negative with one value per dimension")
    squared = (a - b) ** 2 * dw[None, :]
    return float(np.sqrt(np.sum(squared * weights[:, None])))


def pairwise_functional_distances(
    trajectories: TrajectorySet,
    *,
    dimension_weights: np.ndarray | None = None,
) -> np.ndarray:
    """Pairwise integrated L2 distance matrix for complete trajectories."""
    validate_trajectory_set(trajectories, require_complete=True)
    n = trajectories.n_curves
    result = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = functional_l2_distance(
                trajectories.values[i],
                trajectories.values[j],
                time=trajectories.time,
                dimension_weights=dimension_weights,
            )
            result[i, j] = result[j, i] = d
    return result



def _frechet_path_array(values: np.ndarray, *, name: str) -> np.ndarray:
    """Validate one finite non-empty sampled curve for discrete Fréchet analysis."""

    array = np.asarray(values, dtype=float)
    if array.ndim != 2:
        raise ValueError(f"{name} must have shape (n_points, n_dimensions)")
    if array.shape[0] < 1 or array.shape[1] < 1:
        raise ValueError(f"{name} must contain at least one point and one dimension")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _frechet_dimension_weights(
    dimension_weights: np.ndarray | Sequence[float] | None,
    *,
    n_dimensions: int,
) -> np.ndarray:
    if dimension_weights is None:
        return np.ones(n_dimensions, dtype=float)
    weights = np.asarray(dimension_weights, dtype=float)
    if weights.shape != (n_dimensions,):
        raise ValueError(
            "dimension_weights must contain one value per compared dimension"
        )
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError("dimension_weights must be finite and strictly positive")
    return weights


def discrete_frechet_distance(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | Sequence[float] | None = None,
) -> float:
    """Compute the discrete Fréchet distance between two sampled curves.

    The point metric is weighted Euclidean distance. The dynamic program
    preserves point order but may advance one curve while holding the other
    curve's current point. Actual timestamps are not part of this distance.

    The implementation uses rolling dynamic-programming rows, so auxiliary
    memory is O(min(n_a, n_b)); runtime remains O(n_a * n_b).
    """

    left = _frechet_path_array(a, name="a")
    right = _frechet_path_array(b, name="b")
    if left.shape[1] != right.shape[1]:
        raise ValueError("a and b must have the same number of dimensions")
    weights = _frechet_dimension_weights(
        dimension_weights,
        n_dimensions=left.shape[1],
    )

    # Keep the shorter sequence on the dynamic-programming columns so the
    # auxiliary memory contract is O(min(n_a, n_b)).
    if right.shape[0] > left.shape[0]:
        left, right = right, left

    previous = np.empty(right.shape[0], dtype=float)
    current = np.empty(right.shape[0], dtype=float)

    for i in range(left.shape[0]):
        point_distances = np.sqrt(
            np.sum(
                (right - left[i][None, :]) ** 2 * weights[None, :],
                axis=1,
            )
        )
        for j in range(right.shape[0]):
            distance = float(point_distances[j])
            if i == 0 and j == 0:
                current[j] = distance
            elif i == 0:
                current[j] = max(current[j - 1], distance)
            elif j == 0:
                current[j] = max(previous[j], distance)
            else:
                current[j] = max(
                    distance,
                    min(previous[j], previous[j - 1], current[j - 1]),
                )
        previous, current = current, previous

    return float(previous[-1])


def pairwise_discrete_frechet_distances(
    trajectories: TrajectorySet,
    *,
    dimensions: Sequence[str] | None = None,
    dimension_weights: np.ndarray | Sequence[float] | None = None,
) -> np.ndarray:
    """Pairwise discrete Fréchet distances for complete sampled trajectories.

    Unlike integrated functional L2 distance, this comparison does not require
    point i in one curve to correspond to point i in the other. It preserves
    traversal order while allowing monotone differences in progression along
    the sampled paths. The TrajectorySet time grid is therefore not included
    in the distance itself.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if dimensions is None:
        names = trajectories.dimension_names
    else:
        if isinstance(dimensions, (str, bytes)):
            raise TypeError("dimensions must be a non-string sequence of names")
        names = tuple(dimensions)
        if not names:
            raise ValueError("dimensions must contain at least one name")
        if len(set(names)) != len(names):
            raise ValueError("dimensions must not contain duplicates")
        missing = [name for name in names if name not in trajectories.dimension_names]
        if missing:
            raise KeyError(f"Unknown trajectory dimensions: {missing}")
    indices = tuple(trajectories.dimension_names.index(name) for name in names)
    weights = _frechet_dimension_weights(
        dimension_weights,
        n_dimensions=len(indices),
    )

    n = trajectories.n_curves
    result = np.zeros((n, n), dtype=float)
    for i in range(n):
        a = trajectories.values[i][:, indices]
        for j in range(i + 1, n):
            b = trajectories.values[j][:, indices]
            distance = discrete_frechet_distance(
                a,
                b,
                dimension_weights=weights,
            )
            result[i, j] = result[j, i] = distance
    return result



def cluster_fpca_scores(
    fpca: FPCAResult,
    *,
    n_clusters: int,
    n_components: int | None = None,
    random_state: int = 0,
    n_init: int | str = "auto",
) -> ClusterResult:
    """Cluster curves using a deterministic K-means fit to retained FPCA scores."""
    if n_clusters < 2 or n_clusters > len(fpca.curve_ids):
        raise ValueError("n_clusters must be between 2 and number of trajectories")
    if n_components is None:
        n_components = fpca.n_components
    if n_components < 1 or n_components > fpca.n_components:
        raise ValueError("n_components is outside the fitted FPCA range")
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    labels = model.fit_predict(fpca.scores[:, :n_components])
    return ClusterResult(
        labels=labels,
        centers=model.cluster_centers_,
        method="kmeans_fpca_scores",
        model=model,
        provenance={"n_components": n_components, "n_clusters": n_clusters, "random_state": random_state},
    )


def fit_scalar_on_function_regression(
    fpca: FPCAResult,
    outcome: np.ndarray | pd.Series,
    *,
    n_components: int | None = None,
    family: str = "gaussian",
    covariates: pd.DataFrame | None = None,
) -> FunctionalRegressionResult:
    """Approximate scalar-on-function regression through FPCA score predictors."""
    y = np.asarray(outcome, dtype=float)
    if y.shape != (len(fpca.curve_ids),):
        raise ValueError("outcome must contain exactly one value per trajectory")
    if np.isnan(y).any():
        raise ValueError("outcome contains missing values; handle them explicitly")
    if n_components is None:
        n_components = fpca.n_components
    if n_components < 1 or n_components > fpca.n_components:
        raise ValueError("n_components is outside the fitted range")

    x = pd.DataFrame(fpca.scores[:, :n_components], columns=[f"FPC{i + 1}" for i in range(n_components)])
    if covariates is not None:
        if len(covariates) != len(x):
            raise ValueError("covariates must contain one row per trajectory")
        if covariates.isna().any().any():
            raise ValueError("covariates contain missing values")
        x = pd.concat([x, covariates.reset_index(drop=True)], axis=1)
    x = sm.add_constant(x, has_constant="add")

    if family == "gaussian":
        model = sm.OLS(y, x).fit()
    elif family == "binomial":
        if not set(np.unique(y)) <= {0.0, 1.0}:
            raise ValueError("binomial outcome must contain only 0/1 values")
        model = sm.GLM(y, x, family=sm.families.Binomial()).fit()
    else:
        raise ValueError("family must be 'gaussian' or 'binomial'")

    return FunctionalRegressionResult(
        model=model,
        component_indices=tuple(range(n_components)),
        coefficients=pd.Series(model.params, index=x.columns),
        predictions=np.asarray(model.predict(x)),
        family=family,
        provenance={
            "method": "scalar_on_function_via_fpca_scores",
            "n_components": n_components,
            "family": family,
            "covariates": [] if covariates is None else list(covariates.columns),
        },
    )


def nearest_trajectory_indices(trajectories: TrajectorySet, *, index: int, n_neighbors: int = 5) -> np.ndarray:
    """Indices of nearest curves under integrated functional L2 distance."""
    if index < 0 or index >= trajectories.n_curves:
        raise IndexError("index is outside the trajectory set")
    if n_neighbors < 1:
        raise ValueError("n_neighbors must be positive")
    distances = pairwise_functional_distances(trajectories)
    order = np.argsort(distances[index])
    order = order[order != index]
    return order[:n_neighbors]


def score_distance_matrix(fpca: FPCAResult, *, n_components: int | None = None) -> np.ndarray:
    """Euclidean pairwise distances in retained FPCA score space."""
    if n_components is None:
        n_components = fpca.n_components
    if n_components < 1 or n_components > fpca.n_components:
        raise ValueError("n_components is outside the fitted range")
    return pairwise_distances(fpca.scores[:, :n_components], metric="euclidean")
