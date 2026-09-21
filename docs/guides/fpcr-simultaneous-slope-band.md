# Gaussian FPCR simultaneous slope bands

The paired Gaussian FPCR bootstrap introduced in 0.12 produces a full set of reconstructed functional-slope replicates.

Version 0.13 adds a post-calibration layer that turns those existing replicates into a studentized maximum-deviation band over the **observed slope grid**.

No second bootstrap is required.

## Start from the paired-bootstrap object

    inference = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

The calibration then uses <code>inference.bootstrap_slopes</code> directly.

## Global simultaneous scope

    global_band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="global",
    )

For each bootstrap replicate:

1. subtract the full-sample reference slope;
2. divide each observed grid cell by its bootstrap pointwise SE;
3. take the maximum absolute standardized deviation over all time × dimension cells.

The requested quantile of those replicate maxima becomes one critical value, used for every functional dimension.

This is the stronger of the two supported scopes.

## Dimension-wise simultaneous scope

    dimension_band = fpca_regression_slope_simultaneous_band(
        inference,
        confidence_level=0.95,
        simultaneous_scope="dimension",
    )

Here the maximum is taken over observed time separately within each functional dimension.

For planar gaze, x(t) and y(t) receive separate critical values.

This is simultaneous over sampled time within each dimension, not across both dimensions jointly.

## Why this is different from pointwise intervals

The 0.12 percentile intervals ask about each grid cell separately.

The 0.13 band calibrates against the largest studentized deviation across a declared grid family.

Under the same bootstrap replicates:

- the global band should be no narrower than the corresponding dimension-wise band;
- increasing the confidence level should not narrow the band.

These are explicit test contracts.

## Exact zero-variance handling

A slope grid cell can be invariant across all bootstrap refits.

If every replicate equals the reference slope at that cell, the pointwise SE is exactly zero and the simultaneous band is allowed to have zero width there.

The implementation computes SE from bootstrap **deviations from the reference**, avoiding numerical pseudo-variance when identical nonzero slope values are repeated many times.

If a grid cell has effectively zero bootstrap SE but a non-negligible discrepancy from the reference, calibration stops with an explicit error.

No epsilon is inserted to manufacture a finite standardized statistic.

## Observed-grid scope only

The calibration maximum is evaluated only on the time × dimension coordinates represented in the fitted FPCR object.

Therefore the package states:

> simultaneous over the observed grid

and does **not** state:

> simultaneous over the entire continuous functional domain.

A denser grid does not automatically establish the regularity conditions required for continuous-domain coverage.

## Not the operator-scaled FPCR significance test

Yeon (2026) establishes Gaussian and bootstrap approximations after a specific operator scaling of the FPCR estimator and develops slope-significance tests from that result.

The eyetrajectoriespy band is different.

It studentizes the finite-sample paired-bootstrap reconstructed slopes cell by cell and calibrates their observed-grid maximum.

Do not describe it as Yeon's operator-scaled test, as a formal inversion of that test, or as its continuous-domain confidence band.

## Relationship to other simultaneous functional bands

Simultaneous confidence bands have been developed for several functional-regression settings, including function-on-scalar and concurrent functional models. Those methods use model-specific theoretical constructions.

The 0.13 API is intentionally tied to the package's scalar-response Gaussian FPCR pipeline and the bootstrap distribution produced by 0.12.

## Reporting example

> The Gaussian FPCR slope was summarized with a 95% studentized simultaneous bootstrap band calibrated over the observed time-by-dimension grid. The band reused the 1,000 participant-level paired-bootstrap slope refits from the full FPCR analysis. For each replicate, absolute slope deviations were standardized by their pointwise bootstrap SEs and the maximum over all observed x(t)/y(t) grid cells was retained. The resulting band is simultaneous over the sampled slope grid only and does not imply continuous-domain coverage between sampled time points. The procedure is distinct from the operator-scaled FPCR significance test of Yeon (2026).

## API links

- <code>bootstrap_fpca_regression_uncertainty()</code>
- <code>fpca_regression_slope_simultaneous_band()</code>
- <code>FPCARegressionSlopeBandResult</code>
- <code>fpca_regression_slope_band_frame()</code>
- <code>plot_fpca_regression_slope_band()</code>
- <code>fpca_regression_slope_band_reporting_text()</code>

See [References](../methods/references.md).
