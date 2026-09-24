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
    DynamicTimeWarpingResult,
    FPCAResult,
    FunctionalRegressionResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def _validate_discrete_frechet_inputs(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate two complete point sequences for discrete Fréchet analysis."""

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
            "discrete Fréchet distance requires finite complete point sequences"
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
    a_arr, b_arr, weights = _validate_discrete_frechet_inputs(
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
        _validate_discrete_frechet_inputs(
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


def _validate_dynamic_time_warping_inputs(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | None,
    window_radius: int | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int | None]:
    """Validate two complete point sequences for dynamic time warping."""

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
            "dynamic time warping requires finite complete point sequences"
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

    if window_radius is not None:
        if isinstance(window_radius, (bool, np.bool_)) or not isinstance(
            window_radius, (int, np.integer)
        ):
            raise TypeError("window_radius must be an integer or None")
        window_radius = int(window_radius)
        if window_radius < 0:
            raise ValueError("window_radius must be non-negative")
        minimum = abs(a_arr.shape[0] - b_arr.shape[0])
        if window_radius < minimum:
            raise ValueError(
                "window_radius is too small to connect the sequence endpoints"
            )

    return a_arr, b_arr, weights, window_radius


def _validate_dynamic_time_warping_options(
    *,
    step_pattern: str,
    normalize: bool,
) -> tuple[str, bool]:
    """Validate the declared DTW recursion and normalization contract."""

    if not isinstance(step_pattern, str):
        raise TypeError("step_pattern must be a string")
    if step_pattern not in {"symmetric1", "symmetric2"}:
        raise ValueError("step_pattern must be 'symmetric1' or 'symmetric2'")
    if not isinstance(normalize, (bool, np.bool_)):
        raise TypeError("normalize must be boolean")
    normalize_bool = bool(normalize)
    if normalize_bool and step_pattern != "symmetric2":
        raise ValueError(
            "normalize=True is available only for the normalizable "
            "'symmetric2' step pattern"
        )
    return step_pattern, normalize_bool


def dynamic_time_warping_distance(
    a: np.ndarray,
    b: np.ndarray,
    *,
    dimension_weights: np.ndarray | None = None,
    window_radius: int | None = None,
    step_pattern: str = "symmetric1",
    normalize: bool = False,
    return_path: bool = False,
) -> float | DynamicTimeWarpingResult:
    """Compute DTW using explicit symmetric1 or symmetric2 step weighting.

    symmetric1 preserves the 0.33 contract: every visited local distance
    contributes once and the resulting cumulative cost is not normalizable by
    a path-independent length denominator.

    symmetric2 gives diagonal moves weight two and horizontal/vertical
    moves weight one. Its cumulative cost can be normalized by n_a + n_b.
    Set normalize=True to return that normalized value.

    window_radius is an optional Sakoe-Chiba band in sample-index units.
    Recorded timestamps are not used. No interpolation, resampling, smoothing,
    coordinate normalization, path simplification, missing-value deletion, or
    automatic step-pattern/window selection is performed.
    """

    if not isinstance(return_path, (bool, np.bool_)):
        raise TypeError("return_path must be boolean")
    resolved_pattern, normalize_bool = _validate_dynamic_time_warping_options(
        step_pattern=step_pattern,
        normalize=normalize,
    )

    a_arr, b_arr, weights, resolved_window = _validate_dynamic_time_warping_inputs(
        a,
        b,
        dimension_weights=dimension_weights,
        window_radius=window_radius,
    )
    n_a, n_b = a_arr.shape[0], b_arr.shape[0]
    local = np.sqrt(
        np.sum(
            (a_arr[:, None, :] - b_arr[None, :, :]) ** 2
            * weights[None, None, :],
            axis=2,
        )
    )

    cumulative = np.full((n_a, n_b), np.inf, dtype=float)
    predecessor = np.full((n_a, n_b, 2), -1, dtype=int)
    transition_weight = np.full((n_a, n_b), np.nan, dtype=float)

    initial_weight = 2.0 if resolved_pattern == "symmetric2" else 1.0
    cumulative[0, 0] = initial_weight * local[0, 0]
    transition_weight[0, 0] = initial_weight

    for i in range(n_a):
        if resolved_window is None:
            j_start, j_stop = 0, n_b
        else:
            j_start = max(0, i - resolved_window)
            j_stop = min(n_b, i + resolved_window + 1)

        for j in range(j_start, j_stop):
            if i == 0 and j == 0:
                continue

            candidates: list[tuple[float, int, int, float]] = []
            if i > 0 and j > 0 and np.isfinite(cumulative[i - 1, j - 1]):
                step_weight = 2.0 if resolved_pattern == "symmetric2" else 1.0
                candidates.append(
                    (
                        cumulative[i - 1, j - 1] + step_weight * local[i, j],
                        i - 1,
                        j - 1,
                        step_weight,
                    )
                )
            if i > 0 and np.isfinite(cumulative[i - 1, j]):
                candidates.append(
                    (
                        cumulative[i - 1, j] + local[i, j],
                        i - 1,
                        j,
                        1.0,
                    )
                )
            if j > 0 and np.isfinite(cumulative[i, j - 1]):
                candidates.append(
                    (
                        cumulative[i, j - 1] + local[i, j],
                        i,
                        j - 1,
                        1.0,
                    )
                )
            if not candidates:
                continue

            total, prev_i, prev_j, step_weight = min(
                candidates,
                key=lambda item: item[0],
            )
            cumulative[i, j] = total
            predecessor[i, j] = (prev_i, prev_j)
            transition_weight[i, j] = step_weight

    raw_distance = float(cumulative[-1, -1])
    if not np.isfinite(raw_distance):
        raise ValueError(
            "No admissible DTW path reaches the endpoint under window_radius"
        )

    normalization_denominator = (
        float(n_a + n_b) if resolved_pattern == "symmetric2" else None
    )
    normalized_distance = (
        raw_distance / normalization_denominator
        if normalization_denominator is not None
        else None
    )
    distance = (
        float(normalized_distance)
        if normalize_bool and normalized_distance is not None
        else raw_distance
    )
    if not return_path:
        return distance

    path: list[tuple[int, int]] = []
    path_weights: list[float] = []
    i, j = n_a - 1, n_b - 1
    while True:
        path.append((i, j))
        path_weights.append(float(transition_weight[i, j]))
        if i == 0 and j == 0:
            break
        prev_i, prev_j = predecessor[i, j]
        if prev_i < 0 or prev_j < 0:
            raise RuntimeError("DTW predecessor chain is incomplete")
        i, j = int(prev_i), int(prev_j)
    path.reverse()
    path_weights.reverse()

    alignment_path = np.asarray(path, dtype=int)
    step_weights = np.asarray(path_weights, dtype=float)
    aligned_local = local[alignment_path[:, 0], alignment_path[:, 1]]
    weighted_local = aligned_local * step_weights
    if not np.isclose(np.sum(weighted_local), raw_distance):
        raise RuntimeError("DTW path audit does not reproduce the cumulative cost")

    return DynamicTimeWarpingResult(
        distance=distance,
        path=alignment_path,
        local_distances=aligned_local,
        path_length=len(path),
        mean_local_distance=float(np.mean(aligned_local)),
        n_points_a=n_a,
        n_points_b=n_b,
        n_dimensions=a_arr.shape[1],
        window_radius=resolved_window,
        raw_distance=raw_distance,
        normalized_distance=normalized_distance,
        step_pattern=resolved_pattern,
        normalization_denominator=normalization_denominator,
        step_weights=step_weights,
        weighted_local_costs=weighted_local,
        provenance={
            "operation": "dynamic_time_warping_distance",
            "local_metric": "weighted_euclidean",
            "dimension_weights": weights.tolist(),
            "distance_aggregation": "weighted_sum",
            "step_pattern": resolved_pattern,
            "normalizable": resolved_pattern == "symmetric2",
            "normalization_requested": normalize_bool,
            "normalization_denominator": normalization_denominator,
            "distance_returned": (
                "normalized" if normalize_bool else "raw_cumulative"
            ),
            "recorded_time_used": False,
            "sequence_index_warping": True,
            "sample_order_preserved": True,
            "backtracking_allowed": False,
            "window_constraint": (
                "unconstrained"
                if resolved_window is None
                else "sakoe_chiba_index_band"
            ),
            "window_radius": resolved_window,
            "interpolation": False,
            "resampling": False,
            "smoothing": False,
            "coordinate_normalization": False,
            "path_simplification": False,
            "missing_value_deletion": False,
            "automatic_step_pattern_selection": False,
            "automatic_window_selection": False,
            "tie_break_order": ("diagonal", "advance_a", "advance_b"),
            "optimal_path_not_necessarily_unique": True,
        },
    )


def pairwise_dynamic_time_warping_distances(
    trajectories: TrajectorySet,
    *,
    dimensions: tuple[str, ...] | list[str] | None = None,
    dimension_weights: np.ndarray | None = None,
    window_radius: int | None = None,
    step_pattern: str = "symmetric1",
    normalize: bool = False,
) -> np.ndarray:
    """Pairwise DTW distances for complete trajectories.

    The TrajectorySet time grid is not passed into the recurrence.
    window_radius constrains sample-index displacement, not physical time.
    The 0.33 symmetric1 raw-cost behavior remains the default.
    """

    resolved_pattern, normalize_bool = _validate_dynamic_time_warping_options(
        step_pattern=step_pattern,
        normalize=normalize,
    )
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
        _validate_dynamic_time_warping_inputs(
            values[0],
            values[0],
            dimension_weights=dimension_weights,
            window_radius=window_radius,
        )

    result = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            distance = dynamic_time_warping_distance(
                values[i],
                values[j],
                dimension_weights=dimension_weights,
                window_radius=window_radius,
                step_pattern=resolved_pattern,
                normalize=normalize_bool,
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
