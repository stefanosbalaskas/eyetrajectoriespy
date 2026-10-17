# W3 R57 — prospectively frozen exact-zero nested Gaussian REML likelihood comparison

**Research-only mathematical and numerical pilot, not a calibrated variance-boundary hypothesis test.**

## Why R57 is necessary

R56 established with **16 newly independent Gaussian primitive source blocks** that the original R49 strictly positive slope-variance optimizer ratio lower bound is a poor standalone proxy for a **structurally zero** generating random-slope variance. Under ordinary leverage the selected lower-positive-ratio status agreed between structurally zero and positive generating states for all 16 paired blocks. That fitted bound is not a genuine null model containing `theta_slope=0`.

R57's objective is to construct an actually **nested** Gaussian restricted-likelihood comparison that includes the *exact* zero participant-slope variance parameter. It must not confuse numerical feasibility of a likelihood-gap statistic with an inferentially calibrated boundary test.

## Genuine nested Gaussian likelihood and pre-existing mathematical references

Reuse the existing, numerically studied R35 `fixed_slope_reml_objective` for the null with participant Gaussian slope variance fixed **exactly zero**, and the existing R37 `continuous_reml_objective` for the alternative with slope variance constrained **nonnegative, including the exact zero endpoint**. Both fit the same observed Gaussian participant covariance kernels and remove the same fixed mean by the restricted Gaussian likelihood.

Let `reference(y)=max(mean((y-X beta_WLS)^2),1e−8)`, computed from observed native data. The participant intercept, trial and sensor covariance variance ratios remain strictly positive, with common log bounds `[−13.8,7]` as in the earlier Gaussian studies. Define:

- **H0 nested model:** `theta_slope=0` precisely; three nuisance log variance ratios free within the original positive bounds.
- **H1 nested model:** same three nuisance parameters, with fourth **linear slope variance ratio** `theta_slope/reference(y)` in the closed interval **[0,100]**. The alternative **contains the null**; no `log(0)`, substitute 10⁻⁶ or positive-box face is used for the slope parameter.

Both R35 and R37 analytic Gaussian score and negative REML objectives were already investigated in R35–R39. R57 adds strict physically projected KKT and source-level acceptance gates to both, rather than changing the underlying likelihood.

### Frozen optimization starts and numerical refusal contract

H0 uses two fixed original three-positive-ratio starts: `(.1,.1,1)` and `(.6,.3,1)`. H1 uses four fixed three-positive-ratio plus linear slope-ratio starts: `(.1,.1,1,0)`, `(.6,.3,1,.01)`, `(.1,.1,1,1)` and `(.6,.3,1,10)`. Each original start is separately retained with optimizer success, iterations, NLL, reconstructed independent Gaussian objective, analytic physical score, physical KKT and potential error.

Use the unchanged `L-BFGS-B` numerical optimizer with original positive nuisance log coordinate bounds, alternative slope ratio **[0,100]**, maximum iterations 450, `ftol=0`, `gtol=1e−10`, 80 line-search steps and 2400 function evaluations. Recompute the analytic objective at the returned parameters and demand reconstruction error **≤10⁻⁶**, successful optimizer flag, physical-ratio-coordinate projected **KKT≤0.001**, and NLL at most **0.001** above the **lowest NLL observed across *all* prespecified starts**, including starts that otherwise failed a numerical gate. If no candidate passes every criterion, mark that original null/alternative fit **refused**, not accepted by switching to a more convenient start or changing tolerance.

For the alternative at exactly zero, the **one-sided lower-face KKT** is essential: `∂(−REML)/∂(slope_ratio)` must be nonnegative at zero for a local minimum. A negative derivative there is a violation, not evidence of a stationary zero-boundary estimate. Convert Gaussian free nuisance log-variance score into physical ratio-coordinate score for the original projected-gradient KKT gate; retaining a tiny free physical variance ratio must not spuriously suppress a nonzero physical score.

At accepted paired H0/H1 candidates, record the raw signed **nested deviance `2(NLL_H0 − NLL_H1)`**. If the observed numerical H1 candidate is worse than H0 by more than **10⁻⁵** in NLL units corresponding to negative deviance beyond −10⁻⁵, record a **numerical nested-monotonicity refusal**. Within this numerical tolerance, retain both the raw signed value and the separately labeled nonnegative `max(0,raw)`. These are **descriptive likelihood gaps only**; do **not** attach `χ²`, chi-bar-square mixtures, p-values, null-test rejections, sensitivity/specificity, power or Type-I error.

No global Gaussian REML optimum or universally valid boundary-null distribution is established by finite multistart L-BFGS-B convergence.

## Independent Gaussian original generating design

Draw **eight genuinely new independent Gaussian primitive innovation blocks** from frozen seed **202610175757**, distinct from R53–R56 original sources, each with n24 participants and irregular repeated native gaze trials. Within each block, original ordinary and extreme predictor-dependent leverage cases share primitive Gaussian innovations and are therefore **paired**. Within each block and leverage support, structurally **true-zero** and **true-positive** generating random-slope variants share the same original mean, native design, participant intercept, trial errors, sensor innovations and observation weights. The true-zero response is obtained by subtracting *only* the R17 Gaussian participant-slope term `SIGMA_RANDOM_SLOPE × u_i × x_i × (1+0.25t)` from the true-positive original native response. The true-positive generating slope covariance retains variance `SIGMA_RANDOM_SLOPE²=0.002025`; true-zero is mathematically zero. Both null and alternative candidate likelihoods are estimated **only from observed responses/design/participant IDs** and never receive generating source covariance or primitive innovations.

The **independent scientific unit is the generating Gaussian primitive block**, n=8, not the 32 paired source-support-state cases. This is a numerical research pilot, not a conclusive variance-component hypothesis-testing study.

### Frozen denominators and original provenance

Predeclare **8 primitive blocks ×2 paired predictor supports ×2 paired generating slope states =32 original source records**; each has **one H0 fit (two starts) and one H1 fit (four starts)**: **64 original nested likelihood fit slots and 192 numerical optimizer-start records**. A source-generation or Gaussian preparation refusal retains the original null and alternative `not_attempted` placeholder starts; a multistart optimizer refusal retains all attempted starts; and a nested monotonicity refusal retains both original candidate fits and the signed deviance. No conditional success-only denominator may be substituted for the complete planned source count.

Split original independent Gaussian source execution into exactly four nonoverlapping shards: primitive block indices **0–1, 2–3, 4–5, 6–7**, with all paired support/state variants of each block in its assigned shard. Each shard writes immutable case JSON plus source seed/check-out/SHA256 manifest. The final aggregate requires all four original same-checkout SHA256-verified shards, exact expected case identities, 32 source records, 64 candidate model fit slots and all 192 numerical starts. It writes `cases.json`, `summary.json`, `source-commit.txt` and three source SHA256 hashes, and refuses any missing/altered/duplicated original science source.

Report original source, numerical H0/H1 fit and nested-monotonicity refusals separately by ordinary/extreme support and structural zero/positive generating truth, as well as the number of H1 accepted candidate solutions at exactly zero and the **descriptive** median nonnegative likelihood gap among fully accepted case comparisons. Any comparison of null/positive states is exploratory and contains only eight independent primitive sources.

## Scientific and publication boundaries

R57 tests numerical *existence* and behavior of a properly nested structural Gaussian variance-component model; it does **not** calibrate the sampling law of its likelihood gap at the zero-variance boundary. Any future nominal test must specify regularity conditions for random-effect variance component constraints and other nuisance parameters, derive or independently validate the boundary reference distribution and report an explicit actual empirical null Type-I rate with independent Monte Carlo precision. A fixed-effect CR2 pointwise confidence interval and a simultaneous whole-function confidence band are separate scientific targets, not automatically qualified by variance-component null model feasibility.

The original R35–R39 and R53–R56 numerical negatives and optimizer-start discrepancies remain recorded. Keep issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) (fitted covariance inference) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) (MAR/MNAR and latent whole-participant selection) **OPEN**. Do not modify protected main, promote a stable public inference API, tag 1.2 or publish PyPI.
