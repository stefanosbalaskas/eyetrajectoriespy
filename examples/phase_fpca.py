"""Analyze timing warpings as data instead of discarding them."""

import numpy as np

from eyetrajectoriespy import (
    compare_registered_unregistered_fpca,
    fit_phase_fpca,
    phase_landmark_frame,
    register_to_landmarks,
    registration_sensitivity_frame,
    simulate_planar_trajectories,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=3,
        n_time=81,
        duration=2.0,
        random_state=19,
    )
    observed_landmarks = np.linspace(0.72, 1.28, gaze.n_curves)[:, None]
    registration = register_to_landmarks(
        gaze,
        observed_landmarks,
        reference_landmarks=np.array([1.0]),
    )

    phase_fit = fit_phase_fpca(registration, n_components=2)
    print("phase variance ratios:", phase_fit.explained_variance_ratio)
    print(phase_landmark_frame(registration).head().to_string(index=False))

    sensitivity = compare_registered_unregistered_fpca(
        registration,
        n_components=3,
        scaling="dimension_sd",
    )
    print(registration_sensitivity_frame(sensitivity).to_string(index=False))


if __name__ == "__main__":
    main()
