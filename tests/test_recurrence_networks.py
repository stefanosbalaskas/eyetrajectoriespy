import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy.sparse import csr_matrix

from eyetrajectoriespy import (
    RecurrenceNetworkResult,
    RecurrenceResult,
    plot_recurrence_network_degree,
    recurrence_network,
    recurrence_network_node_frame,
    recurrence_network_reporting_text,
    recurrence_network_summary_frame,
)


def _recurrence(matrix, *, theiler=0, kind="auto"):
    matrix = csr_matrix(np.asarray(matrix, dtype=bool))
    n = matrix.shape[0]
    eligible = max(1, (n - theiler - 1) * (n - theiler) // 2)
    return RecurrenceResult(
        matrix=matrix,
        time_a=np.arange(n, dtype=float) * 0.01,
        time_b=np.arange(n, dtype=float) * 0.01,
        source_curve_ids=("curve",),
        radius=0.5,
        target_recurrence_rate=None,
        achieved_recurrence_rate=(
            int(np.triu(matrix.toarray(), k=1).sum()) / eligible
            if kind == "auto"
            else matrix.nnz / max(1, n * n)
        ),
        metric="euclidean",
        theiler_window_samples=theiler,
        kind=kind,
        state_dimension=2,
        provenance={
            "radius_policy": "fixed",
            "recurrence_rate_denominator": (
                "eligible_off_diagonal_pairs_outside_theiler_window"
                if kind == "auto"
                else "all_cross_state_pairs"
            ),
        },
        time_unit="s",
    )


def _triangle_tail_recurrence():
    # Triangle 0-1-2 plus one tail edge 2-3; node 4 is isolated.
    matrix = np.array(
        [
            [0, 1, 1, 0, 0],
            [1, 0, 1, 0, 0],
            [1, 1, 0, 1, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=bool,
    )
    return _recurrence(matrix)


def test_recurrence_network_known_graph_metrics():
    source = _triangle_tail_recurrence()
    result = recurrence_network(source)

    assert isinstance(result, RecurrenceNetworkResult)
    assert result.n_nodes == 5
    assert result.edge_count == 4
    assert result.graph_density == pytest.approx(0.4)
    np.testing.assert_array_equal(result.degree, [2, 2, 3, 1, 0])
    np.testing.assert_allclose(
        result.normalized_degree,
        [0.5, 0.5, 0.75, 0.25, 0.0],
    )
    np.testing.assert_allclose(
        result.local_clustering,
        [1.0, 1.0, 1.0 / 3.0, 0.0, 0.0],
    )
    assert result.mean_local_clustering == pytest.approx(7.0 / 15.0)
    assert result.transitivity == pytest.approx(3.0 / 5.0)
    assert result.n_connected_components == 2
    np.testing.assert_array_equal(np.sort(result.component_sizes), [1, 4])
    assert result.largest_component_fraction == pytest.approx(0.8)
    assert result.isolated_node_fraction == pytest.approx(0.2)

    contract = result.provenance
    assert contract["dense_adjacency_materialized"] is False
    assert contract["automatic_threshold_selection"] is False
    assert contract["automatic_community_detection"] is False
    assert contract["automatic_dimension_interpretation"] is False
    assert contract["triangle_count"] == 1
    assert (
        contract["graph_density_denominator"]
        == "all_unordered_node_pairs"
    )


def test_recurrence_network_frames_plot_and_reporting():
    result = recurrence_network(_triangle_tail_recurrence())

    node_frame = recurrence_network_node_frame(result)
    assert list(node_frame.columns) == [
        "node_index",
        "time",
        "degree",
        "normalized_degree",
        "local_clustering",
        "component",
        "component_size",
    ]
    assert list(node_frame["degree"]) == [2, 2, 3, 1, 0]

    summary = recurrence_network_summary_frame(result)
    assert summary.loc[0, "edge_count"] == 4
    assert summary.loc[0, "graph_density"] == pytest.approx(0.4)
    assert summary.loc[0, "transitivity"] == pytest.approx(0.6)

    ax = plot_recurrence_network_degree(result)
    assert "Recurrence-network degree" in ax.get_title()
    assert "Normalized" in ax.get_ylabel()
    plt.close(ax.figure)

    ax = plot_recurrence_network_degree(result, normalized=False)
    assert ax.get_ylabel() == "Degree"
    plt.close(ax.figure)

    text = recurrence_network_reporting_text(result)
    assert "undirected recurrence network" in text
    assert "graph density" in text
    assert "No threshold tuning" in text


def test_recurrence_network_transitivity_is_explicitly_undefined_without_triples():
    matrix = np.array(
        [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0],
        ],
        dtype=bool,
    )
    result = recurrence_network(_recurrence(matrix))
    assert np.isnan(result.transitivity)
    np.testing.assert_array_equal(result.local_clustering, [0.0, 0.0, 0.0])
    text = recurrence_network_reporting_text(result)
    assert "undefined because the network contained no connected triples" in text


def test_recurrence_network_rejects_invalid_source_contracts():
    source = _triangle_tail_recurrence()

    cross = RecurrenceResult(
        matrix=source.matrix,
        time_a=source.time_a,
        time_b=source.time_b,
        source_curve_ids=("a", "b"),
        radius=0.5,
        target_recurrence_rate=None,
        achieved_recurrence_rate=0.2,
        metric="euclidean",
        theiler_window_samples=0,
        kind="cross",
        state_dimension=2,
        provenance={"recurrence_rate_denominator": "all_cross_state_pairs"},
        time_unit="s",
    )
    with pytest.raises(ValueError, match="auto-recurrence"):
        recurrence_network(cross)

    asymmetric = source.matrix.copy().tolil()
    asymmetric[0, 1] = False
    asymmetric = asymmetric.tocsr()
    asymmetric.eliminate_zeros()
    with pytest.raises(ValueError, match="symmetric"):
        recurrence_network(
            RecurrenceResult(
                **{
                    **source.__dict__,
                    "matrix": asymmetric,
                }
            )
        )

    diagonal = source.matrix.copy().tolil()
    diagonal[0, 0] = True
    with pytest.raises(ValueError, match="main diagonal"):
        recurrence_network(
            RecurrenceResult(
                **{
                    **source.__dict__,
                    "matrix": diagonal.tocsr(),
                }
            )
        )

    theiler_matrix = np.array(
        [
            [0, 0, 1],
            [0, 0, 0],
            [1, 0, 0],
        ],
        dtype=bool,
    )
    theiler_source = _recurrence(theiler_matrix, theiler=2)
    with pytest.raises(ValueError, match="Theiler exclusion"):
        recurrence_network(theiler_source)


def test_recurrence_network_helper_type_validation():
    with pytest.raises(TypeError, match="RecurrenceResult"):
        recurrence_network(object())

    with pytest.raises(TypeError, match="RecurrenceNetworkResult"):
        recurrence_network_node_frame(object())

    with pytest.raises(TypeError, match="RecurrenceNetworkResult"):
        recurrence_network_summary_frame(object())

    with pytest.raises(TypeError, match="RecurrenceNetworkResult"):
        plot_recurrence_network_degree(object())

    with pytest.raises(TypeError, match="RecurrenceNetworkResult"):
        recurrence_network_reporting_text(object())

    result = recurrence_network(_triangle_tail_recurrence())
    with pytest.raises(TypeError, match="normalized must be boolean"):
        plot_recurrence_network_degree(result, normalized="yes")
