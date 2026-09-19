"""Near-tied FPC eigengap and subspace-stability example."""

from eyetrajectoriespy import (
    bootstrap_fpca_subspace_stability,
    fit_mfpca,
    fpca_eigengap_reporting_text,
    fpca_eigenvalue_gap_table,
    fpca_subspace_stability_reporting_text,
    simulate_planar_trajectories,
    summarise_fpca_subspace_stability,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=3,
        n_time=61,
        random_state=42,
    )
    fit = fit_mfpca(
        gaze,
        n_components=4,
        scaling="dimension_sd",
    )
    print(fpca_eigenvalue_gap_table(fit).to_string(index=False))
    print(fpca_eigengap_reporting_text(fit))

    stability = bootstrap_fpca_subspace_stability(
        gaze,
        start_component=0,
        n_components=2,
        n_bootstrap=20,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=42,
    )
    print(summarise_fpca_subspace_stability(stability).to_string(index=False))
    print(fpca_subspace_stability_reporting_text(stability))


if __name__ == "__main__":
    main()
