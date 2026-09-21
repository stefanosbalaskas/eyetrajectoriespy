"""Outcome-tuned FPCA regression with participant-grouped nested CV."""

import numpy as np

from eyetrajectoriespy import (
    cross_validate_fpca_regression,
    fpca_nested_regression_cv_reporting_text,
    fpca_regression_cv_reporting_text,
    nested_cross_validate_fpca_regression,
    select_fpca_regression_components,
    simulate_planar_trajectories,
    summarise_fpca_regression_cv,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

    rng = np.random.default_rng(2026)
    signal = gaze.values[:, :, 0].mean(axis=1)
    outcome = 3.0 * signal + rng.normal(scale=0.03, size=gaze.n_curves)

    cv = cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=(1, 2, 3, 4),
        family="gaussian",
        loss="rmse",
        n_splits=6,
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=2026,
    )
    print(summarise_fpca_regression_cv(cv).to_string(index=False))
    print("one-SE selection:", select_fpca_regression_components(cv, rule="one_se"))
    print(fpca_regression_cv_reporting_text(cv, rule="one_se"))

    nested = nested_cross_validate_fpca_regression(
        gaze,
        outcome,
        candidate_components=(1, 2, 3, 4),
        family="gaussian",
        loss="rmse",
        outer_splits=6,
        inner_splits=5,
        selection_rule="one_se",
        scaling="dimension_sd",
        cv_unit="group",
        group_column="participant_id",
        random_state=2026,
    )
    print()
    print(nested.outer_folds.to_string(index=False))
    print(fpca_nested_regression_cv_reporting_text(nested))


if __name__ == "__main__":
    main()
