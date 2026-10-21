---
title: Missing gaze, independent-unit support, and pointwise feasibility
description: Methods companion for the R82 complete/MCAR/MAR/MNAR observation-process audit
---

# Missing gaze, independent-unit support, and pointwise feasibility

**Methods companion · 21 October 2026 · W3 R82**

The purpose of [R82](w3-response-dependent-gaze-loss-r82.md) is to distinguish *having many observed gaze samples* from *having the independent-unit information needed to estimate a functional slope*. This is fundamentally different from improving Gaussian covariance estimates under fully observed trajectories.

!!! warning "This is not an MNAR adjustment"
    The R82 available-case slopes are deliberately naive diagnostics. The stable public function-on-scalar regression still refuses missing gaze. No new estimator, imputation rule, missingness-robust confidence interval or general nominal-90% band is released. Research issues #289 and #296 remain open.

## 1. Missing completely at random, at random, and not at random

With MCAR, gaze availability is independent of predictors and outcomes. With the frozen R82 MAR law, availability depends on **recorded predictor, time and trial index**, not on the outcome after conditioning on those recorded variables. With the R82 MNAR law, sample loss additionally depends on the **true response residual**, including at times when its value is subsequently unobserved. The selection probabilities are known only because the observations are simulated.

![Analytic R82 MCAR, MAR and outcome-dependent MNAR source laws](../assets/research/w3-r82-analytic-mcar-mar-mnar-loss-laws.svg)

*Figure 1.* The latent outcome moves the MNAR missingness probability, but not the MAR probability at fixed recorded predictors and time. The curves are simulator parameters, not a fitted observation model for a real sensor.

R82 changes **only the observation masks** over the same fully generated trajectory within a source condition. All mechanisms share one uniform mask-generating field, allowing coherent **within-source descriptive** comparisons. Different source/design/support/variance conditions do not constitute independent replications of each other merely because each yields four masks.

## 2. Missingness can destroy the predictor's local support

The original source has 72 independent curves or 36 participants with three trials. Under two-extreme-unit support, exactly one negative and one positive independent predictor extreme can be essential for the deliberately strict pointwise feasibility gate.

At a given time and coordinate, R82 refuses the naive OLS slope unless there are at least eight independent units, a rank-two intercept/slope design and **at least one observed negative and one observed positive extreme**. A central predictor observation does not replace a missing signed extreme under this prespecified rule.

![R82 observed samples versus refused whole-functional-grid positions](../assets/research/w3-r82-missingness-retention-and-grid-refusal.svg)

*Figure 2.* In the adverse two-anchor independent-curve setting, over **83% of coordinate samples are still present under MNAR**, yet approximately **34 of 62 local positions** fail the signed-anchor support gate. This is an intentionally conservative design-feasibility result, not a theorem that OLS mathematically cannot be fitted without extreme units.

In the participant design, the unit at a given time and coordinate remains available if **any of its three trials** is observed. The average uses only observed trials; the analyst still has at most 36 independent participants. Treating trial observations as independent participants would create pseudo-replication.

## 3. Why available-case slope error is not a complete missingness-bias analysis

A naive pointwise fit can use different individuals at different times and coordinates. Its error can therefore reflect outcome selection, changes in leverage, different observed-unit weights and the absence of data in parts of the functional grid.

![R82 source-wise available-case versus complete-source slope changes](../assets/research/w3-r82-available-case-slope-deviation.svg)

*Figure 3.* Source-average absolute masked-versus-complete slope differences use only the grid positions that remain estimable. The curves for two- and sixteen-anchor support **do not necessarily use identical sets of positions**.

One cannot conclude that a missingness mechanism improves or worsens estimation merely because its selected-position mean absolute error is smaller or larger. The refused-position fraction must be reported. The same caution applies when comparing source-wise generating-truth error means or interpreting MAR and MNAR under different overall retention probabilities.

## 4. What was independently audited?

Original [R82 source run #39571308151](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151) passed 12/12 scientific jobs; independent [R82-A real original-source replay #39572315409](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409) passed 4/4. Independently implemented numerical reconstruction verified **256 original complete X/Y source conditions, 1,024 MCAR/MAR/MNAR/complete masks, mask and source digests, native refusal flags, participant trial aggregation, signed-anchor gates and pointwise slope diagnostics**, with a true denominator of 32 independent primitive blocks per fixed condition.

That establishes the computational consistency of **one prescribed synthetic source and observation mechanism**, not an empirical dropout model. No public package code was changed to accept NaN trajectories.

## 5. What would constitute a missingness-aware next step?

A defensible inferential extension would first specify the target functional estimand, define why sample loss may be ignorable or nonignorable, justify observed auxiliary variables or sensitivity parameters, handle irregular and partially observed trial grids, and propagate uncertainty from both outcome and observation models.

Such an extension would need prospectively frozen source designs, source-independent coverage and failure accounting, and external checks on real recorded gaze loss. Until those conditions are met, the valid response to incomplete input is the existing **explicit refusal** rather than unqualified 90% bands.

[Full R82 study](w3-response-dependent-gaze-loss-r82.md) · [All original sources and plots](../development/w3-r82-observation-process-evidence-ledger.md) · [Earlier R81 skewed-unit test](w3-skew-unit-contamination-r81.md)
