---
title: Do regularized functional confidence bands survive time-varying AR(1) errors?
description: Independently source-audited R78 temporal covariance falsification of unchanged HC3 Gaussian simultaneous-band candidates
---

# Do regularized functional confidence bands survive time-varying AR(1) errors?

**Research article · 20 October 2026 · R78 original and independent R78-A source audit**

!!! danger "Simulation evidence, not a qualified inference method"
    **No generally calibrated nominal-90% W3 simultaneous-band method is established here.** This experiment exists only in [R78 research PR #408](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/408) and its separately implemented [original-source R78-A audit PR #409](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/409). Stable release 1.1.0 is unaffected. Version 1.2 remains unreleased, and scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.

## Why challenge the covariance law?

The preceding [R77 regularization experiment](covariance-regularization-and-w3-coverage.md) suggested that a fixed, positive-definite modification of the estimated HC3 covariance can improve full-function slope truth inclusion when only two independent observations carry extreme predictor values. That experiment generated temporally independent Gaussian innovations within a trial, with a simple participant latent random-effect function in its repeated-trial design.

The observed improvement is not guaranteed to persist when measurement errors are serially correlated and have variance that changes over the trial. R78 therefore **changes the simulation source law**, while freezing the previously tested candidate estimators, regularization strengths, smoothing window, number of conditional reference draws and functional truth grid. It is a *robustness falsification*, not a search for a better hyperparameter.

## Prospective Gaussian generating mechanism

The [protocol was frozen before original R78 source outcomes](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r78-fresh-temporal-covariance-misspecification-20261020/docs/development/w3-r78-prospective-temporal-covariance-falsification.md). The trial-level innovation has a **time-scaled Gaussian AR(1)** correlation law:

$$
\operatorname{Corr}(\epsilon_t,\epsilon_s)=0.72^{|t-s|},
\qquad
\sigma(t)=0.04(0.70+0.60t),\quad t\in[0,1].
$$

The true within-trial covariance is consequently the AR(1) correlation matrix pre- and post-multiplied by the known diagonal of time-specific standard deviations. Gaze coordinates are independent across dimensions within the trial-innovation component. In the participant design, an additional dimension-specific Gaussian random-effect trend of scale $0.065(1+0.35t)$ is shared across each participant's three trials. The participant is the *independent observation unit*; three trials do not generate three independent participants.

The source experiment uses **32 entirely new independent primitive generating blocks**, two observation designs (72 independent curves; 36 participants × 3 trials), **two or 16 independent predictor extremes** at $x=\pm4$, and either constant independent-unit noise scale or predictor-dependent scale $1+0.75|x|$. These produce **256 source-condition cases**: 32 × 2 × 2 × 2. Because anchor/variance conditions within a block are paired, the correct simulation denominator for each design/support/variance cell is **32 independent source blocks**, not 256 or 999.

Everything is **fully observed, synthetic and Gaussian**, on the fixed 31 × 2 slope grid. No gaze dropout, MNAR process, non-Gaussian innovation or real participant recording appears in this experiment.

## Exactly which inference candidates were retained?

The original unchanged W3 Rademacher wild-HC1 band, the source-weighted HC3 Gaussian maximum-statistic reference, and **two previously frozen covariance regularizations** were carried forward without parameter changes:

$$
F_{ik}=\frac{a_i r_{ik}}{1-h_i},
\quad
C_{\mathrm{HC3}}=F^{\mathsf T}F,
$$

$$
C_{\lambda}=(1-\lambda)C_{\mathrm{HC3}}
+\lambda\,\operatorname{diag}\left(K_7\operatorname{diag}(C_{\mathrm{HC3}})\right),
\qquad \lambda\in\{0.25,0.50\}.
$$

Here $a_i$ is the independent-unit slope design weight, $r_{ik}$ the observed residual and $h_i$ the estimated leverage, while $K_7$ is the unchanged seven-time-point moving mean **within** each gaze coordinate. Each estimated Gaussian reference standardizes its 999 maximum-statistic draws with its own candidate marginal SE. The fifth reference, using the **true temporally correlated Gaussian generating law**, is a simulation-only benchmark. Its true covariance is not supplied to any data-estimated method.

For every original source, the study archived 999 maximum-statistic draws for **all five references**, estimated and known marginal SE grids, source coefficient deviations from known truth, full-grid maximum pivots and exact truth-inclusion events.

## Full-grid results under predictor-dependent noise

![Independently audited original R78 whole-function truth inclusion by Gaussian source design, regularization candidate and extreme independent-unit support](../assets/research/w3-r78-ar1-whole-band-coverage.svg)

*Figure 1.* Nominal-90% **31 × 2 whole-slope-function** inclusion under time-scaled Gaussian AR(1), with source-level denominator 32 for each design/support combination. The known-law Gaussian covariance is specified by the simulator, not estimated from observations.

| Reference | Curves, 2 extreme units | Participants, 2 extreme units | Curves, 16 extreme units | Participants, 16 extreme units |
|---|---:|---:|---:|---:|
| Original W3 wild-HC1 | **0/32** | **5/32** | 12/32 | 29/32 |
| Estimated HC3 Gaussian | **5/32** | **9/32** | 21/32 | 30/32 |
| Fixed regularization λ=.25 | **15/32** | **19/32** | 26/32 | 31/32 |
| Fixed regularization λ=.50 | **22/32** | **19/32** | 27/32 | 31/32 |
| Simulation-known Gaussian | **26/32** | **28/32** | 30/32 | 31/32 |

When only two extreme high-noise independent units are present, the original HC3 reference includes the true entire slope in **5/32 curve datasets** and **9/32 participant datasets**. Fixed λ=.50 regularization yields **22/32** and **19/32**, respectively. The numerical change is substantial, but **22/32 is 68.75% and 19/32 is 59.38%**, not validated nominal 90% coverage. Under 16 independent extremes, counts are generally higher, but those designs also differ in their regression weights and information distribution; the comparison cannot establish an independent causal effect of information concentration.

### The constant-variance falsification cells

For the prespecified constant-variance setting with two extreme units, HC3 / λ=.25 / λ=.50 / known Gaussian whole-grid inclusion was **19/32, 23/32, 27/32, 28/32** for curves and **18/32, 25/32, 28/32, 28/32** for participants. These cells remain visible to avoid selecting only favorable candidate comparisons. The new experiment does not identify a universally reliable strength, and fixed smoothing can be either unhelpful or excessively conservative under other covariance laws.

## Did the improvement transport from R77?

![Separate-source R77 and R78 Gaussian covariance sensitivity comparison for the two-anchor high-noise scenario](../assets/research/w3-r77-r78-unpaired-temporal-covariance-stress.svg)

*Figure 2.* A descriptive comparison of **separate R77 and R78 experiments**, each with 32 new independent primitive generating blocks per design and condition. The experiments do **not** use the same original datasets. Comparisons across stages cannot be treated as source-paired experimental differences or as a clean estimate of the causal effect of serial correlation.

| Band reference | Curves: R77 → R78 | Participants: R77 → R78 |
|---|---:|---:|
| Original estimated HC3 | 1/32 → 5/32 | 9/32 → 9/32 |
| Fixed λ=.25 | 22/32 → 15/32 | 23/32 → 19/32 |
| Fixed λ=.50 | 24/32 → 22/32 | 24/32 → 19/32 |
| Source-known Gaussian benchmark | 27/32 → 26/32 | 29/32 → 28/32 |

R77's temporally independent within-trial Gaussian law was more favorable for some regularized candidates. R78's correlated and time-scaled noise retained some improvement relative to HC3, but observed inclusion under high leverage remained markedly short of a broadly credible nominal-90% target. The independent source generation makes this **transportability evidence**, not a single paired test of two generating laws.

## Why did the band widths change?

![R78 independently audited lower-tail estimated slope SE ratios and reference maximum criticals](../assets/research/w3-r78-ar1-lower-tail-and-critical-diagnostics.svg)

*Figure 3.* Two-extreme-unit, predictor-dependent Gaussian noise. The lower-tail SE diagnostic is the across-source average of each source's 10th percentile across all 62 cells of estimated marginal SE divided by **simulation-known** true SE. That true SE is not available to an observed-data method. The second panel plots the mean estimated Gaussian maximum-statistic reference critical for each data-estimated candidate.

| Two-anchor high-noise diagnostic | HC3 | λ=.25 | λ=.50 |
|---|---:|---:|---:|
| Curves, source-wise SE ratio 10th percentile | 0.442 | 0.578 | 0.651 |
| Participants, source-wise SE ratio 10th percentile | 0.487 | 0.517 | 0.541 |
| Curves, Gaussian maximum critical | 2.717 | 2.957 | 3.061 |
| Participants, Gaussian maximum critical | 2.240 | 2.817 | 3.007 |

In this experiment, regularization changed **both** the lower tail of marginal SE ratios and the Gaussian maximum critical. The observed improvement therefore cannot be attributed only to a better covariance estimate: widening the maximum-statistic threshold also matters, and might cause overconservatism in other designs. Even with the regularized candidates, the average lower-tail SE ratio remains well below one under sparse influential support.

## Independent numerical audit and what it establishes

The original [R78 science workflow #39477000929](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39477000929) completed **12/12 dedicated scientific jobs**, with **256/256 accepted source cases and zero refusals**. Original immutable evidence is retained in [artifact #12290295000](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39477000929/artifacts/12290295000), at scientific source checkout `f438b9680d81f5e5e3e893b1ff7a0bc93383a619`.

A separately implemented [R78-A read-only original-archive audit #39477446946](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39477446946) passed **4/4 dedicated jobs** and independently reproduced the **256 original X/Y source datasets, 1,278,720 original maximum-statistic values**, all five source-specific quantile reference arrays, known AR(1) Gaussian variance, source-level truth classifications and SHA256 checks. The independent audit evidence is [artifact #12290570185](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39477446946/artifacts/12290570185).

This audit qualifies the **numerical reproducibility of the simulation result**, not the frequentist calibration of an observed-data confidence-band estimator.

## What must happen before inferential qualification?

The fixed candidates now have independently audited tests in more than one synthetic Gaussian covariance regime, but **neither is demonstrably reliable under sparse independent high-leverage support**. Next studies should target source-independent stress under stronger nonstationarity, nonseparable cross-coordinate covariance, heavier-tailed innovations, irregular observation intervals and **response-dependent gaze loss**, without retuning hyperparameters to select a favorable outcome. Quantifying overcoverage and refusal behavior is equally important.

The W3 inference issue #289 and missingness issue #296 remain **OPEN**. No experimental W3 estimator is merged to the stable package or qualified for a public nominal-90% claim, and **eyetrajectoriespy 1.2 remains on release HOLD**.
