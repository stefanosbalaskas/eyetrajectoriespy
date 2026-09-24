"""Sensitivity analysis across declared trajectory-distance contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .analysis import (
    discrete_frechet_distance,
    dynamic_time_warping_distance,
    functional_l2_distance,
)
from .types import TrajectoryDistanceSensitivityResult, TrajectorySet
from .validation import validate_trajectory_set


_ALLOWED_METHODS = {
    "functional_l2",
    "discrete_frechet",
    "dtw",
}


def _validate_dimensions(
    trajectories: TrajectorySet,
    dimensions: Sequence[str] | None,
) -> tuple[tuple[str, ...], np.ndarray]:
    if dimensions is None:
        names = trajectories.dimension_names
    else:
        if isinstance(dimensions, (str, bytes)):
            raise TypeError("dimensions must be a non-string sequence")
        names = tuple(dimensions)
        if not names:
            raise ValueError("dimensions must contain at least one dimension")
        if not all(isinstance(name, str) for name in names):
            raise TypeError("dimension names must be strings")
        if len(set(names)) != len(names):
            raise ValueError("dimensions must not contain duplicates")
        missing = [
            name for name in names
            if name not in trajectories.dimension_names
        ]
        if missing:
            raise KeyError(f"Unknown trajectory dimensions: {missing}")

    indices = np.asarray(
        [trajectories.dimension_names.index(name) for name in names],
        dtype=int,
    )
    return tuple(names), indices


def _validate_dimension_weights(
    n_dimensions: int,
    dimension_weights: np.ndarray | Sequence[float] | None,
) -> np.ndarray:
    if dimension_weights is None:
        weights = np.ones(n_dimensions, dtype=float)
    else:
        weights = np.asarray(dimension_weights, dtype=float)
        if weights.shape != (n_dimensions,):
            raise ValueError(
                "dimension_weights must contain one value per selected "
                "dimension"
            )
        if not np.all(np.isfinite(weights)):
            raise ValueError("dimension_weights must be finite")
        if np.any(weights < 0):
            raise ValueError("dimension_weights must be non-negative")
        if not np.any(weights > 0):
            raise ValueError(
                "dimension_weights must contain at least one positive value"
            )
    return weights


def _validate_specifications(
    specifications: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    if isinstance(specifications, (str, bytes)):
        raise TypeError("specifications must be a non-string sequence")
    raw = tuple(specifications)
    if len(raw) < 2:
        raise ValueError(
            "trajectory distance sensitivity requires at least two "
            "specifications"
        )

    normalized: list[dict[str, Any]] = []
    names: list[str] = []
    for index, specification in enumerate(raw):
        if not isinstance(specification, Mapping):
            raise TypeError(
                "every distance specification must be a mapping"
            )
        if "name" not in specification or "method" not in specification:
            raise ValueError(
                "each distance specification requires 'name' and 'method'"
            )

        name = specification["name"]
        method = specification["method"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"specification {index} name must be a non-empty string"
            )
        if not isinstance(method, str):
            raise TypeError(
                f"specification {name!r} method must be a string"
            )
        if method not in _ALLOWED_METHODS:
            raise ValueError(
                f"specification {name!r} method must be one of "
                f"{sorted(_ALLOWED_METHODS)}"
            )

        if method == "dtw":
            allowed = {
                "name",
                "method",
                "step_pattern",
                "normalize",
                "window_radius",
            }
            unknown = set(specification) - allowed
            if unknown:
                raise ValueError(
                    f"specification {name!r} contains unsupported DTW "
                    f"options: {sorted(unknown)}"
                )
            step_pattern = specification.get(
                "step_pattern",
                "symmetric1",
            )
            normalize = specification.get("normalize", False)
            window_radius = specification.get("window_radius", None)
            # Validate the declared DTW option contract through the public
            # implementation on a tiny complete pair later; here retain the
            # options without coercion.
            normalized.append(
                {
                    "name": name,
                    "method": method,
                    "step_pattern": step_pattern,
                    "normalize": normalize,
                    "window_radius": window_radius,
                }
            )
        else:
            allowed = {"name", "method"}
            unknown = set(specification) - allowed
            if unknown:
                raise ValueError(
                    f"specification {name!r} contains options not supported "
                    f"for method {method!r}: {sorted(unknown)}"
                )
            normalized.append(
                {
                    "name": name,
                    "method": method,
                }
            )
        names.append(name)

    if len(set(names)) != len(names):
        raise ValueError("distance specification names must be unique")
    return tuple(normalized)


def _pairwise_distance_matrix(
    values: np.ndarray,
    time: np.ndarray,
    *,
    specification: Mapping[str, Any],
    dimension_weights: np.ndarray,
) -> np.ndarray:
    n_curves = values.shape[0]
    matrix = np.zeros((n_curves, n_curves), dtype=float)

    for left in range(n_curves):
        for right in range(left + 1, n_curves):
            if specification["method"] == "functional_l2":
                distance = functional_l2_distance(
                    values[left],
                    values[right],
                    time=time,
                    dimension_weights=dimension_weights,
                )
            elif specification["method"] == "discrete_frechet":
                distance = discrete_frechet_distance(
                    values[left],
                    values[right],
                    dimension_weights=dimension_weights,
                )
            else:
                distance = dynamic_time_warping_distance(
                    values[left],
                    values[right],
                    dimension_weights=dimension_weights,
                    step_pattern=specification["step_pattern"],
                    normalize=specification["normalize"],
                    window_radius=specification["window_radius"],
                )
            matrix[left, right] = matrix[right, left] = float(distance)
    return matrix


def _neighbor_orders(
    matrix: np.ndarray,
    *,
    neighbor_k: int,
) -> tuple[np.ndarray, np.ndarray]:
    n_curves = matrix.shape[0]
    orders = np.empty((n_curves, neighbor_k), dtype=int)
    cutoff_ties = np.zeros(n_curves, dtype=bool)

    for curve_index in range(n_curves):
        candidates = np.delete(np.arange(n_curves), curve_index)
        distances = matrix[curve_index, candidates]
        order = np.argsort(distances, kind="mergesort")
        ranked_candidates = candidates[order]
        ranked_distances = distances[order]
        orders[curve_index] = ranked_candidates[:neighbor_k]

        if neighbor_k < ranked_distances.size:
            cutoff_ties[curve_index] = bool(
                np.isclose(
                    ranked_distances[neighbor_k - 1],
                    ranked_distances[neighbor_k],
                    rtol=1e-12,
                    atol=0.0,
                )
            )
    return orders, cutoff_ties


def trajectory_distance_sensitivity(
    trajectories: TrajectorySet,
    specifications: Sequence[Mapping[str, Any]],
    *,
    dimensions: Sequence[str] | None = None,
    dimension_weights: np.ndarray | Sequence[float] | None = None,
    neighbor_k: int = 3,
) -> TrajectoryDistanceSensitivityResult:
    """Compare trajectory-distance conclusions across declared specifications.

    The function compares the *same* complete trajectories and selected
    dimensions under at least two explicitly declared distance contracts.
    It returns all raw distance matrices, global pairwise-distance rank
    agreement, and local nearest-neighbor overlap.

    No distance matrix is standardized, rescaled, averaged into a consensus,
    or assigned a preferred metric. Correlation quantities are descriptive:
    no p-values are computed because the upper-triangle pair distances are not
    independent observations.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if trajectories.n_curves < 3:
        raise ValueError(
            "trajectory distance sensitivity requires at least three curves"
        )
    if (
        isinstance(neighbor_k, bool)
        or not isinstance(neighbor_k, (int, np.integer))
    ):
        raise TypeError("neighbor_k must be an integer")
    neighbor_k = int(neighbor_k)
    if neighbor_k < 1 or neighbor_k >= trajectories.n_curves:
        raise ValueError(
            "neighbor_k must be between 1 and n_curves - 1"
        )

    dimension_names, dimension_indices = _validate_dimensions(
        trajectories,
        dimensions,
    )
    weights = _validate_dimension_weights(
        len(dimension_names),
        dimension_weights,
    )
    specs = _validate_specifications(specifications)

    values = trajectories.values[:, :, dimension_indices]
    n_specs = len(specs)
    n_curves = trajectories.n_curves
    matrices = np.empty(
        (n_specs, n_curves, n_curves),
        dtype=float,
    )

    for specification_index, specification in enumerate(specs):
        matrices[specification_index] = _pairwise_distance_matrix(
            values,
            trajectories.time,
            specification=specification,
            dimension_weights=weights,
        )

    upper = np.triu_indices(n_curves, k=1)
    condensed = matrices[:, upper[0], upper[1]]
    ranks = np.vstack(
        [
            stats.rankdata(row, method="average")
            for row in condensed
        ]
    )

    neighbor_orders = np.empty(
        (n_specs, n_curves, neighbor_k),
        dtype=int,
    )
    cutoff_ties = np.empty((n_specs, n_curves), dtype=bool)
    for specification_index in range(n_specs):
        (
            neighbor_orders[specification_index],
            cutoff_ties[specification_index],
        ) = _neighbor_orders(
            matrices[specification_index],
            neighbor_k=neighbor_k,
        )

    comparison_rows: list[dict[str, Any]] = []
    neighbor_rows: list[dict[str, Any]] = []
    for left in range(n_specs):
        for right in range(left + 1, n_specs):
            left_vector = condensed[left]
            right_vector = condensed[right]
            spearman = float(
                stats.spearmanr(
                    left_vector,
                    right_vector,
                ).statistic
            )
            if np.std(left_vector) > 0 and np.std(right_vector) > 0:
                pearson = float(
                    np.corrcoef(left_vector, right_vector)[0, 1]
                )
            else:
                pearson = float("nan")

            rank_difference = np.abs(ranks[left] - ranks[right])
            jaccards: list[float] = []
            exact_sets: list[bool] = []
            nearest_matches: list[bool] = []

            for curve_index in range(n_curves):
                left_neighbors = tuple(
                    int(value)
                    for value in neighbor_orders[left, curve_index]
                )
                right_neighbors = tuple(
                    int(value)
                    for value in neighbor_orders[right, curve_index]
                )
                left_set = set(left_neighbors)
                right_set = set(right_neighbors)
                intersection = len(left_set & right_set)
                union = len(left_set | right_set)
                jaccard = (
                    float(intersection / union)
                    if union > 0
                    else 1.0
                )
                exact_set = left_set == right_set
                nearest_match = (
                    left_neighbors[0] == right_neighbors[0]
                )
                jaccards.append(jaccard)
                exact_sets.append(exact_set)
                nearest_matches.append(nearest_match)
                neighbor_rows.append(
                    {
                        "specification_a": specs[left]["name"],
                        "specification_b": specs[right]["name"],
                        "curve_id": trajectories.curve_ids[curve_index],
                        "neighbor_k": neighbor_k,
                        "neighbors_a": tuple(
                            trajectories.curve_ids[index]
                            for index in left_neighbors
                        ),
                        "neighbors_b": tuple(
                            trajectories.curve_ids[index]
                            for index in right_neighbors
                        ),
                        "overlap_count": intersection,
                        "jaccard": jaccard,
                        "exact_neighbor_set_match": exact_set,
                        "nearest_neighbor_match": nearest_match,
                        "cutoff_tie_a": bool(
                            cutoff_ties[left, curve_index]
                        ),
                        "cutoff_tie_b": bool(
                            cutoff_ties[right, curve_index]
                        ),
                    }
                )

            comparison_rows.append(
                {
                    "specification_a": specs[left]["name"],
                    "specification_b": specs[right]["name"],
                    "n_curve_pairs": condensed.shape[1],
                    "spearman_rank_correlation": spearman,
                    "pearson_raw_distance_correlation": pearson,
                    "mean_absolute_rank_difference": float(
                        np.mean(rank_difference)
                    ),
                    "median_absolute_rank_difference": float(
                        np.median(rank_difference)
                    ),
                    "maximum_absolute_rank_difference": float(
                        np.max(rank_difference)
                    ),
                    "mean_top_k_neighbor_jaccard": float(
                        np.mean(jaccards)
                    ),
                    "exact_top_k_neighbor_set_agreement_fraction": float(
                        np.mean(exact_sets)
                    ),
                    "nearest_neighbor_identity_agreement_fraction": float(
                        np.mean(nearest_matches)
                    ),
                    "any_neighbor_cutoff_tie": bool(
                        np.any(cutoff_ties[left])
                        or np.any(cutoff_ties[right])
                    ),
                }
            )

    specification_table = pd.DataFrame(
        [
            {
                "name": specification["name"],
                "method": specification["method"],
                "step_pattern": specification.get("step_pattern"),
                "normalize": specification.get("normalize"),
                "window_radius": specification.get("window_radius"),
            }
            for specification in specs
        ]
    )

    pair_rows: list[dict[str, Any]] = []
    for specification_index, specification in enumerate(specs):
        for pair_index, (left, right) in enumerate(
            zip(upper[0], upper[1], strict=True)
        ):
            pair_rows.append(
                {
                    "specification": specification["name"],
                    "method": specification["method"],
                    "curve_id_a": trajectories.curve_ids[left],
                    "curve_id_b": trajectories.curve_ids[right],
                    "distance": float(
                        condensed[specification_index, pair_index]
                    ),
                    "distance_rank": float(
                        ranks[specification_index, pair_index]
                    ),
                }
            )

    return TrajectoryDistanceSensitivityResult(
        specification_names=tuple(
            specification["name"] for specification in specs
        ),
        distance_matrices=matrices,
        specification_table=specification_table,
        pairwise_distance_table=pd.DataFrame(pair_rows),
        comparison_table=pd.DataFrame(comparison_rows),
        neighbor_overlap_table=pd.DataFrame(neighbor_rows),
        neighbor_orders=neighbor_orders,
        neighbor_cutoff_ties=cutoff_ties,
        curve_ids=trajectories.curve_ids,
        dimensions=dimension_names,
        dimension_weights=weights,
        neighbor_k=neighbor_k,
        provenance={
            **dict(trajectories.provenance),
            "trajectory_distance_sensitivity": {
                "operation": "trajectory_distance_sensitivity",
                "specifications": [
                    dict(specification) for specification in specs
                ],
                "dimensions": list(dimension_names),
                "dimension_weights": weights.tolist(),
                "n_curves": n_curves,
                "n_curve_pairs": int(condensed.shape[1]),
                "neighbor_k": neighbor_k,
                "distance_matrix_standardization": False,
                "distance_matrix_rescaling": False,
                "consensus_distance_constructed": False,
                "preferred_metric_selected": False,
                "correlation_p_values_computed": False,
                "pairwise_distances_treated_as_independent": False,
                "rank_tie_method": "average",
                "neighbor_tie_break": (
                    "stable_original_curve_order_with_cutoff_tie_flag"
                ),
                "interpretation_boundary": (
                    "descriptive sensitivity of pairwise ordering and local "
                    "neighbor structure to the declared trajectory-distance "
                    "contract; not a test that one metric is correct"
                ),
            },
        },
    )


def trajectory_distance_comparison_frame(
    result: TrajectoryDistanceSensitivityResult,
) -> pd.DataFrame:
    """Return one row per pair of distance specifications."""

    if not isinstance(result, TrajectoryDistanceSensitivityResult):
        raise TypeError(
            "result must be a TrajectoryDistanceSensitivityResult"
        )
    return result.comparison_table.copy()


def trajectory_distance_neighbor_frame(
    result: TrajectoryDistanceSensitivityResult,
) -> pd.DataFrame:
    """Return per-curve local-neighborhood agreement across specifications."""

    if not isinstance(result, TrajectoryDistanceSensitivityResult):
        raise TypeError(
            "result must be a TrajectoryDistanceSensitivityResult"
        )
    return result.neighbor_overlap_table.copy()
