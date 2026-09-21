# Worked example: Gaussian FPCR simultaneous slope band

This example reuses an existing paired-bootstrap Gaussian FPCR fit and calibrates an observed-grid simultaneous slope band.

## Fit the paired bootstrap

    import numpy as np

    from eyetrajectoriespy import (
        bootstrap_fpca_regression_uncertainty,
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
        + generator.normal(0.0, 0.35, size=gaze.n_curves)
    )

    inference = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=500,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

## Calibrate one band across x and y

    from eyetrajectoriespy import fpca_regression_slope_simultaneous_band

    global_band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="global",
    )

One critical value is used across all sampled time × dimension cells.

## Compare per-dimension calibration

    dimension_band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="dimension",
    )

For the same bootstrap slope replicates, the global critical value is at least as conservative as the separate x/y critical values.

## Inspect the long-form band

    from eyetrajectoriespy import fpca_regression_slope_band_frame

    table = fpca_regression_slope_band_frame(global_band)
    print(table.head())

## Plot one dimension

    from eyetrajectoriespy import plot_fpca_regression_slope_band

    plot_fpca_regression_slope_band(
        global_band,
        dimension="x",
    )

## Generate manuscript wording

    from eyetrajectoriespy import fpca_regression_slope_band_reporting_text

    print(fpca_regression_slope_band_reporting_text(global_band))

## Interpretation

The band can support statements about the reconstructed slope across the **sampled grid family**.

It does not justify statements about unobserved times between grid points without additional theory.

It also does not replace the operator-scaled FPCR slope-significance test from recent asymptotic work.

## Next steps

- [Gaussian FPCR simultaneous slope bands](../guides/fpcr-simultaneous-slope-band.md)
- [Gaussian FPCR bootstrap uncertainty](../guides/fpcr-bootstrap-inference.md)
- [Predictive FPC selection](../guides/predictive-component-selection.md)
- [Reporting checklist](../methods/reporting.md)
