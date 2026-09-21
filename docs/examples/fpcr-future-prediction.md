# Worked example: Gaussian FPCR future-outcome prediction

This example contrasts uncertainty in a fitted conditional mean with uncertainty for a future observed scalar response.

## Simulate functional predictors and an outcome

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

    reference = fit_mfpca(
        gaze,
        n_components=2,
        scaling="dimension_sd",
    )

    generator = np.random.default_rng(2026)
    outcome = (
        1.0
        + 1.4 * reference.scores[:, 0]
        - 0.6 * reference.scores[:, 1]
        + generator.normal(0.0, 0.6, size=gaze.n_curves)
    )

## Fit paired-bootstrap conditional-mean uncertainty

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
        random_state=2026,
    )

The stored <code>prediction_lower</code> and <code>prediction_upper</code> fields describe the fitted conditional mean.

## Add future response noise

    from eyetrajectoriespy import fpca_regression_future_prediction_interval

    future = fpca_regression_future_prediction_interval(
        inference,
        outcome,
        confidence_level=0.95,
        random_state=2026,
    )

Every future predictive draw is the corresponding bootstrap conditional mean plus one independently sampled centered training residual.

## Inspect the table

    from eyetrajectoriespy import fpca_regression_future_prediction_frame

    table = fpca_regression_future_prediction_frame(future)
    print(table)

The table keeps the conditional-mean interval and future-outcome interval side by side.

## Plot prediction intervals

    from eyetrajectoriespy import plot_fpca_regression_future_prediction_interval

    plot_fpca_regression_future_prediction_interval(
        future,
        max_targets=6,
    )

## Generate reporting language

    from eyetrajectoriespy import fpca_regression_future_prediction_reporting_text

    print(fpca_regression_future_prediction_reporting_text(future))

## Interpretation checklist

Before calling the interval a future-outcome prediction interval:

1. confirm the underlying model is Gaussian FPCR;
2. report how the FPC count was chosen;
3. verify the underlying paired-bootstrap unit;
4. inspect residual heterogeneity rather than assuming pooled residual exchangeability automatically;
5. remember that the target trajectory is treated as fixed;
6. do not call the intervals simultaneous or joint across targets;
7. do not claim target measurement-error or preprocessing uncertainty is included.

## Next steps

- [Gaussian FPCR future-outcome prediction](../guides/fpcr-future-prediction.md)
- [Gaussian FPCR bootstrap uncertainty](../guides/fpcr-bootstrap-inference.md)
- [Gaussian FPCR simultaneous slope bands](../guides/fpcr-simultaneous-slope-band.md)
- [Reporting checklist](../methods/reporting.md)
