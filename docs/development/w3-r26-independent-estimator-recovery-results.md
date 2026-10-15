# R26 — independent 16-block Gaussian REML versus NNLS covariance-recovery replication

**Original research:** [draft PR #328](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/328), [scientific run #38703326033](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38703326033), original research head `6a681cca0e66200b15bde51480a1e216f38a3d49`. The dedicated independent-source study and source-contract jobs passed, along with **24/24 exact-head repository workflows** before this article commit. New seed `202610153626`, **16 independent generating blocks**, nested n24/n48/n96; four prespecified predictor support × source covariance mechanisms, one Legendre-5 mean basis and both candidate working covariance families. **384 paired cases** evaluated, zero source generation failures, zero missing, zero NNLS or REML fit failures.

The original scientific [artifact #11957955618](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38703326033/artifacts/11957955618) preserves all 384 case records, original source checkout SHA, summary and SHA256SUMS. The three named artifact source files independently passed their SHA256 checks after retrieval. The original R20 pilot's 41/256 failures and R22's 32 new numerical refusals are historical, unchanged findings on different source seeds.

## Predeclared common near-zero threshold (simulation-only)

Original NNLS allows exactly zero variance estimates; Gaussian REML uses bounded positive log parameters, so comparing raw zeros alone would favor REML mechanically. **Only AFTER both estimators fitted the same observed source data**, and exclusively on **192 matching source/fitted-family cases**, we classified `variance estimate < 0.05 × known generating variance`. The generator variances were never supplied to either estimator.

| Component | NNLS below 5% generating variance | REML below 5% generating variance |
|---|---:|---:|
| Participant intercept | 19 / 192 | 23 / 192 |
| Participant slope | 85 / 192 | 52 / 192 |
| Trial variance | 88 / 192 | 0 / 192 |
| Sensor variance | 1 / 192 | 0 / 192 |

Even when applying this same threshold, REML showed fewer near-zero slope and trial estimates but **not** intercept estimates. However, fewer near-zero values does not prove more accurate estimation; accuracy must be assessed jointly with overestimation, dispersion, bias, boundary behavior and source-block uncertainty.

## Matched-family recovery: paired block-level error difference

For each matched pair, absolute relative component error is `|estimated variance / generating variance − 1|`. Within each of the 16 genuinely independent generating blocks, average the error difference REML minus NNLS over the prespecified three sample sizes and four source mechanisms; then resample **whole generating blocks** 2,500 times. These are paired bootstrap **method-recovery** intervals, not coverage intervals or confidence intervals for gaze effects.

| Component | Mean REML − NNLS error | 95% whole-block bootstrap interval | Interpretation |
|---|---:|---:|---|
| participant intercept | 0.024 | -0.020 to 0.076 | Neither method clearly favored |
| participant slope | -0.022 | -0.169 to 0.175 | Neither method clearly favored |
| trial | -1.830 | -2.748 to -1.111 | REML improved under the matched Gaussian source |
| sensor | -0.112 | -0.167 to -0.060 | REML improved under the matched Gaussian source |

A negative mean REML − NNLS error favors REML. The intervals for trial and sensor errors exclude zero under the described block-resampling analysis. The intercept and slope intervals do not; their recoveries cannot support a general REML advantage. The paired estimates are not 384 independent observations, and the simulated covariance family is structurally aligned with both fitted families in the matched subset.

## All 24 frozen experimental cells

Each cell contains **16 independent generating blocks**. Exactly one of the candidate families matches the source covariance structure in each source condition; recovery errors and common 5% threshold counts are shown only for that structurally compatible candidate.

| n | Source covariance / leverage | Working family | Matched | NNLS successes | REML successes | NNLS trial near-zero | REML trial near-zero | NNLS slope near-zero | REML slope near-zero | Median trial relative error: NNLS / REML |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 24 | ordinary_independent | shared_slope | Yes | 16/16 | 16/16 | 7 | 0 | 8 | 6 | 1.000 / 0.255 |
| 24 | ordinary_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 24 | ordinary_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 24 | ordinary_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 6 | 0 | 7 | 5 | 1.000 / 0.265 |
| 24 | extreme_independent | shared_slope | Yes | 16/16 | 16/16 | 7 | 0 | 8 | 5 | 1.000 / 0.254 |
| 24 | extreme_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 24 | extreme_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 24 | extreme_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 9 | 0 | 6 | 4 | 1.000 / 0.268 |
| 48 | ordinary_independent | shared_slope | Yes | 16/16 | 16/16 | 8 | 0 | 9 | 5 | 1.000 / 0.145 |
| 48 | ordinary_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 48 | ordinary_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 48 | ordinary_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 9 | 0 | 9 | 6 | 1.000 / 0.147 |
| 48 | extreme_independent | shared_slope | Yes | 16/16 | 16/16 | 8 | 0 | 8 | 4 | 1.000 / 0.144 |
| 48 | extreme_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 48 | extreme_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 48 | extreme_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 9 | 0 | 2 | 1 | 1.000 / 0.149 |
| 96 | ordinary_independent | shared_slope | Yes | 16/16 | 16/16 | 4 | 0 | 10 | 4 | 1.000 / 0.062 |
| 96 | ordinary_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 96 | ordinary_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 96 | ordinary_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 9 | 0 | 6 | 5 | 1.000 / 0.065 |
| 96 | extreme_independent | shared_slope | Yes | 16/16 | 16/16 | 3 | 0 | 10 | 5 | 1.000 / 0.061 |
| 96 | extreme_independent | predictor_scaled_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 96 | extreme_dependent | shared_slope | No | 16/16 | 16/16 | — | — | — | — | — / — |
| 96 | extreme_dependent | predictor_scaled_slope | Yes | 16/16 | 16/16 | 9 | 0 | 2 | 2 | 1.000 / 0.064 |

## Scientific decision and unqualified stages

The R25 four-block pilot's large trial and sensor benefits persisted in an independent, larger 16-block Gaussian-source study using the exact same native observation data for both methods. Thus REML is a better **research candidate for trial and sensor covariance recovery under the specified Gaussian working family**, not a winner for all four components or a production inference procedure.

Participant random-slope variance remained difficult to recover with either method: slope component values fell below 5% of truth in **52/192** matched REML fits, and slope absolute relative recovery errors remain substantial. Next evaluate the independently specified expected Gaussian *restricted-likelihood variance-component Fisher information* under frozen native designs and the fitted model sensitivity before considering estimated-target CR2 inferential calibration. A full-rank information matrix can still be practically uninformative for one component.

Neither R25 nor R26 computed any coefficient CI, estimated-target CR2 SE/df or pointwise or simultaneous functional coverage. Variance recovery does not account for nuisance covariance estimation uncertainty in the existing conditional Satterthwaite degrees of freedom. Additional independent measurement-process and misspecification studies would be needed for eye-tracking recordings beyond this intentionally simulation-aligned Gaussian family.

`covariance_estimator_winner_selected=false`, `estimated_nuisance_inference_qualified=false`, `simultaneous_functional_bands_qualified=false`, `release_authorized=false`. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN. All research branches are drafts, protected main and supported public API unchanged, no version 1.2 tag or PyPI publication.
