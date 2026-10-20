# W3 R75-A — independent original marginal-SE × joint-correlation Gaussian audit

**Research only; no qualified 90% simultaneous confidence bands.** This page preserves the [R75 frozen original protocol](w3-r75-prospective-SE-correlation-factorial.md), complete original source outcomes and the separate independent actual-source reconstruction gate for [undercoverage blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289). Gaze-loss blocker #296 remains open.

## Original new-source simulation

Prospective [R75 draft PR #399](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/399), frozen source seed **202610207575**, standardized Gaussian reference seed **202610207576**, original W3 whole-unit wild seed **202610207577**. Original [R75 scientific workflow #39385910433](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39385910433) completed **8/8 dedicated jobs** (three Python 3.11–3.13 numerical contract tests, four new 8-block source shards, full immutable original SHA256 source aggregate). Complete original [evidence artifact #12247965574](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39385910433/artifacts/12247965574) pins exact original R75 scientific Actions checkout **`7bcdf6fee93e6a0964913e44b5c78a60d3cfc7e3`**.

R75 generated **32 genuinely NEW independent Gaussian primitive generating blocks** × two native independent-unit configurations (72 curves or 36 participants×three trials) × paired ordinary/extreme predictor supports × paired constant versus predictor-dependent unit Gaussian SD s_i=1+.75|x_i|. Original **256/256 source cases completed, zero numerical refusals**. Each case archives 999 original W3 wild-HC1 maxima, 999 standardized generating-Gaussian correlation maxima and 999 estimated weighted-HC3 correlation maxima, plus original X, native independent-unit Y, truth, source scales and true/HC3 marginal SE grids. These **767,232 conditional maximum-statistic values are not independent source blocks**. Both 2×2 marginal-SE crossings reuse the **same** true-correlation and HC3-correlation reference maxima within their source.

## Original nominal 90% full-grid slope truth inclusion

Each cell has exactly **32 independent primitive generating blocks**; those blocks are paired across methods and source support/variance regimes. Original results are from the immutable source archive, not a separate independent audit until the mandatory actual-data reconstruction passes.

| Native-unit design | Leverage | Source variance | True SE + true correlation | True SE + HC3 correlation | HC3 SE + true correlation | HC3 SE + HC3 correlation | Original wild-HC1 |
|---|---|---|---:|---:|---:|---:|---:|
| 72 curves | Ordinary | Constant | 30/32 | 30/32 | 29/32 | 29/32 | 24/32 |
| 72 curves | Ordinary | Predictor-dependent | 30/32 | 29/32 | 29/32 | 28/32 | 23/32 |
| 72 curves | Extreme | Constant | 25/32 | 23/32 | 20/32 | 16/32 | 2/32 |
| **72 curves** | **Extreme** | **Predictor-dependent** | **26/32** | **20/32** | **5/32** | **1/32** | **0/32** |
| 36 participants × 3 | Ordinary | Constant | 27/32 | 27/32 | 28/32 | 27/32 | 22/32 |
| 36 participants × 3 | Ordinary | Predictor-dependent | 27/32 | 27/32 | 28/32 | 29/32 | 23/32 |
| 36 participants × 3 | Extreme | Constant | 26/32 | 23/32 | 21/32 | 20/32 | 14/32 |
| **36 participants × 3** | **Extreme** | **Predictor-dependent** | **26/32** | **24/32** | **12/32** | **10/32** | **3/32** |

Under extreme predictor-dependent heteroskedasticity, average estimated **weighted HC3 / known true marginal slope-SE** was **0.98075456 curves** and **0.94114698 participants**. These averages mask systematic source/unit/time-grid structure and cannot substitute for full joint coverage analysis. Average original empirical **HC3-reference 90% max critical** was **2.74479193 curves** versus **3.13726904 true correlation**; for participants **2.29628311** versus **2.48732146**.

**Source-matched factorial interpretation (exploratory):**
- Holding each source's *true slope SE fixed*, exchanging true correlation for estimated HC3 correlation changes whole-grid truth inclusion from **26→20/32** for curves and **26→24/32** for participants under the extreme adverse law. This isolates the reference correlation/critical effect in an otherwise hypothetical true-SE procedure.
- Holding the *true Gaussian correlation reference fixed*, exchanging known marginal slope SE for estimated weighted HC3 slope SE changes whole-grid inclusion from **26→5/32** for curves and **26→12/32** for participants. Despite near-unit average estimated/true SE ratios, this source/grid-sensitive marginal-scale substitution greatly reduces complete-grid truth inclusion.
- Simultaneously using estimated HC3 slope SE and HC3 correlation yields **1/32** curves and **10/32** participant inclusions. These are the actual estimated weighted-HC3 candidate source results; neither is remotely sufficient for a nominal-90% claim.

This decomposition documents a **joint** problem, not a causal or implementation-free guarantee. The fully true benchmark is based on artificial generating covariance; the off-diagonal factorial cells with one true component **are not observed-data estimators**. It does not follow that substituting any arbitrary shrinkage or finite-sample correction would repair coverage. Even the known-law oracle has wide 32-source Monte Carlo uncertainty.

## Independent original R75-A numerical contract

The separately implemented `scripts/audit_w3_r75_independent_original_SE_correlation.py` **imports none** of R75's generator, source W3 package OLS/bootstrap, covariance code, original summary/aggregate or source-level labels. Its mandatory actual original-source job downloads the frozen original archive, verifies **3 original SHA256 members** and original checkout, then independently regenerates all **256 source X/Y native-unit Gaussian observations** from the frozen seeds, known functional truth and participant-time covariance.

For every original completed source it independently derives:

- native-unit OLS slope, HC1 wild-SE reference and **slope-specific HC3 residual factor `a_i*r_i/(1-h_i)`**, and the exact simulation-known heterogeneous slope SE (source-only benchmark);
- original **999 native-unit Rademacher wild maximum-statistic values**, the exact 999 standardized true-correlation Gaussian maxima, and the exact 999 estimated-HC3-correlation Gaussian maxima **from the SAME original sequential Gaussian random stream**;
- every empirical 90% `higher` critical, the original four 2×2 observed true/HC3-SE max pivots and binary full-grid truth inclusion classifications, and original W3 wild-HC1 truth inclusion;
- eight design/support/law fixed 32-block denominators, Wilson 95% independent-source Monte Carlo intervals, original complete/refusal records, source mean true/HC3 critical and HC3/true marginal SE ratios and all prespecified paired changes.

The audit fails closed on wrong source checkout, wrong original RNG seed, SHA tamper, missing/duplicated source, altered X/Y, true or HC3 SE, forged critical/max array or truth inclusion, silently omitted fit failures, and false release/calibration claims. Three Python numerical fixture contract jobs are **not sufficient**: independent original-archive verification is complete only after a separate fourth actual-data job succeeds and publishes a second evidence artifact.

## Executed independent source-level verification — PASSED

The mandatory [R75-A genuine original-source audit workflow #39386725214](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39386725214) completed **4/4 scientific jobs successfully**: three Python 3.11–3.13 numerical source/correlation/forgery test jobs plus the required read-only original R75 archive audit. Its independently retained [numerical evidence artifact #12247767973](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39386725214/artifacts/12247767973) verifies the three original immutable SHA256 members and exact science checkout `7bcdf6fee93e6a0964913e44b5c78a60d3cfc7e3`.

The independently implemented checker reconstructed **all 256 original source X/Y Gaussian datasets** from the prospective RNG and exact source law, 32 primitive generating blocks per design/support/variance, **256/256 accepted with zero refusals**. It independently recomputed original OLS/HC1, true heterogeneous slope SE, estimated weighted HC3 residual factor and source truth max pivots, re-simulated **255,744 original 999-draw wild-HC1 maxima + 255,744 original 999-draw standardized true-Gaussian-correlation maxima + 255,744 original 999-draw estimated-HC3-correlation maxima** (**767,232 total conditional maximum statistics**), re-derived each source's empirical higher 90% critical and complete 2×2 inclusion status, and independently reconstructed all full-denominator rates, Wilson Monte Carlo intervals and paired truth-inclusion changes. The frozen original archive and source are unchanged.

The **source independently reproduced extreme-leverage and predictor-dependent heteroskedasticity** result is:

| Native independent-unit design, 32 new blocks | True SE / true corr | True SE / estimated HC3 corr | HC3 SE / true corr | HC3 SE / estimated HC3 corr | W3 wild-HC1 |
|---|---:|---:|---:|---:|---:|
| 72 independent curves | **26/32** | **20/32** | **5/32** | **1/32** | **0/32** |
| 36 participants × 3 trials | **26/32** | **24/32** | **12/32** | **10/32** | **3/32** |

Independently rederived average HC3/true marginal SE ratios: **0.98075456 curves** and **0.94114698 participants**. Average original estimated HC3 versus source-true 90% reference criticals were **2.74479193 versus 3.13726904 curves**, **2.29628311 versus 2.48732146 participants**. This source-verified factorial diagnostic establishes that both estimated covariance components can matter, with a particularly large source-level role for HC3 marginal scale even when the *average* SE ratio is near one. It does **not** uniquely separate bias, stochastic leverage geometry and cross-grid dependence at every original generating source, and cannot validate a real-data method.

The true-correlation and true-SE factor-isolation cells are **simulation-only counterfactuals**; no true covariance is available in observed eye-tracking. The R75 source archive's three Gaussian/wild maximum arrays are not independent source replications; 32 generating blocks per cell remain the Monte Carlo denominator. R75 does **not** repair 90% W3 simultaneous inference.

## Scientific limitations and release HOLD

R75 has **32 independently generated blocks per configuration/law**, not 256 independent coverage replicates per cell. Its model is fully observed Gaussian data with 31×2 regular time–dimension grid and scaled participant random intercept, not arbitrary eye-tracking dynamics. Estimated HC3 marginal SE ratios near one do not imply proper simultaneous bands; the needed reliable joint correlation/covariance estimation remains unsolved, especially with leverage and predictor-dependent heteroskedasticity. No candidate, including weighted HC3, is qualified for public W3 simultaneous inference. #289 remains OPEN. Real gaze observation loss and response-dependent missingness #296 are untouched.

Protected main, stable v1.1.0, 1.2 tags, PyPI release and public inference APIs remain **HOLD**.
