# Bayesian research figures — synthetic and algorithm-derived

!!! warning "Illustrative, not scientifically calibrated"
    These SVGs use actual B5/B6/B8 fitted/conjugate objects on deterministic **synthetic** data, except the separately identified exact Normal–Normal reference. They are not participant outcomes and do not imply nominal coverage.

## Time-varying Bayesian regression

![Fitted Gaussian-spline condition posterior with pointwise and finite-grid joint credible bands](../assets/research/b5-credible-bands.svg)

Pointwise credible intervals and a *joint finite-grid posterior band* from the B8 fixed-noise model. Neither is a frequentist confidence band.

## Declared prior versus fitted posterior

![Gaussian-spline prior compared with fitted B8 posterior curves](../assets/research/b8-prior-versus-posterior.svg)

The prior uses the exact declared independent Gaussian spline-coefficient distribution.

## Conditional sparse-score benchmark

![Known-basis Gaussian posterior sparse curve reconstruction](../assets/research/b6-fixed-population-sparse-scores.svg)

The mean and eigenfunctions are **given as known truth**; these posterior reconstructions cannot be advertised as learned Bayesian FPCA.

## Posterior predictive discrepancy

![Fixed-noise Bayesian spline model posterior predictive check](../assets/research/b5-posterior-predictive-check.svg)

A descriptive marginal SD check, not an established posterior predictive validation test.

## Genuine conjugate Normal–Normal SBC rank histogram

![Known-prior Normal Normal rank histogram from exact posterior](../assets/research/b5-exact-normal-sbc-ranks.svg)

The SBC simulator uses an explicit scalar Gaussian prior, Gaussian likelihood and its analytic exact posterior. This tests rank-handling infrastructure **only**, not sparse FPCA calibration.

The next figure tranche requires a **learned** eigenbasis, component sign/rotation alignment, near-tied posterior eigenspaces and empirical functional-model SBC.

[Research roadmap](bayesian-research-programme.md) · [Programme #236](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/236)
