"""Split-conformal anomaly review for common-grid functional trajectories."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.covariance import EmpiricalCovariance, MinCovDet

from .fpca import fit_fpca, fit_mfpca, reconstruct_fpca, transform_fpca
from .types import ConformalFunctionalAnomalyResult, FPCAResult, TrajectorySet
from .validation import validate_trajectory_set


def _validate_partition(
    reference: TrajectorySet,
    candidate: TrajectorySet,
    *,
    name: str,
) -> None:
    validate_trajectory_set(candidate, require_complete=True)
    if candidate.n_curves < 1:
        raise ValueError(f"{name} must contain at least one trajectory")
    if not np.all(np.isfinite(candidate.values)):
        raise ValueError(f"{name} must contain only finite trajectory values")
    if not np.array_equal(reference.time, candidate.time):
        raise ValueError(f"{name} must use the exact proper-training time grid")
    if reference.dimension_names != candidate.dimension_names:
        raise ValueError(
            f"{name} must use the same functional dimension names and order"
        )
    if reference.coordinate_system != candidate.coordinate_system:
        raise ValueError(
            f"{name} must use the same coordinate_system as proper training"
        )
    if reference.time_unit != candidate.time_unit:
        raise ValueError(f"{name} must use the same time_unit as proper training")


def _validate_disjoint_ids(
    proper_training: TrajectorySet,
    calibration: TrajectorySet,
    targets: TrajectorySet,
) -> None:
    proper_ids = set(proper_training.curve_ids)
    calibration_ids = set(calibration.curve_ids)
    target_ids = set(targets.curve_ids)
    overlaps = {
        "proper/calibration": sorted(proper_ids & calibration_ids),
        "proper/targets": sorted(proper_ids & target_ids),
        "calibration/targets": sorted(calibration_ids & target_ids),
    }
    bad = {name: values for name, values in overlaps.items() if values}
    if bad:
        raise ValueError(
            "proper-training, calibration, and target curve IDs must be disjoint; "
            f"overlaps={bad}"
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


def _reconstruction_scores(
    reference: FPCAResult,
    trajectories: TrajectorySet,
    *,
    n_components: int,
) -> np.ndarray:
    scores = transform_fpca(reference, trajectories)[:, :n_components]
    reconstructed = reconstruct_fpca(
        reference,
        scores=scores,
        n_components=n_components,
    )
    error = reconstructed - trajectories.values
    weighted_mse = np.sum(
        error**2 * reference.weights[None, :, None],
        axis=(1, 2),
    ) / (reference.weights.sum() * trajectories.n_dimensions)
    values = np.sqrt(weighted_mse)
    if not np.all(np.isfinite(values)):
        raise RuntimeError("reconstruction nonconformity contains non-finite values")
    return np.asarray(values, dtype=float)


def _fit_score_covariance(
    reference: FPCAResult,
    *,
    n_components: int,
    method: str,
    random_state: int | None,
):
    scores = np.asarray(reference.scores[:, :n_components], dtype=float)
    if method == "empirical":
        if scores.shape[0] <= n_components:
            raise ValueError(
                "empirical score covariance requires more proper-training "
                "trajectories than retained components"
            )
        estimator = EmpiricalCovariance()
    elif method == "robust":
        if scores.shape[0] <= 2 * n_components:
            raise ValueError(
                "robust score covariance requires more than 2 * n_components "
                "proper-training trajectories"
            )
        estimator = MinCovDet(random_state=random_state)
    else:
        raise ValueError(
            "mahalanobis_covariance must be 'empirical' or 'robust'"
        )
    try:
        return estimator.fit(scores)
    except Exception as exc:
        raise ValueError(
            "score covariance estimation failed; reduce n_components, inspect "
            "score degeneracy, or choose another covariance estimator explicitly"
        ) from exc


def _mahalanobis_scores(
    reference: FPCAResult,
    trajectories: TrajectorySet,
    *,
    n_components: int,
    covariance,
) -> np.ndarray:
    scores = transform_fpca(reference, trajectories)[:, :n_components]
    values = np.asarray(covariance.mahalanobis(scores), dtype=float)
    if not np.all(np.isfinite(values)):
        raise RuntimeError("score-space nonconformity contains non-finite values")
    return values


def split_conformal_fpca_anomaly(
    proper_training: TrajectorySet,
    calibration: TrajectorySet,
    targets: TrajectorySet,
    *,
    n_components: int = 3,
    scaling: str = "none",
    nonconformity: str = "reconstruction_rmse",
    mahalanobis_covariance: str | None = None,
    alpha: float = 0.05,
    random_state: int | None = 0,
) -> ConformalFunctionalAnomalyResult:
    """Compute marginal split-conformal anomaly p-values for new trajectories.

    The FPCA/MFPCA reference and any score-space covariance estimator are fitted
    on the proper-training set only. Calibration and target trajectories are
    scored without refitting the reference.

    P-values use the conservative split-conformal rule

        (1 + number of calibration scores >= target score) / (n_calibration + 1).

    Review flags are p <= alpha and are never automatic exclusions.

    The finite-sample marginal conformal interpretation requires exchangeable
    inlier trajectories at the curve level and a proper-training/calibration
    reference population appropriate for the targets. This function does not
    implement calibration-conditional adjustments or multiple-testing/FDR
    control.
    """

    validate_trajectory_set(proper_training, require_complete=True)
    if proper_training.n_curves < 2:
        raise ValueError("proper_training must contain at least two trajectories")
    if not np.all(np.isfinite(proper_training.values)):
        raise ValueError("proper_training must contain only finite trajectory values")
    _validate_partition(proper_training, calibration, name="calibration")
    _validate_partition(proper_training, targets, name="targets")
    _validate_disjoint_ids(proper_training, calibration, targets)

    if isinstance(n_components, bool) or not isinstance(
        n_components, (int, np.integer)
    ):
        raise TypeError("n_components must be an integer")
    n_components = int(n_components)
    max_nonzero_rank = min(
        proper_training.n_curves - 1,
        proper_training.n_time * proper_training.n_dimensions,
    )
    if n_components < 1 or n_components > max_nonzero_rank:
        raise ValueError(
            f"n_components must be in [1, {max_nonzero_rank}] for the "
            "proper-training non-zero FPCA rank"
        )
    if scaling not in {"none", "dimension_sd"}:
        raise ValueError("scaling must be 'none' or 'dimension_sd'")
    if nonconformity not in {"reconstruction_rmse", "score_mahalanobis"}:
        raise ValueError(
            "nonconformity must be 'reconstruction_rmse' or 'score_mahalanobis'"
        )
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    if random_state is not None and (
        isinstance(random_state, bool) or not isinstance(random_state, (int, np.integer))
    ):
        raise TypeError("random_state must be an integer or None")

    if nonconformity == "reconstruction_rmse":
        if mahalanobis_covariance is not None:
            raise ValueError(
                "mahalanobis_covariance must be None when "
                "nonconformity='reconstruction_rmse'"
            )
    elif mahalanobis_covariance not in {"empirical", "robust"}:
        raise ValueError(
            "score_mahalanobis requires explicit mahalanobis_covariance="
            "'empirical' or 'robust'"
        )

    reference = _fit_reference(
        proper_training,
        n_components=n_components,
        scaling=scaling,
    )

    if nonconformity == "reconstruction_rmse":
        calibration_scores = _reconstruction_scores(
            reference,
            calibration,
            n_components=n_components,
        )
        target_scores = _reconstruction_scores(
            reference,
            targets,
            n_components=n_components,
        )
    else:
        covariance = _fit_score_covariance(
            reference,
            n_components=n_components,
            method=str(mahalanobis_covariance),
            random_state=None if random_state is None else int(random_state),
        )
        calibration_scores = _mahalanobis_scores(
            reference,
            calibration,
            n_components=n_components,
            covariance=covariance,
        )
        target_scores = _mahalanobis_scores(
            reference,
            targets,
            n_components=n_components,
            covariance=covariance,
        )

    counts = np.sum(
        calibration_scores[None, :] >= target_scores[:, None],
        axis=1,
    )
    p_values = (1.0 + counts.astype(float)) / (calibration.n_curves + 1.0)
    review_flags = p_values <= float(alpha)
    minimum_p = 1.0 / (calibration.n_curves + 1.0)

    return ConformalFunctionalAnomalyResult(
        reference=reference,
        calibration_curve_ids=calibration.curve_ids,
        target_curve_ids=targets.curve_ids,
        calibration_scores=np.asarray(calibration_scores, dtype=float),
        target_scores=np.asarray(target_scores, dtype=float),
        p_values=np.asarray(p_values, dtype=float),
        review_flags=np.asarray(review_flags, dtype=bool),
        alpha=float(alpha),
        nonconformity=nonconformity,
        mahalanobis_covariance=(
            str(mahalanobis_covariance)
            if nonconformity == "score_mahalanobis"
            else None
        ),
        n_components=n_components,
        scaling=scaling,
        provenance={
            **dict(proper_training.provenance),
            "split_conformal_fpca_anomaly": {
                "method": "split_conformal_marginal_p_value",
                "reference_model": "proper_training_fpca",
                "proper_training_n": proper_training.n_curves,
                "calibration_n": calibration.n_curves,
                "target_n": targets.n_curves,
                "n_components": n_components,
                "scaling": scaling,
                "nonconformity": nonconformity,
                "mahalanobis_covariance": (
                    mahalanobis_covariance
                    if nonconformity == "score_mahalanobis"
                    else None
                ),
                "random_state": (
                    None if random_state is None else int(random_state)
                ),
                "alpha": float(alpha),
                "minimum_attainable_p": float(minimum_p),
                "tie_rule": "greater_equal_conservative",
                "exchangeability_unit": "curve",
                "marginal_validity_only": True,
                "calibration_conditional_adjustment": False,
                "multiple_testing_correction": False,
                "fdr_control_claimed": False,
                "automatic_exclusion": False,
                "repeated_trial_warning": (
                    "Curve-level conformal validity does not make repeated trials "
                    "from the same participant independent. Use genuinely "
                    "exchangeable independent units for inferential claims."
                ),
            },
        },
    )


def conformal_fpca_anomaly_frame(
    result: ConformalFunctionalAnomalyResult,
) -> pd.DataFrame:
    """Return target split-conformal anomaly results as a tidy table."""

    return pd.DataFrame(
        {
            "curve_id": result.target_curve_ids,
            "nonconformity_score": result.target_scores,
            "conformal_p_value": result.p_values,
            "alpha": np.full(result.n_targets, result.alpha, dtype=float),
            "review_flag": result.review_flags,
            "minimum_attainable_p": np.full(
                result.n_targets,
                result.minimum_attainable_p,
                dtype=float,
            ),
        }
    )
