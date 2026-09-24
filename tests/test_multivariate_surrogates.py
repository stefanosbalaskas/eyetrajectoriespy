import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from eyetrajectoriespy import (
    MultivariateIAAFTResult,
    MultivariateSurrogateNonlinearityResult,
    TrajectorySet,
    generate_multivariate_iaaft_surrogates,
    multivariate_iaaft_diagnostics_frame,
    multivariate_iaaft_reporting_text,
    multivariate_surrogate_nonlinearity_reporting_text,
    multivariate_surrogate_nonlinearity_test,
    plot_multivariate_iaaft_diagnostics,
    plot_multivariate_surrogate_nonlinearity,
)


def _coupled_planar(n=256, seed=12):
    rng = np.random.default_rng(seed)
    x = np.empty(n, dtype=float)
    y = np.empty(n, dtype=float)
    x[0] = rng.normal()
    y[0] = rng.normal()
    for index in range(1, n):
        x[index] = 0.82 * x[index - 1] + rng.normal(0.0, 0.55)
        y[index] = (
            0.55 * y[index - 1]
            + 0.65 * x[index - 1]
            + rng.normal(0.0, 0.35)
        )
    values = np.column_stack([x, y])[None, :, :]
    return TrajectorySet(
        time=np.arange(n, dtype=float) * 0.01,
        values=values,
        curve_ids=("coupled",),
        dimension_names=("x", "y"),
        coordinate_system="unknown",
        time_unit="s",
    )


def _planar_logistic(n=360):
    x = np.empty(n, dtype=float)
    x[0] = 0.217
    for index in range(n - 1):
        x[index + 1] = 4.0 * x[index] * (1.0 - x[index])
    y = np.roll(x, 1)
    y[0] = x[0]
    y = 0.7 * y + 0.3 * x**2
    return TrajectorySet(
        time=np.arange(n, dtype=float) * 0.01,
        values=np.column_stack([x, y])[None, :, :],
        curve_ids=("planar_logistic",),
        dimension_names=("x", "y"),
        coordinate_system="unknown",
        time_unit="s",
    )


def test_multivariate_iaaft_preserves_marginals_and_is_seeded():
    data = _coupled_planar()
    first = generate_multivariate_iaaft_surrogates(
        data,
        curve=0,
        dimensions=("x", "y"),
        reference_dimension="x",
        n_surrogates=3,
        max_iterations=500,
        tolerance=1e-6,
        random_state=42,
    )
    second = generate_multivariate_iaaft_surrogates(
        data,
        curve=0,
        dimensions=("x", "y"),
        reference_dimension="x",
        n_surrogates=3,
        max_iterations=500,
        tolerance=1e-6,
        random_state=42,
    )

    assert isinstance(first, MultivariateIAAFTResult)
    assert first.surrogates.shape == (3, data.n_time, 2)
    assert first.spectral_errors.shape == (3, 2)
    assert first.cross_spectral_errors.shape == (3, 1)
    assert first.dimension_pairs == (("x", "y"),)
    assert first.reference_dimension == "x"
    assert np.all(np.isfinite(first.spectral_errors))
    assert np.all(np.isfinite(first.cross_spectral_errors))
    assert np.all(first.convergence_iterations >= 1)
    np.testing.assert_allclose(first.surrogates, second.surrogates)

    source = first.source_values
    for surrogate in first.surrogates:
        for dimension_index in range(2):
            np.testing.assert_allclose(
                np.sort(surrogate[:, dimension_index]),
                np.sort(source[:, dimension_index]),
                atol=0.0,
                rtol=0.0,
            )

    assert np.max(first.spectral_errors) < 0.20
    assert np.max(first.cross_spectral_errors) < 0.35
    assert (
        first.provenance["reference_dimension_selected_automatically"]
        is False
    )
    assert (
        first.provenance["cross_spectral_preservation"]
        == "approximate_after_final_rank_remapping_with_error_retained"
    )


def test_multivariate_iaaft_diagnostics_and_reporting():
    result = generate_multivariate_iaaft_surrogates(
        _coupled_planar(n=180),
        curve="coupled",
        dimensions=("x", "y"),
        reference_dimension="y",
        n_surrogates=2,
        max_iterations=400,
        tolerance=1e-6,
        random_state=9,
    )
    frame = multivariate_iaaft_diagnostics_frame(result)
    assert list(frame["surrogate"]) == [0, 1]
    assert np.all(frame["max_spectral_error"] >= 0)
    assert np.all(frame["max_cross_spectral_error"] >= 0)

    text = multivariate_iaaft_reporting_text(result)
    assert "multivariate IAAFT" in text
    assert "cross-spectrum mismatch" in text
    assert "phase-reference dimension" in text

    ax = plot_multivariate_iaaft_diagnostics(result)
    assert len(ax.lines) == 2
    assert "reference" in ax.get_title()
    plt.close(ax.figure)


def test_multivariate_surrogate_nonlinearity_test_is_seeded_plus_one():
    data = _planar_logistic()
    first = multivariate_surrogate_nonlinearity_test(
        data,
        curve=0,
        dimensions=("x", "y"),
        reference_dimension="x",
        statistic="largest_lyapunov",
        embedding_dimension=2,
        delay=1,
        theiler_window=8,
        max_horizon=6,
        fit_start=1,
        fit_end=4,
        n_surrogates=2,
        max_iterations=400,
        tolerance=1e-5,
        random_state=123,
    )
    second = multivariate_surrogate_nonlinearity_test(
        data,
        curve=0,
        dimensions=("x", "y"),
        reference_dimension="x",
        statistic="largest_lyapunov",
        embedding_dimension=2,
        delay=1,
        theiler_window=8,
        max_horizon=6,
        fit_start=1,
        fit_end=4,
        n_surrogates=2,
        max_iterations=400,
        tolerance=1e-5,
        random_state=123,
    )

    assert isinstance(first, MultivariateSurrogateNonlinearityResult)
    assert first.n_surrogates == 2
    assert first.p_value in {1.0 / 3.0, 2.0 / 3.0, 1.0}
    np.testing.assert_allclose(
        first.surrogate_statistics,
        second.surrogate_statistics,
    )
    assert first.p_value == second.p_value

    text = multivariate_surrogate_nonlinearity_reporting_text(first)
    assert "cross-spectrum-aware MIAAFT" in text
    assert "plus-one Monte Carlo" in text

    ax = plot_multivariate_surrogate_nonlinearity(
        first,
        bins=3,
    )
    assert len(ax.lines) == 1
    plt.close(ax.figure)


def test_multivariate_surrogate_contracts_fail_closed():
    data = _coupled_planar()

    with pytest.raises(ValueError, match="at least two dimensions"):
        generate_multivariate_iaaft_surrogates(
            data,
            curve=0,
            dimensions=("x",),
            reference_dimension="x",
            n_surrogates=1,
        )

    with pytest.raises(ValueError, match="reference_dimension"):
        generate_multivariate_iaaft_surrogates(
            data,
            curve=0,
            dimensions=("x", "y"),
            reference_dimension="z",
            n_surrogates=1,
        )

    with pytest.raises(ValueError, match="positive integer"):
        generate_multivariate_iaaft_surrogates(
            data,
            curve=0,
            dimensions=("x", "y"),
            reference_dimension="x",
            n_surrogates=0,
        )

    constant = TrajectorySet(
        time=data.time,
        values=np.column_stack(
            [data.values[0, :, 0], np.ones(data.n_time)]
        )[None, :, :],
        curve_ids=("constant",),
        dimension_names=("x", "y"),
        coordinate_system="unknown",
        time_unit="s",
    )
    with pytest.raises(ValueError, match="constant dimensions"):
        generate_multivariate_iaaft_surrogates(
            constant,
            curve=0,
            dimensions=("x", "y"),
            reference_dimension="x",
            n_surrogates=1,
        )

    with pytest.raises(ValueError, match="largest_lyapunov"):
        multivariate_surrogate_nonlinearity_test(
            data,
            curve=0,
            dimensions=("x", "y"),
            reference_dimension="x",
            statistic="entropy",
            embedding_dimension=2,
            delay=1,
            theiler_window=4,
            max_horizon=5,
            fit_start=1,
            fit_end=3,
            n_surrogates=1,
        )


def test_multivariate_surrogate_helpers_validate_types():
    with pytest.raises(TypeError, match="MultivariateIAAFTResult"):
        multivariate_iaaft_diagnostics_frame(object())
    with pytest.raises(TypeError, match="MultivariateIAAFTResult"):
        multivariate_iaaft_reporting_text(object())
    with pytest.raises(TypeError, match="MultivariateIAAFTResult"):
        plot_multivariate_iaaft_diagnostics(object())
    with pytest.raises(TypeError, match="MultivariateSurrogateNonlinearityResult"):
        multivariate_surrogate_nonlinearity_reporting_text(object())
    with pytest.raises(TypeError, match="MultivariateSurrogateNonlinearityResult"):
        plot_multivariate_surrogate_nonlinearity(
            object(),
            bins=3,
        )
