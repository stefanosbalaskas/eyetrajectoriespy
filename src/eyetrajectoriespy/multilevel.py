"""Multilevel functional PCA for participant → trial → time designs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fpca import fit_fpca, fpca_score_frame
from .types import MultilevelFPCAResult, TrajectorySet
from .validation import validate_trajectory_set


def fit_multilevel_fpca(
    trajectories: TrajectorySet,
    *,
    participant_column: str,
    participant_components: int | float = 0.95,
    trial_components: int | float = 0.95,
    scaling: str = "none",
) -> MultilevelFPCAResult:
    """Separate between-participant and within-participant functional variation.

    This implements a transparent two-level functional ANOVA decomposition:

    ``G_ij(t) = mu(t) + U_i(t) + V_ij(t)``

    FPCA is then fitted separately to participant mean deviations ``U_i`` and
    trial residuals ``V_ij``. It is appropriate for repeated trial designs when
    the goal is to avoid mixing stable participant differences with trial-level
    functional variability.
    """

    validate_trajectory_set(trajectories, require_complete=True)
    if participant_column not in trajectories.metadata.columns:
        raise ValueError(f"metadata does not contain {participant_column!r}")
    participants = trajectories.metadata[participant_column].astype(str).to_numpy()
    unique = pd.unique(participants)
    if len(unique) < 2:
        raise ValueError("At least two participants are required")

    participant_means = []
    participant_ids = []
    trial_residuals = np.empty_like(trajectories.values)
    for participant in unique:
        idx = np.flatnonzero(participants == participant)
        mean_curve = trajectories.values[idx].mean(axis=0)
        participant_means.append(mean_curve)
        participant_ids.append(str(participant))
        trial_residuals[idx] = trajectories.values[idx] - mean_curve[None, :, :]

    grand_mean = trajectories.values.mean(axis=0)
    participant_deviations = np.stack(participant_means) - grand_mean[None, :, :]
    participant_set = TrajectorySet(
        time=trajectories.time,
        values=participant_deviations,
        curve_ids=tuple(participant_ids),
        dimension_names=trajectories.dimension_names,
        metadata=pd.DataFrame({participant_column: participant_ids}),
        coordinate_system=trajectories.coordinate_system,
        time_unit=trajectories.time_unit,
        provenance={**dict(trajectories.provenance), "level": "participant_deviation"},
    )
    trial_set = trajectories.with_values(
        trial_residuals,
        provenance_update={"level": "within_participant_trial_residual"},
    )

    participant_fpca = fit_fpca(
        participant_set,
        n_components=participant_components,
        scaling=scaling,
    )
    trial_fpca = fit_fpca(
        trial_set,
        n_components=trial_components,
        scaling=scaling,
    )
    participant_scores = fpca_score_frame(participant_fpca, prefix="participant_FPC")
    participant_scores[participant_column] = participant_ids
    trial_scores = fpca_score_frame(trial_fpca, prefix="trial_FPC")
    trial_scores[participant_column] = participants

    return MultilevelFPCAResult(
        grand_mean=grand_mean,
        participant_fpca=participant_fpca,
        trial_fpca=trial_fpca,
        participant_scores=participant_scores,
        trial_scores=trial_scores,
        participant_column=participant_column,
        provenance={
            "method": "two_level_functional_ANOVA_FPCA",
            "n_participants": int(len(unique)),
            "n_trials": int(trajectories.n_curves),
            "scaling": scaling,
        },
    )
