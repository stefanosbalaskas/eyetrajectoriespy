"""Phase-function analysis and registration sensitivity diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fpca import fit_fpca, fit_mfpca
from .stability import match_fpca_components
from .types import (
    FPCAResult,
    RegistrationResult,
    RegistrationSensitivityResult,
    TrajectorySet,
)


def phase_trajectory_set(
    registration: RegistrationResult,
    *,
    representation: str = "displacement",
) -> TrajectorySet:
    """Convert registration warpings into a one-dimensional functional object.

    Parameters
    ----------
    representation:
        "displacement" returns h_i(t) - t. "warping" returns h_i(t).
    """

    if representation == "displacement":
        values = (
            registration.warping_functions
            - registration.original.time[None, :]
        )[:, :, None]
        dimension_name = "phase_displacement"
    elif representation == "warping":
        values = registration.warping_functions[:, :, None]
        dimension_name = "warping_time"
    else:
        raise ValueError("representation must be 'displacement' or 'warping'")

    return TrajectorySet(
        time=registration.original.time,
        values=values,
        curve_ids=registration.original.curve_ids,
        dimension_names=(dimension_name,),
        metadata=registration.original.metadata.reset_index(drop=True),
        coordinate_system="phase_time",
        time_unit=registration.original.time_unit,
        provenance={
            **dict(registration.provenance),
            "phase_representation": representation,
            "registration_method": registration.method,
        },
    )


def fit_phase_fpca(
    registration: RegistrationResult,
    *,
    representation: str = "displacement",
    n_components: int | float = 0.95,
) -> FPCAResult:
    """Fit univariate FPCA to registration-derived phase functions."""

    phase = phase_trajectory_set(
        registration,
        representation=representation,
    )
    return fit_fpca(
        phase,
        n_components=n_components,
        scaling="none",
    )


def _fit_spatial(
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


def compare_registered_unregistered_fpca(
    registration: RegistrationResult,
    *,
    n_components: int = 3,
    scaling: str = "none",
) -> RegistrationSensitivityResult:
    """Compare dominant FPCs before and after explicit registration.

    Component functions are matched by maximum absolute functional similarity.
    Score correlations use sign-aligned registered scores and quantify whether
    participant/trial ordering is preserved after timing alignment.
    """

    if n_components < 1:
        raise ValueError("n_components must be positive")
    original = registration.original
    registered = registration.registered
    if original.curve_ids != registered.curve_ids:
        raise ValueError("Original and registered curve ordering must match")

    unregistered_fit = _fit_spatial(
        original,
        n_components=n_components,
        scaling=scaling,
    )
    registered_fit = _fit_spatial(
        registered,
        n_components=n_components,
        scaling=scaling,
    )

    assignments, signed_similarity = match_fpca_components(
        unregistered_fit,
        registered_fit,
        n_components=n_components,
    )

    score_correlations = np.empty(n_components, dtype=float)
    for k, matched in enumerate(assignments):
        sign = 1.0 if signed_similarity[k] >= 0 else -1.0
        a = unregistered_fit.scores[:, k]
        b = sign * registered_fit.scores[:, matched]
        if np.std(a) <= np.finfo(float).eps or np.std(b) <= np.finfo(float).eps:
            score_correlations[k] = np.nan
        else:
            score_correlations[k] = float(np.corrcoef(a, b)[0, 1])

    return RegistrationSensitivityResult(
        unregistered_fpca=unregistered_fit,
        registered_fpca=registered_fit,
        component_assignments=assignments,
        signed_component_similarity=signed_similarity,
        score_correlations=score_correlations,
        provenance={
            "method": "registered_vs_unregistered_fpca",
            "registration_method": registration.method,
            "n_components": n_components,
            "scaling": scaling,
        },
    )


def registration_sensitivity_frame(
    result: RegistrationSensitivityResult,
) -> pd.DataFrame:
    """Return a tidy component-level registration sensitivity table."""

    return pd.DataFrame(
        {
            "unregistered_component": np.arange(
                1,
                result.unregistered_fpca.n_components + 1,
            ),
            "registered_component": result.component_assignments + 1,
            "signed_component_similarity": result.signed_component_similarity,
            "absolute_component_similarity": np.abs(
                result.signed_component_similarity
            ),
            "score_correlation": result.score_correlations,
        }
    )


def phase_landmark_frame(
    registration: RegistrationResult,
) -> pd.DataFrame:
    """Return observed-minus-reference landmark timing deviations by curve."""

    observed = np.asarray(registration.observed_landmarks, dtype=float)
    reference = np.asarray(registration.reference_landmarks, dtype=float)
    if observed.ndim != 2:
        raise ValueError("observed_landmarks must be two-dimensional")
    rows: list[dict[str, float | int | str]] = []
    for i, curve_id in enumerate(registration.original.curve_ids):
        for landmark in range(observed.shape[1]):
            rows.append(
                {
                    "curve_id": curve_id,
                    "landmark": landmark + 1,
                    "observed_time": float(observed[i, landmark]),
                    "reference_time": float(reference[landmark]),
                    "timing_deviation": float(
                        observed[i, landmark] - reference[landmark]
                    ),
                }
            )
    return pd.DataFrame(rows)
