"""Landmark registration while preserving phase/warping information."""

import numpy as np

from eyetrajectoriespy import phase_summary, register_to_landmarks, simulate_planar_trajectories


def main() -> None:
    gaze = simulate_planar_trajectories(n_participants=8, trials_per_participant=4, n_time=101)
    rng = np.random.default_rng(9)
    observed = np.clip(rng.normal(0.9, 0.12, size=(gaze.n_curves, 1)), 0.2, 1.8)
    result = register_to_landmarks(gaze, observed, reference_landmarks=np.array([0.9]))
    print(phase_summary(result))


if __name__ == "__main__":
    main()
