# W3 R46 — independent-block MAR propensity-bootstrap uncertainty and positivity stress

**Research-only, predeclared exploratory pointwise coverage comparison.** The methods and fixed numerical denominators were frozen before examining original R46 scientific outcomes. There is no fitted-covariance-adjusted CR2 claim, no simultaneous functional 90% band, no MNAR correction, and no release authorization.

## Why R46 is a separate scientific step

[R45](w3-r45-observed-propensity-pointwise-results.md) used **12 independent Gaussian primitive blocks**, paired into 96 source variants, and found that under its observed-design MAR dropout the fitted logistic-propensity IPW did **not** improve finite-source mean absolute focal-slope error relative to unadjusted weighted regression. Its participant-cluster **CR1 pointwise** intervals treated estimated propensity as fixed; observed nominal 90% truth inclusion could not be called calibrated coverage.

R46 examines uncertainty from estimating the MAR propensity, with new primitive source draws and transparent alternative propensity mechanisms. An observed MAR schedule is assumed to include original participant/trial identities, scheduled timestamps, predictors, and retention indicators even for the missing gaze measurements. The missing gaze values are `NaN`; the fitted propensity cannot access them.

## Frozen source and observation design

New primitive Gaussian master seed **202610164646**, dropout master seed **202610164647**, participant-bootstrap master seed **202610164648**, separate from all earlier studies. Generate **32 independent primitive blocks**, **n=36 participants per block**, each with native irregular trials; within each block pair ordinary/extreme predictor support and generating exact-zero/positive participant random-slope states, where the zero state removes the slope innovation from the reconstructed genuine Gaussian response. These are **128 paired source variants, not 128 independent primitive blocks**.

For each variant, evaluate three purely **observed-design MAR** point-retention mechanisms:

- **Matched logistic:** `logit p = 1.2 - 0.9 q - 0.7t`
- **Nonlinear/misspecified logistic:** `logit p = 1.2 - 0.9 q - 0.7t - 2(qt) - 1.4(t-0.5)^2`
- **Weak-overlap design:** `logit p = -1.5 - 2q - 2.5t`

where `q=|x|/(1+|x|)`. Native trial endpoints are retained with probability exactly one. Bernoulli retention of interior points depends **only on scheduled predictor/time**, and the fitted model is deliberately restricted to `1,q,t`, so it is correctly specified for the first and third regimes and misspecified for the second. Fitted probabilities are clipped below at the frozen threshold **0.05** in the IPW estimator. Clipping may stabilize the numerical estimator but changes its estimand/finite-sample properties and does not prove positivity.

Only native observed gaze responses enter point-estimation and variance calculations. All scheduled `R,x,t` enter the propensity model. No source innovations, generating coefficients, missing gaze values, true propensity probabilities, or excluded outcomes can enter the estimator.

## Frozen methods and resampling policy

All methods estimate the **generating fixed function-on-scalar predictor slope at original focal time** from the retained native data, using Legendre-five basis and the participant-balanced WLS contracts:

1. **Naïve observed WLS CR1**, no missingness adjustment; participant-cluster CR1 with the original Student-t df correction yields an exploratory 90% pointwise interval.
2. **Fitted observed-design MAR IPW with fixed-weight CR1**, using a Bernoulli logistic GLM on scheduled interior `R,q,t` with ridge **1e-5**, Newton limit **45**, predicted probability floor **0.05**, endpoint probability one, and fixed native-schedule participant/trial balancing. The CR1 variance **treats the fitted weights as fixed**.
3. **Fitted MAR IPW with whole-participant pairs bootstrap and propensity refit**, retaining all original scheduled observations and missing indicators from each resampled participant, refitting the logistic propensity in **every bootstrap replicate**, then recalculating the weighted focal slope. Freeze **79 participant-level resamples per source/regime case**, seeded independently but reproducibly, without substituting successful resamples when a fit fails. A percentile **5%–95%** interval is constructed only if all 79 prespecified resampled fits succeed. An incomplete bootstrap explicitly fails instead of dropping unfavorable resamples. This percentile interval is **not a studentized, bootstrap-t, BCa, CR2, or simultaneous interval**.

Never resample timestamps independently or allow the original fitted propensity to carry over into the “refit” method. All bootstrap trial multiplicities, masked response `NaN` values, observed schedule and selection indicators must be preserved exactly.

**Frozen denominator:** 32 primitive blocks × 2 paired predictor supports × 2 paired true slope states = **128 source variants**; × 3 observed-design dropout mechanisms = **384 source/regime cases**, × 3 interval methods = **1,152 planned pointwise interval records**, and **384 × 79 = 30,336 individual bootstrap-fit attempts**. Every slot—including source exceptions, failed logistic fits, rank failures, refused resamples, and missing intervals—must be in the original evidence ledger. The full source-denominator checks may fail a scientific job while the `if: always()` artifact retains the original failure counts.

## Frozen interpretation and independent-source limitations

Compare descriptive mean absolute point-estimation error against generating focal-slope truth, mean interval width, truth-inclusion numerator and denominator, observed interior retention, bootstrap success/failure count and propensity positivity diagnostics **separately by source/regime/method**. Do not infer population-level superiority from paired counts without handling source-level clustering, or relabel the three regimes as different independent populations.

With only **32 independent primitive blocks**, this remains an **exploratory** coverage pilot. Observed truth-inclusion rates—even when close to 90%—cannot qualify a public 90% pointwise statistical method. Moreover, a percentile participant bootstrap can have finite-sample bias, and refitting the observation propensity does not automatically validate nuisance-adjusted covariance estimation or a CR2/Satterthwaite reference law. Misspecification and clipping can invalidate a theoretical inverse-probability interpretation. Neither this pilot nor MAR identification resolves loss depending on potentially missing gaze responses or selection of whole participants on latent outcomes.

Future inferential qualification requires many more **independent** primitive blocks, model and positivity sensitivity, refit-propensity uncertainty validation, separate fitted-working-covariance-aware CR2 inference, and **independent nominal 90% simultaneous function-wide band calibration**; variance-component null boundary testing requires a distinct study.

Keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**. Retain all original R20/R22/R33–R45 unfavorable findings. No supported inference API, protected-main merge, version 1.2 tag, or PyPI publication.
