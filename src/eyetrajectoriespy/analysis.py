"""Downstream analyses built on functional representations and FPCA scores."""

from __future__ import annotations

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
