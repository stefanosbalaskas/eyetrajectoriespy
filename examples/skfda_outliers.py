"""Optional scikit-fda functional boxplot outlier screening."""

from eyetrajectoriespy import (
    detect_functional_outliers_skfda,
    simulate_planar_trajectories,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=10,
        trials_per_participant=2,
        n_time=61,
        random_state=6,
    )
    result = detect_functional_outliers_skfda(
        gaze,
        dimension="x",
        method="boxplot",
        factor=1.5,
    )
    print(result.diagnostics.to_string(index=False))


if __name__ == "__main__":
    main()
