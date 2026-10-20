---
title: Why two-dimensional gaze covariance matters for functional inference
description: A methods companion to R79's nonseparable covariance simulations and maximum-statistic confidence bands
---

# Why two-dimensional gaze covariance matters for functional inference

**Methods companion · 20 October 2026 · unreleased W3 research**

Functional models of a two-coordinate trajectory represent outcomes at several time locations and both horizontal and vertical dimensions. A **simultaneous confidence band** for a functional slope must cover all of these coordinates *jointly*. Dependence across time and dependence between coordinates therefore influence the quantile of the largest standardized deviation, even when the marginal standard error at every grid point appears reasonable.

The independently source-audited [R79 experiment](w3-nonseparable-coordinate-covariance-r79.md) was designed to expose this distinction with a **known synthetic Gaussian generating law**. It does not establish an empirical model of any specific eye-tracker's recorded errors.

!!! warning "Known-source diagnostics are not observed-data estimators"
    The temporal correlation, time-varying cross-coordinate correlation and exact Gaussian slope covariance discussed below are *specified by the simulator*. Real gaze datasets do not supply them automatically, and these research results do not validate a public nominal-90% inference method. W3 #289 and response-dependent gaze-loss #296 remain open.

## 1. What is separability?

A separable spatiotemporal covariance law has a product structure: one temporal covariance component multiplied by one spatial covariance component. For two gaze coordinates, this allows the coordinate relationship to stay fixed while temporal dependence evolves according to a shared law.

R78's within-trial Gaussian innovations had **independent coordinates** and temporally correlated within-coordinate noise. R79 instead imposes **time-varying coordinate correlation** while retaining an AR(1) temporal base and time-varying marginal scale:

$$
\operatorname{Corr}\bigl(Z_1(t),Z_2(t)\bigr)=0.15+0.65t.
$$

![R79 within-trial Gaussian time-varying cross-coordinate dependence and marginal innovation scale](../assets/research/w3-r79-generating-nonseparable-covariance-law.svg)

*Figure 1.* The horizontal and vertical source error components are weakly correlated at trial start and much more strongly correlated at trial end. This functional change is deliberately *known by construction* and cannot be recovered simply by assuming the two dimensions are independent.

This is nonseparable because the coordinate mixing depends on time. In the participant design, a differently correlated latent random-effect component is shared by three trials, adding another source of dependence. The two components may be combined into a Gaussian participant-level process, but its joint covariance is no longer adequately described by the original independent-coordinate trial law.

## 2. Why does this matter for simultaneous bands?

For a slope estimate $\widehat{\beta}_1(t,d)$, a candidate simultaneous band has the schematic form

$$
\widehat{\beta}_1(t,d)\;\pm\;
c_{0.90}\widehat{\mathrm{SE}}_1(t,d).
$$

The critical $c_{0.90}$ must reflect the **maximum across the entire grid** of standardized coefficient uncertainty. It depends on covariance among all 62 slope coordinates, not just marginal standard errors. Two estimated covariance matrices may agree on every diagonal variance and nevertheless imply different distributions of the maximum deviation.

Therefore, improving marginal standard-error stability is not sufficient evidence that a simultaneously valid joint reference has been obtained. Likewise, a larger maximum critical can improve observed inclusion by widening intervals without showing that the covariance estimator is calibrated.

The R79 fixed regularizations use previously frozen diagonal smoothing. They modify both the marginal variances and the estimated Gaussian maximum-statistic reference. These numerical interventions were fixed **before** the R79 new-source outcomes; they were not selected from an observed coverage plot.

## 3. The statistical denominator is the generated dataset

In the R79 design, the independent scientific simulation units are **32 primitive Gaussian blocks per design/support/variance condition**. The study's 256 source cases are factorial evaluations, several of which share a generating block. Its 999 maximum-statistic reference draws per source and candidate estimate one critical value, not 999 new datasets.

The whole-grid inclusion event is a source-level binary indicator:

$$
I_b=\mathbb{1}\left[
\text{the entire known slope function lies in the source's 31 × 2 band}
\right].
$$

For the challenging two-anchor heteroskedastic R79 curves, fixed λ=.50 gave **24 inclusions among 32 independent source blocks**. This is **75% empirical whole-function inclusion**, not 90% and not 24/999. For repeated-trial participants, it gave **20/32**, or 62.5%. Monte Carlo uncertainty remains material at n=32.

![R79 five-method truth inclusion across two independent-unit designs and leverage supports](../assets/research/w3-r79-nonseparable-full-band-coverage.svg)

*Figure 2.* Different methods within one condition are evaluated on the same generating sources, but R78 and R79 were generated from **different independent blocks**. Between-study differences should therefore not be described as source-paired causal effects of cross-coordinate dependence.

## 4. What independent auditing guarantees

The R79-A implementation independently rebuilds all **256 original Gaussian X/Y source arrays**, the time-varying coordinate mixing, the participant-level correlated latent effect, the known Gaussian reference and the data-estimated HC3 candidates. It also checks the full set of **1,278,720 original conditional maximum-statistic values**, criticals, source-level pivots and immutable SHA256/source identities. Both original [R79 science](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483619384) and independent [R79-A audit](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483939543) passed their dedicated numerical jobs.

This qualifies the **computational reproduction of the tested experiment**. It does not qualify the procedure for real gaze trajectories, non-Gaussian measurement errors, unknown temporal or spatial covariance, irregular recording times or response-dependent missingness.

In particular, knowing the true joint Gaussian covariance is possible in these simulations because the generation law is explicitly controlled. That oracle reference is valuable for diagnosing where candidate estimators fail but must not be presented as an attainable observed-data reference.

## 5. Next scientific boundary

Nonseparable *Gaussian* covariance does not stand in for all realistic gaze measurement processes. The next logically distinct falsification is the behavior of fixed covariance regularization under **heavy-tailed independent-unit errors**, including extreme leverage and participant-level clustering. Missingness and irregular time grids then require their own source designs, prespecified acceptance gates and independent audits.

The appropriate conclusion from R79 is narrow: **in the specified independently audited nonseparable Gaussian source law, fixed source-observable regularization improved simultaneous functional slope inclusion relative to baseline HC3, but substantial undercoverage remained under sparse influential-unit support.**

[Read the R79 scientific results](w3-nonseparable-coordinate-covariance-r79.md) · [Full source and figure ledger](../development/w3-r79-nonseparable-covariance-evidence-ledger.md) · [W3 research dashboard](../development/research-scientific-dashboard.md)
