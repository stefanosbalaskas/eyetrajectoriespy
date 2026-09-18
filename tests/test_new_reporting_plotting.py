import numpy as np
import matplotlib.pyplot as plt

from eyetrajectoriespy import (
    bootstrap_fpca_stability,
    compare_registered_unregistered_fpca,
    fpca_reconstruction_curve,
    fpca_stability_reporting_text,
    plot_fpca_stability,
    plot_reconstruction_curve,
    register_to_landmarks,
    registration_sensitivity_reporting_text,
    simulate_planar_trajectories,
)


def test_new_reporting_and_plotting_helpers():
    gaze = simulate_planar_trajectories(
        n_participants=6,
        trials_per_participant=2,
        n_time=31,
        duration=2.0,
        random_state=2,
    )
    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=4,
        n_components=2,
        scaling="dimension_sd",
        random_state=2,
    )
    text = fpca_stability_reporting_text(stability)
    assert "Bootstrap FPCA stability" in text
    ax = plot_fpca_stability(stability)
    assert ax is not None

    curve = fpca_reconstruction_curve(stability.reference, gaze)
    ax2 = plot_reconstruction_curve(curve)
    assert ax2 is not None

    observed = np.linspace(0.8, 1.2, gaze.n_curves)[:, None]
    registration = register_to_landmarks(
        gaze,
        observed,
        reference_landmarks=np.array([1.0]),
    )
    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=2,
        scaling="dimension_sd",
    )
    text2 = registration_sensitivity_reporting_text(sensitivity)
    assert "Registration sensitivity" in text2
    plt.close("all")
