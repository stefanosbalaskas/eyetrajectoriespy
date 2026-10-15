# W3 R39 — nuisance variance coordinate and restricted-likelihood offset sensitivity

**Research-only preregistered numerical diagnostic.** Direct successor to the original R38 [two-initialization nuisance likelihood counterexample](w3-r38-dualseed-profile-results.md). Do not label this an independently replicated experiment, globally optimized REML estimator, type-I-calibrated boundary test, or covariance-estimation-aware functional confidence interval.

## Why this question is narrower than generic optimizer replacement

R38 found substantial starting-point-dependent **nuisance restricted negative loglikelihood disagreement at fixed random-slope variance**, especially in true-positive slope states, although the optimizer returned success. Its poor local outcome commonly placed **participant-intercept variance extremely close to its positive lower box bound**, while trial variance compensated. The original log-variance gradient is `variance_ratio * linear_variance_ratio_gradient`, so it can become deceptively small as the variance approaches its numerical lower bound. In addition, L-BFGS-B's relative objective termination may behave differently when the raw restricted NLL includes a large arbitrary additive constant.

R39 isolates these two hypotheses by using **the same Gaussian objective, same observed data, same nuisance variance box, same analytic derivatives and same solver**, changing only (a) mathematical coordinates and (b) an additive constant that has no effect on the location of the true objective minimum.

## Frozen factorial numerical protocol

Original Gaussian seed `202610163737`, **R37 generating block 2**, all four paired ordinary/extreme leverage × true-zero/positive-slope source states. **No new generating blocks**, four paired data conditions only, 24 participants, native irregular repeated trials. At fixed random-slope variance ratios **0, 0.1, 0.75, 1.75, 3.5**, reoptimize the three nuisance variances (participant intercept, trial, sensor).

Three frozen nuisance seeds per fixed ratio are original R37's **best** and **worst** converged four-start solutions, and their log-coordinate midpoint (= geometric midpoint of the three component *physical* variance ratios). These are **numerical starts, not independent data draws**.

Factor A: **log variance ratios** versus **direct positive linear variance ratios**. Factor B: **raw Gaussian restricted negative loglikelihood** versus the identical objective minus one case/ratio-specific constant, frozen as its value at the R37 best nuisance initializer. There is no artificial regularization, hidden data-dependent penalty, change to the likelihood or change of original lower/upper nuisance physical-variance ratio limits `[exp(-13.8), exp(7.0)]`.

**4 paired data states × 5 fixed slope ratios × 3 nuisance starts × 2 coordinate systems × 2 objective offsets = 240 prespecified L-BFGS-B fits.**

Use identical optimization settings across all four method conditions: maxiter 250, ftol `1e-12`, gtol `1e-8`, maxls 45. The R35 log-variance Gaussian restricted-likelihood and analytic score are unchanged. In the linear-ratio coordinate the score is re-expressed using the exact chain rule `score_ratio = score_log / ratio`. Tests cross-check value, gradient transformation, additive-offset invariance and independent finite differences at the original exact-zero random-slope boundary.

For every run, retain optimizer return status, objective recomputed **on the same unshifted original NLL scale**, iterations, fitted three nuisance components, whether physical bounds were encountered, reconstructed objective discrepancies and projected KKT residual in a **common linear physical nuisance-variance ratio coordinate**. A comparison tolerance `0.001 NLL` summarizes numerical agreement only; its magnitude is not a significance test. Record all solver failures/nonconvergence and **do not select only favorable successful starts** to count completed evaluations.

## Interpretation, failure modes and next statistical gate

A method may recover lower objective solutions at more starting points without proving global optimality. If centering improves recovery, that reveals an optimizer stopping-rule issue, not an improved Gaussian model. If linear coordinates improve recovery, that reveals parameterization sensitivity, not a finding that random-slope variation truly exists. Direct linear-coordinate optimization is still subject to the original strictly-positive nuisance-variance bounds; it does not introduce a new exact-zero nuisance-component model.

Do not recommend adopting a modified estimator on the basis of one reused generating block. A numerically better candidate would need separate fresh-source replication, broader nuisance geometry, stable KKT/interval diagnostics and failure-inclusive empirical qualification. This research is upstream of, and scientifically distinct from, variance-component test reference calibration, working-covariance uncertainty, nominal **90% pointwise functional CR2 intervals**, and whole-function simultaneous 90% bands.

Keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) open. Retain the original negative evidence from R20, R22, R33–R38. **No protected-main merge, supported-API promotion, version 1.2 release tag or PyPI publication**.
