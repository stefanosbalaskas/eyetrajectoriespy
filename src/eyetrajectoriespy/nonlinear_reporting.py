"""Reporting helpers for nonlinear trajectory dynamics."""

from __future__ import annotations

import numpy as np

from .nonlinear_types import (
    LargestLyapunovResult,
    RecurrenceResult,
    RQAResult,
    ReturnMapStabilityResult,
    SurrogateNonlinearityResult,
    WindowedRQAResult,
)


def rqa_reporting_text(
    recurrence: RecurrenceResult,
    metrics: RQAResult,
) -> str:
    """Return concise manuscript-ready recurrence-analysis wording."""

    radius_policy = recurrence.provenance.get("radius_policy", "unknown")
    if radius_policy == "target_recurrence_rate":
        policy = (
            f"target recurrence rate {recurrence.target_recurrence_rate:.4g}, "
            f"yielding radius {recurrence.radius:.4g} and achieved RR "
            f"{recurrence.achieved_recurrence_rate:.4g}"
        )
    else:
        policy = f"fixed radius {recurrence.radius:.4g}"
    return (
        f"Recurrence analysis used {recurrence.kind} recurrence with the "
        f"{recurrence.metric} metric, {policy}, and a Theiler window of "
        f"{recurrence.theiler_window_samples} samples. RQA used minimum "
        f"diagonal and vertical line lengths of {metrics.min_diagonal_length} "
        f"and {metrics.min_vertical_length}, respectively. The resulting "
        f"RR was {metrics.recurrence_rate:.4g}, DET {metrics.determinism:.4g}, "
        f"LAM {metrics.laminarity:.4g}, and trapping time "
        f"{metrics.trapping_time:.4g}."
    )


def windowed_rqa_reporting_text(result: WindowedRQAResult) -> str:
    """Return concise manuscript-ready wording for sliding-window RQA."""

    return (
        f"Windowed RQA used full windows of {result.window_samples} samples "
        f"advanced by {result.step_samples} samples, producing "
        f"{len(result.table)} windows. The final {result.dropped_tail_samples} "
        "samples outside a complete window were retained in the audit record "
        "but not analyzed as a partial window."
    )


def largest_lyapunov_reporting_text(result: LargestLyapunovResult) -> str:
    """Return wording that keeps the Rosenstein estimate distinct from chaos claims."""

    return (
        f"A Rosenstein-style local-divergence estimate was fitted over "
        f"{result.fit_start:.4g} to {result.fit_end:.4g} "
        f"{result.divergence.time_unit} using {result.n_fit_points} divergence "
        f"points. The estimated largest Lyapunov exponent was "
        f"{result.exponent:.4g} {result.exponent_unit} "
        f"(R^2={result.r_squared:.3f}, slope SE={result.standard_error:.4g}). "
        "This quantity was interpreted as a conditional local-divergence "
        "estimate and not as standalone evidence of deterministic chaos."
    )


def surrogate_nonlinearity_reporting_text(
    result: SurrogateNonlinearityResult,
) -> str:
    """Return manuscript-ready IAAFT surrogate-test wording."""

    finite = np.isfinite(result.surrogate_statistics)
    if not np.all(finite):
        raise ValueError("surrogate statistics must all be finite for reporting")
    return (
        f"Nonlinearity was assessed with {result.n_surrogates} "
        f"{result.method.upper()} surrogates using the "
        f"{result.statistic.replace('_', ' ')} statistic and a "
        f"{result.alternative} alternative. A plus-one Monte Carlo p-value "
        f"was used (p={result.p_value:.4g}; random_state={result.random_state}). "
        "The test was interpreted relative to the declared surrogate null, "
        "not as proof of a unique nonlinear or chaotic mechanism."
    )


def return_map_stability_reporting_text(
    result: ReturnMapStabilityResult,
) -> str:
    """Return manuscript-ready wording for experimental empirical return-map stability."""

    eigenvalue_text = ", ".join(
        f"{value.real:.4g}{value.imag:+.4g}i" if abs(value.imag) > 1e-12 else f"{value.real:.4g}"
        for value in result.eigenvalues
    )
    return (
        "Experimental empirical return-map stability was summarized from the "
        f"local fitted Jacobian eigenvalues ({eigenvalue_text}), with spectral "
        f"radius {result.spectral_radius:.4g} and tolerance {result.tolerance:.4g}; "
        f"the map was classified as {result.classification}. These eigenvalues "
        "were not interpreted as classical Floquet multipliers and the fitted "
        "Jacobian was not described as a monodromy matrix."
    )
