"""Eigenvalue-gap and eigenspace stability diagnostics for FPCA."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stability import _bootstrap_curves, _bootstrap_participants, _fit_for_trajectories
from .types import (
    FPCAResult,
    FPCASubspaceComparisonResult,
    FPCASubspaceStabilityResult,
    TrajectorySet,
)
from .validation import validate_trajectory_set


def fpca_eigenvalue_gap_table(
    result: FPCAResult,
    *,
    relative_gap_threshold: float | None = None,
) -> pd.DataFrame:
    """Return adjacent retained-eigenvalue gap diagnostics.

    The table is descriptive. A relative_gap_threshold is optional and, when
    supplied, creates an explicit near_tie_flag. No threshold is imposed by
    default because the meaning of a practically small eigengap depends on the
    study, sample size, and downstream interpretation.

    Only gaps between retained components can be calculated from the supplied
    fit. To inspect the gap at a proposed retention boundary, fit at least one
    component beyond that boundary.
    """

    values = np.asarray(result.explained_variance, dtype=float)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("At least two fitted components are required for eigengap diagnostics")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("explained_variance must contain finite non-negative values")
    if np.any(np.diff(values) > np.finfo(float).eps * max(1.0, float(values[0]))):
        raise ValueError("explained_variance must be non-increasing")

    if relative_gap_threshold is not None:
        threshold = float(relative_gap_threshold)
        if not 0 <= threshold < 1:
            raise ValueError("relative_gap_threshold must be in [0, 1)")
    else:
        threshold = None

    current = values[:-1]
    following = values[1:]
    absolute_gap = current - following
    denominator = np.maximum(current, np.finfo(float).eps)
    relative_gap = absolute_gap / denominator
    ratio = np.divide(
        following,
        denominator,
        out=np.zeros_like(following),
        where=denominator > 0,
    )

    frame = pd.DataFrame(
        {
            "component": np.arange(1, len(values)),
            "next_component": np.arange(2, len(values) + 1),
            "eigenvalue": current,
            "next_eigenvalue": following,
            "absolute_gap": absolute_gap,
            "relative_gap": relative_gap,
            "next_to_current_ratio": ratio,
        }
    )
    if threshold is not None:
        frame["near_tie_flag"] = frame["relative_gap"] <= threshold
        frame["relative_gap_threshold"] = threshold
    return frame


def _validate_subspace_inputs(
    reference: FPCAResult,
    candidate: FPCAResult,
    *,
    start_component: int,
    n_components: int,
) -> tuple[int, int]:
    if isinstance(start_component, bool) or not isinstance(start_component, int):
        raise TypeError("start_component must be an integer")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if start_component < 0:
        raise ValueError("start_component must be non-negative")
    if n_components < 1:
        raise ValueError("n_components must be positive")

    stop = start_component + n_components
    if stop > reference.n_components or stop > candidate.n_components:
        raise ValueError("Requested subspace is outside the common fitted component range")
    if not np.array_equal(reference.time, candidate.time):
        raise ValueError("FPCA results must use the same time grid")
    if reference.dimension_names != candidate.dimension_names:
        raise ValueError("FPCA results must use the same functional dimensions")
    if reference.coordinate_system != candidate.coordinate_system:
        raise ValueError("FPCA results must use the same coordinate system")
    if reference.time_unit != candidate.time_unit:
        raise ValueError("FPCA results must use the same time unit")
    if not np.allclose(reference.weights, candidate.weights):
        raise ValueError("FPCA quadrature weights differ between results")
    return start_component, stop


def _standardized_block(
    result: FPCAResult,
    *,
    start: int,
    stop: int,
) -> np.ndarray:
    block = (
        result.components[start:stop]
        / result.scale[None, None, :]
        * np.sqrt(result.weights)[None, :, None]
    )
    flat = block.reshape(stop - start, -1)
    gram = flat @ flat.T
    if not np.allclose(gram, np.eye(stop - start), atol=1e-7, rtol=1e-7):
        raise ValueError("Selected FPCA components are not orthonormal in the fitted functional geometry")
    return flat


def compare_fpca_subspaces(
    reference: FPCAResult,
    candidate: FPCAResult,
    *,
    start_component: int = 0,
    n_components: int = 2,
) -> FPCASubspaceComparisonResult:
    """Compare corresponding FPC subspaces using principal angles.

    This diagnostic is invariant to sign changes, permutations, and rotations
    within the selected subspace. It is useful when adjacent eigenvalues are
    close and individual FPC labels can swap or rotate.

    normalized_projector_distance lies in [0, 1], where zero indicates
    identical subspaces. It is the Frobenius distance between the two
    projection operators divided by sqrt(2 * n_components).
    """

    start, stop = _validate_subspace_inputs(
        reference,
        candidate,
        start_component=start_component,
        n_components=n_components,
    )
    ref = _standardized_block(reference, start=start, stop=stop)
    cand = _standardized_block(candidate, start=start, stop=stop)

    singular_values = np.linalg.svd(ref @ cand.T, compute_uv=False)
    principal_cosines = np.clip(singular_values, 0.0, 1.0)
    principal_angles = np.degrees(np.arccos(principal_cosines))

    squared_sines = np.maximum(0.0, 1.0 - principal_cosines**2)
    projector_distance = float(np.sqrt(2.0 * np.sum(squared_sines)))
    normalized_distance = float(projector_distance / np.sqrt(2.0 * n_components))

    indices = tuple(range(start, stop))
    return FPCASubspaceComparisonResult(
        reference=reference,
        candidate=candidate,
        component_indices=indices,
        principal_cosines=principal_cosines,
        principal_angles_degrees=principal_angles,
        projector_distance_frobenius=projector_distance,
        normalized_projector_distance=normalized_distance,
        provenance={
            "method": "principal_angles_weighted_functional_subspace",
            "start_component_zero_based": start_component,
            "n_components": n_components,
            "standardization": "fit_specific_dimension_scale",
            "rotation_invariant_within_selected_subspace": True,
        },
    )


def bootstrap_fpca_subspace_stability(
    trajectories: TrajectorySet,
    *,
    start_component: int = 0,
    n_components: int = 2,
    n_bootstrap: int = 200,
    scaling: str = "none",
    resample_unit: str = "curve",
    participant_column: str | None = None,
    random_state: int | None = 0,
) -> FPCASubspaceStabilityResult:
    """Bootstrap stability of a contiguous FPCA eigenspace.

    The same ranked component block is compared between the full-sample fit and
    each bootstrap fit using principal angles. Individual FPC matching is not
    required, so rotations or swaps within the selected block do not create
    false instability.

    The result is descriptive and does not test equality of population
    eigenspaces.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if isinstance(start_component, bool) or not isinstance(start_component, int):
        raise TypeError("start_component must be an integer")
    if isinstance(n_components, bool) or not isinstance(n_components, int):
        raise TypeError("n_components must be an integer")
    if start_component < 0:
        raise ValueError("start_component must be non-negative")
    if n_components < 1:
        raise ValueError("n_components must be positive")
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int) or n_bootstrap < 2:
        raise ValueError("n_bootstrap must be an integer >= 2")
    if resample_unit not in {"curve", "participant"}:
        raise ValueError("resample_unit must be 'curve' or 'participant'")
    if resample_unit == "participant" and not participant_column:
        raise ValueError("participant_column is required for participant bootstrap")

    stop = start_component + n_components
    if stop > trajectories.n_curves - 1:
        raise ValueError(
            "Requested subspace exceeds the maximum non-zero sample FPCA rank; "
            "reduce start_component or n_components"
        )

    reference = _fit_for_trajectories(
        trajectories,
        n_components=stop,
        scaling=scaling,
    )
    rng = np.random.default_rng(random_state)
    principal_cosines = np.empty((n_bootstrap, n_components), dtype=float)
    principal_angles = np.empty_like(principal_cosines)
    projector_distance = np.empty(n_bootstrap, dtype=float)
    normalized_distance = np.empty(n_bootstrap, dtype=float)

    for bootstrap_index in range(n_bootstrap):
        if resample_unit == "curve":
            sample = _bootstrap_curves(trajectories, rng)
        else:
            sample = _bootstrap_participants(
                trajectories,
                rng,
                participant_column=str(participant_column),
            )
        if stop > sample.n_curves - 1:
            raise ValueError(
                f"Bootstrap replicate {bootstrap_index} has insufficient non-zero "
                "sample rank for the requested subspace"
            )
        candidate = _fit_for_trajectories(
            sample,
            n_components=stop,
            scaling=scaling,
        )
        comparison = compare_fpca_subspaces(
            reference,
            candidate,
            start_component=start_component,
            n_components=n_components,
        )
        principal_cosines[bootstrap_index] = comparison.principal_cosines
        principal_angles[bootstrap_index] = comparison.principal_angles_degrees
        projector_distance[bootstrap_index] = comparison.projector_distance_frobenius
        normalized_distance[bootstrap_index] = comparison.normalized_projector_distance

    return FPCASubspaceStabilityResult(
        reference=reference,
        component_indices=tuple(range(start_component, stop)),
        principal_cosines=principal_cosines,
        principal_angles_degrees=principal_angles,
        projector_distance_frobenius=projector_distance,
        normalized_projector_distance=normalized_distance,
        resampling_unit=resample_unit,
        random_state=random_state,
        provenance={
            "method": "bootstrap_principal_angle_subspace_stability",
            "n_bootstrap": n_bootstrap,
            "start_component_zero_based": start_component,
            "n_components": n_components,
            "scaling": scaling,
            "participant_column": participant_column,
            "scientific_warning": (
                "Subspace stability is descriptive and does not establish that "
                "individual FPC labels within a near-tied block are identifiable."
            ),
        },
    )


def summarise_fpca_subspace_stability(
    result: FPCASubspaceStabilityResult,
    *,
    interval: tuple[float, float] = (0.025, 0.975),
) -> pd.DataFrame:
    """Summarize bootstrap principal-angle and projector-distance stability."""

    low, high = interval
    if not 0 <= low < high <= 1:
        raise ValueError("interval must satisfy 0 <= low < high <= 1")

    minimum_cosine = np.min(result.principal_cosines, axis=1)
    maximum_angle = np.max(result.principal_angles_degrees, axis=1)
    distance = result.normalized_projector_distance
    indices = result.component_indices
    return pd.DataFrame(
        [
            {
                "component_start": indices[0] + 1,
                "component_end": indices[-1] + 1,
                "n_components": len(indices),
                "median_min_principal_cosine": float(np.median(minimum_cosine)),
                "min_principal_cosine_interval_low": float(np.quantile(minimum_cosine, low)),
                "min_principal_cosine_interval_high": float(np.quantile(minimum_cosine, high)),
                "median_max_principal_angle_degrees": float(np.median(maximum_angle)),
                "max_principal_angle_interval_low": float(np.quantile(maximum_angle, low)),
                "max_principal_angle_interval_high": float(np.quantile(maximum_angle, high)),
                "median_normalized_projector_distance": float(np.median(distance)),
                "normalized_projector_distance_interval_low": float(np.quantile(distance, low)),
                "normalized_projector_distance_interval_high": float(np.quantile(distance, high)),
            }
        ]
    )
