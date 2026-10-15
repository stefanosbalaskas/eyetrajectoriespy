# R32 — exploratory 90%-nominal CR2 pointwise inclusion with fitted REML covariance

**Research-only feasibility/falsification pilot, NOT a statistical qualification or release authorization.** R31 found that observation-only Gaussian covariance components were computationally estimable in all 192 new native observation-loss cases, but participant random-slope recovery remained weak and some incompleteness regimes degraded component recovery. There is currently no warrant that plugging an estimated covariance into a CR2 Satterthwaite reference, whose derivation conditions on a known working target, yields a calibrated coefficient confidence interval.

## New independently generated original-source pilot

Fresh Gaussian seed **202610153232** and **16 original independent generating blocks**, nested **24/96 participants**, ordinary predictor-independent/dependent covariance sources, fixed Legendre-5 functional time mean basis, and **two predeclared observation regimes**: complete original native recordings and R31's native observed-time MAR point loss (nominal ~20%). Exactly **128 paired source/observation cases** (16×2×2×2), NOT 128 independent original source blocks. The R31 time-MAR mask algorithm has fixed seed `202610153132`, uses only native timestamps and participant/trial/source identity, and never accesses missing or unobserved outcomes. Original native values are deleted only, without interpolation or imputation.

On every retained source, calculate **two separate covariance targets** for exactly the same CR2 contrast, mean basis and observed rows:

1. **Simulation-known target**, reconstructed independently as `Phi_i = sum_k theta_true,k K_ik`, with correct WLS whitening and observed retained trial and time labels. This reference is permitted to access generator-known variance coefficients **only for the independent Gaussian oracle calculation**. An original complete-source R17 covariance reconstruction is required to match this target to numerical precision.
2. **Observed-only Gaussian REML plug-in covariance**, using the independent R25 estimator with its prespecified matching four-component covariance family. No true coefficients, random effects, innovations, omitted samples or simulation covariance parameters are passed into REML fitting.

Both targets are passed unchanged to the previously numerically verified **R22 scaled-Cholesky CR2** procedure, which may explicitly refuse ill-conditioned covariance adjustments. Crucially the R22 Satterthwaite df assumes a specified target; plugging in REML does not magically account for estimating that target. Every source and REML optimizer failure, numerical CR2 refusal and valid interval computation must remain a separate outcome, not an exclusion from the denominator.

## Estimand, interval construction and interpretational validity

The contrast is the modeled predictor effect at focal native time `r16.TIME[r16.FOCAL]`, with basis `[0,...,0,basis(t_focal)]`. The generating functional mean is not guaranteed to lie exactly in the fixed Legendre-5 basis. To avoid falsely attributing **basis projection bias** to covariance estimation, the primary truth-inclusion indicator is the **known generating mean's weighted projection onto the fixed observed WLS design**:

`beta_projected = argmin_b || sqrt(W)(mu_true - Xb) ||²`, with truth `c' beta_projected`.

The original generating functional slope at the focal time is recorded separately, together with the projection difference; it must **NOT** be silently interchanged with the projected estimand. This is a source-specific conditional pseudo-true parameter, not proof the functional mean basis is correctly specified or empirically identifiable. Model-mean misspecification may still influence residual-based SE behavior, a separate scientific limitation.

For each accepted CR2 target, compute **90%-nominal two-sided truth inclusion** via `|c'beta_hat−c'beta_projected| <= t_.95,df × SE_CR2`, once with the **conditional Satterthwaite df** and once with a conventional **t(G−1)** df. The same source/mean/contrast is used for oracle and plug-in. Under 16 independent generating blocks per cell, the Monte Carlo evidence is deliberately small; report Wilson 95% intervals for computational acceptance and empirical inclusion **among accepted computations**.

Also report **joint numerical success and truth inclusion / all source cases** separately from conditional-on-success inclusion, and count refusals and REML estimation failures. Never present accepted-only inclusion as unconditional 90% coverage, and never interpret a software-green CI workflow as successful statistical calibration. These data can detect severe problems but cannot support fine nominal-coverage error bounds or an estimator/method winner.

## Research gates

The R32 output does **not** qualify a fitted-target CR2/Satterthwaite interval because covariance-estimation uncertainty remains excluded from the conditional reference; sample sizes and generating blocks are insufficient; Gaussian source and fitted working families are simulation-aligned; and only a single coefficient contrast is tested. No simultaneous function-wide interval has been constructed.

The next meaningful scientific gate after this falsification pilot is a larger independently seeded procedure-specific comparison that explicitly accounts for nuisance-covariance estimation uncertainty, preserving unconditional computational failure and confidence-interval coverage, then a **separate simultaneous functional band** calibration. No fitted-covariance API promotion or release tag from R32.

Historical R20 41/256 source failures, R22 32 explicit numerical refusals and all R16–R31 original negative results remain immutable. Scientific blocker issues #289/#296 remain OPEN, all PRs draft, protected main and supported API unchanged, and version 1.2 PyPI release unauthorized.
