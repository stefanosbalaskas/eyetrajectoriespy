"""Bootstrap-calibrated simultaneous uncertainty bands for FPC functions."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .stability import (
    _bootstrap_curves,
    _bootstrap_participants,
    _fit_for_trajectories,
    match_fpca_components,
)
from .types import FPCAComponentBandResult, TrajectorySet
from .validation import validate_trajectory_set


def _minimum_adjacent_relative_gaps(
    trajectories: TrajectorySet,
    *,
    n_components: int,
    scaling: str,
) -> np.ndarray:
    """Return each retained FPC's smallest adjacent relative eigengap."""

    feature_count = trajectories.n_time * trajectories.n_dimensions
    max_nonzero_rank = min(trajectories.n_curves - 1, feature_count)
    if n_components + 1 > max_nonzero_rank:
        raise ValueError(
            "relative eigengap screening requires one additional non-zero-rank "
            "component beyond n_components; reduce n_components or omit "
            "relative_gap_threshold"
        )

    screen = _fit_for_trajectories(
        trajectories,
        n_components=n_components + 1,
        scaling=scaling,
    )
    eigenvalues = np.asarray(screen.explained_variance, dtype=float)
    eps = np.finfo(float).eps
    minimum = np.empty(n_components, dtype=float)

    for component in range(n_components):
        gaps: list[float] = []
        if component > 0:
            previous = eigenvalues[component - 1]
            current = eigenvalues[component]
            gaps.append(float((previous - current) / max(previous, eps)))
        current = eigenvalues[component]
        following = eigenvalues[component + 1]
        gaps.append(float((current - following) / max(current, eps)))
        minimum[component] = min(gaps)
    return minimum


def bootstrap_fpca_component_bands(
    trajectories: TrajectorySet,
    *,
    n_bootstrap: int = 500,
    n_components: int = 3,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "component",
    relative_gap_threshold: float | None = None,
    on_near_tie: str = "error",
    random_state: int | None = 0,
) -> FPCAComponentBandResult:
    """Estimate matched-bootstrap simultaneous bands for individual FPC shapes.

    Bootstrap FPCs are matched to the full-sample reference by maximum absolute
    functional similarity and sign-aligned before uncertainty is calibrated.
    Pointwise bootstrap standard errors are combined with a studentized maximum
    absolute deviation over the observed time-by-dimension grid.

    Component scope calibrates each FPC separately across its full observed
    grid. Family scope uses a single maximum across all requested FPCs and the
    grid, providing a more conservative familywise band.

    Because individual eigenfunctions can be weakly identified when adjacent
    eigenvalues are close, relative_gap_threshold optionally performs an
    explicit descriptive identifiability screen. No universal threshold is
    imposed by default. If supplied, on_near_tie controls whether a retained
    FPC meeting the threshold raises, warns, or is recorded only.

    These are bootstrap-calibrated simultaneous uncertainty bands over the
    observed grid. They do not assert exact finite-sample coverage or coverage
    between sampled time points.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, (int, np.integer)):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 20:
        raise ValueError("n_bootstrap must be at least 20")
    if isinstance(n_components, bool) or not isinstance(n_components, (int, np.integer)):
        raise TypeError("n_components must be an integer")
    n_components = int(n_components)
    max_nonzero_rank = min(
        trajectories.n_curves - 1,
        trajectories.n_time * trajectories.n_dimensions,
    )
    if n_components < 1 or n_components > max_nonzero_rank:
        raise ValueError(
            f"n_components must be in [1, {max_nonzero_rank}] for non-zero-rank FPCA"
        )
    if resample_unit not in {"curve", "participant"}:
        raise ValueError("resample_unit must be 'curve' or 'participant'")
    if resample_unit == "participant" and not participant_column:
        raise ValueError("participant_column is required for participant bootstrap")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"component", "family"}:
        raise ValueError("simultaneous_scope must be 'component' or 'family'")
    if on_near_tie not in {"error", "warn", "ignore"}:
        raise ValueError("on_near_tie must be 'error', 'warn', or 'ignore'")

    if relative_gap_threshold is not None:
        if isinstance(relative_gap_threshold, bool):
            raise TypeError("relative_gap_threshold must be numeric or None")
        relative_gap_threshold = float(relative_gap_threshold)
        if not 0 <= relative_gap_threshold < 1:
            raise ValueError("relative_gap_threshold must be in [0, 1)")
        minimum_relative_gaps = _minimum_adjacent_relative_gaps(
            trajectories,
            n_components=n_components,
            scaling=scaling,
        )
        near_tie_components = np.flatnonzero(
            minimum_relative_gaps <= relative_gap_threshold
        )
        if len(near_tie_components):
            labels = [int(index + 1) for index in near_tie_components]
            message = (
                "individual FPC simultaneous bands are weakly identified under "
                f"the supplied relative-gap threshold for component(s) {labels}; "
                "inspect eigenspace/subspace stability before interpreting axes"
            )
            if on_near_tie == "error":
                raise ValueError(message)
            if on_near_tie == "warn":
                warnings.warn(message, RuntimeWarning, stacklevel=2)
    else:
        minimum_relative_gaps = np.full(n_components, np.nan, dtype=float)
        near_tie_components = np.array([], dtype=int)

    reference = _fit_for_trajectories(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    rng = np.random.default_rng(random_state)
    samples = np.empty(
        (
            n_bootstrap,
            n_components,
            trajectories.n_time,
            trajectories.n_dimensions,
        ),
        dtype=float,
    )
    similarities = np.empty((n_bootstrap, n_components), dtype=float)

    for bootstrap_index in range(n_bootstrap):
        if resample_unit == "curve":
            sample = _bootstrap_curves(trajectories, rng)
        else:
            sample = _bootstrap_participants(
                trajectories,
                rng,
                participant_column=str(participant_column),
            )

        candidate = _fit_for_trajectories(
            sample,
            n_components=n_components,
            scaling=scaling,
        )
        assignments, signed_similarity = match_fpca_components(
            reference,
            candidate,
            n_components=n_components,
        )
        similarities[bootstrap_index] = np.abs(signed_similarity)
        for component, matched in enumerate(assignments):
            sign = 1.0 if signed_similarity[component] >= 0 else -1.0
            samples[bootstrap_index, component] = sign * candidate.components[matched]

    pointwise_se = np.std(samples, axis=0, ddof=1)
    deviations = samples - reference.components[None, :, :, :]
    positive_variance = pointwise_se > np.finfo(float).eps
    reference_scale = max(1.0, float(np.max(np.abs(reference.components))))
    zero_tolerance = 100.0 * np.finfo(float).eps * reference_scale
    degenerate_discrepancy = (~positive_variance) & (
        np.max(np.abs(deviations), axis=0) > zero_tolerance
    )
    if np.any(degenerate_discrepancy):
        raise RuntimeError(
            "bootstrap component uncertainty is degenerate at a zero-variance "
            "grid cell with non-zero reference discrepancy"
        )

    standardized = np.zeros_like(deviations)
    np.divide(
        deviations,
        pointwise_se[None, :, :, :],
        out=standardized,
        where=positive_variance[None, :, :, :],
    )
    max_statistics = np.max(np.abs(standardized), axis=(2, 3))

    if simultaneous_scope == "component":
        critical_values = np.quantile(
            max_statistics,
            confidence_level,
            axis=0,
            method="higher",
        )
    else:
        critical = float(
            np.quantile(
                np.max(max_statistics, axis=1),
                confidence_level,
                method="higher",
            )
        )
        critical_values = np.full(n_components, critical, dtype=float)

    half_width = critical_values[:, None, None] * pointwise_se
    lower = reference.components - half_width
    upper = reference.components + half_width

    return FPCAComponentBandResult(
        reference=reference,
        lower=lower,
        upper=upper,
        pointwise_se=pointwise_se,
        critical_values=np.asarray(critical_values, dtype=float),
        max_statistics=max_statistics,
        similarities=similarities,
        confidence_level=float(confidence_level),
        simultaneous_scope=simultaneous_scope,
        resampling_unit=resample_unit,
        participant_column=(
            participant_column if resample_unit == "participant" else None
        ),
        relative_gap_threshold=relative_gap_threshold,
        minimum_relative_gaps=minimum_relative_gaps,
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_component_band": {
                "method": "matched_sign_aligned_bootstrap_studentized_maximum",
                "n_bootstrap": n_bootstrap,
                "n_components": n_components,
                "scaling": scaling,
                "confidence_level": float(confidence_level),
                "simultaneous_scope": simultaneous_scope,
                "resample_unit": resample_unit,
                "participant_column": (
                    participant_column if resample_unit == "participant" else None
                ),
                "random_state": random_state,
                "simultaneous_domain": "observed_time_by_dimension_grid",
                "continuous_between_grid_points": False,
                "relative_gap_threshold": relative_gap_threshold,
                "on_near_tie": on_near_tie,
                "near_tie_components": [
                    int(index + 1) for index in near_tie_components
                ],
                "component_identity_screened": relative_gap_threshold is not None,
                "coverage_claim": "bootstrap_calibrated_observed_grid_approximation",
            },
        },
    )


def fpca_component_band_frame(
    result: FPCAComponentBandResult,
) -> pd.DataFrame:
    """Return long-form values for simultaneous FPC uncertainty bands."""

    rows: list[dict[str, float | int | str]] = []
    for component in range(result.n_components):
        for dimension, name in enumerate(result.reference.dimension_names):
            for index, time in enumerate(result.reference.time):
                rows.append(
                    {
                        "component": component + 1,
                        "time": float(time),
                        "dimension": name,
                        "reference": float(
                            result.reference.components[component, index, dimension]
                        ),
                        "pointwise_se": float(
                            result.pointwise_se[component, index, dimension]
                        ),
                        "lower": float(result.lower[component, index, dimension]),
                        "upper": float(result.upper[component, index, dimension]),
                    }
                )
    return pd.DataFrame(rows)
