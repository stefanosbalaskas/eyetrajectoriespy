import numpy as np
import pytest

from eyetrajectoriespy import (
    DelayEmbeddingResult,
    TrajectorySet,
    delay_embed_trajectory,
    estimate_largest_lyapunov_kantz,
    estimate_largest_lyapunov_rosenstein,
    kantz_divergence_curve,
    local_divergence_curve,
)


def _simple_embedding():
    states = np.array([0.0, 1.0, 2.0, 3.0], dtype=float)[None, :, None]
    return DelayEmbeddingResult(
        values=states,
        time=np.arange(4, dtype=float),
        curve_ids=("simple",),
        source_dimension_names=("x",),
        state_names=("x[t]",),
        embedding_dimension=1,
        delay_samples=1,
        delay_time=1.0,
        time_unit="samples",
        coordinate_system="normalized",
        provenance={"fixture": "hand-countable line"},
    )


def _logistic_set(n=700):
    x = np.empty(n, dtype=float)
    x[0] = 0.217
    for i in range(n - 1):
        x[i + 1] = 4.0 * x[i] * (1.0 - x[i])
    return TrajectorySet(
        time=np.arange(n, dtype=float) * 0.01,
        values=x[None, :, None],
        curve_ids=("logistic",),
        dimension_names=("x",),
        time_unit="s",
        coordinate_system="normalized",
    )


def test_kantz_hand_counted_neighborhood_average_and_counts():
    result = kantz_divergence_curve(
        _simple_embedding(),
        curve=0,
        radius=1.1,
        theiler_window=0,
        max_horizon=1,
        min_neighbors=1,
    )

    np.testing.assert_allclose(result.mean_log_divergence, [0.0, 0.0])
    assert result.reference_counts.tolist() == [4, 3]
    assert result.pair_counts.tolist() == [6, 4]
    assert result.zero_mean_neighborhood_counts.tolist() == [0, 0]
    assert result.initial_neighbor_counts.tolist() == [1, 2, 2, 1]
    assert result.radius == pytest.approx(1.1)
    assert result.provenance["radius_selected_automatically"] is False
    assert result.provenance["neighborhood_expansion_policy"] == (
        "none_fail_or_skip_reference"
    )


def test_kantz_min_neighbors_filters_reference_states_without_expansion():
    result = kantz_divergence_curve(
        _simple_embedding(),
        curve="simple",
        radius=1.1,
        theiler_window=0,
        max_horizon=1,
        min_neighbors=2,
    )
    assert result.reference_counts.tolist() == [2, 1]
    assert result.pair_counts.tolist() == [4, 2]

    with pytest.raises(ValueError, match="no reference state"):
        kantz_divergence_curve(
            _simple_embedding(),
            curve=0,
            radius=0.1,
            theiler_window=0,
            max_horizon=1,
            min_neighbors=1,
        )


def test_kantz_logistic_lle_is_finite_positive_and_explicit():
    data = _logistic_set()
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    divergence = kantz_divergence_curve(
        embedding,
        curve=0,
        radius=0.08,
        theiler_window=10,
        max_horizon=8,
        min_neighbors=2,
    )
    result = estimate_largest_lyapunov_kantz(
        divergence,
        fit_start=1,
        fit_end=5,
    )

    assert np.isfinite(result.exponent)
    assert result.exponent > 0
    assert result.exponent_unit == "1/s"
    assert result.n_fit_points == 5
    assert result.provenance["fit_interval_selected_automatically"] is False
    assert result.divergence.provenance["estimator_family"].startswith("Kantz")


def test_kantz_input_contracts_fail_closed():
    embedding = _simple_embedding()

    with pytest.raises(TypeError, match="numeric"):
        kantz_divergence_curve(
            embedding,
            curve=0,
            radius=True,
            theiler_window=0,
            max_horizon=1,
        )
    with pytest.raises(ValueError, match="positive finite"):
        kantz_divergence_curve(
            embedding,
            curve=0,
            radius=0.0,
            theiler_window=0,
            max_horizon=1,
        )
    with pytest.raises(TypeError, match="integer"):
        kantz_divergence_curve(
            embedding,
            curve=0,
            radius=1.1,
            theiler_window=0,
            max_horizon=1,
            min_neighbors=True,
        )
    with pytest.raises(ValueError, match="at least 1"):
        kantz_divergence_curve(
            embedding,
            curve=0,
            radius=1.1,
            theiler_window=0,
            max_horizon=1,
            min_neighbors=0,
        )


def test_named_lle_fitters_reject_wrong_divergence_family():
    data = _logistic_set(400)
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    rosenstein = local_divergence_curve(
        embedding,
        curve=0,
        theiler_window=8,
        max_horizon=6,
    )
    kantz = kantz_divergence_curve(
        embedding,
        curve=0,
        radius=0.08,
        theiler_window=8,
        max_horizon=6,
        min_neighbors=2,
    )

    with pytest.raises(TypeError, match="KantzDivergenceResult"):
        estimate_largest_lyapunov_kantz(
            rosenstein,  # type: ignore[arg-type]
            fit_start=1,
            fit_end=4,
        )
    with pytest.raises(TypeError, match="LocalDivergenceResult"):
        estimate_largest_lyapunov_rosenstein(
            kantz,  # type: ignore[arg-type]
            fit_start=1,
            fit_end=4,
        )
