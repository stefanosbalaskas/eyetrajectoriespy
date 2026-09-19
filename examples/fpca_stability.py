"""Bootstrap functional principal component stability."""

from eyetrajectoriespy import (
    bootstrap_fpca_stability,
    fpca_stability_reporting_text,
    simulate_planar_trajectories,
    summarise_fpca_stability,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=16,
        trials_per_participant=4,
        n_time=61,
        random_state=33,
    )
    stability = bootstrap_fpca_stability(
        gaze,
        n_bootstrap=20,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=33,
    )
    print(summarise_fpca_stability(stability).to_string(index=False))
    print()
    print(fpca_stability_reporting_text(stability))


if __name__ == "__main__":
    main()
