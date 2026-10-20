---
title: How rare asymmetric unit shocks affect simultaneous functional inference
description: Centered Bernoulli contamination, known Student-t5 mixtures, sample independence, maximum-statistic bands and source auditing
---

# How rare asymmetric unit shocks affect simultaneous functional inference

**Methods companion · 20 October 2026 · W3 R81**

The [R81 independently audited simulation](w3-skew-unit-contamination-r81.md) provides a carefully constrained demonstration: confidence-band procedures can be numerically reproduced exactly, and an estimated covariance regularizer can improve inclusion in a synthetic design, **without that being sufficient to establish nominal-90% whole-function confidence coverage**.

The methodological challenge is not just heavy tails. Rare asymmetric measurement shocks can affect every time point and both gaze coordinates of an **independent participant or curve**.

!!! warning "Known simulation mechanisms are unavailable in observed data"
    The Bernoulli event probability p=.08, contamination amplitude .16, time/coordinate shock profile, Student-t5 degrees of freedom and generating covariance are **all specified by the R81 simulator**, not estimated from recorded gaze. Results do not establish that real eye-tracker contamination follows this law. W3 #289/#296 remain open and experimental estimators are unreleased.

## 1. A persistent unit shock is not ordinary white noise

For R81, a unit-level contamination indicator $B_i$ is Bernoulli with p=.08. Its centered functional contribution is

$$
C_i(t,d)=0.16(B_i-0.08)(0.75+0.25t)
\begin{bmatrix}1 & -0.65\end{bmatrix}_d.
$$

Unlike independently injected sample noise, one realization affects an entire independent source trajectory and, where applicable, the same participant's three trials. The shock has **zero unconditional mean** but asymmetric realizations: a rare large event and a common smaller shift of the opposite sign.

![Analytic rare centered asymmetric contamination profile and its known covariance contribution](../assets/research/w3-r81-analytic-skew-contamination-law.svg)

*Figure 1.* The rare-event trajectory and fraction of true marginal slope-source variance attributed to the contamination. This is a theoretical generating-law illustration, not an estimate of real sensor disturbances.

Independently drawn Student-t5 radial multipliers from the preceding R80 design remain present, multiplying the correlated Gaussian base. Thus R81 tests **a combined heavy-tailed and skew-contamination law**, not one factor in isolation. This distinction prevents attribution of any R80–R81 difference to contamination alone.

## 2. Mean-zero contamination can still change covariance and simultaneous criticals

Centering $B_i$ by p protects the original population slope, but it does not remove the contamination variance:

$$
\operatorname{Var}(C_i(t,d))
=0.16^2(0.08)(0.92)H(t,d)^2.
$$

Cross-coordinate and cross-time contamination covariances also arise because the same Bernoulli indicator multiplies the entire signed functional profile. In addition to the original nonseparable Gaussian covariance and shared Student-t5 radial shocks, R81 therefore has a **rank-one functional covariance component** from the rare event.

A 31-time-point × 2-coordinate simultaneous band must contain all 62 generating-slope values. Its correct source maximum-statistic reference involves the joint law across those coordinates, not merely 62 separate pointwise normal limits.

## 3. The source-known benchmark must include both the t scales and asymmetry

The R81 known-law reference takes a weighted sum of independent units. Given fixed source design weights $a_i$ and known scales $s_i$, it independently draws each replicate's unit-specific chi-square Student-t radial multipliers and Bernoulli events, combines their effects over the whole functional grid, and standardizes by the **true variance including the centered contamination term**.

That reference is a simulation benchmark, not a usable observed-data correction. In particular, an ordinary Gaussian reference, a single shared Student-t multiplier, symmetric event sampling or a known-SE denominator copied from R80 would evaluate a *different generating mechanism*.

All four data-estimated candidates were deliberately unchanged from R80: wild-HC1, baseline residual HC3 Gaussian and the two frozen λ=.25/.50 positive-definite HC3 covariance adjustments with seven-time smoothing.

## 4. Count independent generating source datasets, not trial samples or reference replicates

The R81 experiment generated **32 new primitive blocks**, evaluated over two observational units, two leverage configurations and two variance laws, giving 256 source-condition evaluations. The correct denominator for empirical truth inclusion in any one such design/support/variance cell remains **32 independent primitive sources**.

Each source retained **five sets of 999 maximum-statistic draws**. Those 999 draws approximate candidate criticals. They do not multiply the independent source sample size, and three repeated trials do not multiply the number of independent participants.

![Five-reference R81 full-functional-slope inclusion over new independent source blocks](../assets/research/w3-r81-skew-contaminated-whole-band-inclusion.svg)

*Figure 2.* Under the difficult two-anchor heteroskedastic condition, frozen λ=.50 includes the full generating slope in **24/32 curves and 24/32 participants**. That is 75% observed source inclusion, **not** nominal-90% calibration. The source-known skewed Student-t5 mixture includes 29/32 in each, which remains a finite 32-source result.

## 5. Estimated marginal uncertainty and whole-grid dependence interact

![R81 marginal SE ratio lower tails and estimated Gaussian maximum-statistic criticals](../assets/research/w3-r81-skew-se-tail-and-criticals.svg)

*Figure 3.* Mean source-specific 10th-percentile estimated/known marginal SE ratios and mean estimated Gaussian simultaneous criticals for baseline HC3 and the two fixed regularizers.

With two high-leverage heteroskedastic units, both adjustments raise some lower-tail estimated standard errors and change the critical value of the Gaussian reference. Better empirical truth inclusion cannot be equated mechanically with accurately estimated covariance: wider bands can cover the generating slope more frequently without correctly representing its sampling distribution.

This is why a defensible evaluation retains source-level inclusion events, candidate criticals, marginal scale diagnostics, pairing/discordance, source failures, and the simulator-known reference, rather than reporting only a favorable average coverage count.

## 6. Independent numerical reproducibility is necessary, not sufficient

The original [R81 scientific workflow #39490888383](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383) passed 12/12 scientific jobs, and the separately coded [R81-A original archive audit #39491187099](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099) passed 4/4. R81-A independently reconstructed **256 X/Y source datasets, zero source refusals, all 1,278,720 original conditional maximum-statistic values**, the original true Student-t5 and asymmetric-event reference, source truth classifications and SHA256 manifest.

This supports the **numerical accuracy and reproducibility of the prespecified synthetic experiment**. It does not establish actual gaze errors as Student-t5, calibrate an estimated covariance in real recordings, or solve the response-dependent observation problem.

The next scientific problem with greatest immediate relevance is **missing gaze as an observation process**, particularly where the probability of dropout varies with true eye position, velocity, participant and trial conditions. That needs a distinct frozen experiment and independent source replay, not retroactive interpretations of the fully observed R81 results.

[Read the complete R81 study](w3-skew-unit-contamination-r81.md) · [Open original source and figure ledger](../development/w3-r81-skewed-unit-evidence-ledger.md) · [Earlier R80 Student-t5 experiment](w3-student-t5-heavy-tail-inference-r80.md)
