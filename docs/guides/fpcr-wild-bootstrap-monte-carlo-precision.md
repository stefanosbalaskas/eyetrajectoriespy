# Finite-B precision for FPCR wild-bootstrap tests

## Purpose

Version 0.20 adds a diagnostic layer for the fixed-family Gaussian FPCR wild-bootstrap tests introduced in 0.19. It answers a narrower question than a new hypothesis test:

> How much numerical Monte Carlo uncertainty remains because only B wild-bootstrap replicates were generated?

The diagnostic never changes the target-wise, maxT-adjusted, or global p-values already stored in the family-test result.

## When to use it

Use this diagnostic after `fpca_wild_bootstrap_projection_family_test()` when a bootstrap p-value is close enough to the declared alpha level that finite resampling error may matter, when B is modest, or when a report should document the numerical precision of resampling-based probabilities.

Do not interpret it as an effect-size confidence interval, a replacement hypothesis test, or evidence that the bootstrap validity assumptions are satisfied.

## Core workflow

```python
from eyetrajectoriespy import (
    fpca_wild_bootstrap_family_test_monte_carlo_precision,
    fpca_wild_bootstrap_monte_carlo_precision_frame,
)

precision = fpca_wild_bootstrap_family_test_monte_carlo_precision(
    family_test,
    confidence_level=0.95,
)

print(fpca_wild_bootstrap_monte_carlo_precision_frame(precision))
```

The function reuses the exact studentized-root matrix retained by the 0.19 test result. No FPCA fit, score regression, residual calculation, multiplier generation, or bootstrap replicate is rerun.

## Exceedance-count model

For any fixed observed statistic, each retained bootstrap replicate either exceeds the observed absolute statistic or does not. The diagnostic therefore records the exact exceedance count r out of B replicates and the raw tail-probability estimate

    p_hat = r / B

separately for target-wise, maxT-adjusted, and complete-family global comparisons.

The 0.19 reported p-value remains whatever correction was originally requested. In particular, the default plus-one value

    (r + 1) / (B + 1)

is not overwritten by r/B.

## Monte Carlo standard error

The reported plug-in Monte Carlo standard error is

    sqrt[p_hat * (1 - p_hat) / B]

This describes simulation variability in the estimated resampling tail probability. At boundary counts r=0 or r=B the plug-in MCSE is zero, so it must not be used alone as a precision statement.

## Exact binomial interval

To preserve information at the boundaries, the primary interval diagnostic is the exact Clopper-Pearson interval for the Bernoulli exceedance probability.

For each target, adjusted comparison, and global comparison the result stores:

- exceedance count;
- raw tail-probability estimate;
- Monte Carlo SE;
- exact lower and upper interval limits;
- relation of that interval to the declared alpha level.

## Alpha relation

The interval is labelled:

- `below_alpha` when the entire interval is below alpha;
- `above_alpha` when the entire interval is above alpha;
- `overlaps_alpha` otherwise.

These labels are deliberately diagnostic. They do not replace the 0.19 reject/non-reject indicators and are not a sequential-testing stopping rule.

A result whose interval overlaps alpha should be reported as having limited finite-B numerical separation from the threshold. Increasing B can reduce Monte Carlo uncertainty, but doing so does not fix model misspecification, dependence violations, multiplicity assumptions, or component-selection uncertainty.

## P-value resolution

The result exposes `pvalue_grid_step`.

With the default plus-one correction, the grid step is `1/(B+1)` and the minimum attainable reported p-value is also `1/(B+1)`. With the explicit raw empirical option, the step is `1/B` and zero is attainable when there are no exceedances.

The `alpha_resolvable` property reports only whether the minimum attainable reported p-value can reach the declared alpha. It is a numerical resolution check, not a power calculation.

## Interpretation

A narrow exact interval far from alpha suggests that Monte Carlo simulation error is unlikely to change the numerical interpretation of the resampling tail probability at that threshold.

An interval overlapping alpha indicates that the finite number of retained replicates does not sharply separate the underlying resampling tail probability from alpha. This does not establish that the scientific null is true or false.

## Limitations

The diagnostic does not:

- regenerate the bootstrap under an explicitly imposed target null;
- add strong FWER control for arbitrary subsets of null hypotheses;
- assume or establish subset pivotality;
- support clustered or repeated-participant wild-bootstrap dependence;
- propagate k/h or other data-driven component-selection uncertainty;
- quantify target measurement error or preprocessing uncertainty;
- convert fixed centered-projection tests into future-outcome tests;
- provide confidence intervals for scientific effect sizes.

## Reporting

Report B, the original p-value correction, the declared alpha, the exact exceedance count, raw r/B tail estimate, Monte Carlo SE, exact binomial interval and confidence level, the interval-to-alpha relation, and the p-value grid step.

A suitable statement is:

> Finite-resample Monte Carlo precision was assessed from the retained B wild-bootstrap draws. Exceedance fractions were accompanied by exact binomial intervals and Monte Carlo standard errors; these diagnostics quantify simulation error only and did not alter the reported bootstrap p-values.

## API links

- `fpca_wild_bootstrap_family_test_monte_carlo_precision()`
- `FPCAWildBootstrapMonteCarloPrecisionResult`
- `fpca_wild_bootstrap_monte_carlo_precision_frame()`
- `plot_fpca_wild_bootstrap_monte_carlo_precision()`
- `fpca_wild_bootstrap_monte_carlo_precision_reporting_text()`
- `fpca_wild_bootstrap_projection_family_test()`

See also [Fixed-family FPCR wild-bootstrap tests](fpcr-wild-bootstrap-family-tests.md) and [References](../methods/references.md).
