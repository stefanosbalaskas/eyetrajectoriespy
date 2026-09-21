"""Bootstrap uncertainty for FPCA eigenvalues and explained-variance spectra."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stability import (
    _bootstrap_curves,
    _bootstrap_participants,
    _fit_for_trajectories,
    match_fpca_components,
)
from .types import FPCASpectrumUncertaintyResult, TrajectorySet
from .validation import validate_trajectory_set


def _calibrate_spectrum_metric(
    samples: np.ndarray,
    reference: np.ndarray,
    *,
    confidence_level: float,
    simultaneous_scope: str,
    metric_name: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Studentize bootstrap deviations and calibrate component/family maxima."""

    samples = np.asarray(samples, dtype=float)
    reference = np.asarray(reference, dtype=float)
    if samples.ndim != 2 or reference.ndim != 1 or samples.shape[1] != reference.size:
        raise ValueError("spectrum calibration arrays have incompatible shapes")
    if not np.all(np.isfinite(samples)) or not np.all(np.isfinite(reference)):
        raise ValueError(f"{metric_name} samples/reference must be finite")

    standard_error = np.std(samples, axis=0, ddof=1)
    scale = max(1.0, float(np.max(np.abs(reference))))
    positive_variance = standard_error > np.finfo(float).eps * scale
    deviations = samples - reference[None, :]
    tolerance = 100.0 * np.finfo(float).eps * scale

    degenerate = (~positive_variance) & (
        np.max(np.abs(deviations), axis=0) > tolerance
    )
    if np.any(degenerate):
        components = [int(i + 1) for i in np.flatnonzero(degenerate)]
        raise RuntimeError(
            f"{metric_name} bootstrap uncertainty is degenerate for component(s) "
            f"{components}: zero bootstrap SE with non-zero reference discrepancy"
        )

    standardized = np.zeros_like(deviations)
    np.divide(
        deviations,
        standard_error[None, :],
        out=standardized,
        where=positive_variance[None, :],
    )
    absolute_statistics = np.abs(standardized)

    if simultaneous_scope == "component":
        critical_values = np.quantile(
            absolute_statistics,
            confidence_level,
            axis=0,
            method="higher",
        )
    else:
        critical = float(
            np.quantile(
                np.max(absolute_statistics, axis=1),
                confidence_level,
                method="higher",
            )
        )
        critical_values = np.full(reference.size, critical, dtype=float)

    half_width = critical_values * standard_error
    return (
        standard_error,
        np.asarray(critical_values, dtype=float),
        reference - half_width,
        reference + half_width,
        absolute_statistics,
    )


def bootstrap_fpca_spectrum_uncertainty(
    trajectories: TrajectorySet,
    *,
    n_bootstrap: int = 500,
    n_components: int = 3,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    confidence_level: float = 0.95,
    simultaneous_scope: str = "component",
    random_state: int | None = 0,
) -> FPCASpectrumUncertaintyResult:
    """Bootstrap uncertainty for matched FPCA eigenvalues and variance ratios.

    Bootstrap FPCs are matched to the full-sample reference by maximum absolute
    functional similarity before eigenvalues and explained-variance ratios are
    attached to reference component identities.

    Component scope calibrates each component separately. Family scope controls
    the maximum across all requested components within each spectrum metric:
    eigenvalue, explained-variance ratio, or cumulative explained variance.
    It is not a joint guarantee across the three different metrics.

    Intervals are symmetric studentized bootstrap approximations around the
    full-sample estimate. They are not clipped to parameter support, so a finite
    sample interval may extend below zero or outside [0, 1].
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
    if resample_unit == "curve" and participant_column is not None:
        raise ValueError(
            "participant_column must be None when resample_unit='curve'"
        )
    if resample_unit == "participant" and not participant_column:
        raise ValueError(
            "participant_column is required when resample_unit='participant'"
        )
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie in (0, 1)")
    if simultaneous_scope not in {"component", "family"}:
        raise ValueError("simultaneous_scope must be 'component' or 'family'")

    reference = _fit_for_trajectories(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    reference_eigenvalues = np.asarray(
        reference.explained_variance[:n_components],
        dtype=float,
    )
    reference_ratios = np.asarray(
        reference.explained_variance_ratio[:n_components],
        dtype=float,
    )
    reference_cumulative = np.cumsum(reference_ratios)

    rng = np.random.default_rng(random_state)
    eigenvalues = np.empty((n_bootstrap, n_components), dtype=float)
    ratios = np.empty_like(eigenvalues)
    assignments = np.empty((n_bootstrap, n_components), dtype=int)
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
        if sample.n_curves <= n_components:
            raise ValueError(
                f"bootstrap replicate {bootstrap_index} has too few curves for "
                f"{n_components} non-zero-rank components"
            )

        candidate = _fit_for_trajectories(
            sample,
            n_components=n_components,
            scaling=scaling,
        )
        matched, signed_similarity = match_fpca_components(
            reference,
            candidate,
            n_components=n_components,
        )
        assignments[bootstrap_index] = matched
        similarities[bootstrap_index] = np.abs(signed_similarity)
        eigenvalues[bootstrap_index] = candidate.explained_variance[matched]
        ratios[bootstrap_index] = candidate.explained_variance_ratio[matched]

        # Cumulative explained variance retains its conventional descending-rank
        # meaning. It is intentionally not reordered by component-shape matching.
        # This keeps "top k components explain ..." invariant to within-block
        # swaps of near-tied eigenfunctions.
        if bootstrap_index == 0:
            cumulative = np.empty((n_bootstrap, n_components), dtype=float)
        cumulative[bootstrap_index] = np.cumsum(
            candidate.explained_variance_ratio[:n_components]
        )

    eig_se, eig_crit, eig_lower, eig_upper, eig_stats = _calibrate_spectrum_metric(
        eigenvalues,
        reference_eigenvalues,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
        metric_name="eigenvalue",
    )
    ratio_se, ratio_crit, ratio_lower, ratio_upper, ratio_stats = (
        _calibrate_spectrum_metric(
            ratios,
            reference_ratios,
            confidence_level=confidence_level,
            simultaneous_scope=simultaneous_scope,
            metric_name="explained_variance_ratio",
        )
    )
    cum_se, cum_crit, cum_lower, cum_upper, cum_stats = _calibrate_spectrum_metric(
        cumulative,
        reference_cumulative,
        confidence_level=confidence_level,
        simultaneous_scope=simultaneous_scope,
        metric_name="cumulative_explained_variance_ratio",
    )

    return FPCASpectrumUncertaintyResult(
        reference=reference,
        bootstrap_eigenvalues=eigenvalues,
        bootstrap_explained_variance_ratio=ratios,
        bootstrap_cumulative_variance_ratio=cumulative,
        eigenvalue_se=eig_se,
        eigenvalue_critical_values=eig_crit,
        eigenvalue_lower=eig_lower,
        eigenvalue_upper=eig_upper,
        eigenvalue_max_statistics=eig_stats,
        explained_variance_ratio_se=ratio_se,
        explained_variance_ratio_critical_values=ratio_crit,
        explained_variance_ratio_lower=ratio_lower,
        explained_variance_ratio_upper=ratio_upper,
        explained_variance_ratio_max_statistics=ratio_stats,
        cumulative_variance_ratio_se=cum_se,
        cumulative_variance_ratio_critical_values=cum_crit,
        cumulative_variance_ratio_lower=cum_lower,
        cumulative_variance_ratio_upper=cum_upper,
        cumulative_variance_ratio_max_statistics=cum_stats,
        assignments=assignments,
        similarities=similarities,
        confidence_level=float(confidence_level),
        simultaneous_scope=simultaneous_scope,
        resampling_unit=resample_unit,
        participant_column=(
            participant_column if resample_unit == "participant" else None
        ),
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_spectrum_uncertainty": {
                "method": "matched_bootstrap_studentized_spectrum",
                "n_bootstrap": n_bootstrap,
                "n_components": n_components,
                "scaling": scaling,
                "confidence_level": float(confidence_level),
                "simultaneous_scope": simultaneous_scope,
                "familywise_domain": (
                    "requested_components_within_each_metric"
                    if simultaneous_scope == "family"
                    else "one_component_within_each_metric"
                ),
                "joint_across_metrics": False,
                "resample_unit": resample_unit,
                "participant_column": (
                    participant_column if resample_unit == "participant" else None
                ),
                "random_state": random_state,
                "component_matching": "maximum_absolute_functional_similarity",
                "individual_spectrum_order": "matched_reference_component_identity",
                "cumulative_spectrum_order": "descending_eigenvalue_rank",
                "support_clipping": False,
                "coverage_claim": "bootstrap_studentized_approximation",
            },
        },
    )


def fpca_spectrum_uncertainty_frame(
    result: FPCASpectrumUncertaintyResult,
) -> pd.DataFrame:
    """Return component-level FPCA spectrum estimates and uncertainty intervals."""

    reference = result.reference
    n = result.n_components
    return pd.DataFrame(
        {
            "component": np.arange(1, n + 1),
            "eigenvalue": reference.explained_variance[:n],
            "eigenvalue_se": result.eigenvalue_se,
            "eigenvalue_lower": result.eigenvalue_lower,
            "eigenvalue_upper": result.eigenvalue_upper,
            "explained_variance_ratio": reference.explained_variance_ratio[:n],
            "explained_variance_ratio_se": result.explained_variance_ratio_se,
            "explained_variance_ratio_lower": result.explained_variance_ratio_lower,
            "explained_variance_ratio_upper": result.explained_variance_ratio_upper,
            "cumulative_variance_ratio": np.cumsum(
                reference.explained_variance_ratio[:n]
            ),
            "cumulative_variance_ratio_se": result.cumulative_variance_ratio_se,
            "cumulative_variance_ratio_lower": result.cumulative_variance_ratio_lower,
            "cumulative_variance_ratio_upper": result.cumulative_variance_ratio_upper,
            "median_matched_abs_similarity": np.median(
                result.similarities,
                axis=0,
            ),
        }
    )
