# W3 R23 — estimated covariance-component identifiability: original-source results

**Research-only evidence:** [draft PR #325](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/325), [original 576-case research run #38699204234](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38699204234), original source head `80d66502a94e719841ad3d4aeabc3e192202a7b1`. Seed `202610153301` and **12 independent generating blocks**; nested n=24,48,96; ordinary/extreme support × predictor-independent/dependent sources; Legendre-5/cubic-spline-13; separately fitted shared/predictor-scaled nuisance covariance structures. **576 paired evaluations, not 576 independent replications.** Source completed 576/576 with **0 source generation failures, 0 estimator failures, 0 scaled-Cholesky refusals and 0 sensor floors**. The dedicated design/ledger tests passed on Python 3.11, 3.12, 3.13. The complete exact-head repository matrix should be checked separately after this results-document change.

All four variance-component moment operators had *algebraic rank four* according to the existing numerical rank test. This does NOT prove adequate statistical recovery: the source study was explicitly designed to examine component identification, not interval coverage.

## Original outcome across all 576 evaluations

| Component | Estimated at zero | Among 288 structurally matched cases |
|---|---:|---:|
| Participant intercept | 84/576 | 54/288 |
| Participant random slope | 192/576 | 72/288 |
| Trial-level innovation | 282/576 | 140/288 |
| Sensor innovation | 0/576 | 0/288 |

All 576 computations passed the proposed R22 scale-normalized numerical test, with *no* sensor floors, compared with R20's prior **41 historical failures out of 256**. This is a new seed/design with different source blocks, and should **not** be interpreted as successful reclassification, a controlled method improvement rate or nominal coverage. Sensor estimates were never zero in the new source, but other source components frequently hit the NNLS boundary.

The approximate groupwise moment-fit residuals are 0.81–0.85 as a fraction of the raw fitted-residual outer-product norms, which contain high stochastic noise. Large values are not automatically evidence of model misspecification or an invalid covariance estimator. The stronger concern is nontrivial boundary frequency despite positive generating components, including in structurally matched model-family pairs.

## All prespecified source × sample × basis × working-family cells

Each row has exactly 12 independent generating blocks as its denominator. Matched indicates whether the candidate covariance structure reproduces the *generating source family* (simulation-only label, never supplied to the estimator). The four 'zero' columns are counts out of 12. For matched designs, median relative component recovery error reports absolute difference divided by the simulation-known generating component variance, with no attempt to pool dependent observations as independent evidence.

| Participants | Source mechanism | Mean basis | Fitted family | Matched | Zero intercept | Zero slope | Zero trial | Median NNLS moment residual | Median moment operator cond. | Median relative intercept/slope/trial recovery error |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| 24 | ordinary_independent | legendre5 | shared_slope | Yes | 5 | 3 | 4 | 0.82 | 145.73 | 0.89/2.11/0.99 |
| 24 | ordinary_independent | legendre5 | predictor_scaled_slope | No | 0 | 4 | 3 | 0.82 | 3.93 | — |
| 24 | ordinary_independent | cubic_spline13 | shared_slope | Yes | 5 | 3 | 4 | 0.82 | 145.76 | 0.88/2.21/0.99 |
| 24 | ordinary_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 4 | 3 | 0.82 | 3.93 | — |
| 24 | ordinary_dependent | legendre5 | shared_slope | No | 3 | 3 | 8 | 0.83 | 145.73 | — |
| 24 | ordinary_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 5 | 8 | 0.81 | 3.93 | 0.27/1.00/1.00 |
| 24 | ordinary_dependent | cubic_spline13 | shared_slope | No | 3 | 3 | 8 | 0.83 | 145.76 | — |
| 24 | ordinary_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 5 | 8 | 0.81 | 3.93 | 0.27/1.00/1.00 |
| 24 | extreme_independent | legendre5 | shared_slope | Yes | 5 | 3 | 4 | 0.81 | 145.65 | 0.87/2.24/1.00 |
| 24 | extreme_independent | legendre5 | predictor_scaled_slope | No | 0 | 7 | 4 | 0.81 | 3.16 | — |
| 24 | extreme_independent | cubic_spline13 | shared_slope | Yes | 5 | 3 | 4 | 0.81 | 145.68 | 0.87/2.24/1.00 |
| 24 | extreme_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 7 | 4 | 0.81 | 3.16 | — |
| 24 | extreme_dependent | legendre5 | shared_slope | No | 2 | 4 | 7 | 0.83 | 145.65 | — |
| 24 | extreme_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 3 | 6 | 0.82 | 3.16 | 0.18/0.86/1.00 |
| 24 | extreme_dependent | cubic_spline13 | shared_slope | No | 2 | 4 | 7 | 0.83 | 145.68 | — |
| 24 | extreme_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 3 | 6 | 0.82 | 3.16 | 0.18/0.86/1.00 |
| 48 | ordinary_independent | legendre5 | shared_slope | Yes | 4 | 2 | 6 | 0.83 | 145.47 | 0.65/1.84/1.00 |
| 48 | ordinary_independent | legendre5 | predictor_scaled_slope | No | 0 | 6 | 6 | 0.82 | 3.78 | — |
| 48 | ordinary_independent | cubic_spline13 | shared_slope | Yes | 4 | 2 | 6 | 0.83 | 145.49 | 0.65/1.84/1.00 |
| 48 | ordinary_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 6 | 6 | 0.82 | 3.78 | — |
| 48 | ordinary_dependent | legendre5 | shared_slope | No | 3 | 5 | 7 | 0.85 | 145.47 | — |
| 48 | ordinary_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 4 | 7 | 0.85 | 3.78 | 0.05/1.00/1.00 |
| 48 | ordinary_dependent | cubic_spline13 | shared_slope | No | 3 | 5 | 7 | 0.85 | 145.49 | — |
| 48 | ordinary_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 4 | 7 | 0.85 | 3.78 | 0.05/1.00/1.00 |
| 48 | extreme_independent | legendre5 | shared_slope | Yes | 4 | 2 | 6 | 0.83 | 145.44 | 0.59/1.38/1.00 |
| 48 | extreme_independent | legendre5 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.82 | 3.11 | — |
| 48 | extreme_independent | cubic_spline13 | shared_slope | Yes | 4 | 2 | 6 | 0.83 | 145.45 | 0.59/1.36/1.00 |
| 48 | extreme_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.82 | 3.11 | — |
| 48 | extreme_dependent | legendre5 | shared_slope | No | 3 | 5 | 8 | 0.85 | 145.44 | — |
| 48 | extreme_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 4 | 7 | 0.84 | 3.11 | 0.15/0.43/1.00 |
| 48 | extreme_dependent | cubic_spline13 | shared_slope | No | 3 | 5 | 8 | 0.85 | 145.45 | — |
| 48 | extreme_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 4 | 7 | 0.84 | 3.11 | 0.15/0.43/1.00 |
| 96 | ordinary_independent | legendre5 | shared_slope | Yes | 4 | 2 | 5 | 0.83 | 145.81 | 0.67/1.90/0.93 |
| 96 | ordinary_independent | legendre5 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.83 | 3.79 | — |
| 96 | ordinary_independent | cubic_spline13 | shared_slope | Yes | 4 | 2 | 5 | 0.83 | 145.81 | 0.67/1.89/0.94 |
| 96 | ordinary_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.83 | 3.79 | — |
| 96 | ordinary_dependent | legendre5 | shared_slope | No | 2 | 2 | 5 | 0.85 | 145.81 | — |
| 96 | ordinary_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 2 | 5 | 0.85 | 3.79 | 0.14/0.90/1.00 |
| 96 | ordinary_dependent | cubic_spline13 | shared_slope | No | 2 | 2 | 5 | 0.85 | 145.81 | — |
| 96 | ordinary_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 2 | 5 | 0.85 | 3.79 | 0.14/0.90/1.00 |
| 96 | extreme_independent | legendre5 | shared_slope | Yes | 5 | 2 | 7 | 0.83 | 145.81 | 0.61/1.66/1.00 |
| 96 | extreme_independent | legendre5 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.83 | 3.20 | — |
| 96 | extreme_independent | cubic_spline13 | shared_slope | Yes | 5 | 2 | 7 | 0.83 | 145.81 | 0.61/1.65/1.00 |
| 96 | extreme_independent | cubic_spline13 | predictor_scaled_slope | No | 0 | 7 | 6 | 0.83 | 3.20 | — |
| 96 | extreme_dependent | legendre5 | shared_slope | No | 2 | 3 | 5 | 0.85 | 145.81 | — |
| 96 | extreme_dependent | legendre5 | predictor_scaled_slope | Yes | 0 | 4 | 5 | 0.85 | 3.20 | 0.14/0.64/1.00 |
| 96 | extreme_dependent | cubic_spline13 | shared_slope | No | 2 | 3 | 5 | 0.85 | 145.81 | — |
| 96 | extreme_dependent | cubic_spline13 | predictor_scaled_slope | Yes | 0 | 4 | 5 | 0.85 | 3.20 | 0.14/0.64/1.00 |

## Interpretation and next numerical-statistical diagnostic

A rank-four kernel operator and a positive-definite covariance matrix are **necessary algebraic checks**, but not sufficient for practically identifiable nonnegative variance components. In structurally matched cases, median absolute relative slope and trial error is often large; in several cells, half or more of the estimated trial variances are zero despite the generator's positive trial component. Increasing participant count from 24 to 96 did not simply eliminate the boundary problem.

The present NNLS objective fits noisy participant residual outer products after adjusting the *expected residual covariance* for leverage, i.e., a mathematically motivated moment estimator rather than a demonstrated efficient component estimator. Its residual-fit ratio cannot separate finite-sample outer-product noise from misspecification. A more decisive subsequent R23/R24 diagnostic should test (a) the **population moment operator at known variance coefficients** under fixed native design, (b) the distribution and covariance of observable residual moments, (c) zero-frequency and component-recovery behavior under independent conditional innovations with the design held fixed, and (d) declared alternative objectives/regularization choices *without selecting a convenient answer after observing these outcomes*. Independent analytical covariance score information and parameter sensitivity would strengthen component-identification claims.

A larger, independently seeded inferential calibration would remain necessary even if covariance components could be recovered: the proposed conditional Satterthwaite df does **not** account for covariance-estimation uncertainty. No truth-inclusion or confidence-interval coverage values were computed in R23. Consequently `estimated_covariance_inference_qualified=false`, `simultaneous_bands_qualified=false`, `release_authorized=false`; scientific blockers #289 and #296 remain open. Protected main, the supported public API, version 1.2 tags and PyPI are unchanged.
