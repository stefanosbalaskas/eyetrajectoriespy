---
title: Can functional covariance regularization reduce simultaneous-band undercoverage?
description: Independent source and numerical audit of two frozen positive-definite HC3 regularizations in R77
---

# Can functional covariance regularization reduce simultaneous-band undercoverage?

**Research article · 20 October 2026 · R77 original experiment and independent R77-A audit**

!!! danger "Research result, not a qualified confidence interval"
    **Stable PyPI eyetrajectoriespy is 1.1.0.** R77 exists only in separate unreleased research [PR #405](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/405) and independently audited [PR #406](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/406). The candidate methods are **not public stable APIs** and **do not establish reliable nominal-90% simultaneous confidence bands**. [Scientific blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [response-dependent missingness blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. The release of 1.2 remains on hold.

## From numerical correctness to finite-sample uncertainty

[The R70–R75 evidence article](when-w3-simultaneous-bands-undercover.md) identified a recurring discrepancy: regression coefficients, HC1/HC3 marginal standard errors and bootstrap maximum-statistic quantiles agreed with independent numerical implementations, yet simultaneous 90% functional slope bands sometimes missed their known generating truth in most independent datasets. [R76 subsequently varied independently observed influential predictor support](how-independent-leverage-support-affects-coverage.md). Increasing extreme-predictor support coincided with improved truth inclusion, suggesting that sparse slope-variance contributors and unstable *source-specific* standard errors were important in the tested Gaussian setting.

R77 asks a different question: **can an entirely data-estimated covariance regularization change those finite-sample failures when influential independent observations remain scarce?** The investigation is deliberately prospective. The strength of the regularization, local smoothing width, generating seeds, primary comparisons and simulation source units were fixed *before* examining R77 outcomes.

## What was held fixed, and what was altered?

The unchanged R76 slope-weighted HC3 factor for independent unit $i$ and functional coordinate $k$ was

$$
F_{ik}=\frac{a_i r_{ik}}{1-h_i}, \qquad C_{HC3}=F^{\mathsf T}F,
$$

where $a_i$ is the fitted slope's OLS design weight, $r_{ik}$ the observed residual and $h_i$ the corresponding unit leverage. This covariance already incorporates independent-unit contributions, but when a few units dominate, its realized diagonal elements can vary sharply across the 62 grid cells (31 times × two coordinates).

For the two **fixed** regularization strengths $\lambda\in\{0.25,0.50\}$, R77 compared

$$
C_\lambda=(1-\lambda)C_{HC3}
+\lambda\operatorname{diag}
\left(K_7\operatorname{diag}(C_{HC3})\right).
$$

Here $K_7$ is a simple, seven-time-point, edge-truncated moving average applied to diagonal variances **separately by coordinate**, never across the two gaze dimensions. The candidate covariance remains positive-definite under the verified positive-diagonal conditions. For each source, Gaussian draws from $N(0,C_\lambda)$ are standardized using **that same candidate covariance diagonal** and the *higher* empirical 90th percentile of the maximum absolute standardized coefficient departure is used. Importantly, both candidate covariances are constructed **only from the data-estimated HC3 residual factor**. The Gaussian law known to the simulator supplies a separate comparison benchmark, **never a parameter or adjustment input to either candidate**.

Regularization alters the estimated **marginal standard-error grid and joint correlation/critical-value reference** together; it is not valid to describe the change as an isolated correction to one factor or as a theoretically established robust variance estimator. The fixed local diagonal smoothing also imposes an assumption that may be wrong for nonstationary or strongly dependent participant trajectories.

## Original source design and independent verification

The prospectively frozen [R77 protocol](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r77-prespecified-covariance-shrinkage-20261020/docs/development/w3-r77-prospective-covariance-regularization.md) generated **32 genuinely new independent primitive Gaussian blocks**, with two native-unit configurations: 72 independent curves and 36 independent participants observed over three complete trials. Every block paired two extreme-predictor support levels (two or 16 **independent** x = ±4 units) with two variance laws (constant Gaussian standard deviation and predictor-dependent $s_i=1+0.75|x_i|$). Thus **256 source cases** were evaluated, but **each design/support/variance cell still contains only 32 independent generating blocks**. Repeated source conditions are paired and cannot be treated as 256 statistically independent replicates.

For every source, five reference distributions produced exactly **999 maximum-statistic draws**: unchanged package W3 wild-HC1, original HC3 Gaussian, the two fixed regularized Gaussian candidates, and the **simulation-known** Gaussian benchmark. Original [workflow #39403101425](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39403101425) passed **12/12 dedicated scientific jobs**, completed **256/256 sources**, and recorded **zero refused fits** in the immutable original source [artifact #12255412132](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39403101425/artifacts/12255412132).

A **separately implemented** read-only replay of the actual original evidence passed [R77-A workflow #39403655264](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39403655264), **4/4 independent audit jobs**, and verified all **256 original X/Y datasets, 1,278,720 original reference maxima**, original SHA256 members, case-wise criticals, source-wise 31×2 truth-inclusion events and source-paired contrasts. Its archived report is [artifact #12255897976](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39403655264/artifacts/12255897976). Green scientific workflows and complete independent numerical replay establish reproducibility—not formal inferential calibration.

## Observed truth inclusion: adverse and better-supported designs

![Independently audited R77 source-level whole-function truth inclusion for baseline and two regularized covariance choices across two independent extreme-anchor supports](../assets/research/w3-r77-audited-regularization-coverage.svg)

*Figure 1.* Source-level truth-inclusion counts of the **entire 31×2 slope function** under predictor-dependent heteroskedastic Gaussian noise. Each condition has 32 independent generating blocks; five methods are evaluated on the **same** generating datasets within condition. The oracle uses covariance known only in the simulation.

| Band reference | Curves, 2 anchors | Participants, 2 anchors | Curves, 16 anchors | Participants, 16 anchors |
|---|---:|---:|---:|---:|
| Original W3 wild-HC1 | **0/32** | **4/32** | 16/32 | 25/32 |
| Data-estimated HC3 Gaussian | **1/32** | **9/32** | 28/32 | 27/32 |
| Frozen regularization, λ = 0.25 | **22/32** | **23/32** | 28/32 | 30/32 |
| Frozen regularization, λ = 0.50 | **24/32** | **24/32** | 30/32 | 30/32 |
| Source-known Gaussian reference | 27/32 | 29/32 | 30/32 | 29/32 |

Under two influential independent high-noise units, the original HC3 estimate includes the entire generating slope in only **1/32 curve datasets** and **9/32 participant datasets**. In the same source blocks, fixed λ = 0.50 regularization increases observed inclusion to **24/32 in both designs**. This is a sizeable source-matched descriptive difference, not a calibrated superiority result. **24/32 corresponds to 75% empirical inclusion**, below 90%. With 32 independent source blocks per condition, Monte Carlo uncertainty is also substantial.

The higher-support comparator offers a different perspective: once 16 independent extreme predictor observations are available, both the original HC3 and regularized references show markedly higher observed inclusion in these particular Gaussian mechanisms. That does not imply that 16 influential units constitute a universally adequate sample size, or that changing support isolates an independent causal treatment.

### Constant-variance counterexamples are retained

R77 prospectively retained constant-Gaussian-variance cases. With two extreme anchors, the curves' baseline HC3 / λ=.25 / λ=.50 / source-known inclusion was **15/32, 23/32, 25/32, 26/32**, and participants' counts were **20/32, 26/32, 27/32, 32/32**. These are not replacements for the adverse results and have not been selected to declare a winning method. They show what occurred in the specified simpler law, with n=32 independent sources each.

## Separating standard-error stabilization from the reference critical

![Independently audited R77 source-specific lower-tail estimated SE ratios and simultaneous Gaussian maximum criticals for baseline and fixed regularized candidates](../assets/research/w3-r77-audited-se-lower-tail-and-criticals.svg)

*Figure 2.* Two-anchor predictor-dependent heteroskedastic condition. Left: across-source mean of each source's 10th percentile over the 62 grid cells of its data-estimated SE divided by **simulation-known** true SE. Right: across-source mean of each data-estimated Gaussian 90% maximum-statistic reference critical. The source-known SE appears **only in this diagnostic**, not in the candidate estimator.

| Design / metric | HC3 baseline | Fixed λ=.25 | Fixed λ=.50 |
|---|---:|---:|---:|
| Curves: mean source-wise 10th-percentile SE/true-SE ratio | 0.445 | 0.619 | 0.719 |
| Participants: mean source-wise 10th-percentile SE/true-SE ratio | 0.457 | 0.517 | 0.560 |
| Curves: mean Gaussian max critical | 2.746 | 2.988 | 3.056 |
| Participants: mean Gaussian max critical | 2.305 | 2.837 | 3.016 |

Both aspects of uncertainty change. Regularization reduces the apparent instability of the HC3 marginal-SE lower tail **and** increases the simultaneous Gaussian critical, especially in repeated-trial participants. The stronger critical can materially widen the band independently of smoothing the marginal SE. Hence the observed improvement is not solely evidence that the covariance *estimate itself* is more accurate; conservative widening, altered correlation structure and finite-sample stochastic variability can all contribute.

## What the evidence supports—and what remains open

R77 provides an independently replicated **numerical mechanism and controlled simulation comparison**, not a new validated W3 inference method. The tested design is fully observed, Gaussian, uses a complete 31×2 function grid, has a particular participant random-effect law, and examines exactly two fixed strengths of a particular time-diagonal regularization. It does not demonstrate coverage with response-dependent missingness, irregular observation times, heavy-tailed errors, misspecified or changing temporal covariance, AOI structure, or authentic sensor calibration loss.

Moreover, the generator-known Gaussian reference is not available when working with actual eye-tracking participants. A credible next study must independently stress candidate estimators against **nonseparable/nonstationary covariance, heavier-tailed unit innovations, sample-size imbalance and irregular response-dependent gaze loss**, with genuine unmodified source retention and rejection/inclusion counts. Candidate performance must also be checked for overconservatism and bandwidth/regularization misspecification **without choosing settings after viewing coverage**.

**Practical status:** the new findings are suitable as a *research-development evidence article* and source-grounded vector figures. They do **not** authorize a public robust simultaneous-band API, closing W3 scientific blocker #289, relaxing the missingness boundary #296, merging experimental code into protected `main`, or publishing eyetrajectoriespy 1.2.

[Compare R70–R75 falsifications](when-w3-simultaneous-bands-undercover.md) · [R76 information-concentration experiment](how-independent-leverage-support-affects-coverage.md) · [R77 original/audit PRs](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/406)
