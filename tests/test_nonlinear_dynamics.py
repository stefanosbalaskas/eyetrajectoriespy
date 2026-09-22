import numpy as np
import pytest

from eyetrajectoriespy import (
    TrajectorySet,
    delay_embed_trajectory,
    estimate_largest_lyapunov_rosenstein,
    local_divergence_curve,
    surrogate_nonlinearity_test,
)


def _logistic_set(n=600):
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
        coordinate_system="arbitrary",
    )


def test_local_divergence_curve_retains_counts_and_neighbors():
    data = _logistic_set()
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    result = local_divergence_curve(
        embedding,
        curve=0,
        theiler_window=10,
        max_horizon=8,
    )

    assert result.horizons.tolist() == list(range(9))
    assert result.pair_counts.shape == (9,)
    assert result.zero_distance_counts.shape == (9,)
    assert result.nearest_neighbor_indices.shape == (embedding.n_states,)
    assert np.isfinite(result.mean_log_divergence[:6]).all()
    assert result.provenance["automatic_fit_interval_selection"] is False


def test_rosenstein_lle_requires_declared_fit_interval_and_is_finite():
    data = _logistic_set()
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    divergence = local_divergence_curve(
        embedding,
        curve=0,
        theiler_window=10,
        max_horizon=8,
    )
    result = estimate_largest_lyapunov_rosenstein(
        divergence,
        fit_start=1,
        fit_end=5,
    )

    assert np.isfinite(result.exponent)
    assert result.exponent_unit == "1/s"
    assert np.isfinite(result.r_squared)
    assert result.n_fit_points == 5
    assert result.provenance["fit_interval_selected_automatically"] is False


def test_rosenstein_rejects_too_short_fit_interval():
    data = _logistic_set()
    embedding = delay_embed_trajectory(
        data,
        embedding_dimension=2,
        delay=1,
        dimensions=("x",),
    )
    divergence = local_divergence_curve(
        embedding,
        curve=0,
        theiler_window=10,
        max_horizon=8,
    )
    with pytest.raises(ValueError, match="fewer than three"):
        estimate_largest_lyapunov_rosenstein(
            divergence,
            fit_start=1,
            fit_end=2,
        )


def test_iaaft_surrogate_test_is_seeded_plus_one_and_retains_all_surrogates():
    data = _logistic_set(450)
    result = surrogate_nonlinearity_test(
        data,
        curve=0,
        dimension="x",
        statistic="largest_lyapunov",
        embedding_dimension=2,
        delay=1,
        theiler_window=8,
        max_horizon=7,
        fit_start=1,
        fit_end=4,
        n_surrogates=3,
        max_iterations=30,
        tolerance=1e-6,
        random_state=123,
    )

    assert result.surrogate_statistics.shape == (3,)
    assert result.convergence_iterations.shape == (3,)
    assert result.p_value in {0.25, 0.5, 0.75, 1.0}
    assert result.provenance["p_value_correction"] == "plus_one"

    again = surrogate_nonlinearity_test(
        data,
        curve=0,
        dimension="x",
        statistic="largest_lyapunov",
        embedding_dimension=2,
        delay=1,
        theiler_window=8,
        max_horizon=7,
        fit_start=1,
        fit_end=4,
        n_surrogates=3,
        max_iterations=30,
        tolerance=1e-6,
        random_state=123,
    )
    np.testing.assert_allclose(
        result.surrogate_statistics,
        again.surrogate_statistics,
    )
    assert result.p_value == again.p_value


def test_surrogate_test_rejects_unsupported_statistic():
    data = _logistic_set(100)
    with pytest.raises(ValueError, match="largest_lyapunov"):
        surrogate_nonlinearity_test(
            data,
            curve=0,
            dimension="x",
            statistic="entropy",
            embedding_dimension=2,
            delay=1,
            theiler_window=2,
            max_horizon=5,
            fit_start=1,
            fit_end=3,
            n_surrogates=2,
        )
