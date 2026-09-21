# Worked example: predictive FPCA selection with nested participant CV

This synthetic example asks how many FPC scores are useful for predicting a scalar outcome.

The participants contribute repeated trials, so every cross-validation split is participant-grouped.

## Generate trajectories and an outcome

    import numpy as np

    from eyetrajectoriespy import simulate_planar_trajectories

    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

    rng = np.random.default_rng(2026)
    signal = gaze.values[:, :, 0].mean(axis=1)
    outcome = 3.0 * signal + rng.normal(
        scale=0.03,
        size=gaze.n_curves,
    )

The example deliberately creates an outcome related to continuous gaze geometry. Real studies should define the scalar outcome independently of exploratory tuning.

## Tune component count

    from eyetrajectoriespy import (
        cross_validate_fpca_regression,
        select_fpca_regression_components,
        summarise_fpca_regression_cv,
    )

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

    print(summarise_fpca_regression_cv(cv))

Audit participant leakage:

    assert (
        cv.assignments
        .groupby("group")["fold"]
        .nunique()
        .eq(1)
        .all()
    )

Select using the pre-specified rule:

    selected = select_fpca_regression_components(
        cv,
        rule="one_se",
    )

## Why this CV loss is not the final performance estimate

The same folds were used to compare candidate component counts. The best observed loss therefore participated in model selection.

To estimate the performance of the complete selection procedure, use nested CV.

## Nested participant-grouped evaluation

    from eyetrajectoriespy import nested_cross_validate_fpca_regression

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

    print(nested.outer_folds)
    print(nested.inner_summaries)

Each outer test participant is unseen during:

- FPCA mean/scaling estimation;
- FPCA eigenfunction estimation;
- regression fitting;
- inner component-count selection.

## Plot the diagnostics

    from eyetrajectoriespy import (
        plot_fpca_regression_cv,
        plot_nested_fpca_regression_cv,
    )

    plot_fpca_regression_cv(cv)
    plot_nested_fpca_regression_cv(nested)

## Manuscript wording

    from eyetrajectoriespy import (
        fpca_nested_regression_cv_reporting_text,
        fpca_regression_cv_reporting_text,
    )

    print(
        fpca_regression_cv_reporting_text(
            cv,
            rule="one_se",
        )
    )

    print(
        fpca_nested_regression_cv_reporting_text(
            nested,
        )
    )

## Binary outcome variant

For a binary outcome, use probability scoring:

    cv_binary = cross_validate_fpca_regression(
        gaze,
        choice,
        candidate_components=(1, 2, 3, 4),
        family="binomial",
        loss="log_loss",
        cv_unit="group",
        group_column="participant_id",
        n_splits=6,
    )

Brier loss is also available.

The model refuses to silently accept training folds with one class, perfect separation, non-convergence, or invalid probability predictions.

## Interpretation

A smaller selected component count does not mean the discarded FPCs are scientifically unimportant. It means they did not improve the chosen held-out prediction loss enough under the specified selection rule.

Likewise, a component retained for prediction should not automatically be labeled as a psychological mechanism.

## Next steps

- [Selecting FPC count for reconstruction](../guides/component-selection.md)
- [Outcome-tuned predictive selection](../guides/predictive-component-selection.md)
- [FPC stability](../guides/stability-validation.md)
- [Functional regression & clustering](../guides/downstream.md)
- [Reporting checklist](../methods/reporting.md)
