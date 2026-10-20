---
title: Do functional confidence bands survive nonseparable gaze-coordinate covariance?
description: Independently verified R79 fixed-HC3 candidate stress under time-varying cross-coordinate Gaussian correlation
---

# Do functional confidence bands survive nonseparable gaze-coordinate covariance?

**Scientific research article · 20 October 2026 · R79 and independently implemented R79-A**

!!! danger "No qualified nominal 90% band"
    This article reports numerical simulations of fully observed Gaussian trajectories, **not authentic human eye-tracking measurements**. The fixed positive-definite HC3 regularization candidates live only in [R79 research PR #411](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/411) and independent [audit PR #412](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/412). Neither candidate establishes reliable general nominal-90% simultaneous functional inference. Issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. Stable 1.1.0 is unchanged; version 1.2 is still unreleased.

## The next source-covariance challenge

The preceding [R77 research study](covariance-regularization-and-w3-coverage.md) found improved whole-band truth inclusion after prespecified source-observable HC3 covariance regularization in a simple Gaussian model. [R78](w3-temporal-covariance-robustness-r78.md) then added serially correlated, time-varying Gaussian trial noise without retuning the estimators. R79 challenges a different assumption: **that the two gaze-coordinate innovation processes are independent and follow a single separable spatial-temporal covariance structure.**

Real two-coordinate trajectories need not have a constant relationship between their horizontal and vertical components. The R79 simulation deliberately makes the *within-time coordinate correlation* increase across a trial while keeping serial covariance and marginal scale otherwise specified. It is a numerical portability test of the same frozen candidates, not a search for favorable regularization settings.

## What was prospectively changed?

The [R79 protocol was committed before new source results](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r79-nonseparable-coordinate-covariance-falsification-20261020/docs/development/w3-r79-prospective-nonseparable-cross-coordinate-falsification.md). Within each trial, two initially independent Gaussian innovation processes have lag correlation $\rho^{|j-k|}$ with $\rho=0.72$ and time-varying marginal standard deviation $\sigma(t)=0.04(0.70+0.60t)$. They are mixed at each time point to produce

$$
Z_1(t)=U_1(t),\qquad
Z_2(t)=q(t)U_1(t)+\sqrt{1-q(t)^2}\,U_2(t),
$$

where

$$
q(t)=0.15+0.65t,\qquad 0\leq t\leq1.
$$

The within-time trial cross-coordinate correlation therefore rises from **0.15 to 0.80**, preserving each coordinate's marginal innovation variance while changing joint covariance as a function of time. The combination with serially correlated innovations induces a nonseparable spatial-temporal covariance law. In the repeated-participant design, a shared Gaussian participant latent term additionally has **fixed cross-coordinate correlation 0.45**, distinct from the trial correlation profile.

![R79 true time-varying cross-coordinate correlation and Gaussian trial standard-deviation profiles](../assets/research/w3-r79-generating-nonseparable-covariance-law.svg)

*Figure 1.* The **source generating mechanism**, not a fitted estimate from an eye-tracking recording. The left panel shows the stipulated cross-coordinate correlation function, and the right the within-trial marginal standard deviation. The candidate inferential procedures do **not** receive these parameters.

The original source experiment used **32 genuinely new primitive Gaussian generating blocks**, 72 independent curves versus 36 independent participants observed on three complete trials, 2 or 16 independent extreme $x=\pm4$ predictor units, and constant versus predictor-dependent unit error scale $1+0.75|x|$. In total, the factorial has **256 cases**, but **only 32 independent blocks in each design/support/variance cell**. Conditions generated from one primitive block are paired; 999 reference draws per candidate are not additional independent source datasets.

## Frozen original inferential candidates

The established W3 Rademacher wild-HC1 reference was retained as a negative-control comparator, alongside the original estimated slope-weighted HC3 Gaussian reference. Two unchanged *data-estimated* regularizations used

$$
C_{\lambda}=(1-\lambda)C_{\mathrm{HC3}}+
\lambda\operatorname{diag}\left[K_7\operatorname{diag}(C_{\mathrm{HC3}})\right],
\quad\lambda\in\{0.25,0.50\},
$$

where $K_7$ averages diagonal variance estimates across a fixed seven-time-point local window **within each coordinate**. The corresponding Gaussian maximum-statistic reference is standardized with each candidate's own estimated marginal standard deviation.

A fifth reference uses the **exact known generating Gaussian law, including the changing cross-coordinate correlation**. It is an in-simulation reference, not a feasible real-data estimator. All five references used **999 raw conditional maximum-statistic draws per source**, with a frozen higher empirical 90th-percentile rule. Source inclusion means the entire known **31-time-point × 2-coordinate slope function** lies in the simultaneous band.

## Whole-function inclusion under predictor-dependent variance

![R79 source-level Gaussian functional whole-band truth inclusion for five candidates, two independent curve designs and extreme-unit supports](../assets/research/w3-r79-nonseparable-full-band-coverage.svg)

*Figure 2.* Individually source-level full-function truth inclusions among 32 independent new Gaussian generating blocks in each fixed design/support cell. The simulation-known Gaussian reference is not a data-estimated procedure.

| Reference | Curves, 2 extreme units | Participants, 2 extreme units | Curves, 16 extreme units | Participants, 16 extreme units |
|---|---:|---:|---:|---:|
| Original W3 wild-HC1 | **1/32** | **6/32** | 19/32 | 21/32 |
| Original HC3 Gaussian | **3/32** | **11/32** | 25/32 | 23/32 |
| Fixed regularization λ=.25 | **19/32** | **17/32** | 29/32 | 28/32 |
| Fixed regularization λ=.50 | **24/32** | **20/32** | 31/32 | 28/32 |
| Generating-law Gaussian reference | 26/32 | 27/32 | 30/32 | 27/32 |

The two-source-support adverse condition is especially revealing. Baseline HC3 includes the entire generating functional slope in only **3/32 curve datasets** and **11/32 participant datasets**. Fixed $\lambda=0.50$ gives **24/32** and **20/32**, respectively. In the same sources, the true Gaussian benchmark gives **26/32** and **27/32**. These model-conditional gains are numerically meaningful, but **24/32 is 75% and 20/32 is 62.5%**, both well below 90%.

With 16 independent extreme observations, estimated regularization sometimes produces more inclusions than the source-known benchmark in this finite set of 32 sources. Such a difference is not evidence that the data-estimated method is more accurate than a correct known generating distribution, or that regularization is universally conservative; Monte Carlo uncertainty and source-specific random outcomes matter.

The prespecified **constant-variance comparator** remains part of the evidence. With two extreme units, HC3 / λ=.25 / λ=.50 / generating-law inclusion was **16/32, 21/32, 25/32, 28/32** for curves and **20/32, 26/32, 26/32, 30/32** for repeated participants. These findings are not substitutes for the difficult heteroskedastic condition and do not license post hoc candidate selection.

## Distinguishing marginal uncertainty from maximum-statistic correlation

![R79 estimated marginal HC3-to-known SE lower-tail and simultaneous Gaussian critical comparisons](../assets/research/w3-r79-hc3-se-tail-and-critical.svg)

*Figure 3.* Primary two-anchor predictor-heteroskedastic condition. The first panel shows the source mean of each source's 10th percentile, over the 62 grid coordinates, of estimated-to-**true** marginal slope standard error. The second panel shows mean data-estimated Gaussian simultaneous critical values. True marginal SE is available only within the generating experiment.

| Source-averaged diagnostic | Original HC3 | Fixed λ=.25 | Fixed λ=.50 |
|---|---:|---:|---:|
| Curves: source-wise lower-tail estimated/true SE | 0.460 | 0.583 | 0.651 |
| Participants: source-wise lower-tail estimated/true SE | 0.509 | 0.542 | 0.567 |
| Curves: estimated Gaussian maximum critical | 2.711 | 2.949 | 3.067 |
| Participants: estimated Gaussian maximum critical | 2.255 | 2.829 | 2.998 |

The fixed regularization increases the lower-tail estimated/true SE ratios **and** the estimated joint Gaussian critical. The resulting improvement cannot be assigned exclusively to either better marginal covariance estimation or altered simultaneous thresholding. More conservative reference quantiles can widen bands without making the underlying covariance model accurate; source-level undercoverage nevertheless remains appreciable.

## Independent verification and limits

The original [R79 scientific workflow #39483619384](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483619384) passed **12/12 dedicated scientific jobs**. Its [original evidence archive #12292856827](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483619384/artifacts/12292856827) contains **256/256 completed source cases**, zero refusals and the complete five-reference source arrays at original scientific source checkout **15bcbe55d42579c9788cd94b9516850b6eabc1b2**.

An independently implemented [R79-A mandatory actual-original-source replay #39483939543](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483939543) passed **4/4 independent audit jobs**, recreating all **256 source X/Y arrays, 1,278,720 reference maximum-statistic values**, time-varying trial spatial mixing, correlated participant latent generation, all source full-grid inclusion classifications, original immutable source identity and checksum, with zero source refusals. The [independent numerical report #12291983970](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483939543/artifacts/12291983970) is separate from the original source implementation. Numerical agreement verifies the experiment's computational reproducibility, not statistical validity across other data-generating mechanisms.

The two gaze coordinates are still fully observed Gaussian values. R79 does **not** test non-Gaussian innovations, authentic calibration noise, observation irregularity, dropout or response-dependent missingness. In addition, R78 and R79 use **different new primitive source blocks**; their coverage counts cannot be treated as paired source-level differences. A next study should stress the unchanged candidates under explicitly heavy-tailed independent-unit innovations, followed by realistic missingness processes and independent original-source audits.

**Release decision:** no estimated robust simultaneous-band procedure is qualified for general nominal 90% coverage. W3 #289 and missingness #296 remain open; experimental research stays in draft branches; the stable 1.1.0 package and unreleased version 1.2 stay unchanged.

[Read R78 temporal covariance evidence](w3-temporal-covariance-robustness-r78.md) · [Read how to interpret source-level audits](interpreting-w3-coverage-and-source-audits.md) · [Source and figure ledger](../development/w3-r79-nonseparable-covariance-evidence-ledger.md)
