# W3 R85 — prospectively frozen validation-ascertainment bias falsification

**Research-only protocol frozen 21 October 2026 before any R85 numerical results; no estimator or release qualification.**

## Scientific question
R84 introduced new, genuinely independently ascertained outcomes for 25%/50% of originally missing synthetic gaze values. That was MCAR **within the originally missing stratum** by generator construction. R85 tests a necessary assumption: **what happens when the external ascertainment of otherwise missing values is itself selective?** Correcting the first-stage missing gaze mechanism is not credible if the auxiliary validation stream has outcome-dependent loss and its own measurement/selection model is unverified.

## New source denominators and outcomes
Exactly **32 new independent primitive source blocks** for each fixed (unit design × predictor support × source variance) cell: 72 independent curves or 36 participants with 3 correlated trials; 2 or 16 signed x=±4 independent predictor anchors; constant or s_i=1+.75|x_i| unit scale; 31×2 time/coordinate slope truth. Frozen **NEW source seed 202610218580**, original MAR/MNAR mask seed **202610218581**, validation ascertainment seed **202610218582**. Complete source law retains R84's prespecified correlated temporal/spatial Gaussian process, independent-unit Student-t5 radial multiplier and rare centered signed Bernoulli unit shock. There are **256 complete synthetic X/Y source conditions**, two paired **MAR (true first-stage δ=0) and MNAR (true first-stage δ=1.1)** masks per source, therefore **512 original source/mask observations**. Each source/mask is analyzed under five validation/estimator strategies, **2,560 source-strategy rows** but only **32 independent generating blocks per fixed cell**, not 2,560 independent source samples.

## Independent recovery innovations and three frozen validation laws
For originally MISSING observations only, share a newly generated independent U ~Uniform(0,1) across three recovery laws:
- **Independent validation**: recovery probability r_independent=.25.
- **Recorded-input-selective validation**: $r_{obs}=\operatorname{logit}^{-1}(\operatorname{logit}(.25)+.7|x|/4+.7t)$. This selection probability depends on *recorded* x and normalized time, and is computable for recovered samples without source truth.
- **Latent-outcome-selective validation**: $r_{latent}=\operatorname{logit}^{-1}(\operatorname{logit}(.25)+1.0\tanh((Y-\mu_{true})/.08))$. This additionally depends on the original true response residual; its true validation propensity is **simulator-only** because the generating conditional mean is unavailable in an experiment. It is NOT a real sensor validation mechanism.

## Fixed analysis strategy
For each source and original MAR/MNAR mask, the five predeclared strategies are:
1. `independent_known`: independent validation, correct constant recovery weight 1/.25.
2. `recorded_naive`: recorded-selective validation, incorrectly assume constant probability .25.
3. `recorded_correct`: same recorded-selective mask, recovery inverse weight 1/r_obs(x,t), computable from recorded covariates **only under the stipulated known validation law**.
4. `latent_naive`: latent-outcome-selective validation, incorrectly assume constant .25.
5. `latent_oracle`: same latent-selective mask, simulator-known true recovery propensity 1/r_latent(Y,true_mean), **not a generally feasible observed-data correction**.

The original gaze missingness model remains $\operatorname{logit}(P(M=1))=-2.2+|x|/4+.7t+.2j+\delta\tanh((Y-\mu_{true})/.08)$. For all five strategies, estimate original first-stage scalar δ with the **same original-visible-only pointwise intercept/slope pilot** as R84, using genuinely visible Y plus only externally recovered originally missing Y. Weighted Bernoulli selection score uses original observed Y weight 1 and recovered Y weight 1/r_assumed. **Never** use unrecovered Y for score or pilot. Original simulator-known true δ is only for evaluation. The source generator's true conditional mean may be consulted only by `latent_oracle` to compute the *recovery* probability (not original pilot). Solver: frozen bounded bisection δ in [-4,4], refuse nonfinite/no information/unbracketed roots. For all rows report convergence, actual recovered count and fraction, true δ, point estimate, absolute signed error, visible-only pilot refused grid count, generator truth-use flag only for oracle; original native function-on-scalar still refuses incomplete trajectories. No standard error, no 90% coverage, no missingness-adjusted functional band.

## Falsification comparisons
Primary adverse cell (2 extreme predictor anchors, heteroskedasticity), both curve and repeated-participant designs, MAR negative and MNAR positive controls. Report all eight design/support/variance cells, including any failures. Compare **within-source** `recorded_correct - recorded_naive` and `latent_oracle - latent_naive`, noting that corrected weighting **need not improve every finite sample** and that the oracle is unavailable in field data. Compare fitted δ signed error, absolute error, true source denominator and recovered sample counts. No publication of numerical articles/plots until **separate R85-A actual original archive audit** independently reconstructs all 256 new X/Y, all 512 masks, all three recovery fields, 2,560 strategy results and source SHA256.

## Publication and release gates
Three Python 3.11–3.13 deterministic tests gate eight original disjoint four-block source shards and immutable SHA256 aggregate. R85-A independently reconstructs the actual archived original source and scores using a distinct numerical solver (original bounded bisection; independent Newton), with fail-closed source/recovery identity, irrecoverable-sample exclusion, and no-release assertions. Publish only independently audited documentation/plots, not experimental estimator implementation. **Issues #289 and #296 stay OPEN; stable 1.1.0, public API, and unreleased 1.2/PyPI RELEASE HOLD unchanged.**
