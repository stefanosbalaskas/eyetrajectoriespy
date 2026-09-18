import matplotlib.pyplot as plt
import numpy as np

from eyetrajectoriespy import (
    diagnose_fpca_outliers,
    fit_mfpca,
    fpca_influence_reporting_text,
    fpca_outlier_reporting_text,
    leave_one_group_out_fpca_influence,
    plot_fpca_influence,
    plot_fpca_outlier_diagnostics,
    simulate_planar_trajectories,
)


def test_outlier_and_influence_reporting_and_plots():
    gaze = simulate_planar_trajectories(
        n_participants=8,
        trials_per_participant=3,
        n_time=41,
        duration=2.0,
        random_state=17,
    )
    values = gaze.values.copy()
    u = gaze.time / gaze.time[-1]
    values[-1, :, 0] = np.clip(0.15 + 0.75 * np.sin(np.pi * u) ** 2, 0, 1)
    values[-1, :, 1] = np.clip(0.85 - 0.65 * u, 0, 1)
    gaze = gaze.with_values(values)

    fit = fit_mfpca(gaze, n_components=3, scaling="dimension_sd")
    outliers = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=3,
        random_state=17,
    )
    assert "Functional anomaly screening" in fpca_outlier_reporting_text(outliers)
    assert plot_fpca_outlier_diagnostics(outliers) is not None

    influence = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=2,
        scaling="dimension_sd",
    )
    assert "Leave-one-participant_id-out FPCA influence" in fpca_influence_reporting_text(influence)
    assert plot_fpca_influence(influence) is not None
    plt.close("all")
