"""Downstream analyses built on functional representations and FPCA scores."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances

from .fpca import functional_trapezoid_weights
from .types import (
    ClusterResult,
    DiscreteFrechetResult,
    FPCAResult,
    FunctionalRegressionResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _validate_trajectory_sequence_inputs(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate two complete point sequences for elastic trajectory analysis."""

    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.ndim != 2 or b_arr.ndim != 2:
        raise ValueError("a and b must have shape (n_points, n_dimensions)")
    if a_arr.shape[0] < 1 or b_arr.shape[0] < 1:
        raise ValueError("a and b must each contain at least one point")
    if a_arr.shape[1] != b_arr.shape[1]:
        raise ValueError("a and b must have the same number of dimensions")
    if a_arr.shape[1] < 1:
        raise ValueError("a and b must contain at least one dimension")
    if not np.all(np.isfinite(a_arr)) or not np.all(np.isfinite(b_arr)):
        raise ValueError(
            "elastic trajectory comparison requires finite complete point sequences"
        )

    if dimension_weights is None:
        weights = np.ones(a_arr.shape[1], dtype=float)
    else:
        weights = np.asarray(dimension_weights, dtype=float)
        if weights.shape != (a_arr.shape[1],):
            raise ValueError(
                "dimension_weights must contain one value per dimension"
            )
        if not np.all(np.isfinite(weights)) or np.any(weights < 0):
            raise ValueError(
                "dimension_weights must contain finite non-negative values"
            )
        if not np.any(weights > 0):
            raise ValueError(
                "dimension_weights must contain at least one positive value"
            )
    return a_arr, b_arr, weights


def discrete_frechet_distance(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | None = None,
    return_coupling: bool = False,
) -> float | DiscreteFrechetResult:
    """Compute discrete Fréchet distance between ordered point sequences.

    The coupling is monotone in both sequence indices. Elapsed time is not
    used. No interpolation, resampling, coordinate normalization, or path
    simplification is performed.

    With return_coupling=True, one deterministic optimal coupling is returned.
    Multiple optimal couplings can exist; ties prefer a diagonal predecessor,
    then advancing a, then advancing b.
    """

    if not isinstance(return_coupling, (bool, np.bool_)):
        raise TypeError("return_coupling must be boolean")
    a_arr, b_arr, weights = _validate_trajectory_sequence_inputs(
        a, b, dimension_weights=dimension_weights
    )
    n_a, n_b = a_arr.shape[0], b_arr.shape[0]
    local = np.sqrt(
        np.sum(
            (a_arr[:, None, :] - b_arr[None, :, :]) ** 2
            * weights[None, None, :],
            axis=2,
        )
    )

    cumulative = np.empty((n_a, n_b), dtype=float)
    predecessor = np.full((n_a, n_b, 2), -1, dtype=int)
    cumulative[0, 0] = local[0, 0]

    for i in range(1, n_a):
        cumulative[i, 0] = max(cumulative[i - 1, 0], local[i, 0])
        predecessor[i, 0] = (i - 1, 0)
    for j in range(1, n_b):
        cumulative[0, j] = max(cumulative[0, j - 1], local[0, j])
        predecessor[0, j] = (0, j - 1)

    for i in range(1, n_a):
        for j in range(1, n_b):
            candidates = (
                (cumulative[i - 1, j - 1], i - 1, j - 1),
                (cumulative[i - 1, j], i - 1, j),
                (cumulative[i, j - 1], i, j - 1),
            )
            previous, prev_i, prev_j = min(candidates, key=lambda item: item[0])
            cumulative[i, j] = max(local[i, j], previous)
            predecessor[i, j] = (prev_i, prev_j)

    distance = float(cumulative[-1, -1])
    if not return_coupling:
        return distance

    path: list[tuple[int, int]] = []
    i, j = n_a - 1, n_b - 1
    while True:
        path.append((i, j))
        if i == 0 and j == 0:
            break
        i, j = predecessor[i, j]
    path.reverse()
    coupling = np.asarray(path, dtype=int)
    coupled_local = local[coupling[:, 0], coupling[:, 1]]
    return DiscreteFrechetResult(
        distance=distance,
        coupling=coupling,
        local_distances=coupled_local,
        n_points_a=n_a,
        n_points_b=n_b,
        n_dimensions=a_arr.shape[1],
        provenance={
            "operation": "discrete_frechet_distance",
            "local_metric": "weighted_euclidean",
            "dimension_weights": weights.tolist(),
            "continuous_frechet": False,
            "elapsed_time_used": False,
            "sample_order_preserved": True,
            "backtracking_allowed": False,
            "interpolation": False,
            "resampling": False,
            "coordinate_normalization": False,
            "path_simplification": False,
            "tie_break_order": ("diagonal", "advance_a", "advance_b"),
            "optimal_coupling_not_necessarily_unique": True,
        },
    )


def pairwise_discrete_frechet_distances(
    trajectories: TrajectorySet,
    *,
    dimensions: tuple[str, ...] | list[str] | None = None,
    dimension_weights: np.ndarray | None = None,
) -> np.ndarray:
    """Pairwise discrete Fréchet distances for complete trajectories.

    dimensions=None uses every stored functional dimension in its current
    order. No time values are passed to the Fréchet recurrence.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if dimensions is None:
        selected = trajectories.dimension_names
    else:
        if isinstance(dimensions, (str, bytes)):
            raise TypeError("dimensions must be a non-string sequence")
        selected = tuple(dimensions)
        if not selected:
            raise ValueError("dimensions must contain at least one dimension")
        if len(set(selected)) != len(selected):
            raise ValueError("dimensions must not contain duplicates")
        missing = [
            name for name in selected if name not in trajectories.dimension_names
        ]
        if missing:
            raise KeyError(f"Unknown trajectory dimensions: {missing}")

    indices = [trajectories.dimension_names.index(name) for name in selected]
    values = trajectories.values[:, :, indices]
    n = trajectories.n_curves
    if n > 0:
        _validate_trajectory_sequence_inputs(
            values[0],
            values[0],
            dimension_weights=dimension_weights,
        )
    result = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            distance = discrete_frechet_distance(
                values[i], values[j], dimension_weights=dimension_weights
            )
            result[i, j] = result[j, i] = float(distance)
    return result


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
