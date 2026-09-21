# Gaussian FPCR bootstrap uncertainty

Scalar-on-function functional principal-component regression (FPCR) is often implemented as a two-stage estimator: first estimate an FPCA/MFPCA basis, then regress the scalar outcome on retained FPC scores.

A conventional score regression conditions on the estimated basis. When the functional slope or fitted mean response is itself a scientific result, that conditioning can understate uncertainty contributed by re-estimating the functional representation.

Use <code>bootstrap_fpca_regression_uncertainty()</code> for a transparent paired-bootstrap layer around the package's Gaussian FPCR pipeline.

## Estimand

The fitted model is a scalar response linked to the centered functional predictor through a functional slope. The finite FPCR approximation uses a fixed number of empirical FPCs.

The API returns uncertainty summaries for:

- the reconstructed functional slope for each functional dimension;
- the fitted conditional mean response for fixed target trajectories.

## What is resampled

The functional predictor and scalar outcome are resampled **together**.

For independent trajectories:

    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=1000,
        n_components=2,
        resample_unit="curve",
        random_state=2026,
    )

For repeated trials clustered within participant:

    result = bootstrap_fpca_regression_uncertainty(
        gaze,
        outcome,
        n_bootstrap=1000,
        n_components=2,
        resample_unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

Participant resampling copies all trials and their paired outcomes for each sampled participant.

## Full refit in every bootstrap replicate

Each replicate performs a complete refit:

1. resample the independent unit and outcome together;
2. refit FPCA/MFPCA;
3. recompute scores;
4. refit the Gaussian score regression;
5. reconstruct the functional slope;
6. project fixed targets into that bootstrap basis;
7. compute fitted conditional means.

No bootstrap replicate reuses the full-sample FPCA basis.

## Why FPC label matching is not required here

For FPC-shape or individual-score uncertainty, sign alignment and component matching are essential because an individual FPC label is the inferential target.

The FPCR slope is different. If one retained FPC changes sign, its regression coefficient changes sign too, leaving their contribution to the reconstructed slope unchanged. A permutation or rotation inside a fully retained subspace is likewise absorbed by the associated regression coefficients.

Therefore the inferential target is the **reconstructed complete slope**, not an intermediate FPC coefficient label.

This invariance does not eliminate truncation sensitivity near the retained/excluded boundary.

## Mapping back to original trajectory units

With <code>scaling="dimension_sd"</code>, MFPCA uses standardized functional channels.

For a channel scale s_d, the package's score geometry implies that the original-unit slope is reconstructed as:

    beta_d(t) = sum_j b_j * phi_jd(t) / s_d^2

where b_j is the Gaussian regression coefficient for FPC j and phi_jd(t) is the stored component trajectory.

The implementation uses this mapping explicitly rather than plotting raw FPC regression coefficients as if they were a functional slope.

## Fixed component count

The retained component count is **not reselected inside bootstrap replicates**.

This isolates sampling variability conditional on the declared truncation dimension.

If the component count was selected by reconstruction CV or outcome-tuned nested CV, report that selection procedure separately. The 0.12 bootstrap does not claim to incorporate model-selection uncertainty.

## Pointwise slope envelopes

The lower/upper slope summaries are empirical percentile intervals at each observed time × functional-dimension coordinate.

They are not simultaneous confidence bands over the whole functional domain.

Do not interpret exclusion of zero at one time point as a multiplicity-adjusted global significance test.

## Fixed-target mean-response intervals

Pass compatible targets:

    result = bootstrap_fpca_regression_uncertainty(
        training_gaze,
        outcome,
        targets=new_gaze,
        n_bootstrap=1000,
        n_components=2,
        scaling="dimension_sd",
        random_state=2026,
    )

The target trajectories remain fixed while the training predictor/outcome pairs are resampled.

The resulting intervals quantify uncertainty in the **estimated conditional mean response** for each target.

They are not prediction intervals for a future observed outcome because residual outcome noise is not added to target predictions.

## Rank-deficient bootstrap replicates

Paired resampling can occasionally produce too little independent variation for the requested FPCR dimension.

eyetrajectoriespy does not silently discard such replicates.

If the reference or a bootstrap regression design is rank deficient, the function stops with the replicate number and asks the analyst to reduce the component count or use a larger/more variable independent-unit sample.

Discard-and-redraw would silently change the bootstrap distribution.

## Gaussian-only scope

The point-estimation helper <code>fit_scalar_on_function_regression()</code> supports Gaussian and binomial families.

The 0.12 bootstrap API intentionally supports **Gaussian scalar-on-function regression only**. Functional logistic/binomial inference has different theoretical and convergence issues and is not implied by the Gaussian bootstrap.

## Relationship to current methodology

González-Manteiga and Martínez-Calvo (2011) developed bootstrap pointwise inference for FPCA-based functional linear regression.

A 2026 FPCR theory paper by Yeon establishes Gaussian and bootstrap approximations for an **operator-scaled** FPCR estimator and uses them for slope-significance testing. It emphasizes that ordinary scalar scaling of the full FPCR slope does not yield the usual central limit theorem and that operator scaling is essential for its formal test.

The eyetrajectoriespy 0.12 routine is **not** an implementation of that operator-scaled test. It is a paired nonparametric full-pipeline bootstrap that exposes finite-sample variability of the package's Gaussian FPCR slope and fixed-target conditional means.

## Reporting example

> Gaussian scalar-on-function FPCR uncertainty was evaluated using 1,000 participant-level paired bootstrap resamples. In each replicate, participants and their trial-level outcomes were resampled together, dimension-SD-scaled MFPCA was refitted with two prespecified components, and the Gaussian score regression was refitted. The functional slope was reconstructed in the original x/y coordinate units. Ninety-five-percent pointwise percentile intervals were reported for the slope. For six fixed target trajectories, bootstrap intervals describe uncertainty in the fitted conditional mean response and not prediction intervals for future noisy outcomes. Component count was held fixed across bootstrap replicates.

## Related APIs

- <code>fit_scalar_on_function_regression()</code>
- <code>bootstrap_fpca_regression_uncertainty()</code>
- <code>fpca_regression_slope_uncertainty_frame()</code>
- <code>fpca_regression_prediction_uncertainty_frame()</code>
- <code>plot_fpca_regression_slope_uncertainty()</code>
- <code>plot_fpca_regression_mean_prediction_uncertainty()</code>
- <code>cross_validate_fpca_regression()</code>
- <code>nested_cross_validate_fpca_regression()</code>

See [References](../methods/references.md).
