"""Participant → trial → time functional decomposition."""

from eyetrajectoriespy import fit_multilevel_fpca, simulate_planar_trajectories


def main() -> None:
    gaze = simulate_planar_trajectories(n_participants=10, trials_per_participant=5, n_time=81)
    result = fit_multilevel_fpca(
        gaze,
        participant_column="participant_id",
        participant_components=0.9,
        trial_components=0.9,
        scaling="dimension_sd",
    )
    print(result.participant_scores.head().to_string(index=False))
    print(result.trial_scores.head().to_string(index=False))


if __name__ == "__main__":
    main()
