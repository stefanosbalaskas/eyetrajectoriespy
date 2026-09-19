# Worked example: anomaly screening and influence

This synthetic example deliberately inserts one atypical continuous path into the final trial.

    gaze = simulate_planar_trajectories(
        n_participants=16,
        trials_per_participant=3,
        n_time=61,
        random_state=33,
    )

    values = gaze.values.copy()
    u = gaze.time / gaze.time[-1]
    values[-1, :, 0] = np.clip(
        0.10 + 0.80 * np.sin(np.pi * u) ** 2,
        0,
        1,
    )
    values[-1, :, 1] = np.clip(
        0.90 - 0.70 * u,
        0,
        1,
    )
    gaze = gaze.with_values(values)

## Fit the planned FPCA

    fit = fit_mfpca(
        gaze,
        n_components=4,
        scaling="dimension_sd",
    )

## Screen trajectories for review

    review = diagnose_fpca_outliers(
        fit,
        gaze,
        n_components=4,
        score_covariance="robust",
        random_state=33,
    )

    review.diagnostics.sort_values(
        "score_mahalanobis_sq",
        ascending=False,
    ).head()

A high score-space distance identifies a trajectory occupying an unusual position in the retained functional score space.

## Check participant influence

Because each participant contributes three trials:

    influence = leave_one_group_out_fpca_influence(
        gaze,
        group_column="participant_id",
        n_components=3,
        scaling="dimension_sd",
    )

    influence.summary.sort_values(
        "influence_score",
        ascending=False,
    ).head()

In the synthetic truth case, the participant containing the deliberately atypical path should have the greatest influence on the component structure.

## Visual diagnostics

    plot_fpca_outlier_diagnostics(review)
    plot_fpca_influence(influence)

The first plot contrasts reconstruction unusualness with score-space unusualness. The second shows how much component structure changes under each group omission.

## Interpretation

The correct conclusion is **not** “delete the most influential participant.”

The correct conclusion is:

> This participant merits review because omitting their trials changes the estimated functional covariance structure more than omitting other participants.

Whether that reflects error or scientifically meaningful heterogeneity requires separate evidence.
