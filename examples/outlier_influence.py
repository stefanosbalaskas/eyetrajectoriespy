"""FPCA anomaly screening and participant-level influence diagnostics."""

import numpy as np

from eyetrajectoriespy import (
    diagnose_fpca_outliers,
    fit_mfpca,
    leave_one_group_out_fpca_influence,
    simulate_planar_trajectories,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=16,
        trials_per_participant=3,
        n_time=61,
        duration=2.0,
        random_state=33,
    )
    values = gaze.values.copy()
    u = gaze.time / gaze.time[-1]
    values[-1, :, 0] = np.clip(0.10 + 0.80 * np.sin(np.pi * u) ** 2, 0, 1)
    values[-1, :, 1] = np.clip(0.90 - 0.70 * u, 0, 1)
    gaze = gaze.with_values(
        values,
        provenance_update={"synthetic_atypical_curve": gaze.curve_ids[-1]},
    )

    fit = fit_mfpca(gaze, n_components=4, scaling="dimension_sd")
    outliers = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=4,
        score_covariance="robust",
        random_state=33,
    )
    print(outliers.diagnostics.sort_values("score_mahalanobis_sq", ascending=False).head())

    influence = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=3,
        scaling="dimension_sd",
    )
    print()
    print(influence.summary.sort_values("influence_score", ascending=False).head())


if __name__ == "__main__":
    main()
