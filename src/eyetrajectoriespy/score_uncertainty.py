"""Basis-resampling uncertainty for FPCA score projections."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fpca import transform_fpca
from .stability import (
    _bootstrap_curves,
    _bootstrap_participants,
    _fit_for_trajectories,
    match_fpca_components,
)
from .types import FPCAScoreUncertaintyResult, TrajectorySet
from .validation import validate_trajectory_set


def _validate_score_targets(
    training: TrajectorySet,
    targets: TrajectorySet,
) -> None:
    """Require targets to share the fitted functional representation exactly."""

    validate_trajectory_set(targets, require_complete=True)
    if not np.all(np.isfinite(targets.values)):
        raise ValueError("targets must contain only finite values")
    if targets.n_curves < 1:
        raise ValueError("targets must contain at least one trajectory")
    if not np.array_equal(training.time, targets.time):
        raise ValueError("targets must use the exact training time grid")
    if training.dimension_names != targets.dimension_names:
        raise ValueError(
            "targets must use the same functional dimension names and order"
        )
    if training.coordinate_system != targets.coordinate_system:
        raise ValueError("targets must use the same coordinate_system as training")
    if training.time_unit != targets.time_unit:
        raise ValueError("targets must use the same time_unit as training")


def bootstrap_fpca_score_uncertainty(
    trajectories: TrajectorySet,
    *,
    targets: TrajectorySet | None = None,
    n_bootstrap: int = 500,
    n_components: int = 3,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    level: float = 0.95,
    random_state: int | None = 0,
) -> FPCAScoreUncertaintyResult:
    """Quantify FPC score sensitivity to re-estimation of the FPCA basis.

    The training trajectories are resampled and FPCA is refitted in every
    bootstrap replicate. Bootstrap FPCs are matched to the full-sample
    reference by maximum absolute functional similarity and sign-aligned.
    Fixed target trajectories are then projected into each aligned bootstrap
    basis.

    The returned percentile envelopes quantify *basis-resampling uncertainty*
    for fixed target curves. They do not include target measurement error,
    uncertainty about a latent target trajectory, conditional PACE score
    uncertainty, future-curve sampling variability, or uncertainty from
    preprocessing decisions. They are descriptive bootstrap uncertainty
    summaries rather than exact finite-sample confidence intervals.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.all(np.isfinite(trajectories.values)):
        raise ValueError("training trajectories must contain only finite values")
    if targets is None:
        target_set = trajectories
        target_source = "training"
    else:
        target_set = targets
        target_source = "external"
        _validate_score_targets(trajectories, target_set)

    if isinstance(n_bootstrap, bool) or not isinstance(
        n_bootstrap, (int, np.integer)
    ):
        raise TypeError("n_bootstrap must be an integer")
    n_bootstrap = int(n_bootstrap)
    if n_bootstrap < 20:
        raise ValueError("n_bootstrap must be at least 20")

    if isinstance(n_components, bool) or not isinstance(
        n_components, (int, np.integer)
    ):
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
    if not 0 < level < 1:
        raise ValueError("level must lie in (0, 1)")

    reference = _fit_for_trajectories(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    reference_scores = transform_fpca(reference, target_set)[:, :n_components]

    rng = np.random.default_rng(random_state)
    bootstrap_scores = np.empty(
        (n_bootstrap, target_set.n_curves, n_components),
        dtype=float,
    )
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

        candidate_scores = transform_fpca(candidate, target_set)
        orientation = np.where(signed_similarity >= 0.0, 1.0, -1.0)
        aligned_scores = candidate_scores[:, matched] * orientation[None, :]
        if not np.all(np.isfinite(aligned_scores)):
            raise RuntimeError(
                f"bootstrap replicate {bootstrap_index} produced non-finite target scores"
            )
        bootstrap_scores[bootstrap_index] = aligned_scores

    alpha = (1.0 - float(level)) / 2.0
    lower = np.quantile(bootstrap_scores, alpha, axis=0)
    median = np.quantile(bootstrap_scores, 0.5, axis=0)
    upper = np.quantile(bootstrap_scores, 1.0 - alpha, axis=0)
    score_se = np.std(bootstrap_scores, axis=0, ddof=1)

    return FPCAScoreUncertaintyResult(
        reference=reference,
        target_curve_ids=target_set.curve_ids,
        reference_scores=reference_scores,
        bootstrap_scores=bootstrap_scores,
        lower=lower,
        median=median,
        upper=upper,
        score_se=score_se,
        assignments=assignments,
        similarities=similarities,
        level=float(level),
        resampling_unit=resample_unit,
        participant_column=(
            participant_column if resample_unit == "participant" else None
        ),
        target_source=target_source,
        random_state=random_state,
        provenance={
            **dict(trajectories.provenance),
            "fpca_score_uncertainty": {
                "method": "matched_sign_aligned_basis_resampling",
                "interval": "pointwise_percentile_descriptive",
                "n_bootstrap": n_bootstrap,
                "n_components": n_components,
                "scaling": scaling,
                "level": float(level),
                "resample_unit": resample_unit,
                "participant_column": (
                    participant_column if resample_unit == "participant" else None
                ),
                "target_source": target_source,
                "target_curves_fixed": True,
                "component_matching": "maximum_absolute_functional_similarity",
                "sign_alignment": True,
                "includes_basis_estimation_uncertainty": True,
                "includes_target_measurement_error": False,
                "includes_latent_target_curve_uncertainty": False,
                "includes_future_curve_sampling_variability": False,
                "includes_preprocessing_uncertainty": False,
                "full_downstream_uncertainty_propagation": False,
                "random_state": random_state,
            },
        },
    )


def fpca_score_uncertainty_frame(
    result: FPCAScoreUncertaintyResult,
) -> pd.DataFrame:
    """Return tidy fixed-target score uncertainty summaries."""

    rows: list[dict[str, float | int | str]] = []
    median_similarity = np.median(result.similarities, axis=0)
    for target_index, curve_id in enumerate(result.target_curve_ids):
        for component in range(result.n_components):
            rows.append(
                {
                    "curve_id": curve_id,
                    "component": component + 1,
                    "reference_score": float(
                        result.reference_scores[target_index, component]
                    ),
                    "bootstrap_median": float(
                        result.median[target_index, component]
                    ),
                    "bootstrap_se": float(
                        result.score_se[target_index, component]
                    ),
                    "lower": float(result.lower[target_index, component]),
                    "upper": float(result.upper[target_index, component]),
                    "median_matched_abs_similarity": float(
                        median_similarity[component]
                    ),
                }
            )
    return pd.DataFrame(rows)
