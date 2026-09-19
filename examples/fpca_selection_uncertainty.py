"""Grouped reconstruction CV and matched-bootstrap FPC envelopes."""

from eyetrajectoriespy import (
    bootstrap_fpca_component_envelopes,
    cross_validate_fpca_reconstruction,
    fpca_component_envelope_reporting_text,
    fpca_cross_validation_reporting_text,
    select_fpca_components_cv,
    simulate_planar_trajectories,
    summarise_fpca_cross_validation,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=12,
        trials_per_participant=3,
        n_time=61,
        random_state=2026,
    )
    cv = cross_validate_fpca_reconstruction(
        gaze,
        candidate_components=(1, 2, 3, 4, 5),
        n_splits=4,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
    )
    print(summarise_fpca_cross_validation(cv).to_string(index=False))
    print("minimum-RMSE count:", select_fpca_components_cv(cv, rule="minimum"))
    print("one-SE count:", select_fpca_components_cv(cv, rule="one_se"))
    print(fpca_cross_validation_reporting_text(cv, rule="one_se"))

    envelopes = bootstrap_fpca_component_envelopes(
        gaze,
        n_bootstrap=20,
        n_components=3,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.95,
        random_state=2026,
    )
    print(fpca_component_envelope_reporting_text(envelopes))


if __name__ == "__main__":
    main()
