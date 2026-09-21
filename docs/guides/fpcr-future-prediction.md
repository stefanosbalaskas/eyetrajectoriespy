# Gaussian FPCR future-outcome prediction

The paired Gaussian FPCR bootstrap distinguishes two prediction targets:

1. the **conditional mean response** for a fixed functional trajectory;
2. a **future observed scalar outcome** for that trajectory.

These are not the same inferential object.

## Conditional-mean uncertainty

The 0.12 API

    bootstrap_fpca_regression_uncertainty(...)

refits FPCA/MFPCA and the Gaussian score regression in every paired bootstrap sample, then predicts each fixed target trajectory.

Its target interval summarizes uncertainty in the fitted conditional mean.

It does not add future response noise.

## Future-outcome uncertainty

The 0.14 API starts from the same paired-bootstrap object:

    future = fpca_regression_future_prediction_interval(
        inference,
        outcome,
        confidence_level=0.95,
        random_state=2026,
    )

For each bootstrap replicate and fixed target it computes:

    future draw = bootstrap conditional mean + sampled centered residual

The residual draw is independent of the paired resampling already represented in the stored conditional-mean bootstrap distribution.

## Why a second uncertainty component is needed

A conditional mean describes the expected scalar response at a fixed functional predictor.

A future observed response also includes the model error term.

Cai and Hall (2006) emphasize that functional-linear prediction has properties distinct from slope-function estimation. Bootstrap work on functional linear regression has separately studied residual and paired resampling for prediction.

The 0.14 implementation makes the two uncertainty components visible rather than relabeling a conditional-mean interval as a prediction interval.

## Residual construction

The full-sample Gaussian FPCR training residuals are

    residual_i = observed outcome_i - fitted outcome_i

The empirical residual pool is centered before sampling.

The centered pool is retained in the result object, as is every sampled residual used to construct a future predictive draw.

No residual is silently standardized, winsorized, trimmed, or replaced by a parametric Gaussian draw.

## Exchangeability assumption

The residual-resampling step assumes that one centered empirical residual distribution is appropriate for the future target response.

This is a common/exchangeable residual assumption.

If response variance changes systematically with the functional predictor, fitted mean, condition, participant, or another covariate, the pooled residual distribution may be inappropriate.

Recent 2026 work on functional-linear mean-response inference specifically notes that ordinary residual bootstrap can fail under heterogeneous errors and develops a wild-bootstrap alternative.

eyetrajectoriespy 0.14 does **not** claim that robustness.

## Participant-level paired bootstrap

The underlying FPCR uncertainty object can use participant-level paired resampling so that repeated functional trajectories are not treated as independent participants during model refitting.

The 0.14 residual draw is still a marginal response-noise draw from the pooled centered residual distribution.

Therefore the resulting intervals are marginal per target. They do not model a joint residual correlation structure for multiple future trials from the same participant.

## Fixed target trajectories

The predictive API operates on whatever fixed target trajectories were supplied to the 0.12 bootstrap fit.

For a scientifically clean prediction workflow, external compatible targets are usually preferable to training targets.

The target trajectories themselves remain fixed. The 0.14 method does not add target measurement error, latent-trajectory uncertainty, preprocessing uncertainty, or future-functional-predictor uncertainty.

## Marginal, not simultaneous

Each target receives a marginal percentile prediction interval.

The package does not claim:

- simultaneous coverage over all supplied targets;
- a joint multivariate prediction region;
- familywise calibration across targets.

## Component selection remains fixed

The retained FPC count is inherited from the underlying 0.12 object and remains fixed.

If component count was selected from the same dataset, its selection uncertainty is not automatically included.

## Relationship to paired-bootstrap prediction literature

Khademnoe and Hosseini-Nasab (2016) study percentile bootstrap intervals for prediction in functional linear regression using paired resampling and distinguish the model-refit resampling from response-error resampling.

The eyetrajectoriespy implementation is deliberately transparent and finite-sample oriented: it reuses the exact paired-bootstrap mean predictions already retained by the package, then independently samples centered full-sample residuals.

It should not be described as a universal optimal prediction interval or a heteroscedasticity-robust procedure.

## Reporting example

> Future scalar responses for six fixed target gaze trajectories were summarized with 95% marginal Gaussian FPCR prediction intervals. The predictive distribution reused 1,000 participant-level paired-bootstrap conditional-mean predictions and added independent draws from the centered empirical residual distribution of the full-sample FPCR fit. The residual-resampling step assumes a common exchangeable response-error distribution; the intervals were not interpreted as heteroscedasticity-robust, simultaneous across targets, or a joint prediction region.

## API links

- <code>bootstrap_fpca_regression_uncertainty()</code>
- <code>FPCARegressionPredictionIntervalResult</code>
- <code>fpca_regression_future_prediction_interval()</code>
- <code>fpca_regression_future_prediction_frame()</code>
- <code>plot_fpca_regression_future_prediction_interval()</code>
- <code>fpca_regression_future_prediction_reporting_text()</code>

See [References](../methods/references.md).
