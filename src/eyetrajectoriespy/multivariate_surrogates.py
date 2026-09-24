"""Cross-spectrum-aware multivariate IAAFT surrogate generation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .embedding import _curve_index, _regular_step, _require_finite
from .nonlinear_dynamics import _lle_statistic
from .nonlinear_types import (
    MultivariateIAAFTResult,
    MultivariateSurrogateNonlinearityResult,
)
from .types import TrajectorySet
from .validation import validate_trajectory_set


def _validate_dimensions(
    trajectories: TrajectorySet,
    dimensions: Sequence[str],
) -> tuple[tuple[str, ...], np.ndarray]:
    if isinstance(dimensions, (str, bytes)):
        raise TypeError("dimensions must be a non-string sequence")
    names = tuple(dimensions)
    if len(names) < 2:
        raise ValueError("multivariate surrogates require at least two dimensions")
    if not all(isinstance(name, str) for name in names):
        raise TypeError("dimension names must be strings")
    if len(set(names)) != len(names):
        raise ValueError("dimensions must not contain duplicates")
    missing = [name for name in names if name not in trajectories.dimension_names]
    if missing:
        raise KeyError(f"Unknown trajectory dimensions: {missing}")
    indices = np.asarray(
        [trajectories.dimension_names.index(name) for name in names],
        dtype=int,
    )
    return names, indices


def _rank_match_columns(
    adjusted: np.ndarray,
    sorted_target: np.ndarray,
) -> np.ndarray:
    ranked = np.empty_like(adjusted)
    for dimension_index in range(adjusted.shape[1]):
        order = np.argsort(
            adjusted[:, dimension_index],
            kind="mergesort",
        )
        ranked[order, dimension_index] = sorted_target[:, dimension_index]
    return ranked


def _spectrum_errors(
    values: np.ndarray,
    *,
    target_amplitudes: np.ndarray,
    target_cross_spectra: tuple[np.ndarray, ...],
    pairs: tuple[tuple[int, int], ...],
) -> tuple[np.ndarray, np.ndarray]:
    spectrum = np.fft.rfft(values, axis=0)
    amplitudes = np.abs(spectrum)
    eps = np.finfo(float).eps

    spectral_errors = np.empty(values.shape[1], dtype=float)
    for dimension_index in range(values.shape[1]):
        target = target_amplitudes[:, dimension_index]
        denominator = max(float(np.linalg.norm(target)), eps)
        spectral_errors[dimension_index] = float(
            np.linalg.norm(amplitudes[:, dimension_index] - target)
            / denominator
        )

    cross_errors = np.empty(len(pairs), dtype=float)
    for pair_index, (left, right) in enumerate(pairs):
        current = spectrum[:, left] * np.conj(spectrum[:, right])
        target = target_cross_spectra[pair_index]
        # DC is determined exactly by the retained marginal mean and carries
        # no useful phase-randomization information.
        current_eval = current[1:]
        target_eval = target[1:]
        denominator = max(float(np.linalg.norm(target_eval)), eps)
        cross_errors[pair_index] = float(
            np.linalg.norm(current_eval - target_eval) / denominator
        )
    return spectral_errors, cross_errors


def _multivariate_iaaft_one(
    values: np.ndarray,
    *,
    reference_index: int,
    rng: np.random.Generator,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, int, np.ndarray, np.ndarray]:
    """Generate one reference-anchored multivariate IAAFT surrogate."""

    n_time, n_dimensions = values.shape
    sorted_target = np.sort(values, axis=0)
    target_spectrum = np.fft.rfft(values, axis=0)
    target_amplitudes = np.abs(target_spectrum)
    target_phases = np.angle(target_spectrum)

    phase_offsets = (
        target_phases
        - target_phases[:, [reference_index]]
    )
    pairs = tuple(
        (left, right)
        for left in range(n_dimensions)
        for right in range(left + 1, n_dimensions)
    )
    target_cross_spectra = tuple(
        target_spectrum[:, left] * np.conj(target_spectrum[:, right])
        for left, right in pairs
    )

    surrogate = np.column_stack(
        [rng.permutation(values[:, index]) for index in range(n_dimensions)]
    )
    previous_error = np.inf

    for iteration in range(1, max_iterations + 1):
        current_spectrum = np.fft.rfft(surrogate, axis=0)
        reference_phase = np.angle(
            current_spectrum[:, reference_index]
        )
        desired_phases = (
            reference_phase[:, None]
            + phase_offsets
        )
        adjusted_spectrum = (
            target_amplitudes
            * np.exp(1j * desired_phases)
        )

        # Retain the real-valued DC and, for even-length signals, Nyquist
        # coefficients exactly. These bins cannot carry arbitrary complex
        # phases in a real inverse FFT.
        adjusted_spectrum[0] = target_spectrum[0]
        if n_time % 2 == 0:
            adjusted_spectrum[-1] = target_spectrum[-1]

        adjusted = np.fft.irfft(
            adjusted_spectrum,
            n=n_time,
            axis=0,
        )
        ranked = _rank_match_columns(adjusted, sorted_target)

        spectral_errors, cross_errors = _spectrum_errors(
            ranked,
            target_amplitudes=target_amplitudes,
            target_cross_spectra=target_cross_spectra,
            pairs=pairs,
        )
        combined_error = max(
            float(np.max(spectral_errors)),
            float(np.max(cross_errors)),
        )
        rank_stable = np.array_equal(ranked, surrogate)
        surrogate = ranked

        if rank_stable or abs(previous_error - combined_error) <= tolerance:
            return (
                surrogate,
                iteration,
                spectral_errors,
                cross_errors,
            )
        previous_error = combined_error

    raise RuntimeError(
        "multivariate IAAFT surrogate did not converge within max_iterations; "
        "increase max_iterations or relax tolerance explicitly"
    )


def generate_multivariate_iaaft_surrogates(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    reference_dimension: str,
    n_surrogates: int = 199,
    max_iterations: int = 1000,
    tolerance: float = 1e-8,
    random_state: int | None = None,
) -> MultivariateIAAFTResult:
    """Generate cross-spectrum-aware multivariate IAAFT surrogates.

    The implementation follows the Prichard-Theiler multivariate phase
    constraint extended through an IAAFT rank-remapping loop. At each Fourier
    adjustment, the original inter-channel phase differences are imposed
    relative to an explicitly declared reference dimension while every channel
    receives its original Fourier amplitudes. Rank remapping then restores each
    channel's empirical marginal distribution exactly.

    Because rank remapping perturbs the spectrum, the final power spectra and
    cross-spectra are approximate and their relative errors are retained for
    every surrogate. The reference dimension is never selected automatically.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    regular_step = _regular_step(trajectories.time)
    dimension_names, dimension_indices = _validate_dimensions(
        trajectories,
        dimensions,
    )
    if reference_dimension not in dimension_names:
        raise ValueError(
            "reference_dimension must be one of the declared dimensions"
        )
    if (
        isinstance(n_surrogates, bool)
        or not isinstance(n_surrogates, (int, np.integer))
        or int(n_surrogates) < 1
    ):
        raise ValueError("n_surrogates must be a positive integer")
    if (
        isinstance(max_iterations, bool)
        or not isinstance(max_iterations, (int, np.integer))
        or int(max_iterations) < 1
    ):
        raise ValueError("max_iterations must be a positive integer")
    if (
        isinstance(tolerance, bool)
        or not isinstance(
            tolerance,
            (int, float, np.integer, np.floating),
        )
        or not np.isfinite(tolerance)
        or float(tolerance) <= 0
    ):
        raise ValueError("tolerance must be positive and finite")

    curve_index = _curve_index(trajectories, curve)
    values = trajectories.values[curve_index][
        :,
        dimension_indices,
    ].astype(float, copy=False)
    _require_finite(
        values,
        context="multivariate IAAFT surrogate generation",
    )
    zero_variance = [
        dimension_names[index]
        for index in range(values.shape[1])
        if np.std(values[:, index], ddof=0) <= 0
    ]
    if zero_variance:
        raise ValueError(
            "multivariate IAAFT requires non-constant dimensions; "
            f"constant dimensions: {zero_variance}"
        )

    reference_index = dimension_names.index(reference_dimension)
    pairs = tuple(
        (left, right)
        for left in range(len(dimension_names))
        for right in range(left + 1, len(dimension_names))
    )
    pair_names = tuple(
        (dimension_names[left], dimension_names[right])
        for left, right in pairs
    )

    rng = np.random.default_rng(random_state)
    surrogates = np.empty(
        (
            int(n_surrogates),
            values.shape[0],
            values.shape[1],
        ),
        dtype=float,
    )
    iterations = np.empty(int(n_surrogates), dtype=int)
    spectral_errors = np.empty(
        (int(n_surrogates), values.shape[1]),
        dtype=float,
    )
    cross_spectral_errors = np.empty(
        (int(n_surrogates), len(pairs)),
        dtype=float,
    )

    for surrogate_index in range(int(n_surrogates)):
        try:
            (
                surrogate,
                n_iterations,
                spectrum_error,
                cross_error,
            ) = _multivariate_iaaft_one(
                values,
                reference_index=reference_index,
                rng=rng,
                max_iterations=int(max_iterations),
                tolerance=float(tolerance),
            )
        except Exception as exc:
            raise RuntimeError(
                f"multivariate surrogate {surrogate_index} failed under "
                "the declared MIAAFT contract"
            ) from exc

        surrogates[surrogate_index] = surrogate
        iterations[surrogate_index] = n_iterations
        spectral_errors[surrogate_index] = spectrum_error
        cross_spectral_errors[surrogate_index] = cross_error

    return MultivariateIAAFTResult(
        surrogates=surrogates,
        source_values=values.copy(),
        curve_id=trajectories.curve_ids[curve_index],
        dimension_names=dimension_names,
        reference_dimension=reference_dimension,
        dimension_pairs=pair_names,
        convergence_iterations=iterations,
        spectral_errors=spectral_errors,
        cross_spectral_errors=cross_spectral_errors,
        n_surrogates=int(n_surrogates),
        max_iterations=int(max_iterations),
        tolerance=float(tolerance),
        random_state=random_state,
        provenance={
            "operation": "generate_multivariate_iaaft_surrogates",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": trajectories.curve_ids[curve_index],
            "dimensions": list(dimension_names),
            "reference_dimension": reference_dimension,
            "method": "reference_anchored_multivariate_IAAFT",
            "fourier_constraint": (
                "original_per_dimension_amplitudes_plus_original_"
                "inter_dimension_phase_differences"
            ),
            "marginal_constraint": (
                "exact_per_dimension_empirical_rank_distribution"
            ),
            "cross_spectral_preservation": (
                "approximate_after_final_rank_remapping_with_error_retained"
            ),
            "reference_dimension_selected_automatically": False,
            "sampling_grid": "regular_common_grid",
            "sampling_step": float(regular_step),
            "time_unit": trajectories.time_unit,
            "dimension_scaling": False,
            "smoothing": False,
            "interpolation": False,
            "failed_surrogate_policy": "raise",
            "interpretation_boundary": (
                "surrogates target a multivariate linear-stochastic null "
                "with retained marginal distributions and approximate "
                "auto/cross-spectral structure; they do not preserve "
                "nonlinear cross-dependence by construction"
            ),
        },
    )


def multivariate_iaaft_diagnostics_frame(
    result: MultivariateIAAFTResult,
) -> pd.DataFrame:
    """Return convergence and spectral diagnostics for every surrogate."""

    if not isinstance(result, MultivariateIAAFTResult):
        raise TypeError("result must be a MultivariateIAAFTResult")

    rows: list[dict[str, float | int]] = []
    for surrogate_index in range(result.n_surrogates):
        rows.append(
            {
                "surrogate": surrogate_index,
                "iterations": int(
                    result.convergence_iterations[surrogate_index]
                ),
                "max_spectral_error": float(
                    np.max(result.spectral_errors[surrogate_index])
                ),
                "max_cross_spectral_error": float(
                    np.max(
                        result.cross_spectral_errors[surrogate_index]
                    )
                ),
                "mean_spectral_error": float(
                    np.mean(result.spectral_errors[surrogate_index])
                ),
                "mean_cross_spectral_error": float(
                    np.mean(
                        result.cross_spectral_errors[surrogate_index]
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def _multivariate_surrogate_trajectory(
    source: TrajectorySet,
    *,
    curve_index: int,
    dimension_names: tuple[str, ...],
    values: np.ndarray,
) -> TrajectorySet:
    return TrajectorySet(
        time=source.time.copy(),
        values=np.asarray(values, dtype=float)[None, :, :],
        curve_ids=(source.curve_ids[curve_index],),
        dimension_names=dimension_names,
        metadata=source.metadata.iloc[[curve_index]].reset_index(drop=True),
        coordinate_system=source.coordinate_system,
        time_unit=source.time_unit,
        provenance={
            **dict(source.provenance),
            "multivariate_surrogate_dimensions": list(dimension_names),
        },
    )


def multivariate_surrogate_nonlinearity_test(
    trajectories: TrajectorySet,
    *,
    curve: int | str,
    dimensions: Sequence[str],
    reference_dimension: str,
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
    n_surrogates: int = 199,
    alternative: str = "greater",
    max_iterations: int = 1000,
    tolerance: float = 1e-8,
    random_state: int | None = None,
) -> MultivariateSurrogateNonlinearityResult:
    """Test multichannel LLE against cross-spectrum-aware MIAAFT surrogates."""

    if statistic != "largest_lyapunov":
        raise ValueError(
            "0.37 supports statistic='largest_lyapunov' only"
        )
    if alternative not in {"greater", "less", "two-sided"}:
        raise ValueError(
            "alternative must be 'greater', 'less', or 'two-sided'"
        )

    dimension_names, dimension_indices = _validate_dimensions(
        trajectories,
        dimensions,
    )
    curve_index = _curve_index(trajectories, curve)
    observed_values = trajectories.values[curve_index][
        :,
        dimension_indices,
    ]
    observed_trajectory = _multivariate_surrogate_trajectory(
        trajectories,
        curve_index=curve_index,
        dimension_names=dimension_names,
        values=observed_values,
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

    surrogate_result = generate_multivariate_iaaft_surrogates(
        trajectories,
        curve=curve,
        dimensions=dimension_names,
        reference_dimension=reference_dimension,
        n_surrogates=n_surrogates,
        max_iterations=max_iterations,
        tolerance=tolerance,
        random_state=random_state,
    )

    surrogate_statistics = np.empty(
        surrogate_result.n_surrogates,
        dtype=float,
    )
    for surrogate_index in range(surrogate_result.n_surrogates):
        try:
            surrogate_trajectory = _multivariate_surrogate_trajectory(
                trajectories,
                curve_index=curve_index,
                dimension_names=dimension_names,
                values=surrogate_result.surrogates[surrogate_index],
            )
            surrogate_statistics[surrogate_index] = _lle_statistic(
                surrogate_trajectory,
                **common,
            )
        except Exception as exc:
            raise RuntimeError(
                f"multivariate surrogate statistic {surrogate_index} "
                "failed under the declared analysis contract"
            ) from exc

    upper = (
        int(np.sum(surrogate_statistics >= observed)) + 1.0
    ) / (surrogate_result.n_surrogates + 1.0)
    lower = (
        int(np.sum(surrogate_statistics <= observed)) + 1.0
    ) / (surrogate_result.n_surrogates + 1.0)
    if alternative == "greater":
        p_value = upper
    elif alternative == "less":
        p_value = lower
    else:
        p_value = min(1.0, 2.0 * min(upper, lower))

    return MultivariateSurrogateNonlinearityResult(
        observed_statistic=float(observed),
        surrogate_statistics=surrogate_statistics,
        p_value=float(p_value),
        alternative=alternative,
        statistic=statistic,
        surrogate_result=surrogate_result,
        provenance={
            "operation": "multivariate_surrogate_nonlinearity_test",
            "source_provenance": dict(trajectories.provenance),
            "curve_id": trajectories.curve_ids[curve_index],
            "dimensions": list(dimension_names),
            "reference_dimension": reference_dimension,
            "surrogate_method": "multivariate_IAAFT",
            "common_statistic_settings": common,
            "p_value_correction": (
                "plus_one"
                if alternative in {"greater", "less"}
                else "two_sided_double_min_plus_one_tails"
            ),
            "failed_surrogate_policy": "raise",
            "interpretation_boundary": (
                "rejection is evidence against the declared multivariate "
                "linear-stochastic surrogate null; it does not establish "
                "deterministic chaos or a unique nonlinear mechanism"
            ),
        },
    )
