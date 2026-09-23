"""Reporting helpers for nonlinear trajectory dynamics."""

from __future__ import annotations

import numpy as np

from .nonlinear_types import (
    KantzDivergenceResult,
    LargestLyapunovResult,
    LyapunovParameterSensitivityResult,
    RecurrenceRadiusProfileResult,
    RecurrenceResult,
    RQAMeanBootstrapResult,
    RQAResult,
    RQAParameterSensitivityResult,
    LocalReturnMapResult,
    ReturnMapStabilityResult,
    SurrogateNonlinearityResult,
    WindowedRQAFunctionalResult,
    WindowedRQAMeanBandResult,
    WindowedRQAResult,
    WindowedRQASensitivityResult,
)


def recurrence_radius_profile_reporting_text(
    result: RecurrenceRadiusProfileResult,
) -> str:
    """Return manuscript-ready wording for recurrence-threshold diagnostics."""

    table = result.table
    coverage = float(
        result.provenance.get(
            "maximum_radius_coverage_fraction",
            table["recurrence_rate"].iloc[-1],
        )
    )
    complete = bool(
        result.provenance.get("full_distance_distribution_captured", False)
    )
    coverage_text = (
        "the supplied maximum radius covered the complete eligible "
        "pair-distance distribution"
        if complete
        else (
            f"the supplied maximum radius covered {100.0 * coverage:.1f}% "
            "of eligible pair distances"
        )
    )
    return (
        f"Recurrence-threshold diagnostics evaluated {result.n_radii} "
        f"predeclared radii for curve {result.curve_id!r} using the "
        f"{result.metric} state-space distance and a Theiler window of "
        f"{result.theiler_window_samples} samples. RR increased from "
        f"{table['recurrence_rate'].iloc[0]:.4g} to "
        f"{table['recurrence_rate'].iloc[-1]:.4g}; {coverage_text}. "
        "Cumulative and shell pair counts were computed with the same "
        "eligible-pair denominator and inclusive radius rule as the base "
        "recurrence estimator. No radius was selected automatically."
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


def rqa_metric_mean_bootstrap_reporting_text(
    result: RQAMeanBootstrapResult,
) -> str:
    """Return manuscript-ready wording for population-average RQA uncertainty."""

    metric_text = ", ".join(result.metrics)
    if result.unit == "participant":
        unit_text = (
            f"{result.n_units} equal-weight participant units defined by "
            f"{result.participant_column!r}; repeated curve-level RQA metrics "
            "were averaged within participant before resampling"
        )
    else:
        unit_text = f"{result.n_units} curve-level independent units"

    return (
        f"Population-average RQA uncertainty for {metric_text} used "
        f"{result.n_bootstrap} percentile bootstrap replicates at the "
        f"{100.0 * result.confidence_level:.1f}% level and {unit_text}. "
        "Each source curve was summarized under one fixed declared RQA "
        "specification before unit-level resampling. Undefined selected "
        "curve-level metrics caused analysis failure rather than deletion or "
        "imputation. These intervals describe between-unit population sampling "
        "uncertainty conditional on the declared RQA specification; they do "
        "not estimate within-single-trajectory recurrence uncertainty, "
        "recurrence-line resampling uncertainty, or parameter-selection "
        "uncertainty."
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



def windowed_rqa_functional_reporting_text(
    result: WindowedRQAFunctionalResult,
) -> str:
    """Return manuscript-ready wording for RQA-derived functional trajectories."""

    metric_text = ", ".join(result.metrics)
    overlap = 100.0 * result.overlap_fraction
    radius_policy = result.trajectories.provenance.get("radius_policy", "unknown")
    return (
        f"Windowed RQA was converted to functional trajectories for "
        f"{result.n_curves} source curve(s) using {result.n_windows} complete "
        f"windows of {result.window_samples} samples, advanced by "
        f"{result.step_samples} samples ({overlap:.1f}% sample overlap). "
        f"Functional dimensions were {metric_text}; the recurrence-radius "
        f"policy was {radius_policy}. Window centers formed the functional "
        f"time grid and {result.dropped_tail_samples} trailing samples outside "
        "a complete window were excluded explicitly. Window rows were not "
        "treated as independent observations; downstream inference retained "
        "the source curve/participant as the sampling unit."
    )


def windowed_rqa_sensitivity_reporting_text(
    result: WindowedRQASensitivityResult,
) -> str:
    """Return manuscript-ready wording for declared window/step sensitivity."""

    design = result.design_table
    overlap_min = 100.0 * float(design["overlap_fraction"].min())
    overlap_max = 100.0 * float(design["overlap_fraction"].max())
    spacing_min = float(design["profile_grid_spacing_time"].min())
    spacing_max = float(design["profile_grid_spacing_time"].max())
    return (
        f"Functional RQA sensitivity was evaluated across "
        f"{result.n_specifications} predeclared window/step specifications. "
        f"Sample overlap ranged from {overlap_min:.1f}% to {overlap_max:.1f}% "
        f"and derived-profile grid spacing ranged from {spacing_min:.4g} to "
        f"{spacing_max:.4g} {design['profile_time_unit'].iloc[0]}. "
        "Overlap diagnostics quantified deterministic source-sample reuse; "
        "they were not converted into an effective independent sample size. "
        "Pairwise profile comparisons used exact shared window centers only, "
        "with no interpolation and no automatic selection of a preferred "
        "window/step specification."
    )


def windowed_rqa_mean_band_reporting_text(
    result: WindowedRQAMeanBandResult,
) -> str:
    """Return wording for unit-level simultaneous functional-RQA inference."""

    band = result.band
    overlap = 100.0 * result.functional_rqa.overlap_fraction
    if result.unit == "participant":
        unit_text = (
            f"participant-level units defined by "
            f"{result.participant_column!r}"
        )
    else:
        unit_text = "curve-level units"
    return (
        f"Windowed RQA functions used {result.functional_rqa.window_samples}-sample "
        f"windows advanced by {result.functional_rqa.step_samples} samples "
        f"({overlap:.1f}% overlap). Simultaneous observed-grid mean inference "
        f"used {len(band.unit_ids)} independent {unit_text} and a "
        f"{100.0 * band.confidence_level:.1f}% Gaussian multiplier band. "
        "Complete derived functions, not window rows, were the resampling "
        "objects, preserving within-function temporal dependence. The procedure "
        "does not provide a within-trajectory block-bootstrap guarantee or "
        "treat overlapping windows as independent observations."
    )



def rqa_parameter_sensitivity_reporting_text(
    result: RQAParameterSensitivityResult,
) -> str:
    """Return manuscript-ready wording for an RQA parameter multiverse."""

    summary = result.summary_table.set_index("metric")
    det = summary.loc["determinism"]
    lam = summary.loc["laminarity"]
    rr = summary.loc["recurrence_rate"]
    threshold_policy = result.provenance.get("threshold_policy", "unknown")
    controlled = (
        " Recurrence rate was controlled by the target-rate design and was "
        "not treated as an independent robustness outcome."
        if threshold_policy == "target_recurrence_rate"
        else ""
    )
    return (
        f"RQA robustness was evaluated across {result.n_specifications} "
        f"predeclared parameter specifications for curve {result.curve_id!r}. "
        f"DET ranged from {det['minimum']:.4g} to {det['maximum']:.4g}, "
        f"LAM from {lam['minimum']:.4g} to {lam['maximum']:.4g}, and RR from "
        f"{rr['minimum']:.4g} to {rr['maximum']:.4g}. Every Cartesian-product "
        "specification was retained in the sensitivity table; no parameter "
        "combination was selected automatically and invalid specifications "
        "were configured to fail the analysis rather than disappear silently."
        + controlled
    )


def lyapunov_parameter_sensitivity_reporting_text(
    result: LyapunovParameterSensitivityResult,
) -> str:
    """Return manuscript-ready wording for Rosenstein-LLE sensitivity."""

    summary = result.summary_table.set_index("metric")
    exponent = summary.loc["exponent"]
    return (
        f"Rosenstein local-divergence sensitivity was evaluated across "
        f"{result.n_specifications} predeclared reconstruction, Theiler-window, "
        f"and fit-interval specifications for curve {result.curve_id!r}. "
        f"Estimated exponents ranged from {exponent['minimum']:.4g} to "
        f"{exponent['maximum']:.4g} {result.exponent_unit}; "
        f"{100.0 * exponent['positive_specification_fraction']:.1f}% of finite "
        "declared specifications had positive slopes. This percentage was "
        "reported only as descriptive sensitivity across the declared analysis "
        "grid, not as a probability of deterministic chaos. No reconstruction "
        "or fit interval was selected automatically."
    )


def largest_lyapunov_reporting_text(result: LargestLyapunovResult) -> str:
    """Return named-estimator LLE wording without turning slope into a chaos claim."""

    if isinstance(result.divergence, KantzDivergenceResult):
        method = (
            f"Kantz fixed-radius neighborhood divergence "
            f"(radius={result.divergence.radius:.4g}, "
            f"min_neighbors={result.divergence.min_neighbors})"
        )
    else:
        method = "Rosenstein nearest-neighbor divergence"

    return (
        f"A {method} estimate was fitted over "
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
        f"was used (p={result.p_value:.4g}; random_state={result.random_state}); "
        f"the maximum retained final relative spectrum mismatch was "
        f"{np.max(result.spectral_errors):.4g}. "
        "The test was interpreted relative to the declared surrogate null, "
        "not as proof of a unique nonlinear or chaotic mechanism."
    )


def return_map_stability_reporting_text(
    fit: LocalReturnMapResult,
    result: ReturnMapStabilityResult,
) -> str:
    """Return manuscript-ready wording for experimental empirical return-map stability."""

    eigenvalue_text = ", ".join(
        f"{value.real:.4g}{value.imag:+.4g}i" if abs(value.imag) > 1e-12 else f"{value.real:.4g}"
        for value in result.eigenvalues
    )
    r2_text = ", ".join(
        "nan" if not np.isfinite(value) else f"{value:.3f}"
        for value in fit.r_squared
    )
    crossing = fit.provenance.get("crossing_provenance", {})
    section = crossing.get("section_dimension", "unknown")
    section_value = crossing.get("section_value", "unknown")
    direction = crossing.get("direction", "unknown")
    return (
        "Experimental empirical return-map stability used section "
        f"{section}={section_value} with {direction} crossings and a "
        f"{fit.neighborhood_policy} neighborhood ({fit.neighborhood_value}); "
        f"{fit.n_transitions} transitions were fitted. The local design "
        f"condition number was {fit.design_condition_number:.4g} and per-state "
        f"R^2 values were [{r2_text}]. Jacobian eigenvalues were "
        f"({eigenvalue_text}), with spectral radius {result.spectral_radius:.4g} "
        f"and tolerance {result.tolerance:.4g}; the map was classified as "
        f"{result.classification}. These eigenvalues were not interpreted as "
        "classical Floquet multipliers and the fitted Jacobian was not described "
        "as a monodromy matrix."
    )
