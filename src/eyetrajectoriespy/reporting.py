"""Concise reporting helpers for functional gaze analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .selection import select_fpca_components_cv, summarise_fpca_cross_validation
from .subspace import fpca_eigenvalue_gap_table, summarise_fpca_subspace_stability
from .types import (
    FPCAComponentEnvelopeResult,
    FPCACrossValidationResult,
    FPCAInfluenceResult,
    FPCAResult,
    FPCAStabilityResult,
    FPCASubspaceStabilityResult,
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
    return (
        f"Sparse univariate FPCA was fitted to the {result.dimension!r} trajectory "
        f"dimension using FDApy's covariance-operator estimator, with "
        f"{result.fit_smoothing!r} fitting smoothness and PACE "
        f"conditional-expectation scores ({result.n_components} components; "
        f"per-curve sample-count range={sample_range}; retained eigenvalues={eigen}). "
        "No common-grid interpolation was performed before sparse FPCA. "
        f"PACE tolerance was {result.tolerance:g} and score smoothing was "
        f"{result.score_smoothing!r}."
    )
