"""Sparse recurrence-network summaries derived from auto-recurrence plots."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, triu
from scipy.sparse.csgraph import connected_components

from .nonlinear_types import RecurrenceNetworkResult, RecurrenceResult


def _validate_recurrence_network_source(
    recurrence: RecurrenceResult,
) -> csr_matrix:
    if not isinstance(recurrence, RecurrenceResult):
        raise TypeError("recurrence must be a RecurrenceResult")
    if recurrence.kind != "auto":
        raise ValueError(
            "recurrence networks require an auto-recurrence result"
        )

    adjacency = recurrence.matrix.astype(bool).tocsr().copy()
    if adjacency.shape[0] != adjacency.shape[1]:
        raise ValueError(
            "recurrence network adjacency must be square"
        )
    if adjacency.shape[0] < 2:
        raise ValueError(
            "recurrence network requires at least two state nodes"
        )
    n_nodes = adjacency.shape[0]
    time_a = np.asarray(recurrence.time_a, dtype=float)
    time_b = np.asarray(recurrence.time_b, dtype=float)
    if time_a.shape != (n_nodes,) or time_b.shape != (n_nodes,):
        raise ValueError(
            "recurrence network time grids must match adjacency dimensions"
        )
    if not np.array_equal(time_a, time_b):
        raise ValueError(
            "auto-recurrence network requires identical time grids on both axes"
        )
    if recurrence.theiler_window_samples < 0:
        raise ValueError("theiler_window_samples must be non-negative")
    if (adjacency != adjacency.T).nnz:
        raise ValueError(
            "recurrence network source must be symmetric"
        )
    if np.any(adjacency.diagonal()):
        raise ValueError(
            "recurrence network source must exclude the main diagonal"
        )

    coo = adjacency.tocoo()
    if np.any(
        np.abs(coo.row - coo.col)
        <= int(recurrence.theiler_window_samples)
    ):
        raise ValueError(
            "recurrence network source contains edges inside its declared "
            "Theiler exclusion"
        )
    adjacency.eliminate_zeros()
    adjacency.sort_indices()
    return adjacency


def _triangle_counts(
    adjacency: csr_matrix,
) -> tuple[np.ndarray, int]:
    """Count graph triangles without materializing a dense square matrix."""

    n_nodes = adjacency.shape[0]
    counts = np.zeros(n_nodes, dtype=np.int64)
    n_triangles = 0

    for left in range(n_nodes):
        left_neighbors = adjacency.indices[
            adjacency.indptr[left] : adjacency.indptr[left + 1]
        ]
        right_candidates = left_neighbors[left_neighbors > left]
        for right_value in right_candidates:
            right = int(right_value)
            right_neighbors = adjacency.indices[
                adjacency.indptr[right] : adjacency.indptr[right + 1]
            ]

            left_tail = left_neighbors[left_neighbors > right]
            right_tail = right_neighbors[right_neighbors > right]
            if left_tail.size == 0 or right_tail.size == 0:
                continue

            common = np.intersect1d(
                left_tail,
                right_tail,
                assume_unique=True,
            )
            if common.size == 0:
                continue

            count = int(common.size)
            counts[left] += count
            counts[right] += count
            counts[common] += 1
            n_triangles += count

    return counts, n_triangles


def recurrence_network(
    recurrence: RecurrenceResult,
) -> RecurrenceNetworkResult:
    """Convert one auto-recurrence matrix into an undirected simple network.

    Every recurrence state/time index becomes one network node. Every retained
    off-diagonal recurrence pair becomes one undirected edge.

    The network inherits the recurrence threshold, state representation,
    metric, Theiler exclusion, and any target-recurrence-rate constraint from
    the source recurrence object. No edge weighting, temporal edge restoration,
    graph threshold tuning, community optimization, or dimensionality
    interpretation is introduced automatically.
    """

    adjacency = _validate_recurrence_network_source(recurrence)
    n_nodes = adjacency.shape[0]
    upper = triu(adjacency, k=1).tocsr()
    edge_count = int(upper.nnz)
    total_pairs = n_nodes * (n_nodes - 1) // 2
    graph_density = float(edge_count / total_pairs)

    degree = np.asarray(
        adjacency.sum(axis=1)
    ).ravel().astype(np.int64)
    normalized_degree = degree.astype(float) / float(n_nodes - 1)

    triangle_count_by_node, n_triangles = _triangle_counts(adjacency)
    possible_neighbor_pairs = (
        degree.astype(np.int64) * (degree.astype(np.int64) - 1) // 2
    )
    local_clustering = np.zeros(n_nodes, dtype=float)
    eligible_local = possible_neighbor_pairs > 0
    local_clustering[eligible_local] = (
        triangle_count_by_node[eligible_local].astype(float)
        / possible_neighbor_pairs[eligible_local].astype(float)
    )
    mean_local_clustering = float(np.mean(local_clustering))

    connected_triples = int(np.sum(possible_neighbor_pairs))
    transitivity = (
        float(3 * n_triangles / connected_triples)
        if connected_triples > 0
        else float("nan")
    )

    n_components, labels = connected_components(
        adjacency,
        directed=False,
        return_labels=True,
    )
    component_sizes = np.bincount(
        labels,
        minlength=n_components,
    ).astype(np.int64)
    largest_component_fraction = float(
        component_sizes.max() / n_nodes
    )
    isolated_node_fraction = float(np.mean(degree == 0))

    return RecurrenceNetworkResult(
        adjacency=adjacency,
        degree=degree,
        normalized_degree=normalized_degree,
        local_clustering=local_clustering,
        component_labels=labels.astype(np.int64),
        component_sizes=component_sizes,
        edge_count=edge_count,
        graph_density=graph_density,
        transitivity=transitivity,
        mean_local_clustering=mean_local_clustering,
        n_connected_components=int(n_components),
        largest_component_fraction=largest_component_fraction,
        isolated_node_fraction=isolated_node_fraction,
        source_recurrence=recurrence,
        provenance={
            "operation": "recurrence_network",
            "network_type": "undirected_unweighted_simple_graph",
            "node_definition": "recurrence_state_time_index",
            "edge_definition": "retained_off_diagonal_recurrence_pair",
            "source_recurrence_provenance": dict(recurrence.provenance),
            "source_metric": recurrence.metric,
            "source_radius": float(recurrence.radius),
            "source_target_recurrence_rate": (
                recurrence.target_recurrence_rate
            ),
            "source_achieved_recurrence_rate": float(
                recurrence.achieved_recurrence_rate
            ),
            "source_theiler_window_samples": int(
                recurrence.theiler_window_samples
            ),
            "source_state_dimension": int(recurrence.state_dimension),
            "source_time_unit": recurrence.time_unit,
            "graph_density_denominator": "all_unordered_node_pairs",
            "source_recurrence_rate_denominator": (
                recurrence.provenance.get(
                    "recurrence_rate_denominator"
                )
            ),
            "local_clustering_degree_lt_2": 0.0,
            "transitivity_undefined_when_no_connected_triples": True,
            "triangle_count": int(n_triangles),
            "dense_adjacency_materialized": False,
            "automatic_threshold_selection": False,
            "automatic_community_detection": False,
            "automatic_dimension_interpretation": False,
            "interpretation_boundary": (
                "network topology describes the geometry induced by the "
                "declared recurrence relation; it remains conditional on the "
                "state representation, metric, threshold policy, Theiler "
                "window, and sampling design"
            ),
        },
    )


def recurrence_network_node_frame(
    result: RecurrenceNetworkResult,
) -> pd.DataFrame:
    """Return one row per recurrence-network node/state index."""

    if not isinstance(result, RecurrenceNetworkResult):
        raise TypeError("result must be a RecurrenceNetworkResult")

    time = np.asarray(
        result.source_recurrence.time_a,
        dtype=float,
    )
    return pd.DataFrame(
        {
            "node_index": np.arange(result.n_nodes, dtype=int),
            "time": time,
            "degree": result.degree,
            "normalized_degree": result.normalized_degree,
            "local_clustering": result.local_clustering,
            "component": result.component_labels,
            "component_size": result.component_sizes[
                result.component_labels
            ],
        }
    )


def recurrence_network_summary_frame(
    result: RecurrenceNetworkResult,
) -> pd.DataFrame:
    """Return a one-row table of global recurrence-network summaries."""

    if not isinstance(result, RecurrenceNetworkResult):
        raise TypeError("result must be a RecurrenceNetworkResult")

    return pd.DataFrame(
        [
            {
                "n_nodes": result.n_nodes,
                "edge_count": result.edge_count,
                "graph_density": result.graph_density,
                "source_achieved_recurrence_rate": (
                    result.source_recurrence.achieved_recurrence_rate
                ),
                "mean_degree": float(np.mean(result.degree)),
                "mean_local_clustering": (
                    result.mean_local_clustering
                ),
                "transitivity": result.transitivity,
                "n_connected_components": (
                    result.n_connected_components
                ),
                "largest_component_fraction": (
                    result.largest_component_fraction
                ),
                "isolated_node_fraction": (
                    result.isolated_node_fraction
                ),
            }
        ]
    )
