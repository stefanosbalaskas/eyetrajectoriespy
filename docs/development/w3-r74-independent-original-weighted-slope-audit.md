# W3 R74-A — independent original 512-source slope-weighted HC2/HC3 numerical audit

**Research only, no calibrated 90% simultaneous inference.** This page preserves the source-NEW R74 evidence, its first nonqualification result, and the independent original-data verification contract. It does not authorize releasing version 1.2. Blocker [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and gaze-loss blocker [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN.

## Original prospectively frozen source experiment

The [R74 protocol](w3-r74-prospective-weighted-slope-HC2-HC3-protocol.md) and statistical thresholds were committed before original outcomes. Original [draft PR #396](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/396) source [workflow #39315676669](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39315676669) completed **12/12 dedicated science jobs**: 3/3 Python 3.11–3.13 exact source covariance/OLS/HC1/preserved pooled HC2 and Gaussian algebra contracts, eight original four-block NEW-source shards, and the complete failure-inclusive immutable SHA256 aggregate. Frozen source scientific PR merge checkout: **`4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9`**; original [immutable 512-source evidence artifact #12217916622](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39315676669/artifacts/12217916622).

The exact **32 NEW independent primitive Gaussian generating blocks** supplied 4 separate source-size configurations (36/72 independent curves, 24/36 independent participants × three repeated trials), each paired ordinary/extreme leverage × constant/predictor-dependent unit noise. **512/512 source cases completed, zero numerical refusals**; a single method/size/support/law cell has **32 independent generating blocks**, not 512 independent coverage replicates. Original 999 native independent-unit Rademacher vectors/case, and separately 999 Gaussian z draws/case shared across the pooled-HC2, weighted-slope-HC2 and weighted-slope-HC3 candidate covariances. Source means and generating covariance are fixed by the original Gaussian W3 law; original unequal unit SD multiplier `1+.75|x|`, especially ±4 extreme predictor units with scale 4 and variance 16×.

The **original unmodified W3 wild-HC1** and **unchanged original R72 pooled common-covariance HC2 Gaussian** are negative-controls, and the simulation-known heterogeneous Gaussian slope reference is explicitly unavailable for real-data estimation. New experimental slope-weighted methods use original regression slope design weights and unit-level residuals:


- Weighted HC2: `V_slope,HC2 = Σ_i a_i² (r_i r_iᵀ)/(1−h_i)`.
- Weighted HC3: `V_slope,HC3 = Σ_i a_i² (r_i r_iᵀ)/(1−h_i)²`.

The 999 multivariate Gaussian maximum-statistic references are computed from these **rank-deficient rectangular factors**, with covariance-inferred standardization separately for each method, not from the generating covariance. Neither method is yet a statistically qualified confidence-band procedure.

## Original observed 90% simultaneous full-grid slope truth inclusion

All rates below have **32 independently generated primitive blocks per size/support/source-law configuration**. These are originally archived simulation findings, subject to the separately required independent original archive audit.

| Configuration | Leverage | Unit variance | W3 wild-HC1 | Pooled HC2 Gaussian | Weighted-slope HC2 | Weighted-slope HC3 | Known heterogeneous Gaussian |
|---|---|---|---:|---:|---:|---:|---:|
| 36 curves | Ordinary | Constant | 16/32 | 29/32 | 23/32 | 24/32 | 32/32 |
| 36 curves | Ordinary | Predictor-dependent | 13/32 | 18/32 | 20/32 | 23/32 | 30/32 |
| 36 curves | Extreme | Constant | 1/32 | 22/32 | 5/32 | 8/32 | 28/32 |
| **36 curves** | **Extreme** | **Predictor-dependent** | **0/32** | **0/32** | **0/32** | **0/32** | **30/32** |
| 72 curves | Ordinary | Constant | 23/32 | 29/32 | 29/32 | 29/32 | 31/32 |
| 72 curves | Ordinary | Predictor-dependent | 24/32 | 23/32 | 27/32 | 29/32 | 31/32 |
| 72 curves | Extreme | Constant | 5/32 | 27/32 | 9/32 | 10/32 | 27/32 |
| **72 curves** | **Extreme** | **Predictor-dependent** | **0/32** | **0/32** | **0/32** | **0/32** | **31/32** |
| 24 participants × 3 trials | Ordinary | Constant | 25/32 | 27/32 | 26/32 | 27/32 | 30/32 |
| 24 participants × 3 trials | Ordinary | Predictor-dependent | 24/32 | 26/32 | 27/32 | 27/32 | 30/32 |
| 24 participants × 3 trials | Extreme | Constant | 12/32 | 29/32 | 15/32 | 18/32 | 31/32 |
| **24 participants × 3 trials** | **Extreme** | **Predictor-dependent** | **5/32** | **4/32** | **7/32** | **9/32** | **31/32** |
| 36 participants × 3 trials | Ordinary | Constant | 25/32 | 26/32 | 27/32 | 29/32 | 30/32 |
| 36 participants × 3 trials | Ordinary | Predictor-dependent | 24/32 | 24/32 | 27/32 | 29/32 | 29/32 |
| 36 participants × 3 trials | Extreme | Constant | 11/32 | 24/32 | 16/32 | 18/32 | 28/32 |
| **36 participants × 3 trials** | **Extreme** | **Predictor-dependent** | **5/32** | **4/32** | **6/32** | **10/32** | **27/32** |

**Original source mathematical diagnostic:** Under extreme support × predictor-dependent unequal variance, average estimated-to-true heterogeneous slope SE ratios:

| Source design | Pooled common HC2 | Weighted HC2 | Weighted HC3 |
|---|---:|---:|---:|
| 36 curves | 0.4402 | 0.7906 | **1.0126** |
| 72 curves | 0.4614 | 0.8340 | **0.9816** |
| 24 participants | 0.4527 | 0.8011 | **1.0733** |
| 36 participants | 0.4554 | 0.8067 | **1.0291** |

The **source-level diagonal SE correction** improves greatly under slope-specific weighting and HC3, yet full-grid truth inclusion remains very low. This is *consistent with* an inadequate estimated joint Gaussian maximum-reference distribution, including potential near-low-rank bootstrap correlations and high-leverage design behavior; the experiment alone does not identify which contribution caused the remaining undercoverage. Mean scale ratios across source cells do not imply matched coverage or calibrated uncertainty. Under **constant** variance, the pooled HC2 normal-reference often outperforms weighted HC2/HC3 despite similarly well-scaled pointwise SE; consequently no candidate is selected by favorable post-hoc coverage.

## Mandatory R74-A independently reconstructed original source evidence

The independent `scripts/audit_w3_r74_independent_original_weighted_slope.py` **imports none** of the original R74 simulator, original W3 fitter/bootstrap, original R72 pooled covariance code or original R74 aggregation. It independently reads the original **exact immutable source archive** and verifies all three SHA256 members and pinned scientific checkout. Then it must independently:

1. **Regenerate all 512 original Gaussian X and native independent-unit Y arrays** from the prospective generating seeds and source Gaussian error laws, including both 4-size configurations, paired leverage and variance regimes, trial-averaged participant responses and true functional coefficients.
2. Independently compute original OLS/HC1, unit leverage, **pooled common HC2** and both **slope-weighted HC2/HC3** covariance rectangular factors, as well as **the known heterogeneous Gaussian slope covariance** strictly as a simulation reference, from each regenerated source X and Y.
3. Independently reconstruct **all 511,488 original source wild maximum-statistic draws** (999×512), and all **1,534,464 original source Gaussian maximum-statistic draws** (999×512×3 covariance candidates), matched on their original separate RNG streams; check the complete method SE grids, 90% empirical higher quantiles, source truth pivots, inclusion decisions, independent-block Wilson MC intervals, fixed denominator and paired source discords.
4. Fail closed on a missing/duplicate source identity or primitive block, altered source seed/checkout, original source X/Y/variance scaling, tampered maximum array, false source status or false nominal-90%/release assertion. Preserve every refused original source with the same 32 planned independent-generating-unit denominator.

That amounts to **2,045,952 original conditional maximum-statistic values**, not 2,045,952 statistically independent datasets. This independent actual-original-source audit is required **in addition to** the original 12/12 R74 simulation jobs and its cross-Python regression contracts. *Until the actual archive job is green, independent R74-A source verification must not be claimed.* Original Gaussian known covariance is unobservable in real gaze data, and an independent simulation replay does not certify general nominal confidence bands.

## Executed independent original-data verification — 4/4 PASS

The *genuine original data* [R74-A numerical audit workflow #39316800177](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39316800177) **passed all 4/4 scientific jobs**, including Python 3.11–3.13 source-generation, covariance-factor, source-refusal and tamper-check fixtures (3/3), plus the **mandatory read-only reconstruction of the original immutable R74 archive** (1/1). Its separately retained [independent original evidence artifact #12218955708](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39316800177/artifacts/12218955708) verifies exact original scientific PR-merge checkout `4031d3dbe5cfc5617bd939c8ea9cd00d17376bd9`, 3/3 original SHA256 archive members, all 32 source IDs × four native unit-size configurations × both support × both variance regimes, **512/512 originally completed Gaussian source cases**, zero numerical failures, all original source X/Y Gaussian vectors, unit scales and truth curves.

The separately implemented code independently recreates original source W3 OLS/HC1, the unchanged R72 pooled common-covariance HC2 Gaussian reference, R74 slope-specific HC2 and HC3 source covariance factors, and the true unequal-variance generating-law slope SE. It replays and checks **511,488 original whole-unit wild maximum-statistic values** and **1,534,464 estimated Gaussian maximum-statistic values** across three covariance factors (**2,045,952 original conditional max-statistic values total**); independently recomputes all higher empirical 90% critical values, 2,560 source×method truth decisions, 16-cell independent-source denominators/Wilson Monte Carlo intervals, and original within-source method discordances.

**The adverse result was reproduced from original source X/Y**, not copied from the original source aggregate. Under extreme predictors and unequal Gaussian source variances, **both curve configurations** have 0/32 coverage for both weighted slope HC2 and HC3 compared with source-known oracle 30/32 and 31/32; **24-participant source** gives weighted HC2 7/32, weighted HC3 9/32, oracle 31/32; **36-participant source** gives weighted HC2 6/32, weighted HC3 10/32, oracle 27/32. The marginal weighted HC3/true SE ratio is approximately **1.013** and **0.982** for curves (36/72 units) and **1.073** and **1.029** for participant units (24/36 units), but *this does not imply a correctly calibrated joint covariance/reference distribution*.

The separate original and independent scientific jobs establish **implementation reproducibility for the defined artificial source law**, not empirical coverage qualification across other generating laws, covariance estimators, bootstrap references or actual gaze observation loss. The source-law oracle remains unavailable for real observations; the sample consists of only 32 independent primitive sources per experimental condition. The negative source evidence rules out automatic release promotion of **these particular weighted HC2/HC3 Gaussian references**, not all possible leverage corrections.

**Both issues #289 and #296 remain OPEN. Release/merge/tag/PyPI remain HOLD.**

## Qualification and release boundary

These are **negative and method-comparison pilot results** under a complete, Gaussian, intentionally adverse heteroskedastic independent-unit model, with artificial extreme leverage. None of the candidate estimated normal-reference simultaneous slope bands is qualified as a general 90% inferential procedure; the broader covariance-law, non-Gaussian error, temporal-shape heterogeneity, irregular observation, MAR/MNAR and eye-tracker signal-quality qualification remains absent. Source blocks, method statistics, and bootstrap draw counts are not interchangeable denominators.

Keep blocker **#289** open and separate gaze-observation blocker **#296** open; stable 1.1.0, protected `main`, unreleased development 1.2, production API, tags and PyPI untouched.
