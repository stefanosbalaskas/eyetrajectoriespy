"""Local divergence, Rosenstein LLE, and surrogate-data diagnostics."""

from __future__ import annotations

import numpy as np
from scipy import stats

from .embedding import (
    _TIME_TO_SECONDS,
    _curve_index,
    _nearest_temporally_separated,
    _require_finite,
    _resolve_samples,
    delay_embed_trajectory,
)
from .nonlinear_types import (
    DelayEmbeddingResult,
    LargestLyapunovResult,
    LocalDivergenceResult,
    SurrogateNonlinearityResult,
)
from .types import TrajectorySet


def _embedded_curve_index(embedding: DelayEmbeddingResult, curve: int | str) -> int:
    if isinstance(curve, str):
        try:
            return embedding.curve_ids.index(curve)
        except ValueError as exc:
            raise KeyError(f"Unknown curve_id {curve!r}") from exc
    if not isinstance(curve, (int, np.integer)):
        raise TypeError("curve must be an integer index or curve_id string")
    index = int(curve)
    if index < 0 or index >= embedding.n_curves:
        raise IndexError("curve index is out of range")
    return index


def local_divergence_curve(
    embedding: DelayEmbeddingResult,
    *,
    curve: int | str,
    theiler_window: float | int,
    max_horizon: float | int,
    theiler_window_units: str = "samples",
    max_horizon_units: str = "samples",
) -> LocalDivergenceResult:
    """Compute a Rosenstein-style mean log-divergence curve.

    Zero distances encountered after forward evolution are excluded from the
    logarithm but counted explicitly in zero_distance_counts.
    """

    index = _embedded_curve_index(embedding, curve)
    states = np.asarray(embedding.values[index], dtype=float)
    _require_finite(states, context="local divergence")
    theiler = _resolve_samples(
        embedding.time,
        theiler_window,
        units=theiler_window_units,
        time_unit=embedding.time_unit,
        name="theiler_window",
        allow_zero=True,
    )
    max_horizon_samples = _resolve_samples(
        embedding.time,
        max_horizon,
        units=max_horizon_units,
        time_unit=embedding.time_unit,
        name="max_horizon",
        allow_zero=True,
    )
    if max_horizon_samples < 1:
        raise ValueError("max_horizon must be at least one sample")
    if max_horizon_samples >= embedding.n_states:
        raise ValueError("max_horizon must be smaller than the number of reconstructed states")

    neighbor_indices, _ = _nearest_temporally_separated(
        states,
        theiler_window_samples=theiler,
    )
    horizons = np.arange(max_horizon_samples + 1, dtype=int)
    means = np.full(horizons.size, np.nan, dtype=float)
    pair_counts = np.zeros(horizons.size, dtype=int)
    zero_counts = np.zeros(horizons.size, dtype=int)

    for k in horizons:
        valid = (
            (np.arange(states.shape[0]) + k < states.shape[0])
            & (neighbor_indices + k < states.shape[0])
        )
        refs = np.where(valid)[0]
        if refs.size == 0:
            continue
        distances = np.linalg.norm(
            states[refs + k] - states[neighbor_indices[refs] + k],
            axis=1,
        )
        zero = distances <= 0
        zero_counts[k] = int(np.sum(zero))
        positive = distances[~zero]
        pair_counts[k] = int(positive.size)
        if positive.size:
            means[k] = float(np.mean(np.log(positive)))

    step = float(np.median(np.diff(embedding.time)))
    return LocalDivergenceResult(
        horizons=horizons,
        time_lags=horizons.astype(float) * step,
        mean_log_divergence=means,
        pair_counts=pair_counts,
        zero_distance_counts=zero_counts,
        nearest_neighbor_indices=neighbor_indices,
        theiler_window_samples=theiler,
        max_horizon_samples=max_horizon_samples,
        curve_id=embedding.curve_ids[index],
        time_unit=embedding.time_unit,
        provenance={
            "operation": "local_divergence_curve",
            "embedding_provenance": dict(embedding.provenance),
            "estimator_family": "Rosenstein nearest-neighbor divergence",
            "theiler_window_samples": theiler,
            "max_horizon_samples": max_horizon_samples,
            "zero_distance_policy": "excluded_from_log_and_counted_explicitly",
            "automatic_fit_interval_selection": False,
        },
    )


def _fit_interval_samples(
    divergence: LocalDivergenceResult,
    start: float | int,
    end: float | int,
    units: str,
) -> tuple[int, int]:
    pseudo_time = divergence.time_lags
    start_sample = _resolve_samples(
        pseudo_time,
        start,
        units=units,
        time_unit=divergence.time_unit,
        name="fit_start",
        allow_zero=True,
    )
    end_sample = _resolve_samples(
        pseudo_time,
        end,
        units=units,
        time_unit=divergence.time_unit,
        name="fit_end",
        allow_zero=False,
    )
    if end_sample <= start_sample:
        raise ValueError("fit_end must be greater than fit_start")
    if end_sample > divergence.max_horizon_samples:
        raise ValueError("fit_end exceeds the computed divergence horizon")
    return start_sample, end_sample


def estimate_largest_lyapunov_rosenstein(
    divergence: LocalDivergenceResult,
    *,
    fit_start: float | int,
    fit_end: float | int,
    fit_units: str = "samples",
) -> LargestLyapunovResult:
    """Fit the declared linear segment of a Rosenstein divergence curve.

    A positive result is a local-divergence estimate and is not, by itself,
    evidence that behavioral gaze is a deterministic chaotic system.
    """

    start, end = _fit_interval_samples(divergence, fit_start, fit_end, fit_units)
    mask = (
        (divergence.horizons >= start)
        & (divergence.horizons <= end)
        & np.isfinite(divergence.mean_log_divergence)
        & (divergence.pair_counts > 0)
    )
    if int(np.sum(mask)) < 3:
        raise ValueError("the declared fit interval contains fewer than three finite divergence points")

    raw_time = divergence.time_lags[mask]
    normalized_unit = divergence.time_unit.lower()
    if normalized_unit in _TIME_TO_SECONDS:
        x = raw_time * _TIME_TO_SECONDS[normalized_unit]
        exponent_unit = "1/s"
    else:
        x = raw_time
        exponent_unit = f"1/{divergence.time_unit}"
    y = divergence.mean_log_divergence[mask]
    fit = stats.linregress(x, y)
    return LargestLyapunovResult(
        exponent=float(fit.slope),
        exponent_unit=exponent_unit,
        intercept=float(fit.intercept),
        r_squared=float(fit.rvalue**2),
        standard_error=float(fit.stderr),
        fit_start=float(divergence.time_lags[start]),
        fit_end=float(divergence.time_lags[end]),
        n_fit_points=int(np.sum(mask)),
        divergence=divergence,
        provenance={
            "operation": "estimate_largest_lyapunov_rosenstein",
            "divergence_provenance": dict(divergence.provenance),
            "fit_start_samples": start,
            "fit_end_samples": end,
            "fit_interval_selected_automatically": False,
            "interpretation_boundary": (
                "positive exponent estimates local exponential divergence; "
                "it is not standalone evidence of deterministic chaos"
            ),
        },
    )


def _iaaft_one(
    signal: np.ndarray,
    *,
    rng: np.random.Generator,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, int]:
    sorted_target = np.sort(signal)
    target_amplitude = np.abs(np.fft.rfft(signal))
    surrogate = rng.permutation(signal)
    previous_error = np.inf

    for iteration in range(1, max_iterations + 1):
        spectrum = np.fft.rfft(surrogate)
        phase = np.exp(1j * np.angle(spectrum))
        adjusted = np.fft.irfft(target_amplitude * phase, n=signal.size)
        order = np.argsort(adjusted, kind="mergesort")
        ranked = np.empty_like(adjusted)
        ranked[order] = sorted_target
        current_amplitude = np.abs(np.fft.rfft(ranked))
        denominator = max(float(np.linalg.norm(target_amplitude)), np.finfo(float).eps)
        error = float(np.linalg.norm(current_amplitude - target_amplitude) / denominator)
        surrogate = ranked
        if abs(previous_error - error) <= tolerance:
            return surrogate, iteration
        previous_error = error
    return surrogate, max_iterations


def _scalar_trajectory(
    source: TrajectorySet,
    *,
    curve_index: int,
    dimension: str,
    values: np.ndarray,
) -> TrajectorySet:
    return TrajectorySet(
        time=source.time.copy(),
        values=np.asarray(values, dtype=float)[None, :, None],
        curve_ids=(source.curve_ids[curve_index],),
        dimension_names=(dimension,),
        metadata=source.metadata.iloc[[curve_index]].reset_index(drop=True),
        coordinate_system=source.coordinate_system,
        time_unit=source.time_unit,
        provenance={
            **dict(source.provenance),
            "surrogate_dimension": dimension,
        },
    )


def _lle_statistic(
    trajectory: TrajectorySet,
    *,
    embedding_dimension: int,
    delay: float | int,
    delay_units: str,
    theiler_window: float | int,
    theiler_window_units: str,
    max_horizon: float | int,
    max_horizon_units: str,
    fit_start: float | int,
    fit_end: float | int,
    fit_units: str,
) -> float:
    embedding = delay_embed_trajectory(
        trajectory,
        embedding_dimension=embedding_dimension,
        delay=delay,
        delay_units=delay_units,
        dimensions=trajectory.dimension_names,
    )
    divergence = local_divergence_curve(
        embedding,
        curve=0,
        theiler_window=theiler_window,
        theiler_window_units=theiler_window_units,
        max_horizon=max_horizon,
        max_horizon_units=max_horizon_units,
    )
    return estimate_largest_lyapunov_rosenstein(
        divergence,
        fit_start=fit_start,
        fit_end=fit_end,
        fit_units=fit_units,
    ).exponent


def surrogate_nonlinearity_test(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimension: str,
    statistic: str,
    embedding_dimension: int,
    delay: float | int,
    theiler_window: float | int,
    max_horizon: float | int,
    fit_start: float | int,
    fit_end: float | int,
    delay_units: str = "samples",
    theiler_window_units: str = "samples",
    max_horizon_units: str = "samples",
    fit_units: str = "samples",
    method: str = "iaaft",
    n_surrogates: int = 199,
    alternative: str = "greater",
    max_iterations: int = 1000,
    tolerance: float = 1e-8,
    random_state: int | None = None,
) -> SurrogateNonlinearityResult:
    """Test a declared nonlinear statistic against IAAFT surrogate series.

    Version 0.23 supports statistic='largest_lyapunov' only. Every surrogate is
    evaluated under the identical embedding and fit contract.
    """

    if statistic != "largest_lyapunov":
        raise ValueError("0.23 supports statistic='largest_lyapunov' only")
    if method != "iaaft":
        raise ValueError("0.23 supports method='iaaft' only")
    if alternative not in {"greater", "less", "two-sided"}:
        raise ValueError("alternative must be 'greater', 'less', or 'two-sided'")
    if not isinstance(n_surrogates, (int, np.integer)) or n_surrogates < 1:
        raise ValueError("n_surrogates must be a positive integer")
    if not isinstance(max_iterations, (int, np.integer)) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")
    if dimension not in trajectories.dimension_names:
        raise KeyError(f"Unknown dimension {dimension!r}")

    curve_index = _curve_index(trajectories, curve)
    signal = trajectories.dimension(dimension)[curve_index].astype(float, copy=False)
    _require_finite(signal, context="surrogate nonlinearity testing")
    if np.std(signal, ddof=0) <= 0:
        raise ValueError("surrogate testing requires a non-constant signal")

    observed_trajectory = _scalar_trajectory(
        trajectories,
        curve_index=curve_index,
        dimension=dimension,
        values=signal,
    )
    common = {
        "embedding_dimension": embedding_dimension,
        "delay": delay,
        "delay_units": delay_units,
        "theiler_window": theiler_window,
        "theiler_window_units": theiler_window_units,
        "max_horizon": max_horizon,
        "max_horizon_units": max_horizon_units,
        "fit_start": fit_start,
        "fit_end": fit_end,
        "fit_units": fit_units,
    }
    observed = _lle_statistic(observed_trajectory, **common)

    rng = np.random.default_rng(random_state)
    surrogate_statistics = np.empty(int(n_surrogates), dtype=float)
    iterations = np.empty(int(n_surrogates), dtype=int)
    for b in range(int(n_surrogates)):
        surrogate, n_iter = _iaaft_one(
            signal,
            rng=rng,
            max_iterations=int(max_iterations),
            tolerance=float(tolerance),
        )
        surrogate_trajectory = _scalar_trajectory(
            trajectories,
            curve_index=curve_index,
            dimension=dimension,
            values=surrogate,
        )
        try:
            surrogate_statistics[b] = _lle_statistic(surrogate_trajectory, **common)
        except Exception as exc:
            raise RuntimeError(
                f"surrogate {b} failed under the declared analysis contract"
            ) from exc
        iterations[b] = n_iter

    if alternative == "greater":
        exceedances = int(np.sum(surrogate_statistics >= observed))
    elif alternative == "less":
        exceedances = int(np.sum(surrogate_statistics <= observed))
    else:
        center = float(np.median(surrogate_statistics))
        exceedances = int(
            np.sum(np.abs(surrogate_statistics - center) >= abs(observed - center))
        )
    p_value = (exceedances + 1.0) / (int(n_surrogates) + 1.0)

    return SurrogateNonlinearityResult(
        observed_statistic=float(observed),
        surrogate_statistics=surrogate_statistics,
        p_value=float(p_value),
        alternative=alternative,
        statistic=statistic,
        method=method,
        n_surrogates=int(n_surrogates),
        random_state=random_state,
        convergence_iterations=iterations,
        provenance={
            "operation": "surrogate_nonlinearity_test",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": trajectories.curve_ids[curve_index],
            "dimension": dimension,
            "surrogate_method": "IAAFT",
            "p_value_correction": "plus_one",
            "common_statistic_settings": common,
            "failed_surrogate_policy": "raise",
            "interpretation_boundary": (
                "rejection is evidence against the declared linear-stochastic surrogate null; "
                "it does not establish a unique deterministic chaotic mechanism"
            ),
        },
    )
