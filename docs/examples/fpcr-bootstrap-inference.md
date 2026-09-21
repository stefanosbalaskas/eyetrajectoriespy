# Worked example: Gaussian FPCR bootstrap uncertainty

This example models a scalar outcome from repeated-trial planar gaze trajectories and propagates paired sampling variability through both MFPCA and the Gaussian regression.

## Simulate functional predictors

    import numpy as np

    from eyetrajectoriespy import (
        fit_mfpca,
        simulate_planar_trajectories,
    )

    gaze = simulate_planar_trajectories(
        n_participants=24,
        trials_per_participant=2,
        n_time=61,
        random_state=2026,
    )

## Create a reproducible scalar outcome

For the synthetic demonstration, generate an outcome from two fitted FPC score coordinates plus noise:

    generator = np.random.default_rng(2026)

    reference = fit_mfpca(
        gaze,
        n_components=2,
        scaling="dimension_sd",
    )

    outcome = (
        1.0
        + 1.4 * reference.scores[:, 0]
        - 0.6 * reference.scores[:, 1]
        + generator.normal(0.0, 0.35, size=gaze.n_curves)
    )

In real research the outcome is observed independently of this fitting step; this construction exists only to provide a compact synthetic truth-oriented example.

## Paired participant bootstrap

    from eyetrajectoriespy import bootstrap_fpca_regression_uncertainty

    inference = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        targets=gaze.subset([0, 1, 2, 3, 4, 5]),
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        level=0.95,
        random_state=2026,
    )

The component count is held fixed at two in every replicate.

## Inspect the functional slope

    from eyetrajectoriespy import fpca_regression_slope_uncertainty_frame

    slope = fpca_regression_slope_uncertainty_frame(inference)
    print(slope.head())

The slope is reported in the original functional-predictor coordinate system. With multichannel scaling, the API performs the required back-transformation rather than interpreting raw FPC regression coefficients as slopes.

## Plot one functional dimension

    from eyetrajectoriespy import plot_fpca_regression_slope_uncertainty

    plot_fpca_regression_slope_uncertainty(
        inference,
        dimension="x",
    )

The envelope is pointwise, not simultaneous over time.

## Inspect fixed-target conditional means

    from eyetrajectoriespy import (
        fpca_regression_prediction_uncertainty_frame,
        plot_fpca_regression_mean_prediction_uncertainty,
    )

    prediction = fpca_regression_prediction_uncertainty_frame(inference)
    print(prediction)

    plot_fpca_regression_mean_prediction_uncertainty(
        inference,
        max_targets=6,
    )

These are intervals for the fitted conditional mean response of the six fixed trajectories.

They are **not** prediction intervals for future observed outcomes.

## Generate reporting language

    from eyetrajectoriespy import fpca_regression_uncertainty_reporting_text

    print(fpca_regression_uncertainty_reporting_text(inference))

## Interpretation checklist

Before interpreting the slope:

1. verify the bootstrap unit matches the independent sampling unit;
2. report how the FPC count was chosen;
3. remember that the bootstrap keeps that count fixed;
4. treat slope envelopes as pointwise;
5. distinguish conditional-mean intervals from future-outcome prediction intervals;
6. do not generalize the Gaussian inference to binomial models;
7. if the requested component dimension repeatedly causes rank-deficient bootstrap samples, reconsider the model dimension rather than deleting failed replicates.

## Next steps

- [Gaussian FPCR bootstrap uncertainty](../guides/fpcr-bootstrap-inference.md)
- [Predictive FPC selection](../guides/predictive-component-selection.md)
- [FPC score basis uncertainty](../guides/score-uncertainty.md)
- [FPCA spectrum uncertainty](../guides/spectrum-uncertainty.md)
- [Reporting checklist](../methods/reporting.md)
