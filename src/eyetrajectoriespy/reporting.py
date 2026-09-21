"""Concise reporting helpers for functional gaze analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .prediction import select_fpca_regression_components, summarise_fpca_regression_cv
from .selection import select_fpca_components_cv, summarise_fpca_cross_validation
from .subspace import fpca_eigenvalue_gap_table, summarise_fpca_subspace_stability
from .types import (
    FPCAComponentBandResult,
    FPCAComponentEnvelopeResult,
    FPCACrossValidationResult,
    FPCAInfluenceResult,
    FPCANestedRegressionCVResult,
    FPCARegressionCVResult,
    FPCARegressionPredictionIntervalResult,
    FPCARegressionSlopeBandResult,
    FPCARegressionUncertaintyResult,
    FPCAResult,
    FPCAScoreUncertaintyResult,
    FPCASpectrumUncertaintyResult,
    FPCAStabilityResult,
    FPCASubspaceStabilityResult,
    FunctionalMeanBandResult,
    ConformalFunctionalAnomalyResult,
    FunctionalOutlierResult,
    MultilevelFPCAResult,
    RegistrationSensitivityResult,
    SparseFPCAResult,
    TrajectorySet,
)


def summarise_trajectory_set(trajectories: TrajectorySet) -> pd.DataFrame:
    """Return a one-row representation summary without making exclusion decisions."""
    missing = np.isnan(trajectories.values)
    return pd.DataFrame([{
        "n_curves": trajectories.n_curves,
        "n_time": trajectories.n_time,
        "n_dimensions": trajectories.n_dimensions,
        "time_start": trajectories.time[0],
        "time_end": trajectories.time[-1],
        "time_unit": trajectories.time_unit,
        "coordinate_system": trajectories.coordinate_system,
        "missing_fraction": float(missing.mean()),
        "dimensions": ", ".join(trajectories.dimension_names),
    }])


def summarise_fpca(result: FPCAResult) -> pd.DataFrame:
    """Return a component-level explained-variance table."""
    return pd.DataFrame({
        "component": np.arange(1, result.n_components + 1),
        "explained_variance": result.explained_variance,
        "explained_variance_ratio": result.explained_variance_ratio,
        "cumulative_variance_ratio": np.cumsum(result.explained_variance_ratio),
    })


def fpca_reporting_text(result: FPCAResult, *, digits: int = 1) -> str:
    """Generate compact manuscript-ready descriptive text for an FPCA fit."""
    pct = 100 * result.cumulative_explained_variance()[-1]
    individual = 100 * result.explained_variance_ratio
    head = ", ".join(f"FPC{i + 1}={v:.{digits}f}%" for i, v in enumerate(individual[:4]))
    scaling = result.provenance.get("fpca", {}).get("scaling", "unknown")
    return (
        f"Functional PCA retained {result.n_components} component(s), explaining {pct:.{digits}f}% of the "
        f"weighted functional variance ({head}). The analysis used {result.coordinate_system} coordinates, "
        f"time unit '{result.time_unit}', and channel scaling='{scaling}'."
    )


def fpca_score_uncertainty_reporting_text(
    result: FPCAScoreUncertaintyResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented wording for basis-resampled FPC scores."""

    median_similarity = np.median(result.similarities, axis=0)
    similarity_text = ", ".join(
        f"FPC{k + 1}={value:.{digits}f}"
        for k, value in enumerate(median_similarity)
    )
    settings = result.provenance.get("fpca_score_uncertainty", {})
    scaling = settings.get("scaling", "unknown")
    return (
        f"FPC score sensitivity to basis estimation was evaluated with "
        f"{result.n_bootstrap} {result.resampling_unit}-level bootstrap "
        f"refits (scaling={scaling!r}) for {result.n_targets} fixed "
        f"{result.target_source} target trajectory/trajectories. Bootstrap "
        "components were matched and sign-aligned to the full-sample reference "
        f"(median absolute similarities: {similarity_text}). Pointwise "
        f"{100 * result.level:.1f}% percentile envelopes summarize variation "
        "in target scores induced by re-estimation of the FPCA basis. These "
        "envelopes do not include target measurement error, uncertainty in a "
        "latent target curve, future-curve sampling variability, preprocessing "
        "uncertainty, or full downstream-model uncertainty propagation."
    )


def fpca_spectrum_uncertainty_reporting_text(
    result: FPCASpectrumUncertaintyResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented wording for FPCA spectrum uncertainty."""

    median_similarity = np.median(result.similarities, axis=0)
    similarity_text = ", ".join(
        f"FPC{k + 1}={value:.{digits}f}"
        for k, value in enumerate(median_similarity)
    )
    scope = (
        "familywise across the requested components within each spectrum metric"
        if result.simultaneous_scope == "family"
        else "component-wise within each spectrum metric"
    )
    first_ratio = result.reference.explained_variance_ratio[0]
    return (
        "FPCA spectrum uncertainty was evaluated with "
        f"{result.n_bootstrap} {result.resampling_unit}-level bootstrap "
        "replicates. Bootstrap FPCs were matched to the full-sample reference "
        "before eigenvalues and variance ratios were attached to component "
        f"identities. Studentized {100 * result.confidence_level:.1f}% "
        f"uncertainty intervals were calibrated {scope}. "
        f"Median matched absolute similarities were {similarity_text}; the "
        f"reference FPC1 explained-variance ratio was {first_ratio:.{digits}f}. "
        "Familywise calibration, when requested, applies separately to "
        "eigenvalues, explained-variance ratios, and cumulative ratios rather "
        "than jointly across all three metrics. Intervals are not clipped to "
        "the mathematical support and are bootstrap approximations rather than "
        "exact finite-sample confidence guarantees."
    )


def multilevel_fpca_reporting_text(result: MultilevelFPCAResult, *, digits: int = 1) -> str:
    """Generate a compact description of participant/trial functional decomposition."""
    p = 100 * result.participant_fpca.cumulative_explained_variance()[-1]
    t = 100 * result.trial_fpca.cumulative_explained_variance()[-1]
    return (
        "Two-level functional decomposition separated participant-level from within-participant trial variation. "
        f"The retained participant components explained {p:.{digits}f}% of fitted participant-level variance; "
        f"the retained trial components explained {t:.{digits}f}% of fitted trial-level variance."
    )



def fpca_stability_reporting_text(
    result: FPCAStabilityResult,
    *,
    similarity_threshold: float = 0.80,
    digits: int = 2,
) -> str:
    """Generate compact descriptive text for bootstrap FPC stability."""

    if not 0 <= similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be in [0, 1]")
    medians = np.median(result.similarities, axis=0)
    fractions = np.mean(result.similarities >= similarity_threshold, axis=0)
    pieces = [
        (
            f"FPC{k + 1}: median |similarity|={medians[k]:.{digits}f}, "
            f"fraction >= {similarity_threshold:.{digits}f}={fractions[k]:.{digits}f}"
        )
        for k in range(result.reference.n_components)
    ]
    return (
        f"Bootstrap FPCA stability used {result.n_bootstrap} {result.resampling_unit}-level "
        f"replicates with component matching by absolute functional similarity. "
        + "; ".join(pieces)
        + ". Stability fractions are descriptive robustness summaries, not inferential probabilities."
    )


def registration_sensitivity_reporting_text(
    result: RegistrationSensitivityResult,
    *,
    digits: int = 2,
) -> str:
    """Generate descriptive text comparing FPC structure before/after registration."""

    similarity = np.abs(result.signed_component_similarity)
    score = result.score_correlations
    parts = []
    for k in range(len(similarity)):
        parts.append(
            f"FPC{k + 1}: matched shape similarity={similarity[k]:.{digits}f}, "
            f"score correlation={score[k]:.{digits}f}"
        )
    return (
        "Registration sensitivity compared matched functional principal components before "
        "and after the explicit registration step. "
        + "; ".join(parts)
        + "."
    )



def fpca_outlier_reporting_text(result: FunctionalOutlierResult) -> str:
    """Generate descriptive text for functional review diagnostics."""

    frame = result.diagnostics
    if "review_flag" not in frame.columns:
        raise ValueError("result diagnostics do not contain review_flag")
    n_review = int(frame["review_flag"].sum())
    return (
        f"Functional anomaly screening ({result.method}) flagged {n_review} of "
        f"{len(frame)} trajectories for review. Flags were treated as diagnostic "
        "signals only and were not used as automatic exclusion criteria."
    )


def fpca_influence_reporting_text(
    result: FPCAInfluenceResult,
    *,
    digits: int = 2,
) -> str:
    """Generate descriptive text for leave-one-group-out FPCA influence."""

    if result.summary.empty:
        raise ValueError("influence summary is empty")
    row = result.summary.loc[result.summary["influence_score"].idxmax()]
    unit = result.group_column or "curve_id"
    return (
        f"Leave-one-{unit}-out FPCA influence analysis evaluated "
        f"{len(result.summary)} omission fits. The largest observed influence "
        f"was for {row['group']!r}, with minimum matched component similarity "
        f"{row['min_abs_component_similarity']:.{digits}f}. Influence diagnostics "
        "were used for sensitivity assessment rather than automatic exclusion."
    )



def fpca_cross_validation_reporting_text(
    result: FPCACrossValidationResult,
    *,
    rule: str = "minimum",
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented text for held-out component selection."""

    summary = summarise_fpca_cross_validation(result)
    selected = select_fpca_components_cv(result, rule=rule)
    row = summary.loc[summary["n_components"] == selected].iloc[0]
    unit = "grouped" if result.cv_unit == "group" else "curve-level"
    heuristic = (
        " The one-standard-error rule was used as a parsimony heuristic."
        if rule == "one_se"
        else ""
    )
    return (
        f"FPCA component selection used {result.n_splits}-fold {unit} held-out "
        "reconstruction cross-validation, with FPCA refitted inside every "
        f"training fold. The explicit '{rule}' rule selected {selected} "
        f"component(s) (mean integrated RMSE={row['mean_rmse']:.{digits}f}, "
        f"SE={row['se_rmse']:.{digits}f}).{heuristic}"
    )


def fpca_component_envelope_reporting_text(
    result: FPCAComponentEnvelopeResult,
    *,
    digits: int = 2,
) -> str:
    """Describe matched-bootstrap FPC envelopes without confidence-band claims."""

    median_similarity = np.median(result.similarities, axis=0)
    similarity_text = ", ".join(
        f"FPC{k + 1}={value:.{digits}f}"
        for k, value in enumerate(median_similarity)
    )
    return (
        "Functional principal-component shape uncertainty was summarized with "
        f"{result.n_bootstrap} {result.resampling_unit}-level bootstrap "
        "replicates. Replicate components were matched and sign-aligned to the "
        f"full-sample reference before forming {100 * result.level:.1f}% "
        "pointwise descriptive envelopes. Median matched absolute similarities "
        f"were {similarity_text}. These envelopes are descriptive and are not "
        "simultaneous confidence bands."
    )



def fpca_component_band_reporting_text(
    result: FPCAComponentBandResult,
    *,
    digits: int = 2,
) -> str:
    """Generate manuscript-oriented wording for simultaneous FPC uncertainty bands."""

    median_similarity = np.median(result.similarities, axis=0)
    similarity_text = ", ".join(
        f"FPC{k + 1}={value:.{digits}f}"
        for k, value in enumerate(median_similarity)
    )
    scope = (
        "familywise across the requested FPCs and observed time-by-dimension grid"
        if result.simultaneous_scope == "family"
        else "component-wise across each FPC's observed time-by-dimension grid"
    )
    text = (
        "Functional principal-component shape uncertainty was evaluated with "
        f"{result.n_bootstrap} {result.resampling_unit}-level bootstrap "
        "replicates. Replicate FPCs were matched and sign-aligned to the "
        "full-sample reference, then studentized maximum absolute deviations "
        f"were calibrated at {100 * result.confidence_level:.1f}% {scope}. "
        f"Median matched absolute similarities were {similarity_text}. "
    )
    if result.relative_gap_threshold is None:
        text += (
            "No numerical near-tie threshold was imposed; component "
            "identifiability should therefore be assessed separately with "
            "eigengap and subspace diagnostics. "
        )
    else:
        minimum = ", ".join(
            f"FPC{k + 1}={gap:.{digits + 1}f}"
            for k, gap in enumerate(result.minimum_relative_gaps)
        )
        text += (
            f"The pre-specified relative-gap screen used threshold "
            f"{result.relative_gap_threshold:.{digits + 1}f} "
            f"(minimum adjacent gaps: {minimum}). "
        )
    return (
        text
        + "The band is calibrated over the observed grid and does not establish "
        "continuous-domain coverage between sampled times or substantive "
        "identifiability of a near-tied individual FPC axis."
    )


def fpca_eigengap_reporting_text(
    result: FPCAResult,
    *,
    relative_gap_threshold: float | None = None,
    digits: int = 3,
) -> str:
    """Generate descriptive text for adjacent retained FPCA eigengaps."""

    table = fpca_eigenvalue_gap_table(
        result,
        relative_gap_threshold=relative_gap_threshold,
    )
    row = table.loc[table["relative_gap"].idxmin()]
    text = (
        f"The smallest adjacent retained FPCA eigengap was between FPC"
        f"{int(row['component'])} and FPC{int(row['next_component'])} "
        f"(relative gap={row['relative_gap']:.{digits}f}; "
        f"next/current eigenvalue ratio={row['next_to_current_ratio']:.{digits}f})."
    )
    if relative_gap_threshold is not None:
        count = int(table["near_tie_flag"].sum())
        text += (
            f" Using the pre-specified relative-gap threshold "
            f"{relative_gap_threshold:.{digits}f}, {count} adjacent retained "
            "pair(s) met the descriptive near-tie criterion."
        )
    return text


def fpca_subspace_stability_reporting_text(
    result: FPCASubspaceStabilityResult,
    *,
    digits: int = 3,
) -> str:
    """Generate descriptive text for bootstrap FPCA eigenspace stability."""

    summary = summarise_fpca_subspace_stability(result)
    row = summary.iloc[0]
    start = int(row["component_start"])
    end = int(row["component_end"])
    return (
        f"Bootstrap FPCA subspace stability evaluated FPC{start}–FPC{end} using "
        f"{result.n_bootstrap} {result.resampling_unit}-level resamples. The "
        f"median minimum principal cosine was "
        f"{row['median_min_principal_cosine']:.{digits}f}, the median maximum "
        f"principal angle was {row['median_max_principal_angle_degrees']:.{digits}f} "
        f"degrees, and the median normalized projector distance was "
        f"{row['median_normalized_projector_distance']:.{digits}f}. These are "
        "descriptive eigenspace-stability summaries; they do not establish "
        "identifiability of individual FPC labels within the selected block."
    )



def sparse_fpca_reporting_text(
    result: SparseFPCAResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented wording for sparse PACE FPCA."""

    sample_counts = result.provenance.get("sparse_fpca", {}).get("sample_counts", [])
    if sample_counts:
        sample_range = f"{min(sample_counts)}–{max(sample_counts)}"
    else:
        sample_range = "not recorded"
    eigen = ", ".join(f"{value:.{digits}f}" for value in result.eigenvalues)
    sparse = result.provenance.get("sparse_fpca", {})
    grid = sparse.get("evaluation_grid")
    if grid:
        grid_text = f"{len(grid)} points over [{grid[0]:g}, {grid[-1]:g}]"
    else:
        grid_text = "backend-default evaluation points"
    custom = bool(sparse.get("kwargs_mean") or sparse.get("kwargs_covariance"))
    custom_text = " Custom mean/covariance smoothing parameters were supplied." if custom else ""
    return (
        f"Sparse univariate FPCA was fitted to the {result.dimension!r} trajectory "
        f"dimension using FDApy's covariance-operator estimator, with "
        f"{result.fit_smoothing!r} fitting smoothness and PACE "
        f"conditional-expectation scores ({result.n_components} components; "
        f"per-curve sample-count range={sample_range}; retained eigenvalues={eigen}). "
        "No common-grid interpolation was performed before sparse FPCA. "
        f"Eigenfunctions/covariance were evaluated on {grid_text}. "
        f"PACE tolerance was {result.tolerance:g} and score smoothing was "
        f"{result.score_smoothing!r}.{custom_text}"
    )



def functional_mean_band_reporting_text(
    result: FunctionalMeanBandResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented wording for a simultaneous mean band."""

    settings = result.provenance.get("functional_mean_band", {})
    n_multiplier = settings.get("n_multiplier", "unknown")
    estimand = settings.get("estimand", "unspecified")
    return (
        f"The functional mean was estimated from {result.n_units} {result.unit}-level "
        f"inference units using estimand={estimand!r}. A "
        f"{100 * result.confidence_level:.1f}% simultaneous observed-grid band "
        f"was calibrated with a studentized Gaussian multiplier maximum using "
        f"{n_multiplier} multiplier replicates "
        f"(critical value={result.critical_value:.{digits}f}). The band is "
        "simultaneous across the observed time-by-dimension grid and does not "
        "claim continuous-domain coverage between sampled grid points."
    )



def fpca_regression_future_prediction_reporting_text(
    result: FPCARegressionPredictionIntervalResult,
    *,
    digits: int = 3,
) -> str:
    """Generate reporting text for Gaussian FPCR future-outcome intervals."""

    median_width = float(np.median(result.upper - result.lower))
    residual_sd = float(np.std(result.centered_residuals, ddof=1))
    return (
        f"Future scalar outcomes for {result.n_targets} fixed target trajectory(ies) "
        f"were summarized with {100 * result.confidence_level:.1f}% marginal "
        "Gaussian FPCR prediction intervals. The predictive distribution reused "
        f"{result.n_bootstrap} paired-bootstrap conditional-mean predictions and "
        "added independent draws from the centered empirical residual distribution "
        f"of the full-sample FPCR fit (residual SD={residual_sd:.{digits}f}; "
        f"median predictive width={median_width:.{digits}f}). Residual exchangeability "
        "and a common response-error distribution across targets are assumed. The "
        "intervals are not heteroscedasticity-robust and are not simultaneous or "
        "joint across multiple target trajectories."
    )


def fpca_regression_slope_band_reporting_text(
    result: FPCARegressionSlopeBandResult,
    *,
    digits: int = 3,
) -> str:
    """Generate reporting text for observed-grid simultaneous FPCR slope bands."""

    critical = ", ".join(
        f"{dimension}={value:.{digits}f}"
        for dimension, value in zip(
            result.regression_uncertainty.reference_fpca.dimension_names,
            result.critical_values,
            strict=True,
        )
    )
    scope = (
        "one maximum over the full observed time-by-dimension grid"
        if result.simultaneous_scope == "global"
        else "a separate maximum over observed time within each functional dimension"
    )
    return (
        f"A {100 * result.confidence_level:.1f}% observed-grid simultaneous "
        "Gaussian FPCR slope band was calibrated from the retained paired "
        f"bootstrap slope refits using {scope}. Studentized maximum-deviation "
        f"critical value(s) were {critical}. The band is simultaneous only over "
        "the sampled grid represented in the fit and does not claim coverage "
        "between grid points. This calibration reuses the 0.12 paired-bootstrap "
        "FPCR distribution and is not the operator-scaled FPCR significance "
        "test developed in recent asymptotic theory."
    )


def fpca_regression_uncertainty_reporting_text(
    result: FPCARegressionUncertaintyResult,
    *,
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented wording for Gaussian FPCR bootstrap uncertainty."""

    slope_width = float(np.median(result.slope_upper - result.slope_lower))
    prediction_width = float(
        np.median(result.prediction_upper - result.prediction_lower)
    )
    unit = (
        "participant"
        if result.resampling_unit == "participant"
        else "curve"
    )
    return (
        "Gaussian scalar-on-function FPCR uncertainty was evaluated with "
        f"{result.n_bootstrap} paired {unit}-level bootstrap refits. FPCA/MFPCA "
        f"and the score regression were refitted in every replicate using "
        f"{result.n_components} fixed component(s) and scaling={result.scaling!r}. "
        f"Pointwise {100 * result.level:.1f}% percentile envelopes were formed "
        "for the reconstructed functional slope in the original trajectory "
        f"units (median grid-point width={slope_width:.{digits}f}). Fixed-target "
        "response intervals summarize uncertainty in the fitted conditional "
        f"mean (median width={prediction_width:.{digits}f}); they are not "
        "prediction intervals for future noisy outcomes. Component count was "
        "not reselected inside bootstrap replicates, and this routine does not "
        "implement the operator-scaled FPCR hypothesis test from recent theory."
    )


def fpca_regression_cv_reporting_text(
    result: FPCARegressionCVResult,
    *,
    rule: str = "minimum",
    digits: int = 3,
) -> str:
    """Generate manuscript-oriented text for outcome-tuned FPC selection."""

    summary = summarise_fpca_regression_cv(result)
    selected = select_fpca_regression_components(result, rule=rule)
    row = summary.loc[summary["n_components"] == selected].iloc[0]
    unit = "grouped" if result.cv_unit == "group" else "curve-level"
    heuristic = (
        " The one-standard-error rule was used as a parsimony heuristic."
        if rule == "one_se"
        else ""
    )
    return (
        f"Outcome-tuned FPCA regression used {result.n_splits}-fold {unit} "
        f"cross-validation with family={result.family!r} and held-out "
        f"{result.loss}. FPCA and the scalar regression were refitted inside "
        f"every training fold. The explicit {rule!r} rule selected {selected} "
        f"component(s) (mean held-out loss={row['mean_loss']:.{digits}f}, "
        f"SE={row['se_loss']:.{digits}f}).{heuristic}"
    )


def fpca_nested_regression_cv_reporting_text(
    result: FPCANestedRegressionCVResult,
    *,
    digits: int = 3,
) -> str:
    """Describe nested predictive performance after inner FPC-count selection."""

    mean_loss = float(result.outer_folds["loss"].mean())
    sd_loss = float(result.outer_folds["loss"].std(ddof=1))
    counts = result.outer_folds["selected_n_components"].astype(int)
    selected_text = ", ".join(
        f"{int(component)}×{int((counts == component).sum())}"
        for component in sorted(counts.unique())
    )
    unit = "grouped" if result.cv_unit == "group" else "curve-level"
    return (
        f"Nested FPCA regression used {result.outer_splits} outer and "
        f"{result.inner_splits} inner {unit} folds. Inner folds selected the "
        f"retained FPC count using the {result.selection_rule!r} rule; outer "
        f"folds were untouched by selection. Mean outer held-out {result.loss} "
        f"was {mean_loss:.{digits}f} (SD={sd_loss:.{digits}f}). Selected "
        f"component counts across outer fits were {selected_text}. This outer "
        "loss estimates the complete selection-and-fit pipeline rather than "
        "reusing the inner selection loss as performance evidence."
    )


def conformal_fpca_anomaly_reporting_text(
    result: ConformalFunctionalAnomalyResult,
    *,
    digits: int = 3,
) -> str:
    """Generate reporting text for split-conformal FPCA anomaly review."""

    flagged = int(np.count_nonzero(result.review_flags))
    covariance = (
        ""
        if result.mahalanobis_covariance is None
        else f" using {result.mahalanobis_covariance} score covariance"
    )
    return (
        f"Split-conformal functional anomaly review fitted an FPCA reference with "
        f"{result.n_components} component(s) on the proper-training set and used "
        f"{result.n_calibration} calibration trajectory(ies). Nonconformity was "
        f"{result.nonconformity}{covariance}. Marginal conformal p-values used the "
        "conservative greater-than-or-equal tie rule; the minimum attainable "
        f"p-value was {result.minimum_attainable_p:.{digits}f}. At alpha="
        f"{result.alpha:.{digits}f}, {flagged} of {result.n_targets} target "
        "trajectory(ies) were flagged for review. Flags are not automatic "
        "exclusions. The marginal conformal interpretation requires curve-level "
        "exchangeability of inlier trajectories. No calibration-conditional "
        "adjustment, multiple-testing correction, or FDR guarantee was applied."
    )
