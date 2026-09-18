"""Explicit curve registration for gaze trajectories.

Registration is never automatic in eyetrajectoriespy because phase variation
(e.g. time to inspect evidence) can itself be scientifically meaningful.
"""

from __future__ import annotations

import numpy as np

from .preprocessing import _resample_single_curve
from .types import RegistrationResult, TrajectorySet
from .validation import validate_trajectory_set


def _validate_landmarks(
    observed: np.ndarray,
    reference: np.ndarray,
    trajectories: TrajectorySet,
) -> tuple[np.ndarray, np.ndarray]:
    observed = np.asarray(observed, dtype=float)
    reference = np.asarray(reference, dtype=float)
    if observed.ndim != 2 or observed.shape[0] != trajectories.n_curves:
        raise ValueError("observed_landmarks must have shape (n_curves, n_landmarks)")
    if reference.ndim != 1 or reference.shape[0] != observed.shape[1]:
        raise ValueError("reference_landmarks must contain one value per landmark")
    if observed.shape[1] < 1:
        raise ValueError("At least one landmark is required")
    if not np.all(np.isfinite(observed)) or not np.all(np.isfinite(reference)):
        raise ValueError("Landmarks must be finite")
    if not np.all(np.diff(reference) > 0):
        raise ValueError("reference_landmarks must be strictly increasing")
    if not np.all(np.diff(observed, axis=1) > 0):
        raise ValueError("observed landmarks must be strictly increasing within every curve")
    start, end = trajectories.time[0], trajectories.time[-1]
    if np.any(observed <= start) or np.any(observed >= end):
        raise ValueError("observed landmarks must lie strictly inside the trajectory time domain")
    if np.any(reference <= start) or np.any(reference >= end):
        raise ValueError("reference landmarks must lie strictly inside the trajectory time domain")
    return observed, reference


def register_to_landmarks(
    trajectories: TrajectorySet,
    observed_landmarks: np.ndarray,
    *,
    reference_landmarks: np.ndarray | None = None,
    interpolation: str = "linear",
    max_gap: float | None = None,
) -> RegistrationResult:
    """Register trajectories using monotone piecewise-linear landmark warping.

    The returned warping function ``h_i(t)`` maps *reference time* to the
    corresponding time in each original trajectory. Registered curves are
    therefore evaluated as ``G_i(h_i(t))``.

    Notes
    -----
    The function preserves both the original trajectories and the warping
    functions so phase information is not lost from the analysis record.
    """

    validate_trajectory_set(trajectories)
    observed = np.asarray(observed_landmarks, dtype=float)
    if reference_landmarks is None:
        reference = np.median(observed, axis=0)
    else:
        reference = np.asarray(reference_landmarks, dtype=float)
    observed, reference = _validate_landmarks(observed, reference, trajectories)

    target_time = trajectories.time
    anchor_ref = np.r_[target_time[0], reference, target_time[-1]]
    registered_values = np.full_like(trajectories.values, np.nan, dtype=float)
    warpings = np.empty((trajectories.n_curves, trajectories.n_time), dtype=float)
    for i in range(trajectories.n_curves):
        anchor_obs = np.r_[target_time[0], observed[i], target_time[-1]]
        warped_source_time = np.interp(target_time, anchor_ref, anchor_obs)
        warpings[i] = warped_source_time
        registered_values[i] = _resample_single_curve(
            target_time,
            trajectories.values[i],
            warped_source_time,
            method=interpolation,
            max_gap=max_gap,
        )

    registered = trajectories.with_values(
        registered_values,
        provenance_update={
            "registration": {
                "method": "landmark_piecewise_linear",
                "reference_landmarks": reference.tolist(),
                "interpolation": interpolation,
                "max_gap": max_gap,
            }
        },
    )
    return RegistrationResult(
        registered=registered,
        original=trajectories,
        warping_functions=warpings,
        reference_landmarks=reference,
        observed_landmarks=observed,
        method="landmark_piecewise_linear",
        provenance={
            "scientific_warning": (
                "Registration removes some timing variation. Analyze warping functions or unregistered trajectories "
                "when latency/phase is scientifically meaningful."
            )
        },
    )


def warping_displacement(result: RegistrationResult) -> np.ndarray:
    """Return ``h_i(t) - t`` for each curve and grid point."""

    return result.warping_functions - result.original.time[None, :]


def phase_summary(result: RegistrationResult) -> dict[str, np.ndarray]:
    """Summarize phase/warping magnitude without discarding the full functions."""

    displacement = warping_displacement(result)
    return {
        "mean_absolute_displacement": np.mean(np.abs(displacement), axis=1),
        "max_absolute_displacement": np.max(np.abs(displacement), axis=1),
        "signed_mean_displacement": np.mean(displacement, axis=1),
    }
