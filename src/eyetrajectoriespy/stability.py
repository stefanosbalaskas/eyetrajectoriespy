"""Stability and reconstruction diagnostics for functional principal components."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from .fpca import fit_fpca, fit_mfpca, reconstruct_fpca
from .types import FPCAResult, FPCAStabilityResult, TrajectorySet
from .validation import validate_trajectory_set


def component_similarity_matrix(
    reference: FPCAResult,
    candidate: FPCAResult,
    *,
    n_components: int | None = None,
) -> np.ndarray:
    """Signed integrated cosine similarity between two FPCA component sets.

    Components are compared in the standardized functional geometry used by
    each fit so explicit channel scaling does not distort matching.
    """

    if not np.array_equal(reference.time, candidate.time):
        raise ValueError("FPCA results must use the same time grid")
    if reference.dimension_names != candidate.dimension_names:
        raise ValueError("FPCA results must use the same functional dimensions")
    if n_components is None:
        n_components = min(reference.n_components, candidate.n_components)
    if n_components < 1 or n_components > min(reference.n_components, candidate.n_components):
        raise ValueError("n_components is outside the common fitted range")

    weights = reference.weights
    if not np.allclose(weights, candidate.weights):
        raise ValueError("FPCA quadrature weights differ between results")

    ref = reference.components[:n_components] / reference.scale[None, None, :]
    cand = candidate.components[:n_components] / candidate.scale[None, None, :]
    matrix = np.empty((n_components, n_components), dtype=float)
    for i in range(n_components):
        a = ref[i]
        norm_a = np.sqrt(np.sum((a**2) * weights[:, None]))
        for j in range(n_components):
            b = cand[j]
            norm_b = np.sqrt(np.sum((b**2) * weights[:, None]))
            if norm_a <= np.finfo(float).eps or norm_b <= np.finfo(float).eps:
                matrix[i, j] = np.nan
            else:
                inner = np.sum(a * b * weights[:, None])
                matrix[i, j] = float(inner / (norm_a * norm_b))
    return matrix


def match_fpca_components(
    reference: FPCAResult,
    candidate: FPCAResult,
    *,
    n_components: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Match candidate FPCs to reference FPCs by maximum absolute similarity.

    Returns
    -------
    assignments:
        Candidate component index matched to each reference component.
    signed_similarity:
        Signed similarity after matching. Sign is retained because FPC
        orientation is arbitrary and should be inspected explicitly.
    """

    similarity = component_similarity_matrix(reference, candidate, n_components=n_components)
    if np.isnan(similarity).any():
        raise ValueError("Component similarity is undefined for a zero-norm component")
    rows, cols = linear_sum_assignment(-np.abs(similarity))
    order = np.argsort(rows)
    assignments = cols[order]
    signed = similarity[rows[order], cols[order]]
    return assignments.astype(int), signed.astype(float)


def _fit_for_trajectories(
    trajectories: TrajectorySet,
    *,
    n_components: int,
    scaling: str,
) -> FPCAResult:
    if trajectories.n_dimensions > 1:
        return fit_mfpca(trajectories, n_components=n_components, scaling=scaling)
    return fit_fpca(trajectories, n_components=n_components, scaling=scaling)


def _bootstrap_curves(
    trajectories: TrajectorySet,
    rng: np.random.Generator,
) -> TrajectorySet:
    indices = rng.integers(0, trajectories.n_curves, size=trajectories.n_curves)
    metadata = trajectories.metadata.iloc[indices].reset_index(drop=True)
    ids = tuple(f"bootstrap_curve_{j:05d}|{trajectories.curve_ids[i]}" for j, i in enumerate(indices))
    return TrajectorySet(
        time=trajectories.time,
        values=trajectories.values[indices],
        curve_ids=ids,
        dimension_names=trajectories.dimension_names,
        metadata=metadata,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "bootstrap": {"unit": "curve", "n_draws": trajectories.n_curves},
        },
    )


def _bootstrap_participants(
    trajectories: TrajectorySet,
    rng: np.random.Generator,
    *,
    participant_column: str,
) -> TrajectorySet:
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(f"metadata does not contain participant column {participant_column!r}")
    participant = trajectories.metadata[participant_column].astype(str).to_numpy()
    unique = pd.unique(participant)
    if len(unique) < 2:
        raise ValueError("At least two participants are required for participant bootstrap")
    draws = rng.choice(unique, size=len(unique), replace=True)
    indices: list[int] = []
    labels: list[str] = []
    for copy_index, participant_id in enumerate(draws):
        source = np.flatnonzero(participant == participant_id)
        indices.extend(source.tolist())
        labels.extend([f"{participant_id}#bootstrap{copy_index:04d}"] * len(source))
    idx = np.asarray(indices, dtype=int)
    metadata = trajectories.metadata.iloc[idx].reset_index(drop=True).copy()
    metadata[participant_column] = labels
    ids = tuple(f"bootstrap_{j:05d}|{trajectories.curve_ids[i]}" for j, i in enumerate(idx))
    return TrajectorySet(
        time=trajectories.time,
        values=trajectories.values[idx],
        curve_ids=ids,
        dimension_names=trajectories.dimension_names,
        metadata=metadata,
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={
            **dict(trajectories.provenance),
            "bootstrap": {
                "unit": "participant",
                "participant_column": participant_column,
                "n_draws": len(unique),
            },
        },
    )


def bootstrap_fpca_stability(
    trajectories: TrajectorySet,
    *,
    n_bootstrap: int = 200,
    n_components: int = 3,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    random_state: int | None = 0,
) -> FPCAStabilityResult:
    """Estimate descriptive FPC stability under nonparametric bootstrap.

    Component labels are matched to the full-sample reference by maximum
    absolute functional similarity. Returned bootstrap fractions are
    descriptive stability summaries, not probabilities that a component is
    scientifically true.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if n_bootstrap < 2:
        raise ValueError("n_bootstrap must be at least 2")
    if n_components < 1 or n_components > trajectories.n_curves:
        raise ValueError("n_components must be between 1 and number of trajectories")
    if resample_unit not in {"curve", "participant"}:
        raise ValueError("resample_unit must be 'curve' or 'participant'")
    if resample_unit == "participant" and not participant_column:
        raise ValueError("participant_column is required for participant bootstrap")

    reference = _fit_for_trajectories(
        trajectories,
        n_components=n_components,
        scaling=scaling,
    )
    rng = np.random.default_rng(random_state)
    similarities = np.empty((n_bootstrap, n_components), dtype=float)
    signed = np.empty_like(similarities)
    assignments = np.empty((n_bootstrap, n_components), dtype=int)
    explained = np.empty_like(similarities)
    curve_counts = np.empty(n_bootstrap, dtype=int)

    for b in range(n_bootstrap):
        if resample_unit == "curve":
            sample = _bootstrap_curves(trajectories, rng)
        else:
            sample = _bootstrap_participants(
                trajectories,
                rng,
                participant_column=str(participant_column),
            )
        if sample.n_curves < n_components:
            raise ValueError(
                f"Bootstrap replicate {b} has fewer curves than n_components; reduce n_components"
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
        assignments[b] = matched
        signed[b] = signed_similarity
        similarities[b] = np.abs(signed_similarity)
        explained[b] = candidate.explained_variance_ratio[matched]
        curve_counts[b] = sample.n_curves

    return FPCAStabilityResult(
        reference=reference,
        similarities=similarities,
        signed_similarities=signed,
        assignments=assignments,
        explained_variance_ratio=explained,
        bootstrap_curve_counts=curve_counts,
        resampling_unit=resample_unit,
        random_state=random_state,
        provenance={
            "method": "nonparametric_bootstrap_component_matching",
            "n_bootstrap": n_bootstrap,
            "n_components": n_components,
            "scaling": scaling,
            "participant_column": participant_column,
        },
    )


def summarise_fpca_stability(
    result: FPCAStabilityResult,
    *,
    similarity_threshold: float = 0.80,
    interval: tuple[float, float] = (0.025, 0.975),
) -> pd.DataFrame:
    """Summarize matched FPC stability across bootstrap replicates."""

    if not 0 <= similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be in [0, 1]")
    low, high = interval
    if not 0 <= low < high <= 1:
        raise ValueError("interval must satisfy 0 <= low < high <= 1")
    rows = []
    for k in range(result.reference.n_components):
        values = result.similarities[:, k]
        ev = result.explained_variance_ratio[:, k]
        rows.append(
            {
                "component": k + 1,
                "median_abs_similarity": float(np.median(values)),
                "similarity_interval_low": float(np.quantile(values, low)),
                "similarity_interval_high": float(np.quantile(values, high)),
                "fraction_at_or_above_threshold": float(np.mean(values >= similarity_threshold)),
                "similarity_threshold": similarity_threshold,
                "median_explained_variance_ratio": float(np.median(ev)),
            }
        )
    return pd.DataFrame(rows)


def reconstruction_error_by_curve(
    result: FPCAResult,
    trajectories: TrajectorySet,
    *,
    n_components: int | None = None,
) -> pd.DataFrame:
    """Integrated root-mean-square reconstruction error for each trajectory."""

    validate_trajectory_set(trajectories, require_complete=True)
    if not np.array_equal(trajectories.time, result.time):
        raise ValueError("Trajectory grid must match the fitted FPCA grid")
    if trajectories.dimension_names != result.dimension_names:
        raise ValueError("Functional dimensions must match the fitted FPCA model")
    if trajectories.curve_ids != result.curve_ids:
        raise ValueError("Trajectory IDs/order must match the fitted FPCA result")
    reconstructed = reconstruct_fpca(result, scores=None, n_components=n_components)
    if reconstructed.shape[0] != trajectories.n_curves:
        raise ValueError(
            "reconstruction_error_by_curve requires the trajectories used to fit the supplied result"
        )
    error = reconstructed - trajectories.values
    weighted_mse = np.sum(
        error**2 * result.weights[None, :, None],
        axis=(1, 2),
    ) / (result.weights.sum() * trajectories.n_dimensions)
    return pd.DataFrame(
        {
            "curve_id": trajectories.curve_ids,
            "n_components": result.n_components if n_components is None else n_components,
            "integrated_rmse": np.sqrt(weighted_mse),
        }
    )


def fpca_reconstruction_curve(
    result: FPCAResult,
    trajectories: TrajectorySet,
) -> pd.DataFrame:
    """Overall reconstruction error as the retained component count increases."""

    rows = []
    for n_components in range(1, result.n_components + 1):
        frame = reconstruction_error_by_curve(
            result,
            trajectories,
            n_components=n_components,
        )
        rows.append(
            {
                "n_components": n_components,
                "mean_integrated_rmse": float(frame["integrated_rmse"].mean()),
                "median_integrated_rmse": float(frame["integrated_rmse"].median()),
                "cumulative_variance_ratio": float(
                    result.cumulative_explained_variance()[n_components - 1]
                ),
            }
        )
    return pd.DataFrame(rows)
