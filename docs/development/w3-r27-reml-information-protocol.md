# R27 — original fixed-design Gaussian REML component information

**Research-only local-identifiability diagnostic, not estimator approval or confidence-interval calibration.** [R26 PR #328](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/328) replicated REML's trial/sensor covariance-component recovery advantage in **16 independent source blocks and 384 paired cases**, yet matching-family random-slope variance estimates were below 5% of generating truth in 52/192 REML cases. Paired whole-block bootstrap intervals did not establish an overall REML advantage for slope or intercept. Numerical convergence and nonsingular moment kernels alone cannot establish practical parameter information.

## Original frozen study design

Reuse exact R26 generating master seed `202610153626` and **two original independent source blocks (0, 15)**, participant sizes n=24 and 96, ordinary-support predictor-independent and predictor-dependent Gaussian covariance source mechanisms, and the matched covariance family only, with native trial/timing/participant structure unchanged. **Eight fixed original design configurations; no new independently generated source designs.** Gaussian source-known variance coefficients are used **only to define this oracle information reference**, not to estimate working covariance for new eye-tracking observations.

For each frozen design, calculate the exact Gaussian **restricted-likelihood expected Fisher information** for four covariance variance components as

`I_jk = 1/2 tr(P K_j P K_k)`, where `P = V⁻¹ − V⁻¹ Z (Zᵀ V⁻¹ Z)⁻¹ Zᵀ V⁻¹`, `K_j= ∂V/∂theta_j`, and `Z= sqrt(W) X`.

Compute this from original within-participant covariance blocks without a global dense P matrix using the algebraic decomposition into `tr(V⁻¹ K_j V⁻¹ K_k)`, the GLS leverage terms, and the Gram cross-products. Standardize information to the **log-variance parameterization**, `I_log,jk = theta_j I_jk theta_k`. Report its eigencondition number, component correlation, and diagonal of `I_log⁻¹`, whose square roots are **local asymptotic** standard errors of log component variances under the *specified known Gaussian design*. Large slope-relative uncertainty warns that an estimator may be near a boundary despite positive true covariance and mathematically full-rank scores.

## Independent conditional Gaussian score reference

For each of the eight original frozen designs, draw **128 independent conditional Gaussian innovation vectors** (separate seed `202610153727`) with the original known covariance, and compute the analytical REML score after refitting GLS fixed effects to each noise vector. Check the score vector against the separately tested R25 negative restricted-likelihood gradient. Describe the empirical score covariance relative to the exact expected information and the mean Gaussian score, without requiring empirical Monte Carlo identity in only 128 draws.

The **1,024 conditional noise vectors** are repeated draws at eight fixed source designs, not 1,024 new independent generating blocks, and must not be pooled as independent source replicates. The separate exact expected information, not just simulated covariance, is the main numerical/statistical contract.

## Strict boundaries

The Fisher information is a **local expected information** calculation conditional on a correctly specified Gaussian covariance structure at **known true source coefficients**. It is not a covariance-estimation procedure itself and does not account for model misspecification, trial-dependent physiological departures, empirical distributional biases, or the sampling distribution of bounded REML estimators at a near-zero variance boundary. It cannot qualify the currently conditional CR2/Satterthwaite df with fitted covariance, 90% pointwise or simultaneous functional bands, or public release.

Scientific issues #289/#296 stay open. R20 41/256 original failures and R22 32 numerical refusals remain immutable. All PRs draft, protected main untouched, 1.2 release tag and PyPI publication prohibited.
