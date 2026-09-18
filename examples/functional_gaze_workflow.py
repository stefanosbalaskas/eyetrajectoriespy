"""End-to-end continuous 2-D gaze FPCA example."""

from eyetrajectoriespy import (
    fit_mfpca,
    fpca_reporting_text,
    simulate_planar_trajectories,
    summarise_fpca,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=6,
        n_time=101,
        random_state=7,
    )
    fit = fit_mfpca(gaze, n_components=0.95, scaling="dimension_sd")
    print(summarise_fpca(fit).to_string(index=False))
    print()
    print(fpca_reporting_text(fit))


if __name__ == "__main__":
    main()
