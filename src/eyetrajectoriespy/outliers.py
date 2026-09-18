"""Functional outlier screening and FPCA influence diagnostics.

These routines are diagnostic by design. They never remove trajectories or
convert review flags into exclusions automatically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.covariance import EmpiricalCovariance, MinCovDet

from .fpca import fit_fpca, fit_mfpca
from .stability import match_fpca_components, reconstruction_error_by_curve
from .types import (
    FPCAInfluenceResult,
    FPCAResult,
    FunctionalOutlierResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


_NORMAL_MAD_CONSTANT = 0.6744897501960817


def _resolve_component_count(result: FPCAResult, n_components: int | None) -> int:
    if n_components is None:
        return result.n_components
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer or None")
    if n_components < 1 or n_components > result.n_components:
        raise ValueError("n_components is outside the fitted FPCA range")
    return n_components


def _validate_fitted_sample(result: FPCAResult, trajectories: TrajectorySet) -> None:
    validate_trajectory_set(trajectories, require_complete=True)
    if result.curve_ids != trajectories.curve_ids:
        raise ValueError("Trajectory IDs/order must match the fitted FPCA result")
    if not np.array_equal(result.time, trajectories.time):
        raise ValueError("Trajectory grid must match the fitted FPCA result")
    if result.dimension_names != trajectories.dimension_names:
        raise ValueError("Functional dimensions must match the fitted FPCA result")


def _robust_upper_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad <= np.finfo(float).eps:
        if np.allclose(values, median):
            return np.zeros_like(values)
        raise ValueError(
            "Median absolute deviation is zero; a robust reconstruction threshold "
            "cannot be defined for these values"
        )
    return _NORMAL_MAD_CONSTANT * (values - median) / mad


def diagnose_fpca_outliers(
    result: FPCAResult,
    trajectories: TrajectorySet,
    *,
    n_components: int | None = None,
    reconstruction_z_threshold: float = 3.5,
    score_alpha: float = 0.99,
    score_covariance: str = "robust",
    random_state: int | None = 0,
) -> FunctionalOutlierResult:
    """Screen fitted trajectories using reconstruction and FPCA-score diagnostics.

    Review flags are diagnostics only. The package never removes flagged
    trajectories automatically.
    """

    _validate_fitted_sample(result, trajectories)
    k = _resolve_component_count(result, n_components)
    if reconstruction_z_threshold <= 0:
        raise ValueError("reconstruction_z_threshold must be positive")
    if not 0 < score_alpha < 1:
        raise ValueError("score_alpha must lie in (0, 1)")
    if score_covariance not in {"robust", "empirical"}:
        raise ValueError("score_covariance must be 'robust' or 'empirical'")

    reconstruction = reconstruction_error_by_curve(
        result,
        trajectories,
        n_components=k,
    )
    reconstruction_error = reconstruction["integrated_rmse"].to_numpy(dtype=float)
    reconstruction_z = _robust_upper_z(reconstruction_error)

    scores = np.asarray(result.scores[:, :k], dtype=float)
    if score_covariance == "robust":
        if trajectories.n_curves <= 2 * k:
            raise ValueError(
                "Robust score covariance requires more than 2 * n_components trajectories"
            )
        try:
            covariance = MinCovDet(random_state=random_state).fit(scores)
        except Exception as exc:
            raise ValueError(
                "Robust covariance estimation failed; reduce n_components, inspect "
                "score degeneracy, or request score_covariance='empirical' explicitly"
            ) from exc
    else:
        if trajectories.n_curves <= k:
            raise ValueError(
                "Empirical score covariance requires more trajectories than components"
            )
        covariance = EmpiricalCovariance().fit(scores)

    mahalanobis_sq = np.asarray(covariance.mahalanobis(scores), dtype=float)
    score_cutoff = float(chi2.ppf(score_alpha, df=k))
    reconstruction_flag = reconstruction_z > reconstruction_z_threshold
    score_flag = mahalanobis_sq > score_cutoff
    review_flag = reconstruction_flag | score_flag

    diagnostics = pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "reconstruction_rmse": reconstruction_error,
            "reconstruction_robust_z": reconstruction_z,
            "score_mahalanobis_sq": mahalanobis_sq,
            "score_cutoff": score_cutoff,
            "reconstruction_flag": reconstruction_flag,
            "score_flag": score_flag,
            "review_flag": review_flag,
        }
    )
    return FunctionalOutlierResult(
        diagnostics=diagnostics,
        method="fpca_reconstruction_and_score_space",
        reference=result,
        provenance={
            "n_components": k,
            "reconstruction_z_threshold": reconstruction_z_threshold,
            "score_alpha": score_alpha,
            "score_covariance": score_covariance,
            "random_state": random_state,
            "scientific_warning": (
                "Review flags are diagnostics only. Do not exclude flagged trajectories "
                "without a pre-specified substantive or quality rule."
            ),
        },
    )


def _fit_reference(
    trajectories: TrajectorySet,
    *,
    n_components: int,
    scaling: str,
) -> FPCAResult:
    if trajectories.n_dimensions > 1:
        return fit_mfpca(
            trajectories,
            n_components=n_components,
            scaling=scaling,
        )
    return fit_fpca(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )


def leave_one_group_out_fpca_influence(
    trajectories: TrajectorySet,
    *,
    group_column: str | None = None,
    n_components: int = 3,
    scaling: str = "none",
) -> FPCAInfluenceResult:
    """Quantify how much each curve or group influences fitted FPC structure.

    When group_column is supplied, all curves belonging to one group are
    removed together. For repeated-trial eye-tracking designs this is commonly
    a participant identifier.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if n_components < 1 or n_components > trajectories.n_curves:
        raise ValueError("n_components must be between 1 and number of trajectories")

    if group_column is None:
        group_values = np.asarray(trajectories.curve_ids, dtype=object)
        groups = list(trajectories.curve_ids)
    else:
        if group_column not in trajectories.metadata.columns:
            raise ValueError(f"metadata does not contain group column {group_column!r}")
        if trajectories.metadata[group_column].isna().any():
            raise ValueError("group_column contains missing values")
        group_values = trajectories.metadata[group_column].astype(str).to_numpy()
        groups = list(pd.unique(group_values))

    reference = _fit_reference(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    summary_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []

    for group in groups:
        omitted = np.flatnonzero(group_values == group)
        keep = np.flatnonzero(group_values != group)
        if len(keep) < max(2, n_components):
            raise ValueError(
                f"Removing group {group!r} leaves too few trajectories for "
                f"{n_components} components"
            )
        candidate_data = trajectories.subset(keep)
        candidate = _fit_reference(
            candidate_data,
            n_components=n_components,
            scaling=scaling,
        )
        assignments, signed = match_fpca_components(
            reference,
            candidate,
            n_components=n_components,
        )
        abs_similarity = np.abs(signed)
        matched_evr = candidate.explained_variance_ratio[assignments]
        evr_change = matched_evr - reference.explained_variance_ratio[:n_components]

        summary_rows.append(
            {
                "group": str(group),
                "omitted_n_curves": int(len(omitted)),
                "remaining_n_curves": int(len(keep)),
                "min_abs_component_similarity": float(np.min(abs_similarity)),
                "mean_abs_component_similarity": float(np.mean(abs_similarity)),
                "max_abs_explained_variance_change": float(np.max(np.abs(evr_change))),
                "mean_abs_explained_variance_change": float(np.mean(np.abs(evr_change))),
                "influence_score": float(1.0 - np.min(abs_similarity)),
            }
        )
        for component in range(n_components):
            component_rows.append(
                {
                    "group": str(group),
                    "reference_component": component + 1,
                    "matched_component": int(assignments[component]) + 1,
                    "signed_similarity": float(signed[component]),
                    "absolute_similarity": float(abs_similarity[component]),
                    "explained_variance_change": float(evr_change[component]),
                }
            )

    return FPCAInfluenceResult(
        reference=reference,
        summary=pd.DataFrame(summary_rows),
        components=pd.DataFrame(component_rows),
        group_column=group_column,
        n_components=n_components,
        provenance={
            "method": "leave_one_group_out_fpca",
            "group_column": group_column,
            "scaling": scaling,
            "scientific_warning": (
                "Influence diagnostics quantify sensitivity to omission. They are not "
                "automatic exclusion criteria."
            ),
        },
    )
